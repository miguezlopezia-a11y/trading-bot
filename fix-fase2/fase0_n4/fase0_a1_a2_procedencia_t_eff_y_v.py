"""Fase 0 N4 - A-1 y A-2: reproducir T_eff=4336 y las dos V, sin usar
el codigo del repo para el ajuste AR(1) (reimplementado aqui a mano)."""
import json
import numpy as np
import pandas as pd

# --- A-1: T_eff del portfolio, reimplementado a mano ---
eq = pd.read_csv("results/portfolio_equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
r = eq.pct_change().dropna().values
rho = np.corrcoef(r[:-1], r[1:])[0, 1]
n = len(r)
t_eff_raw = n * (1 - rho) / (1 + rho)
print("=== A-1 : T_eff del portfolio (reimplementado) ===")
print(f"dias de equity          : {len(eq)}")
print(f"retornos diarios (T)    : {n}")
print(f"rho lag-1               : {rho!r}")
print(f"T_eff = T*(1-rho)/(1+rho): {t_eff_raw!r}")
print(f"int(T_eff)              : {int(t_eff_raw)}   <-- comparar con 4336")
print(f"skew                    : {float(pd.Series(r).skew()):.6f}  <-- vs SKEW=1.037")
print(f"kurt raw (kurt+3)       : {float(pd.Series(r).kurt())+3:.6f}  <-- vs KURT=31.999")
print(f"sharpe diario           : {r.mean()/r.std()!r}")
print(f"sharpe anual (x sqrt365): {r.mean()/r.std()*np.sqrt(365):.6f}  <-- vs 1.008")

# --- A-2: las dos V ---
print()
print("=== A-2 : las dos V ===")
d = json.load(open("results/rigor_estadistico.json"))
s11 = np.array([v["sharpe_per"] for v in d["variantes"].values()])
v11 = float(np.var(s11, ddof=1))
s_port = float(r.mean() / r.std())
s12 = np.append(s11, s_port)
v12 = float(np.var(s12, ddof=1))
print(f"V de 11 trials (Fase A)  : {v11!r}")
print(f"  JSON rigor_estadistico : {d['var_trials']!r}")
print(f"  identico?              : {v11 == d['var_trials']}")
print(f"V de 12 trials (+portf.) : {v12!r}")
print(f"  cableada en Fase B     : 0.0007021947704551833")
print(f"  diferencia             : {v12 - 0.0007021947704551833:.6e}")
print(f"Sharpe diario del portfolio anadido como trial 12: {s_port!r}")
