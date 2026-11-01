# Tarea N6 (nube) — Holdout, recuento de `N` y qué test debe decidir Fase B

**Creada:** 2026-11-01 por Claude Opus 5 (sesión de escritorio de Pablo).
**Repo:** `miguezlopezia-a11y/trading-bot`. **Base:** rama `fase-b-recuperada`.
**Rama de trabajo:** cortar `nube/n6-holdout-y-recuento` desde `fase-b-recuperada`.
**Estado:** PARADO en Fase 0. **No se ejecuta "Alcance" sin OK escrito de Pablo.**

**Sustituye a los Alcances de N4 y N5, que quedan cancelados.** Las dos Fase 0
llegaron más lejos que sus propios Alcances y los dejaron sin sentido:

- **N4** (rama `nube/n4-procedencia-v-t-n`): su §4 no sobrevive. 4.1 ya estaba
  hecho en la propia Fase 0; 4.3, 4.4 y 4.5 quedaron vaciados o imposibles;
  4.6 no se podía construir encima. Su registro lo dice literal: *"Si Pablo
  quiere que el Alcance se ejecute, no debería firmar el que está escrito."*
- **N5** (rama `nube/n5-reconocimiento-datos`): paró por NO-GO. **0 de 10
  fuentes de datos alcanzables** desde el contenedor (lista blanca del proxy).
  Su Alcance no es ejecutable en la nube, con OK o sin él.

**Lectura previa obligatoria, en este orden:**

1. El `## Registro de revisión némesis` de
   `fix-fase2/tareas/tarea-nube-N4-procedencia-de-V-T-y-N.md` en la rama
   `nube/n4-procedencia-v-t-n` — **entero**, incluida la crítica del segundo
   agente. Es el documento del que sale esta tarea.
2. El `## Registro de revisión némesis` de
   `fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md`
   en la rama `nube/n5-reconocimiento-datos`, secciones "NO-GO" y "Lo que esta
   Fase 0 deja decidido".
3. `fix-fase2/docs/fase_b_reevaluacion_resultado.md` — el dictamen en disputa.
4. `fix-fase2/docs/estado-auditoria-n1.md`.

---

## 1. La pregunta, reformulada

El expediente lleva un mes preguntando **qué `V` es la correcta**, porque de
eso depende si el listón del DSR es 1.312 o 0.823 y si el Sharpe observado de
1.008 lo pasa.

**N4 demostró que esa es la pregunta equivocada.** El listón es auditable, la
aritmética es correcta y no hay manipulación. Lo que hay es que **el test está
mal aplicado**, por tres razones que ningún valor de `V` arregla:

1. **El sujeto del test está dentro de su propia `V`**, y además duplicado: el
   trial nº12 es la misma regla que el nº9.
2. **No hay familia de intentos sobre el objeto evaluado.** El DSR corrige el
   sesgo de elegir el mejor de `N` intentos; aquí la `V` se mide sobre once
   reglas de un activo y se aplica a un portfolio multi-activo que no sale de
   esa familia.
3. **El número evaluado no tiene holdout y el listón sí.** El Sharpe 1.008 se
   midió sobre la historia entera; los once Sharpes que forman `V` son solo el
   40% OOS. **Esta es la única heterogeneidad con dirección conocida, y va en
   contra de Fase B.**

Y `N` está mal contado: hay al menos tres estrategias más con resultados
publicados que no entran en ningún recuento.

**Esta tarea hace tres cosas y ninguna más:** cerrar el recuento de `N`, medir
Fase B con el holdout que ya estaba pre-registrado, y enumerar qué tests
podrían decidir Fase B con su umbral. **No elige el test.** Esa decisión es de
Pablo y se toma con la tabla delante.

---

## 2. Hechos verificados desde el escritorio (reverificar, no creer)

### 2.1 El repo tiene DOS árboles de resultados, y uno no se ha auditado nunca

```
$ ls results/ | wc -l
15
$ ls fix-fase2/results/ | wc -l
12
$ comm -12 <(ls results/ | sort) <(ls fix-fase2/results/ | sort)
rigor_estadistico.json
walkforward_stability_rsi_hidden_divergence.json
```

**Solo dos ficheros en común.** N1, N4 y N5 trabajaron en `fix-fase2/`. El
árbol de la raíz tiene trece ficheros que ninguna auditoría ha mirado, entre
ellos los once `walkforward_stability_*.json` por variante y
`backtest_summary.json`. **Esto no es un detalle de rutas: es material no
auditado del expediente.**

