# AUDIT BRIEF — Trading Bot Pipeline Fase 1

**Auditor:** agente externo (Kimi u otro). **Builder:** MaiA (OpenClaw), 2026-10-05.
**Objetivo:** verificación independiente del pipeline de backtesting antes de construir las capas de deliberación y paper trading encima.

---

## 1. Contexto de arquitectura

Pipeline de trading algorítmico inspirado en los 4 arquetipos del PDF "La guía del (buen) trader algorítmico" (Andrea Soler Pla). Fase 1 = validación cuantitativa. Arquitectura completa prevista (para contexto, NO auditable aún):

```
Scanner → Analista (6 Sombreros + skills auditados) → Sentiment → Risk (veto) → Executor
                                     ↑
                         Segundo cerebro (Supabase pgvector, journal)
```

Lo que se audita HOY es solo la base cuantitativa sobre la que se apoya todo.

## 2. Archivos a auditar

Ruta base: `/opt/trading-bot/`

| Archivo | Líneas aprox | Qué hace |
|---|---|---|
| `src/indicators.py` | ~110 | RSI, SMA/EMA, MACD, Bollinger, Estocástico, ATR, ADX — todos vectorizados |
| `src/strategies.py` | ~130 | 4 arquetipos → DataFrame con entry_long/short, SL/TP, trailing MA |
| `src/backtester.py` | ~150 | Event-driven, 1 posición, costes, gestión de salidas, métricas |
| `src/run_backtest.py` | ~110 | Runner: descarga yfinance, split train/test, walk-forward |

Entorno: Python 3.12 venv en `/opt/trading-bot/venv/` (pandas 3.0.6, numpy 2.5.3, yfinance).
Reproducción: `cd /opt/trading-bot && ./venv/bin/python src/run_backtest.py`

## 3. Sospechas conocidas del builder (verificar prioritariamente)

### S1 — Posible look-ahead bias en fills (ALTA prioridad)
En `backtester.py`, la entrada se ejecuta al **cierre de la misma vela** donde se calculó la señal (`price = close[i]`, señal `entry_long[i]` calculada con indicadores que incluyen `close[i]`). Señal y fill comparten vela → la señal "ve" el cierre antes de "comprar" en ese cierre. Lo correcto sería señal en vela i → fill en apertura de vela i+1. **Cuantificar cuánto infla los resultados**: si ma_cross deja de ser rentable con fill en next-open, todo cambia.

### S2 — Drawdown idéntico train/test (-2.18% exacto en ma_cross)
Coincidencia numérica exacta en dos periodos disjuntos es estadísticamente rara. Hipótesis del builder: artefacto de muestra pequeña (15-19 trades) + `cummax()` con equity casi monótona. Verificar que `compute_metrics` no tiene un bug que fije o pise el cálculo (p.ej. drawdown sobre equity normalizado mal reiniciado entre llamadas).

### S3 — Comisión posiblemente doble-contabilizada o mal aplicada
En `Trade`: `cost = (entry_price + exit_price) * size * commission`. Verificar dimensionalidad: `size` ya es notional/price (cantidad de activo), ¿el coste debería ser `qty * price * commission` por lado? Confirmar que comisión + slippage no se aplican dos veces al mismo lado (hay slippage en fill de entrada y en salida + comisión en ambos).

### S4 — Salidas intravela ambiguas
Conservador declarado: long SL mira `low[i]`, TP mira `high[i]`. Pero si en la misma vela se tocan AMBOS (low ≤ SL y high ≥ TP), el código asume SL primero (favorable a... ¿pessimista? — en realidad para long, si ambos se tocan en la vela, orden desconocido; el código elige SL = pesimista, OK, pero documentarlo). Además: la posición se abre al final de la iteración i, y sus salidas se evalúan desde i+1 — verificar que no puede salir en su propia vela de entrada (sería imposible en real y una vía de look-ahead).

### S5 — Walk-forward sin optimización real
`walk_forward()` no optimiza parámetros en train (los params son fijos). Solo mide consistencia OOS. No es un bug, es simplificación — pero el auditor debe confirmar que no se anuncia como "walk-forward con optimización" en documentación.

### S6 — yfinance y datos
`auto_adjust=True`, columnas a minúsculas, dropna. Verificar: ¿huecos de datos crypto? ¿el índice timezone-aware mezclado? ¿la ventana `period="5y"` es estable en re-ejecuciones (datos descargados en distintos días → resultados ligeramente distintos)? Considerar cachear CSV para reproducibilidad exacta.

## 4. Verificaciones estándar (además de las sospechas)

- **Indicadores:** comparar RSI/ATR/ADX contra implementación de referencia (p.ej. `pandas-ta` o TA-Lib) en un chunk de datos — tolerancia numérica razonable (EMA warm-up).
- **Métricas:** Sharpe anualizado correcto para daily (sqrt(365) en crypto daily), profit factor con pérdidas = 0 evitando div/0, win rate con trades cerrados en end_of_data.
- **Sesgo de supervivencia:** n/a aún (un activo), pero documentar.
- **Determinismo:** dos ejecuciones seguidas → mismos números (salvo descarga de datos).

## 5. Criterios de aprobación

| # | Criterio | Bloquea |
|---|---|---|
| A1 | S1 resuelto (fill en next-open o justificado con datos) o cuantificado su impacto | SÍ |
| A2 | S2 explicado: bug → corregir; artefacto → documentar con evidencia | SÍ |
| A3 | S3 verificado dimensionalmente, con test numérico de un trade manual | SÍ |
| A4 | S4 documentado (orden intravela explícito y por qué) | SÍ |
| A5 | Indicadores validados vs referencia (± tolerancia) | SÍ |
| A6 | Métricas verificadas con caso calculable a mano (2-3 trades) | SÍ |
| A7 | Resultados post-fix re-ejecutados y comparados con los actuales | SÍ |
| A8 | Test adversarial mínimo: estrategia aleatoria (coin-flip) debe dar ~0 menos costes | NO, deseable |

## 6. Resultados actuales (línea base pre-auditoría)

BTC-USD daily, 2021-10-05 → 2026-10-05 (1827 velas). Costes: 0.1% comisión + 0.05% slippage por lado.

| Estrategia | IS retorno | OOS retorno | OOS Sharpe | OOS DD | WF positivos |
|---|---|---|---|---|---|
| ma_cross | +30.1% | +24.4% | 1.63 | -2.18% | 12/16 |
| mean_reversion | -31.6% | -34.0% | -1.73 | -37.4% | 6/16 |
| breakout | -7.1% | -0.5% | 0.03 | -15.0% | 4/16 |
| trend_following | +60.9% | -20.0% | -0.45 | -30.6% | 5/16 |

**Estos números NO son confiables hasta que A1-A3 estén resueltos.** Si el look-ahead infla ma_cross, la conclusión "ma_cross es la ganadora" puede ser falsa.

## 7. Qué NO está en scope

- Paper trading, deliberación LLM, segundo cerebro, risk engine multi-pod (fases posteriores).
- Optimización de parámetros (grid/walk-forward con optimización — fase 2).
- Más activos/temporalidades.
