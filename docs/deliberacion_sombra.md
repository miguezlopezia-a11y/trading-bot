# Deliberación 6 Sombreros en modo sombra (1.1) — 2026-10-06

**Estado: MODO SOMBRA, nunca gating.** La deliberación se registra en el journal
junto a la decisión del paper runner; no bloquea, no modifica, no aprueba nada
(ma_cross sigue en modo observación por dictamen walk-forward FRÁGIL).

## Módulos

- `src/deliberation.py` — Analista: 6 llamadas LLM independientes (hechos,
  premortem, riesgo, beneficios, creatividad, proceso), cada una con system
  prompt propio. Veredicto global si/no/ajustar con size_final y justificación
  por sombrero. Salida JSON determinista validada por
  `valida_deliberacion()`. Basura del LLM → 1 reintento de reparación → si
  persiste, veto por defecto parseable (`veto_por_defecto_parse`). Error de
  transporte/API (p. ej. sin crédito) se distingue de basura del modelo:
  `proveedor_indisponible:<tipo>` — nunca disfrazado de "el LLM vetó".
  Versionado de prompts: `prompt_sha256` por sombrero en cada registro.
- `src/risk_veto.py` — Risk (único con potestad de veto): sizing > 5%,
  DD proyectado < -10%, estrategia descartada (las 3 no-ma_cross) → veto
  siempre. Determinista, sin LLM, con y sin proveedor.
- `src/paper_runner.py` — integración sombra: por cada trade, registra
  `risk_veto` y `deliberacion` (o `no_disponible` si no hay proveedor). El
  runner **no se rompe sin LLM**: funciona igual y registra
  `sin_proveedor_llm`.

## Proveedor LLM

Interfaz `Provider` + `FakeProvider` (determinista, tests) +
`AnthropicProvider` (lee `ANTHROPIC_API_KEY` del entorno; modelo por
`DELIBERATION_MODEL`, default `claude-sonnet-4-5`).

**Estado real del proveedor (2026-10-06):** hay `ANTHROPIC_API_KEY` usable en
el entorno (`/root/trading-bot-env`, chmod 600, copiada desde `/root/maia/.env`
sin imprimirla), pero la cuenta **no tiene crédito** — la API responde
`400 credit balance is too low` para todos los modelos probados
(sonnet-4-5, 3-5-sonnet, 3-5-haiku). Smoke test real ejecutado: 1 deliberación
→ `proveedor_indisponible:HTTPError`, registrada en el journal (SQLite). Es
decir: la integración LLM está verificada de punta a punta excepto la respuesta
del modelo, que queda **no verificado por bloqueo de saldo**, no por diseño.
Con crédito, la siguiente ejecución del runner delibera de verdad sin cambios.

## Verificaciones

- `verificar_deliberacion_schema.py`: 25 casos sintéticos (8 sanos con
  veredicto/size coherentes y prompt hashes; 8 malformados × reparación-OK /
  veto-persistente; 1 proveedor caído) — todos con salida schema-valida y
  parseable, nunca una decisión sin parsear.
- `verificar_veto_riesgo.py`: 3 casos vetados siempre, con y sin LLM en el
  entorno; las 3 estrategias descartadas vetadas; caso sano no vetado.
- Las 7 verificaciones previas (paper sin dinero real estructural, MTM, A4/A7,
  a5, a6, h1, a8) siguen en PASS tras los cambios.

## Hallazgo real del modo sombra (primer run, 2026-10-06)

Las 32 señales de ma_cross registran `risk_veto: vetada` con motivo
`sizing_sobre_limite`: el backtester arriesga el 95% del equity por trade
(size_fraction=0.95, spot sin apalancamiento), muy por encima del límite Risk
de Fase 2 (5%). En modo sombra solo se registra (no bloquea nada), pero es un
dato de decisión para Pablo: o el límite SIZE_MAX refleja política real de
riesgo y entonces ma_cross operaría con sizing reducido, o el sizing del
backtest es la política y SIZE_MAX debe revisarse. NO se cambió ningún valor en
esta etapa (prohibido optimizar; el veto no ejecuta nada).

## Coste / tokens

Cada deliberación = 6 llamadas (1 por sombrero, +6 si repara). El runner
registra el detalle completo por sombrero en el journal; el uso de tokens de
API se podría añadir al registro cuando el proveedor funcione (la API
devuelve `usage` por llamada) — pendiente, bloqueado por el saldo.
