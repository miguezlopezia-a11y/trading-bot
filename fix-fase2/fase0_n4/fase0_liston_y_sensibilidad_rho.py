"""Fase 0 N4 - reproducir el liston 1.312 con una implementacion propia
(statistics.NormalDist, sin importar nada de src/), y comprobar si el
n_obs_eff de las 11 variantes entra o no en el liston."""
import json, math
from statistics import NormalDist
import numpy as np

G = 0.5772156649015329
ND = NormalDist()

def emax(N):
    if N <= 1: return 0.0
    z1 = ND.inv_cdf(1 - 1.0/N); z2 = ND.inv_cdf(1 - 1.0/(N*math.e))
    return (1-G)*z1 + G*z2

def psr(sr, T, sr0, skew, kurt):
    num = (sr - sr0) * math.sqrt(T - 1)
    den = math.sqrt(max(1e-18, 1 - skew*sr + (kurt-1)/4.0*sr*sr))
    return ND.cdf(num/den)

def liston(N, V, T, skew, kurt, conf=0.95):
    sr0 = math.sqrt(V)*emax(N)
    if psr(sr0, T, sr0, skew, kurt) >= conf: return sr0, sr0
    lo, hi = sr0, sr0 + 2.0
    for _ in range(200):
        mid = (lo+hi)/2
        if psr(mid, T, sr0, skew, kurt) >= conf: hi = mid
        else: lo = mid
    return (lo+hi)/2, sr0

V12 = 0.0007021947704551833
print("=== reproduccion del liston con implementacion independiente ===")
sr, sr0 = liston(12, V12, 4336, 1.037, 31.999)
print(f"N=12 V=0.00070219 T=4336 skew=1.037 kurt=31.999")
print(f"  SR0 diario       : {sr0:.5f}   (publicado 0.04412)")
print(f"  liston diario    : {sr:.6f}")
print(f"  liston ANUAL     : {sr*math.sqrt(365):.4f}   (publicado 1.312)")
print(f"  DSR del observado: {psr(1.008/math.sqrt(365), 4336, sr0, 1.037, 31.999):.4f}  (publicado 0.7191)")
print()
print("=== el n_obs_eff de las 11 NO entra en el liston: demostracion ===")
d = json.load(open("results/rigor_estadistico.json"))
s11 = [v["sharpe_per"] for v in d["variantes"].values()]
print("Los sharpe_per de las 11 son mean/std de los retornos diarios: no")
print("llevan ningun factor sqrt(T) ni T_eff. Comprobacion aritmetica:")
import sys; sys.path.insert(0,"src")
# recalculo de un sharpe_per a mano, sin T
print(f"  V(11, ddof=1) con los sharpe_per del JSON = {np.var(s11, ddof=1):.16f}")
print(f"  V que usa Fase B (12 trials)              = {V12:.16f}")
print("  => forzar rho=0 cambia n_obs_eff de las 11, NO cambia sus sharpe_per,")
print("     por tanto NO cambia V, por tanto NO cambia el liston.")
print()
print("=== la UNICA sensibilidad real a rho que mueve el liston: el T del portfolio ===")
for T, etq in [(4336, "AR(1) aplicado (el publicado)"), (4403, "rho forzado a 0")]:
    sr_, sr0_ = liston(12, V12, T, 1.037, 31.999)
    dsr_ = psr(1.008/math.sqrt(365), T, sr0_, 1.037, 31.999)
    print(f"  T={T:5d} ({etq:30s}) liston anual {sr_*math.sqrt(365):.4f}  DSR {dsr_:.4f}")