### 2.2 `N ≥ 15`: hay cuatro estrategias más con resultados publicados

```
$ python3 -I -c "
import json
d=json.load(open('results/backtest_sizing05.json'))
print('size_fraction:', d['size_fraction']); print('csv:', d['csv'])
print('claves:', list(d['test_results']))"
size_fraction: 0.05
csv: data/btc_usd_5y_1d.csv
claves: ['mean_reversion', 'ma_cross', 'breakout', 'trend_following']
```

Mismo sizing (0.05) y mismo CSV congelado que las once de Fase A.
`ma_cross` ya está contada; **`mean_reversion`, `breakout` y
`trend_following` no están en ningún recuento de `N`**. N4 midió el efecto:
`V` se dobla (0.000702 → 0.001550) y el listón salta de **1.3118 a 1.8024**.
**Salvedad de N4, que hay que conservar:** el efecto lo manda casi entero
`mean_reversion`, a ~3.5 desviaciones del resto. Es una cota colgada de un
outlier, no un listón nuevo.

### 2.3 El Sharpe de Fase B no tiene holdout

Todas las rutas de aquí en adelante son **desde la raíz del repo**, que no es
`fix-fase2/`. `portfolio_runner.py` y la equity viven solo en `fix-fase2/`;
`backtest_sizing05.json` solo en la raíz. Confundirlas es el error de rutas
que el segundo agente de N4 identificó como causa mecánica de uno de sus dos
errores CRÍTICOS.

```
$ grep -c "TRAIN_FRAC\|train_test\|holdout" fix-fase2/src/portfolio_runner.py
0
$ ls src/portfolio_runner.py
ls: cannot access 'src/portfolio_runner.py': No such file or directory
$ wc -l fix-fase2/results/portfolio_equity.csv
4405 fix-fase2/results/portfolio_equity.csv
$ head -2 fix-fase2/results/portfolio_equity.csv | cut -c1-30
date,0
2014-09-17,1.0
$ tail -1 fix-fase2/results/portfolio_equity.csv | cut -c1-12
2026-10-07,4
```

4404 filas, **2014-09-17 → 2026-10-07**: la historia entera, sin split. Los
once Sharpes de `V` cubren 730 días (2024-10 → 2026-10).

### 2.4 El holdout ya estaba pre-registrado, y eso es lo que lo hace legítimo

`docs/fase_b_reevaluacion_resultado.md:14-22`: los tres tramos T1
(2015-09→2018-12), T2 (2019→2022) y T3 (2023→fin) se fijaron **antes de
correr**, y la métrica decisiva fue *"aprobada por Pablo 2026-10-09, antes de
la corrida"*.

**Por eso esta tarea no elige un split.** Usa el que ya estaba comprometido
por escrito. Elegir un split nuevo ahora, viendo el resultado, sería cambiar
la métrica — prohibido, y el motivo por el que esta tarea existe.

### 2.5 `T` nunca era la restricción (N5 · B-d)

Con `N ≤ 3`, los 11,9 años que ya están en el repo sobran. El "listón
inalcanzable por datos" era **`N=12` disfrazado de escasez de datos**. Y con
`N` bajo la restricción activa no es el DSR sino **`t > 3`, que no se
reinicia**: listón 0.870, no 0.472.

### 2.6 Lo que esto NO prueba

Que Fase B esté muerta. El holdout tiene dirección conocida (en contra), pero
la magnitud no está medida: puede que T3 confirme y puede que no. **Se mide,
no se supone.** Y el recuento de `N` puede subir el listón o dejarlo donde
está según cómo se resuelva el outlier.

---

## 3. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

Dos pasos separados, los dos obligatorios. Al terminar, escribir
`## Registro de revisión némesis` al final de ESTE archivo y **PARAR**.

**Los scripts de la Fase 0 van en `fix-fase2/fase0_n6/`**, nunca en
`auditoria_n6/`, que es del Alcance. N4 recibió esta crítica de su segundo
agente y tenía razón: un documento que reprocha a otro no citar su fuente no
puede llegar sin scripts detrás.

### Paso A — Verificación de hechos

Reverificar con comandos propios los seis puntos de la sección 2, cada uno con
comando, salida pegada y veredicto `CONFIRMADO`/`REFUTADO`/`NO VERIFICABLE`.

Añadir, con salida pegada:

