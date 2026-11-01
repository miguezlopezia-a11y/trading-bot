"""Paso 3.3 — Costes: agregado de rebalanceos y sensibilidad. (hallazgo A-15)

El registro nemesis ya corrigio la premisa del brief original: los costes
estan cifrados (commission 0.001, slippage 0.0005, portfolio_runner.py:39-40)
y el coste de rebalanceo SI se cobra, sobre turnover (:242). Lo que falta es
el agregado, que results/portfolio_runner.json no guarda, y la sensibilidad.

Tres partes:
  A) Cuantificar: cuantos dias rebalancean, turnover total, coste acumulado,
     y que fraccion del retorno se come. Reejecutado, no citado.
  B) Sensibilidad x1 / x2 / x5 / x10 sobre Sharpe, t y DSR. Si el edge muere
     con x2, la "SEÑAL DEBIL" es una ilusion de friccion barata.
  C) Punto de muerte: el multiplicador de costes al que el Sharpe cruza los
     umbrales que el expediente ya tiene fijados (t>3 -> 0.870 anual;
     DSR>=0.95 con N=12 -> 1.312 anual). NO se cambia ningun umbral: se usan
     los que potencia_fase_b.py ya publica.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_3_costes.py
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
os.chdir(FIX2)
import portfolio_runner as pr  # noqa: E402
from portfolio_runner import load_or_download, simulate, metrics  # noqa: E402
from rigor_estadistico import dsr, ar1_effective_n, PPY  # noqa: E402

SELLO = "20261007"
N_TRIALS = 12                 # el N del expediente (asuncion, ver 3.4)
VAR_TRIALS = 0.0007021947704551833   # la V de la bateria Fase B
UMBRAL_T3 = 0.870             # Sharpe anual para t>3, de potencia_fase_b.json
UMBRAL_DSR = 1.312            # Sharpe anual para DSR>=0.95 con N=12


def estadisticos(eq):
    r = eq.pct_change().dropna().values
    s_per = r.mean() / r.std() if r.std() > 0 else 0.0
    t_eff = int(ar1_effective_n(r))
    skew = float(pd.Series(r).skew())
    kurt = float(pd.Series(r).kurt() + 3)
    d, sr0 = dsr(s_per, t_eff, N_TRIALS, VAR_TRIALS, skew, kurt)
    return {"sharpe_anual": s_per * math.sqrt(PPY),
            "t": s_per * math.sqrt(t_eff), "dsr": d,
            "t_eff": t_eff, "skew": skew, "kurt": kurt}


print("=" * 74)
print("PASO 3.3 — costes: agregado de rebalanceos y sensibilidad")
print("=" * 74)
print(f"COMMISSION = {pr.COMMISSION}   SLIPPAGE = {pr.SLIPPAGE}   "
      f"(portfolio_runner.py:39-40)")
print(f"coste del dia = turnover * (COMMISSION + SLIPPAGE) = turnover * "
      f"{pr.COMMISSION + pr.SLIPPAGE}   (:242)")
print(f"sello congelado {SELLO} (el que reproduce Fase B, paso 3.0c)")
print()

datos = load_or_download(stamp=SELLO, verbose=False)

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — el agregado que results/portfolio_runner.json no guarda")
print("-" * 74)
res = simulate(datos)
costes = res["costes"]
eq = res["equity"]
n_dias = res["n_dias"]
tasa = pr.COMMISSION + pr.SLIPPAGE
turnover = costes / tasa                    # invirtiendo coste = turnover*tasa
dias_reb = int((turnover > 1e-12).sum())
coste_total_mult = float(np.prod(1.0 - costes.values))

print(f"  dias simulados                     {n_dias}")
print(f"  dias con rebalanceo (turnover>0)   {dias_reb}  "
      f"({100*dias_reb/n_dias:.1f}% de los dias)")
print(f"  turnover total (suma de |dw|)      {float(turnover.sum()):.4f}")
print(f"  turnover medio por dia con reb.    {float(turnover.sum())/max(dias_reb,1):.6f}")
print(f"  coste acumulado como factor        {coste_total_mult:.6f}  "
      f"-> {(1-coste_total_mult)*100:.2f}% de la equity comida por friccion")
print(f"  coste medio diario                 {float(costes.mean()):.8f}")
print(f"  coste maximo en un dia             {float(costes.max()):.8f}")
print(f"  equity final                       {float(eq.iloc[-1]):.4f}")
print()
# contrafactual: la misma simulacion con coste cero
pr.COMMISSION, pr.SLIPPAGE = 0.0, 0.0
res0 = simulate(datos)
pr.COMMISSION, pr.SLIPPAGE = 0.001, 0.0005
m_con = metrics(res["equity"], res["benchmark"])
m_sin = metrics(res0["equity"], res0["benchmark"])
print("  Contrafactual sin costes (mismos datos, misma regla):")
print(f"    retorno   {m_con['retorno_pct']:>10}%  ->  {m_sin['retorno_pct']:>10}%  "
      f"sin costes")
print(f"    Sharpe    {m_con['sharpe']:>10}   ->  {m_sin['sharpe']:>10}")
print(f"    la friccion cuesta {m_sin['retorno_pct']-m_con['retorno_pct']:.2f} puntos de")
print(f"    retorno y {m_sin['sharpe']-m_con['sharpe']:.3f} de Sharpe.")
print()
print("  -> El coste de rebalanceo SI se cobra. El miedo del brief original")
print("     ('rebalancea 10 activos a diario 4404 dias y no paga esos")
print("     ajustes') no se cumple: se paga en "
      f"{dias_reb} de {n_dias} dias.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — sensibilidad x1 / x2 / x5 / x10")
print("-" * 74)
print(f"  Umbrales del expediente (NO se cambian, son los de")
print(f"  potencia_fase_b.json): t>3 exige Sharpe {UMBRAL_T3}; DSR>=0.95 con")
print(f"  N={N_TRIALS} exige Sharpe {UMBRAL_DSR}.")
print()
print(f"  {'mult':>5} {'comision':>10} {'slippage':>10} {'retorno %':>11} "
      f"{'Sharpe':>8} {'t':>7} {'DSR':>7} {'coste acum %':>13}")
print(f"  {'-'*5} {'-'*10} {'-'*10} {'-'*11} {'-'*8} {'-'*7} {'-'*7} {'-'*13}")
tabla = {}
for mult in (1, 2, 5, 10):
    pr.COMMISSION, pr.SLIPPAGE = 0.001 * mult, 0.0005 * mult
    r = simulate(datos)
    pr.COMMISSION, pr.SLIPPAGE = 0.001, 0.0005
    m = metrics(r["equity"], r["benchmark"])
    st = estadisticos(r["equity"])
    acum = (1 - float(np.prod(1.0 - r["costes"].values))) * 100
    tabla[mult] = {**m, **st, "coste_acum_pct": acum}
    print(f"  {'x'+str(mult):>5} {0.001*mult:>10.4f} {0.0005*mult:>10.5f} "
          f"{m['retorno_pct']:>11} {st['sharpe_anual']:>8.3f} {st['t']:>7.2f} "
          f"{st['dsr']:>7.3f} {acum:>13.2f}")
print()
s1 = tabla[1]["sharpe_anual"]
print(f"  Referencia: el expediente publica Sharpe 1.008 y DSR 0.72 para")
print(f"  Fase B. Aqui x1 da Sharpe {s1:.3f} y DSR {tabla[1]['dsr']:.3f}.")
print()
for mult in (2, 5, 10):
    st = tabla[mult]
    veredicto = []
    veredicto.append("t>3 SI" if st["t"] > 3 else "t>3 NO")
    veredicto.append(f"DSR {st['dsr']:.3f}")
    veredicto.append("retorno POSITIVO" if st["retorno_pct"] > 0
                     else "retorno NEGATIVO")
    print(f"  x{mult}: Sharpe {st['sharpe_anual']:.3f} "
          f"({st['sharpe_anual']-s1:+.3f} vs x1)  " + "  ".join(veredicto))
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — a que multiplicador de costes muere el edge")
print("-" * 74)
print("  Barrido fino. Se buscan los cruces de los umbrales ya fijados.")
print()
print(f"  {'mult':>6} {'Sharpe':>8} {'t':>7} {'DSR':>7} {'retorno %':>11}")
print(f"  {'-'*6} {'-'*8} {'-'*7} {'-'*7} {'-'*11}")
barrido = {}
for mult in (1, 1.5, 2, 3, 4, 5, 7, 10, 15, 20, 30):
    pr.COMMISSION, pr.SLIPPAGE = 0.001 * mult, 0.0005 * mult
    r = simulate(datos)
    pr.COMMISSION, pr.SLIPPAGE = 0.001, 0.0005
    st = estadisticos(r["equity"])
    m = metrics(r["equity"], r["benchmark"])
    barrido[mult] = {**st, "retorno_pct": m["retorno_pct"]}
    print(f"  {'x'+str(mult):>6} {st['sharpe_anual']:>8.3f} {st['t']:>7.2f} "
          f"{st['dsr']:>7.3f} {m['retorno_pct']:>11}")
print()


def cruce(clave, umbral, mayor_es_mejor=True):
    """Primer multiplicador donde la serie cruza el umbral."""
    prev = None
    for mult in sorted(barrido):
        v = barrido[mult][clave]
        if mayor_es_mejor and v < umbral:
            return (prev, mult)
        prev = mult
    return (prev, None)


a_t, b_t = cruce("sharpe_anual", UMBRAL_T3)
a_d, b_d = cruce("sharpe_anual", UMBRAL_DSR)
a_0, b_0 = cruce("retorno_pct", 0.0)
print("  Cruces de los umbrales del expediente:")
print(f"    Sharpe {UMBRAL_DSR} (DSR>=0.95, N=12): el Sharpe ya esta por DEBAJO"
      if barrido[1]["sharpe_anual"] < UMBRAL_DSR else
      f"    Sharpe {UMBRAL_DSR} (DSR>=0.95, N=12): se cruza entre x{a_d} y x{b_d}")
print(f"      en x1 ({barrido[1]['sharpe_anual']:.3f}) — es la brecha +0.304 "
      "que el expediente ya registra, no un hallazgo nuevo.")
if b_t is None:
    print(f"    Sharpe {UMBRAL_T3} (t>3): NO se cruza ni con x30 "
          f"(x30 da {barrido[30]['sharpe_anual']:.3f})")
else:
    print(f"    Sharpe {UMBRAL_T3} (t>3): se cruza entre x{a_t} y x{b_t}")
if b_0 is None:
    print(f"    retorno 0: sigue POSITIVO hasta x30 "
          f"({barrido[30]['retorno_pct']}%)")
else:
    print(f"    retorno 0: se vuelve negativo entre x{a_0} y x{b_0}")
print()
print("=" * 74)
muere_x2 = tabla[2]["sharpe_anual"] < UMBRAL_T3
print("VEREDICTO 3.3")
print(f"  El coste de rebalanceo se cobra: {dias_reb} de {n_dias} dias, "
      f"turnover total {float(turnover.sum()):.1f},")
print(f"  {(1-coste_total_mult)*100:.2f}% de la equity. No hay Sharpe fantasma por")
print("  rebalanceo gratis.")
if muere_x2:
    print("  PERO el edge MUERE con costes x2: la 'SEÑAL DEBIL' es una ilusion")
    print("  de friccion barata. HALLAZGO.")
else:
    print(f"  Con costes x2 el Sharpe baja a {tabla[2]['sharpe_anual']:.3f} y sigue")
    print(f"  por encima del umbral de t>3 ({UMBRAL_T3}). El edge NO es una")
    print("  ilusion de friccion barata: resiste duplicar los costes.")
print("  Limite declarado: el modelo de friccion es proporcional al turnover,")
print("  sin impacto de mercado ni profundidad de libro. Un multiplicador x10")
print("  no es lo mismo que operar size grande en un activo ilíquido.")
with open(os.path.join(AQUI, "salida_3_3_costes.json"), "w") as f:
    json.dump({"sello": SELLO, "dias": n_dias, "dias_rebalanceo": dias_reb,
               "turnover_total": float(turnover.sum()),
               "coste_acumulado_pct": (1 - coste_total_mult) * 100,
               "umbral_t3": UMBRAL_T3, "umbral_dsr": UMBRAL_DSR,
               "sensibilidad": {str(k): v for k, v in tabla.items()},
               "barrido": {str(k): v for k, v in barrido.items()}},
              f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_3_costes.json')}")
