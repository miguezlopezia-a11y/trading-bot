import sys
sys.path.insert(0, "src")
import importlib.util

spec2 = importlib.util.spec_from_file_location("bt2", "src/backtester_paso2_ref.py")
bt2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(bt2)

from backtester import run_backtest as run_h1, compute_metrics
from strategies import STRATEGIES
from run_backtest import load_data, signals_with_warmup

df = load_data()
split = int(len(df) * 0.6)
data, sig = signals_with_warmup(df, 0, split, STRATEGIES["ma_cross"])

res_old = bt2.run_backtest(data, sig)
res_new = run_h1(data, sig)

old_trades = res_old["trades"]
new_trades = res_new["trades"]
print(f"n_trades old={len(old_trades)} new={len(new_trades)}")

ok = True
for i, (to, tn) in enumerate(zip(old_trades, new_trades)):
    if abs(to.pnl - tn.pnl) > 1e-12 or to.exit_date != tn.exit_date:
        ok = False
        print(f"DIVERGE trade {i}: old.pnl={to.pnl} new.pnl={tn.pnl} old.exit={to.exit_date} new.exit={tn.exit_date}")

eq_old_final = res_old["equity"].iloc[-1]
eq_new_final = res_new["equity"].iloc[-1]
print(f"equity_final old={eq_old_final:.8f} new={eq_new_final:.8f} diff={abs(eq_old_final-eq_new_final):.2e}")

for t in new_trades[:3] + new_trades[-3:]:
    pass

print("INVARIANTE:", "OK" if ok and abs(eq_old_final - eq_new_final) < 1e-9 else "FALLO")