- **A-1.** Inventariar **los trece ficheros de `results/` que ninguna
  auditoría ha mirado**. Para cada uno: qué estrategia o experimento
  documenta, con qué sizing, sobre qué CSV, y **si constituye un trial** bajo
  la regla que el Alcance va a escribir. Es el paso que decide si `N` es 15 o
  más.
- **A-2.** ¿Los dos árboles (`results/` y `fix-fase2/results/`) se contradicen
  en algún fichero con el mismo nombre? Comparar los dos comunes al byte y
  decir cuál manda. Si se contradicen, es un hallazgo mayor que el recuento.
- **A-3.** Verificar que los tramos T1/T2/T3 de `portfolio_walkforward_temporal.json`
  son reproducibles con los CSV congelados y reproducen los Sharpe/t/DSR
  publicados (1.33/1.22/0.57 y 0.824/0.772/0.301).
- **A-4.** Verificar el intérprete y que no hay red (N5 midió 0/10 fuentes).
  Si algo intenta descargar, es el defecto H1: **reportarlo, no sortearlo**.
- **A-5.** Reverificar de forma independiente **el número que esta tarea va a
  usar como eje**: que `V` con las tres estrategias añadidas da 0.001550 y
  listón 1.8024. Es de N4, no mío, y no vale creerlo.

### Paso B — Ataque adversarial al planteamiento

Mínimo cinco objeciones reales, con severidad y qué cambiaría del Alcance. Si
no se encuentra ninguna, **decir por qué no se encontró**.

- **B-a.** ¿Es legítimo medir con holdout **ahora**? El split estaba
  pre-registrado, sí — pero la **decisión de usarlo como criterio de holdout**
  se toma hoy, después de ver que el número no cuadra. Un escéptico diría que
  eso es elegir el test después del resultado por la puerta de atrás.
  Responder con argumento: ¿qué distingue esto de cambiar la métrica?
  **Si la respuesta honesta es que no se distingue, el paso 4.2 sobra y hay
  que decirlo.**
- **B-b.** Si `N` sube a 15 o más, el listón sube y Fase B se aleja. Si el
  Sharpe se mide con holdout, también baja. **Las dos correcciones van en la
  misma dirección.** ¿Hay alguna corrección pendiente que vaya en la
  dirección contraria y que esta tarea esté omitiendo? Buscarla activamente:
  un brief que solo encuentra pruebas en un sentido está mal construido.
- **B-c.** El DSR se aplicó a un portfolio que no pertenece a la familia de
  trials que forma su `V`. ¿Existe un test estándar para esa situación, o la
  respuesta honesta es que **no hay test** y Fase B no es decidible con este
  material? La segunda opción es admisible y hay que decirla si es la cierta.
- **B-d.** ¿Cuenta esta tarea como trial? Recalcular el Sharpe de la misma
  regla con un split pre-registrado no es un intento nuevo. Confirmarlo o
  refutarlo, porque si cuenta, la tarea se penaliza a sí misma.
- **B-e.** La objeción que no está en esta lista.

### Maker/Verifier

Tras escribir el registro, invocar un segundo agente que **solo critique ese
registro**. Pegar su crítica literal y responder hallazgo por hallazgo,
reverificando con comandos propios antes de aceptar nada. En N4 este paso
encontró **dos errores CRÍTICOS** que la némesis no vio. No es un trámite.

### NO-GO de la Fase 0

- Sin intérprete usable → PARAR.
- Si A-2 encuentra que los dos árboles de resultados **se contradicen** →
  PARAR y reportar. Sería un hallazgo de orden superior al de esta tarea.
- Si A-3 no reproduce los tres tramos → PARAR. Sin eso, 4.2 no se sostiene.
- Si B-a concluye que medir con holdout ahora **es** cambiar el test después
  del resultado → PARAR. La tarea estaría mal planteada de raíz.
- Si algo de la §2 sale REFUTADO → PARAR.

---

## 4. Alcance (NO EJECUTAR sin OK escrito de Pablo en la sección 7)

Scripts en `fix-fase2/auditoria_n6/`, salida en JSON del mismo nombre.
Timeout **20 minutos** por paso; si uno no termina, matarlo, anotarlo y seguir.

