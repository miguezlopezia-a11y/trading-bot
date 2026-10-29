"""PASO 1 (H2): indicadores con prefijo de warm-up de la serie completa por slice."""
import sys
import json
import pandas as pd
import yfinance as yf

sys.path.insert(0, "src")
from strategies import STRATEGIES
from backtester import run_backtest, compute_metrics

TICKER = "BTC-USD"
INTERVAL = "1d"
YEARS = 5
TRAIN_FRAC = 0.6
WF_TRAIN, WF_TEST = 365, 90
PPY = 365
WARMUP = 200


def load_data() -> pd.DataFrame:
    df = yf.download(TICKER, period=f"{YEARS}y", interval=INTERVAL, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
    return df


def signals_with_warmup(df_full: pd.DataFrame, start: int, end: int, fn):
    a = max(0, start - WARMUP)
    full_signals = fn(df_full.iloc[a:end])
    cut = start - a
    return df_full.iloc[start:end], full_signals.iloc[cut:]


def evaluate(df_full: pd.DataFrame, start: int, end: int, label: str) -> dict:
    data = df_full.iloc[start:end]
    print(f"\n{'='*72}\n  {label}  ({data.index[0].date()} → {data.index[-1].date()}, {len(data)} velas)\n{'='*72}")
    results = {}
    for name, fn in STRATEGIES.items():
        sliced_data, signals = signals_with_warmup(df_full, start, end, fn)
        res = run_backtest(sliced_data, signals)
        m = compute_metrics(res["equity"], res["trades"], PPY)
        results[name] = m
        exits = pd.Series([t.reason for t in res["trades"]]).value_counts().to_dict() if res["trades"] else {}
        print(f"\n■ {name:<16} retorno {m['total_return_pct']:>8}%  Sharpe {m['sharpe']:>5}  "
              f"DD {m['max_drawdown_pct']:>7}%  trades {m['trades']:>3}  "
              f"win {m['win_rate_pct']:>5}%  PF {m['profit_factor']:>6}")
        print(f"  salidas: {exits}")
    return results


def walk_forward(df_full: pd.DataFrame, strategy_fn) -> list:
    folds = []
    start = 0
    while start + WF_TRAIN + WF_TEST <= len(df_full):
        test_start = start + WF_TRAIN
        test_end = start + WF_TRAIN + WF_TEST
        test_data, sig_v = signals_with_warmup(df_full, test_start, test_end, strategy_fn)
        bt_v = run_backtest(test_data, sig_v)
        r_va = compute_metrics(bt_v["equity"], bt_v["trades"], PPY)
        folds.append({"fold": len(folds) + 1, "test_start": str(test_data.index[0].date()),
                      "oos_return_pct": r_va["total_return_pct"], "oos_sharpe": r_va["sharpe"],
                      "oos_trades": r_va["trades"]})
        start += WF_TEST
    return folds


def main():
    df = load_data()
    print(f"Datos: {TICKER} {INTERVAL} — {len(df)} velas "
          f"({df.index[0].date()} → {df.index[-1].date()})")

    split = int(len(df) * TRAIN_FRAC)

    evaluate(df, 0, split, f"IN-SAMPLE (train) — {TRAIN_FRAC:.0%}")
    results = evaluate(df, split, len(df), f"OUT-OF-SAMPLE (test) — {1-TRAIN_FRAC:.0%}")

    print(f"\n{'='*72}\n  WALK-FORWARD ({WF_TRAIN}d train / {WF_TEST}d test, rueda cada {WF_TEST}d)\n{'='*72}")
    for name, fn in STRATEGIES.items():
        folds = walk_forward(df, fn)
        pos = [f for f in folds if f["oos_return_pct"] > 0]
        avg = sum(f["oos_return_pct"] for f in folds) / len(folds) if folds else 0
        print(f"\n■ {name:<16} folds {len(folds)}  positivos {len(pos)}/{len(folds)}  "
              f"retorno OOS medio {avg:>7.2f}%")
        for f in folds[:4]:
            print(f"    fold {f['fold']} ({f['test_start']}): {f['oos_return_pct']:>7.2f}%  "
                  f"Sharpe {f['oos_sharpe']:>5}  trades {f['oos_trades']}")
        if len(folds) > 4:
            print(f"    … (+{len(folds)-4} folds más)")

    with open("results/backtest_summary.json", "w") as f:
        json.dump({"test_results": results}, f, indent=2)
    print("\n→ results/backtest_summary.json guardado")


if __name__ == "__main__":
    main()
