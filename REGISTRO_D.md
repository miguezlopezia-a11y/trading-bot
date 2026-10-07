# REGISTRO D — 3 estrategias candidatas de Opus (9 variantes)

**Fecha:** 2026-10-07 · **Ejecutor:** Sonnet Windows (en chat, Pablo pidió
"lee y ejecuta" sobre `tarea-trading-bot-3-estrategias-candidatas.md`).
**VPS:** 46.224.0.226. Desarrollado y probado en copia de trabajo
(`/root/trading-bot-fix-fase2/`), aplicado a un `git worktree` nuevo
(`/root/trading-bot-featbranch`, rama `feat/estrategias-candidatas`) — **main
de `/opt/trading-bot/` nunca tocado**, sigue en `62503a4` durante todo el
trabajo.

---

## 1. TDD — rojo antes de implementar

```
$ ./venv/bin/python verificar_estrategias_candidatas.py
Traceback (most recent call last):
  ...
ImportError: cannot import name 'sma_timing' from 'strategies'
```

## 2. Implementación: `sma_timing`, `tsmom`, `connors_rsi2` + 9 registros en `STRATEGIES`

Las 3 funciones tal como las especifica la tarea (código ya citado en el
archivo de tarea, verificado línea a línea contra el backtester real).
Registradas vía `functools.partial`: `sma_timing_{5,10,20,50,100,304}`,
`tsmom_{365,7}`, `connors_rsi2` (9 entradas nuevas, las 4 originales
intactas).

```
$ ./venv/bin/python verificar_estrategias_candidatas.py
  OK sma_timing: entry_long solo en el cruce al alza, nunca entry_short, SL/TP NaN, trailing_ma_period=period
  OK tsmom: entry_long solo en el cambio de signo, exit_long cuando el retorno vuelve a <=0, nunca cortos
  OK connors_rsi2: entry_long == rsi(2)<5 & close>sma(filtro) (3 filas), exit_long == close>sma(5) (197 filas), nunca cortos
  OK registro: las 9 variantes estan en STRATEGIES y devuelven las columnas del contrato sobre datos reales
VERIFICACION OK: 3 funciones + 9 variantes registradas, contrato de columnas respetado.
```

Los tests de `sma_timing` y `tsmom` verifican índices exactos calculados a
mano sobre series sintéticas pequeñas. El de `connors_rsi2` recalcula el
esperado llamando a `rsi()`/`sma()` de forma independiente sobre un escenario
realista (rampa + caída de 2 velas) en vez de adivinar índices — más robusto
contra errores de cálculo manual, sigue detectando errores de cableado
(operador, prioridad, columna equivocada).

## 3. Generalización de `walkforward_stability.py`

`STRATEGY = sys.argv[1] if len(sys.argv) > 1 else "ma_cross"` (compatible,
default intacto). `size_fraction=0.05` añadido a la llamada a `run_backtest`
— **antes no se pasaba ningún valor y corría al default del backtester
(0.95)**, pese a que la política de Risk (`SIZE_MAX=0.05`) ya estaba vigente
desde el 2026-10-07 para todo lo demás. Error real encontrado y corregido en
esta tarea, no solo en las 9 variantes nuevas — afecta también a `ma_cross`
corrido con este script desde ahora. Salida por estrategia:
`results/walkforward_stability_<estrategia>.json` (antes un único archivo
fijo, se habría pisado entre estrategias).

**Bug encontrado y corregido en el propio patch:** el mensaje `DICTAMEN:`
tenía `"ma_cross"` escrito literal en el f-string en vez de `{STRATEGY}` —
las primeras 9 corridas imprimieron el dictamen correcto pero con el nombre
de estrategia equivocado en el texto. Corregido antes de la corrida final
(ver diff en `src/walkforward_stability.py`, commit de esta rama).

```
$ ./venv/bin/python src/walkforward_stability.py
Walk-forward estabilidad ma_cross (size_fraction=0.05) — ...
DICTAMEN: ma_cross es FRAGIL en walk-forward post-fix (modo observacion en paper runner).
-> results/walkforward_stability_ma_cross.json guardado
```

Default (`ma_cross`, sin argumento) sigue funcionando — compatibilidad
verificada.

## 4. Walk-forward de las 9 variantes (+ ma_cross de referencia), `size_fraction=0.05`

Resumen agregado (4 configs de ventana, 57 folds por variante):

```
variante        dictamen  folds    cobertura  %pos    media%   cfg_eval
sma_timing_5    fragil    57/57    100.0      47.4    0.109    4/4
sma_timing_10   fragil    57/57    100.0      50.9    0.218    4/4
sma_timing_20   fragil    57/57    100.0      59.6    0.373    4/4
sma_timing_50   fragil    54/57    94.7       57.4    0.43     4/4
sma_timing_100  fragil    45/57    78.9       57.8    0.622    4/4
sma_timing_304  fragil    5/57     8.8        80.0    0.388    0/4
tsmom_365       fragil    0/57     0.0        0.0     0.0      0/4
tsmom_7         fragil    57/57    100.0      52.6    0.109    4/4
connors_rsi2    estable   12/57    21.1       66.7    0.18     2/4
ma_cross        fragil    47/57    82.5       55.3    0.073    4/4
```

Lectura completa, honesta, variante por variante (incluidos los 2 hallazgos
que no son "éxito" — `tsmom_365` sin un solo trade en 5 años de datos,
`sma_timing_304` sin evidencia suficiente) y el matiz sobre el ESTABLE de
`connors_rsi2` (cobertura 21%, 2 de 4 configs sin ningún trade): ver
`docs/estrategias_candidatas_resultado.md`.

**Ninguna variante queda en modo aprobación** — las 9 arrancarían en modo
observación igual que `ma_cross`, si se activaran.

## 5. Suite completa (9 scripts existentes de Fase 2 + el nuevo), reejecutada contra el código de esta rama

```
verificar_a4_a7_cierre.py          exit=0
verificar_deliberacion_schema.py   exit=0
verificar_exit_signal.py           exit=0
verificar_journal_idempotente.py   exit=0
verificar_kimi_provider.py         exit=0
verificar_mark_to_market_paper.py  exit=0
verificar_openrouter_provider.py   exit=0
verificar_paper_no_dinero_real.py  exit=0
verificar_veto_riesgo.py           exit=0
verificar_estrategias_candidatas.py exit=0
```

10/10, sin regresiones.

## 6. Rama y commit

Trabajo aplicado a `/root/trading-bot-featbranch` (worktree de
`/opt/trading-bot`, rama `feat/estrategias-candidatas` creada desde `main`
en `62503a4`). `main` del repo real nunca tuvo el working tree cambiado.
Commit de la rama, push a GitHub (no a `main`) — hash y salida de `git log`
en el mensaje de cierre de esta sesión.

## 7. Pendiente — explícito, no implícito

- **Nada mergeado a `main`.** Queda en `feat/estrategias-candidatas` para que
  Pablo/Sonnet Windows revisen antes de decidir.
- `connors_rsi2` ESTABLE es la aprobación más débil de las 10 filas —
  decisión de Pablo si se trata como señal real o se descarta por falta de
  datos, igual que `sma_timing_304`.
- `ESTRATEGIAS_DESCARTADAS` en `risk_veto.py` no se tocó — las 9 variantes
  nuevas no están ni incluidas ni excluidas ahí; si alguna se activa algún
  día en el paper runner, esa decisión (y el veto correspondiente) queda
  pendiente, fuera del alcance de esta tarea.
