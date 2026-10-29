"""Fase B — Portfolio multi-activo con vol-targeting (Carver simplificado).

Plan aprobado (tarea rigor estadistico, Fase 0, 2026-10-07):
  - Regla: tsmom_365 (long-only) identica en los 10 activos, sin optimizar
    por activo. Un activo entra cuando tiene >=366 velas de historia.
  - Sizing Carver: w_i = sigma_target/sigma_i, sigma_i = EWMA(lambda=0.94)
    de la vol de retornos diarios; sigma_target=10% anual; w_max=0.20;
    gross <= 1.0; rebalanceo diario. Reemplaza size_fraction.
  - Riesgo con matriz de covarianza EWMA COMPLETA (w'Σw, correlacion real).
    La aproximacion diagonal es optimista con criptos correlacionadas
    (correccion de Sonnet Windows) — NO se usa. Vetos registrados:
    peso>w_max tras cap, vol portfolio > 1.25*sigma_target (escala a tope).
  - UNA curva de equity con capital compartido: r_p(t) = sum_i w_i(t-1)*r_i(t);
    mismos costes que el backtester (0.1% comision + 0.05% slippage sobre el
    turnover); invariante H1 sobre la curva combinada.
  - Datos congelados: un CSV por activo con sha256 + meta en data/multi/.

RAMA fase-b-multiactivo — capa de analisis; NO toca main ni el paper runner.

Uso: /opt/trading-bot/venv/bin/python src/portfolio_runner.py
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ACTIVOS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
           "ADA-USD", "AVAX-USD", "LINK-USD", "DOGE-USD", "LTC-USD"]
LOOKBACK = 365
LAMBDA = 0.94
SIGMA_TARGET = 0.10          # anual
W_MAX = 0.20
GROSS_MAX = 1.0
VOL_TOPE_MULT = 1.25
PPY = 365
COMMISSION = 0.001
SLIPPAGE = 0.0005
DATA_DIR = "data/multi"
RESULTS = "results/portfolio_runner.json"


# ---------------------------------------------------------------- nucleo puro
def ewma_vol(rets: np.ndarray, lam: float = LAMBDA) -> np.ndarray:
    """Vol diaria EWMA de varianza: s2_t = lam*s2_(t-1) + (1-lam)*r_t^2.
    Devuelve sigma diaria por fila (nan hasta el primer dato valido)."""
    s2 = np.full(len(rets), np.nan)
    prev = None
    for i, r in enumerate(rets):
        if np.isnan(r):
            s2[i] = prev if prev is not None else np.nan
            continue
        prev = r * r if prev is None else lam * prev + (1 - lam) * r * r
        s2[i] = prev
    return np.sqrt(s2)


def ewma_cov_matrix(rets_mat: np.ndarray, lam: float = LAMBDA) -> np.ndarray:
    """Matriz de covarianza EWMA COMPLETA en el ultimo instante.
    rets_mat: (T, n) con nan permitidos; usa pares validos acumulados."""
    n = rets_mat.shape[1]
    cov = np.full((n, n), np.nan)
    acc = np.zeros((n, n))
    filled = np.zeros((n, n), dtype=bool)
    for t in range(rets_mat.shape[0]):
        r = rets_mat[t]
        for i in range(n):
            for j in range(n):
                if np.isnan(r[i]) or np.isnan(r[j]):
                    continue
                if not filled[i, j]:
                    acc[i, j] = r[i] * r[j]
                    filled[i, j] = True
                else:
                    acc[i, j] = lam * acc[i, j] + (1 - lam) * r[i] * r[j]
    cov[filled] = acc[filled]
    return cov


def carver_weights(sigmas_anual: np.ndarray, w_max: float = W_MAX,
                   gross_max: float = GROSS_MAX) -> tuple:
    """w_i = sigma_target/sigma_i capado a w_max; si gross>gross_max se
    escala proporcionalmente. Devuelve (w, vetos_wmax: list)."""
    vetos = []
    w = np.zeros(len(sigmas_anual))
    for i, s in enumerate(sigmas_anual):
        if np.isnan(s) or s <= 0:
            continue
        raw = SIGMA_TARGET / s
        if raw > w_max:
            vetos.append({"activo_idx": i, "peso_crudo": round(float(raw), 4)})
        w[i] = min(raw, w_max)
    gross = w.sum()
    if gross > gross_max and gross > 0:
        w = w * (gross_max / gross)
    return w, vetos


def portfolio_vol_anual(w: np.ndarray, cov_diaria: np.ndarray) -> float:
    """Vol anual del portfolio con covarianza COMPLETA: sqrt(w'Σw)*sqrt(365).
    Si la cov no esta disponible para pares activos, usa solo las varianzas
    disponibles (documentado: pares sin historia se tratan como sin
    covarianza cruzada — se reduce al bloque disponible)."""
    idx = [i for i in range(len(w)) if w[i] != 0]
    if not idx:
        return 0.0
    sub = cov_diaria[np.ix_(idx, idx)]
    sub = np.where(np.isnan(sub), 0.0, sub)
    var = float(w[idx] @ sub @ w[idx])
    return float(np.sqrt(max(var, 0.0)) * np.sqrt(PPY))


# ---------------------------------------------------------------- datos
def load_or_download() -> dict:
    """Un CSV congelado por activo (+ sha256 + meta). Devuelve {ticker: df}."""
    os.makedirs(DATA_DIR, exist_ok=True)
    import yfinance as yf
    out = {}
    for ticker in ACTIVOS:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(DATA_DIR, f"{ticker.lower().replace('-', '_')}_{stamp}.csv")
        if os.path.exists(path):
            # ya congelado hoy: reutilizar (no re-descargar, hash preservado)
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
            out[ticker] = df
            print(f"  {ticker:<10} {len(df):>5} velas (cache hoy) sha256 {digest[:12]}…")
            continue
        df = yf.download(ticker, period="max", interval="1d",
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.lower)[["open", "high", "low", "close",
                                           "volume"]].dropna()
        df.to_csv(path, index_label="date")
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        with open(path + ".sha256", "w") as f:
            f.write(f"{digest}  {os.path.basename(path)}\n")
        with open(path + ".meta.json", "w") as f:
            json.dump({"fecha_descarga": datetime.now(timezone.utc).isoformat(),
                       "ticker": ticker, "period": "max", "interval": "1d",
                       "auto_adjust": True, "sha256": digest,
                       "n_velas": len(df),
                       "primera_fecha": str(df.index[0].date()),
                       "ultima_fecha": str(df.index[-1].date())}, f, indent=2)
        out[ticker] = df
        print(f"  {ticker:<10} {len(df):>5} velas "
              f"({df.index[0].date()} -> {df.index[-1].date()}) sha256 {digest[:12]}…")
    return out


# ---------------------------------------------------------------- simulacion
def simulate(datos: dict):
    """Bucle diario sobre el union de fechas. Pesos decididos con datos hasta
    t-1 y aplicados a r(t) (sin look-ahead). Devuelve dict con equity,
    vetos, benchmark y diagnosticos."""
    closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
    rets = closes.pct_change()
    fechas = closes.index
    tickers = list(datos.keys())
    n = len(tickers)

    # ---- prepase vectorizado: vol EWMA y cov EWMA acumuladas para todo t.
    # Un solo pase: s2_i(t) usa r_i(t); la simulacion consulta el valor en
    # t-1 (decision con datos hasta t-1, sin look-ahead).
    R = rets.values
    s2_path = np.full((len(fechas), n), np.nan)
    cov_path = np.full((len(fechas), n, n), np.nan)
    s2 = np.full(n, np.nan)
    cov_acc = np.full((n, n), np.nan)
    have_var = np.zeros(n, dtype=bool)
    have_cov = np.zeros((n, n), dtype=bool)
    for t in range(len(fechas)):
        r = R[t]
        for i in range(n):
            if np.isnan(r[i]):
                continue
            if not have_var[i]:
                s2[i] = r[i] * r[i]
                have_var[i] = True
            else:
                s2[i] = LAMBDA * s2[i] + (1 - LAMBDA) * r[i] * r[i]
        for i in range(n):
            if np.isnan(r[i]):
                continue
            for j in range(n):
                if np.isnan(r[j]):
                    continue
                if not have_cov[i, j]:
                    cov_acc[i, j] = r[i] * r[j]
                    have_cov[i, j] = True
                else:
                    cov_acc[i, j] = LAMBDA * cov_acc[i, j] + \
                        (1 - LAMBDA) * r[i] * r[j]
        s2_path[t] = s2
        cov_path[t] = cov_acc

    equity = 1.0
    eq_curve, bench_curve = [], []
    vetos_wmax, vetos_vol, exposure = [], [], []
    rp_hist, coste_hist = [], []
    w_prev = np.zeros(n)

    for t in range(len(fechas)):
        # 1. senal y vol con datos hasta t-1
        w_target = np.zeros(n)
        sigmas_anual = np.full(n, np.nan)
        if t > 0:
            for i, tk in enumerate(tickers):
                s = rets[tk].iloc[:t]
                if s.notna().sum() < LOOKBACK + 1:
                    continue
                mom = closes[tk].iloc[t - 1] / closes[tk].iloc[t - 1 - LOOKBACK] - 1
                if not (mom > 0):
                    continue
                sig = np.sqrt(s2_path[t - 1, i])
                if not np.isnan(sig) and sig > 0:
                    sigmas_anual[i] = sig * np.sqrt(PPY)
            w_target, vetos_dia = carver_weights(sigmas_anual)
            for v in vetos_dia:
                vetos_wmax.append({"fecha": str(fechas[t].date()),
                                   "activo": tickers[v["activo_idx"]],
                                   "peso_crudo": v["peso_crudo"]})
        # 2. covarianza completa hasta t-1 y veto de vol de portfolio
        cov = cov_path[t - 1] if t > 1 else np.full((n, n), np.nan)
        vol_p = portfolio_vol_anual(w_target, cov)
        if vol_p > VOL_TOPE_MULT * SIGMA_TARGET:
            escala = (VOL_TOPE_MULT * SIGMA_TARGET) / vol_p
            vetos_vol.append({"fecha": str(fechas[t].date()),
                              "vol_portfolio": round(vol_p, 4),
                              "escala_aplicada": round(escala, 4)})
            w_target = w_target * escala
        # 3. retorno del dia con pesos de cierre de t-1 (w_prev) — ya
        #    rebalanceados; los pesos objetivo de hoy se aplican manana.
        r_dia = rets.iloc[t].values
        r_p = float(np.nansum(w_prev * r_dia))
        turnover = float(np.nansum(np.abs(w_prev - w_target)))
        coste = turnover * (COMMISSION + SLIPPAGE)
        equity *= (1 + r_p - coste)
        # benchmark: media de activos elegibles (misma condicion de historia)
        elig = [i for i in range(n) if rets.iloc[:t + 1].iloc[:, i].notna().sum() >= LOOKBACK + 1]
        r_b = float(np.nanmean(r_dia[elig])) if elig else 0.0
        eq_curve.append(equity)
        bench_curve.append((bench_curve[-1] if bench_curve else 1.0) * (1 + r_b))
        exposure.append(float(np.nansum(w_prev)))
        rp_hist.append(r_p)
        coste_hist.append(coste)
        w_prev = w_target

    eq = pd.Series(eq_curve, index=fechas)
    bench = pd.Series(bench_curve, index=fechas)
    return {"equity": eq, "benchmark": bench, "vetos_wmax": vetos_wmax,
            "vetos_vol": vetos_vol, "exposure": pd.Series(exposure, index=fechas),
            "rp": pd.Series(rp_hist, index=fechas),
            "costes": pd.Series(coste_hist, index=fechas),
            "n_dias": len(fechas)}


def metrics(eq: pd.Series, bench: pd.Series) -> dict:
    rets = eq.pct_change().dropna()
    sharpe = float(rets.mean() / rets.std() * np.sqrt(PPY)) if rets.std() > 0 else 0.0
    dd = (eq - eq.cummax()) / eq.cummax()
    calmar = float((eq.iloc[-1] / eq.iloc[0] - 1) / abs(dd.min())) if dd.min() != 0 else 0.0
    rb = bench.pct_change().dropna()
    sharpe_b = float(rb.mean() / rb.std() * np.sqrt(PPY)) if rb.std() > 0 else 0.0
    ddb = (bench - bench.cummax()) / bench.cummax()
    calmar_b = float((bench.iloc[-1] / bench.iloc[0] - 1) / abs(ddb.min())) if ddb.min() != 0 else 0.0
    return {"retorno_pct": round((eq.iloc[-1] / eq.iloc[0] - 1) * 100, 2),
            "sharpe": round(sharpe, 3), "max_dd_pct": round(dd.min() * 100, 2),
            "calmar": round(calmar, 3),
            "bench_retorno_pct": round((bench.iloc[-1] / bench.iloc[0] - 1) * 100, 2),
            "bench_sharpe": round(sharpe_b, 3),
            "bench_max_dd_pct": round(ddb.min() * 100, 2),
            "bench_calmar": round(calmar_b, 3)}


def main():
    print("Descarga y congelacion de datos (10 activos):")
    datos = load_or_download()
    print("Simulacion portfolio (tsmom_365 + Carver + cov EWMA completa):")
    res = simulate(datos)
    m = metrics(res["equity"], res["benchmark"])
    print(json.dumps(m, indent=2))
    print(f"dias={res['n_dias']} vetos_wmax={len(res['vetos_wmax'])} "
          f"vetos_vol={len(res['vetos_vol'])} "
          f"exposicion_media={res['exposure'].mean():.3f}")
    res["equity"].to_csv("results/portfolio_equity.csv", index_label="date")
    res["benchmark"].to_csv("results/portfolio_benchmark.csv", index_label="date")
    with open(RESULTS, "w") as f:
        json.dump({"activos": ACTIVOS, "lookback": LOOKBACK, "lambda": LAMBDA,
                   "sigma_target": SIGMA_TARGET, "w_max": W_MAX,
                   "gross_max": GROSS_MAX, "vol_tope_mult": VOL_TOPE_MULT,
                   "costes": {"commission": COMMISSION, "slippage": SLIPPAGE},
                   "metricas": m,
                   "n_vetos_wmax": len(res["vetos_wmax"]),
                   "n_vetos_vol": len(res["vetos_vol"]),
                   "vetos_wmax_muestra": res["vetos_wmax"][:10],
                   "vetos_vol_muestra": res["vetos_vol"][:10],
                   "exposicion_media": float(res["exposure"].mean())},
                  f, indent=2)
    print(f"-> {RESULTS} y results/portfolio_equity.csv guardados")


if __name__ == "__main__":
    main()
