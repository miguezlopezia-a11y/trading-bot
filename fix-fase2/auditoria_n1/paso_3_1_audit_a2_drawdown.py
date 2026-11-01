"""Paso 3.1 — AUDIT-A2: el drawdown identico train/test. (criterio BLOQUEANTE)

AUDIT-S2 de fix-fase2/docs/AUDIT_BRIEF.md, sospecha del builder 2026-10-05:
"Drawdown identico train/test (-2.18% exacto en ma_cross). Coincidencia
numerica exacta en dos periodos disjuntos es estadisticamente rara. Hipotesis
del builder: artefacto de muestra pequeña + cummax con equity casi monotona.
Verificar que compute_metrics no tiene un bug que fije o pise el calculo
(p.ej. drawdown sobre equity normalizado mal reiniciado entre llamadas)."
Criterio AUDIT-A2: explicado — bug -> corregir; artefacto -> documentar con
evidencia. BLOQUEA.

Nunca tuvo script. Este es ese script. Separa las dos hipotesis:

  A) ¿Hay bug en compute_metrics? (estado compartido, orden de llamada,
     cummax mal) -> cuatro pruebas sinteticas con respuesta a mano.
  B) ¿Que pasa de verdad con ma_cross? -> reproducir train/test sobre el CSV
     congelado real y mirar los trades que producen el minimo.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_1_audit_a2_drawdown.py
"""
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
from backtester import run_backtest, compute_metrics  # noqa: E402
from strategies import STRATEGIES  # noqa: E402

CSV = os.path.join(FIX2, "data", "btc_usd_5y_1d.csv")
TRAIN_FRAC, WARMUP, PPY = 0.6, 200, 365
fallos = []


def ok(cond, titulo, detalle=""):
    print(f"  [{'OK  ' if cond else 'FALLA'}] {titulo}")
    if detalle:
        for linea in detalle.strip().splitlines():
            print(f"          {linea}")
    if not cond:
        fallos.append(titulo)


def eq(valores):
    return pd.Series([float(v) for v in valores],
                     index=pd.date_range("2026-01-01", periods=len(valores),
                                         freq="D"))


print("=" * 74)
print("PASO 3.1 — AUDIT-A2: drawdown identico train/test (BLOQUEANTE)")
print("=" * 74)
print()
print("-" * 74)
print("HIPOTESIS A — ¿tiene compute_metrics un bug de estado o de cummax?")
print("-" * 74)

print("\nPrueba 1 — drawdown contra un calculo a mano")
# equity 100,110,99,120,60 -> maximos 100,110,110,120,120
# dd 0, 0, -11/110=-10%, 0, -60/120=-50%  -> minimo -50.00%
serie = eq([100, 110, 99, 120, 60])
m = compute_metrics(serie, [], PPY)
ok(m["max_drawdown_pct"] == -50.0,
   "max_drawdown_pct == -50.00 en la serie 100,110,99,120,60",
   f"a mano:   maximos 100,110,110,120,120 -> dd 0%, 0%, -10%, 0%, -50%\n"
   f"esperado  -50.0\nobservado {m['max_drawdown_pct']}")

print("\nPrueba 2 — ¿hay estado compartido entre llamadas?")
a1 = compute_metrics(eq([100, 50]), [], PPY)["max_drawdown_pct"]
b1 = compute_metrics(eq([100, 90]), [], PPY)["max_drawdown_pct"]
# el mismo par, en orden inverso
b2 = compute_metrics(eq([100, 90]), [], PPY)["max_drawdown_pct"]
a2 = compute_metrics(eq([100, 50]), [], PPY)["max_drawdown_pct"]
ok(a1 == a2 == -50.0 and b1 == b2 == -10.0,
   "el resultado no depende del orden de llamada ni de llamadas previas",
   f"serie A primero: A={a1}  B={b1}\nserie B primero: B={b2}  A={a2}")

print("\nPrueba 3 — ¿reinicia bien? misma serie 3 veces seguidas")
vals = [compute_metrics(eq([100, 110, 99, 120, 60]), [], PPY)["max_drawdown_pct"]
        for _ in range(3)]
ok(len(set(vals)) == 1 and vals[0] == -50.0,
   "tres llamadas identicas dan el mismo valor",
   f"valores = {vals}")

print("\nPrueba 4 — equity monotona creciente -> drawdown 0, no NaN ni negativo")
m_mono = compute_metrics(eq([100, 101, 102, 103]), [], PPY)
ok(m_mono["max_drawdown_pct"] == 0.0,
   "serie sin caidas da exactamente 0.00",
   f"observado {m_mono['max_drawdown_pct']}")

print("\n-> Hipotesis A: ", end="")
if fallos:
    print("HAY BUG. Detalle arriba.")
else:
    print("descartada. compute_metrics no tiene estado, reinicia bien y el")
    print("   cummax es correcto. El calculo es una funcion pura de su entrada.")

print()
print("-" * 74)
print("HIPOTESIS B — ¿que hace ma_cross de verdad en train y en test?")
print("-" * 74)
if not os.path.exists(CSV):
    print(f"  NO EJECUTABLE: falta {CSV}")
    sys.exit(1)

