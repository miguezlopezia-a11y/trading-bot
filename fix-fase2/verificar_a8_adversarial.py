import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
import yfinance as yf
from backtester import run_backtest, compute_metrics

df = yf.download("BTC-USD", period="5y", interval="1d", auto_adjust=True, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()


def random_strategy(data, seed, p_entry=0.05, stop_pct=0.03, tp_pct=0.03):
    rng = np.random.default_rng(seed)
    n = len(data)
    coin = rng.random(n)
    direction = rng.random(n)
    out = pd.DataFrame(index=data.index)
    want_entry = coin < p_entry
    out["entry_long"] = want_entry & (direction < 0.5)
    out["entry_short"] = want_entry & (direction >= 0.5)
    close = data["close"].values
    out["stop_loss"] = np.where(out["entry_long"], close * (1 - stop_pct),
                        np.where(out["entry_short"], close * (1 + stop_pct), np.nan))
    out["take_profit"] = np.where(out["entry_long"], close * (1 + tp_pct),
                          np.where(out["entry_short"], close * (1 - tp_pct), np.nan))
    out["trailing_ma_period"] = None
    return out


returns, sharpes, trade_counts = [], [], []
for seed in range(30):
    signals = random_strategy(df, seed)
    res = run_backtest(df, signals)
    m = compute_metrics(res["equity"], res["trades"], 365)
    returns.append(m["total_return_pct"])
    sharpes.append(m["sharpe"])
    trade_counts.append(m["trades"])

returns = np.array(returns)
print(f"seeds=30  trades_prom={np.mean(trade_counts):.1f}")
print(f"retorno: media={returns.mean():.3f}%  mediana={np.median(returns):.3f}%  "
      f"min={returns.min():.3f}%  max={returns.max():.3f}%  std={returns.std():.3f}%")
print(f"sharpe:  media={np.mean(sharpes):.3f}  mediana={np.median(sharpes):.3f}")
pos = (returns > 0).sum()
print(f"seeds con retorno positivo: {pos}/30")
print(f"t-stat aprox (media/std*sqrt(n)): {returns.mean()/returns.std()*np.sqrt(30):.3f}")
