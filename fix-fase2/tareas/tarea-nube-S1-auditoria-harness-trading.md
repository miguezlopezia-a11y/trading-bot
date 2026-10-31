# Tarea S1 (sesión en la nube) — Auditoría adversarial del harness de backtesting

**Estado:** CREADA 2026-10-29 por Sonnet (Claude Code, Windows). Sin ejecutar.
**Ejecutor:** sesión en la nube de Claude Code (no Kimi, no el VPS).
**Repo:** `miguezlopezia-a11y/trading-bot`, rama base `fase-b-recuperada`
(commit `d34b147`), rama de trabajo `nube/s1-auditoria-harness`.
**Alcance físico:** solo `fix-fase2/`. Ningún otro directorio.

> **Actualización 2026-10-29 13:50.** Este brief se escribió apuntando al
> snapshot de `bunker-2026/shared/trading-bot-fase1/`, que no tiene los CSV.
> Ese mismo día se recuperó del VPS el directorio real
> (`/root/trading-bot-fix-fase2`, que no estaba bajo git) y se subió a
> `trading-bot` en la rama `fase-b-recuperada`: código vivo, docs, results y
> los **35 CSV congelados verificados 35/35 contra su sha256**. Trabajar
> sobre esa rama, no sobre el snapshot. El snapshot sigue sirviendo para
> contrastar: si el código difiere entre ambos, **eso es un hallazgo** (el
> snapshot pasó por un hook de estilo que recortó comentarios).
**Duración estimada:** [estimado] 1-3 h de sesión. Sin límite duro; ver §7 timeouts.

---

## 1. Por qué existe esta tarea

El expediente del trading-bot tiene tres dictámenes encadenados, todos con
evidencia pegada:

| Fase | Resultado | Documento |
|---|---|---|
| A (11 variantes, BTC 5 años) | NINGUNA sobrevive. DSR máx 0.66, t máx 1.52 | `fix-fase2/docs/rigor_estadistico_resultado.md` |
| B (portfolio 10 activos, 12 años) | SEÑAL DÉBIL. Sharpe 1.01, t 3.48, DSR 0.72, pierde vs B&H (1.01 vs 1.16) | `fix-fase2/docs/portfolio_resultado.md` |
| B-reevaluación (walk-forward + potencia + supervivencia) | P1 y P3 SUPERADOS, DSR sigue 0.72 | `fix-fase2/docs/fase_b_reevaluacion_resultado.md` |
| TimesFM 2.5 (H1/H2) | MUERTA. dir_acc 0.4925 agregada, peor que naive | `fix-fase2/docs/timesfm_fase2_resultado.md` |

Todas esas cifras salen del **mismo harness**: `src/backtester.py`,
`fix-fase2/src/portfolio_runner.py`, `fix-fase2/src/rigor_estadistico.py`.
Si ese harness tiene un defecto sistemático, los cuatro dictámenes son ruido
—tanto las muertes como la señal débil superviviente— y cualquier cómputo
que se gaste encima hereda el defecto.

Precedente que lo justifica: en la Fase 2 de TimesFM se encontró un bug real
de harness (PEFT in-place, `zeroshot == lora_ft`) que falseaba la comparación
entre modelos, y se encontró **por una prueba física, no por lectura**. No es
una hipótesis abstracta: ya ha pasado una vez en este proyecto.

**Esta tarea no busca una estrategia. Busca errores en el instrumento de
medida.** Un hallazgo que invalide un dictamen es un éxito de esta tarea,
no un fracaso del proyecto.

---

## 2. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

Dos pasos separados y ambos obligatorios. El paso B no es opcional ni se
cumple con "parece bien".

### Paso A — Verificación de hechos

Reverificar de forma independiente, con comandos reales cuya salida se pega
en el registro. Que Sonnet lo haya comprobado en otra ventana **no cuenta**:

- [ ] `shared/trading-bot-fase1/src/backtester.py`, `indicators.py`,
      `strategies.py`, `run_backtest.py` existen; anotar sha256 de cada uno.
- [ ] `fix-fase2/src/` contiene los 14 módulos citados en §1; anotar sha256.
- [ ] Los 15 `verificar_*.py` de `fix-fase2/` existen y **se ejecutan hoy**.
      Pegar la salida completa. El expediente afirma "suite 15/15 PASS"
      (`fase_b_reevaluacion_resultado.md`) — confirmar o desmentir con la
      salida real, no citarla.
- [ ] `data/btc_usd_5y_1d.csv` existe y su sha256 coincide con
      `btc_usd_5y_1d.sha256` y con el campo `sha256` de
      `btc_usd_5y_1d.meta.json`. **Normalización exacta**: `sha256sum` sobre
      el archivo tal cual, sin reescribir finales de línea. Si los tres
      valores no coinciden entre sí, es hallazgo, no ruido.
- [ ] `data/multi/` y `data/multi_muertos/` contienen `.meta.json` y
      `.sha256` pero **ningún `.csv`** (verificado por Sonnet 2026-10-29 —
      reverificar). Consecuencia a confirmar: ningún backtest multi-activo es
      reproducible hoy desde este repo. Ese es el objeto de la tarea S3; aquí
      solo se constata.
- [ ] `README.md` del snapshot dice que es copia estática de
      `/opt/trading-bot/src/` del VPS y que "no sirve para verificar nada con
      evidencia real". Leerlo entero y anotar qué partes de esta tarea quedan
      afectadas por esa limitación.

### Paso B — Ataque adversarial al planteamiento de ESTA tarea

No a la estrategia: a este documento. Mínimo a responder por escrito:

- ¿Cuál es la asunción más débil de esta tarea? (candidata honesta: que un
  snapshot con comentarios recortados por un hook de estilo es equivalente
  al código vivo del VPS — si el hook tocó una línea de lógica y no solo un
  comentario, se está auditando un código que nadie ejecutó nunca).
- ¿Qué alternativa se descartó sin justificar? (candidata: auditar
  directamente en el VPS por SSH, que es lo único que ve el código vivo y
  los datos reales; se descartó porque una sesión en la nube no tiene SSH —
  ¿invalida eso la tarea entera o solo una parte?).
- ¿Qué objeción le pondría un enemigo a la lista de defectos de §3? ¿Qué
  clase de error **no** está en esa lista y debería?
- Si no encuentras ninguna objeción real, **di explícitamente por qué no la
  encontraste**. "Parece correcto" no es una respuesta admisible.

### Salida de la Fase 0

Escribir al final de este mismo archivo una sección
`## Registro de revisión némesis — S1` con: lo confirmado y su evidencia
(salidas pegadas, hashes), lo que no cuadra, hallazgos nuevos con severidad
(CRÍTICO/ALTO/MEDIO/BAJO), y el plan exacto de §3 corregido según lo
encontrado.

**Y PARAR AHÍ.** No ejecutar §3 en la misma pasada. Commit + push de la rama
con el registro, y fin de la sesión. La ejecución del Alcance solo arranca
cuando Pablo lea ese registro y escriba su OK en este archivo. Esto es norma
del proyecto (`shared/NEMESIS.md`, y el punto 10 del checklist de task
files), no una formalidad: en este mismo proyecto, el 2026-10-28, un agente
ejecutó una decisión de producto sin parar a pedir OK y eso quedó anotado
como el patrón a no repetir.

---

## 3. Alcance (NO ejecutar hasta OK escrito de Pablo)

Auditar el harness buscando las clases de defecto que inflan o destruyen
resultados de backtest. Para **cada una**: una prueba ejecutable que la
detecte, no una lectura del código.

### 3.1 Look-ahead bias

Que ninguna decisión de la barra `t` use información de `t` o posterior.

- Prueba exigida: inyectar en una copia de los datos un shock artificial
  conocido en la barra `t+1` (p. ej. multiplicar el cierre por 3) y
  comprobar que la posición en `t` **no cambia**. Si cambia, hay look-ahead.
- Repetir para: señal de entrada, señal de salida, cálculo de indicadores
  (`indicators.py`), sizing (EWMA de volatilidad — el caso más propenso: una
  EWMA que incluye la barra actual al decidir el tamaño de esa barra ya es
  look-ahead), y los vetos de riesgo (`risk_veto.py`).
- Para la covarianza EWMA completa de `portfolio_runner.py`: comprobar que la
  matriz usada para ponderar el día `t` se construye solo con datos `< t`.

### 3.2 Costes y fricción

El expediente dice "costes del backtester" sin cifra visible en los
documentos leídos.

- Localizar en el código el valor exacto de comisión, spread y slippage
  aplicados. Pegar la línea con `archivo:línea`.
- Comprobar que se aplican **en ambos lados** (entrada y salida) y sobre el
  nominal correcto, no sobre el capital total.
- Rebalanceo diario con sizing Carver: comprobar que el coste del
  **rebalanceo** se cobra, no solo el de abrir y cerrar posición. Un
  portfolio que rebalancea 10 activos a diario durante 4404 días y no paga
  esos ajustes tiene un Sharpe fantasma. Cuantificar: ¿cuántas operaciones de
  rebalanceo se ejecutan en total y qué coste acumulado suponen?
- Prueba de sensibilidad: recorrer el backtest de Fase B con costes ×2, ×5 y
  ×10 y reportar cómo se mueven Sharpe, t y DSR. Si el edge muere con ×2, la
  "señal débil" es una ilusión de fricción barata.

### 3.3 Survivorship y sesgo de selección de datos

- `multi_muertos/` cubre 5 caídos elegidos por un criterio documentado
  (top-20 market-cap histórico 2017-2021, hoy >85% bajo máximo). El propio
  documento admite que "top-N por market-cap histórico congelado seguiría
  siendo mejor y no se hizo". Evaluar cuánto sesgo residual queda y si es
  acotable sin datos nuevos.
