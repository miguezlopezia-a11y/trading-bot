"""Paquete 1 — Walk-forward temporal del portfolio multi-activo.

Pregunta: ¿el t=3.48 de la curva completa se sostiene dentro de subperiodos
o se concentra en el primer ciclo cripto?

DISENO (criterio fijado ANTES de correr, 2026-10-09):
  3 tramos contiguos justificados por ciclos de mercado (acumulacion/bull/bear
  en cada tramo), no por los resultados:
    T1: 2015-09-01 -> 2018-12-31  (acumulacion 2015-16, bull 2017, bear 2018)
    T2: 2019-01-01 -> 2022-12-31  (acumulacion, bull 2021, bear 2022)
    T3: 2023-01-01 -> fin datos   (bull 2023-2025)
  T1 empieza 2015-09 porque es cuando el universo diversificado existe
  (ETH entra 2015-08); se documenta, no se ajusta a resultados.

  Una sola simulacion sobre datos completos (warm-up real, parametros
  congelados); la equity se corta por tramo. N sigue = 12 trials.

METRICA DECISIVA (aprobada por Pablo 2026-10-09, antes de la corrida):
  >=2 de 3 tramos con IC95 del retorno POSITIVO (limite inferior > 0) Y
  NINGUN tramo con IC claramente negativo (limite superior < 0).

Uso: /opt/trading-bot/venv/bin/python src/portfolio_walkforward_temporal.py
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from portfolio_runner import load_or_download, simulate, SIGMA_TARGET  # noqa: E402
from rigor_estadistico import dsr, block_bootstrap_ci, ar1_effective_n, PPY  # noqa: E402

TRAMOS = [("T1_2015-2018", "2015-09-01", "2018-12-31"),
          ("T2_2019-2022", "2019-01-01", "2022-12-31"),
          ("T3_2023-fin", "2023-01-01", "2262-12-31")]
N_TRIALS = 12
VAR_TRIALS = 0.0007021947704551833  # misma V de la bateria Fase B (comparabilidad)
BLOCK = 21
B_BOOT = 10000
SEED = 42


def bateria_tramo(rets: pd.Series, n_trials=N_TRIALS,
                  var_trials=VAR_TRIALS, seed=SEED):
    per = rets.values
    per = per[~np.isnan(per)]
    if len(per) < 50:
        return None
    t_eff = int(ar1_effective_n(per))
    sharpe_per = per.mean() / per.std() if per.std() > 0 else 0.0
    skew = float(pd.Series(per).skew())
    kurt = float(pd.Series(per).kurt() + 3)
    dsr_val, sr0 = dsr(sharpe_per, t_eff, n_trials, var_trials, skew, kurt)
    t_stat = float(per.mean() / per.std() * np.sqrt(t_eff)) if per.std() > 0 else 0.0
    lo, hi, _ = block_bootstrap_ci(per, BLOCK, B_BOOT,
                                   lambda x: x.mean() * PPY * 100, seed)
    return {"sharpe_anual": round(sharpe_per * np.sqrt(PPY), 3),
            "dsr": round(dsr_val, 4), "t_stat": round(t_stat, 2),
            "ic95_retorno_anual_pct": [round(lo, 2), round(hi, 2)],
            "n_obs_eff": t_eff}


def dictamen_tramos(resultados: dict):
    """Metrica decisiva aprobada por Pablo (2026-10-09):
    >=2 de 3 tramos con IC95 positivo (limite inferior > 0) y ningun tramo
    con IC claramente negativo (limite superior < 0)."""
    ics = [r["ic95_retorno_anual_pct"] for r in resultados.values() if r]
    positivos = sum(1 for lo, hi in ics if lo > 0)
    claros_neg = sum(1 for lo, hi in ics if hi < 0)
    superado = len(ics) >= 3 and positivos >= 2 and claros_neg == 0
    return {"superado": bool(superado), "tramos_positivos": positivos,
            "tramos_claramente_negativos": claros_neg, "n_tramos": len(ics)}


def main():
    datos = load_or_download()
    res = simulate(datos)
    eq, bench, exposure = res["equity"], res["benchmark"], res["exposure"]
    rets_all = eq.pct_change()

    out = {}
    for i, (nombre, ini, fin) in enumerate(TRAMOS):
        mask = (eq.index >= ini) & (eq.index <= fin)
        rets = rets_all[mask].dropna()
        b = bateria_tramo(rets, seed=SEED + i)
        if b is None:
            out[nombre] = None
            print(f"{nombre}: sin datos suficientes")
            continue
        eq_t = eq[mask]
        bench_t = bench[mask]
        rb = bench_t.pct_change().dropna()
        sharpe_b = float(rb.mean() / rb.std() * np.sqrt(PPY)) if rb.std() > 0 else 0.0
        pnl_t = float((eq_t.iloc[-1] / eq_t.iloc[0] - 1) * 100) if len(eq_t) > 1 else 0.0
        b["pnl_pct"] = round(pnl_t, 2)
        b["exposicion_media"] = round(float(exposure[mask].mean()), 3)
        b["bench_pnl_pct"] = round(float((bench_t.iloc[-1] / bench_t.iloc[0] - 1) * 100), 2)
        b["bench_sharpe"] = round(sharpe_b, 3)
        b["supera_bench_sharpe"] = bool(b["sharpe_anual"] > sharpe_b)
        out[nombre] = b
        print(f"{nombre}: PnL {pnl_t:>8.2f}% exp {b['exposicion_media']:>5} "
              f"Sharpe {b['sharpe_anual']:>6} t {b['t_stat']:>6.2f} "
              f"DSR {b['dsr']:>6.3f} IC {b['ic95_retorno_anual_pct']} "
              f"vs B&H {b['bench_sharpe']:>6}")

    d = dictamen_tramos({k: v for k, v in out.items() if v})
    print(f"\nMETRICA DECISIVA (aprobada 2026-10-09): {d}")
    out["_dictamen"] = d
    with open("results/portfolio_walkforward_temporal.json", "w") as f:
        json.dump({"tramos_definicion": [list(t) for t in TRAMOS],
                   "n_trials": N_TRIALS, "var_trials": VAR_TRIALS,
                   "seed": SEED, "resultados": out}, f, indent=2)
    print("-> results/portfolio_walkforward_temporal.json guardado")


if __name__ == "__main__":
    main()
