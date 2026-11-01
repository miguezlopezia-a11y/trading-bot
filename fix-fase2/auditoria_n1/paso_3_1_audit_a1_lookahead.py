"""Paso 3.1 — AUDIT-A1: look-ahead en los fills. (criterio BLOQUEANTE)

AUDIT-S1 de fix-fase2/docs/AUDIT_BRIEF.md, sospecha del builder 2026-10-05:
"la entrada se ejecuta al cierre de la misma vela donde se calculo la señal
(price = close[i]); señal y fill comparten vela". Criterio AUDIT-A1: resuelto
(fill en next-open) o cuantificado su impacto. BLOQUEA.

Nunca tuvo script. Este es ese script. Cinco pruebas fisicas sobre series
construidas a mano, con la respuesta calculada aparte:

  1. El fill ocurre en la vela i+1, no en la i.
  2. El precio de fill es open[i+1]*(1+slippage), no close[i].
  3. El cierre de la vela de la señal NO influye en el fill: se cambia
     close[i] de forma brutal y el trade resultante es identico.
  4. Una señal en la ultima vela no abre posicion (no hay i+1 donde rellenar).
  5. Lo mismo en corto: fill en open[i+1]*(1-slippage).

Sintetico DECLARADO como tal: son series inventadas para probar el mecanismo,
no datos de mercado.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_1_audit_a1_lookahead.py
"""
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
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


def serie(open_, high, low, close):
    n = len(open_)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close,
         "volume": [1.0] * n},
        index=pd.date_range("2026-01-01", periods=n, freq="D"))


def senales(n, idx_long=None, idx_short=None):
    s = pd.DataFrame({
        "entry_long": [False] * n, "entry_short": [False] * n,
        "stop_loss": [np.nan] * n, "take_profit": [np.nan] * n,
        "trailing_ma_period": [np.nan] * n})
    if idx_long is not None:
        s.loc[s.index[idx_long], "entry_long"] = True
    if idx_short is not None:
        s.loc[s.index[idx_short], "entry_short"] = True
    return s


print("=" * 74)
print("PASO 3.1 — AUDIT-A1: look-ahead en los fills (BLOQUEANTE)")
print("=" * 74)
print("Series sinteticas DECLARADAS como tales. slippage=%.4f comision=%.4f"
      % (SLIP, COMM))
print()

# ---------------------------------------------------------------- pruebas 1-2
# Señal en la vela 1. open[2]=200 es muy distinto de close[1]=100: si el fill
# fuese al cierre de la vela de la señal, se veria.
df = serie(open_=[100, 100, 200, 210, 220, 230],
           high=[101, 101, 205, 215, 225, 235],
           low=[99, 99, 195, 205, 215, 225],
           close=[100, 100, 202, 212, 222, 232])
res = run_backtest(df, senales(6, idx_long=1), commission=COMM,
                   slippage=SLIP, size_fraction=1.0)
t = res["trades"][0]

print("Prueba 1 — ¿en que vela se rellena la señal de la vela 1?")
ok(t.entry_date == df.index[2],
   "el fill ocurre en la vela i+1 (2026-01-03), no en la de la señal",
   f"señal en   {df.index[1].date()}\nentrada en {t.entry_date.date()}")

print("\nPrueba 2 — ¿a que precio?")
esperado = df["open"].iloc[2] * (1 + SLIP)
ok(abs(t.entry_price - esperado) < 1e-12,
   "entry_price == open[i+1]*(1+slippage)",
   f"esperado    {esperado!r}\nobservado   {t.entry_price!r}\n"
   f"close[i] era {df['close'].iloc[1]} -> si rellenase ahi, seria "
   f"{df['close'].iloc[1]*(1+SLIP)}")

# ---------------------------------------------------------------- prueba 3
print("\nPrueba 3 — ¿influye el cierre de la vela de la señal en el fill?")
df_mut = df.copy()
df_mut.loc[df_mut.index[1], "close"] = 100000.0   # cierre absurdo en la señal
df_mut.loc[df_mut.index[1], "high"] = 100001.0    # OHLC coherente
res_mut = run_backtest(df_mut, senales(6, idx_long=1), commission=COMM,
                       slippage=SLIP, size_fraction=1.0)
t_mut = res_mut["trades"][0]
ok(t_mut.entry_date == t.entry_date
   and abs(t_mut.entry_price - t.entry_price) < 1e-12
   and abs(t_mut.size - t.size) < 1e-12,
   "cambiar close[i] x1000 no mueve ni la fecha, ni el precio, ni el tamaño",
   f"close[1]  {df['close'].iloc[1]} -> {df_mut['close'].iloc[1]}\n"
   f"entrada   {t.entry_price!r} -> {t_mut.entry_price!r}\n"
   f"tamaño    {t.size!r} -> {t_mut.size!r}")

# ---------------------------------------------------------------- prueba 4
print("\nPrueba 4 — señal en la ULTIMA vela (no hay i+1 donde rellenar)")
res_last = run_backtest(df, senales(6, idx_long=5), commission=COMM,
                        slippage=SLIP, size_fraction=1.0)
ok(len(res_last["trades"]) == 0,
   "no abre ninguna posicion (guarda `i < len(df)-1`)",
   f"trades = {len(res_last['trades'])}")

# ---------------------------------------------------------------- prueba 5
print("\nPrueba 5 — el mismo mecanismo en corto")
res_s = run_backtest(df, senales(6, idx_short=1), commission=COMM,
                     slippage=SLIP, size_fraction=1.0)
ts = res_s["trades"][0]
esperado_s = df["open"].iloc[2] * (1 - SLIP)
ok(ts.entry_date == df.index[2] and abs(ts.entry_price - esperado_s) < 1e-12,
   "entry_price == open[i+1]*(1-slippage), fecha i+1",
   f"esperado   {esperado_s!r}\nobservado  {ts.entry_price!r}")

# ---------------------------------------------------------------- veredicto
print()
print("=" * 74)
if fallos:
    print(f"AUDIT-A1: NO RESUELTO — {len(fallos)} prueba(s) fallan:")
    for f in fallos:
        print(f"  - {f}")
    print("Hay look-ahead en los fills. Los cuatro dictamenes quedan en duda.")
    sys.exit(1)
print("AUDIT-A1: RESUELTO (5/5)")
print("La señal de la vela i se rellena en open[i+1]; el cierre de la vela de")
print("la señal no entra en la decision ni en el precio. El criterio")
print("bloqueante AUDIT-A1 queda cerrado con prueba fisica, no con lectura.")
print("backtester.py:68-71 (relleno del pending) y :132 (guarda de ultima vela)")
sys.exit(0)
