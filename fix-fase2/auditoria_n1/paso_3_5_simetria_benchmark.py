"""Paso 3.5 — simetria estrategia vs benchmark. (objecion B-09)

Clase de defecto que el brief original no buscaba: que la estrategia y su
benchmark no se midan con la misma informacion. Importa porque el dictamen de
Fase B es literalmente "pierde vs B&H" (1.008 vs 1.164), asi que un sesgo en
el benchmark es parte del dictamen, no un detalle.

Dos asimetrias localizadas por lectura en el registro nemesis (A-17):

  A) portfolio_runner.py:246 calcula el conjunto elegible del BENCHMARK con
     rets.iloc[:t + 1] — incluye la barra t — mientras la ESTRATEGIA usa
     rets[tk].iloc[:t] (:229). Una barra de diferencia, a favor del benchmark.
     Se cuantifica: cuantas decisiones cambian y cuanto mueve el Sharpe.

  B) rigor_estadistico.py:185-209 construye el "benchmark de exposicion
     igualada" seleccionando los dias de B&H con la MASCARA DE POSICION DE LA
     ESTRATEGIA. Eso es una seleccion de dias condicionada al comportamiento
     de la estrategia. Se contrasta contra mascaras aleatorias de la misma
     tasa de exposicion, con semilla fija.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_5_simetria_benchmark.py
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
from portfolio_runner import load_or_download, LOOKBACK, PPY  # noqa: E402
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest  # noqa: E402

SELLO = "20261007"
SEED = 20261101
N_SORTEOS = 2000
VARIANTES_A = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
               "sma_timing_50", "sma_timing_100", "sma_timing_304",
               "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]


def sharpe(x):
    v = np.asarray(x, dtype=float)
    v = v[~np.isnan(v)]
    return float(v.mean() / v.std() * math.sqrt(PPY)) if len(v) > 1 and v.std() > 0 else 0.0


print("=" * 74)
print("PASO 3.5 — simetria estrategia vs benchmark")
print("=" * 74)
print()

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — la barra de mas del benchmark en el portfolio (:t+1 vs :t)")
print("-" * 74)
datos = load_or_download(stamp=SELLO, verbose=False)
tickers = list(datos.keys())
fechas = sorted(set().union(*[d.index for d in datos.values()]))
fechas = pd.DatetimeIndex(fechas)
closes = {tk: datos[tk]["close"].reindex(fechas) for tk in tickers}
rets = pd.DataFrame({tk: closes[tk].pct_change() for tk in tickers},
                    index=fechas)
n = len(tickers)
print(f"  {len(fechas)} fechas, {n} activos, LOOKBACK={LOOKBACK}")
print()
print("  Codigo auditado:")
print("    estrategia (:229)  s = rets[tk].iloc[:t]")
print("                       if s.notna().sum() < LOOKBACK + 1: continue")
print("    benchmark  (:246)  elig = [i for i in range(n)")
print("                        if rets.iloc[:t + 1].iloc[:, i].notna().sum()")
print("                           >= LOOKBACK + 1]")
print()
notna = rets.notna().values.astype(np.int64)
acum = np.cumsum(notna, axis=0)          # acum[t-1, i] = notna hasta t-1
dif_total, primera_dif, por_activo = 0, None, {tk: 0 for tk in tickers}
for t in range(1, len(fechas)):
    # estrategia: rets.iloc[:t]  -> acum[t-1]
    e_est = acum[t - 1] >= LOOKBACK + 1
    # benchmark: rets.iloc[:t+1] -> acum[t]
    e_ben = acum[t] >= LOOKBACK + 1
    d = e_est != e_ben
    k = int(d.sum())
    if k:
        dif_total += k
        for i in np.where(d)[0]:
            por_activo[tickers[i]] += 1
        if primera_dif is None:
            primera_dif = (t, fechas[t], [tickers[i] for i in np.where(d)[0]])
print(f"  decisiones (dia x activo) evaluadas      {(len(fechas)-1)*n}")
print(f"  decisiones donde elegible difiere        {dif_total}")
print(f"  fraccion                                 {dif_total/((len(fechas)-1)*n):.6%}")
if primera_dif:
    t, f, act = primera_dif
    print(f"  primera divergencia                      t={t} {f.date()} {act}")
print(f"  dias de divergencia por activo:")
for tk, k in por_activo.items():
    print(f"    {tk:<10} {k}")
print()
# impacto en el Sharpe del benchmark: recomputar las dos curvas
def curva_benchmark(usar_t_mas_1):
    eqb, val = [1.0], 1.0
    for t in range(1, len(fechas)):
        a = acum[t] if usar_t_mas_1 else acum[t - 1]
        elig = np.where(a >= LOOKBACK + 1)[0]
        r = rets.iloc[t].values
        rb = float(np.nanmean(r[elig])) if len(elig) else 0.0
        if np.isnan(rb):
            rb = 0.0
        val *= (1 + rb)
        eqb.append(val)
    return pd.Series(eqb, index=fechas)


b_actual = curva_benchmark(True)     # como esta en el codigo
b_simetrico = curva_benchmark(False)  # con la misma informacion que la estrategia
s_act, s_sim = sharpe(b_actual.pct_change().dropna()), \
    sharpe(b_simetrico.pct_change().dropna())
r_act = (b_actual.iloc[-1] / b_actual.iloc[0] - 1) * 100
r_sim = (b_simetrico.iloc[-1] / b_simetrico.iloc[0] - 1) * 100
print(f"  {'benchmark':<34} {'Sharpe':>9} {'retorno %':>14}")
print(f"  {'-'*34} {'-'*9} {'-'*14}")
print(f"  {'tal como esta (:t+1)':<34} {s_act:>9.4f} {r_act:>14.2f}")
print(f"  {'simetrico con la estrategia (:t)':<34} {s_sim:>9.4f} {r_sim:>14.2f}")
print(f"  {'diferencia':<34} {s_act-s_sim:>+9.4f} {r_act-r_sim:>+14.2f}")
print()
material_a = abs(s_act - s_sim) > 0.01
if material_a:
    print("  HALLAZGO: la asimetria mueve el Sharpe del benchmark de forma")
    print("  material, y el dictamen de Fase B es 'pierde vs B&H'.")
else:
    print("  La asimetria es REAL pero su efecto numerico es inmaterial: solo")
    print("  desplaza un dia la entrada de cada activo al universo elegible.")
    print("  Direccion: favorece al benchmark, que ya gana — es conservadora")
    print("  respecto al dictamen. Queda documentada, no invalida nada.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — el benchmark de exposicion igualada de Fase A")
print("-" * 74)
print("  rigor_estadistico.py:188-190 selecciona los dias de B&H con la")
print("  mascara de posicion DE LA ESTRATEGIA. Pregunta: ¿esa mascara")
print("  selecciona dias favorables para B&H, inflando el benchmark, o")
print("  desfavorables, inflando a la estrategia?")
print()
print("  Contraste: mascaras aleatorias de la MISMA tasa de exposicion,")
print(f"  {N_SORTEOS} sorteos con semilla {SEED}. Si el B&H de la mascara real")
print("  cae en la cola alta de esa distribucion, la seleccion es favorable")
print("  al benchmark.")
print()
dfb = pd.read_csv(os.path.join(FIX2, "data", "btc_usd_5y_1d.csv"),
                  index_col=0, parse_dates=True)
dfb = dfb.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
split = int(len(dfb) * 0.6)
WARMUP = 200
print(f"  {'variante':<22} {'exp %':>7} {'B&H real':>9} {'B&H aleat. medio':>17} "
      f"{'percentil':>10} {'estrategia':>11}")
print(f"  {'-'*22} {'-'*7} {'-'*9} {'-'*17} {'-'*10} {'-'*11}")
filas_b, percentiles = {}, []
for nombre in VARIANTES_A:
    fn = STRATEGIES[nombre]
    a = max(0, split - WARMUP)
    sig = fn(dfb.iloc[a:])
    sliced = dfb.iloc[split:]
    res = run_backtest(sliced, sig.iloc[split - a:], size_fraction=0.05)
    eq = res["equity"]
    r_est = eq.pct_change().dropna()
    bh = sliced["close"].pct_change().dropna()
    # la mascara, igual que rigor_estadistico.py:163-164
    pos = eq.index.to_series().map(
        lambda d: any(t.entry_date <= d <= (t.exit_date or d)
                      for t in res["trades"]))
    bh_al = bh.reindex(pos.index).fillna(0.0)
    mask = pos.values.astype(bool)
    k = int(mask.sum())
    if k < 10:
        print(f"  {nombre:<22} {'n/a — menos de 10 dias con posicion':>60}")
        continue
    bh_real = sharpe(bh_al[mask].values)
    est_real = sharpe(r_est.reindex(pos.index).fillna(0.0)[mask].values)
    rng = np.random.default_rng(SEED)
    vals = np.empty(N_SORTEOS)
    arr = bh_al.values
    for j in range(N_SORTEOS):
        idx = rng.choice(len(arr), size=k, replace=False)
        vals[j] = sharpe(arr[idx])
    pct = float((vals < bh_real).mean() * 100)
    percentiles.append(pct)
    filas_b[nombre] = {"exposicion_pct": 100 * k / len(mask),
                       "bh_mascara_real": bh_real,
                       "bh_aleatorio_medio": float(vals.mean()),
                       "percentil": pct, "estrategia": est_real}
    print(f"  {nombre:<22} {100*k/len(mask):>7.1f} {bh_real:>9.3f} "
          f"{vals.mean():>17.3f} {pct:>9.1f}% {est_real:>11.3f}")
print()
extremos = [p for p in percentiles if p > 95 or p < 5]
print(f"  Variantes cuyo B&H con mascara real cae fuera del [5%, 95%] de la")
print(f"  distribucion aleatoria: {len(extremos)} de {len(percentiles)}")
print(f"  Percentil medio: {np.mean(percentiles):.1f}% "
      f"(50% seria seleccion neutra)")
print()
if np.mean(percentiles) > 70:
    print("  HALLAZGO: la mascara de la estrategia selecciona dias")
    print("  sistematicamente FAVORABLES para B&H -> el benchmark de")
    print("  exposicion igualada esta inflado, y la comparacion de Fase A")
    print("  ('ninguna variante supera al benchmark') es mas dura de lo que")
    print("  deberia.")
elif np.mean(percentiles) < 30:
    print("  HALLAZGO: la mascara selecciona dias DESFAVORABLES para B&H -> el")
    print("  benchmark esta deprimido y la comparacion es mas benigna de lo")
    print("  que deberia. Eso favorece a las estrategias, en contra del")
    print("  dictamen conservador que el expediente publica.")
else:
    print("  La seleccion es aproximadamente NEUTRA: el B&H con la mascara")
    print("  real no se distingue del B&H con mascaras aleatorias de la misma")
    print("  tasa. El benchmark de exposicion igualada no esta sesgado por")
    print("  condicionar en la estrategia. No hay hallazgo aqui.")
print()
print("=" * 74)
print("VEREDICTO 3.5")
print(f"  A) Asimetria :t+1 / :t en el portfolio: REAL, {dif_total} decisiones")
print(f"     afectadas de {(len(fechas)-1)*n} ({dif_total/((len(fechas)-1)*n):.4%}).")
print(f"     Efecto en el Sharpe del benchmark: {s_act-s_sim:+.4f}. "
      f"{'MATERIAL' if material_a else 'INMATERIAL'}.")
print(f"  B) Mascara de exposicion igualada: percentil medio "
      f"{np.mean(percentiles):.1f}% -> "
      f"{'sesgada' if abs(np.mean(percentiles)-50) > 20 else 'neutra'}.")
print("  Limite declarado: B compara contra mascaras aleatorias sin")
print("  estructura temporal. Una mascara real tiene rachas; el contraste")
print("  aleatorio no las reproduce.")
with open(os.path.join(AQUI, "salida_3_5_simetria.json"), "w") as f:
    json.dump({"sello": SELLO,
               "parte_a": {"decisiones": (len(fechas) - 1) * n,
                           "divergentes": dif_total,
                           "por_activo": por_activo,
                           "sharpe_benchmark_actual": s_act,
                           "sharpe_benchmark_simetrico": s_sim},
               "parte_b": filas_b,
               "percentil_medio": float(np.mean(percentiles))},
              f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_5_simetria.json')}")
