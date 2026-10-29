"""Bateria Fase A sobre la curva combinada del portfolio multi-activo.

DSR con N=12 (registro explicito: las 11 variantes de Fase A + esta regla en
portfolio; V recalculada como varianza across-trial de los Sharpes diarios de
esas 12 series), block bootstrap (21d, B=10000) del retorno medio, t>3, y
benchmark = portfolio igual-ponderado buy&hold de los mismos 10 activos
(curva ya generada por portfolio_runner; datos congelados en data/multi/).

Uso: /opt/trading-bot/venv/bin/python src/portfolio_bateria.py
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from rigor_estadistico import (dsr, block_bootstrap_ci,  # noqa: E402
                               ar1_effective_n, PPY)
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest  # noqa: E402

CSV_BTC = "data/btc_usd_5y_1d.csv"
EQ = "results/portfolio_equity.csv"
BENCH = "results/portfolio_benchmark.csv"
SIZE_FRACTION = 0.05
WARMUP = 200
BLOCK = 21
B_BOOT = 10000
SEED = 43
# Fase A: 11 variantes sobre BTC-USD 5y + esta Fase B en portfolio = 12 intentos
VARIANTES_A = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
               "sma_timing_50", "sma_timing_100", "sma_timing_304",
               "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
N_TRIALS = 12


def sharpe_diario(rets):
    r = np.asarray(rets, dtype=float)
    r = r[~np.isnan(r)]
    return float(r.mean() / r.std()) if r.std() > 0 else 0.0, len(r)


def main():
    eq = pd.read_csv(EQ, index_col=0, parse_dates=True).iloc[:, 0]
    bench = pd.read_csv(BENCH, index_col=0, parse_dates=True).iloc[:, 0]
    rets = eq.pct_change().dropna()
    per = rets.values
    s_per, t_raw = sharpe_diario(per)
    t_eff = int(ar1_effective_n(per))
    skew = float(rets.skew())
    kurt = float(rets.kurt() + 3)

    # V across-trial: Sharpe diario de las 11 variantes Fase A (mismo CSV BTC
    # 5y, OOS 60/40, sizing 5%) + este portfolio = 12 series
    df = pd.read_csv(CSV_BTC, index_col=0, parse_dates=True)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
    split = int(len(df) * 0.6)
    sharpes = []
    for name in VARIANTES_A:
        fn = STRATEGIES[name]
        a = max(0, split - WARMUP)
        sig = fn(df.iloc[a:])
        res = run_backtest(df.iloc[split:], sig.iloc[split - a:],
                           size_fraction=SIZE_FRACTION)
        s, _ = sharpe_diario(res["equity"].pct_change().dropna().values)
        sharpes.append(s)
    sharpes.append(s_per)
    var_trials = float(np.var(sharpes, ddof=1))

    dsr_val, sr0 = dsr(s_per, t_eff, N_TRIALS, var_trials, skew, kurt)
    t_stat = float(per.mean() / per.std() * np.sqrt(t_eff)) if per.std() > 0 else 0.0
    lo, hi, pt = block_bootstrap_ci(per, BLOCK, B_BOOT,
                                    lambda x: x.mean() * PPY * 100, SEED)
    rb = bench.pct_change().dropna()
    sharpe_b = float(rb.mean() / rb.std() * np.sqrt(PPY)) if rb.std() > 0 else 0.0
    ddb = (bench - bench.cummax()) / bench.cummax()
    ddp = (eq - eq.cummax()) / eq.cummax()

    out = {
        "n_trials": N_TRIALS, "var_trials": var_trials,
        "sharpe_anual": round(s_per * np.sqrt(PPY), 3),
        "n_obs": t_raw, "n_obs_eff": t_eff, "skew": round(skew, 3),
        "kurt": round(kurt, 3), "sr0_per": round(sr0, 5),
        "dsr": round(dsr_val, 4), "t_stat": round(t_stat, 2),
        "pasa_t3": bool(t_stat > 3),
        "ic_retorno_anual_pct": [round(lo, 2), round(hi, 2)],
        "edge_ic": bool(lo > 0 and hi > 0),
        "retorno_pct": round((eq.iloc[-1] / eq.iloc[0] - 1) * 100, 2),
        "max_dd_pct": round(ddp.min() * 100, 2),
        "bench_retorno_pct": round((bench.iloc[-1] / bench.iloc[0] - 1) * 100, 2),
        "bench_sharpe": round(sharpe_b, 3),
        "bench_max_dd_pct": round(ddb.min() * 100, 2),
        "dias": len(eq),
        "exposicion_media": json.load(open("results/portfolio_runner.json"))["exposicion_media"],
    }
    print(json.dumps(out, indent=2))
    with open("results/portfolio_bateria.json", "w") as f:
        json.dump(out, f, indent=2)
    print("-> results/portfolio_bateria.json guardado")


if __name__ == "__main__":
    main()
