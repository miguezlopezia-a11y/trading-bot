"""Fase 0 N4 - A-4: el signo del ajuste AR(1) y el 2188 de tsmom_365."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES
from backtester import run_backtest

PPY, TRAIN_FRAC, WARMUP, SIZE = 365, 0.6, 200, 0.05
VARIANTES = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
             "sma_timing_50", "sma_timing_100", "sma_timing_304",
             "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]

df = pd.read_csv("data/btc_usd_5y_1d.csv", index_col=0, parse_dates=True)
df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
split = int(len(df) * TRAIN_FRAC)
print(f"velas totales {len(df)}  split {split}  OOS filas {len(df)-split}")
print()
print(f"{'variante':24s} {'T':>5s} {'rho':>9s} {'T_eff':>8s} {'int':>6s} "
      f"{'T_eff/T':>8s} {'trades':>7s} {'exp%':>6s}")
print("-" * 86)
rows = []
for name in VARIANTES:
    fn = STRATEGIES[name]
    a = max(0, split - WARMUP)
    sig = fn(df.iloc[a:])
    res = run_backtest(df.iloc[split:], sig.iloc[split - a:], size_fraction=SIZE)
    r = res["equity"].pct_change().dropna().values
    r = r[~np.isnan(r)]
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho_c = min(max(rho, -0.95), 0.95)
    teff = len(r) * (1 - rho_c) / (1 + rho_c)
    ntr = len(res.get("trades", []))
    # exposicion: dias con equity moviendose (proxy via posicion si existe)
    exp = float(np.mean(r != 0.0)) * 100
    rows.append((name, len(r), rho, teff, ntr, exp))
    print(f"{name:24s} {len(r):5d} {rho:9.5f} {teff:8.1f} {int(teff):6d} "
          f"{teff/len(r):8.3f} {ntr:7d} {exp:6.1f}")

print()
print("=== despeje analitico para tsmom_365 ===")
n, target = 730, 2188
# T_eff = n(1-rho)/(1+rho) = target  ->  rho = (n-target)/(n+target)
rho_req = (n - target) / (n + target)
print(f"con T={n} y T_eff={target}:  rho necesario = {rho_req:.6f}")
print(f"comprobacion: {n}*(1-{rho_req:.6f})/(1+{rho_req:.6f}) = "
      f"{n*(1-rho_req)/(1+rho_req):.2f}")
print()
print("=== si se fuerza rho=0 (sin ajuste AR(1)) ===")
for name, n_, rho, teff, ntr, exp in rows:
    print(f"{name:24s} T_eff AR(1) {int(teff):6d} -> rho=0 daria {n_:6d} "
          f"(factor {teff/n_:.3f})")
