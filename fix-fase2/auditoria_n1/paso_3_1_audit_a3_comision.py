"""Paso 3.1 — AUDIT-A3: dimensionalidad de la comision. (criterio BLOQUEANTE)

AUDIT-S3 de fix-fase2/docs/AUDIT_BRIEF.md, sospecha del builder 2026-10-05:
"cost = (entry_price + exit_price) * size * commission. Verificar
dimensionalidad: size ya es notional/price (cantidad de activo), ¿el coste
deberia ser qty * price * commission por lado? Confirmar que comision +
slippage no se aplican dos veces al mismo lado". Criterio AUDIT-A3: verificado
dimensionalmente, con test numerico de un trade manual. BLOQUEA.

Nunca tuvo script. Este es ese script. Un trade manual con la respuesta
calculada aparte, a mano, y seis comprobaciones:

  1. El pnl del backtester coincide con el calculado a mano (exacto).
  2. El coste es comision por lado sobre el nominal de cada lado.
  3. El slippage se aplica exactamente UNA vez por lado.
  4. El coste escala con el nominal, no con el capital total.
  5. Poner comision=0 cambia el pnl en exactamente el coste (no hay doble
     contabilizacion escondida en otro sitio).
  6. Las cifras cableadas son las que el expediente declara (0.001 / 0.0005).

Sintetico DECLARADO como tal.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_1_audit_a3_comision.py
"""
import inspect
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
import backtester  # noqa: E402
from backtester import run_backtest  # noqa: E402

COMM, SLIP = 0.001, 0.0005
fallos = []


def ok(cond, titulo, detalle=""):
    print(f"  [{'OK  ' if cond else 'FALLA'}] {titulo}")
    if detalle:
        for linea in detalle.strip().splitlines():
            print(f"          {linea}")
    if not cond:
        fallos.append(titulo)


OPEN = [100.0, 100.0, 200.0, 210.0, 220.0, 250.0]
HIGH = [101.0, 101.0, 205.0, 215.0, 225.0, 255.0]
LOW = [99.0, 99.0, 195.0, 205.0, 215.0, 245.0]
CLOSE = [100.0, 100.0, 202.0, 212.0, 222.0, 252.0]
N = len(OPEN)
df = pd.DataFrame({"open": OPEN, "high": HIGH, "low": LOW, "close": CLOSE,
                   "volume": [1.0] * N},
                  index=pd.date_range("2026-01-01", periods=N, freq="D"))
sig = pd.DataFrame({"entry_long": [False, True] + [False] * (N - 2),
                    "entry_short": [False] * N,
                    "stop_loss": [np.nan] * N, "take_profit": [np.nan] * N,
                    "trailing_ma_period": [np.nan] * N})


def manual(size_fraction, comm=COMM, slip=SLIP):
    """La respuesta, calculada aparte. Largo: señal en vela 1 -> fill en
    open[2]; cierra por end_of_data en close[-1]."""
    cash = 1.0
    entry = OPEN[2] * (1 + slip)
    qty = (cash * size_fraction) / entry
    exit_ = CLOSE[-1] * (1 - slip)
    gross = (exit_ - entry) * qty
    coste_entrada = qty * entry * comm
    coste_salida = qty * exit_ * comm
    return {"entry": entry, "qty": qty, "exit": exit_, "gross": gross,
            "coste_entrada": coste_entrada, "coste_salida": coste_salida,
            "coste": coste_entrada + coste_salida,
            "pnl": gross - (coste_entrada + coste_salida)}


print("=" * 74)
print("PASO 3.1 — AUDIT-A3: dimensionalidad de la comision (BLOQUEANTE)")
print("=" * 74)
print("Serie sintetica DECLARADA. Un unico trade largo, cierre end_of_data.")
print()

m = manual(1.0)
res = run_backtest(df, sig, commission=COMM, slippage=SLIP, size_fraction=1.0)
t = res["trades"][0]
coste_obs = (t.entry_price + t.exit_price) * t.size * COMM

print("Trade calculado a mano (size_fraction=1.0, capital inicial 1.0):")
print(f"    entrada  = open[2]*(1+s)  = {OPEN[2]} * {1+SLIP} = {m['entry']!r}")
print(f"    cantidad = 1.0/entrada                   = {m['qty']!r}")
print(f"    salida   = close[-1]*(1-s) = {CLOSE[-1]} * {1-SLIP} = {m['exit']!r}")
print(f"    bruto    = (salida-entrada)*cantidad     = {m['gross']!r}")
print(f"    coste    = cant*entrada*c + cant*salida*c = "
      f"{m['coste_entrada']!r} + {m['coste_salida']!r}")
