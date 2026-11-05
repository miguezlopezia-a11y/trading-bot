"""A-5 (N6, Fase 0) — Reverificacion INDEPENDIENTE del numero que esta tarea
usa como eje: que V con las tres estrategias anadidas da 0.001550 y el liston
1.8024.

El brief lo dice literal: "Es de N4, no mio, y no vale creerlo."

Independencia: la PSR, el E[max_N] y el ajuste AR(1) estan REESCRITOS aqui
desde statistics.NormalDist. No se importa nada de rigor_estadistico.py ni de
potencia_fase_b.py. Lo unico que se importa de src/ es el pipeline de
backtest (strategies + backtester), porque el brief prohibe editarlo y
reimplementar un backtester seria evaluar de otra forma, no reverificar.

Tambien cubre §2.2 (que backtest_sizing05.json tiene sizing 0.05 y el CSV
congelado) y §2.5 (que con N bajo la restriccion es t>3, no el DSR).

Uso (desde fix-fase2/):  python3 fase0_n6/a5_v_y_liston_n15.py
"""
import json
import math
import os
import statistics
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES          # noqa: E402  (pipeline, no metrica)
from backtester import run_backtest        # noqa: E402

CSV = "data/btc_usd_5y_1d.csv"
PPY = 365
TRAIN_FRAC = 0.6
WARMUP = 200
SIZE_FRACTION = 0.05
GAMMA_E = 0.5772156649
ND = statistics.NormalDist()

V11 = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
       "sma_timing_50", "sma_timing_100", "sma_timing_304",
       "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
EXTRA3 = ["mean_reversion", "breakout", "trend_following"]


# ---------- metrica reescrita a mano -----------------------------------
def psr_m(sharpe_per, n_obs, sr_star, skew, kurt):
    num = (sharpe_per - sr_star) * math.sqrt(n_obs - 1)
    den = math.sqrt(1 - skew * sharpe_per + (kurt - 1) / 4 * sharpe_per ** 2)
    return ND.cdf(num / den)


def sr0_m(n_trials, var_trials):
    if n_trials <= 1:
        return 0.0
    z1 = ND.inv_cdf(1 - 1.0 / n_trials)
    z2 = ND.inv_cdf(1 - 1.0 / (n_trials * math.e))
    return math.sqrt(var_trials) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def liston_dsr_m(n_trials, var_trials, n_eff, skew, kurt, conf=0.95):
    """Menor Sharpe diario con PSR(SR0) >= conf, por biseccion."""
    s0 = sr0_m(n_trials, var_trials)
    if psr_m(s0, n_eff, s0, skew, kurt) >= conf:
        return s0, s0
    lo, hi = s0, s0 + 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if psr_m(mid, n_eff, s0, skew, kurt) >= conf:
            hi = mid
        else:
            lo = mid
    return hi, s0


def ar1_eff_m(r):
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0:
        return float(len(r))
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho = min(max(rho, -0.95), 0.95)
    return len(r) * (1 - rho) / (1 + rho)


# ---------- pipeline de Fase A ----------------------------------------
def serie_diaria(nombre, df):
    split = int(len(df) * TRAIN_FRAC)
    a = max(0, split - WARMUP)
    sig_full = STRATEGIES[nombre](df.iloc[a:])
    sliced = df.iloc[split:]
    sig = sig_full.iloc[split - a:]
    res = run_backtest(sliced, sig, size_fraction=SIZE_FRACTION)
    rets = res["equity"].pct_change().dropna().values
    return rets, len(res["trades"])


def sharpe_diario(r):
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    return float(r.mean() / r.std()) if r.std() > 0 else 0.0


