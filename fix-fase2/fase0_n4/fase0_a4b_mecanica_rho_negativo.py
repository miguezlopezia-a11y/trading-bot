"""A-4 (cont): por que rho = -0.4997 en tsmom_365."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "src")
from strategies import STRATEGIES
from backtester import run_backtest

df = pd.read_csv("data/btc_usd_5y_1d.csv", index_col=0, parse_dates=True)
df = df.rename(columns=str.lower)[["open","high","low","close","volume"]].dropna()
split = int(len(df)*0.6); a = max(0, split-200)
sig = STRATEGIES["tsmom_365"](df.iloc[a:])
res = run_backtest(df.iloc[split:], sig.iloc[split-a:], size_fraction=0.05)
r = res["equity"].pct_change().dropna()
nz = r[r != 0.0]
print(f"retornos diarios totales : {len(r)}")
print(f"retornos EXACTAMENTE cero: {int((r==0.0).sum())}  ({(r==0.0).mean()*100:.2f}%)")
print(f"retornos no cero         : {len(nz)}")
print("los no cero, con fecha:")
for d_, v in nz.items():
    print(f"   {d_.date()}  {v:+.8f}")
print()
print(f"rho lag-1 de la serie completa : {np.corrcoef(r.values[:-1], r.values[1:])[0,1]:.6f}")
print()
print("Mecanica: una serie de ceros con un UNICO par de valores no nulos de")
print("signo opuesto en dias consecutivos tiene autocorrelacion lag-1 ~ -0.5")
print("por construccion. Demostracion con una serie sintetica del mismo tamano:")
for pair in [(+1,-1), (+1,+1), (+2,-1)]:
    s = np.zeros(730); s[400] = pair[0]; s[401] = pair[1]
    print(f"   ceros + ({pair[0]:+d},{pair[1]:+d}) consecutivos -> rho = "
          f"{np.corrcoef(s[:-1], s[1:])[0,1]:+.6f}")
