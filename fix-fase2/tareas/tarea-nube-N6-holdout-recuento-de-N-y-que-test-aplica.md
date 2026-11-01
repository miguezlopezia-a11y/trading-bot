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

---

## Registro de revisión némesis

**Fecha:** 2026-11-01 · **Ejecutor:** sesión N6 en la nube (Claude Code, Opus 5).
**Rama:** `nube/n6-holdout-y-recuento`, cortada de `fase-b-recuperada` @ `b158016`.
PR contra `fase-b-recuperada`, nunca contra `main`.
**Alcance ejecutado:** solo la **Fase 0** (§3), pasos A y B, más el segundo
agente del Maker/Verifier. **Ni un paso de la §4.** La §7 sigue sin firma.
**Scripts:** `fix-fase2/fase0_n6/*.py`, nueve ficheros, cada uno ejecutable por
separado y cada uno con su JSON de salida. Ninguno está en `auditoria_n6/`.
**Lectura previa:** las cuatro del encabezado, enteras y en orden. El registro
némesis de N4 completo, incluida la crítica literal del segundo agente y las
dieciséis respuestas.

**Nota de rutas.** El brief dice en su §2.3: *"Todas las rutas de aquí en
adelante son **desde la raíz del repo**, que no es `fix-fase2/`"*. Ese convenio
**se rompe en su propia §2.4**, que cita
`docs/fase_b_reevaluacion_resultado.md:14-22` — un fichero que desde la raíz no
existe. En este registro cada bloque dice desde dónde corre: los que tocan
`results/` de la raíz corren desde la raíz; los que tocan el pipeline o la
equity corren desde `fix-fase2/`. Es la misma confusión de rutas que el segundo
agente de N4 identificó como causa mecánica de uno de sus dos errores CRÍTICOS,
y aquí vuelve a aparecer en el brief que la denuncia.

### Resumen ejecutivo

| | Resultado |
|---|---|
| Hechos de la §2 | **4 CONFIRMADOS** (2.1, 2.3, 2.4, 2.6), **1 CONFIRMADO con la cifra corregida** (2.2: el outlier está a 4.24–4.49 sd, no a ~3.5), **1 CONFIRMADO en parte y REFUTADO en parte** (2.5: `t>3` manda para `N≤2`, no para `N=3`) |
| A-1 inventario de los 13 | **Hecho. `N` no pasa de 15 por este inventario.** Los once `walkforward_stability_*` no añaden estrategias: cubren las mismas de `V(11)`. Hallazgo nuevo: los produjo `yf.download`, no el CSV congelado |
| A-2 ¿se contradicen los árboles? | **NO.** Los dos ficheros comunes son idénticos al byte y semánticamente. Los conjuntos difieren; el contenido no. **NO-GO no se dispara** |
| A-3 tramos T1/T2/T3 | **REPRODUCEN los tres, campo a campo, IC del bootstrap incluidos** — pero **solo re-simulando con el sello `20261009`**. Desde la equity congelada del repo, **T3 no reproduce**. **NO-GO no se dispara**, y 6.4 tal como está escrito lo dispararía en falso |
| A-4 intérprete y red | Python 3.13.18 + numpy/pandas. **0 de 10 fuentes de mercado**, PyPI sí. 8 módulos de `src/` descargarían si se ejecutasen: reportados, no parcheados |
| A-5 el eje de la tarea | **CONFIRMADO al bit.** `V(15) = 0.001550366`, listón **1.8024**. `V(12)` reproduce con diferencia **0.0e+00** |
| Paso B | **10 objeciones**, de ellas **2 CRÍTICAS** (B-a, B-b) y **4 ALTAS**. B-a vacía la función decisoria de 6.4. B-b encuentra la corrección contraria que el brief pide, la mide, y **en una construcción Fase B pasa** |
| Maker/Verifier | pendiente de pegar abajo |

**Lo que cambia respecto al brief.** El brief dice que hace tres cosas: cerrar
el recuento de `N`, medir Fase B con el holdout pre-registrado, y enumerar qué
tests podrían decidir. De las tres:

1. **El recuento de `N` se cierra, y resulta casi vacío.** `N ≥ 15` se
   confirma, pero **el 89 % del salto del listón lo aporta un único trial**
   (`mean_reversion`, a 4.24 sd). Sin él, el recuento mueve el listón **+0.054**,
   que es ruido al lado de los ±0.49 de H10. La primera de las dos correcciones
   de la tarea es, medida, casi inconsecuente salvo que se decida conservar el
   outlier — y esa decisión, tomada hoy, es ella misma una elección de métrica.
2. **La medición con holdout es legítima; usarla como criterio no.** Lo que
   estaba pre-registrado era el split **y una métrica decisiva distinta** (≥2
   de 3 tramos con IC95 positivo), que ya se aplicó y dio SUPERADO. Comparar el
   Sharpe de T3 contra el listón del DSR es un **criterio nuevo**, elegido hoy.
   Ver B-a, que es la objeción que decide la tarea.
3. **La enumeración de tests sí se sostiene, y su respuesta honesta es que
   ninguno decide.** Ver B-c.

Y una cosa que el brief no contempla y que sale de medirlo: **las dos
correcciones no solo van en la misma dirección, van más lejos de lo que el
brief dice.** Medir en T3 baja el Sharpe (1.008 → 0.572) **y sube el listón**
(1.3117 → 1.7007, porque la PSR va con `√(T−1)`), y sube también el de `t>3`
(0.870 → 1.557). Fase B pasa `t>3` en la muestra completa y **no lo pasa en
T3**. No hay compensación por ningún lado.

---

## Paso A — Verificación de hechos

Todo reverificado con comandos propios. Donde se reproduce aritmética del
expediente, está **reimplementada desde cero** (`statistics.NormalDist`, PSR,
`E[max_N]`, ajuste AR(1) y block bootstrap escritos a mano en
`fase0_n6/a5_v_y_liston_n15.py` y `fase0_n6/a3_tramos_t1_t2_t3.py`) y no
importada de `src/`. Lo único que se importa de `src/` es el pipeline de
backtest (`strategies` + `backtester`), porque el brief prohíbe editarlo y
reimplementar un backtester sería evaluar de otra forma, no reverificar.

### §2.1 — El repo tiene dos árboles de resultados y comparten dos ficheros → **CONFIRMADO**

Desde la raíz:

```
$ ls results/ | wc -l
15
$ ls fix-fase2/results/ | wc -l
12
$ comm -12 <(ls results/ | sort) <(ls fix-fase2/results/ | sort)
rigor_estadistico.json
walkforward_stability_rsi_hidden_divergence.json
```

Los tres números salen. **Dos desviaciones de forma en la redacción del brief,
que importan porque están en la sección que manda reverificar:**

- El brief dice *"los **once** `walkforward_stability_*.json` por variante"*
  entre los trece de la raíz. Son once ficheros `walkforward_stability*`, sí,
  pero cubren **diez** estrategias distintas: el undécimo es
  `walkforward_stability.json` sin sufijo (el default, `ma_cross`, duplicado), y
  la estrategia que falta, `rsi_hidden_divergence`, está en el conjunto **común**
  a los dos árboles, no entre los trece. Ver A-1.
- El brief dice *"el árbol de la raíz tiene trece ficheros que **ninguna
  auditoría ha mirado**"*. No es exacto: `backtest_sizing05.json` **lo miró
  N4**, y es el fichero sobre el que descansa su hallazgo B-03 y el eje de esta
  tarea. Los no mirados son doce.

### §2.2 — `N ≥ 15`: hay tres estrategias más con resultados publicados → **CONFIRMADO; la salvedad del outlier, CONFIRMADA con la cifra corregida**

Desde `fix-fase2/`:

```
$ python3 fase0_n6/a5_v_y_liston_n15.py
=== A-5.0 §2.2: que dice backtest_sizing05.json ===
  size_fraction : 0.05
  csv           : data/btc_usd_5y_1d.csv
  claves        : ['mean_reversion', 'ma_cross', 'breakout', 'trend_following']
  sharpes       : {'mean_reversion': -1.75, 'ma_cross': 0.81, 'breakout': -0.02, 'trend_following': -0.15}
```

Mismo sizing y mismo CSV congelado que las once. `ma_cross` ya está contada;
las otras tres no están en ningún recuento. **CONFIRMADO.**

**La salvedad: `mean_reversion` es un outlier, y más de lo que el brief dice.**

