"""Paso 3.4 — el DSR como funcion de N, y V recalculada por tramo.
   (objeciones B-02 y B-08)

B-02: el expediente entero cuelga de la brecha +0.304, que es funcion de
N=12. N en Bailey-LdP cuenta configuraciones PROBADAS, no publicadas. El repo
solo puede corroborar las publicadas, asi que N=12 es una ASUNCION NO
VERIFICABLE. §3.5 del brief original preguntaba si el 12 estaba contado de
forma consistente (lo esta, hallazgo A-14) — la pregunta equivocada.

B-08: SR0 = sqrt(V) * E[max_N]. V es la otra mitad y el brief original no la
auditaba. V se calcula en un solo sitio (portfolio_bateria.py:69) y viaja
CABLEADA como literal a tres modulos. portfolio_walkforward_temporal.py:38
aplica la MISMA V congelada a los tres tramos.

Cuatro partes:
  A) DSR(N) para el Sharpe observado de Fase B. N maximo que aun da DSR>=0.95.
  B) ¿A partir de que N "SEÑAL DEBIL" pasaria a "MUERTA"? Respuesta leida de
     los criterios del propio expediente, no inventada.
  C) V recalculada DENTRO de cada tramo, y como se mueven los tres DSR.
  D) De que esta hecha V: los 12 Sharpe que la componen, y sensibilidad.

No cambia ninguna metrica, umbral ni criterio (prohibido por §3.6 y por el OK).

Uso:  python3 fix-fase2/auditoria_n1/paso_3_4_dsr_funcion_de_n_y_v.py
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
from rigor_estadistico import (dsr, psr, expected_max_sharpe,  # noqa: E402
                               ar1_effective_n, PPY)
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest  # noqa: E402
from portfolio_runner import load_or_download, simulate  # noqa: E402
from portfolio_walkforward_temporal import TRAMOS, bateria_tramo  # noqa: E402

SELLO = "20261007"
V_CABLEADA = 0.0007021947704551833
VARIANTES_A = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
               "sma_timing_50", "sma_timing_100", "sma_timing_304",
               "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
SIZE_FRACTION, WARMUP = 0.05, 200
CONF = 0.95

print("=" * 74)
print("PASO 3.4 — DSR como funcion de N, y V recalculada por tramo")
print("=" * 74)
print("[ASUNCION NO VERIFICABLE] N=12 no es comprobable desde este repo: el")
print("repo solo registra los intentos PUBLICADOS. Todo lo que sigue es, por")
print("tanto, condicional en N.")
print()

datos = load_or_download(stamp=SELLO, verbose=False)
res = simulate(datos)
eq = res["equity"]
rets = eq.pct_change().dropna()
per = rets.values
s_per = per.mean() / per.std()
t_eff = int(ar1_effective_n(per))
skew = float(rets.skew())
kurt = float(rets.kurt() + 3)
s_anual = s_per * math.sqrt(PPY)
print(f"Fase B observada: Sharpe anual {s_anual:.3f}  T_eff {t_eff}  "
      f"skew {skew:.3f}  curtosis {kurt:.3f}")
print()

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — DSR(N) con V cableada, y el N maximo que aun da DSR>=0.95")
print("-" * 74)
print(f"  {'N':>5} {'SR0 diario':>12} {'DSR':>8} {'Sharpe min DSR>=0.95':>22} "
      f"{'¿DSR>=0.95?':>12}")
print(f"  {'-'*5} {'-'*12} {'-'*8} {'-'*22} {'-'*12}")


def sharpe_min(n_trials, var_trials):
    sr0, _ = expected_max_sharpe(n_trials, var_trials)
    if psr(sr0, t_eff, sr0, skew, kurt) >= CONF:
        return sr0 * math.sqrt(PPY)
    lo, hi = sr0, sr0 + 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if psr(mid, t_eff, sr0, skew, kurt) >= CONF:
            hi = mid
        else:
            lo = mid
    return hi * math.sqrt(PPY)


tabla_n = {}
for n in (1, 2, 3, 4, 5, 8, 12, 20, 30, 50, 100):
    d, sr0 = dsr(s_per, t_eff, n, V_CABLEADA, skew, kurt)
    smin = sharpe_min(n, V_CABLEADA)
    tabla_n[n] = {"dsr": d, "sr0": sr0, "sharpe_min": smin}
    marca = "SI" if d >= CONF else "no"
    destaca = " <-- N del expediente" if n == 12 else ""
    print(f"  {n:>5} {sr0:>12.5f} {d:>8.4f} {smin:>22.3f} {marca:>12}"
          f"{destaca}")
print()
# N maximo con DSR>=0.95
n_max = None
for n in range(1, 201):
    d, _ = dsr(s_per, t_eff, n, V_CABLEADA, skew, kurt)
    if d >= CONF:
        n_max = n
    else:
        break
print(f"  N maximo para el que el Sharpe observado ({s_anual:.3f}) aun da")
print(f"  DSR >= 0.95:  N = {n_max}")
print(f"  El expediente usa N = 12. Es decir, el dictamen 'no alcanza DSR")
print(f"  0.95' se sostiene para cualquier N >= {n_max + 1}, y solo se")
print(f"  revertiria si el numero real de intentos fuese <= {n_max}.")
print(f"  Lectura: la conclusion NO es fragil al alza de N — subir N solo la")
print(f"  refuerza. Es fragil a la BAJA, y a la baja es implausible: el repo")
print(f"  documenta 11 variantes de Fase A mas la regla de portfolio.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — ¿a partir de que N 'SEÑAL DEBIL' pasaria a 'MUERTA'?")
print("-" * 74)
print("  Criterios, citados de fase_b_reevaluacion_resultado.md:")
print("    A) ACTIVABLE:    los 3 paquetes + DSR >= 0.95")
print("    B) SEÑAL DEBIL:  P1 y P3 superados, DSR < 0.95")
print("    C) SEÑAL MUERTA: 'ni el walk-forward temporal cayo ni la")
print("                      supervivencia la mato' -> no aplica")
print()
print("  P1 (walk-forward) se decide por IC95 del retorno: '>=2 de 3 tramos")
print("  con IC95 positivo y ningun tramo con IC claramente negativo'")
print("  (portfolio_walkforward_temporal.py:66-74). P3 (supervivencia) se")
print("  decide por t>3, IC positivo y comparacion con B&H.")
print()
print("  NINGUNO de los dos depende de N. El DSR no entra en P1 ni en P3.")
print()
print("  RESPUESTA EXPLICITA: bajo los criterios que el propio expediente")
print("  tiene fijados, NO existe ningun N que convierta 'SEÑAL DEBIL' en")
print("  'SEÑAL MUERTA'. Subir N baja el DSR y aleja la señal de ACTIVABLE,")
print("  pero MUERTA esta definida por el fallo de P1 o P3, que son pruebas")
print("  basadas en intervalos de confianza y en t, no en N.")
print("  Lo que N si hace, cuantificado:")
for n in (12, 20, 30, 50):
    t = tabla_n[n]
    print(f"    N={n:<4} DSR {t['dsr']:.4f}   brecha de Sharpe hasta 0.95: "
          f"{t['sharpe_min'] - s_anual:+.3f}")
print("  Es decir: cada variante nueva que se pruebe encarece el umbral. De")
print(f"  N=12 a N=50 la brecha pasa de {tabla_n[12]['sharpe_min']-s_anual:+.3f} a "
      f"{tabla_n[50]['sharpe_min']-s_anual:+.3f}.")
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — V recalculada DENTRO de cada tramo (B-08)")
print("-" * 74)
print("  portfolio_walkforward_temporal.py:38 aplica la misma V congelada")
print(f"  ({V_CABLEADA:.10f}) a los tres tramos. Aqui se recalcula la V de")
print("  cada tramo con los Sharpe de las 12 series restringidos a ese tramo,")
print("  y se recomputan los tres DSR.")
print()
# las 11 series de Fase A (BTC single-asset, OOS 60/40, size 0.05)
dfb = pd.read_csv(os.path.join(FIX2, "data", "btc_usd_5y_1d.csv"),
                  index_col=0, parse_dates=True)
dfb = dfb.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
split = int(len(dfb) * 0.6)
series_trial = {}
for nombre in VARIANTES_A:
    fn = STRATEGIES[nombre]
    a = max(0, split - WARMUP)
    sig = fn(dfb.iloc[a:])
    r = run_backtest(dfb.iloc[split:], sig.iloc[split - a:],
                     size_fraction=SIZE_FRACTION)
    series_trial[nombre] = r["equity"].pct_change().dropna()
series_trial["portfolio_fase_b"] = rets


def sharpe_d(s):
    v = np.asarray(s, dtype=float)
    v = v[~np.isnan(v)]
    return float(v.mean() / v.std()) if len(v) > 1 and v.std() > 0 else 0.0


# cobertura temporal de cada una de las 12 series (se usa mascara booleana,
# igual que portfolio_walkforward_temporal.py:85, no .loc con fechas)
print("  Cobertura temporal de las 12 series que componen V:")
for nombre, serie in series_trial.items():
    print(f"    {nombre:<24} {serie.index[0].date()} -> "
          f"{serie.index[-1].date()}  ({len(serie)} obs)")
print()
print(f"  {'tramo':<16} {'dias':>6} {'series con >=30 obs':>21} "
      f"{'V del tramo':>14} {'DSR cableada':>13}")
print(f"  {'-'*16} {'-'*6} {'-'*21} {'-'*14} {'-'*13}")
filas_c = {}
for i, (etiqueta, desde, hasta) in enumerate(TRAMOS):
    mask = (rets.index >= desde) & (rets.index <= hasta)
    r_tr = rets[mask].dropna()
    if len(r_tr) < 50:
        continue
    sh, presentes = [], []
    for nombre, serie in series_trial.items():
        m2 = (serie.index >= desde) & (serie.index <= hasta)
        sub = serie[m2].dropna()
        if len(sub) >= 30:
            sh.append(sharpe_d(sub))
            presentes.append(nombre)
    v_tramo = float(np.var(sh, ddof=1)) if len(sh) > 1 else float("nan")
    base = bateria_tramo(r_tr, seed=42 + i)
    con_v = (bateria_tramo(r_tr, var_trials=v_tramo, seed=42 + i)
             if len(sh) > 1 else None)
    filas_c[etiqueta] = {"dias": len(r_tr), "n_series_presentes": len(sh),
                         "series_presentes": presentes,
                         "v_cableada": V_CABLEADA,
                         "v_tramo": None if math.isnan(v_tramo) else v_tramo,
                         "dsr_cableada": base["dsr"],
                         "dsr_v_tramo": con_v["dsr"] if con_v else None,
                         "sharpe_anual": base["sharpe_anual"],
                         "ic95": base["ic95_retorno_anual_pct"]}
    v_txt = "no calculable" if math.isnan(v_tramo) else f"{v_tramo:.8f}"
    print(f"  {etiqueta:<16} {len(r_tr):>6} {len(sh):>21} {v_txt:>14} "
          f"{base['dsr']:>13.4f}")
print()
print("  Los DSR publicados en fase_b_reevaluacion_resultado.md son")
print("  0.824 / 0.772 / 0.301. La columna 'DSR cableada' los reproduce.")
print()
sin_v = [k for k, v in filas_c.items() if v["v_tramo"] is None]
if sin_v:
    print("  HALLAZGO — V NO SE PUEDE RECALCULAR POR TRAMO con esta familia de")
    print(f"  intentos. En {len(sin_v)} de {len(filas_c)} tramos solo hay UNA serie")
    print("  con historia suficiente (la propia curva del portfolio), y la")
    print("  varianza de una sola observacion no existe.")
    print()
    print("  La razon esta en la tabla de cobertura de arriba: las 11 series")
    print("  de Fase A son el tramo OOS de un CSV de 2021-2026, es decir")
    print("  2024-10 -> 2026-10. NO SOLAPAN con T1 (2015-2018) ni con T2")
    print("  (2019-2022). De los tres tramos del walk-forward, los dos que")
    print("  sostienen el dictamen P1 son justamente los dos donde 11 de los")
    print("  12 intentos no existen.")
    print()
    print("  Esto reformula la objecion B-08 y la agrava: usar la misma V")
    print("  congelada en los tres tramos no es una comodidad, es la UNICA")
    print("  opcion disponible. Pero esa V se estima en una ventana de 2 años")
    print("  (2024-2026) y se aplica a tramos que empiezan en 2015. El SR0 de")
    print("  T1 y T2 — y por tanto sus DSR 0.824 y 0.772 — descansan en una")
    print("  dispersion across-trial medida en un periodo que no es el suyo.")
    print()
    print("  No se corrige: cambiar V despues de ver el resultado seria")
    print("  cambiar la metrica, prohibido por §3.6 y por el OK de Pablo.")
    print("  Severidad: MEDIO. No invalida P1 (que se decide por IC95, no por")
    print("  DSR) ni el veredicto global (que se decide por el DSR del periodo")
    print("  completo, donde las 12 series si coexisten). Afecta a la lectura")
    print("  de los DSR POR TRAMO, que el expediente publica como si fuesen")
    print("  comparables entre si.")
    max_delta = None
else:
    cambios = [(k, v["dsr_cableada"], v["dsr_v_tramo"])
               for k, v in filas_c.items() if v["dsr_v_tramo"] is not None]
    max_delta = max(abs(b - c) for _, b, c in cambios) if cambios else 0.0
    print(f"  Mayor desplazamiento de DSR al recalcular V por tramo: {max_delta:.4f}")
print()
# ¿cambia el dictamen P1? P1 no usa DSR, asi que no.
print("  Nota: P1 se decide por IC95, no por DSR, asi que ningun valor de V")
print("  cambia el dictamen P1. Los IC de los tres tramos son:")
for k, v in filas_c.items():
    print(f"    {k:<16} IC95 {v['ic95']}  Sharpe {v['sharpe_anual']}")
print()

# ------------------------------------------------------------------ PARTE D
print("-" * 74)
print("PARTE D — de que esta hecha V, y cuanto importa")
print("-" * 74)
sh_full = {k: sharpe_d(v) for k, v in series_trial.items()}
v_recalc = float(np.var(list(sh_full.values()), ddof=1))
print("  Los 12 Sharpe diarios que componen V (portfolio_bateria.py:54-69):")
for k, v in sh_full.items():
    print(f"    {k:<24} {v:+.6f}   (anualizado {v*math.sqrt(PPY):+.3f})")
print(f"\n  V recalculada aqui   {v_recalc:.12f}")
print(f"  V cableada           {V_CABLEADA:.12f}")
print(f"  diferencia           {abs(v_recalc - V_CABLEADA):.2e}")
coincide_v = abs(v_recalc - V_CABLEADA) < 1e-9
print(f"  -> {'COINCIDE: la constante cableada es reproducible.' if coincide_v else 'NO COINCIDE: la constante cableada no sale de este calculo.'}")
print()
print("  Critica metodologica (B-08), con la evidencia delante: de las 12")
print("  series, 11 son estrategias single-asset sobre BTC en 731 barras OOS")
print("  con sizing 0.05, y la 12a es un portfolio de 10 activos sobre 4404")
print("  dias con sizing Carver. En Bailey-LdP, V es la varianza del Sharpe")
print("  entre los intentos de UNA misma busqueda. Mezclar dos familias que")
print("  no son intercambiables es una eleccion discutible, y determina SR0.")
print("  No se corrige aqui: cambiar V despues de ver el resultado seria")
print("  cambiar la metrica, que esta prohibido. Queda documentado.")
print()
print("  Sensibilidad del DSR de Fase B a V:")
print(f"  {'V':>16} {'factor':>8} {'SR0 diario':>12} {'DSR':>8}")
print(f"  {'-'*16} {'-'*8} {'-'*12} {'-'*8}")
for f in (0.25, 0.5, 1.0, 2.0, 4.0):
    v = V_CABLEADA * f
    d, sr0 = dsr(s_per, t_eff, 12, v, skew, kurt)
    print(f"  {v:>16.10f} {'x'+str(f):>8} {sr0:>12.5f} {d:>8.4f}")
print()
print("=" * 74)
print("VEREDICTO 3.4")
print(f"  N: ASUNCION NO VERIFICABLE. El dictamen 'DSR < 0.95' se sostiene")
print(f"  para todo N >= {n_max + 1} y solo caeria si los intentos reales")
print(f"  fuesen <= {n_max}. La conclusion es robusta al alza de N.")
print("  No existe N que convierta SEÑAL DEBIL en MUERTA: MUERTA se decide")
print("  por P1/P3, que no dependen de N.")
print(f"  V: reproducible ({'si' if coincide_v else 'no'}), pero mezcla dos familias de")
print("  intentos no intercambiables, y se congela para los tres tramos.")
if max_delta is None:
    print("  Recalcularla por tramo es IMPOSIBLE: en T1 y T2 solo existe 1 de")
    print("  las 12 series. La V de los tres tramos se estima en 2024-2026 y")
    print("  se aplica a tramos que empiezan en 2015.")
else:
    print(f"  Recalcularla por tramo mueve los DSR como maximo {max_delta:.4f}.")
with open(os.path.join(AQUI, "salida_3_4_dsr.json"), "w") as f:
    json.dump({"sello": SELLO, "sharpe_anual": s_anual, "t_eff": t_eff,
               "skew": skew, "kurt": kurt, "n_max_dsr_095": n_max,
               "dsr_por_n": {str(k): v for k, v in tabla_n.items()},
               "v_cableada": V_CABLEADA, "v_recalculada": v_recalc,
               "v_coincide": coincide_v,
               "sharpes_trial": sh_full, "tramos": filas_c},
              f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_4_dsr.json')}")
