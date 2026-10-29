import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from backtester import run_backtest, compute_metrics

dates = pd.date_range("2026-01-01", periods=6, freq="D")
df = pd.DataFrame({
    "open":  [100, 101, 105, 106, 103, 103],
    "high":  [100, 112, 105, 106, 103, 103],
    "low":   [100, 100, 99,  95,  103, 103],
    "close": [100, 108, 100, 95,  103, 103],
}, index=dates)

signals = pd.DataFrame({
    "entry_long":  [True,  False, True,  False, False, False],
    "entry_short": [False, False, False, False, False, False],
    "stop_loss":   [94.0,  np.nan, 100.0, np.nan, np.nan, np.nan],
    "take_profit": [110.0, np.nan, 112.0, np.nan, np.nan, np.nan],
    "trailing_ma_period": [None] * 6,
}, index=dates)

COMM, SLIP, FRAC = 0.001, 0.0005, 0.95

res = run_backtest(df, signals, commission=COMM, slippage=SLIP, size_fraction=FRAC)
trades = res["trades"]
eq = res["equity"]

print(f"n_trades={len(trades)}")
for t in trades:
    print(f"  {t.side} entry={t.entry_price:.6f} exit={t.exit_price:.6f} "
          f"reason={t.reason} size={t.size:.8f} pnl={t.pnl:.8f}")
print("equity curve:", [round(x, 6) for x in eq.values])

cash = 1.0
expected_trades = []

fill1 = 101 * (1 + SLIP)
qty1 = (cash * FRAC) / fill1
exit1 = 110 * (1 - SLIP)
gross1 = qty1 * (exit1 - fill1)
cost1 = (fill1 + exit1) * qty1 * COMM
pnl1 = gross1 - cost1
cash += pnl1
expected_trades.append(("long", fill1, exit1, "take_profit", pnl1))

fill2 = 106 * (1 + SLIP)
qty2 = (cash * FRAC) / fill2
exit2 = 100 * (1 - SLIP)
gross2 = qty2 * (exit2 - fill2)
cost2 = (fill2 + exit2) * qty2 * COMM
pnl2 = gross2 - cost2
cash += pnl2
expected_trades.append(("long", fill2, exit2, "stop_loss", pnl2))

print("\nEsperado a mano:")
for side, f, x, r, p in expected_trades:
    print(f"  {side} entry={f:.6f} exit={x:.6f} reason={r} pnl={p:.8f}")
print(f"cash final esperado = {cash:.8f}")
print(f"equity final real    = {eq.iloc[-1]:.8f}")
print(f"MATCH equity final: {'OK' if abs(cash - eq.iloc[-1]) < 1e-9 else 'FALLO'}")

m = compute_metrics(eq, trades, 365)
win_rate_exp = 50.0
pf_exp = pnl1 / abs(pnl2)
ret_exp = (cash / 1.0 - 1) * 100
print(f"\ncompute_metrics real: {m}")
print(f"total_return esperado={ret_exp:.4f} vs real={m['total_return_pct']}")
print(f"win_rate esperado={win_rate_exp} vs real={m['win_rate_pct']}")
print(f"profit_factor esperado={pf_exp:.4f} vs real={m['profit_factor']}")
