# Fase B — Reevaluación: walk-forward temporal, potencia formal y supervivencia

**Fecha:** 2026-10-09 · **Ejecutor:** Kimi Code · **Rama:** `fase-b-multiactivo`
(commits nuevos sobre `9249cf4`). main intacto — verificación pegada abajo.
TDD: verificación sintética de los 3 paquetes ANTES de datos reales (3/3 OK).

**Nota de datos:** la reevaluación congeló datos frescos el 2026-10-09
(`data/multi/*_20261009.csv`, +2 velas respecto al run de la Fase B de
2026-10-07; los hashes de hoy son los que mandan aquí; ambos conjuntos
preservados). Los 5 activos caídos se congelaron en `data/multi_muertos/`.

## Paquete 1 — Walk-forward temporal

**Diseño (fijado antes de correr):** 3 tramos contiguos por ciclos de
mercado: T1 2015-09→2018-12 (acumulación+bull 2017+bear 2018), T2
2019→2022 (acumulación+bull 2021+bear 2022), T3 2023→fin (bull 2023-2025).
Una sola simulación (warm-up real, parámetros congelados), equity cortada por
tramo. N=12 trials en todos los DSR.

**Métrica decisiva (aprobada por Pablo 2026-10-09, antes de la corrida):**
≥2 de 3 tramos con IC95 del retorno positivo (límite inferior > 0) y ningún
tramo con IC claramente negativo (límite superior < 0).

| Tramo | PnL | Exposición | Sharpe | t | DSR | IC95 retorno anual % | B&H Sharpe |
|---|---|---|---|---|---|---|---|
| T1 2015-2018 | +81.7% | 0.186 | 1.33 | 2.34 | 0.824 | **[+0.57, +38.51]** | 1.47 |
| T2 2019-2022 | +82.4% | 0.141 | 1.22 | 2.49 | 0.772 | **[+1.13, +30.71]** | 1.29 |
| T3 2023-fin | +26.0% | 0.184 | 0.57 | 1.10 | 0.301 | [-5.86, +20.30] | 0.80 |

**Dictamen P1: SUPERADO** — 2 de 3 tramos con IC positivo, 0 claramente
negativos (`{'superado': True, 'tramos_positivos': 2, 'tramos_claramente_negativos': 0}`).
Lectura honesta: el edge se concentra en los dos tramos con ciclo completo
(2015-2018, 2019-2022) y se debilita en el tramo actual (t=1.10, IC cruza
cero) — no es un artefacto del primer ciclo, pero el tramo 2023+ no
confirma todavía (es también el más corto).

## Paquete 2 — Potencia formal A PRIORI

Sharpe anual mínimo exigido (T_eff=4336, skew 1.037, curtosis 32, V=0.0007022),
invirtiendo la PSR de Bailey-LdP (reutilizada de `rigor_estadistico.py`):

| N trials | SR₀ (diario) | Sharpe mínimo para DSR≥0.95 |
|---|---|---|
| 1 | 0.00000 | 0.472 |
| 5 | 0.03160 | 1.073 |
| **12** | **0.04412** | **1.312** |
| 50 | 0.06032 | 1.622 |
| 100 | 0.06706 | 1.751 |

Sharpe mínimo para **t>3: 0.870** (anual). Observado Fase B: **1.008**.
**Brecha vs DSR≥0.95: +0.304** — el DSR exigente sigue sin alcanzarse; el
t>3 se supera con holgura (y también explica por qué Fase A nunca pudo
ver nada: con T~700 y N=11, el umbral t era inalcanzable).

**Dictamen P2:** cálculo entregado y verificado (sintético: curvas encima/
debajo del umbral clasificadas bien, 3/3). Conclusión: con N=12 y estas
colas, un Sharpe 1.0 no basta para DSR 0.95 — hacen falta ~1.31, o menos
trials, o más T. **Este es el cálculo que se exigirá A PRIORI antes de
cualquier fase nueva (regla de proyecto).**

## Paquete 3 — Sesgo de supervivencia

Universo alternativo: 10 supervivientes + 5 caídos (criterio fijado antes de
correr, sin mirar la señal: top-20 market-cap histórico 2017-2021 y hoy >85%
bajo su máximo — EOS, XLM, BCH, FIL, ICP; CSV congelados en
`data/multi_muertos/` con sha256+meta). Misma regla, mismos parámetros.

| Universo | Retorno | Sharpe | t | DSR | IC95 anual % | vs B&H Sharpe |
|---|---|---|---|---|---|---|
| Superviviente (10) | +317.5% | 1.01 | 3.48 | 0.72 | [+4.47, +20.91] | 1.01 vs 1.16 (no) |
| Con 5 caídos (15) | +266.1% | 0.92 | **3.18** | 0.60 | **[+3.27, +19.90]** | 0.92 vs 1.07 (no) |

Las tres pruebas booleanas se mantienen en el universo extendido (t>3 sí, IC
positivo sí, B&H igual que antes: no superado en ambos). **Dictamen P3:
SUPERADO — la señal sobrevive a los muertos.**

## Veredicto global: **B) SEÑAL DÉBIL**

- A) ACTIVABLE: exige los 3 paquetes + DSR ≥ 0.95 → **DSR es 0.72. No.**
- B) SEÑAL DÉBIL: P1 y P3 superados, DSR < 0.95 → **es este.**
- C) SEÑAL MUERTA: ni el walk-forward temporal cayó ni la supervivencia la
  mató → no aplica.

**Queda en la rama como candidata a más datos. Nada se activa. Lo que falta
para subir a A:** cerrar la brecha DSR de +0.304 (más años de datos, o menos
trials futuros — cada variante nueva que se pruebe sube el umbral), o que el
tramo 2023+ confirme en el tiempo (t=1.10 aún).

## Lo que nada de esto responde (límites declarados)

- El período incluye un bull histórico cripto irrepetible; el tramo T3, el
  más reciente, es el que peor se comporta.
- El benchmark igual-ponderado no es operable sin suerte de rebalanceo; en
  Sharpe gana al portfolio en ambos universos.
- σ_target=10% puede ser bajo para participar del bull (el B&H gana por
  mucho en retorno pese a su −89% de DD).
- La lista de caídos (EOS/XLM/BCH/FIL/ICP) sigue siendo una elección
  documentable, no el universo completo de 2017; top-N por market-cap
  histórico congelado seguiría siendo mejor y no se hizo.
- Sesgo de supervivencia residual: los datos de FIL en yfinance empiezan
  2017-12 (anterior a su listado real) — se usa lo que el proveedor da, sin
  validar.

## Verificación

- Sintéticos 3/3 antes de datos reales (walkforward, potencia, supervivencia)
  + suite completa 15/15 PASS (12 previos + 3 nuevos). Salidas en
  `REGISTRO_F.md`.
- `git log main` verificado intacto (abajo).
- Ningún commit toca `paper_runner.py`, `risk_veto.py` ni `deliberation.py`.
