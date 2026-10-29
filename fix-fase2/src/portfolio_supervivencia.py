"""Paquete 3 — Test de sesgo de supervivencia del portfolio.

Pregunta: los 10 activos son los supervivientes de hoy. ¿Sobrevive la senal
si el universo incluye activos que cayeron >85-90% desde sus maximos?

UNIVERSO ALTERNATIVO (criterio fijado ANTES de correr, sin mirar la senal):
activos que estuvieron en el top-20 de market-cap en 2017-2021 y hoy cotizan
>85% por debajo de su maximo historico, con datos diarios congelables desde
el mismo proveedor (yfinance):
  EOS-USD  (top-5 en 2017-2018 por ICO; ~-95% desde ATH 2018)
  XLM-USD  (top-10 2017-2018; ~-90% desde ATH 2018)
  BCH-USD  (top-5 desde el fork 2017; ~-90% desde ATH 2017)
  FIL-USD  (top-15 en 2020; ~-98% desde ATH 2021)
  ICP-USD  (top-10 en 2021; ~-98% desde ATH 2021)
No se cherry-pickea contra la senal: el criterio es de caida desde maximo y
capitalizacion historica, no de resultado de la regla. Los CSV se congelan
en data/multi_muertos/ con sha256 + meta (mismo protocolo que data/multi/).

Misma regla (tsmom_365), mismos parametros (Carver, cov EWMA completa,
w_max, gross, costes). La curva del universo extendido (15 activos) se bate
con la misma bateria de 4 pruebas y se compara con el universo superviviente.

Uso: /opt/trading-bot/venv/bin/python src/portfolio_supervivencia.py
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from portfolio_runner import (simulate, SIGMA_TARGET, LAMBDA, W_MAX,  # noqa: E402
                              GROSS_MAX, COMMISSION, SLIPPAGE)
from rigor_estadistico import dsr, block_bootstrap_ci, ar1_effective_n, PPY  # noqa: E402
import sys
sys.path.insert(0, "src")

MUERTOS = ["EOS-USD", "XLM-USD", "BCH-USD", "FIL-USD", "ICP-USD"]
VIVOS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
         "ADA-USD", "AVAX-USD", "LINK-USD", "DOGE-USD", "LTC-USD"]
DATA_DIR = "data/multi_muertos"
N_TRIALS = 12
VAR_TRIALS = 0.0007021947704551833
BLOCK = 21
B_BOOT = 10000
SEED = 42
CRITERIO = ("top-20 market-cap historico (2017-2021) y hoy >85% bajo maximo; "
            "criterio de caida, no de senal; yfinance period=max")


def congelar(tickers):
    os.makedirs(DATA_DIR, exist_ok=True)
    import yfinance as yf
    out = {}
    for ticker in tickers:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(DATA_DIR,
                            f"{ticker.lower().replace('-', '_')}_{stamp}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            out[ticker] = df
            print(f"  {ticker:<10} {len(df):>5} velas (cache hoy)")
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
                       "auto_adjust": True, "sha256": digest, "n_velas": len(df),
                       "primera_fecha": str(df.index[0].date()),
                       "ultima_fecha": str(df.index[-1].date()),
                       "criterio_inclusion": CRITERIO}, f, indent=2)
        out[ticker] = df
        print(f"  {ticker:<10} {len(df):>5} velas ({df.index[0].date()} -> "
              f"{df.index[-1].date()}) sha256 {digest[:12]}…")
    return out


def bateria(eq: pd.Series, bench: pd.Series):
    rets = eq.pct_change().dropna()
    per = rets.values
    t_eff = int(ar1_effective_n(per))
    sharpe_per = per.mean() / per.std() if per.std() > 0 else 0.0
    skew = float(rets.skew())
    kurt = float(rets.kurt() + 3)
    dsr_val, _ = dsr(sharpe_per, t_eff, N_TRIALS, VAR_TRIALS, skew, kurt)
    t_stat = float(per.mean() / per.std() * np.sqrt(t_eff)) if per.std() > 0 else 0.0
    lo, hi, _ = block_bootstrap_ci(per, BLOCK, B_BOOT,
                                   lambda x: x.mean() * PPY * 100, SEED)
    rb = bench.pct_change().dropna()
    sharpe_b = float(rb.mean() / rb.std() * np.sqrt(PPY)) if rb.std() > 0 else 0.0
    dd = (eq - eq.cummax()) / eq.cummax()
    return {"retorno_pct": round((eq.iloc[-1] / eq.iloc[0] - 1) * 100, 2),
            "sharpe": round(sharpe_per * np.sqrt(PPY), 3),
            "max_dd_pct": round(dd.min() * 100, 2),
            "dsr": round(dsr_val, 4), "t_stat": round(t_stat, 2),
            "pasa_t3": bool(t_stat > 3),
            "ic95_retorno_anual_pct": [round(lo, 2), round(hi, 2)],
            "edge_ic": bool(lo > 0 and hi > 0),
            "bench_retorno_pct": round((bench.iloc[-1] / bench.iloc[0] - 1) * 100, 2),
            "bench_sharpe": round(sharpe_b, 3),
            "supera_bench_sharpe": bool(sharpe_per * np.sqrt(PPY) > sharpe_b)}


def main():
    datos_vivos = congelar(VIVOS)
    datos_muertos = congelar(MUERTOS)
    datos_ext = {**datos_vivos, **datos_muertos}
    print(f"Universo extendido: {len(datos_ext)} activos "
          f"(10 supervivientes + 5 caidos)")
    res = simulate(datos_ext)
    r = bateria(res["equity"], res["benchmark"])
    print(json.dumps(r, indent=2))
    print(f"vetos_wmax={len(res['vetos_wmax'])} vetos_vol={len(res['vetos_vol'])} "
          f"exposicion_media={res['exposure'].mean():.3f}")
    res["equity"].to_csv("results/portfolio_equity_muertos.csv", index_label="date")
    res["benchmark"].to_csv("results/portfolio_benchmark_muertos.csv", index_label="date")
    with open("results/portfolio_supervivencia.json", "w") as f:
        json.dump({"criterio_inclusion": CRITERIO, "muertos": MUERTOS,
                   "n_activos": len(datos_ext), "metricas": r,
                   "n_vetos_wmax": len(res["vetos_wmax"]),
                   "n_vetos_vol": len(res["vetos_vol"]),
                   "exposicion_media": float(res["exposure"].mean())},
                  f, indent=2)
    print("-> results/portfolio_supervivencia.json guardado")


if __name__ == "__main__":
    main()
