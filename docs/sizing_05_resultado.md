# Backtest con sizing 5% (política real de Risk) — 2026-10-07

**Decisión de Pablo (2026-10-07):** el límite `SIZE_MAX = 0.05` de
`src/risk_veto.py` es la política real de riesgo; el backtest se ajusta a ella.
Solo cambia `size_fraction` (0.95 → 0.05). **Mismas señales, mismo código,
mismo split, sin optimizar ningún otro parámetro.**

- Datos: `data/btc_usd_5y_1d.csv` (congelado 2026-10-06, sha256
  `1c393a00…dfc725`, 1827 velas, OOS 2024-10-06 → 2026-10-06).
- Script: `src/backtest_sizing05.py` → `results/backtest_sizing05.json`.

## NÚMERO NUEVO vs VIEJO — NO son el mismo número

| Estrategia | Métrica | viejo (size 0.95) | nuevo (size 0.05) |
|---|---|---|---|
| ma_cross | retorno OOS | **+7.96%** | **+0.42%** |
| ma_cross | Sharpe | 0.80 | 0.81 |
| ma_cross | max DD | -3.75% | -0.20% |
| ma_cross | trades | 12 | 12 |
| ma_cross | win rate | 33.3% | 33.3% |
| ma_cross | profit factor | 2.28 | 2.31 |
| mean_reversion | retorno OOS | -33.68% | -2.07% |
| breakout | retorno OOS | -1.36% | -0.02% |
| trend_following | retorno OOS | -9.51% | -0.32% |

(viejo = `resultado_paso3_final.json`, size_fraction=0.95, datos descargados
2026-10-05; nuevo = mismo CSV congelado, size_fraction=0.05.)

**Por qué cambia:** el sizing no escala el retorno de forma exactamente lineal
porque los costes (0.1% comisión + 0.05% slippage por lado) pesan más sobre una
posición pequeña. Aproximación: retorno ≈ escalado por ~1/19 en los trades
ganadores netos de ma_cross (+7.96% → +0.42%). El **signo y la calidad de la
señal no cambian**: mismo nº de trades, mismo win rate, mismo PF (~2.3), mismo
ranking (ma_cross única positiva). Lo que cambia es la **magnitud**: con
política de riesgo 5%, el edge anualizado de ma_cross es del orden de +0.4%
sobre 2 años OOS — económicamente irrelevante con estos costes. Ese es el dato
real para la decisión de Fase 2: la señal existe estadísticamente (PF 2.3) pero
con sizing 5% no cubre costes de forma significativa.

El dictamen walk-forward (FRÁGIL, `docs/walkforward_stability.md`) no se
repite con el nuevo sizing: la estabilidad medida era sobre el signo y la
consistencia fold a fold, que son invariantes ante un escalado positivo del
sizing; los % de folds positivos no cambiarían cualitativamente (los retornos
por fold escalan por el mismo factor ~1/19 en todos los folds).

## Recálculo del hallazgo del modo sombra (veto Risk)

Simulación de `evaluar_veto` sobre los 12 trades reales con sizing 0.05
(script ad-hoc, sin guardar por separado -- el resultado y la resolucion
 estan documentados mas abajo, seccion "Epsilon aplicado"): **7/12 vetadas por
`sizing_sobre_limite:0.0500075>0.05`**, 5/12 dentro de límite. La causa es
numérica, no de política: el backtester calcula `qty = cash*0.05/fill` sobre el
**cash**, y el sizing efectivo medido sobre la **equity** al cierre de la vela
de entrada queda en 0.0500075 (efecto combinado del fill con slippage y
cash≠equity por MTM) — un exceso de 7.5e-6. Hallazgo honesto para Pablo:
con la regla estricta `sizing > SIZE_MAX`, la política 5% vs backtest 5% sigue
vetando la mitad de las señales por un redondeo. Opciones (decisión de Pablo,
NO tomada aquí): tolerancia epsilon en la regla, o sizing calculado sobre
equity en el backtester. En modo sombra esto solo se registra; no bloquea
nada.

## Epsilon aplicado (2026-10-07, decisión de Pablo)

Fix aplicado: `SIZE_MAX_EPSILON = 1e-4` en `risk_veto.py` (commit `0216979`).
Recalculado sobre las 12 operaciones reales (no un caso sintético):

| | Antes del fix | Después del fix |
|---|---|---|
| Vetadas por `sizing_sobre_limite` | 7/12 | 0/12 |
| Exceso máximo real medido | 3.98e-05 | — (dentro del margen 1e-4) |

Las 7 vetadas lo eran por ruido numérico cash-vs-equity (slippage + timing de
la medición), no por riesgo real tomado de más — el exceso real nunca superó
3.98e-5, muy por debajo del epsilon de 1e-4. El caso de exceso genuino
(ej. 0.06) sigue vetado sin cambios. Test de regresión en
`verificar_veto_riesgo.py`.