print(f"             = {m['coste']!r}")
print(f"    pnl      = bruto - coste                 = {m['pnl']!r}")
print()
print("Trade del backtester:")
print(f"    entrada {t.entry_price!r}  cantidad {t.size!r}")
print(f"    salida  {t.exit_price!r}  motivo {t.reason}")
print(f"    pnl     {t.pnl!r}")
print()

print("Prueba 1 — pnl del backtester vs calculado a mano")
ok(abs(t.pnl - m["pnl"]) < 1e-15,
   "coinciden a precision de float",
   f"diferencia = {abs(t.pnl - m['pnl']):.3e}")

print("\nPrueba 2 — ¿es comision por lado sobre el nominal de cada lado?")
ok(abs(coste_obs - m["coste"]) < 1e-18
   and abs(coste_obs - (t.size * t.entry_price * COMM
                        + t.size * t.exit_price * COMM)) < 1e-18,
   "(entrada+salida)*cantidad*c == cant*entrada*c + cant*salida*c",
   f"nominal entrada {t.size*t.entry_price!r} -> coste {t.size*t.entry_price*COMM!r}\n"
   f"nominal salida  {t.size*t.exit_price!r} -> coste {t.size*t.exit_price*COMM!r}\n"
   f"coste total     {coste_obs!r}\n"
   "Es decir: AUDIT-S3 preguntaba si deberia ser qty*price*comm por lado. Lo es.")

print("\nPrueba 3 — ¿el slippage se aplica una sola vez por lado?")
ratio_e = t.entry_price / OPEN[2]
ratio_s = t.exit_price / CLOSE[-1]
ok(abs(ratio_e - (1 + SLIP)) < 1e-15 and abs(ratio_s - (1 - SLIP)) < 1e-15,
   "entrada lleva (1+s) exacto y salida (1-s) exacto, no (1+s)^2",
   f"entrada/open[2]   = {ratio_e!r}  (1+s = {1+SLIP})\n"
   f"salida/close[-1]  = {ratio_s!r}  (1-s = {1-SLIP})\n"
   f"si fuese doble    = {(1+SLIP)**2}")

print("\nPrueba 4 — ¿el coste escala con el nominal o con el capital total?")
res_h = run_backtest(df, sig, commission=COMM, slippage=SLIP,
                     size_fraction=0.5)
th = res_h["trades"][0]
coste_h = (th.entry_price + th.exit_price) * th.size * COMM
ok(abs(th.size / t.size - 0.5) < 1e-15
   and abs(coste_h / coste_obs - 0.5) < 1e-12,
   "al medio nominal, medio coste (lineal en el nominal)",
   f"cantidad  {t.size!r} -> {th.size!r}  (ratio {th.size/t.size!r})\n"
   f"coste     {coste_obs!r} -> {coste_h!r}  (ratio {coste_h/coste_obs!r})\n"
   "Si el coste fuese sobre el capital total, el ratio seria 1.0, no 0.5.")

print("\nPrueba 5 — comision=0 debe cambiar el pnl en exactamente el coste")
res0 = run_backtest(df, sig, commission=0.0, slippage=SLIP, size_fraction=1.0)
t0 = res0["trades"][0]
ok(abs((t0.pnl - t.pnl) - coste_obs) < 1e-15,
   "no hay comision cobrada en ningun otro sitio del bucle",
   f"pnl con comision  {t.pnl!r}\npnl sin comision  {t0.pnl!r}\n"
   f"diferencia        {t0.pnl - t.pnl!r}\ncoste esperado    {coste_obs!r}")

print("\nPrueba 6 — las cifras cableadas son las que declara el expediente")
firma = inspect.signature(backtester.run_backtest).parameters
c_def = firma["commission"].default
s_def = firma["slippage"].default
ok(c_def == 0.001 and s_def == 0.0005,
   "backtester.run_backtest: commission=0.001, slippage=0.0005 por defecto",
   f"commission = {c_def}\nslippage   = {s_def}\n"
   "AUDIT_BRIEF.md §6: 'Costes: 0.1% comision + 0.05% slippage por lado'")

print()
print("=" * 74)
if fallos:
    print(f"AUDIT-A3: NO RESUELTO — {len(fallos)} prueba(s) fallan:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("AUDIT-A3: RESUELTO (6/6)")
print("La comision es dimensionalmente correcta: un cobro por lado sobre el")
print("nominal de ese lado, lineal en el nominal y no en el capital. El")
print("slippage entra una sola vez por lado, en el precio. No hay doble")
print("contabilizacion. El criterio bloqueante AUDIT-A3 queda cerrado.")
print("backtester.py:126 y :153 (coste), :71/:120/:149 (slippage)")
sys.exit(0)
