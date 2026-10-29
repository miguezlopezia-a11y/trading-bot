"""Backtest con size_fraction=0.05 (politica real de Risk, decision de Pablo
2026-10-07) sobre el CSV congelado. MISMAS senales, MISMO codigo, MISMO split
que run_backtest.py; solo cambia el sizing. NO es optimizacion de parametros.

Referencia vieja (size_fraction=0.95, OOS 2024-10-05 -> 2026-10-05,
resultado_paso3_final.json): ma_cross +7.96%, Sharpe 0.80, DD -3.75%,
12 trades, win 33.3%, PF 2.28.

Salida: results/backtest_sizing05.json
Uso: /opt/trading-bot/venv/bin/python src/backtest_sizing05.py
     (desde la raiz, con data/btc_usd_5y_1d.csv presente)
"""
import json
import sys

import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest, compute_metrics  # noqa: E402

CSV = "data/btc_usd_5y_1d.csv"
SIZE_FRACTION = 0.05
TRAIN_FRAC = 0.6
WARMUP = 200
PPY = 365


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV, index_col=0, parse_dates=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()


def signals_with_warmup(df_full, start, end, fn):
    a = max(0, start - WARMUP)
    full_signals = fn(df_full.iloc[a:end])
    return df_full.iloc[start:end], full_signals.iloc[start - a:]


def main():
    df = load_data()
    split = int(len(df) * TRAIN_FRAC)
    print(f"CSV {CSV} — {len(df)} velas ({df.index[0].date()} -> {df.index[-1].date()}), "
          f"size_fraction={SIZE_FRACTION}")
    print(f"OOS: {df.index[split].date()} -> {df.index[-1].date()}")
    results = {}
    for name, fn in STRATEGIES.items():
        sliced, signals = signals_with_warmup(df, split, len(df), fn)
        res = run_backtest(sliced, signals, size_fraction=SIZE_FRACTION)
        m = compute_metrics(res["equity"], res["trades"], PPY)
        results[name] = m
        print(f"{name:<16} retorno {m['total_return_pct']:>8}%  Sharpe {m['sharpe']:>5}  "
              f"DD {m['max_drawdown_pct']:>7}%  trades {m['trades']:>3}  "
              f"win {m['win_rate_pct']:>5}%  PF {m['profit_factor']:>6}")
    with open("results/backtest_sizing05.json", "w") as f:
        json.dump({"size_fraction": SIZE_FRACTION, "csv": CSV,
                   "test_results": results}, f, indent=2)
    print("-> results/backtest_sizing05.json guardado")


if __name__ == "__main__":
    main()