- Verificar el caso FIL: el documento dice que yfinance da datos desde
  2017-12, anterior a su listado real. Comprobar si hay más casos iguales
  entre los 15 activos y qué efecto tienen sobre el resultado agregado.

### 3.4 Reproducibilidad numérica

- Reejecutar lo que sea reejecutable hoy (lo single-asset de BTC, que sí
  tiene CSV) y comparar cifra a cifra con las publicadas en
  `rigor_estadistico_resultado.md`.
- Cualquier discrepancia, por pequeña que sea, se documenta. Una diferencia
  en el cuarto decimal puede ser un generador aleatorio sin semilla fija; eso
  es un hallazgo (el bootstrap y el Monte Carlo deben tener semilla fijada y
  anotada).
- Comprobar que existe semilla fija y determinismo declarado en:
  bootstrap por bloques, cualquier remuestreo, y cualquier orden de
  iteración que dependa de un `set`/`dict` sin ordenar.

### 3.5 La implementación del DSR

Es la métrica de la que cuelga todo el proyecto.

- Verificar la fórmula implementada en `rigor_estadistico.py` contra la
  fuente original (Bailey & López de Prado 2014, SSRN 2460551) o una
  implementación de referencia revisada. **Citar de dónde sale cada término**
  (sigma_SR con skew y curtosis, SR esperado bajo N intentos).
- Comprobar el manejo de `N` (número de trials): el expediente usa N=12.
  Verificar que ese 12 está contado de forma consistente en todos los sitios
  donde se calcula un DSR, y que no hay ningún cálculo con un N distinto
  silenciosamente.
- Prueba sintética: series con Sharpe conocido y N conocido deben dar el DSR
  que predice la fórmula. Si `potencia_fase_b.py` ya hace esto, reejecutarlo
  y pegar la salida.

### 3.6 Lo que NO entra en esta tarea

- No proponer estrategias nuevas.
- No cambiar ninguna métrica, umbral ni criterio de aceptación. Si crees que
  una métrica está mal elegida, se documenta como hallazgo; **no se sustituye**.
  Cambiar la métrica después de ver el resultado invalida el expediente
  entero.
- No ejecutar nada contra el VPS ni contra dinero real.
- No tocar `paper_runner.py`, `risk_veto.py` ni `deliberation.py` salvo para
  leerlos.

---

## 4. Restricciones NO-GO (bloqueantes)

- **NO-GO** — Ninguna orden real, ningún broker, ninguna API de trading.
  Esta tarea no se conecta a ningún exchange ni con credenciales ni sin ellas.
- **NO-GO** — No declarar un criterio cumplido sin la salida real del comando
  que lo demuestra, pegada en el registro.
- **NO-GO** — No modificar ningún `.csv`, `.sha256` ni `.meta.json` existente.
  Son evidencia congelada. Si un dato hace falta transformado, se escribe una
  copia nueva con nombre distinto.
- **NO-GO** — No mergear a `main`. El trabajo vive en
  `nube/s1-auditoria-harness` y se entrega por PR.
- **NO-GO** — No ejecutar §3 sin el OK escrito de Pablo en §8.
- **NO-GO** — Si el repo no contiene algún archivo citado en §2, **parar y
  reportar**, nunca improvisar con contexto equivalente. Improvisar sobre un
  documento no encontrado es la causa raíz documentada de un incidente previo
  en este proyecto (11 archivos borrados sin querer).

---

## 5. Definition of Done

Ningún punto se da por hecho sin script ejecutado y salida pegada.

- [ ] `## Registro de revisión némesis — S1` escrito, con los dos pasos A y B.
- [ ] Un script por cada subapartado de §3 (3.1 a 3.5), en
      `fix-fase2/auditoria_s1/`, ejecutable de forma independiente y con
      salida determinista.
- [ ] `fix-fase2/docs/auditoria_harness_s1.md` con: tabla de hallazgos
      (id, archivo:línea, tipo, ¿real?, ¿afecta a qué dictamen?, severidad),
      y para cada hallazgo la prueba que lo demuestra.
- [ ] Veredicto explícito sobre cada uno de los cuatro dictámenes de §1:
      **se sostiene** / **queda en duda** / **queda invalidado**, con el
      hallazgo que lo justifica.
- [ ] Si no se encuentra ningún defecto: decirlo así, y además decir qué
      clases de defecto quedaron sin poder probarse por falta de datos o de
      acceso al VPS. Una auditoría que no encuentra nada y no declara sus
      límites no es una auditoría.
- [ ] PR abierto contra `main` con todo lo anterior. Sin mergear.

---

## 6. Entregables

1. `fix-fase2/docs/auditoria_harness_s1.md` — el informe.
2. `fix-fase2/auditoria_s1/*.py` — los scripts de prueba.
3. `## Registro de revisión némesis — S1` al final de este archivo.
4. PR abierto, sin mergear.

---

## 7. Decisiones bajo presión (número, no criterio)

- Si un script de prueba tarda **más de 20 minutos**, abortarlo, anotar el
  caso y seguir con el siguiente. No esperar indefinidamente.
- Si la suite `verificar_*.py` falla en la Fase 0: **parar la tarea entera**
  y reportar. Una suite roja invalida la premisa de §1 y hay que decidir
  antes de seguir.
- Si falta una dependencia de Python que no se puede instalar: anotar cuál,
  saltar esa prueba, y declararla explícitamente como no ejecutada en el
  informe. Nunca sustituirla por una "equivalente" sin decirlo.
- Si el repo no trae los datos necesarios para una prueba: esa prueba se
  declara **no ejecutable hoy** y se enlaza con la tarea S3. No se inventan
  datos sintéticos haciéndolos pasar por reales (sí se permiten sintéticos
  **declarados como tales** para validar un script antes de usarlo con datos
  reales — es el patrón TDD que ya usa este proyecto).

---

## 8. OK de Pablo

> Pendiente. Esta sección la rellena Pablo después de leer el
> `## Registro de revisión némesis — S1`. Sin texto aquí, la §3 no se ejecuta.

---

## 9. Sincronía entre documentos

Si esta auditoría invalida o pone en duda un dictamen, hay que actualizar
**ambos** sitios, no solo uno:

- el documento del dictamen afectado (`fix-fase2/docs/*.md`), y
- `shared/estado-y-siguiente-paso.md`, que es el ancla que lee cualquier
  agente que se incorpore.

Un hallazgo que solo vive en el informe de auditoría y no llega al ancla es
un hallazgo que el próximo agente no verá.

---

## Registro de revisión némesis — S1

**Ejecutado:** 2026-10-31 · sesión en la nube de Claude Code (Opus 5).
**Rama:** `nube/s1-auditoria-harness` (creada desde `fase-b-recuperada`).
**Alcance de esta pasada:** solo §2. La §3 NO se ha ejecutado ni preparado.
**Entorno:** Python 3.13.18, numpy 2.5.3, pandas 3.0.5. `scipy` y `yfinance`
instalados por esta sesión (no venían). `torch` y `timesfm` no disponibles.
Red saliente: política del contenedor **bloquea Yahoo Finance** (evidencia en
A-05).

### Paso A — Verificación de hechos

Cada punto lleva el comando y su salida literal. Donde el comando falla o
devuelve vacío, el resultado es **no lo sé**, no "está bien".

---

#### A-01 · Rama y commit base — **NO CUADRA (benigno)**

El brief fija la base en `d34b147`. El HEAD real de `fase-b-recuperada` es
`adad9e7`.

```
$ git log --all --oneline | head -3
adad9e7 Anade los tres briefs de las sesiones en la nube (S1 auditoria del harness, S2 literatura, S3 ampliacion de T)
d34b147 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
663db2c Fase A rigor estadistico: DSR (Bailey-LdP 2014), block bootstrap, t>3, benchmark exposicion igualada — ninguna de las 11 variantes sobrevive
```

`d34b147` existe y es `HEAD~1`. `adad9e7` solo añade los tres briefs, no toca
código ni datos. El desajuste es benigno pero el ancla del brief está vieja.

---

#### A-02 · `shared/` — **NO EXISTE. Dos puntos de §2 quedan sin verificar**

```
$ ls -d shared
ls: cannot access 'shared': No such file or directory
$ find . -name "README*" -not -path "./.git/*"
(salida vacía)
```

Consecuencias directas:

- El primer punto de §2 (`shared/trading-bot-fase1/src/backtester.py`,
  `indicators.py`, `strategies.py`, `run_backtest.py`) **no es verificable en
  este repo**: esa ruta no existe.
- El último punto de §2 (leer el `README.md` del snapshot) **no es
  verificable**: no hay ningún README en todo el repo.
- §9 manda actualizar `shared/estado-y-siguiente-paso.md`. Ese archivo no
  existe aquí. Un hallazgo que deba llegar al ancla **no tiene ancla a la que
  llegar** desde esta sesión.