| # | Paso | Entrega |
|---|---|---|
| 6.1 | Escribir `fix-fase2/docs/registro_N.md`: una línea por trial con fecha, fichero de resultado, sizing, CSV y commit si es rastreable. Incluir los once de Fase A, las tres de `backtest_sizing05.json`, el portfolio de Fase B, y lo que A-1 encuentre. Marcar el duplicado (nº12 = nº9) | `registro_N.md` |
| 6.2 | **La regla prospectiva**: qué cuenta como trial de aquí en adelante, en prosa accionable, con los casos límite resueltos (¿una variante de parámetro? ¿un universo nuevo? ¿una reejecución?) | sección de `registro_N.md` |
| 6.3 | Recalcular el listón con el `N` que resulte de 6.1, y con el duplicado colapsado. Tabla con y sin `mean_reversion`, declarando que es un outlier a ~3.5 sd | `salida_6_3_liston.json` |
| 6.4 | Medir el Sharpe de Fase B **en el holdout pre-registrado** (T3, 2023→fin) y compararlo contra el listón de 6.3 y contra `t > 3`. Sin elegir split nuevo | `salida_6_4_holdout.json` |
| 6.5 | Enumerar los tests que podrían decidir Fase B —DSR como está, DSR con familia corregida, `t > 3`, bootstrap del IC, o ninguno— con **su umbral y qué asunción exige cada uno**. No elegir | `salida_6_5_tests.json` |
| 6.6 | Informe `fix-fase2/docs/auditoria_n6.md`: el veredicto de Fase B bajo cada test de 6.5, con el `N` de 6.1 y el Sharpe de 6.4 | el entregable |

**El entregable es 6.6 y no lleva recomendación.** Dice qué veredicto sale
bajo cada test, y qué habría que creer para que ese test sea el correcto. La
elección es de Pablo.

Si 6.5 concluye que **ningún** test disponible puede decidir Fase B con este
material, se escribe tal cual. Es un resultado, y cierra el expediente de otra
manera: Fase B quedaría indecidible, no débil.

### Límites de escritura

- **Permitido crear:** `fix-fase2/fase0_n6/*.py` (Fase 0),
  `fix-fase2/auditoria_n6/*.py` y sus JSON, `fix-fase2/docs/auditoria_n6.md`,
  `fix-fase2/docs/registro_N.md`.
- **Prohibido modificar:** cualquier `src/*.py`, cualquier `results/*.json` de
  los dos árboles, cualquier CSV, cualquier documento de dictamen previo. Para
  ejecutar algo de `src/` con otros parámetros, se importa y se llama desde
  el directorio de la tarea; **no se edita**.
- **Prohibido evaluar ninguna estrategia nueva**, ni una variante de
  parámetro, ni sobre datos nuevos ni viejos. Esta tarea mide lo ya medido,
  mejor. Si un paso exige probar una regla, está mal diseñado: parar y
  reportar.
- **Prohibido descargar.** No hay red (N5: 0/10 fuentes). Todo sale de los
  CSV congelados.
- Nada se activa.

### NO-GO del Alcance

- Si 6.1 no puede fechar ni rastrear un trial, se escribe como **no
  auditable** con esa etiqueta. No inventar una procedencia plausible.
- Si 6.4 no reproduce el tramo T3 publicado → parar en 6.4 y reportar.
- Si el listón de 6.3 depende enteramente de `mean_reversion`, decirlo en la
  cabecera de la tabla, no en una nota al pie.

---

## 5. Lo que esta tarea NO hace

- **No elige la `V`.** H10 sigue abierto y esta tarea no lo cierra.
- **No busca universo nuevo.** No hay red, y N5 demostró que `T` no era la
  restricción: lo que haría falta es independencia de muestra, no historia.
- **No reabre el edge estructural.** N5 · B-c: la fórmula del listón no sabe
  si la hipótesis predice, y las colas del carry lo suben. No hay ventaja.
- **No audita el harness.** N1 lo hizo y está limpio.

---

## 6. Entregables

1. `## Registro de revisión némesis` al final de este archivo, con la crítica
   del segundo agente pegada literal y respondida.
2. `fix-fase2/docs/registro_N.md`.
3. `fix-fase2/docs/auditoria_n6.md`.
4. `fix-fase2/fase0_n6/` y `fix-fase2/auditoria_n6/`.
5. PR contra **`fase-b-recuperada`**, nunca contra `main`.

Mecánica de ejecución (intérprete, red, timeouts) al registro némesis.
Resultados a `auditoria_n6.md`. No mezclar.

`shared/` no existe en este repo y no va a existir.

---

## 7. Estado de la tarea

**PARADO EN FASE 0.** Pablo escribe aquí el OK, con fecha, cuando haya leído
el registro némesis.

```
OK para ejecutar el Alcance: [pendiente]
```
