import json, math, sys
from statistics import NormalDist
import numpy as np, pandas as pd
sys.path.insert(0,"src")
from strategies import STRATEGIES
from backtester import run_backtest
G=0.5772156649015329; ND=NormalDist()
def emax(N):
    if N<=1: return 0.0
    return (1-G)*ND.inv_cdf(1-1.0/N)+G*ND.inv_cdf(1-1.0/(N*math.e))
def psr(sr,T,sr0,sk,ku):
    return ND.cdf((sr-sr0)*math.sqrt(T-1)/math.sqrt(max(1e-18,1-sk*sr+(ku-1)/4*sr*sr)))
def liston(N,V,T,sk,ku,conf=0.95):
    sr0=math.sqrt(V)*emax(N)
    if psr(sr0,T,sr0,sk,ku)>=conf: return sr0,sr0
    lo,hi=sr0,sr0+2.0
    for _ in range(200):
        m=(lo+hi)/2
        if psr(m,T,sr0,sk,ku)>=conf: hi=m
        else: lo=m
    return (lo+hi)/2,sr0

d=json.load(open("results/rigor_estadistico.json"))
s11=[v["sharpe_per"] for v in d["variantes"].values()]
eq=pd.read_csv("results/portfolio_equity.csv",index_col=0,parse_dates=True).iloc[:,0]
r=eq.pct_change().dropna().values
sp=float(r.mean()/r.std())
s12=s11+[sp]; V12=float(np.var(s12,ddof=1))

print("=== (2) el fichero correcto para B-03: sizing y origen de datos ===")
b=json.load(open("../results/backtest_sizing05.json"))
print(f"  backtest_sizing05.json: size_fraction={b['size_fraction']}  csv={b['csv']}")
print("  sharpes:", {k: v["sharpe"] for k, v in b["test_results"].items()})
b2=json.load(open("../results/backtest_summary.json"))
print("  backtest_summary.json (sizing 0.95 por defecto, datos descargados):")
print("  sharpes:", {k: v["sharpe"] for k, v in b2["test_results"].items()})
print(f"  ma_cross de Fase A anualizado: {0.04228845931653596*math.sqrt(365):.4f}"
      f"  -> redondea a {round(0.04228845931653596*math.sqrt(365),2)}"
      "  (sizing05 dice 0.81; summary dice 0.80)")

print()
print("=== (7) la causa del 0.7187 vs 0.7191 ===")
_,sr0=liston(12,V12,4336,1.037,31.999)
print(f"  con sharpe exacto {sp!r} -> DSR {psr(sp,4336,sr0,1.037,31.999):.6f}")
print(f"  con 1.008/sqrt(365)                 -> DSR {psr(1.008/math.sqrt(365),4336,sr0,1.037,31.999):.6f}")
print("  publicado: 0.7191")

print()
print("=== (6) ¿anualizar da el mismo liston? ===")
Va=V12*365
_,sr0a=liston(12,Va,4336,1.037,31.999)
print(f"  SR0 diario            : {sr0:.6f}")
print(f"  SR0 de V anual        : {sr0a:.6f}   /sqrt(365) = {sr0a/math.sqrt(365):.6f}")
la,_=liston(12,V12,4336,1.037,31.999)
print(f"  liston anual via V diaria : {la*math.sqrt(365):.4f}")
# reconvertido: resolver en unidades anuales es solo reescalar; comprobacion directa
print(f"  SR0 anual / SR0 diario    : {sr0a/sr0:.6f}  (sqrt(365)={math.sqrt(365):.6f})")

print()
print("=== (3) magnitud de B-03: las tres estrategias omitidas ===")
df=pd.read_csv("data/btc_usd_5y_1d.csv",index_col=0,parse_dates=True)
df=df.rename(columns=str.lower)[["open","high","low","close","volume"]].dropna()
split=int(len(df)*0.6); a=max(0,split-200)
extra=[]
for n in ["mean_reversion","breakout","trend_following"]:
    sig=STRATEGIES[n](df.iloc[a:])
    res=run_backtest(df.iloc[split:],sig.iloc[split-a:],size_fraction=0.05)
    rr=res["equity"].pct_change().dropna().values
    sd=float(rr.mean()/rr.std()); extra.append(sd)
    print(f"  {n:18s} sharpe_diario={sd:+.8f} anual={sd*math.sqrt(365):+.4f} trades={len(res['trades'])}")
s15=s12+extra; V15=float(np.var(s15,ddof=1))
for N,V,etq in [(12,V12,"expediente: 11+portfolio"),(15,V15,"11+portfolio+3 extra"),(12,V15,"V de 15, N=12 fijo"),(15,V12,"V de 12, N=15")]:
    L,S=liston(N,V,4336,1.037,31.999)
    print(f"  N={N:2d} V={V:.8f} SR0={S:.5f} liston_anual={L*math.sqrt(365):.4f}  {etq}")

print()
print("=== (12) el eje 'dias con posicion' aplicado al propio portfolio ===")
rs=pd.Series(r); act=rs[rs!=0.0]
rho_a=np.corrcoef(act.values[:-1],act.values[1:])[0,1]
Ta=len(act)*(1-min(max(rho_a,-0.95),0.95))/(1+min(max(rho_a,-0.95),0.95))
sa=float(act.mean()/act.std())
print(f"  T completo {len(r)}  ceros {int((rs==0).sum())} ({(rs==0).mean()*100:.2f}%)")
print(f"  T activos  {len(act)}  rho {rho_a:+.5f}  T_eff {int(Ta)}  skew {act.skew():.3f} kurt {act.kurt()+3:.3f}")
print(f"  sharpe anual sobre dias activos: {sa*math.sqrt(365):.4f}  (periodo completo: {sp*math.sqrt(365):.4f})")
L,_=liston(12,V12,int(Ta),float(act.skew()),float(act.kurt()+3))
print(f"  liston con T=dias activos: {L*math.sqrt(365):.4f}   (publicado 1.3118)")