Según §4 NO-GO ("si el repo no contiene algún archivo citado en §2, parar y
reportar"), esto se reporta y no se improvisa con equivalentes.

---

#### A-03 · Los 4 módulos citados sí existen en `src/` de la raíz — **CONFIRMADO**

```
$ sha256sum src/backtester.py src/indicators.py src/strategies.py src/run_backtest.py
265ab6b44ee9ada0ae2aaf5bb120d983c4d5a606400478f8907419404871fcf0  src/backtester.py
dcb8d2cac94b31eb01e91d66c997d447f0c3b4e4b52de56b5e35ccebf6e62468  src/indicators.py
c800b640462253dbe00a35d68e5cc59d8fa04eeb17abe8de33cd3414c363a66d  src/strategies.py
b35b87bf197b47b7084d066b53b787eb15f56b182e7af7261f1f653d0119d068  src/run_backtest.py
```

Comparación `src/` (raíz) contra `fix-fase2/src/`, archivo a archivo por
sha256:

```
IDENTICO  backtest_sizing05.py      IDENTICO  rigor_estadistico.py
IDENTICO  backtester.py             IDENTICO  risk_veto.py
IDENTICO  brain.py                  IDENTICO  run_backtest.py
IDENTICO  deliberation.py           IDENTICO  strategies.py
IDENTICO  indicators.py             IDENTICO  walkforward_stability.py
IDENTICO  paper_runner.py
```

Los 11 comunes son **byte-idénticos**. No hay divergencia snapshot/vivo
detectable dentro de este repo (ver objeción B-11: eso no significa que sea el
código que produjo los resultados).

---

#### A-04 · `fix-fase2/src/` tiene **19** módulos, no 14 — **NO CUADRA**

```
$ ls fix-fase2/src/*.py | wc -l
19
```

sha256 de los 19:

```
735223d65db6bb086903ec4ce484def614580fcf174724e6fc40135f5d14fa71  backtest_sizing05.py
265ab6b44ee9ada0ae2aaf5bb120d983c4d5a606400478f8907419404871fcf0  backtester.py
8a7cdac387192c2cc0ab6ddc0d2b409b188ef7daaa749ee885393c5adc429cee  backtester_paso2_ref.py
28ceb23c2804f499cb3980a023b1b82734b9a94e09bbf8e01f349d919f9530e3  brain.py
d5e2a1093bac04bfe9f441a0fd30888b468dc4205ca777342cedfee34ca7bff2  deliberation.py
dcb8d2cac94b31eb01e91d66c997d447f0c3b4e4b52de56b5e35ccebf6e62468  indicators.py
5b8e2f29806aa54d5bf89491a403c2957f62cd11fe68cbbff0517fc680ca431e  paper_runner.py
363c4a3ffe4372e3dd111a734f5f87ba088c80e0096acea0929bb29611343663  portfolio_bateria.py
a7677d26deebd414a309a12aad8b14e4d288f66d196c52b34074b242a96fdd73  portfolio_runner.py
f4aa99385f594f5e0c320bc55312865a404eb08714842e951a842fc2251521ec  portfolio_supervivencia.py
e81db2f09056bdd9a9aac5bc421c515cd0e1cfad99c560db95ebcb086f036c45  portfolio_walkforward_temporal.py
b0b08bbfd931e95842a0fb26e34ca574e1962586299678189b18cc98d97e3538  potencia_fase_b.py
58217a1ee751dbccf0ab8a1bad00df509264ada5860aa04e77f4195511ade64c  rigor_estadistico.py
fca6645ace2113af5df3ea929aa41b7abdb360c0208bb523b160f7f131b2726c  risk_veto.py
b35b87bf197b47b7084d066b53b787eb15f56b182e7af7261f1f653d0119d068  run_backtest.py
c800b640462253dbe00a35d68e5cc59d8fa04eeb17abe8de33cd3414c363a66d  strategies.py
d5486b764c7b6fdb2dd1c60ee53406d9bb6c72d66566b07c2fe82a6f2d38ccbe  timesfm_harness.py
04bad9032c6311d9b1fc4bf2cb7fa5f13cd6b7215c917415bf75d86214199a10  timesfm_t3_zeroshot.py
761e95eb69dbddb6ae0f6f62bae7e9465a9f52a508bab86ef5de87777bcb064c  walkforward_stability.py
```

§1 habla de "los 14 módulos citados". Son 19. Hay además un **segundo
backtester** (`backtester_paso2_ref.py`) que el brief no menciona en ningún
sitio y que es la línea base de `verificar_invariante_h1.py`. Difiere del
principal en dos cosas: no tiene señales `exit_long`/`exit_short`, y dimensiona
con `equity * size_fraction` en vez de `cash * size_fraction`. Ambos rellenan
en `open[i+1]`.

---

#### A-05 · La suite `verificar_*.py`: **23 scripts, no 15. Hoy da 16 PASS / 7 FAIL** — **NO CUADRA**

```
$ ls fix-fase2/verificar_*.py | wc -l
23
```

Ejecución completa, hoy, con timeout de 300 s por script (`rc=0` es PASS):

```
verificar_a4_a7_cierre.py                          rc=0    0s
verificar_a5_indicadores.py                        rc=1    0s
verificar_a6_metricas.py                           rc=0    1s
verificar_a8_adversarial.py                        rc=1    0s
verificar_deliberacion_schema.py                   rc=0    0s
verificar_estrategias_candidatas.py                rc=0    0s
verificar_exit_signal.py                           rc=0    1s
verificar_invariante_h1.py                         rc=1    0s
verificar_journal_idempotente.py                   rc=1    0s
verificar_kimi_provider.py                         rc=0    1s
verificar_mark_to_market_paper.py                  rc=0    0s
verificar_openrouter_provider.py                   rc=0    0s
verificar_opus_fase2.py                            rc=1    1s
verificar_paper_no_dinero_real.py                  rc=0    0s
verificar_portfolio_sintetico.py                   rc=0    0s
verificar_portfolio_walkforward_sintetico.py       rc=0   11s
verificar_potencia_sintetico.py                    rc=0    0s
verificar_rigor_sintetico.py                       rc=0   26s
verificar_rsi_hidden_divergence.py                 rc=0    0s
verificar_supervivencia_sintetico.py               rc=0    0s
verificar_timesfm_t1_harness.py                    rc=1    0s
verificar_timesfm_t2_diferencial.py                rc=1    0s
verificar_veto_riesgo.py                           rc=0    0s
```

**Los 7 fallos son de entorno, ninguno de lógica.** Causa raíz de cada uno:

| Script | Causa |
|---|---|
| `verificar_a5_indicadores.py` | descarga yfinance en vivo |
| `verificar_a8_adversarial.py` | descarga yfinance en vivo |
| `verificar_invariante_h1.py` | `run_backtest.py` importa yfinance |
| `verificar_opus_fase2.py` | `run_backtest.py` importa yfinance |
| `verificar_journal_idempotente.py` | `FileNotFoundError: '/root/trading-bot-env'` |
| `verificar_timesfm_t1_harness.py` | `ModuleNotFoundError: timesfm` |
| `verificar_timesfm_t2_diferencial.py` | `ModuleNotFoundError: torch` |

Instalé `yfinance 1.7.0` y `scipy 1.18.1` y reejecuté los cuatro de yfinance.
**Siguen fallando**, porque la política de red del contenedor bloquea Yahoo:

```
$ python3 verificar_a8_adversarial.py
1 Failed download:
['BTC-USD']: ConnectionError('Failed to perform, curl: (7) CONNECT tunnel failed, response 403...')
...
IndexError: single positional indexer is out-of-bounds
```

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
"recentRelayFailures": [
  {"kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"fc.yahoo.com:443"},
  {"kind":"connect_rejected","detail":"gateway answered 403 to CONNECT (policy denial or upstream failure)","host":"query2.finance.yahoo.com:443"}, ...
```

Dos hallazgos propios aquí, independientes del entorno:

1. **4 de los 23 verificadores descargan datos en vivo en lugar de usar los
   CSV congelados.** Un verificador cuyo insumo cambia cada día no es una
   comprobación congelada, sea cual sea el entorno. Severidad **ALTO**.
2. Ninguno de los cuatro **comprueba que la descarga trajo datos**: fallan con
   `IndexError` sobre un DataFrame vacío, no con un error claro. Severidad
   **MEDIO**.

§7 ordena: "si la suite falla en la Fase 0, parar la tarea entera y reportar".
Se para. Matiz necesario: la suite **no está roja por lógica**; está roja por
dependencias y por red. Los 16 que corren, pasan.

---

#### A-06 · "suite completa 15/15 PASS" — **NO VERIFICABLE. Su evidencia no está en el repo**

`fase_b_reevaluacion_resultado.md` afirma: *"Sintéticos 3/3 antes de datos
reales + suite completa 15/15 PASS (12 previos + 3 nuevos). Salidas en
`REGISTRO_F.md`"*. Ese archivo no existe, ni en el árbol ni en la historia:

```
$ find . -name "REGISTRO*" -not -path "./.git/*"
./REGISTRO_D.md
$ git log --all --diff-filter=A --name-only --format="" | grep -i registro | sort -u
REGISTRO_D.md
```

El mismo documento dice *"Rama: `fase-b-multiactivo` (commits nuevos sobre
`9249cf4`)"*. Ese commit no existe en este repo:

```
$ git cat-file -t 9249cf4
fatal: Not a valid object name 9249cf4
$ git branch -a --list "*multiactivo*"
(salida vacía)
```

Resultado: **no lo sé**. La afirmación 15/15 no se confirma ni se desmiente;
su evidencia y su commit de referencia no están aquí. Hoy la suite son 23
scripts con 16 PASS.

---

#### A-07 · `btc_usd_5y_1d.csv` — existe, pero **no tiene `.sha256` ni `.meta.json`** — **NO CUADRA**

El brief lo sitúa en `data/`. Está en `fix-fase2/data/`:

```
$ sha256sum fix-fase2/data/btc_usd_5y_1d.csv
1c393a0095688754c8e5eeeca222077ca7f03eb493e080b50fc33c03b5dfc725  fix-fase2/data/btc_usd_5y_1d.csv
$ wc -l fix-fase2/data/btc_usd_5y_1d.csv
1828 fix-fase2/data/btc_usd_5y_1d.csv
$ head -2 fix-fase2/data/btc_usd_5y_1d.csv
date,open,high,low,close,volume
2021-10-06,51486.6640625,55568.46484375,50488.19140625,55361.44921875,49034730168
```

Búsqueda de sus anclas de integridad en todo el repo:

```
$ find . -name "*btc_usd_5y*" -not -path "./.git/*"
./fix-fase2/data/btc_usd_5y_1d.csv
```

**No existe `btc_usd_5y_1d.sha256` ni `btc_usd_5y_1d.meta.json`.** La
comprobación a tres bandas que pide §2 es imposible: solo hay una banda. El
único corroborante es el hash escrito a mano en el docstring de
`rigor_estadistico.py:5` (`sha256 1c393a00...`), que **coincide** con el
calculado arriba — pero un hash en un comentario no es un ancla congelada:
está en el mismo commit que el CSV y lo edita quien edite el archivo.

Esto importa porque este CSV es el **único** insumo de los 11 dictámenes de
Fase A. Severidad **ALTO**.

---

#### A-08 · `multi/` y `multi_muertos/` **SÍ tienen los CSV** — la afirmación de §2 es **FALSA**

§2 dice: *"contienen `.meta.json` y `.sha256` pero **ningún `.csv`** (verificado
por Sonnet 2026-10-29 — reverificar)"*. Reverificado: es falso.

```
$ ls fix-fase2/data/multi/*.csv | wc -l
20
$ ls fix-fase2/data/multi_muertos/*.csv | wc -l
15
$ git ls-files fix-fase2/data | grep -c "\.csv$"
36
```

35 CSV multiactivo + `btc_usd_5y_1d.csv` = 36, todos trackeados en git.
Verificación de los 35 contra su `.sha256`:

```
$ cd fix-fase2/data/multi      && for f in *.csv; do sha256sum -c "$f.sha256"; done
ada_usd_20261007.csv: OK      doge_usd_20261009.csv: OK     ltc_usd_20261007.csv: OK
ada_usd_20261009.csv: OK      eth_usd_20261007.csv: OK      ltc_usd_20261009.csv: OK
avax_usd_20261007.csv: OK     eth_usd_20261009.csv: OK      sol_usd_20261007.csv: OK
avax_usd_20261009.csv: OK     link_usd_20261007.csv: OK     sol_usd_20261009.csv: OK
bnb_usd_20261007.csv: OK      link_usd_20261009.csv: OK     xrp_usd_20261007.csv: OK
bnb_usd_20261009.csv: OK                                    xrp_usd_20261009.csv: OK
btc_usd_20261007.csv: OK      doge_usd_20261007.csv: OK
btc_usd_20261009.csv: OK

$ cd fix-fase2/data/multi_muertos && for f in *.csv; do sha256sum -c "$f.sha256"; done
ada_usd_20261009.csv: OK   bnb_usd_20261009.csv: OK   eth_usd_20261009.csv: OK   link_usd_20261009.csv: OK   xlm_usd_20261009.csv: OK
avax_usd_20261009.csv: OK  btc_usd_20261009.csv: OK   fil_usd_20261009.csv: OK   ltc_usd_20261009.csv: OK    xrp_usd_20261009.csv: OK
bch_usd_20261009.csv: OK   doge_usd_20261009.csv: OK  icp_usd_20261009.csv: OK   sol_usd_20261009.csv: OK
```

**35/35 OK.** La "Actualización 2026-10-29" de la cabecera del brief tiene
razón y el checklist de §2 contradice a su propia cabecera. Consecuencia: la
premisa "ningún backtest multiactivo es reproducible hoy desde este repo" es
**falsa por el lado de los datos** — los datos están y están verificados. Lo
que impide reproducirlo es otra cosa (A-10), y eso cambia también el
planteamiento de la tarea S3.

---

#### A-09 · `portfolio_resultado.md` — **NO EXISTE, y nunca existió**

La tabla de §1 cita `fix-fase2/docs/portfolio_resultado.md` como el documento
del dictamen de Fase B (el de la "SEÑAL DÉBIL").

```
$ ls fix-fase2/docs/ | grep portfolio
(salida vacía)
$ find . -name "portfolio_resultado*" -not -path "./.git/*"
(salida vacía)
$ git log --all --diff-filter=A --name-only --format="" | grep -i portfolio_resultado
(salida vacía)
```

Los otros tres documentos de la tabla sí están:

```
OK      fix-fase2/docs/rigor_estadistico_resultado.md
FALTA   fix-fase2/docs/portfolio_resultado.md
OK      fix-fase2/docs/fase_b_reevaluacion_resultado.md
OK      fix-fase2/docs/timesfm_fase2_resultado.md
```

Las cifras del dictamen de Fase B **sí** son recuperables, de otras dos
fuentes: la tabla del Paquete 3 de `fase_b_reevaluacion_resultado.md` y
`fix-fase2/results/portfolio_runner.json`. Pero el documento primario del
dictamen más importante del expediente no está en el repo. Severidad **ALTO**.

---

#### A-10 · `load_or_download()` no puede alcanzar los CSV congelados — **HALLAZGO NUEVO, CRÍTICO**

`portfolio_runner.py:116-132` compone el nombre del fichero de caché con la
**fecha de hoy**:

```
$ sed -n '122,124p' fix-fase2/src/portfolio_runner.py
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(DATA_DIR, f"{ticker.lower().replace('-', '_')}_{stamp}.csv")
        if os.path.exists(path):
```

Los congelados llevan dos sellos, y hoy es otro:

```
$ date -u +%Y%m%d
20261031
$ ls fix-fase2/data/multi/*.csv | sed 's/.*_\([0-9]\{8\}\)\.csv/\1/' | sort -u
20261007
20261009
```

No hay parámetro de ruta, ni override, ni fallback al sello más reciente.
Prueba empírica: copio los 20 CSV congelados a `data/multi/` y llamo a la
función:

```
$ ls data/multi/*.csv | wc -l
20
$ python3 -c "import sys; sys.path.insert(0,'src'); from portfolio_runner import load_or_download; ..."
DATA_DIR = data/multi | activos = 10
Failed to get ticker 'BTC-USD' reason: ... CONNECT tunnel failed, response 403 ...
1 Failed download:
['BTC-USD']: ConnectionError(...)
EXCEPCION: IndexError index 0 is out of bounds for axis 0 with size 0
```

Con los 20 CSV verificados delante, el loader **los ignora y va a la red**.

Consecuencias:

- Cualquier reejecución del portfolio de Fase B hecha un día distinto del
  2026-10-07 o 2026-10-09 **no usa los datos congelados**. Si hay red,
  descarga datos frescos, escribe un fichero nuevo con el sello de hoy y
  sigue, en silencio. Si no hay red, revienta.
- §3.2 (sensibilidad de costes ×2/×5/×10), §3.3 (supervivencia) y §3.4
  (reproducibilidad numérica) **no son ejecutables hoy** sin modificar antes el
  loader. No porque falten datos — están y verifican 35/35 — sino porque el
  código no los alcanza.
- La regla de decisión de §7 ("si el repo no trae los datos necesarios, prueba
  no ejecutable hoy, enlazar con S3") **diagnostica mal este caso**.

Severidad **CRÍTICO** para la ejecutabilidad de §3.

---

#### A-11 · La cifra central del expediente — **CONFIRMADA, reproduce exacta**

`potencia_fase_b.py` reejecutado en una copia aislada (para no sobrescribir
`fix-fase2/results/`):

```
$ python3 src/potencia_fase_b.py
N=  1: SR0=0.00000 (diario)  Sharpe min para DSR>=0.95: 0.472 (anual)
N=  5: SR0=0.03160 (diario)  Sharpe min para DSR>=0.95: 1.073 (anual)
N= 12: SR0=0.04412 (diario)  Sharpe min para DSR>=0.95: 1.312 (anual)
N= 50: SR0=0.06032 (diario)  Sharpe min para DSR>=0.95: 1.622 (anual)
N=100: SR0=0.06706 (diario)  Sharpe min para DSR>=0.95: 1.751 (anual)

Sharpe min para t>3: 0.870 (anual) [t = SR*sqrt(T_eff), T_eff=4336]
Sharpe observado Fase B: 1.008 | brecha vs umbral N=12: +0.304
```

Las cinco filas coinciden con la tabla publicada. **1.312 / 1.008 / +0.304
confirmados.** Matiz importante: es un cálculo analítico sobre constantes
cableadas (`T_EFF = 4336`, `SKEW = 1.037`, `KURT = 31.999`,
`V_TRIALS = 0.0007021947704551833`, `potencia_fase_b.py:25-28`). Confirma la
aritmética, no la procedencia de esas cuatro constantes.

---

#### A-12 · Walk-forward de tres tramos — **CONFIRMADO en el documento**

`fase_b_reevaluacion_resultado.md`, Paquete 1:

```
| T1 2015-2018 | +81.7% | 0.186 | 1.33 | 2.34 | 0.824 | [+0.57, +38.51] | 1.47 |
| T2 2019-2022 | +82.4% | 0.141 | 1.22 | 2.49 | 0.772 | [+1.13, +30.71] | 1.29 |
| T3 2023-fin  | +26.0% | 0.184 | 0.57 | 1.10 | 0.301 | [-5.86, +20.30] | 0.80 |
```

Sharpe 1.33 / 1.22 / 0.57 y el IC del tercer tramo cruzando cero: coinciden.
Los números de los otros dos dictámenes también:

```
$ grep -n "0.660\|1.52" fix-fase2/docs/rigor_estadistico_resultado.md
60:| sma_timing_50 | **1.12** | **0.660** | 1.52 | [-0.47, +4.87] | [8, 33] | no |
107:DSR (corrección por selección, mejor 0.66), ni por bootstrap (todos los IC
108:del retorno cruzan cero), ni por t>3 (máximo 1.52), ni contra el benchmark de

$ grep -n "0.4925" fix-fase2/docs/timesfm_fase2_resultado.md
67:| **AGREGADO** | **0.4925** | **-1.13** | **2.75** | 1118 ventanas |

$ python3 -c "import json; print(json.load(open('fix-fase2/results/portfolio_runner.json'))['metricas'])"
{'retorno_pct': 317.52, 'sharpe': 1.008, 'max_dd_pct': -26.9, 'calmar': 11.804,
 'bench_retorno_pct': 132831.04, 'bench_sharpe': 1.164, ...}
```

---

#### A-13 · La fórmula del DSR está validada contra el paper — **CONFIRMADO**

`verificar_rigor_sintetico.py` (PASS, 26 s) incluye la validación cruzada
contra el ejemplo impreso de Bailey & López de Prado 2014:

```
  1. ejemplo paper: SR0=0.113172 (esperado 0.1132) DSR=0.900397 (esperado 0.9004) -> OK
  2. ruido puro (N=100, 200 corpus): DSR rechazo al mejor en 199/200 (100%) -> OK
  3. edge inyectado (SR diario 0.15, T=1250): PSR(0)=1.0000 DSR(N=1)=1.0000 -> OK
  4. block bootstrap: ruido puro x100: IC sin cruzar 0 en 3 (3%, esperado ~5%) -> OK;
     edge IC95 [+0.0410,+0.1535] punto +0.0961 no cruza -> OK
```

El núcleo (PSR con corrección de Mertens + `E[max]` de N normales) reproduce
el ejemplo del paper a cuatro decimales. El primer guion de §3.5 ya está
sustancialmente satisfecho por un test que ya existe y pasa.

Dos desviaciones respecto al paper, **declaradas en el código**, que §3.5
encontrará y conviene anotar ya:

- El DSR se evalúa con `T` **efectivo AR(1)** (`n_obs_eff`, vía
  `ar1_effective_n`, `rigor_estadistico.py:110-120`), no con `T` bruto
  (`rigor_estadistico.py:179` lo comenta: *"DSR con T efectivo (AR1) —
  documentado"*). Reduce `T`, luego reduce el DSR: la desviación es
  **conservadora**.
- `V` es la varianza across-trial de los Sharpes **observados**
  (`rigor_estadistico.py:219-220`), estimada de los mismos trials que define
  `N`. Coherente con el paper, pero ver A-14 y B-08.

Semillas: `SEED = 42` fija, `np.random.default_rng(seed)`,
`block_bootstrap_ci` recibe `SEED + i` por variante
(`rigor_estadistico.py:48, 132, 236, 243`). El bootstrap es determinista.

---

#### A-14 · `N` y `V` — **N es consistente; V es una constante mágica copiada**

```
$ grep -rn "N_TRIALS\s*=\|V_TRIALS\s*=\|VAR_TRIALS\s*=" fix-fase2/src/*.py
fix-fase2/src/portfolio_bateria.py:35:N_TRIALS = 12
fix-fase2/src/portfolio_supervivencia.py:43:N_TRIALS = 12
fix-fase2/src/portfolio_supervivencia.py:44:VAR_TRIALS = 0.0007021947704551833
fix-fase2/src/portfolio_walkforward_temporal.py:37:N_TRIALS = 12
fix-fase2/src/portfolio_walkforward_temporal.py:38:VAR_TRIALS = 0.0007021947704551833  # misma V de la bateria Fase B (comparabilidad)
fix-fase2/src/potencia_fase_b.py:28:V_TRIALS = 0.0007021947704551833
fix-fase2/src/rigor_estadistico.py:45:N_TRIALS = len(VARIANTES)
```

Sobre `N`: **consistente**. Fase A usa `len(VARIANTES)` = 11; los cuatro
módulos de Fase B cablean 12. `portfolio_bateria.py:3` lo justifica: *"DSR con
N=12 (registro explícito: las 11 variantes de Fase A + esta regla)"*. No hay
ningún cálculo con un `N` distinto en silencio. El guion de §3.5 sobre
consistencia de `N` queda respondido: sí lo es. (Pero ver B-02: consistente no
es lo mismo que correcto.)

Sobre `V`: **solo se calcula en un sitio** (`portfolio_bateria.py:69`,
`np.var(sharpes, ddof=1)`). Los otros tres módulos la llevan cableada como
literal. En particular `portfolio_walkforward_temporal.py` aplica **la misma
`V` congelada a los tres tramos**, pese a que cada tramo tiene su propia
distribución de Sharpes across-trial. §3.5 no menciona `V` en ningún guion.
Ver B-08.

---

#### A-15 · Costes: **existen y están cifrados.** La premisa de §3.2 es incorrecta

§3.2 dice: *"El expediente dice 'costes del backtester' sin cifra visible en
los documentos leídos"*. Las cifras están, en código y en documento:

```
$ grep -n "commission\|slippage" fix-fase2/src/backtester.py | head -4
31:                 commission: float = 0.001, slippage: float = 0.0005,
33:    """Backtest event-driven, 1 posicion, costes (comision + slippage por lado).
71:            fill = open_[i] * (1 + slippage) if side == "long" else open_[i] * (1 - slippage)
120:                exit_price *= (1 - slippage) if position.side == "long" else (1 + slippage)

$ sed -n '39,40p' fix-fase2/src/portfolio_runner.py
COMMISSION = 0.001
SLIPPAGE = 0.0005
```

`fix-fase2/docs/AUDIT_BRIEF.md` §6 ya las publica: *"Costes: 0.1% comisión +
0.05% slippage por lado"*. Y `results/portfolio_runner.json` las deja
grabadas: `"costes": {"commission": 0.001, "slippage": 0.0005}`.

Ambos lados: `backtester.py:71` aplica slippage al fill de entrada, `:120` y
`:149` al de salida, y `:126`/`:153` cobran comisión sobre
`(entry_price + exit_price) * size`, que es nominal de entrada + nominal de
salida. Dimensionalmente es comisión por lado sobre el nominal, no sobre el
capital total.

**El coste de rebalanceo sí se cobra**, sobre turnover:

```
$ sed -n '241,243p' fix-fase2/src/portfolio_runner.py
        turnover = float(np.nansum(np.abs(w_prev - w_target)))
        coste = turnover * (COMMISSION + SLIPPAGE)
        equity *= (1 + r_p - coste)
```

Es decir, el miedo central de §3.2 ("un portfolio que rebalancea 10 activos a
diario durante 4404 días y no paga esos ajustes tiene un Sharpe fantasma") no
se cumple: se paga `|Δw| * 0.0015` cada día. Lo que **no** está registrado es
el agregado: `portfolio_runner.json` guarda las métricas pero **no** el coste
acumulado ni el número de rebalanceos (`claves: activos, lookback, lambda,
sigma_target, w_max, gross_max, vol_tope_mult, costes, metricas,
n_vetos_wmax, n_vetos_vol, vetos_wmax_muestra, vetos_vol_muestra,
exposicion_media`). Cuantificarlo exige reejecutar, y eso está bloqueado por
A-10.

Dato de contexto verificado: `wc -l fix-fase2/results/portfolio_equity.csv` →
`4405`, es decir 4404 días + cabecera. El "4404 días" del brief es correcto.

---

#### A-16 · `risk_veto.py` **no está en la ruta del backtest** — la premisa de §3.1 falla ahí

```
$ grep -rln "risk_veto" fix-fase2/src/ fix-fase2/*.py
fix-fase2/src/paper_runner.py
fix-fase2/src/deliberation.py
fix-fase2/verificar_veto_riesgo.py
$ grep -n "risk_veto\|evaluar_veto" fix-fase2/src/backtester.py fix-fase2/src/portfolio_runner.py fix-fase2/src/portfolio_bateria.py
(salida vacía)
```

`risk_veto.py` lo importan únicamente `paper_runner.py`, `deliberation.py` y
su propio verificador. **No contribuyó a ninguno de los cuatro dictámenes.**
§3.1 pide probar look-ahead en "los vetos de riesgo (`risk_veto.py`)": esa
parte del alcance no puede invalidar ningún dictamen. Ver B-07.

---

#### A-17 · Causalidad estructural del harness — leída, **pendiente de prueba física**

Lectura, no prueba (la prueba es §3 y no se ha ejecutado). Lo que la lectura
dice, para que §3 lo confirme o lo tumbe:

`backtester.py:42-46`, docstring, y `:68-71` / `:132-137`: la señal de la vela
`i` crea un `pending` que se rellena en `open[i+1]`. **No** rellena al cierre
de la vela de la señal. Esto es la sospecha S1 del `AUDIT_BRIEF.md` previo, y
en el código **está corregida**.

`portfolio_runner.py:207-229`: todo lo que decide el día `t` usa índices
`t-1`: `s2_path[t-1, i]` para la volatilidad del sizing Carver,
`cov_path[t-1]` para la covarianza del veto de vol, `closes.iloc[t-1]` y
`closes.iloc[t-1-LOOKBACK]` para el momentum, `rets[tk].iloc[:t]` para la
elegibilidad. El "caso más propenso" que señala §3.1 (una EWMA que incluye la
barra actual al dimensionar esa barra) **no se da**: `cov_path[t]` sí incluye
`R[t]`, pero el bucle consume `cov_path[t-1]`.

`strategies.py:167-182`: la detección de swings usa
`rolling(2*order+1, center=True)` — ventana **centrada**, por tanto no causal
en el punto del extremo — pero emite la señal con retraso en
`conf2 = p + order`, el momento en que el swing ya es conocible, y filtra los
que caen fuera de la serie (`if p + order < n`). El patrón de mitigación es el
correcto. Esto corresponde al commit `5b2851c` ("look-ahead corregido").

Una asimetría real que la lectura sí detecta, y que §3 no busca:

```
$ sed -n '246p' fix-fase2/src/portfolio_runner.py
        elig = [i for i in range(n) if rets.iloc[:t + 1].iloc[:, i].notna().sum() >= LOOKBACK + 1]
```

El conjunto elegible del **benchmark** se calcula con `rets.iloc[:t + 1]`
(incluye la barra `t`), mientras el de la **estrategia** usa `rets[tk].iloc[:t]`
(`:229`). El benchmark dispone de una barra más de información que la
estrategia. La dirección es **conservadora** (infla al benchmark, que ya gana
en Sharpe: 1.164 vs 1.008), pero es una inconsistencia y no está en la lista
de §3. Severidad **MEDIO**. Ver B-09.

---

#### A-18 · Existe ya un AUDIT_BRIEF previo, con tres criterios bloqueantes **sin verificador** — **HALLAZGO NUEVO, CRÍTICO**

`fix-fase2/docs/AUDIT_BRIEF.md` (2026-10-05) es una auditoría del mismo harness
que el brief S1 no menciona en ningún punto. Sus sospechas: **S1** look-ahead
en fills, **S2** drawdown idéntico train/test, **S3** comisión mal aplicada,
**S4** salidas intravela, **S5** walk-forward sin optimización, **S6** datos
yfinance y reproducibilidad. Sus criterios de aprobación A1-A8, con la columna
"Bloquea": A1, A2, A3 bloquean.

Su propio texto: *"**Estos números NO son confiables hasta que A1-A3 estén
resueltos.**"* Y `brain.py:75-78` lo tiene grabado en el segundo cerebro:

```
$ sed -n '75,78p' fix-fase2/src/brain.py
        self.add("backtest_result",
                 "Línea base pre-auditoría BTC-USD daily: ma_cross OOS +24.4% Sharpe 1.63 (12/16 WF folds); "
                 "mean_reversion y breakout pierden; trend_following colapsa en OOS (+61% IS → -20% OOS, caso de overfitting). "
                 "NO FIABLE hasta resolver S1 (look-ahead) y S3 (comisión).",
```

Qué verificadores existen por criterio:

```
$ ls fix-fase2/verificar_a*.py
fix-fase2/verificar_a4_a7_cierre.py
fix-fase2/verificar_a5_indicadores.py
fix-fase2/verificar_a6_metricas.py
fix-fase2/verificar_a8_adversarial.py
$ ls fix-fase2/verificar_a1*.py fix-fase2/verificar_a2*.py fix-fase2/verificar_a3*.py
ls: cannot access 'fix-fase2/verificar_a1*.py': No such file or directory
ls: cannot access 'fix-fase2/verificar_a2*.py': No such file or directory
ls: cannot access 'fix-fase2/verificar_a3*.py': No such file or directory
```

**A4, A5, A6, A7 y A8 tienen verificador. A1, A2 y A3 — los tres únicos que
bloquean — no tienen ninguno.** El código parece haber arreglado A1 y A3
(A-17, A-15), pero no hay ni un script que lo demuestre, y A2 (el drawdown
−2.18% idéntico en dos periodos disjuntos) no tiene ni arreglo ni prueba ni
explicación localizable.

Ese es el agujero real del expediente: los cuatro dictámenes se apoyan en un
harness cuyos tres criterios bloqueantes de aceptación nunca se cerraron con
evidencia. Severidad **CRÍTICO**. Ver B-03 y B-04.

---

#### A-19 · Entorno declarado vs entorno real — **NO CUADRA (menor)**

`AUDIT_BRIEF.md` §2 declara: *"Python 3.12 venv en `/opt/trading-bot/venv/`
(pandas 3.0.6, numpy 2.5.3, yfinance)"*. Aquí:

```
$ python3 --version
Python 3.13.18
$ python3 -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
2.5.3 3.0.5
```

Python 3.13.18 vs 3.12; pandas 3.0.5 vs 3.0.6. §3.4 exige comparación "cifra a
cifra" y declarar hallazgo cualquier discrepancia "por pequeña que sea". Con
deriva de versiones, una diferencia en decimales bajos puede no venir del
harness. Ver B-13.

---

#### Resumen del Paso A

| # | Afirmación del brief | Resultado |
|---|---|---|
| A-01 | base `d34b147` | NO CUADRA (HEAD es `adad9e7`), benigno |
| A-02 | `shared/trading-bot-fase1/*`, README del snapshot | **NO EXISTE** → 2 puntos de §2 sin verificar, y §9 sin ancla |
| A-03 | los 4 módulos de `src/` | CONFIRMADO, sha256 anotados, idénticos a `fix-fase2/src/` |
| A-04 | "los 14 módulos" de `fix-fase2/src/` | NO CUADRA: son **19**, sha256 anotados |
| A-05 | 15 `verificar_*.py` que se ejecutan hoy | NO CUADRA: son **23**, hoy **16 PASS / 7 FAIL**, los 7 por entorno |
| A-06 | "suite 15/15 PASS" | **NO LO SÉ** — `REGISTRO_F.md` y commit `9249cf4` no existen |
| A-07 | `btc_usd_5y_1d.csv` = `.sha256` = `.meta.json` | NO CUADRA: **no hay `.sha256` ni `.meta.json`** |
| A-08 | `multi/` y `multi_muertos/` sin ningún `.csv` | **FALSO**: 35 CSV, **35/35 OK** contra su hash |
| A-09 | `portfolio_resultado.md` (dictamen Fase B) | **NO EXISTE** ni existió |
| A-10 | — | **NUEVO/CRÍTICO**: el loader no alcanza los CSV congelados |
| A-11 | 1.312 / 1.008 / +0.304 | CONFIRMADO, reproduce exacto |
| A-12 | 1.33 / 1.22 / 0.57, IC de T3 cruza cero; 0.66, 1.52, 0.4925 | CONFIRMADO |
| A-13 | DSR = Bailey & LdP 2014 | CONFIRMADO contra el ejemplo del paper (0.9004); 2 desviaciones declaradas |
| A-14 | `N=12` consistente | CONFIRMADO para `N`; **`V` es constante mágica** en 3 módulos |
| A-15 | costes "sin cifra visible" | **PREMISA INCORRECTA**: 0.001/0.0005, por lado, y el rebalanceo se cobra |
| A-16 | vetos de riesgo en el harness | **FALSO**: `risk_veto.py` no está en la ruta del backtest |
| A-17 | causalidad | leída y coherente; **sin prueba física** (es §3) |
| A-18 | — | **NUEVO/CRÍTICO**: A1/A2/A3 bloqueantes del AUDIT_BRIEF previo, **sin verificador** |
| A-19 | entorno | NO CUADRA (menor): py3.13.18/pandas 3.0.5 vs py3.12/3.0.6 |

---

### Paso B — Ataque adversarial al planteamiento de esta tarea

Objeciones al documento, no a la estrategia. Numeradas, con gravedad y
propuesta. No hay ninguna "parece correcto".

---

**B-01 · CRÍTICO — Tres de los cinco subapartados de §3 no son ejecutables hoy, y el brief no lo prevé**

§3.2, §3.3 y §3.4 exigen reejecutar el portfolio de Fase B. `load_or_download()`
no alcanza los CSV congelados en ninguna fecha que no sea el 2026-10-07 o el
2026-10-09 (A-10, con prueba empírica). El brief prevé el caso "faltan datos"
(§7) pero no el caso "los datos están, verificados, y el código no los lee".
Peor: si esta sesión tuviera red, la reejecución habría descargado datos de
hoy y producido cifras que parecerían comparables con las publicadas sin serlo
— exactamente el modo de fallo silencioso que la tarea busca.

*Propuesta:* antes de §3, añadir un §3.0 obligatorio: parchear
`load_or_download()` para aceptar un `stamp`/ruta explícita y **fallar en duro**
si el fichero pedido no existe, en vez de descargar. Prohibir la descarga
durante la auditoría. Sin eso, §3.2/§3.3/§3.4 no arrancan.

---

**B-02 · CRÍTICO — `N=12` es incomprobable desde el repo, y §3.5 hace la pregunta equivocada**

§3.5 pide verificar que el 12 "está contado de forma consistente". Lo está
(A-14). Pero la consistencia no es el riesgo: el riesgo es que 12 sea
**falso**. `N` en Bailey-LdP es el número de configuraciones **probadas**, no
el de configuraciones **publicadas**. El repo solo puede corroborar las
publicadas. Cualquier variante probada y descartada antes de entrar en
`VARIANTES` —cualquier parámetro tanteado, cualquier `LOOKBACK`, `LAMBDA`
(0.94), `SIGMA_TARGET` (0.10), `W_MAX` (0.2), `VOL_TOPE_MULT` (1.25) elegido
mirando un resultado— sube `N` y sube el umbral. Y el umbral es sensible: la
propia tabla de A-11 va de 1.312 (N=12) a 1.622 (N=50).

El expediente entero cuelga de la brecha +0.304, que es una función de un
número que ninguna evidencia del repo puede respaldar. Verificar que está
cableado igual en cuatro ficheros no lo hace más verdadero.

*Propuesta:* reescribir §3.5 para (a) declarar `N=12` como **asunción no
verificable**, con esa etiqueta, en el informe y en el ancla; (b) entregar el
DSR como **función de N** (tabla N = 12, 20, 30, 50) en vez de un escalar, y
decir a partir de qué `N` el dictamen "SEÑAL DÉBIL" pasaría a "MUERTA"; (c)
contar los parámetros libres del portfolio como trials candidatos y dar un
`N` mínimo defendible por ese recuento. Esto no cambia ninguna métrica ni
umbral (§3.6 lo prohíbe): añade el eje de sensibilidad que falta.

---

**B-03 · ALTO — El brief ignora que ya existe una auditoría de este mismo harness, y colisiona con su numeración**

`fix-fase2/docs/AUDIT_BRIEF.md` cubre ya look-ahead en fills, dimensionalidad
de la comisión, orden intravela, determinismo y datos de yfinance (A-18). El
brief S1 no lo cita ni una vez. Dos consecuencias:

1. §3 se solapa con trabajo ya hecho (`verificar_a4_a7_cierre.py`,
   `_a5_`, `_a6_`, `_a8_` **son** los criterios A4-A8 de ese brief) y se arriesga
   a repetirlo sin saberlo.
2. **Colisión de nombres grave.** En `AUDIT_BRIEF.md`, "S1" es *look-ahead en
   fills* y "S3" es *comisión*. En los briefs nuevos, "S1" es *auditoría del
   harness* y "S3" es *ampliación de T*. Y `brain.py:78` —el segundo cerebro
   que lee cualquier agente que se incorpore— tiene grabado *"NO FIABLE hasta
   resolver S1 (look-ahead) y S3 (comisión)"* con el significado **viejo**. El
   próximo agente que lea "S1 resuelto" no sabrá cuál de los dos.

*Propuesta:* añadir al brief una tabla de correspondencia explícita entre
S1-S6/A1-A8 del `AUDIT_BRIEF.md` y los subapartados de §3, y renombrar los
briefs nuevos (p. ej. `N1`/`N2`/`N3` de "nube") para romper la colisión. Antes
de §3, no después.

---

**B-04 · ALTO — §3 apunta al sitio equivocado: el agujero es A1/A2/A3, no una auditoría nueva desde cero**

El dato de A-18: los cinco criterios no bloqueantes del audit previo tienen
verificador; los tres bloqueantes no tienen ninguno. El código **parece** haber
arreglado A1 (fill en `open[i+1]`) y A3 (comisión por lado sobre nominal), pero
"parece" es exactamente lo que esta tarea existe para no aceptar. Y **A2 —el
drawdown −2.18% idéntico en dos periodos disjuntos— no tiene arreglo, ni
prueba, ni explicación localizable en el repo.** Es una coincidencia numérica
que el propio builder calificó de estadísticamente rara y que sigue abierta.

§3 está escrito como una auditoría genérica de clases de defecto. Eso es más
difuso y más caro que cerrar tres criterios ya identificados, nominados y
declarados bloqueantes por escrito.

*Propuesta:* reordenar §3 para que sus tres primeros entregables sean
`fix-fase2/auditoria_s1/verificar_a1_lookahead.py`,
`verificar_a2_drawdown.py` y `verificar_a3_comision.py`, cerrando A1/A2/A3 con
evidencia. A2 es el más informativo de los tres: si es un bug de
`compute_metrics`, afecta a todas las métricas de drawdown de los cuatro
dictámenes. §3.1 y §3.2 quedan como la generalización de A1 y A3, no como
trabajo paralelo.

---

**B-05 · ALTO — La prueba que §3.1 prescribe es defectuosa y puede dar falso positivo y falso negativo**

§3.1 manda: *"inyectar un shock artificial conocido en la barra `t+1` (p. ej.
multiplicar el cierre por 3) y comprobar que la posición en `t` no cambia"*.
Tres defectos:

1. **Rompe la coherencia OHLC.** `close[t+1] * 3` deja `close > high`. El
    backtester tiene ramas de gap que comparan `open`, `low` y `high` contra
    `stop`/`target` (`backtester.py:71-120`). Una barra incoherente puede
    disparar esas ramas y producir una diferencia que se leería como
    look-ahead sin serlo: **falso positivo**.
2. **Un solo punto no prueba nada.** Perturbar una única barra `t+1` comprueba
    la causalidad en ese `t` concreto. Un look-ahead con retraso de dos barras,
    o que solo actúa cuando hay posición abierta, o en el warm-up de un
    indicador, pasa la prueba: **falso negativo**.
3. **El criterio de comparación está mal planteado.** Perturbar `close[t+1]`
    cambia legítimamente todo lo posterior a `t+1`. Comparar curvas de equity
    completas dará siempre diferencia; la prueba no dice que hay que comparar
    solo el prefijo `[0..t]`.

*Propuesta:* sustituirla por una prueba de **invariancia de prefijo**: para
cada `t` de una rejilla (p. ej. 200 valores repartidos por la serie), perturbar
**todas** las barras `> t` a la vez —manteniendo coherencia OHLC, p. ej.
escalando `open/high/low/close` de cada barra por el mismo factor— y exigir que
el vector de decisiones y la equity en `[0..t]` sean **bit-idénticos**. Una
sola `t` con diferencia localiza el look-ahead y da la barra exacta. Es más
barata que 200 ejecuciones completas si se corta la serie en `t`.

---

**B-06 · ALTO — §3.1 omite el constructo menos causal del código**

La lista de §3.1 es: entrada, salida, indicadores, sizing EWMA, vetos de
riesgo, covarianza del portfolio. Falta la **detección de extremos con ventana
centrada** de `strategies.py:167-182`
(`rolling(2*order+1, center=True)` en `_swings_confirmados`). Es el único sitio
del código que es no causal **por construcción**; depende de un retraso manual
(`conf2 = p + order`) para ser legítimo; y es el único que ya necesitó un
arreglo documentado por look-ahead (commit `5b2851c`, *"look-ahead
corregido"*). Afecta a `rsi_hidden_divergence`, una de las 11 variantes de
Fase A.

Al mismo tiempo, §3.1 gasta un guion entero en el "caso más propenso" (la EWMA
de volatilidad) que ya consume `s2_path[t-1]` (A-17): ahí no hay nada.

*Propuesta:* añadir `_swings_confirmados` / `rsi_hidden_divergence` como punto
explícito de §3.1, y degradar la EWMA a confirmación por la prueba general de
B-05.

---

**B-07 · MEDIO — Una parte de §3.1 es inútil tal como está escrita, y además se contradice con §3.6**

§3.1 exige probar look-ahead en "los vetos de riesgo (`risk_veto.py`)".
`risk_veto.py` lo importan solo `paper_runner.py`, `deliberation.py` y su
verificador; **no está en la ruta del backtest** (A-16). No produjo ninguna de
las cifras de los cuatro dictámenes, luego ningún hallazgo ahí puede invalidar
ninguno. Es trabajo que no puede cambiar la conclusión.

Y es incoherente con §3.6, que prohíbe tocar `risk_veto.py` "salvo para
leerlos": una prueba de inyección sobre sus vetos es, como mínimo, ejercitarlo
en un arnés nuevo.

*Propuesta:* quitar `risk_veto.py` de §3.1 y dejarlo como lectura declarada
fuera de alcance, con la razón escrita (no participa del harness de backtest).
Si se quiere auditar el camino de paper trading, es otra tarea.

---

**B-08 · MEDIO — §3.5 audita `N` y la fórmula, pero no `V`, que es la otra mitad de `SR0`**

`SR0 = sqrt(V) * E[max_N]`. §3.5 dedica guiones a la fórmula y a `N`, y ninguno
a `V`. Y `V` es lo más frágil de los dos (A-14): se calcula en un solo sitio y
viaja cableada como literal `0.0007021947704551833` a tres módulos. En
particular, `portfolio_walkforward_temporal.py` aplica **la misma `V`
congelada** a los tres tramos, cuando la varianza across-trial de los Sharpes
dentro de un tramo de 3-4 años no tiene por qué ser la del periodo completo.
Los DSR por tramo publicados (0.824 / 0.772 / 0.301) dependen de esa elección.

Añadido: `potencia_fase_b.py` se presenta como potencia **a priori** y cablea
`T_EFF`, `SKEW`, `KURT` y `V_TRIALS` tomados del run **ya observado**
(`:25-28`). Es un cálculo a posteriori con etiqueta de a priori. No invalida la
aritmética (A-11), pero sí la etiqueta.

*Propuesta:* añadir a §3.5 un guion para `V`: de dónde sale, si procede del
mismo conjunto de trials que define `N`, y qué pasa con los DSR por tramo si
`V` se recalcula dentro de cada tramo. Y corregir la descripción de
`potencia_fase_b.py` de "a priori" a "a posteriori con parámetros observados".

---

**B-09 · MEDIO — Falta una clase de defecto en §3: asimetría de información entre estrategia y benchmark**

§3 busca look-ahead, costes, supervivencia, reproducibilidad y DSR. No busca
**que la estrategia y su benchmark no se midan con la misma información**. Ya
hay un caso concreto (A-17): el conjunto elegible del benchmark usa
`rets.iloc[:t + 1]`, el de la estrategia `rets.iloc[:t]`. Una barra de
diferencia. Aquí la dirección es conservadora —infla al benchmark, que ya gana
(1.164 vs 1.008)— pero el dictamen de Fase B es literalmente "pierde vs B&H",
así que un sesgo en el benchmark es parte del dictamen, no un detalle.

La misma clase cubre el "benchmark de exposición igualada" de Fase A
(`rigor_estadistico.py:185-209`), que selecciona los días de B&H con la máscara
de posición **de la estrategia**: es una selección de días condicionada al
comportamiento de la estrategia, y merece una prueba propia.

*Propuesta:* añadir §3.7 "simetría estrategia-benchmark": misma ventana de
información, misma regla de elegibilidad, y prueba de que la máscara de
exposición no introduce selección. Cuesta poco y toca directamente la
comparación que decide el dictamen.

---

**B-10 · ALTO — La asunción más débil del brief no es la que el brief propone**

El brief se autodiagnostica: *"candidata honesta: que un snapshot con
comentarios recortados por un hook de estilo es equivalente al código vivo"*.
**Esa candidata es falsa en este repo**: no hay snapshot. `shared/` no existe
(A-02) y los dos árboles `src/` que sí existen son byte-idénticos en sus 11
ficheros comunes (A-03). No hay nada que contrastar y la objeción se disuelve.

La asunción realmente débil es otra, y es más grave: **que el código de este
repo es el código que produjo los cuatro dictámenes.** Por la propia cabecera
del brief, `fix-fase2/` se recuperó de `/root/trading-bot-fix-fase2` en el VPS,
*"que no estaba bajo git"*. De ahí se sigue que:

- Los 35 CSV tienen procedencia verificable: hash + meta, 35/35 OK (A-08).
- Los `.py` **no tienen ninguna**: ni historia, ni manifiesto de hashes, ni
  firma. Llegaron en un solo commit (`d34b147`) desde un directorio sin git.
- Los `results/*.json` tampoco: no registran versión de código, ni hash del
  código, ni fecha de ejecución.

Es decir: la auditoría puede probar que **este** harness tiene o no un defecto,
pero no puede probar que este harness sea el que generó `portfolio_runner.json`
ni `rigor_estadistico.json`. Si no lo es, un veredicto "se sostiene" no
sostiene nada. Y el precedente del proyecto (el bug PEFT in-place, encontrado
por prueba física y no por lectura) es justamente de esta familia: código que
no hacía lo que su registro decía.

*Propuesta:* convertir esto en la **primera** prueba de §3, antes que
cualquier otra: reejecutar lo que es reejecutable hoy sin red
(`rigor_estadistico.py` lee `data/btc_usd_5y_1d.csv` directamente, sin
yfinance) y comparar cifra a cifra contra `fix-fase2/results/rigor_estadistico.json`.
Si coincide, el vínculo código↔resultados queda establecido para Fase A y el
resto de la auditoría tiene sentido. Si no coincide, **ese es el hallazgo** y
hace falta parar otra vez, porque entonces ni el código ni los resultados son
lo que el expediente dice. Es §3.4 en el brief, al final; debe ser la primera
prueba, porque condiciona el valor de todas las demás.

---

**B-11 · MEDIO — La alternativa descartada (SSH al VPS) no invalida la tarea, pero el brief la descarta por la razón equivocada**

El brief pregunta si la falta de SSH invalida la tarea entera o solo una parte.
Respuesta con lo verificado: **solo una parte, y no la que el brief supone.**

- Lo que no se pierde: los datos. Los 35 CSV están en git y verifican 35/35
  contra sus hashes (A-08). No hace falta el VPS para tener datos de confianza.
- Lo que sí se pierde: la posibilidad de comprobar que el código del VPS y el
  de este repo coinciden — es decir, exactamente B-10. Y eso **no se arregla
  con SSH tampoco**, porque el directorio del VPS no estaba bajo git: comparar
  contra él solo diría que dos copias sin procedencia coinciden entre sí.

*Propuesta:* dejar escrito en §2 que el acceso al VPS no es la vía para cerrar
la procedencia del código, y que la única vía disponible es la reejecución
determinista de B-10. Y, como acción separada de esta tarea, poner
`/root/trading-bot-fix-fase2` bajo git en el VPS y grabar en cada
`results/*.json` el commit y el hash del código que lo generó. Sin eso, la
próxima auditoría tendrá el mismo problema.

---

**B-12 · MEDIO — Los verificadores que descargan datos en vivo hacen que la premisa de §1 no sea estable**

§1 se apoya en que el harness está cubierto por una suite. Cuatro de los 23
verificadores descargan de yfinance en tiempo de ejecución (A-05), entre ellos
`verificar_a8_adversarial.py` — precisamente el test adversarial (estrategia
coin-flip ≈ 0 menos costes), que es el más cercano en espíritu a lo que §3
quiere hacer. Un verificador cuyo insumo cambia cada día no congela nada: puede
pasar hoy y fallar mañana sin que el código cambie. Y ninguno de los cuatro
comprueba que la descarga trajo filas: fallan con `IndexError` sobre un
DataFrame vacío.

*Propuesta:* dentro del alcance físico de `fix-fase2/`, añadir a §3 un
entregable que repunte esos cuatro verificadores a `data/multi/*_20261009.csv`
y `data/btc_usd_5y_1d.csv`, con aserción explícita de "datos cargados, N filas
> 0". Deja la suite ejecutable sin red y hace que "15/15" o "23/23" signifique
algo reproducible.

---

**B-13 · BAJO — §3.4 exige comparación exacta en un entorno que ha derivado**

§3.4: *"cualquier discrepancia, por pequeña que sea, se documenta. Una
diferencia en el cuarto decimal puede ser un generador aleatorio sin semilla
fija"*. Correcto como principio, pero aquí hay deriva de versiones
documentada (A-19: py3.13.18/pandas 3.0.5 frente a py3.12/pandas 3.0.6
declarados). Y el bootstrap **sí** tiene semilla fija y determinista
(`SEED = 42`, `default_rng`, A-13). Luego una diferencia en decimales bajos
apuntará antes a `numpy`/`pandas` que al harness, y el brief no deja sitio para
esa hipótesis.

*Propuesta:* añadir a §3.4 un primer paso de control: dos ejecuciones
consecutivas en **este** entorno deben dar bit-identidad (eso aísla el
no-determinismo propio); solo después comparar contra los JSON publicados, y
clasificar cualquier diferencia como "no determinismo" / "deriva de versiones"
/ "defecto del harness", con la versión de las librerías anotada en el informe.

---

**B-14 · BAJO — El brief se contradice sobre el destino del PR, y el ancla de §9 no existe**

§5 Definition of Done: *"PR abierto contra `main`"*. §4 NO-GO: *"No mergear a
`main`"*. La instrucción de esta sesión: PR contra `fase-b-recuperada`. Tres
destinos en tres sitios. He abierto el PR contra `fase-b-recuperada`, que es lo
que manda la instrucción y lo coherente con que `main` no tiene el trabajo.

Y §9 manda llevar cualquier hallazgo a `shared/estado-y-siguiente-paso.md`,
que no existe en este repo (A-02). Tal como está, §9 es inaplicable desde una
sesión en la nube: el hallazgo se quedaría solo en el informe, que es
exactamente lo que §9 quiere evitar.

*Propuesta:* corregir §5 a `fase-b-recuperada`, y decidir dónde vive el ancla.
Si `shared/` no va a estar en este repo, §9 debe nombrar un archivo que sí
exista aquí (p. ej. `REGISTRO_D.md` o un `fix-fase2/docs/estado.md` nuevo) y
que alguien replique al bunker.

---

#### Por qué no hay ningún "parece correcto"

Las objeciones salen de tres sitios distintos y ninguna es una lectura de
estilo: (1) ejecutar la suite completa, que reveló 23 scripts donde el brief
dice 15 y 4 verificadores que dependen de la red; (2) llamar de verdad a
`load_or_download()` con los datos congelados delante, que es como apareció
B-01 —leyendo el código habría pasado por una caché normal—; (3) leer un
documento que el brief no cita, `AUDIT_BRIEF.md`, que es de donde salen B-03 y
B-04, las dos objeciones más caras.

La candidata que el propio brief proponía (snapshot con comentarios recortados)
resultó **falsa** aquí, y comprobarlo es lo que llevó a la asunción débil de
verdad (B-10): no hay procedencia para los `.py`, solo para los `.csv`.

---

### Estado y plan de §3 corregido

**§3 NO se ha ejecutado.** No se ha creado `fix-fase2/auditoria_s1/`, ni
`fix-fase2/docs/auditoria_harness_s1.md`, ni se ha analizado ningún dictamen.
Ningún `.csv`, `.sha256` ni `.meta.json` se ha modificado; `potencia_fase_b.py`
se reejecutó en una copia fuera del repo para no tocar `fix-fase2/results/`.

Orden propuesto para §3, si Pablo da el OK, reordenado por lo que condiciona a
lo demás:

| Paso | Qué | Por qué va aquí | Objeción |
|---|---|---|---|
| **3.0** | Parchear `load_or_download()` con ruta/stamp explícito y fallo en duro sin descarga | sin esto, 3 de 5 subapartados no arrancan | B-01 |
| **3.0b** | Reejecutar `rigor_estadistico.py` (corre sin red) y comparar contra `results/rigor_estadistico.json`; dos pasadas para bit-identidad | establece el vínculo código↔resultados; si falla, **parar otra vez** | B-10, B-13 |
| **3.1** | Cerrar A1/A2/A3 del `AUDIT_BRIEF.md` con tres scripts | es el agujero nominado y bloqueante | B-04, A-18 |
| **3.2** | Look-ahead por invariancia de prefijo, con rejilla de `t`, OHLC coherente, incluyendo `_swings_confirmados` | la prueba de §3.1 original da falsos positivos y negativos | B-05, B-06 |
| **3.3** | Costes: agregado de rebalanceos y coste acumulado + sensibilidad ×2/×5/×10 | las cifras ya están localizadas (A-15); lo que falta es el agregado | A-15 |
| **3.4** | DSR como función de `N`, y `V` recalculada por tramo | el escalar 0.72 esconde el eje que decide | B-02, B-08 |
| **3.5** | Simetría estrategia-benchmark (`:t` vs `:t+1`, máscara de exposición) | el dictamen es "pierde vs B&H": el benchmark es parte del dictamen | B-09 |
| **3.6** | Supervivencia (§3.3 original, sin cambios de fondo) | ejecutable una vez hecho 3.0 | — |
| **3.7** | Repuntar los 4 verificadores de red a los CSV congelados | hace la suite reproducible sin red | B-12 |

Fuera de §3 y previo a cualquier cosa, porque son de documentación y no de
análisis: la tabla de correspondencia S1-S6/A1-A8 y el renombrado de los briefs
nuevos (B-03), el destino del PR y el ancla de §9 (B-14), y qué se hace con
`portfolio_resultado.md`, que no existe (A-09).

**Parado aquí, según §2 y §4 NO-GO. La §3 no arranca sin el OK escrito de
Pablo en §8.**
