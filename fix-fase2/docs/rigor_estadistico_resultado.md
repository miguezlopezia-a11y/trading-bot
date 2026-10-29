# Rigor estadístico — resultado sobre las 11 variantes (Fase A)

**Fecha:** 2026-10-07 · **Ejecutor:** Kimi Code · Datos: pipeline congelado
(`data/btc_usd_5y_1d.csv`, sha256 `1c393a00…dfc725`, 1827 velas, OOS
2024-10-06 → 2026-10-06, sizing 0.05 = política Risk). Capa de análisis: sin
variantes nuevas, sin optimización, sin tocar el pipeline de trading.

## Fuente de la fórmula DSR (verificada antes de programarla)

- **Paper original:** Bailey, D.H. & López de Prado, M. (2014), *The Deflated
  Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and
  Non-Normality*, Journal of Portfolio Management 40(5), 94-107.
  SSRN 2460551 — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- **Validación cruzada numérica:** el paquete `deflated_sharpe`
  (https://daru.finance/projects/deflated-sharpe) reproduce los ejemplos
  impresos del paper; contra su ejemplo principal se validó esta
  implementación: SR₀ = 0.113172 (paper: 0.1132), DSR = 0.900397 (paper:
  0.9004), con sharpe diario 0.15811388, T=1250, N=100, V=0.002, skew −3,
  kurtosis 10 (raw). Fórmulas:
  - PSR(SR*) = Φ[(ŜR−SR*)·√(T−1) / √(1−γ₃·ŜR+(γ₄−1)/4·ŜR²)] (corrección de
    Mertens por skew γ₃ y curtosis raw γ₄)
  - E[máx_N] = √V·[(1−γ_E)·Φ⁻¹(1−1/N) + γ_E·Φ⁻¹(1−1/(N·e))], γ_E≈0.5772
    (Euler-Mascheroni); SR₀ = E[máx_N] con V = varianza across-trial de los
    Sharpes por periodo
  - DSR = PSR(SR₀); umbral de aceptación 0.95.
- **T efectivo:** los retornos de una estrategia con posiciones abiertas son
  autocorrelados; se aplica el ajuste AR(1) documentado en la misma fuente
  (T_eff = T·(1−ρ)/(1+ρ), ρ = autocorrelación lag-1).
- **V usada:** varianza de los Sharpes diarios de las 11 variantes =
  0.0007017. N = 11 variantes registradas (ma_cross + 9 de Opus +
  rsi_hidden_divergence).

**Nota de método:** se usó **block bootstrap** (bloques de 21 días, B=10000,
seed 42) sobre retornos diarios y sobre PnLs por trade. **No CPCV/PBO** —
aproximación práctica deliberada (CPCV correcto es sustancialmente más
complejo; mezclar ambos sin implementarlo bien sería peor). Documentado, no
camuflado.

## Verificación sintética (ejecutada ANTES de los datos reales)

```
  1. ejemplo paper: SR0=0.113172 (esperado 0.1132) DSR=0.900397 (esperado 0.9004) -> OK
  2. ruido puro (N=100, 200 corpus): DSR rechazo al mejor en 199/200 (100%) -> OK
  3. edge inyectado (SR diario 0.15, T=1250): PSR(0)=1.0000 DSR(N=1)=1.0000 -> OK
  4. block bootstrap: ruido puro x100: IC sin cruzar 0 en 3 (3%, esperado ~5%) -> OK; edge IC95 [+0.0410,+0.1535] no cruza -> OK
VERIFICACION SINTETICA OK
```

(El test encontró dos bugs en el desarrollo — índices de bloque siempre
desde 0 y límite N=1 — antes de tocar datos reales. Es su función.)

## Resultado por variante (OOS, sizing 5%)

| Variante | Sharpe bruto | DSR | t (umbral >3) | IC95 retorno anual % | IC95 win rate % | pasa t>3 |
|---|---|---|---|---|---|---|
| ma_cross | 0.81 | **0.492** | 1.03 | [-0.13, +0.59] | [17, 50] | no |
| sma_timing_5 | -0.30 | 0.059 | -0.42 | [-2.84, +2.15] | [21, 35] | no |
| sma_timing_10 | 0.17 | 0.189 | 0.24 | [-1.80, +2.57] | [18, 40] | no |
| sma_timing_20 | 0.79 | 0.482 | 1.08 | [-1.11, +4.08] | [15, 40] | no |
| sma_timing_50 | **1.12** | **0.660** | 1.52 | [-0.47, +4.87] | [8, 33] | no |
| sma_timing_100 | 1.00 | 0.605 | 1.43 | [-0.59, +4.48] | [0, 46] | no |
| sma_timing_304 | 0.52 | 0.337 | 0.71 | [-0.94, +2.38] | n/a (5 trades) | no |
| tsmom_7 | -0.26 | 0.077 | -0.34 | [-2.59, +1.88] | [24, 40] | no |
| tsmom_365 | -0.02 | 0.020 | -0.04 | [-0.04, +0.04] | n/a (1 trade) | no |
| connors_rsi2 | 0.91 | 0.556 | 1.40 | [-0.12, +0.98] | **[58, 92]** | no |
| rsi_hidden_divergence | 0.52 | 0.323 | 0.75 | [-0.66, +1.99] | n/a (3 trades) | no |

DSR < 0.95 en las 11. Ningún IC del retorno deja el cero. Ningún t>3 (máx
1.52). El Sharpe 0.80 de ma_cross **no sobrevive**: DSR 0.49 — la estimación
de Opus se confirma con el cálculo real.

**Matiz honesto — connors_rsi2:** su IC del win rate [58, 92] **no** cruza
50%: el win rate alto es estadísticamente real (12 trades, poca potencia,
pero consistente). Lo que no existe es edge económico (IC del retorno cruza
cero: TP pequeños, pérdidas grandes). "Acertar mucho" ≠ "ganar dinero".

## Benchmark de exposición igualada

Sharpe/Calmar de la estrategia vs buy&hold de BTC **solo en los días con
posición abierta** (misma exposición media, no el período completo):

| Variante | Exposición % | Sharpe estrat. | Sharpe B&H igual expo. | Calmar estrat. | Calmar B&H igual expo. |
|---|---|---|---|---|---|
| ma_cross | 3.8 | 4.22 | 4.12 | 27.2 | 38.9 |
| sma_timing_5 | 51.8 | -0.41 | 0.25 | -0.24 | 0.03 |
| sma_timing_10 | 51.6 | 0.24 | 0.74 | 0.22 | 0.79 |
| sma_timing_20 | 52.4 | 1.09 | 1.36 | 1.52 | 2.46 |
| sma_timing_50 | 55.1 | 1.50 | 1.77 | 2.35 | 3.77 |
| sma_timing_100 | 50.8 | 1.41 | 1.72 | 2.33 | 3.62 |
| sma_timing_304 | 35.2 | 0.87 | 1.19 | 1.02 | 1.61 |
| tsmom_7 | 53.2 | -0.35 | 0.10 | -0.25 | -0.10 |
| tsmom_365 | 0.3 | -0.34 | 1.63 | -6.6 | 30.9 |
| connors_rsi2 | 5.2 | 4.07 | 4.84 | 28.1 | 38.2 |
| rsi_hidden_divergence | 11.9 | 1.50 | 1.49 | 4.03 | 3.67 |

Con la misma exposición, **todas las sma_timing y tsmom pierden contra el
buy&hold en Sharpe** (y en Calmar casi todas). El Sharpe "respetable" del
período completo de sma_timing_50/100 viene de estar ~50% del tiempo fuera
del mercado — es reducción de exposición/drawdown, no edge de retorno, y aquí
se mide como lo que es. ma_cross y connors_rsi2 apenas difieren del B&H en
sus pocos días expuestos (su valor, si lo tuviera, sería el market timing de
la exposición — que el IC de arriba no respalda).

## Dictamen

**Ninguna de las 11 variantes tiene significancia estadística real.** Ni por
DSR (corrección por selección, mejor 0.66), ni por bootstrap (todos los IC
del retorno cruzan cero), ni por t>3 (máximo 1.52), ni contra el benchmark de
exposición igualada (las de régimen pierden contra B&H a igual exposición).
La sospecha cualitativa queda confirmada por estadística: con ~1 activo, ~5
años y 1-105 trades, no hay potencia suficiente para probar edge — sea cual
sea la regla. **El criterio mecánico `≥60% folds positivos y media>0` queda
degradado a pista documental**: nadie aprueba nada en el runner por ese
criterio (el runner sigue en modo observación y esto no cambia nada del
pipeline).

La consecuencia es la pregunta de la Fase B (multi-activo, sizing por
volatilidad), que **espera el OK explícito de Pablo** — no se ha tocado
código de multi-activo.

Datos completos: `results/rigor_estadistico.json`. Código:
`src/rigor_estadistico.py` + `verificar_rigor_sintetico.py`.
