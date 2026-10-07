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
`AnthropicProvider` (lee `ANTHROPIC_API_KEY`) +
**`KimiProvider` (proveedor activo, commit `8efd0c3`)**.

**Estado real del proveedor (actualizado 2026-10-07):** la vía Anthropic quedó
descartada por proyecto (la cuenta no tiene crédito y no se recarga). El
proveedor activo es `KimiProvider`, verificado de punta a punta con llamadas
reales. Evidencia en `REGISTRO_B.md` §7 (primer smoke real) y en el smoke
re-ejecutado hoy:

```
$ source /root/maia/.env && ./venv/bin/python smoke_kimi_real.py
veredicto_global: no | size_final: 0.0 | motivo: al_menos_un_sombrero_veto
  hechos: veredicto=ajustar size_ajuste=0.006 reparado=False ...
  premortem: veredicto=no ... justificacion='Walkforward fragil en modo observación...'
  riesgo: veredicto=ajustar size_ajuste=0.006 ...
  beneficios: veredicto=ajustar size_ajuste=0.006 reparado=True ...
  creatividad: veredicto=ajustar size_ajuste=0.005 ...
  proceso: veredicto=no ...
sombreros con proveedor_indisponible: 0/6
SMOKE_KIMI_REAL_OK  (EXIT=0)
```

6/6 sombreros con JSON válido (1 reparado), 0 indisponibles, y el veredicto
global "no" es una deliberación real del modelo (consenso: dictamen
walk-forward frágil → no validar aún), no un veto por defecto. La distinción
`proveedor_indisponible` vs `veto_por_defecto_parse` queda verificada por
`verificar_deliberacion_schema.py`.

## Verificaciones

- `verificar_deliberacion_schema.py`: 25 casos sintéticos (8 sanos con
  veredicto/size coherentes y prompt hashes; 8 malformados × reparación-OK /
  veto-persistente; 1 proveedor caído) — todos con salida schema-valida y
  parseable, nunca una decisión sin parsear.
- `verificar_veto_riesgo.py`: 3 casos vetados siempre, con y sin LLM en el
  entorno; las 3 estrategias descartadas vetadas; caso sano no vetado.
- `verificar_kimi_provider.py`: smoke estructural del KimiProvider.
- Las verificaciones previas (paper sin dinero real estructural, MTM, A4/A7,
  a5, a6, h1, a8) siguen en PASS tras los cambios.

## Hallazgo real del modo sombra (actualizado 2026-10-07 con sizing 5%)

**Primera versión del hallazgo (2026-10-06, sizing 95%):** las 32 señales del
run del runner quedaban `vetada` por `sizing_sobre_limite` (0.95 > 0.05). Ese
escenario quedó descartado: Pablo decidió que la política real es SIZE_MAX=5%
y el backtest se ajusta a ella (ver `docs/sizing_05_resultado.md` — retorno
OOS de ma_cross +7.96% → +0.42%, mismas señales).

**Hallazgo actual (sizing 0.05):** el veto por sizing casi desaparece pero NO
del todo — 7/12 señales vetadas por `sizing_sobre_limite:0.0500075>0.05`, un
exceso de 7.5e-6 causado por el cálculo del sizing sobre cash vs equity
(detalle en `docs/sizing_05_resultado.md`). El dictamen walk-forward (FRÁGIL)
no cambia: es invariante ante el escalado del sizing. Pendiente de Pablo:
tolerancia epsilon en la regla o sizing sobre equity en el backtester; en modo
sombra solo se registra, nada se bloquea.

## Coste / tokens

Cada deliberación = 6 llamadas (1 por sombrero, +6 si repara). El runner
registra el detalle completo por sombrero en el journal; el uso de tokens de
API se podría añadir al registro cuando el proveedor funcione (la API
devuelve `usage` por llamada) — pendiente, bloqueado por el saldo.
