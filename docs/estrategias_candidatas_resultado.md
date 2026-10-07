# Walk-forward de estabilidad — 3 estrategias candidatas de Opus (9 variantes)

**Objetivo:** medir estabilidad de las 9 variantes, mismo protocolo que
`ma_cross` (Fase 2): sin optimizar parámetros, mismos params en todos los
folds, `size_fraction=0.05` (política Risk de Pablo) desde el primer intento.
Script: `src/walkforward_stability.py <estrategia>` (generalizado,
`STRATEGIES[sys.argv[1]]`, default `ma_cross`). Datos: BTC-USD 5y 1d
(yfinance, 2021-10-07 → 2026-10-07). Costes: 0.1% comisión + 0.05% slippage
por lado. Folds agregados sobre las 4 configuraciones de ventana
(365/90, 730/180, 180/60, 365/180) — 57 folds totales por variante.

## Resumen (las 9 — ninguna omitida)

| Variante | Dictamen | Folds con trades | Cobertura | % positivos | Media | Configs evaluables* |
|---|---|---|---|---|---|---|
| sma_timing_5 | FRÁGIL | 57/57 | 100.0% | 47.4% | +0.11% | 4/4 |
| sma_timing_10 | FRÁGIL | 57/57 | 100.0% | 50.9% | +0.22% | 4/4 |
| sma_timing_20 | FRÁGIL | 57/57 | 100.0% | 59.6% | +0.37% | 4/4 |
| sma_timing_50 | FRÁGIL | 54/57 | 94.7% | 57.4% | +0.43% | 4/4 |
| sma_timing_100 | FRÁGIL | 45/57 | 78.9% | 57.8% | +0.62% | 4/4 |
| sma_timing_304 | FRÁGIL | 5/57 | 8.8% | 80.0% | +0.39% | **0/4** |
| tsmom_365 | FRÁGIL | **0/57** | **0.0%** | — | — | 0/4 |
| tsmom_7 | FRÁGIL | 57/57 | 100.0% | 52.6% | +0.11% | 4/4 |
| connors_rsi2 | **ESTABLE** | 12/57 | 21.1% | 66.7% | +0.18% | 2/4 |
| ma_cross (referencia) | FRÁGIL | 47/57 | 82.5% | 55.3% | +0.07% | 4/4 |

\* configs con ≥5 folds con trades — umbral mínimo para entrar en el dictamen
(`walkforward_stability.py`, regla ya existente de Fase 2).

Folds completos por variante y config en
`results/walkforward_stability_<variante>.json`.

## Lectura honesta, variante por variante

**sma_timing_5/10/20/50/100** — las 5 FRÁGIL por el mismo motivo: al menos
una config (normalmente 365/90 o 180/60) queda por debajo del 60% de folds
positivos exigido por la regla estricta, aunque el agregado mejore con el
período (5→100: 47.4%→57.8% positivos, +0.11%→+0.62% media). Cobertura alta
en todas (79-100%) — señal de buena frecuencia, no es un problema de datos.
Patrón real: cuanto más largo el período de la SMA, mejor el agregado pero
peor la cobertura (sma_timing_100 pierde 21% de los folds).

**sma_timing_304 (Faber, 10 meses bursátiles)** — **no evaluable**: 0 de 4
configs alcanza el mínimo de 5 folds con trades (2 configs sin ningún trade).
Con un período tan largo sobre solo 5 años de datos diarios, casi no hay
cruces. FRÁGIL por el fallback de ausencia de datos, no por desempeño medido
— no hay suficiente evidencia para decir nada de esta variante con este
dataset.

**tsmom_365 (Moskowitz/Ooi/Pedersen, 12 meses)** — **inactiva de verdad**:
0 trades en los 57 folds, en las 4 configuraciones. El retorno de 365 velas
de BTC en esta ventana de 5 años no vuelve a cruzar de negativo a positivo
dentro de ningún fold de test — la señal de entrada (cambio de signo) no se
dispara ni una vez. No es un bug: verificado que la función genera
`entry_long` correctamente en datos sintéticos (`verificar_estrategias_candidatas.py`).
Es un hallazgo real sobre el régimen de BTC 2021-2026, no sobre el código.

**tsmom_7 (Liu/Tsyvinski, 1 semana)** — cobertura completa (100%), pero
desempeño casi idéntico a `ma_cross` (52.6% positivos, +0.11% media) —
FRÁGIL por el mismo motivo de fondo: alguna config por debajo del 60%.

**connors_rsi2 — ESTABLE, pero con matiz importante.** El dictamen mecánico
dice ESTABLE porque las 2 configs que sí alcanzan el mínimo de 5 folds
(730/180 con 5 trades, 365/180 con 7 trades) son ambas ≥60% positivas y con
media positiva. Pero las otras 2 configs (365/90 y 180/60) tienen **0
trades** — ni una sola operación en 43 de los 57 folds totales (cobertura
global 21.1%). El dictamen ESTABLE aquí describe "las pocas veces que operó,
operó bien", no "esta estrategia opera de forma fiable". Con solo 12 trades
reales en 5 años y la mitad de las configuraciones sin ningún dato, es la
candidata con la evidencia más débil de las 9, pese a la etiqueta formal.
Tratarla como ESTABLE-SOBRE-POCOS-DATOS, no como aprobación de peso
equivalente a una variante con cobertura 100%.

## Comparación con la referencia (ma_cross, FRÁGIL)

Ninguna de las 9 bate a `ma_cross` en el único criterio que importa (dictamen
mecánico pasa a ESTABLE), salvo `connors_rsi2` — y esa aprobación es la más
débil de las 10 filas por cobertura, no la más fuerte. En términos de media
de retorno OOS agregada, varias SMA-timing (20/50/100) superan a `ma_cross`
(+0.07%) con mejor cobertura que `connors_rsi2`, pero ninguna cruza el umbral
de 60% positivos en las 4 configs. **Ninguna variante queda lista para modo
aprobación en el paper runner** — las 9, igual que `ma_cross`, arrancarían en
modo observación si se activaran.

## Suite de verificación

```
$ ./venv/bin/python verificar_estrategias_candidatas.py
  OK sma_timing: entry_long solo en el cruce al alza, nunca entry_short, SL/TP NaN, trailing_ma_period=period
  OK tsmom: entry_long solo en el cambio de signo, exit_long cuando el retorno vuelve a <=0, nunca cortos
  OK connors_rsi2: entry_long == rsi(2)<5 & close>sma(filtro) (3 filas), exit_long == close>sma(5) (197 filas), nunca cortos
  OK registro: las 9 variantes estan en STRATEGIES y devuelven las columnas del contrato sobre datos reales
VERIFICACION OK
```

Suite existente de Fase 2 (9 scripts `verificar_*.py` ya en producción)
reejecutada contra el código de esta rama — ver `REGISTRO_D.md` para la
salida completa de cada una.
