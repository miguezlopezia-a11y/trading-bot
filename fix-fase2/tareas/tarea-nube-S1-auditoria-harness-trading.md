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