def main():
    print("=== A-5.0 §2.2: que dice backtest_sizing05.json ===")
    d05 = json.load(open("../results/backtest_sizing05.json"))
    print("  size_fraction :", d05["size_fraction"])
    print("  csv           :", d05["csv"])
    print("  claves        :", list(d05["test_results"]))
    print("  sharpes       :", {k: v["sharpe"] for k, v in d05["test_results"].items()})
    print()

    df = pd.read_csv(CSV, index_col=0, parse_dates=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
    print(f"=== A-5.1 CSV congelado: {len(df)} velas, "
          f"{df.index[0].date()} -> {df.index[-1].date()} ===")
    print(f"  split 0.6 = {int(len(df) * TRAIN_FRAC)}  "
          f"-> OOS = {len(df) - int(len(df) * TRAIN_FRAC)} velas")
    print()

    print("=== A-5.2 reejecucion de las 11 + las 3, pipeline de Fase A ===")
    sh = {}
    for n in V11 + EXTRA3:
        r, ntr = serie_diaria(n, df)
        s = sharpe_diario(r)
        sh[n] = s
        marca = "   <- FUERA de V(11)" if n in EXTRA3 else ""
        print(f"  {n:<24} sharpe_diario={s:>12.8f}  anual={s*math.sqrt(PPY):>8.4f}"
              f"  trades={ntr:>4}{marca}")
    print()

    # Sharpe diario del portfolio de Fase B (trial nº12 del expediente)
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    rp = eq.pct_change().dropna().values
    s_port = sharpe_diario(rp)
    print(f"  PORTFOLIO Fase B (trial nº12) sharpe_diario={s_port:.11f}")
    print()

    # Parametros del objeto evaluado, recalculados a mano
    t_eff = int(ar1_eff_m(rp))
    skew = float(pd.Series(rp).skew())
    kurt = float(pd.Series(rp).kurt() + 3)
    print("=== A-5.3 parametros del objeto evaluado (recalculados) ===")
    print(f"  T (retornos)   : {len(rp)}")
    print(f"  T_eff AR(1)    : {t_eff}        (cableado: 4336)")
    print(f"  skew           : {skew:.6f}   (cableado: 1.037)")
    print(f"  kurt raw       : {kurt:.6f}  (cableado: 31.999)")
    print(f"  sharpe anual   : {s_port*math.sqrt(PPY):.6f} (cableado: 1.008)")
    print()

    v12 = float(np.var([sh[n] for n in V11] + [s_port], ddof=1))
    v15 = float(np.var([sh[n] for n in V11 + EXTRA3] + [s_port], ddof=1))

    print("=== A-5.4 las dos V, con ddof=1 ===")
    print(f"  V(12) = 11 + portfolio                : {v12:.12f}")
    print(f"    cableada en potencia_fase_b.py      : 0.0007021947704551833")
    print(f"    diferencia                          : "
          f"{abs(v12 - 0.0007021947704551833):.3e}")
    print(f"  V(15) = 11 + portfolio + las 3        : {v15:.12f}")
    print(f"    afirmado por N4                     : 0.001550")
    print(f"    coincide a 6 decimales?             : "
          f"{round(v15, 6) == 0.001550}")
    print(f"  cociente V(15)/V(12)                  : {v15/v12:.4f}")
    print()

    print("=== A-5.5 el liston, con PSR reescrita a mano ===")
    filas = []
    for etiqueta, n, v in [
        ("expediente: 11+portfolio", 12, v12),
        ("11+portfolio+3 extra", 15, v15),
        ("V de 15, N=12 fijo", 12, v15),
        ("V de 12, N=15", 15, v12),
    ]:
        lper, s0 = liston_dsr_m(n, v, t_eff, skew, kurt)
        lan = lper * math.sqrt(PPY)
        filas.append((etiqueta, n, v, s0, lan))
        print(f"  N={n:<3} V={v:.8f} SR0={s0:.5f} liston_anual={lan:.4f}"
              f"   {etiqueta}")
    print()
    print("  Afirmacion de N4 a verificar: N=15 -> V=0.001550 y liston 1.8024")
    l15 = [f for f in filas if f[1] == 15 and f[2] == v15][0][4]
    print(f"  medido aqui                : liston_anual={l15:.4f}  "
          f"-> {'COINCIDE' if abs(l15 - 1.8024) < 5e-4 else 'NO COINCIDE'}")
    print()

    print("=== A-5.6 §2.5: con N bajo, ¿manda el DSR o manda t>3? ===")
    liston_t_per = 3.0 / math.sqrt(t_eff)
    print(f"  liston t>3 (anual) = 3/sqrt({t_eff})*sqrt(365) = "
          f"{liston_t_per*math.sqrt(PPY):.4f}")
    for n in (1, 2, 3, 5, 12, 15):
        lper, s0 = liston_dsr_m(n, v12, t_eff, skew, kurt)
        lan = lper * math.sqrt(PPY)
        manda = "t>3" if liston_t_per * math.sqrt(PPY) > lan else "DSR"
        print(f"  N={n:<3} liston_DSR={lan:.4f}  manda: {manda}")
    print()

    print("=== A-5.7 el duplicado colapsado (B-13 de N4) ===")
    print("  El trial nº12 (portfolio) es la regla tsmom_365, que ya es el nº9.")
    print("  Si se colapsa el duplicado y se saca al sujeto de su propia V:")
    v11_sin_sujeto = float(np.var([sh[n] for n in V11], ddof=1))
    print(f"  V(11) sin el portfolio                : {v11_sin_sujeto:.12f}")
    print(f"    publicada en rigor_estadistico.json : 0.0007016935642058066")
    print(f"    diferencia                          : "
          f"{abs(v11_sin_sujeto - 0.0007016935642058066):.3e}")
    v10_sin_tsmom = float(np.var(
        [sh[n] for n in V11 if n != "tsmom_365"], ddof=1))
    print(f"  V(10) sin portfolio y sin tsmom_365   : {v10_sin_tsmom:.12f}")
    for etq, n, v in [("sin sujeto, N=11", 11, v11_sin_sujeto),
                      ("sin sujeto ni duplicado, N=10", 10, v10_sin_tsmom),
                      ("sin sujeto, +3, N=14", 14,
                       float(np.var([sh[n] for n in V11 + EXTRA3], ddof=1)))]:
        lper, s0 = liston_dsr_m(n, v, t_eff, skew, kurt)
        print(f"    N={n:<3} V={v:.8f} liston_anual={lper*math.sqrt(PPY):.4f}"
              f"   {etq}")

    os.makedirs("fase0_n6", exist_ok=True)
    with open("fase0_n6/a5_salida.json", "w") as f:
        json.dump({"sharpes_diarios": sh, "sharpe_portfolio": s_port,
                   "t_eff": t_eff, "skew": skew, "kurt_raw": kurt,
                   "V12": v12, "V15": v15, "V11_sin_sujeto": v11_sin_sujeto,
                   "liston_t3_anual": liston_t_per * math.sqrt(PPY),
                   "filas": [{"etiqueta": e, "N": n, "V": v, "SR0": s,
                              "liston_anual": l} for e, n, v, s, l in filas]},
                  f, indent=2)
    print("\n-> fase0_n6/a5_salida.json")


if __name__ == "__main__":
    main()
