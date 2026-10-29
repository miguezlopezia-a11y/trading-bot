# Walk-forward de estabilidad de ma_cross (1.4) — 2026-10-06

**Objetivo:** medir estabilidad de ma_cross post-fix, NO optimizar parámetros
(mismos params en todos los folds). Script: `src/walkforward_stability.py`.
Datos: BTC-USD 5y 1d (yfinance, 1827 velas, 2021-10-06 → 2026-10-06).
Costes: 0.1% comisión + 0.05% slippage por lado (los del backtester).

## Resumen por configuración de ventana

| Config (train/test) | Folds | % positivos | Media | Mediana | Std | Min | Max |
|---|---|---|---|---|---|---|---|
| 365d / 90d  | 16 | 50.0% | +1.17% | +1.46% | 2.27% | -2.46% | +3.51% |
| 730d / 180d | 6  | 66.7% | +1.60% | +0.68% | 3.24% | -2.18% | +6.83% |
| 180d / 60d  | 27 | 33.3% | +0.62% | 0.00%  | 2.04% | -2.46% | +3.56% |
| 365d / 180d | 8  | 75.0% | +2.35% | +2.03% | 3.26% | -2.18% | +6.84% |

Folds completos por configuración en `results/walkforward_stability.json`.

## Lectura

- La señal es de **baja frecuencia**: ~1 trade por fold de 90 días; en la
  config 180/60 hay 10 folds de 27 sin ningún trade (mediana 0.00%).
- En ventanas **largas** (test ≥180d) es consistentemente positiva (67-75%
  folds positivos, mediana positiva). En ventanas **cortas** o la config por
  defecto (365/90: 50% positivos) es una moneda al aire.
- Dispersión alta en todas las configs (std 2-3.3pp sobre medias de 0.6-2.4%).

## Dictamen

**FRÁGIL** (regla estricta: ESTABLE solo si TODA config con folds suficientes
tiene ≥60% folds positivos y media > 0; 365/90 = 50% y 180/60 = 33% lo incumplen).

Consecuencia ejecutada: el paper runner arranca en **modo observación** —
registra las señales/trades como decisión "observacion" con motivo
`walkforward_dictamen_fragil_2026-10-06`; ninguna señal se marca "aprobada".
El matiz real: el edge parece existir en horizontes largos, pero con ~12
trades/año y 50% de folds ganadores en la ventana por defecto, no hay base
para aprobación automática. Si el track record de paper trading (varios meses)
confirma expectancy positiva, se puede reevaluar el modo.

**Nota 2026-10-07 (sizing 5%):** Pablo fijó la política de riesgo en
SIZE_MAX=5% y el backtest se rehizo con size_fraction=0.05
(`docs/sizing_05_resultado.md`). El dictamen de estabilidad NO se rehace: la
estabilidad medida (signo y consistencia fold a fold, % de folds positivos) es
invariante ante un escalado positivo del sizing; los retornos por fold
escalan por el mismo factor en todos los folds. El dictamen FRÁGIL se mantiene.
