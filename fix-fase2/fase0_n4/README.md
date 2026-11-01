# `fase0_n4/` — scripts de la Fase 0 de la tarea N4

**Esto NO es `auditoria_n4/`.** No contiene ningún paso de la §4 (Alcance) de
`tareas/tarea-nube-N4-procedencia-de-V-T-y-N.md`, que sigue **sin el OK de
Pablo** en su §6. Cada script aquí solo **reverifica** un punto de la §2 del
brief o una de las preguntas A-1…A-6 de la Fase 0, y existe por una razón: el
segundo agente del Maker/Verifier señaló (hallazgo 7) que la primera versión del
registro pegaba salidas sin script detrás, en un documento cuyo reproche central
a `potencia_fase_b.py` es precisamente que no cita su fuente.

Si se prefiere que la Fase 0 no deje ficheros nuevos, borrar este directorio no
pierde nada salvo la reproducibilidad de estas comprobaciones.

## Cómo correrlos

Desde `fix-fase2/`, con el `python3` del contenedor (3.13.18, numpy 2.5.3,
pandas 3.0.5). **Sin red**: todo sale de los CSV congelados del repo.
Ninguno escribe nada; todos imprimen a stdout. Ninguno pasa de ~3 minutos.

```bash
cd fix-fase2
python3 -I fase0_n4/fase0_a1_a2_procedencia_t_eff_y_v.py
python3 -I fase0_n4/fase0_a4_signo_ar1.py
python3 -I fase0_n4/fase0_a4b_mecanica_rho_negativo.py
python3 -I fase0_n4/fase0_liston_y_sensibilidad_rho.py
python3 -I fase0_n4/fase0_reverificacion_de_la_critica.py
```

## Qué comprueba cada uno

| script | qué reverifica | insumos |
|---|---|---|
| `fase0_a1_a2_procedencia_t_eff_y_v.py` | **A-1 y A-2.** Reproduce `T_eff=4336`, skew, curtosis y el Sharpe del portfolio con el ajuste AR(1) **reescrito a mano**, y las dos `V` (11 y 12 trials) | `results/portfolio_equity.csv`, `results/rigor_estadistico.json` |
| `fase0_a4_signo_ar1.py` | **A-4 y §2.5/§2.6.** Reejecuta las 11 variantes de Fase A y reproduce sus 11 `n_obs_eff`, ρ, trades y exposición; despeja el ρ que da 2188 | `data/btc_usd_5y_1d.csv`, `src/strategies.py`, `src/backtester.py` |
| `fase0_a4b_mecanica_rho_negativo.py` | **A-4.** Que la serie de `tsmom_365` son 728 ceros de 730 y que ρ≈−0.5 es un artefacto aritmético, con series sintéticas de control | ídem |
| `fase0_liston_y_sensibilidad_rho.py` | El listón 1.312, `SR₀` y el DSR, con una PSR/DSR **reimplementada desde `statistics.NormalDist`** sin importar `src/`; y **B-01**: la sensibilidad del listón a ρ | `results/rigor_estadistico.json` |
| `fase0_reverificacion_de_la_critica.py` | Las afirmaciones numéricas de la crítica del segundo agente: la causa del 0.7187 vs 0.7191, que anualizar da el mismo listón (hallazgo 11), la magnitud de **B-03** (listón 1.3118 → 1.8024) y el eje "días con posición" sobre el propio portfolio (hallazgo 12) | todos los anteriores |

Las salidas pegadas en el `## Registro de revisión némesis` del archivo de tarea
son las de estos scripts. **No se guardan JSON**: los JSON de salida pertenecen
al Alcance (`auditoria_n4/`), que no se ha ejecutado.

## Lo que estos scripts NO hacen

- **No ejecutan ningún paso de la §4.** En particular no tabulan el listón bajo
  construcciones alternativas de `V` para que alguien elija (4.2/4.3/4.6): el
  único recálculo de `V` fuera de la del expediente es el de B-03 (añadir las
  tres estrategias omitidas), y está ahí para **medir una magnitud que el
  registro había afirmado sin medir**, no como entregable.
- **No modifican nada** de `src/`, `results/`, `data/` ni ningún documento de
  dictamen. Solo leen.
- **No descargan nada.** La red a fuentes de precios está bloqueada (A-6) y
  ninguno la necesita.