```
$ python3 -I fase0_n6/a7_outlier_mean_reversion.py
  trial                        sharpe_d   z (deja-uno-fuera)
  mean_reversion            -0.09167138               -4.239  <-- OUTLIER
  sma_timing_5              -0.01561966               -0.826
  tsmom_7                   -0.01353410               -0.768
  trend_following           -0.00804383               -0.617
  tsmom_365                 -0.00093498               -0.425
  breakout                  -0.00081649               -0.421
  sma_timing_10              0.00910306               -0.159
  rsi_hidden_divergence      0.02695861                0.311
  sma_timing_304             0.02699677                0.312
  sma_timing_20              0.04123968                0.696
  ma_cross                   0.04228846                0.725
  connors_rsi2               0.04757982                0.873
  sma_timing_100             0.05256141                1.017
  PORTFOLIO                  0.05278116                1.023
  sma_timing_50              0.05841924                1.191

  Afirmacion del brief: mean_reversion a ~3.5 sd del resto.
  Medido: z = -4.239
  Segundo mas extremo: sma_timing_50 con |z| = 1.191
```

Contra las otras bases posibles tampoco sale 3.5:

```
  contra las 11 de V(11)                   z_mean_reversion=-4.405
  contra las 11 + portfolio (V12)          z_mean_reversion=-4.490
  contra 11+portfolio+breakout+trend       z_mean_reversion=-4.239
```

**La sustancia del brief se confirma y se refuerza; la cifra "~3.5" está
subestimada: son 4.24–4.49 sd según el conjunto de referencia, y ninguno da
3.5.** El segundo más extremo está a 1.19 sd: no hay un segundo outlier, hay
uno y una masa.

**Y la consecuencia, que el brief no mide:**

```
  construccion                               N             V   liston    delta
  N=12, expediente (11+portfolio)           12    0.00070219   1.3118  +0.0000
  N=15, con las 3                           15    0.00155037   1.8024  +0.4906
  N=14, con las 3 SIN mean_reversion        14    0.00072911   1.3658  +0.0540
  N=13, solo mean_reversion anadida         13    0.00173283   1.8251  +0.5133

  Fraccion del efecto que aporta mean_reversion: 89.0%
```

**El 89 % del salto es un solo trial.** Sin él, el recuento de `N` mueve el
listón +0.054. Ver B-e3: eso vacía buena parte de la primera corrección de la
tarea.

### §2.3 — El Sharpe de Fase B no tiene holdout → **CONFIRMADO**

Desde `fix-fase2/`:

```
$ python3 fase0_n6/a6_holdout_y_coherencia.py
=== §2.3a el codigo no tiene split ===
  grep 'TRAIN_FRAC' src/portfolio_runner.py -> (0 coincidencias)
  grep 'train_test' src/portfolio_runner.py -> (0 coincidencias)
  grep 'holdout' src/portfolio_runner.py -> (0 coincidencias)
  grep 'split' src/portfolio_runner.py -> 68:    esperado = open(sidecar).read().split()[0]
100:            f.rsplit("_", 1)[1][:8] for f in os.listdir(data_dir)

  Comparar con el pipeline de Fase A, que SI tiene split:
  39:TRAIN_FRAC = 0.6
  152:    split = int(len(df) * TRAIN_FRAC)

  ¿Existe src/portfolio_runner.py en la RAIZ del repo?
    NO   (solo esta en fix-fase2/src/)

=== §2.3b las dos ventanas ===
  objeto evaluado (equity congelada): 4404 dias, 2014-09-17 -> 2026-10-07
  las 11 series de V (OOS de Fase A) : 731 velas, 2024-10-06 -> 2026-10-06
  solape temporal: la V cubre 16.6% de la ventana del objeto evaluado
```

Las dos únicas apariciones de `split` son un `.read().split()` y un `rsplit` de
nombres de fichero, igual que dijo N4 (su B-14). La equity son 4404 días,
2014-09-17 → 2026-10-07: la historia entera. **CONFIRMADO.** El brief dice
"4404 filas"; son 4404 **días** y 4403 retornos, y el fichero tiene 4405 líneas
con la cabecera — detalle sin consecuencia, anotado por completitud.

### §2.4 — El holdout estaba pre-registrado → **CONFIRMADO como texto. Su legitimidad es otra cosa y la decide B-a**

El texto existe y es literal (`fix-fase2/docs/fase_b_reevaluacion_resultado.md`,
no `docs/`):

```
     14| **Diseño (fijado antes de correr):** 3 tramos contiguos por ciclos de
     15| mercado: T1 2015-09→2018-12 (acumulación+bull 2017+bear 2018), T2
     16| 2019→2022 (acumulación+bull 2021+bear 2022), T3 2023→fin (bull 2023-2025).
     ...
     20| **Métrica decisiva (aprobada por Pablo 2026-10-09, antes de la corrida):**
     21| ≥2 de 3 tramos con IC95 del retorno positivo (límite inferior > 0) y ningún
     22| tramo con IC claramente negativo (límite superior < 0).
```

**CONFIRMADO** que el texto dice lo que el brief dice que dice. Pero el brief
da un paso más —*"y eso es lo que lo hace legítimo"*— y ese paso no es un hecho
verificable, es un argumento. **Dos cosas lo debilitan, y las dos son del Paso
A, no del Paso B:**

**(a) La fecha del pre-registro no es auditable.**

```
$ python3 -I fase0_n6/b_a_preregistro_auditable.py
=== B-a.3 ¿se puede FECHAR el pre-registro por git? ===
  portfolio_walkforward_temporal.py          d34b147 2026-10-29 Recupera el trabajo de Fase B, ...
  fase_b_reevaluacion_resultado.md           d34b147 2026-10-29 Recupera el trabajo de Fase B, ...
  portfolio_walkforward_temporal.json        d34b147 2026-10-29 Recupera el trabajo de Fase B, ...
  portfolio_equity.csv                       d34b147 2026-10-29 Recupera el trabajo de Fase B, ...

  Commits del repo entre la fecha declarada del pre-registro
  (2026-10-09) y el commit que trae el material (2026-10-29):
    (NINGUNO)
```

El diseño de los tramos, la métrica decisiva, el código, los resultados y la
curva de equity **llegan al repo en el mismo commit**. No hay ningún commit
entre el 2026-10-07 y el 2026-10-29. Luego *"fijado antes de correr"* es
**autoatestiguado**: lo afirma el mismo documento que publica el resultado.
Eso no dice que sea falso; dice que **no es auditable desde este repo**, con la
misma vara con la que N4 (su A-3) declaró NO VERIFICABLE la cadena
`N = 11 → 12 → 14`. Aplicar una vara más blanda aquí, porque el pre-registro
conviene al planteamiento de la tarea, sería la doble vara que el hallazgo 6
del segundo agente de N4 reprochó.

**(b) Lo pre-registrado era el split *y otra métrica*.** La métrica decisiva
aprobada el 2026-10-09 no es "el Sharpe de T3 contra el listón del DSR": es
"≥2 de 3 tramos con IC95 positivo y ninguno claramente negativo". Esa métrica
**se aplicó y dio SUPERADO** (`{'superado': True, 'tramos_positivos': 2,
'tramos_claramente_negativos': 0}`). Ver B-a.

### §2.5 — `T` nunca era la restricción → **CONFIRMADO en parte, REFUTADO en parte**

Las dos cifras que el brief da salen:

```
  liston t>3 (anual) = 3/sqrt(4336)*sqrt(365) = 0.8704     (brief: 0.870)
  N=1   liston_DSR=0.4723                                   (brief: 0.472)
```

Y los `T` mínimos de N5 se reverifican con la `V` y las colas del expediente:

```
  N=1   DSR: T_eff minimo =     940 dias =   2.58 anos      (N5: 2.6)
  t>3     : T_eff minimo =    3240 dias =   8.88 anos       (N5: 9.0)
  T_eff del expediente = 4336 dias = 11.88 anos
```

**Pero la afirmación "con `N ≤ 3` la restricción activa no es el DSR sino
`t > 3`" es falsa en `N = 3`:**

```
  N=1   liston_DSR=0.4723  manda: t>3
  N=2   liston_DSR=0.7336  manda: t>3
  N=3   liston_DSR=0.9014  manda: DSR     <-- se invierte aqui
  N=5   liston_DSR=1.0729  manda: DSR
  N=12  liston_DSR=1.3118  manda: DSR
  N=15  liston_DSR=1.3654  manda: DSR
```

El cruce está entre `N = 2` y `N = 3`. **CONFIRMADO para `N ≤ 2`, REFUTADO
para `N = 3`.** La diferencia no es cosmética: B-c muestra que el veredicto de
Fase B **cambia de signo** exactamente entre `N = 2` (pasa) y `N = 3` (no pasa),
así que el límite importa.

Cifra nueva, por completitud: con `N = 15` el `T` que el DSR exigiría es
**208.7 años**, no los ~96 que N1 calculó con `N = 12`.

### §2.6 — Lo que esto NO prueba → **CONFIRMADO**

No es una proposición empírica, es una regla de método, y se cumple. Lo
refuerzo con dato propio, que es lo que el brief pide en B-b: existe al menos
una corrección pendiente que va **en contra** del recuento y del holdout, está
medida en B-b, y **en una de sus construcciones Fase B pasa**. Luego "el
holdout tiene dirección conocida pero la magnitud no está medida: se mide, no
se supone" se cumple, y el neto sigue siendo desconocido. **CONFIRMADO como
regla y como estado de cosas.**

