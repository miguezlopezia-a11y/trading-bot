import sys
sys.path.insert(0, "src")
import numpy as np
from strategies import STRATEGIES
from backtester import run_backtest, compute_metrics
from run_backtest import load_data, signals_with_warmup

df = load_data()
split = int(len(df) * 0.6)
test_data, sig = signals_with_warmup(df, split, len(df), STRATEGIES["ma_cross"])

print(f"OOS: {test_data.index[0].date()} -> {test_data.index[-1].date()}  "
      f"({len(test_data)} velas, {len(test_data)/365.25:.2f} anios)")

res = run_backtest(test_data, sig)
trades = res["trades"]
m = compute_metrics(res["equity"], trades, 365)
print(f"n_trades={len(trades)}  pf_real={m['profit_factor']}  sharpe={m['sharpe']}")

wins = [t for t in trades if t.pnl > 0]
losses = [t for t in trades if t.pnl <= 0]
gross_win = sum(t.pnl for t in wins)
gross_loss = abs(sum(t.pnl for t in losses))
print(f"gross_win={gross_win:.4f}  gross_loss={gross_loss:.4f}")

best = max(trades, key=lambda t: t.pnl)
print(f"mejor trade: pnl={best.pnl:.4f}  reason={best.reason}  entry={best.entry_date}")

gross_win_sin_mejor = gross_win - best.pnl if best.pnl > 0 else gross_win
pf_sin_mejor = gross_win_sin_mejor / gross_loss if gross_loss > 0 else float("inf")
print(f"PF sin el mejor trade = {pf_sin_mejor:.3f}")

years = len(test_data) / 365.25
t_stat = m["sharpe"] * np.sqrt(years)
print(f"anios OOS reales = {years:.3f}  t-stat = sharpe*sqrt(anios) = {t_stat:.3f}")
