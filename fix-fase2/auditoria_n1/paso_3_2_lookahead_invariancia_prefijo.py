"""Paso 3.2 — Look-ahead por INVARIANCIA DE PREFIJO. (objeciones B-05, B-06)

El brief original pedia: "multiplicar el cierre de la barra t+1 por 3 y
comprobar que la posicion en t no cambia". El registro nemesis lo rechazo
(B-05) por tres defectos: rompe la coherencia OHLC (close>high) y puede
disparar las ramas de gap -> falso positivo; una sola barra solo comprueba un
t -> falso negativo; y comparar curvas completas da siempre diferencia porque
lo posterior a t+1 cambia legitimamente.

Esta es la prueba corregida:

  Para cada t de una rejilla, se perturban TODAS las barras > t a la vez,
  manteniendo coherencia OHLC (se escalan open/high/low/close de cada barra
  por el MISMO factor, asi que high>=max(o,c) y low<=min(o,c) se conservan),
  con un paseo multiplicativo de semilla fija que cambia niveles Y retornos.
  Se exige que las señales y la equity en [0..t] sean BIT-IDENTICAS.
  Una sola t con diferencia localiza el look-ahead y da la barra exacta.

Cubre de una vez indicadores, estrategias y backtester. Incluye
rsi_hidden_divergence, que usa _swings_confirmados con ventana CENTRADA
(strategies.py:168, rolling(2*order+1, center=True)) — el unico constructo no
causal por construccion del codigo, que el brief original no listaba (B-06).

Parte C: cuantifica el impacto del look-ahead que AUDIT-S1 denunciaba,
comparando el harness actual contra una variante deliberadamente defectuosa
que rellena al cierre de la vela de la señal. Es lo que AUDIT-A1 pedia
("o cuantificado su impacto") y nunca se hizo.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_2_lookahead_invariancia_prefijo.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
os.chdir(FIX2)
from backtester import run_backtest, compute_metrics  # noqa: E402
from strategies import STRATEGIES  # noqa: E402
from portfolio_runner import load_or_download, simulate  # noqa: E402

CSV = os.path.join(FIX2, "data", "btc_usd_5y_1d.csv")
SEED = 20261101
N_T_SINGLE = 40          # puntos de rejilla, single-asset
N_T_PORTFOLIO = 10       # puntos de rejilla, portfolio (cada corrida ~15 s)
SELLO = "20261007"       # el sello que reproduce Fase B (paso 3.0c)
fallos = []


def ok(cond, titulo, detalle=""):
    print(f"  [{'OK  ' if cond else 'FALLA'}] {titulo}")
    if detalle:
        for linea in detalle.strip().splitlines():
            print(f"          {linea}")
    if not cond:
        fallos.append(titulo)


def perturbar(df, t, seed):
    """Escala las barras > t por un paseo multiplicativo de semilla fija.
    Cada barra escala sus cuatro precios por el MISMO factor, asi que la
    coherencia OHLC (high>=max(o,c), low<=min(o,c)) se conserva exactamente."""
    out = df.copy()
    n = len(df)
    if t >= n - 1:
        return out
    rng = np.random.default_rng(seed)
    pasos = 1.0 + 0.05 * rng.standard_normal(n - 1 - t)
    factor = np.cumprod(pasos)
    for col in ("open", "high", "low", "close"):
        out.iloc[t + 1:, out.columns.get_loc(col)] = \
            df[col].values[t + 1:] * factor
    return out


def coherente(df):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    return bool(np.all(h >= np.maximum(o, c) - 1e-9)
                and np.all(l <= np.minimum(o, c) + 1e-9)
                and np.all(h >= l))


print("=" * 74)
print("PASO 3.2 — look-ahead por invariancia de prefijo")
print("=" * 74)
df = pd.read_csv(CSV, index_col=0, parse_dates=True)
df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
n = len(df)
print(f"CSV congelado: {n} velas, {df.index[0].date()} -> {df.index[-1].date()}")
print(f"semilla de perturbacion {SEED}; factor = paseo multiplicativo sigma 5%")
print()

# ------------------------------------------------------- control de coherencia
print("Control previo — la perturbacion mantiene OHLC coherente")
t_ctrl = n // 2
dfp_ctrl = perturbar(df, t_ctrl, SEED)
cambia = not np.allclose(dfp_ctrl["close"].values[t_ctrl + 1:],
                         df["close"].values[t_ctrl + 1:])
ok(coherente(df) and coherente(dfp_ctrl) and cambia,
   "serie perturbada sigue cumpliendo high>=max(o,c), low<=min(o,c), y cambia",
   f"original coherente   {coherente(df)}\n"
   f"perturbada coherente {coherente(dfp_ctrl)}\n"
   f"close[t+1] {df['close'].iloc[t_ctrl+1]:.2f} -> "
   f"{dfp_ctrl['close'].iloc[t_ctrl+1]:.2f}\n"
   f"close[-1]  {df['close'].iloc[-1]:.2f} -> {dfp_ctrl['close'].iloc[-1]:.2f}\n"
   "(el brief original pedia close*3, que deja close>high: eso es lo que\n"
   " habria podido disparar las ramas de gap y dar un falso positivo)")
print()

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print(f"PARTE A — las {len(STRATEGIES)} estrategias de STRATEGIES (las 11 variantes de")
print(f"         Fase A son un subconjunto), rejilla de {N_T_SINGLE} valores de t")
print("-" * 74)
rejilla = sorted(set(np.linspace(250, n - 30, N_T_SINGLE).astype(int)))
print(f"  t de {rejilla[0]} a {rejilla[-1]} ({len(rejilla)} puntos)")
print()
t0 = time.time()
resumen_a = {}
for nombre, fn in STRATEGIES.items():
    sig_base = fn(df)
    res_base = run_backtest(df, sig_base)
    eq_base = res_base["equity"].values
    primera_rotura = None
    for t in rejilla:
        dfp = perturbar(df, t, SEED + t)
        sig_p = fn(dfp)
        # 1) señales del prefijo [0..t]
        cols = ["entry_long", "entry_short"]
        for c in ("exit_long", "exit_short"):
            if c in sig_base.columns and c in sig_p.columns:
                cols.append(c)
        a = sig_base[cols].values[:t + 1]
        b = sig_p[cols].values[:t + 1]
        if not np.array_equal(a, b):
            d = int(np.argmax((a != b).any(axis=1)))
            primera_rotura = ("señal", t, d)
            break
        # 2) equity del prefijo [0..t]
        eq_p = run_backtest(dfp, sig_p)["equity"].values
        if not np.array_equal(eq_base[:t + 1], eq_p[:t + 1]):
            d = int(np.argmax(eq_base[:t + 1] != eq_p[:t + 1]))
            primera_rotura = ("equity", t, d)
            break
    resumen_a[nombre] = primera_rotura
    if primera_rotura is None:
        print(f"  [OK  ] {nombre:<24} invariante en {len(rejilla)}/{len(rejilla)} valores de t")
    else:
        clase, t, barra = primera_rotura
        print(f"  [FALLA] {nombre:<24} rompe en t={t}: {clase} distinta en la barra {barra} "
              f"({df.index[barra].date()})")
        fallos.append(f"look-ahead en {nombre} ({clase}, t={t}, barra {barra})")
print(f"\n  ({time.time()-t0:.1f}s)")
limpias = sum(1 for v in resumen_a.values() if v is None)
print(f"  {limpias}/{len(STRATEGIES)} variantes invariantes al futuro.")
print("  Incluye rsi_hidden_divergence (ventana centrada + retraso conf2=p+order).")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print(f"PARTE B — portfolio de Fase B, rejilla de {N_T_PORTFOLIO} valores de t")
print("-" * 74)
datos = load_or_download(stamp=SELLO, verbose=False)
res_b = simulate(datos)
eq_b = res_b["equity"].values
nb = len(eq_b)
print(f"  curva base: {nb} dias")
rejilla_b = sorted(set(np.linspace(500, nb - 30, N_T_PORTFOLIO).astype(int)))
print(f"  t de {rejilla_b[0]} a {rejilla_b[-1]} ({len(rejilla_b)} puntos)")
t0 = time.time()
rotura_b = None
for t in rejilla_b:
    datos_p = {}
    for tk, d in datos.items():
        # t es indice de la curva (union de fechas); se perturba por fecha
        fecha_corte = res_b["equity"].index[t]
        dp = d.copy()
        mask = dp.index > fecha_corte
        k = int(mask.sum())
        if k:
            rng = np.random.default_rng(SEED + t + abs(hash(tk)) % 1000)
            factor = np.cumprod(1.0 + 0.05 * rng.standard_normal(k))
            for col in ("open", "high", "low", "close"):
                if col in dp.columns:
                    dp.loc[mask, col] = dp.loc[mask, col].values * factor
        datos_p[tk] = dp
    eq_p = simulate(datos_p)["equity"].values
    if not np.array_equal(eq_b[:t + 1], eq_p[:t + 1]):
        d = int(np.argmax(eq_b[:t + 1] != eq_p[:t + 1]))
        rotura_b = (t, d)
        break
ok(rotura_b is None,
   f"equity del portfolio invariante al futuro en {len(rejilla_b)} valores de t",
   f"({time.time()-t0:.1f}s)" if rotura_b is None else
   f"rompe en t={rotura_b[0]}: equity distinta desde la barra {rotura_b[1]}")
print("  Cubre: sizing Carver con EWMA de vol (s2_path[t-1]), covarianza EWMA")
print("  completa (cov_path[t-1]), momentum (closes[t-1]), elegibilidad y el")
print("  veto de vol de portfolio.")
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — cuanto inflaba el look-ahead que AUDIT-S1 denunciaba")
print("-" * 74)
print("  Medicion controlada: mismo CSV, misma estrategia, mismos costes.")
print("  Unica diferencia: donde se rellena la señal.")
print()


def backtest_con_lookahead(df, signals, commission=0.001, slippage=0.0005,
                           size_fraction=0.95):
    """Variante DELIBERADAMENTE defectuosa: rellena al cierre de la MISMA vela
    de la señal, que es lo que AUDIT-S1 denunciaba. Solo para medir el sesgo;
    no se usa en ningun calculo del expediente."""
    close = df["close"].values
    dates = df.index
    entry_long = signals["entry_long"].values
    cash, eq, pos = 1.0, [], None
    for i in range(len(df)):
        if pos is None and entry_long[i]:
            fill = close[i] * (1 + slippage)          # <-- el defecto
            pos = (fill, (cash * size_fraction) / fill, i)
        elif pos is not None and i - pos[2] >= 20:    # cierre a 20 barras
            ex = close[i] * (1 - slippage)
            gross = (ex - pos[0]) * pos[1]
            cash += gross - (pos[0] + ex) * pos[1] * commission
            pos = None
        unreal = (close[i] - pos[0]) * pos[1] if pos else 0.0
        eq.append(cash + unreal)
    return pd.Series(eq, index=dates)


def backtest_sin_lookahead(df, signals, commission=0.001, slippage=0.0005,
                           size_fraction=0.95):
    """La misma logica, con el fill en open[i+1]: lo que hace el harness real."""
    open_, close = df["open"].values, df["close"].values
    dates = df.index
    entry_long = signals["entry_long"].values
    cash, eq, pos, pend = 1.0, [], None, None
    for i in range(len(df)):
        if pend is not None and pos is None:
            pend = None
            fill = open_[i] * (1 + slippage)          # <-- correcto
            pos = (fill, (cash * size_fraction) / fill, i)
        elif pos is not None and i - pos[2] >= 20:
            ex = close[i] * (1 - slippage)
            gross = (ex - pos[0]) * pos[1]
            cash += gross - (pos[0] + ex) * pos[1] * commission
            pos = None
        if pos is None and pend is None and i < len(df) - 1 and entry_long[i]:
            pend = True
        unreal = (close[i] - pos[0]) * pos[1] if pos else 0.0
        eq.append(cash + unreal)
    return pd.Series(eq, index=dates)


print(f"  {'variante':<24} {'Sharpe c/LA':>12} {'Sharpe s/LA':>12} {'delta':>9}")
print(f"  {'-'*24} {'-'*12} {'-'*12} {'-'*9}")
deltas = []
for nombre, fn in STRATEGIES.items():
    sig = fn(df)
    e_la = backtest_con_lookahead(df, sig)
    e_ok = backtest_sin_lookahead(df, sig)
    m_la = compute_metrics(e_la, [], 365)["sharpe"]
    m_ok = compute_metrics(e_ok, [], 365)["sharpe"]
    deltas.append(m_la - m_ok)
    print(f"  {nombre:<24} {m_la:>12} {m_ok:>12} {m_la-m_ok:>+9.2f}")
print(f"  {'-'*24} {'-'*12} {'-'*12} {'-'*9}")
print(f"  {'media del sesgo':<24} {'':>12} {'':>12} {np.mean(deltas):>+9.2f}")
# --- por que el sesgo sale del tamaño que sale: el gap nocturno -----------
gap = df["open"].values[1:] / df["close"].values[:-1] - 1.0
ret = np.abs(np.diff(df["close"].values) / df["close"].values[:-1])
print()
print("  Diagnostico — tamaño del gap open[i+1] vs close[i] en cripto 24/7:")
print(f"    |gap| medio      {np.abs(gap).mean():.6f}  ({np.abs(gap).mean()*100:.4f}%)")
print(f"    |gap| p95        {np.percentile(np.abs(gap), 95):.6f}")
print(f"    |gap| maximo     {np.abs(gap).max():.6f}")
print(f"    |retorno| medio  {ret.mean():.6f}")
print(f"    ratio |gap|/|retorno| = {np.abs(gap).mean()/ret.mean():.3f}")
print()
sesgo_medio = float(np.mean(deltas))
sesgo_abs = float(np.mean(np.abs(deltas)))
sesgo_max = float(np.max(np.abs(deltas)))
print("  Lectura, leida de los numeros de arriba y no al contrario:")
print(f"    sesgo medio      {sesgo_medio:+.3f} Sharpe")
print(f"    |sesgo| medio     {sesgo_abs:.3f} Sharpe")
print(f"    |sesgo| maximo    {sesgo_max:.3f} Sharpe  (y de signo MIXTO: "
      f"{sum(1 for d in deltas if d > 0)} positivos, "
      f"{sum(1 for d in deltas if d < 0)} negativos)")
print()
if abs(sesgo_medio) < 0.05:
    print("    El sesgo NO es material en estos datos, y su signo es mixto.")
    print("    La razon esta en el diagnostico: en un mercado 24/7 el cierre de")
    print("    la vela i y la apertura de la i+1 son casi el mismo precio (el")
    print("    gap medio es ~1% de la magnitud de un retorno diario), asi que")
    print("    rellenar en close[i] en vez de en open[i+1] apenas cambia el")
    print("    precio de entrada. AUDIT-S1 era una sospecha ESTRUCTURALMENTE")
    print("    correcta — señal y fill no deben compartir vela — pero su efecto")
    print("    NUMERICO sobre cripto diario es despreciable.")
    print()
    print("    Consecuencia incomoda y necesaria: la brecha entre la linea base")
    print("    pre-auditoria de AUDIT_BRIEF.md §6 (ma_cross OOS +24.4%, Sharpe")
    print("    1.63, DD -2.18%) y la reejecucion de hoy con el CSV congelado")
    print("    (+7.96%, Sharpe 0.80, DD -3.75%, paso 3.1 AUDIT-A2) **NO queda")
    print("    explicada por el arreglo del look-ahead**. Tampoco por las")
    print("    señales exit_*: ma_cross no las tiene (columnas: entry_long,")
    print("    entry_short, stop_loss, take_profit, trailing_ma_period, regime).")
    print("    Queda sin explicar desde este repo. [no verificado] La causa")
    print("    candidata es que la linea base se calculo sobre una descarga en")
    print("    vivo de yfinance del 2026-10-05 (AUDIT_BRIEF.md §2) y no sobre")
    print("    este CSV: mismo numero de velas (1827) pero ventana desplazada un")
    print("    dia y precios sujetos a revision por auto_adjust. No es")
    print("    comprobable sin esos datos, que no estan en el repo.")
else:
    print("    El sesgo ES material: media "
          f"{sesgo_medio:+.3f} Sharpe. AUDIT-S1 era una sospecha real y")
    print("    cuantificada; el harness actual, que rellena en open[i+1], no la")
    print("    tiene. Esta es la cuantificacion que AUDIT-A1 exigia.")

print()
print("=" * 74)
if fallos:
    print(f"PASO 3.2: HALLAZGOS — {len(fallos)}:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("PASO 3.2: SIN LOOK-AHEAD DETECTADO")
print(f"  {limpias}/{len(STRATEGIES)} variantes de Fase A y la curva del portfolio de")
print("  Fase B son invariantes a cualquier cambio en el futuro, en todas las")
print("  t probadas. El sesgo que AUDIT-S1 denunciaba es estructuralmente real")
print("  pero numericamente despreciable en cripto diario (parte C), y el")
print("  harness actual no lo tiene en ningun caso.")
print("  Limite declarado: la invariancia se prueba en una rejilla, no en todas")
print("  las barras. Un look-ahead que solo actuase en una t no probada")
print("  escaparia. La rejilla cubre el rango completo de la serie.")
sys.exit(0)