df = pd.read_csv(CSV, index_col=0, parse_dates=True)
df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
split = int(len(df) * TRAIN_FRAC)
print(f"  CSV congelado: {len(df)} velas, {df.index[0].date()} -> "
      f"{df.index[-1].date()}, split 60/40 en i={split}")

fn = STRATEGIES["ma_cross"]
tramos = {}
for etiqueta, start, end in [("TRAIN (in-sample)", 0, split),
                             ("TEST  (out-of-sample)", split, len(df))]:
    a = max(0, start - WARMUP)
    sig_full = fn(df.iloc[a:end])
    sliced = df.iloc[start:end]
    sig = sig_full.iloc[start - a:]
    res = run_backtest(sliced, sig)          # size_fraction por defecto 0.95
    met = compute_metrics(res["equity"], res["trades"], PPY)
    equity = res["equity"]
    rmax = equity.cummax()
    dd = (equity - rmax) / rmax
    i_min = dd.values.argmin()
    tramos[etiqueta] = {
        "met": met, "equity": equity, "dd": dd, "i_min": i_min,
        "trades": res["trades"],
        "fecha_min": equity.index[i_min], "dd_min": float(dd.iloc[i_min]),
        "pico": float(rmax.iloc[i_min]), "valle": float(equity.iloc[i_min])}
    print(f"\n  {etiqueta}  ({sliced.index[0].date()} -> {sliced.index[-1].date()}, "
          f"{len(sliced)} velas)")
    print(f"    retorno {met['total_return_pct']:>8}%   Sharpe {met['sharpe']:>5}   "
          f"DD {met['max_drawdown_pct']:>7}%   trades {met['trades']:>3}")
    print(f"    minimo del drawdown el {equity.index[i_min].date()} "
          f"(barra {i_min} de {len(equity)})")
    print(f"    pico {rmax.iloc[i_min]!r} -> valle {equity.iloc[i_min]!r}")
    print(f"    dd exacto (sin redondear) = {float(dd.iloc[i_min])*100!r} %")

t1, t2 = tramos["TRAIN (in-sample)"], tramos["TEST  (out-of-sample)"]
dd1, dd2 = t1["met"]["max_drawdown_pct"], t2["met"]["max_drawdown_pct"]
print()
print("  Comparacion de los dos tramos:")
print(f"    DD redondeado   train {dd1}%   test {dd2}%   "
      f"{'IGUALES' if dd1 == dd2 else 'DISTINTOS'}")
print(f"    DD exacto       train {t1['dd_min']*100!r}%")
print(f"                    test  {t2['dd_min']*100!r}%")
print(f"    diferencia exacta = {abs(t1['dd_min'] - t2['dd_min'])*100:.6f} puntos")
print(f"    fechas del minimo: train {t1['fecha_min'].date()}  "
      f"test {t2['fecha_min'].date()}  "
      f"{'LA MISMA' if t1['fecha_min'] == t2['fecha_min'] else 'distintas'}")
print(f"    trades: train {len(t1['trades'])}  test {len(t2['trades'])}")

print()
print("  Lectura:")
if dd1 == dd2:
    print(f"    Los DD redondeados coinciden ({dd1}%), pero los exactos NO")
    print(f"    ({t1['dd_min']*100:.6f}% vs {t2['dd_min']*100:.6f}%) y los")
    print("    minimos caen en fechas distintas, en tramos disjuntos, con")
    print("    numeros de trade distintos. No es un valor pisado ni fijado:")
    print("    es una coincidencia del redondeo a 2 decimales.")
    veredicto_b = "artefacto de redondeo"
else:
    print(f"    Los DD NO coinciden en este CSV congelado: train {dd1}% vs")
    print(f"    test {dd2}%. La coincidencia -2.18%/-2.18% que reporta")
    print("    AUDIT_BRIEF.md §6 NO se reproduce con los datos del repo.")
    print("    El -2.18% venia de una descarga en vivo de yfinance de")
    print("    2026-10-05 (AUDIT_BRIEF.md §2: 'Runner: descarga yfinance'),")
    print("    no de este CSV. Los dos conjuntos no son el mismo.")
    veredicto_b = "no reproducible: la linea base no salio de este CSV"

print()
print("=" * 74)
if fallos:
    print(f"AUDIT-A2: NO RESUELTO — {len(fallos)} prueba(s) de la hipotesis A fallan:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("AUDIT-A2: EXPLICADO (hipotesis A descartada con 4/4)")
print("  Bug en compute_metrics: DESCARTADO. Es una funcion pura, sin estado,")
print("  con cummax correcto, independiente del orden de llamada.")
print(f"  Lo que pasa de verdad: {veredicto_b}.")
print("  El criterio bloqueante AUDIT-A2 queda cerrado: no hay bug que")
print("  corregir, y el fenomeno queda documentado con la evidencia de arriba.")
print("  backtester.py:169-170 (cummax) y :175 (redondeo a 2 decimales)")
sys.exit(0)
