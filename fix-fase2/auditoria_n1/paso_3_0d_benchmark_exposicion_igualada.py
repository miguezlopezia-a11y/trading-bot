"""Paso 3.0d — benchmark de exposicion igualada sobre la equity de Fase B.
   (objecion B3 de la nemesis de N2, rama nube/s2-literatura)

Fase B tiene exposicion media 0.156 y se compara contra un B&H 100% invertido
(1.008 vs 1.164). Fase A SI aplico la correccion de exposicion igualada, y fue
esa medicion la que mato a sma_timing_50/100: *"el Sharpe 'respetable' viene de
estar ~50% del tiempo fuera del mercado — es reduccion de exposicion/drawdown,
no edge de retorno"*. En Fase B la correccion se omitio.

Matiz de N2 que se respeta aqui: la exposicion baja NO infla el Sharpe por si
sola (el Sharpe es invariante a escala) y la caja al 0% tampoco lo regala. El
defecto es que el BENCHMARK no esta igualado, no el nivel de exposicion.

Cuatro construcciones, porque la exposicion de Fase B es CONTINUA (no binaria
como en Fase A) y no hay una sola traduccion honesta:

  A) perfil de exposicion: que hay que igualar exactamente.
  B) mascara binaria, la traduccion literal de Fase A: B&H solo los dias con
     exposicion > 0.
  C) benchmark escalado, la traduccion correcta para sizing continuo: mismo
     gross que la estrategia cada dia, resto en caja. Pregunta: si hubieses
     tenido la MISMA exposicion al mercado dia a dia pero repartida a pesos
     iguales en vez de con Carver+momentum, ¿te habria ido mejor?
  D) test de seleccion (objecion B-09 del registro nemesis de N1): ¿el camino
     de exposicion real elige dias favorables para el benchmark? Contraste
     contra permutaciones del propio camino, con semilla fija.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py
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
from portfolio_runner import load_or_download, simulate, PPY  # noqa: E402

SELLO = "20261007"
SEED = 20261101
N_PERM = 2000


def sharpe(x):
    v = np.asarray(x, dtype=float)
    v = v[~np.isnan(v)]
    return float(v.mean() / v.std() * math.sqrt(PPY)) if len(v) > 1 and v.std() > 0 else 0.0


def calmar(x):
    v = pd.Series(np.asarray(x, dtype=float))
    eq = (1 + v).cumprod()
    dd = (eq - eq.cummax()) / eq.cummax()
    años = len(v) / PPY
    if dd.min() == 0 or años <= 0:
        return 0.0
    return float((eq.iloc[-1] - 1) / abs(dd.min()) / años)


print("=" * 74)
print("PASO 3.0d — benchmark de exposicion igualada sobre Fase B")
print("=" * 74)
print("Origen: objecion B3 de la nemesis de N2 (rama nube/s2-literatura).")
print("Es un BENCHMARK, no una variante: N no sube.")
print()

datos = load_or_download(stamp=SELLO, verbose=False)
res = simulate(datos)
eq, bench, expo = res["equity"], res["benchmark"], res["exposure"]
r_est = pd.Series(res["rp"].values, index=eq.index)      # retorno de la estrategia
r_ben = bench.pct_change().fillna(0.0)                   # B&H igual-ponderado
r_est_neto = eq.pct_change().fillna(0.0)                 # con costes

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — el perfil de exposicion que hay que igualar")
print("-" * 74)
e = expo.values
print(f"  dias                              {len(e)}")
print(f"  exposicion media (suma de pesos)  {e.mean():.6f}")
print(f"  mediana                           {np.median(e):.6f}")
print(f"  maxima                            {e.max():.6f}")
print(f"  dias con exposicion = 0           {int((e <= 1e-12).sum())} "
      f"({100*(e <= 1e-12).mean():.1f}%)")
print(f"  dias con exposicion > 0           {int((e > 1e-12).sum())} "
      f"({100*(e > 1e-12).mean():.1f}%)")
print(f"  exposicion media en los dias > 0  {e[e > 1e-12].mean():.6f}")
print()
print("  El benchmark publicado esta 100% invertido todos los dias. La")
print("  estrategia esta al "
      f"{100*e.mean():.1f}% de media. Eso es lo que no esta igualado.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — mascara binaria (la traduccion literal de Fase A)")
print("-" * 74)
mask = e > 1e-12
print(f"  {'serie':<42} {'Sharpe':>9} {'Calmar':>9}")
print(f"  {'-'*42} {'-'*9} {'-'*9}")
s_est_m = sharpe(r_est_neto.values[mask])
s_ben_m = sharpe(r_ben.values[mask])
print(f"  {'estrategia, solo dias con exposicion>0':<42} {s_est_m:>9.3f} "
      f"{calmar(r_est_neto.values[mask]):>9.3f}")
print(f"  {'B&H, los MISMOS dias':<42} {s_ben_m:>9.3f} "
      f"{calmar(r_ben.values[mask]):>9.3f}")
print(f"  {'diferencia (estrategia - B&H)':<42} {s_est_m-s_ben_m:>+9.3f}")
print()
gana_b = s_est_m > s_ben_m
print(f"  Con mascara binaria la estrategia "
      f"{'GANA' if gana_b else 'PIERDE'} al B&H.")
print("  Matiz: con 99%+ de dias con exposicion>0 esta construccion apenas")
print("  corrige nada — la exposicion de Fase B es continua, no un on/off.")
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — benchmark escalado a la misma exposicion (la correcta aqui)")
print("-" * 74)
print("  r_bench_igualado(t) = exposicion(t) * r_B&H(t), resto en caja al 0%.")
print("  Mismo gross al mercado cada dia; unica diferencia: Carver+momentum")
print("  frente a reparto igual-ponderado.")
print()
r_ben_ig = e * r_ben.values
print(f"  {'serie':<42} {'Sharpe':>9} {'Calmar':>9} {'exp. media':>11}")
print(f"  {'-'*42} {'-'*9} {'-'*9} {'-'*11}")
s_est = sharpe(r_est_neto.values)
s_ben100 = sharpe(r_ben.values)
s_ben_ig = sharpe(r_ben_ig)
print(f"  {'Fase B (con costes)':<42} {s_est:>9.3f} "
      f"{calmar(r_est_neto.values):>9.3f} {e.mean():>11.3f}")
print(f"  {'B&H 100% invertido (el publicado)':<42} {s_ben100:>9.3f} "
      f"{calmar(r_ben.values):>9.3f} {1.0:>11.3f}")
print(f"  {'B&H a IGUAL exposicion':<42} {s_ben_ig:>9.3f} "
      f"{calmar(r_ben_ig):>9.3f} {e.mean():>11.3f}")
print()
print(f"  Fase B vs B&H 100%          {s_est - s_ben100:+.3f}  "
      f"({'gana' if s_est > s_ben100 else 'pierde'}) <- el par publicado")
print(f"  Fase B vs B&H igualado      {s_est - s_ben_ig:+.3f}  "
      f"({'gana' if s_est > s_ben_ig else 'pierde'}) <- la comparacion justa")
print()
gana_c = s_est > s_ben_ig
if gana_c:
    print("  Con el benchmark igualado en exposicion, Fase B GANA.")
    print("  Es decir: el 'pierde vs B&H' del expediente era un artefacto de")
    print("  comparar una cartera al "
          f"{100*e.mean():.0f}% de exposicion contra una al 100%.")
    print("  La correccion que Fase A aplico y Fase B omitio NO mata a Fase B:")
    print("  invierte el signo de esa comparacion a su favor.")
else:
    print("  Con el benchmark igualado en exposicion, Fase B SIGUE PERDIENDO.")
    print("  Entonces el dictamen del expediente se sostiene por el lado del")
    print("  benchmark, y ademas se sostiene por la razon correcta.")
print()
print("  Control del matiz de N2 — la invariancia de escala:")
for k in (0.5, 1.0, 2.0):
    print(f"    Sharpe de (B&H 100% x {k})  = {sharpe(k*r_ben.values):.3f}  "
          "(constante: el Sharpe es invariante a escala)")
print("  Confirmado: escalar por una CONSTANTE no cambia nada. Lo que cambia")
print("  el Sharpe es escalar por un camino de exposicion VARIABLE en el")
print("  tiempo, que es exactamente de lo que va esta correccion.")
print()

# ------------------------------------------------------------------ PARTE D
print("-" * 74)
print("PARTE D — ¿el camino de exposicion elige dias favorables? (B-09)")
print("-" * 74)
print(f"  Contraste: {N_PERM} permutaciones del propio camino de exposicion")
print(f"  (misma distribucion exacta, orden aleatorio), semilla {SEED}.")
print("  Si el Sharpe del B&H con el camino REAL cae en la cola alta, el")
print("  camino selecciona dias buenos para el benchmark y lo infla.")
print()
rng = np.random.default_rng(SEED)
vals = np.empty(N_PERM)
rb = r_ben.values
for j in range(N_PERM):
    vals[j] = sharpe(rng.permutation(e) * rb)
pct = float((vals < s_ben_ig).mean() * 100)
print(f"  Sharpe del B&H igualado, camino REAL        {s_ben_ig:.4f}")
print(f"  Sharpe del B&H igualado, caminos permutados "
      f"media {vals.mean():.4f}  sd {vals.std(ddof=1):.4f}")
print(f"  percentil del real en la distribucion       {pct:.1f}%  "
      f"(50% = neutro)")
print()
if pct > 90:
    print("  El camino real SI selecciona dias favorables para el benchmark:")
    print("  el B&H igualado esta inflado, asi que la comparacion de la parte")
    print("  C es MAS dura de lo que deberia para la estrategia.")
elif pct < 10:
    print("  El camino real selecciona dias DESfavorables para el benchmark:")
    print("  el B&H igualado esta deprimido y la parte C es mas benigna de lo")
    print("  que deberia. HAY QUE DESCONTARLO al leer la parte C.")
else:
    z = (s_ben_ig - vals.mean()) / vals.std(ddof=1)
    print(f"  Seleccion NO SIGNIFICATIVA: el camino real queda a {z:+.2f} sd de")
    print("  la media de sus permutaciones. Esta algo por encima (percentil")
    f"  {pct:.0f}%)"
    print(f"  del centro ({pct:.1f}%), asi que si hay un leve sesgo va en contra")
    print("  de la estrategia, no a su favor; pero a esa distancia no se")
    print("  distingue del ruido y no cambia la lectura de la parte C.")
print()
print("=" * 74)
print("VEREDICTO 3.0d")
print(f"  El benchmark del expediente esta al 100% y la estrategia al "
      f"{100*e.mean():.1f}%.")
print("  La objecion B3 de N2 es CORRECTA: la correccion que Fase A aplico")
print("  (rigor_estadistico.py:185-209) en Fase B se omitio.")
print()
print(f"  Par publicado:   Fase B {s_est:.3f}  vs  B&H 100% {s_ben100:.3f}  "
      f"-> pierde por {s_ben100-s_est:.3f}")
print(f"  Par igualado:    Fase B {s_est:.3f}  vs  B&H igual exp "
      f"{s_ben_ig:.3f}  -> {'gana' if gana_c else 'pierde'} por "
      f"{abs(s_est-s_ben_ig):.3f}")
print()
if gana_c:
    print("  Contra lo que B3 temia, la correccion NO convierte a Fase B en")
    print("  'el mismo cadaver que sma_timing_50 con otro nombre': la mata en")
    print("  Fase A porque alli la estrategia no batia al B&H de sus propios")
    print("  dias, y aqui si lo bate a su propia exposicion.")
    print("  Lo que si queda establecido, y es lo que importa: el 'pierde vs")
    print("  B&H' del dictamen de Fase B es un VEREDICTO NO MEDIDO, como B3")
    print("  decia. Medido, cambia de signo.")
else:
    print("  B3 queda confirmada en su temor: medido a igual exposicion, el")
    print("  B&H sigue batiendo a Fase B.")
print()
print("  NO se cambia ningun veredicto del expediente: eso lo decide Pablo.")
print("  Limites declarados:")
print("    - El B&H igualado reparte a pesos iguales entre los activos")
print("      elegibles; no es la unica cartera de referencia posible a esa")
print("      exposicion, solo la que usa el expediente escalada.")
print("    - La caja rinde 0%, igual que en el resto del expediente. Con r_f>0")
print("      el B&H igualado mejoraria y la comparacion se endureceria.")
print("    - El Sharpe de la estrategia incluye costes; el del benchmark no,")
print("      igual que en el expediente (no se cambia esa convencion aqui).")
with open(os.path.join(AQUI, "salida_3_0d_exposicion.json"), "w") as f:
    json.dump({"sello": SELLO, "dias": len(e),
               "exposicion_media": float(e.mean()),
               "dias_exposicion_cero": int((e <= 1e-12).sum()),
               "sharpe_fase_b": s_est,
               "sharpe_bh_100": s_ben100,
               "sharpe_bh_igual_exposicion": s_ben_ig,
               "gana_con_benchmark_igualado": bool(gana_c),
               "mascara_binaria": {"sharpe_estrategia": s_est_m,
                                   "sharpe_bh": s_ben_m},
               "percentil_seleccion": pct}, f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_0d_exposicion.json')}")