---

### A-1 — Inventario de los ficheros de `results/` que ninguna auditoría ha mirado

Desde la raíz, `python3 -I fix-fase2/fase0_n6/a1_inventario_results_raiz.py`.
Salida completa en el script; aquí el resumen con lo que el brief pide de cada
uno (estrategia, sizing, CSV, ¿trial?):

| Fichero | Documenta | Sizing | Datos | ¿Trial? |
|---|---|---|---|---|
| `backtest_sizing05.json` | backtest OOS de 4 estrategias | **0.05** (en el JSON) | `data/btc_usd_5y_1d.csv` | **SÍ, 3 de 4** fuera de `V(11)`: `mean_reversion`, `breakout`, `trend_following` |
| `backtest_summary.json` | las mismas 4 estrategias | **0.95** (default de `backtester.py`, no pasado) | **`yf.download`** | **NO COMMENSURABLE**: ni el mismo sizing ni el mismo origen |
| `walkforward_stability.json` | estabilidad de `ma_cross` (default), 4 ventanas | 0.05 | **`yf.download`** | **NO** — reejecución de una ya contada |
| `walkforward_stability_{connors_rsi2, ma_cross, sma_timing_5/10/20/50/100/304, tsmom_7/365}.json` (10) | estabilidad de cada una, 4 ventanas `[365/90, 730/180, 180/60, 365/180]` | 0.05 | **`yf.download`** | **NO** — las diez están en `V(11)` |

```
=== A-1 recuento ===
  walkforward_stability_*.json en results/ (raiz) : 11
  estrategias que cubren : 10 -> ['connors_rsi2', 'ma_cross', 'sma_timing_10',
    'sma_timing_100', 'sma_timing_20', 'sma_timing_304', 'sma_timing_5',
    'sma_timing_50', 'tsmom_365', 'tsmom_7']
  de ellas, FUERA de V(11): ninguna
  Fichero walkforward COMUN a los dos arboles (no contado arriba):
    walkforward_stability_rsi_hidden_divergence.json  estrategia=rsi_hidden_divergence
```

**Respuesta al paso que el brief dice que "decide si `N` es 15 o más": `N` no
pasa de 15 por este inventario.** Los once `walkforward_stability*` no añaden
ninguna configuración de estrategia nueva: reejecutan las mismas once de
`V(11)` sobre ventanas distintas, con los parámetros congelados y con la
prohibición explícita de optimizar escrita en el propio docstring
(`walkforward_stability.py:3-5`: *"Solo mide estabilidad: MISMO codigo, MISMO
parametros, distintas ventanas. Prohibido optimizar parametros"*). Bajo
cualquier regla razonable de "trial", eso es una reejecución, no un intento.

**Hallazgo nuevo que no está en ningún sitio del expediente, y es el que vale
de A-1:** los once se produjeron con **`yf.download`**, no con el CSV
congelado:

```
$ grep -n "yf.download" fix-fase2/src/walkforward_stability.py
42:    df = yf.download("BTC-USD", period="5y", interval="1d", auto_adjust=True, progress=False)
```

`period="5y"` se resuelve contra la fecha de ejecución, que no está registrada
en ningún lado. Luego esos once dictámenes (**diez "fragil", uno "estable"**)
están medidos sobre datos de **vintage desconocido** y no son reproducibles sin
red (A-4: 0 de 10 fuentes). Es el defecto H1/H5 de N1 intacto en material que
el expediente cita. Y lo que dicen no es menor: **`ma_cross`, la que el
expediente trató como ganadora de Fase A, sale `fragil`**; la única `estable`
es `connors_rsi2`. Nadie ha citado eso en ninguna de las tres fases. Ver B-e4.

### A-2 — ¿Se contradicen los dos árboles? → **NO. El NO-GO no se dispara**

Desde la raíz, `python3 -I fix-fase2/fase0_n6/a2_dos_arboles.py`:

```
--- RESULTS ---
  results                15 ficheros
  fix-fase2/results      12 ficheros
  comunes: 2 | solo en results: 13 | solo en fix-fase2/results: 10
    rigor_estadistico.json                           IDENTICO  6ce15b0c8722ee04
    walkforward_stability_rsi_hidden_divergence.json IDENTICO  99797a49f8ff2c45

--- SRC ---
  comunes: 12 | solo en src: 0 | solo en fix-fase2/src: 8
    (los 11 ficheros .py comunes: TODOS IDENTICOS; la 12ª entrada es el
     directorio personas/)
  solo en fix-fase2/src: backtester_paso2_ref.py, portfolio_bateria.py,
    portfolio_runner.py, portfolio_supervivencia.py,
    portfolio_walkforward_temporal.py, potencia_fase_b.py,
    timesfm_harness.py, timesfm_t3_zeroshot.py

--- DATA ---
  data                    1 ficheros   (solo data/brain/knowledge.jsonl)
  fix-fase2/data          5 ficheros
  solo en fix-fase2/data: btc_usd_5y_1d.csv, multi, multi_muertos, paper_journal.db

=== A-2 veredicto ===
  Ningun fichero con el mismo nombre difiere en contenido.
  Los arboles NO se contradicen: se SOLAPAN parcialmente.
  -> NO-GO del brief NO se dispara.
  json.load igualdad semantica de rigor_estadistico.json: True
```

**Veredicto: los dos árboles no se contradicen.** Los dos ficheros comunes son
idénticos al byte **y** semánticamente (`json.load` igual). Lo que difiere son
los **conjuntos**, no el contenido — exactamente el matiz que el hallazgo 16
del segundo agente de N4 obligó a introducir. Cuál manda: para los no comunes,
el único que existe; para los comunes, da igual.

**Y la consecuencia práctica, que vale más que el veredicto:** el CSV de Fase A
(`btc_usd_5y_1d.csv`), los CSV multi-activo y toda la equity **existen solo en
`fix-fase2/`**. `results/` de la raíz es el único sitio donde están
`backtest_sizing05.json` y los once `walkforward_stability*`. **Ningún script
puede leer las dos cosas con el mismo `cwd`.** Eso no es una molestia: es la
razón mecánica por la que N4 abrió el fichero equivocado, y el Alcance de N6
—que necesita `backtest_sizing05.json` de la raíz y la equity de `fix-fase2/`—
va a chocar con lo mismo si no declara el `cwd` de cada paso.

### A-3 — ¿Reproducen los tramos T1/T2/T3? → **SÍ, con el sello `20261009`. El NO-GO no se dispara**

**Primer intento, desde la equity congelada del repo** (`python3 -I
fix-fase2/fase0_n6/a3_tramos_t1_t2_t3.py`, desde `fix-fase2/`):

```
  results/portfolio_equity.csv : 4404 dias, 2014-09-17 -> 2026-10-07

  [T1_2015-2018]  1218 retornos   -> REPRODUCE  (7/7 campos)
  [T2_2019-2022]  1461 retornos   -> REPRODUCE  (7/7 campos)
  [T3_2023-fin ]  1376 retornos   -> NO REPRODUCE
    sharpe_anual   mio=0.573      publicado=0.572      *** DIFIERE ***
    t_stat         mio=1.1        publicado=1.1        OK
    dsr            mio=0.3013     publicado=0.3008     *** DIFIERE ***
    n_obs_eff      mio=1354       publicado=1356       *** DIFIERE ***
    pnl_pct        mio=25.95      publicado=25.95      OK
    ic_lo          mio=-5.82      publicado=-5.86      *** DIFIERE ***
    ic_hi          mio=20.35      publicado=20.3       *** DIFIERE ***
```

T1 y T2 reproducen **campo a campo, IC del block bootstrap incluidos** (seed
42/43, B=10000, bloque 21). **T3 no**, y la diferencia es de exactamente **2
observaciones**.

**Hipótesis y comprobación** (`a3b_tramo_t3_sello.py`, desde `fix-fase2/`, con
`STAMP_CONGELADO=20261009` y **sin** `PERMITIR_DESCARGA`, así que el loader
parcheado por N1 fallaría en duro antes que descargar):

```
$ ls data/multi/*.csv | sed 's/.*_\([0-9]*\)\.csv/\1/' | sort | uniq -c
     10 20261007
     10 20261009
$ for s in 20261007 20261009; do tail -1 data/multi/btc_usd_$s.csv | cut -d, -f1; done
2026-10-07
2026-10-09

$ STAMP_CONGELADO=20261009 python3 fase0_n6/a3b_tramo_t3_sello.py
  equity re-simulada: 4406 dias, 2014-09-17 -> 2026-10-09
  equity en results/: 4404 dias, 2014-09-17 -> 2026-10-07
  max |diferencia| en las 4404 fechas comunes: 8.882e-16

  [T1_2015-2018] REPRODUCE   (6/6 campos)
  [T2_2019-2022] REPRODUCE   (6/6 campos)
  [T3_2023-fin] REPRODUCE
    sharpe_anual   mio=0.572            publicado=0.572            OK
    t_stat         mio=1.1              publicado=1.1              OK
    dsr            mio=0.3008           publicado=0.3008           OK
    ic95           mio=[-5.86, 20.3]    publicado=[-5.86, 20.3]    OK
    n_obs_eff      mio=1356             publicado=1356             OK
    pnl_pct        mio=25.95            publicado=25.95            OK
```

**Veredicto A-3: los tres tramos reproducen, campo a campo, IC incluidos. El
NO-GO de A-3 no se dispara.** La equity congelada en `results/` es del run con
sello `20261007`; el walk-forward publicado es del `20261009` (+2 velas), tal
como declara `fase_b_reevaluacion_resultado.md:8`. Las dos curvas coinciden a
**8.9e-16** en las 4404 fechas comunes: no hay inconsistencia, hay dos vintages.

**Pero esto rompe el NO-GO del Alcance tal como está escrito.** El brief dice:
*"Si 6.4 no reproduce el tramo T3 publicado → parar en 6.4 y reportar."* Desde
el fichero congelado del repo, T3 **no** reproduce. Un 6.4 escrito sin saber
esto pararía en falso, o peor, publicaría 0.573/0.3013 como "el Sharpe de T3" y
no cuadraría con el documento de dictamen. Ver B-e1.

**Y una cosa que A-3 deja a la vista y que es el núcleo de B-a** (está en el
propio docstring de `portfolio_walkforward_temporal.py:16-18`): *"Una sola
simulacion sobre datos completos (warm-up real, parametros congelados); la
equity se corta por tramo."* No hay entrenamiento en T1+T2 y prueba en T3. Los
parámetros están congelados a mano, no ajustados. **T3 es un tramo fuera de
muestra en el tiempo, no un holdout en el sentido "ajustado en train, medido en
test".** El brief lo llama *"el holdout pre-registrado"* nueve veces; es una
etiqueta que importa.

### A-4 — Intérprete y red → **HAY INTÉRPRETE. 0 de 10 FUENTES DE MERCADO**

Desde la raíz, `python3 -I fix-fase2/fase0_n6/a4_entorno_y_red.py`:

```
=== A-4.1 interprete ===
sys.executable : /usr/local/bin/python3
version        : 3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3 ]
=== A-4.2 modulos ===
  numpy          OK   2.5.3          scipy        NO   ModuleNotFoundError
  pandas         OK   3.0.5          statsmodels  NO   ModuleNotFoundError
  statistics     OK   (stdlib)       yfinance     NO   ModuleNotFoundError
                                     torch        NO   ModuleNotFoundError
                                     timesfm      NO   ModuleNotFoundError
=== A-4.3 venv citado en los docstrings de src/ ===
  /opt/trading-bot/venv/bin/python: NO EXISTE
=== A-4.4 red: 12 destinos, solo codigo HTTP ===
  Yahoo chart BTC-USD    http=000  NO  | curl: (56) CONNECT tunnel failed, response 403
  Yahoo fc               http=000  NO  | ...403
  Binance ping           http=000  NO  | ...403
  Coinbase               http=000  NO  | ...403
  Kraken                 http=000  NO  | ...403
  Bitstamp               http=000  NO  | ...403
  OKX                    http=000  NO  | ...403
  Bybit                  http=000  NO  | ...403
  Stooq                  http=000  NO  | ...403
  FRED                   http=000  NO  | ...403
  SSRN 2460551           http=000  NO  | ...403
  PyPI simple            http=200  ALCANZABLE
  destinos alcanzables en total: 1 de 12
```

**0 de 10 fuentes de mercado, confirmando N5. PyPI sí.** `scipy` se instalaría,
y nada del expediente lo necesita (la PSR/DSR usa `statistics.NormalDist`).
**SSRN 2460551 sigue inalcanzable**, así que en este registro no se cita
Bailey-LdP como autoridad: donde hace falta su definición se cita la
transcripción del repo (`fix-fase2/src/rigor_estadistico.py:17-22` y
`docs/rigor_estadistico_resultado.md`). Es la corrección que el hallazgo 6 del
segundo agente de N4 impuso, y aquí va aplicada desde el principio.

**Lo que descargaría si se ejecutase — reportado, no sorteado**, como manda el
brief:

```
src/walkforward_stability.py:42            fix-fase2/src/walkforward_stability.py:42
src/run_backtest.py:21                     fix-fase2/src/run_backtest.py:21
src/paper_runner.py:59                     fix-fase2/src/paper_runner.py:59
                                           fix-fase2/src/portfolio_runner.py:212
                                           fix-fase2/src/portfolio_supervivencia.py:67
```

De estos, `portfolio_runner.py:212` está detrás del parche de N1 (sello
explícito, `PERMITIR_DESCARGA=1` obligatorio, verificación de sha256); los
demás no. **Ningún script de esta Fase 0 ha descargado nada**, y el único que
re-simula (`a3b`) lo hace con `PERMITIR_DESCARGA` sin poner, así que el loader
habría fallado en duro antes que bajar un byte. **El NO-GO de A-4 no se
dispara.**

### A-5 — El número que esta tarea usa como eje → **CONFIRMADO AL BIT**

Desde `fix-fase2/`, con PSR, `E[max_N]` y AR(1) **reescritos a mano** desde
`statistics.NormalDist`, sin importar nada de `rigor_estadistico.py` ni de
`potencia_fase_b.py`:

```
=== A-5.2 reejecucion de las 11 + las 3, pipeline de Fase A ===
  ma_cross                 sharpe_diario=  0.04228846  anual=  0.8079  trades=  12
  sma_timing_5             sharpe_diario= -0.01561966  anual= -0.2984  trades= 105
  sma_timing_10            sharpe_diario=  0.00910306  anual=  0.1739  trades=  67
  sma_timing_20            sharpe_diario=  0.04123968  anual=  0.7879  trades=  40
  sma_timing_50            sharpe_diario=  0.05841924  anual=  1.1161  trades=  24
  sma_timing_100           sharpe_diario=  0.05256141  anual=  1.0042  trades=  13
  sma_timing_304           sharpe_diario=  0.02699677  anual=  0.5158  trades=   5
  tsmom_7                  sharpe_diario= -0.01353410  anual= -0.2586  trades=  70
  tsmom_365                sharpe_diario= -0.00093498  anual= -0.0179  trades=   1
  connors_rsi2             sharpe_diario=  0.04757982  anual=  0.9090  trades=  12
  rsi_hidden_divergence    sharpe_diario=  0.02695861  anual=  0.5150  trades=   3
  mean_reversion           sharpe_diario= -0.09167138  anual= -1.7514  trades=  51   <- FUERA de V(11)
  breakout                 sharpe_diario= -0.00081649  anual= -0.0156  trades=  30   <- FUERA de V(11)
  trend_following          sharpe_diario= -0.00804383  anual= -0.1537  trades=  12   <- FUERA de V(11)
  PORTFOLIO Fase B (trial nº12) sharpe_diario=0.05278115955

=== A-5.3 parametros del objeto evaluado (recalculados) ===
  T (retornos)   : 4403
  T_eff AR(1)    : 4336        (cableado: 4336)
  skew           : 1.036877   (cableado: 1.037)
  kurt raw       : 31.998897  (cableado: 31.999)
  sharpe anual   : 1.008383   (cableado: 1.008)

=== A-5.4 las dos V, con ddof=1 ===
  V(12) = 11 + portfolio                : 0.000702194770
    cableada en potencia_fase_b.py      : 0.0007021947704551833
    diferencia                          : 0.000e+00
  V(15) = 11 + portfolio + las 3        : 0.001550366155
    afirmado por N4                     : 0.001550
    coincide a 6 decimales?             : True
  cociente V(15)/V(12)                  : 2.2079

=== A-5.5 el liston, con PSR reescrita a mano ===
  N=12  V=0.00070219 SR0=0.04412 liston_anual=1.3118   expediente: 11+portfolio
  N=15  V=0.00155037 SR0=0.06972 liston_anual=1.8024   11+portfolio+3 extra
  N=12  V=0.00155037 SR0=0.06555 liston_anual=1.7223   V de 15, N=12 fijo
  N=15  V=0.00070219 SR0=0.04692 liston_anual=1.3654   V de 12, N=15

  Afirmacion de N4 a verificar: N=15 -> V=0.001550 y liston 1.8024
  medido aqui                : liston_anual=1.8024  -> COINCIDE
```

**CONFIRMADO. `V(15) = 0.001550366` y listón `1.8024`, reproducidos con
implementación independiente.** `V(12)` reproduce con diferencia **0.0e+00** y
`V(11)` también:

```
=== A-5.7 el duplicado colapsado (B-13 de N4) ===
  V(11) sin el portfolio                : 0.000701693564
    publicada en rigor_estadistico.json : 0.0007016935642058066
    diferencia                          : 0.000e+00
  V(10) sin portfolio y sin tsmom_365   : 0.000697416407
    N=11  V=0.00070169 liston_anual=1.2899   sin sujeto, N=11
    N=10  V=0.00069742 liston_anual=1.2634   sin sujeto ni duplicado, N=10
    N=14  V=0.00155294 liston_anual=1.7791   sin sujeto, +3, N=14
```

El eje de la tarea es sólido. **Lo que no es sólido es lo que se puede concluir
de él**, y eso es el Paso B.

---

## Paso B — Ataque adversarial al planteamiento

Diez objeciones. **Dos CRÍTICAS** (B-a, B-b), **cuatro ALTAS**, cuatro MEDIAS.
Ninguna ataca la **pregunta** de la §1 —sigue siendo la pregunta correcta— ni
el eje aritmético, que A-5 reproduce al bit. Lo que atacan es qué se puede
concluir, y la función decisoria de uno de los seis pasos.

---

### B-a · Medir en T3 es legítimo; **decidir** con T3 no lo es. El paso 6.4 sobra tal como está escrito — **CRÍTICA**

El brief pregunta si usar el holdout ahora es elegir el test después del
resultado, y dice que si la respuesta honesta es que sí, hay que decirlo. **La
respuesta honesta es que hay que separar dos cosas que el brief junta, y una
de ellas sí lo es.**

**(1) El split: legítimo, con una reserva.** Los tres tramos están escritos
antes del resultado en el propio código (`portfolio_walkforward_temporal.py:8-13`)
y en el documento de dictamen, con su justificación por ciclos de mercado y la
nota de que T1 empieza en 2015-09 *"porque es cuando el universo diversificado
existe (ETH entra 2015-08); se documenta, no se ajusta a resultados"*. Esta
tarea **no elige un split**: usa el que está. Y los números de T3 **ya están
publicados** desde el 2026-10-09 y reproducen campo a campo (A-3). No hay nada
que elegir.

La reserva es la de §2.4(a): **la fecha del pre-registro no es auditable**.
Diseño, código, resultados y equity llegan en el mismo commit. Eso no lo
invalida, pero significa que la legitimidad del split descansa en el testimonio
del propio documento, no en evidencia. **Si N4 declaró NO VERIFICABLE la cadena
`N = 11 → 12 → 14` con exactamente esta evidencia, el pre-registro de los
tramos tiene el mismo estatus y hay que decirlo con la misma letra.**

**(2) El criterio: NO legítimo. Y es lo que 6.4 hace.** Lo que se
pre-registró el 2026-10-09 no fue solo el split. Fue el split **y una métrica
decisiva**, literal: *"≥2 de 3 tramos con IC95 del retorno positivo y ningún
tramo con IC claramente negativo"*. Esa métrica **ya se aplicó** y su veredicto
está publicado: **SUPERADO** (`{'superado': True, 'tramos_positivos': 2,
'tramos_claramente_negativos': 0}`), reproducido en A-3.

El paso 6.4 del Alcance dice otra cosa: *"Medir el Sharpe de Fase B en el
holdout pre-registrado (T3, 2023→fin) y compararlo **contra el listón de 6.3 y
contra `t > 3`**"*. Ese es un **criterio distinto, aplicado al mismo split, y
elegido hoy**, después de ver que 1.008 no pasa 1.312.

La distinción no es sutil y se puede decir en una frase: **el split estaba
pre-registrado, pero el test que 6.4 quiere aplicarle, no.** Y la diferencia
entre "usar un split pre-registrado" y "cambiar la métrica" es precisamente que
el split se fija antes y el criterio también. Aquí solo se fijó uno de los dos.

**Y hay un agravante aritmético que lo hace peor, no mejor.** Medir en T3 no
mueve solo el numerador:

```
  ventana                      T  T_eff    Sh_an      t  lis_N12  lis_N15   lis_t3
  muestra completa          4405   4338   1.0082   3.48   1.3117   1.8022   0.8702
  T3 2023-fin               1378   1356   0.5721   1.10   1.7007   2.1944   1.5565
  ventana de V exacta        731    666   0.2798   0.38   2.1080   2.6126   2.2209
```

En la PSR el numerador va con `√(T−1)`: **acortar la ventana SUBE el listón**,
de 1.3117 a 1.7007 (y a 2.1944 con `V(15)`). El de `t>3` sube más, de 0.870 a
1.557. Y el Sharpe baja. **Fase B pasa `t>3` en la muestra completa y no lo
pasa en T3.** Un criterio que mueve a la vez el número y el umbral en la misma
dirección, elegido después de ver el resultado, no es un test: es la conclusión
escrita como si fuera un test.

> **Corrección propia.** Una versión previa de `fase0_n6/a6_holdout_y_coherencia.py`
> imprimía aquí que *"el listón DSR BAJA al acortar la ventana"*. Era falso y lo
> contradecía su propia tabla, pegada arriba. Está corregido en el script y
> declarado en él. Lo anoto porque es el mismo error de signo que el segundo
> agente de N4 encontró en su B-10, cometido en la Fase 0 que lo había leído.

**Respuesta a lo que el brief pregunta:** medir T3 y **reportarlo** es
legítimo, porque el número ya existe, está publicado y reproduce. **Elevarlo a
criterio de decisión no lo es**, y eso es lo que 6.4 hace al compararlo contra
un listón.

**Qué cambia del Alcance.** 6.4, tal como está escrito, **sobra**: su mitad de
medición ya está hecha en A-3 de esta Fase 0, y su mitad de comparación es el
test elegido a posteriori. Lo que sí cabe escribir, y es honesto, es una fila
en 6.6 que diga: *"el Sharpe de Fase B en el tramo 2023→fin es 0.572 con t=1.10
y DSR 0.301 (publicado, reproducido); el criterio pre-registrado para los
tramos era el de los IC95 y lo superó; ningún criterio basado en el listón del
DSR sobre T3 estaba pre-registrado"*. Sin veredicto.

**¿Dispara el NO-GO del brief?** El brief dice: *"Si B-a concluye que medir con
holdout ahora **es** cambiar el test después del resultado → PARAR. La tarea
estaría mal planteada de raíz."* **Se dispara sobre 6.4, no sobre la tarea.**
La conclusión es más estrecha que el NO-GO: *medir* no lo es, *decidir* sí. Y
los otros cinco pasos no dependen de B-a — 6.1 (registro de `N`), 6.2 (la regla
prospectiva) y 6.5 (enumerar tests) sobreviven intactos; 6.3 queda tocado por
B-d, no por B-a. **No marco el NO-GO como disparado sobre la tarea entera**,
porque hacerlo sería la desproporción que el segundo agente de N4 le reprochó a
N4 en su hallazgo 8. Lo marco sobre el paso, que es donde está.

---

### B-b · Sí hay corrección contraria, está medida, y en una construcción Fase B pasa — **CRÍTICA**

El brief lo pide bien: *"un brief que solo encuentra pruebas en un sentido está
mal construido"*. **La hay. Varias. Y la principal es grande.**

**La candidata principal: `N` efectivo por correlación entre trials.** El
`E[max_N]` del repo (`rigor_estadistico.py:95-103`) es el máximo esperado de
`N` extracciones **independientes** de `N(0,V)`. Los trials del expediente no
lo son: seis son el mismo parámetro barrido sobre la misma serie. N4 (su B-06)
lo afirmó y su segundo agente lo midió; aquí se mide entero y se lleva al
listón (`fase0_n6/b_correccion_contraria.py`, desde `fix-fase2/`):

```
=== B-b.1 matriz de correlacion de los trials (retornos diarios OOS) ===
  ventana comun: 730 dias, 2024-10-07 -> 2026-10-06
  Correlacion entre las SEIS sma_timing: media 0.6411  min 0.3678  max 0.8607
  (N4 B-06 afirmo media 0.641 / min 0.368 / max 0.861)   -> reproduce
  Matriz completa de las 11: media 0.3300  min -0.0058  max 0.8698

=== B-b.2 numero EFECTIVO de trials ===
  [las 11 de V(11)]  N nominal = 11
    rho medio : 0.3300   Cheverud-Nyholt : 9.04   Li-Ji : 6.54   N/(1+(N-1)rho) : 2.56
  [las 11 + las 3 = 14]  N nominal = 14
    rho medio : 0.2131   Cheverud-Nyholt : 12.16  Li-Ji : 8.46   N/(1+(N-1)rho) : 3.71

=== B-b.3 el liston con N efectivo, frente al N nominal ===
  objeto evaluado: T_eff=4336 skew=1.037 kurt=31.999 Sharpe_obs=1.0084
  construccion                                    N            V   liston  ¿pasa?
  expediente, N nominal                       12.00   0.00070219   1.3118   False
  N efectivo CN (11 corr.) + portfolio        10.04   0.00070219   1.2672   False
  N efectivo Li-Ji (11 corr.) + portfolio      7.54   0.00070219   1.1915   False
  N efectivo rho-medio (11) + portfolio        3.56   0.00070219   0.9625    True   <--
  N=15 nominal (recuento de esta tarea)       15.00   0.00155037   1.8024   False
  N efectivo CN (14 corr.) + portfolio        13.16   0.00155037   1.7558   False
  N efectivo Li-Ji (14 corr.) + portfolio      9.46   0.00155037   1.6327   False
  N efectivo rho-medio (14) + portfolio        4.71   0.00155037   1.3389   False

  Magnitud frente a las dos que la tarea aplica:
    N efectivo CN (11 corr.)                   -0.0446
    N efectivo Li-Ji (11 corr.)                -0.1203
    N efectivo rho-medio (11)                  -0.3493
    recuento N=15 (en contra)                  +0.4906
```

**Dirección: corregir `N` por correlación BAJA el listón, entre −0.04 y −0.35
según el estimador. Con el más agresivo, Fase B pasa (1.0084 ≥ 0.9625).** Esa
es la corrección contraria que el brief pide, existe, y es lo bastante grande
como para dar la vuelta al veredicto.

**Límite declarado, y es grande:** Cheverud-Nyholt, Li-Ji y la fórmula de
correlación media vienen de la literatura de **tests múltiples correlacionados**,
no de Bailey-LdP. El repo no transcribe ninguna noción de `N` efectivo por
correlación, y el paper no es alcanzable (A-4). **Aplicarlos al `E[max_N]` es
una analogía defendible, no un resultado citable.** Se reporta como cota de
dirección, no como listón alternativo. Decirlo de otro modo sería la doble vara
con la fuente que el hallazgo 6 del segundo agente de N4 castigó.

**Las otras tres correcciones contrarias, que ya están medidas en el expediente
o en esta Fase 0, todas a la baja:**

| Corrección | Efecto sobre el listón | Origen |
|---|---|---|
| Sacar al sujeto de su propia `V` (`N=11`) | 1.3118 → **1.2899** (−0.022) | B-13 de N4; medido en A-5.7 |
| Colapsar el duplicado nº12 = nº9 (`N=10`) | 1.3118 → **1.2634** (−0.048) | B-13 de N4; medido en A-5.7 |
| `V` homogénea sobre el panel (3.0c de N1, H10) | 1.312 → **0.823** (−0.489) | N1, H10. **No es de esta tarea aplicarla** |
| Quitar el ajuste AR(1) del portfolio (ρ=0) | 1.3118 → **1.3082** (−0.004) | B-01 de N4 |

**Y una cuarta que no es numérica y que el brief no hace, a favor del holdout:**

```
=== B-c.1 solape de ventana entre V y el objeto evaluado ===
  ventana de V (OOS Fase A) : 2024-10-06 -> 2026-10-06 (731 velas)
  muestra completa       T= 4406  solape con V =  731 dias =  16.6%
  T3 2023-fin            T= 1378  solape con V =  731 dias =  53.0%
  ventana de V exacta    T=  731  solape con V =  731 dias = 100.0%
```

La `V` del expediente se mide sobre 2024-10 → 2026-10, que está **dentro de
T3**. Medir Fase B en T3 **sube el solape del 16.6 % al 53 %**: la parte de la
heterogeneidad `V`/`T` que H10 señala **mejora** con el holdout. Eso es un
argumento a favor de 6.4 que el brief no hace, y contrapesa parcialmente a B-a:
si alguien defiende 6.4, este es el argumento que tiene, no el del
pre-registro.

**Balance honesto.** Las dos correcciones de la tarea suman **+0.49** de listón
(más un Sharpe que baja 0.44 y un `t` que baja de 3.48 a 1.10). Las contrarias
suman entre **−0.04 y −0.35** dentro de lo que esta tarea puede tocar, y −0.49
si se cuenta H10, que no es suya. **El neto sigue yendo en contra de Fase B,
pero no es el bloque unidireccional que el brief describe, y hay al menos una
construcción documentable en la que Fase B pasa.** El brief, tal como está,
**sí** estaba mal construido en el sentido que él mismo define; con esta
objeción deja de estarlo.

**Qué cambia del Alcance:** 6.3 y 6.5 tienen que tabular también las filas a la
baja, con su límite declarado, o el entregable 6.6 será un informe que solo
encontró pruebas en un sentido.

---

### B-c · No hay test estándar para esta situación, y Fase B no es decidible por DSR con este material — **ALTA**

El brief pregunta si existe un test estándar para deflactar un objeto que no
pertenece a la familia de trials que forma su `V`, y dice que *"no hay test"*
es una respuesta admisible si es la cierta. **Es la cierta, y con una
precisión: no es que falte el test; es que falta la familia.**

Lo que puedo afirmar sin el paper (A-4: SSRN inalcanzable), apoyado solo en la
transcripción del repo y en aritmética:

**(a) `E[max_N]` necesita la dispersión entre los candidatos de los que se
eligió el máximo.** El portfolio de Fase B no se eligió de entre `N` candidatos
de portfolio. Deflactarlo con la dispersión de once reglas single-asset no es
un cálculo mal hecho: es un cálculo que responde a otra pregunta. Eso ya lo
dijo N4 (B-07) y no lo repito.

**(b) La familia sobre el panel no es `N=1`, pero tampoco es enumerable:**

```
=== B-c.3 ¿cuantas curvas de panel hay? ===
  portfolio_equity.csv               4404 dias 2014-09-17 -> 2026-10-07
  portfolio_equity_muertos.csv       4406 dias 2014-09-17 -> 2026-10-09
  portfolio_supervivencia.json: n_activos=15 sharpe=0.916 dsr=0.6014
  Hiperparametros del panel NO pre-registrados (portfolio_runner.py:32-37):
    32: LOOKBACK = 365          35: W_MAX = 0.20
    33: LAMBDA = 0.94           36: GROSS_MAX = 1.0
    34: SIGMA_TARGET = 0.10     37: VOL_TOPE_MULT = 1.25
```

Dos curvas de panel enumerables (10 activos y 15), seis hiperparámetros sin
pre-registro y la elección del universo de 10 sin rastro de cuántas
combinaciones se probaron.

**(c) Y aquí está lo que decide la objeción.** El veredicto cambia de signo
dentro del rango de incertidumbre:

```
  N=1   liston 0.4723   Fase B PASA
  N=2   liston 0.7336   Fase B PASA
  N=3   liston 0.9014   Fase B NO PASA
```

**Entre `N=2` y `N=3` se invierte el dictamen, y nadie puede decir cuál es.**
No es que el test dé un resultado incómodo: es que el test no tiene entrada
determinable. Con `N` indeterminado entre 2 y 3 —el rango que la familia del
panel admite— el DSR no distingue "pasa" de "no pasa".

**(d) Y la ventana homogénea, que sería la construcción coherente por el lado
de `T`, es la peor de todas:**

```
  ventana                      T  T_eff    Sh_an      t  lis_N12  lis_N15   lis_t3
  ventana de V exacta        731    666   0.2798   0.38   2.1080   2.6126   2.2209
```

**Cuidado con la etiqueta "`T` homogéneo", que significa dos cosas opuestas.**
La de N1 (3.0c) homogeneíza midiendo **`V` sobre el panel** y baja el listón a
0.823. Ésta homogeneíza **recortando `T` a la ventana de `V`** y lo sube a
2.108, con un Sharpe de 0.280. Confundirlas en 6.5 sería un error de bulto, y
el nombre invita a cometerlo. Ver B-e6.

**Respuesta a B-c:** **no hay test estándar, y Fase B no es decidible por DSR
con este material.** Lo que sí es decidible —y ya está decidido, con criterio
pre-registrado y antes del resultado— es la métrica de los IC95 por tramo, que
dio SUPERADO. Y `t>3` da respuestas distintas según la ventana (pasa en la
completa, no en T3), y la elección de ventana es lo que B-a dice que no se
puede hacer hoy.

**Qué cambia del Alcance:** 6.5 puede escribirse tal como está, y su respuesta
previsible es la quinta opción que el propio brief contempla: **ninguno**. Y
entonces 6.6 cierra el expediente diciendo que **Fase B es indecidible con este
material, no débil** — que es, literalmente, lo que el brief dice que se
escribiría *"tal cual"* si saliese. Sale.

---

### B-d · Esta tarea no sube `N` de estrategias, pero 6.3 es una máquina de metric-shopping — **MEDIA**

**No sube `N`.** Recalcular el listón sobre los mismos trials, reproducir T3 y
enumerar tests no introduce ninguna regla nueva, no mide ningún PnL nuevo y no
hay ningún resultado que pudiera "salir bien". La Fase 0 de esta tarea ha
reejecutado las 14 estrategias por el pipeline congelado para medir `V` —eso es
cálculo de métrica, no búsqueda— y ha re-simulado el panel con un sello de
datos ya congelado. **Ninguna de las dos cosas es un intento.** Confirmado,
igual que N4 (B-08) concluyó para sus pasos de análisis.

**Pero sí sube el otro contador, el que el expediente no lleva.** N4 (B-08)
estableció que existe un "`N` de construcciones de métrica probadas" y que iba
por 3 (la del expediente, la de 3.0c de N1, el reescalado de N2). Esta Fase 0
añade al menos **dos**: el `N` efectivo por correlación (B-b, tres estimadores)
y la ventana homogénea en el tiempo (B-c.d). **Van por 5, y ninguna está
registrada en ningún sitio.**

**Y hay un problema estructural en 6.3 que el brief no ve.** 6.3 pide
*"tabla con y sin `mean_reversion`"*. A-5 y §2.2 miden lo que eso significa: con
el outlier el listón es 1.8024, sin él 1.3658. **Ofrecer las dos filas después
de conocer el resultado es el menú; que lo elija Pablo y no el agente no lo
convierte en otra cosa.** El brief se protege diciendo que 6.6 *"no lleva
recomendación"* y que *"la elección es de Pablo"*, pero eso traslada el
metric-shopping, no lo elimina — es exactamente el agravante que N4 (B-04) le
puso a su propio paso 4.3.

**Qué cambia del Alcance:** 6.3 no puede presentarse como un menú. Tiene que
presentarse como una **cota con su regla de lectura escrita antes**: o el
outlier entra siempre (y el listón es 1.80), o nunca (y es 1.37), con el
criterio dicho en 6.2 —la regla prospectiva— **y aplicado hacia atrás sin
excepciones**. Si la regla de 6.2 no determina qué hacer con `mean_reversion`,
6.2 está mal escrita y 6.3 no se puede emitir. Y `registro_N.md` necesita la
segunda columna de N4: construcciones de métrica probadas, que empieza en 5, no
en 0.

---

### B-e1 · El NO-GO de 6.4 se dispararía en falso: T3 no reproduce desde el fichero congelado del repo — **ALTA**

El brief escribe como NO-GO del Alcance: *"Si 6.4 no reproduce el tramo T3
publicado → parar en 6.4 y reportar."* A-3 mide qué pasa si se intenta de la
forma obvia —cortar `results/portfolio_equity.csv` por fecha—: **T3 no
reproduce** (0.573 vs 0.572, DSR 0.3013 vs 0.3008, `n_obs_eff` 1354 vs 1356, IC
[−5.82, +20.35] vs [−5.86, +20.30]).

La causa es trivial y está declarada en el propio documento de dictamen
(`fase_b_reevaluacion_resultado.md:8`): la equity congelada es del run
`20261007` y el walk-forward publicado del `20261009`, +2 velas. T1 y T2 no se
enteran; T3 sí, porque es *"2023-01-01 → fin datos"*. Re-simulando con el sello
correcto reproduce campo a campo.

**Esto no es un detalle de ejecución: es el paso 6.4 entero.** Un 6.4 escrito
sin saberlo o bien para en falso, o bien publica 0.573 como "el Sharpe de Fase
B en el holdout" y no cuadra con el único documento de dictamen del expediente.
Y la diferencia entra justo en la cifra que la tarea quiere poner delante de
Pablo.

**Qué cambia del Alcance:** 6.4, si se ejecuta, tiene que declarar el sello
(`STAMP_CONGELADO=20261009`), re-simular en vez de leer el CSV, y pegar la
comprobación de que las dos curvas coinciden a 8.9e-16 en las fechas comunes.
Y 6.6 tiene que decir qué vintage usa cada número que pone en la misma tabla:
el 1.008 publicado es del `20261007`, el 0.572 publicado es del `20261009`.
Medido, el efecto de mezclarlos es despreciable (el Sharpe completo con
`20261009` es 1.0082 y `T_eff` 4338), pero **"despreciable" es una conclusión,
no una excusa para no decirlo.**

---

### B-e2 · El brief tiene dos numeraciones incompatibles y el OK de la §7 sería ambiguo — **ALTA**

La §3 (B-a) dice *"el **paso 4.2** sobra"*; el NO-GO de la Fase 0 dice *"Si B-a
concluye … **el paso 4.2**"*. Pero **la §4 no tiene ningún paso 4.2**: su tabla
está numerada **6.1 … 6.6**, y el NO-GO del Alcance y los entregables también
hablan de 6.1, 6.4, 6.5. El paso del que B-a habla —medir en el holdout— es
**6.4**, no 4.2. Y la §7, donde Pablo firma, dice *"OK para ejecutar el
Alcance"* sin enumerar qué pasos autoriza.

Es un resto del brief de N4, cuyo Alcance sí iba de 4.1 a 4.6. No es cosmético:
**un OK firmado sobre la §7 autorizaría una §4 cuyas referencias internas
apuntan a pasos que no existen**, y la objeción que el propio brief declara
decisiva (B-a) nombra un paso inexistente. En un expediente cuya tesis es que
el otro lleva mal las cuentas, esto tiene coste.

**Qué cambia del Alcance:** antes de cualquier firma, renumerar la §4 a 4.1–4.6
o reescribir B-a y los NO-GO en 6.x, y que la §7 enumere los pasos que el OK
cubre. Esta Fase 0 usa **6.x**, que es la numeración de la tabla, y lo dice
cada vez que nombra un paso.

---

### B-e3 · El recuento de `N`, medido, es casi vacío sin el outlier: el 89 % del efecto es un trial — **ALTA**

La §1 del brief presenta dos correcciones como el contenido de la tarea. La
primera, medida (§2.2):

```
  N=12, expediente                       liston 1.3118   +0.0000
  N=15, con las 3                        liston 1.8024   +0.4906
  N=14, con las 3 SIN mean_reversion     liston 1.3658   +0.0540
  Fraccion del efecto que aporta mean_reversion: 89.0%
```

**Sin `mean_reversion`, cerrar el recuento de `N` mueve el listón +0.054.** Eso
es un noveno de lo que mueve H10 (±0.49) y menos que la propia incertidumbre
entre las construcciones de `V` que el expediente tiene abiertas. La corrección
existe —las tres estrategias se corrieron y se publicaron, eso no se discute—
pero **su magnitud entera cuelga de un trial a 4.24 sd**, y mantenerlo o no es
una decisión que se toma hoy, viendo el resultado. B-d explica por qué eso es
un problema.

Y hay un detalle que lo agrava y que no está en ningún sitio: **añadir solo
`mean_reversion` (`N=13`) da un listón de 1.8251, MÁS ALTO que añadir las
tres** (1.8024), porque `breakout` y `trend_following` están cerca de la media
y diluyen `V`. O sea que el listón no es monótono en `N`, y "cerrar el
recuento" puede subirlo o bajarlo según a quién se incluya. Eso le quita a 6.1
la propiedad que lo justificaba: que contar bien da un número, no un rango.

**Qué cambia del Alcance:** la §1 no puede seguir diciendo que `N` mal contado
es una de las dos cosas que importan sin la cifra al lado. Con la cifra, lo que
importa es **una** cosa (el holdout) y media.

---

### B-e4 · Los once `walkforward_stability_*` salen de `yf.download`, y dicen que `ma_cross` es frágil — **MEDIA**

A-1 lo encuentra y no está en ningún documento del expediente. Los once
ficheros que el brief llama "material no auditado" se produjeron con
`yf.download("BTC-USD", period="5y")` (`walkforward_stability.py:42`), no con
el CSV congelado. `period="5y"` se resuelve contra la fecha de ejecución, que
no está registrada. **No son reproducibles sin red, y no hay red.**

Lo que dicen: **diez de once `fragil`, una `estable`** (`connors_rsi2`). Entre
las frágiles, **`ma_cross`**, que es la que el expediente trató como ganadora
de Fase A y la que alimenta `paper_runner.py`. El propio docstring dice que el
dictamen *"lo consume `paper_runner.py` (modo observacion si fragil)"*.

**No cambia ningún veredicto** —Fase A murió por DSR, bootstrap y `t` de forma
independiente— y por eso es MEDIA y no ALTA. Pero es material publicado,
citado, no reproducible y nunca auditado, y la tarea que lo inventaría debería
etiquetarlo como tal en `registro_N.md` en vez de dejarlo fuera porque "no es
un trial".

**Qué cambia del Alcance:** 6.1 tiene que listarlos con la etiqueta **no
auditable por vintage de datos**, que es el tipo de honestidad que el NO-GO del
propio Alcance pide (*"se escribe como no auditable con esa etiqueta; no
inventar una procedencia plausible"*).

---

### B-e5 · La §2.5 afirma "con `N ≤ 3`" y el cruce está en `N = 2` — **MEDIA**

Medido en A-5.6: el listón del DSR supera al de `t>3` ya en `N = 3` (0.9014
contra 0.8704). La afirmación del brief es correcta para `N ≤ 2` y falsa para
`N = 3`.

Importa porque B-c muestra que **el veredicto de Fase B se invierte exactamente
ahí**: pasa con `N = 2`, no pasa con `N = 3`. Una tarea que fuese a apoyarse en
"con `N` bajo manda `t>3` = 0.870" estaría usando un umbral que no aplica justo
en el punto donde se decide.

**Qué cambia del Alcance:** 6.5, al enumerar `t > 3` como test, tiene que decir
que su umbral depende de `T_eff` (0.870 en muestra completa, **1.557 en T3**) y
que solo es la restricción activa para `N ≤ 2`.

---

### B-e6 · "`T` homogéneo" nombra dos construcciones opuestas, y 6.5 va a confundirlas — **MEDIA**

H10 de N1 dice que el listón pasa de 1.312 a **0.823** *"si `V` se mide con `T`
homogéneo sobre el panel"*. Eso homogeneíza **subiendo `V` al universo del
objeto**. La otra lectura natural de la misma frase —homogeneizar **bajando
`T` a la ventana de `V`**— da lo contrario:

```
  ventana de V exacta   T=731  T_eff=666  Sharpe 0.2798  t 0.38  liston_N12 2.1080
```

**Una baja el listón 0.49; la otra lo sube 0.80, y hunde el Sharpe a 0.28.** Las
dos se pueden describir con las mismas cuatro palabras. 6.5 pide enumerar tests
*"con su umbral y qué asunción exige cada uno"*, y si una fila se llama "DSR con
`T` homogéneo" sin decir cuál de las dos, la tabla será ilegible o engañosa.

**Qué cambia del Alcance:** 6.5 tiene que nombrarlas por lo que hacen —*"`V`
remedida sobre el panel"* y *"`T` recortado a la ventana de `V`"*— y no usar
"homogéneo" a secas. Y 6.6 tiene que decir que la segunda es la peor fila de
todo el expediente para Fase B, igual que N4 tuvo que declarar que su "fila
dominante" era la mejor.

---

### Lo que NO se encontró, declarado

- **Ningún error aritmético en lo que esta tarea usa como eje.** `V(11)`,
  `V(12)`, `V(15)`, `T_eff`, skew, curtosis, el Sharpe del portfolio, el listón
  1.3118, el 1.8024 y los tres tramos T1/T2/T3 —con sus DSR, sus `t` y sus IC
  de bootstrap— reproducen todos con implementación independiente. Los dos
  primeros con diferencia **0.0e+00**.
- **Ninguna contradicción entre los dos árboles** (A-2). El NO-GO más duro del
  brief no se materializa.
- **Ninguna manipulación.** Las dos `V` siguen correctamente emparejadas con
  sus `N`, y el defecto de recuento es una omisión fechada antes de que
  existiese Fase B, igual que concluyó N4.
- **Ninguna objeción a la pregunta de la §1.** Que el test está mal aplicado y
  que `N` está mal contado es cierto. Lo que no sobrevive es el valor que 6.4
  puede añadir, y la magnitud que 6.1/6.3 pueden mover.
- **Nada que invalide el trabajo de N4.** Sus dos afirmaciones centrales
  (`V` se dobla, listón 1.8024; el sujeto está dentro de su propia `V` con un
  duplicado) se reverifican y salen. La única cifra suya que no sale es el
  "~3.5 sd" del outlier, que está subestimado.

---

## Veredicto de la Fase 0 y NO-GO

| NO-GO de la §3 | Estado |
|---|---|
| *Sin intérprete usable → PARAR* | **No se dispara.** Python 3.13.18 + numpy/pandas; nada del expediente necesita más (A-4) |
| *Si A-2 encuentra que los dos árboles se contradicen → PARAR* | **No se dispara.** Ningún fichero homónimo difiere, al byte ni semánticamente (A-2) |
| *Si A-3 no reproduce los tres tramos → PARAR* | **No se dispara.** Los tres reproducen campo a campo con el sello `20261009`. Desde el fichero congelado T3 no reproduce, y eso es **B-e1**, no el NO-GO |
| *Si B-a concluye que medir con holdout ahora **es** cambiar el test después del resultado → PARAR* | **Se dispara sobre el paso 6.4, no sobre la tarea.** Medir y reportar T3 es legítimo; compararlo contra un listón es un criterio elegido hoy. Ver B-a |
| *Si algo de la §2 sale REFUTADO → PARAR* | **Se dispara parcialmente, por §2.5**, cuya afirmación *"con `N ≤ 3` manda `t>3`"* es falsa en `N = 3`. Lo puntúo **MEDIA** (B-e5) y **no acciono el freno con él**: el encabezado de la §2.5 es cierto, sus dos cifras (0.870 y 0.472) salen exactas, y los `T` mínimos de N5 reverifican. Accionar el NO-GO más duro con una objeción MEDIA es la desproporción que el segundo agente de N4 castigó en su hallazgo 8 |

**La parada se sostiene en B-a y B-b, que es donde está el motivo real**, y no
en los frenos formales.

**Lo que esta Fase 0 deja establecido, sin gastar el Alcance:**

1. **El eje de la tarea es correcto al bit.** `V(15) = 0.001550366`, listón
   **1.8024**, `V(12)` con diferencia 0.0e+00. N4 no se equivocó aquí.
2. **`N` no pasa de 15.** El inventario de los trece ficheros está hecho
   (A-1) y ninguno añade una configuración de estrategia. Los once
   `walkforward_stability*` reejecutan las mismas once de `V(11)` —y con datos
   de vintage desconocido, que es hallazgo nuevo.
3. **Los tres tramos reproducen**, campo a campo, IC de bootstrap incluidos,
   con el sello `20261009`. El dictamen pre-registrado de los IC95 (SUPERADO)
   también reproduce.
4. **Medir en el holdout va en contra de Fase B por los dos lados a la vez**:
   el Sharpe baja de 1.008 a 0.572 **y el listón sube** de 1.3117 a 1.7007,
   porque la PSR va con `√(T−1)`. El de `t>3` sube de 0.870 a 1.557. Fase B
   pasa `t>3` en la muestra completa y no en T3. El brief subestimaba esto.
5. **El recuento de `N`, medido, es casi vacío sin el outlier**: 89 % del
   efecto es `mean_reversion`, y sin él el listón se mueve +0.054. El listón
   además **no es monótono en `N`** (añadir solo `mean_reversion` da 1.8251,
   más que añadir las tres).
6. **Existe corrección contraria y está medida**: corregir `N` por correlación
   entre trials baja el listón entre 0.04 y 0.35, y en una construcción
   **Fase B pasa** (1.0084 ≥ 0.9625). Con su límite declarado: es analogía de
   la literatura de tests múltiples, no de Bailey-LdP.
7. **No hay test que decida Fase B con este material.** El veredicto se
   invierte entre `N = 2` y `N = 3`, y la familia sobre el panel no es
   enumerable. La respuesta honesta a B-c es la quinta opción del propio brief:
   **ninguno**. Fase B quedaría **indecidible, no débil**.
8. **El pre-registro de los tramos no es auditable por git.** Diseño, código,
   resultados y equity llegan en el mismo commit `d34b147`. Mismo estatus
   probatorio que la cadena `N = 11 → 12 → 14` que N4 declaró NO VERIFICABLE.

**Lo que hace falta antes de cualquier OK:**

- **Borrar o reescribir 6.4.** Su mitad de medición ya está hecha arriba; su
  mitad de comparación es el test elegido a posteriori (B-a).
- **Renumerar la §4**, o reescribir B-a y los NO-GO, y que la §7 enumere qué
  pasos cubre el OK (B-e2).
- **Reescribir 6.3** como cota con regla de lectura, no como menú (B-d), y que
  6.2 determine qué hacer con `mean_reversion` **antes** de que 6.3 se emita.
- **Añadir a 6.3/6.5 las filas a la baja** medidas en B-b, con su límite
  declarado, o el informe solo tendrá pruebas en un sentido.
- **Separar las dos "`T` homogéneo"** en 6.5 (B-e6).

**Con eso, lo que queda del Alcance es 6.1, 6.2, 6.5 y 6.6**, que es trabajo
real y que esta Fase 0 no ha hecho: el libro de cuentas de `N`, la regla
prospectiva, la enumeración de tests y el informe. 6.3 necesita reescritura y
6.4 sobra.

**No se ha ejecutado ni un paso de la §4. La §7 sigue sin firma.**
