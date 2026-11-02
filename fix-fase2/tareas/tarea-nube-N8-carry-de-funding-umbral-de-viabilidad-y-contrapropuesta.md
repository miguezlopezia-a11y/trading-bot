# Tarea N8 (nube) — CANCELADA. Reemplazada por N9 (VPS)

> ## ⛔ NO EJECUTAR. Esta tarea está cancelada desde el 2026-11-02 20:56.
>
> **Reemplazada por**
> `fix-fase2/tareas/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md`
> (commit `0f77f9e`), que cubre lo mismo y más, **en el VPS**.
>
> **Por qué se canceló, dicho sin adornos:** este brief se escribió para la nube,
> y la nube **no tiene red** para datos de mercado (medido dos veces: N5 · A-1 y
> N7 · A-7, 0 de 10 fuentes). Así que N8 solo podía entregar una fórmula y una
> tabla de sensibilidad — **otro documento**, cuando lo que hace falta es la
> cuenta con datos reales. Se eligió la nube porque había crédito caducando el
> 05-nov, no porque fuera el sitio correcto. Es un error de quien lo escribió, y
> es el mismo que Pablo ya había señalado ese día.
>
> **N9 hace lo que esto no podía:** corre en el VPS, donde las tres APIs de
> funding (Binance, Bybit, OKX) responden **200 sin credenciales** —verificado
> por SSH el 2026-11-02 a las 18:40—, hay **7,1 años** de histórico, y entrega
> **euros al año** más la especificación del bot. Conserva íntegro lo único
> valioso de este brief: el **Paso C de contrapropuesta obligatoria**, y las tres
> cosas que N5 · B-c ya había refutado y no hay que volver a afirmar.
>
> **Nunca se ejecutó:** §7 entera en `[pendiente]`, sin registro némesis, sin
> rama `nube/n8-carry-funding`, cero código y cero datos. Lo detectó el **Paso
> A-3 de N9**, que es justo la comprobación que este expediente añadió tras el
> fallo de N7 — y cazó un duplicado creado 14 minutos antes. Funcionó.
>
> Se conserva, en vez de borrarse, porque el historial de por qué esto pasó de
> la nube al VPS es parte del expediente.

**Repo:** `miguezlopezia-a11y/trading-bot` · **Rama base:** `fase-b-recuperada`
**Rama de trabajo:** `nube/n8-carry-funding` · **PR contra:** `fase-b-recuperada`, nunca contra `main`
**Autor del brief:** sesión de escritorio, 2026-11-02 18:11 · **Estado:** parada en Fase 0
**Timeout de la Fase 0:** 30 min de reloj, repartidos: A ≤ 8, B ≤ 8, **C ≤ 10**, Maker/Verifier ≤ 4.

## Esta tarea es distinta a las siete anteriores

Las siete tareas previas (S1-S3, N4-N7) auditaban un expediente ya escrito.
Una auditoría solo puede decir **no**: encuentra defectos, no encuentra negocio.
Siete archivos después, el expediente está mejor medido y sigue sin dar un euro.

Esta tarea no audita. **Propone**, y su Fase 0 tiene un paso que las anteriores
no tenían: el **Paso C**, donde la nube, si desarma la propuesta, está obligada a
devolver la suya. Un *"esto no funciona"* sin alternativa es una entrega
incompleta y se rechaza.

## Lecturas previas obligatorias, enteras y en este orden

1. `fix-fase2/tareas/tarea-nube-S2-investigacion-literatura-cripto.md` en
   `nube/s2-literatura` — **el registro némesis completo**. Su §3.2 ya nombró
   el carry de funding como *"la familia que mejor encaja con un expediente que
   ya demostró no poder predecir dirección"*, y su objeción **B6 (ALTO)**
   explica por qué quedó bloqueada. Esta tarea desbloquea eso.
2. `fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md`
   en `nube/n5-reconocimiento-datos` — **la objeción B-c entera**. Refutó la
   versión ingenua de esta misma idea. Si vuelves a cometer su error, la tarea
   no vale nada.
3. `fix-fase2/tareas/tarea-nube-N7-benchmark-de-exposicion-igualada.md` en
   `nube/n7-benchmark-exposicion` — el **resumen ejecutivo y B-c**. N7 pidió
   trabajo que ya estaba hecho y publicado el día antes. Es el error a no
   repetir: **antes de proponer medir algo, busca si ya está medido.**
4. `fix-fase2/src/rigor_estadistico.py` — es la infraestructura que esta tarea
   reutiliza, no reimplementa.

---

## 1. La pregunta

El objetivo del proyecto es **ganar dinero**. No hace falta volver a
preguntarlo.

Siete archivos han apostado a lo mismo: **predecir la dirección del precio** con
velas diarias y OHLCV. El veredicto acumulado es inequívoco —ninguna de las once
variantes de Fase A tiene significancia, y Fase B pierde contra comprar y
aguantar a igual exposición por 0.063 de Sharpe (N7)—, y era previsible: es el
espacio más explorado del mercado, con los datos que tiene todo el mundo.

La pregunta de esta tarea es la primera que no es predictiva:

> **¿Cuánto tiene que pagar el funding de los perpetuos, neto de costes, para
> que un carry delta-neutral supere el listón que este expediente ya tiene
> fijado? ¿Y está ese número al alcance de lo que el funding ha pagado
> históricamente?**

Un perpetuo paga funding cada 8 horas de los longs a los shorts (o al revés).
Si estás corto en el perp y largo en el spot por el mismo nominal, el precio es
irrelevante: el P&L es el funding cobrado menos los costes. **No es una señal,
es una tarifa.**

**Lo que esta tarea NO afirma, porque ya está refutado** (N5 · B-c, severidad
ALTO, y hay que leerlo antes de escribir una línea):

- **"No depende de predecir" no baja ningún listón.** `sharpe_min_dsr` no tiene
  ningún argumento sobre la naturaleza de la hipótesis. El umbral lo fijan `N`,
  `T_eff`, *skew* y curtosis. Nada más.
- **Las colas del carry lo SUBEN.** El carry tiene vol baja y curtosis alta con
  cola izquierda (se cobra durante años y se devuelve en un desapalancamiento).
  En el denominador de la PSR, curtosis 150-400 con *skew* negativo sube el
  listón: N5 midió 0.4723 → 0.4993 al pasar de kurt 32 a kurt 400 con skew −1.
- **El carry no se backtestea con OHLCV diario.** Exige la serie de funding, que
  no está en el repo (verificado en 2.1).

**Entonces, qué ventaja real tiene, si no es el listón.** Una sola, y es
cuantitativa: **`T`**. El funding se liquida cada 8 horas, así que una serie de
la misma historia de calendario tiene **3 observaciones por día en vez de 1**, y
el listón baja con `T`. S2 ya lo señaló (*"T potencialmente 24× mayor si se mide
por hora"*). Esa es la única palanca, y **esta tarea existe para medir si
alcanza**, sabiendo que las colas tiran en contra.

---

## 2. Hechos verificados desde el escritorio

Reverificar los cinco con comandos propios. Cada bloque lleva el comando que lo
produjo. Rutas **desde la raíz del repo**, salvo donde se diga `fix-fase2/`.

### 2.1 No hay nada de funding, perpetuos, basis ni carry en este repo

```
$ git grep -l -i -E "funding|perpetu|perp_|basis|carry|delta.neutral|futures" fase-b-recuperada
fase-b-recuperada:fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md
fase-b-recuperada:fix-fase2/tareas/tarea-nube-N6-holdout-recuento-de-N-y-que-test-aplica.md
fase-b-recuperada:fix-fase2/tareas/tarea-nube-S2-investigacion-literatura-cripto.md
$ git ls-tree -r --name-only fase-b-recuperada | grep -i -E "funding|perp|basis|carry|futur"
(sin salida)
```

Tres archivos de tarea lo mencionan; **ni una línea de código, ni un fichero de
datos.** Esta comprobación es la que N7 no hizo y le costó la tarea: si tu
reverificación encuentra código de funding en algún sitio, **PARA** y repórtalo,
porque entonces esta tarea también está pidiendo trabajo ya hecho.

### 2.2 S2 ya lo propuso, y lo que lo bloqueó fue administrativo, no empírico

S2 · §3.2, literal:

> **Carry / funding rate / basis** en futuros perpetuos: es una fuente de
> retorno estructural, medible, con mecanismo económico identificable, y no
> depende de predecir el precio. Evaluar con atención: es la familia que
> mejor encaja con un expediente que ya demostró no poder predecir dirección.

Y su objeción **B6 (ALTO)** encontró que el propio brief de S2 se lo prohibía en
la §3.6 (*"no proponer nada que exija dinero real, broker o API con
credenciales"*), con esta salida:

> separar *investigar el mecanismo con datos históricos públicos de funding*
> (que no exige dinero ni credenciales, si esos datos son descargables sin
> clave — **[no verificado]**)

**Ese `[no verificado]` sigue sin verificar, y es el primer NO-GO de esta tarea.**

### 2.3 El listón de arranque NO es `N = 1`. Es `N ≥ 16`

S2, en su némesis, cerró por escrito la tentación que esta tarea tendría:

> alguien argumentará que una candidata sobre un universo de datos nuevo
> (funding rates, on-chain) es "trial 1 sobre un panel nuevo" y le corresponde
> el listón de 0.472, no 1.331. **Eso es falso y es el agujero por el que se
> escapa todo el rigor del expediente.** El sesgo de selección múltiple vive en
> el decisor, no en el dataset: si Pablo ha mirado 12 ideas y reportaría la que
> funcione, N=13 al probar la 13ª, venga de donde vengan los datos.

Regla de S2: **`N = N_vigente + 1`**. Con el recuento de N6 (`N ≥ 15`,
posiblemente 19), el carry arranca en **`N ≥ 16`**. Lo que sí cambia con el
universo nuevo es **`V`**, y hay que reestimarla, no resetearla.

### 2.4 Y con `N` alto, el DSR puede no ser la restricción activa

N5 · B-e3 (ALTO) estableció que con `N` bajo la restricción es `t > 3`, que **no
se reinicia** nunca. La criba debe usar el **máximo** de los dos listones, no el
que convenga. Para el carry, con `T` grande, el reparto entre los dos cambia:
**medirlo es parte del Alcance, no asumirlo.**

### 2.5 La nube no puede bajar los datos. El VPS sí

N5 · A-1 y N7 · A-7 lo midieron dos veces: **0 de 10 fuentes de mercado
alcanzables** desde el contenedor, y FRED tampoco. Es lista blanca de red, no
incidencia.

**Consecuencia de diseño, y es el eje de esta tarea:** la nube **no** va a traer
una sola cifra de funding. Lo que sí puede hacer, y es lo que se le pide, es
**matemáticas y crítica**: calcular el umbral de viabilidad de forma analítica,
decir exactamente qué serie hay que bajar en el VPS y con qué formato, y
proponer algo mejor si lo ve. Los datos son un paso posterior, en el VPS, y no
es esta tarea.

---

## 3. Fase 0 (OBLIGATORIA). Tres pasos, no dos

Scripts en **`fix-fase2/fase0_n8/`**. Nunca en `src/` ni en `auditoria_n8/`.
Cada cifra con su comando; una cifra sin script detrás es una cifra inventada, y
en N7 el Maker/Verifier encontró tres bloques de salida **fabricados**.

### Paso A — Verificación de hechos (≤ 8 min)

- **A-1.** Reverificar los cinco bloques de la §2 con veredicto **CONFIRMADO /
  CONFIRMADO con corrección / REFUTADO** y la salida pegada.
- **A-2.** Confirmar que `rigor_estadistico.py` expone `dsr`,
  `block_bootstrap_ci`, `ar1_effective_n` y `PPY`, y que son importables sin
  tocar red. Si algún import descarga datos, reportarlo sin parchearlo.
- **A-3.** Fijar `N_vigente` **leyéndolo** de los registros de N4 y N6, no de
  este brief, y dejar escrito el `N` de arranque del carry con su procedencia.
- **A-4.** Intérprete, numpy, pandas, y reconfirmar la red (§2.5). Basta
  reportar; no hay que repetir el barrido de diez fuentes de N5.

### Paso B — Ataque adversarial (≤ 8 min)

**Mínimo cinco objeciones con severidad (CRÍTICA / ALTA / MEDIA / BAJA) y qué
cambia del Alcance.** Una objeción que al medirla resulta falsa se retira por
escrito, diciendo que era del revisor.

Tres obligatorias, porque son donde esta propuesta se rompe si está mal:

- **B-a (obligatoria).** El `T` del carry. El brief dice que 3 observaciones
  diarias bajan el listón. **Mídelo contra las colas**: con los momentos
  plausibles de un carry (vol baja, *skew* negativo, curtosis 150-400 según
  N5 · B-c) y `N ≥ 16`, ¿el listón resultante es **más alto o más bajo** que el
  1.8024 de Fase B? Si sale más alto, **la única palanca de esta tarea no
  existe y hay que decirlo en la primera línea del registro.** Y ojo con el
  AR(1): el funding está autocorrelacionado por construcción (los regímenes de
  funding duran días), así que `ar1_effective_n` puede **destruir** la ganancia
  de `T` que el brief presume. Mide `T_eff`, no `T`.

- **B-b (obligatoria).** La cola izquierda. El carry delta-neutral no quiebra
  por el precio, quiebra por **liquidación de la pata corta** en un
  desapalancamiento, por **desanclaje** entre perp y spot, y por el exchange
  (rehipotecación, cambio de reglas, retiradas congeladas). Esos riesgos **no
  están en el Sharpe** y por tanto no están en el listón. ¿Es el DSR el test
  adecuado para una estrategia cuyo modo de muerte es un salto único y total?
  Si la respuesta es que no, **dilo**, y di qué métrica lo captura.

- **B-c (obligatoria).** Busca activamente el argumento de que esto **tampoco**
  vale. Dos candidatos que te doy: (i) el carry de funding es la operación más
  conocida del mercado cripto y lleva años comprimido por capital institucional
  — si paga poco, la cuenta no cierra ni con `T` infinito; (ii) capturarlo
  exige cuenta en un exchange de derivados, lo que mete riesgo de contraparte
  que ninguna estadística mide. Y uno más que busques tú.

Y al menos dos de cosecha propia.

### Paso C — Contrapropuesta (≤ 10 min) — ESTE PASO ES NUEVO Y ES OBLIGATORIO

Lo pide Pablo explícitamente: **desarma esta propuesta si puedes, y devuelve la
tuya.**

Un registro que concluye *"el carry tampoco funciona"* **y se queda ahí** está
incompleto y se rechaza. Si el Paso B tumba la propuesta, el Paso C tiene que
decir qué se hace en su lugar.

**Formato obligatorio.** Entre **una y tres** candidatas, cada una con:

| Campo | Qué tiene que decir |
|---|---|
| Mecanismo | **Por qué** debería pagar, en una frase económica. Una regla sin mecanismo es una regla que no se sabe por qué funcionaría (S2 · §3.2) |
| Predictiva o no | Si exige pronosticar dirección, va al final de la lista y dice por qué merece excepción tras siete fracasos |
| Datos | La serie exacta, el proveedor, y **si se descarga sin clave** |
| `N` que le toca | Por la regla de S2 (`N_vigente + 1`), con el número puesto |
| Listón estimado | Con `sharpe_min_dsr` y los momentos **de esa candidata**, y el `max` con `t>3` |
| Qué la mata rápido | **La comprobación más barata que la descarta**, y cuánto cuesta en horas |
| Por qué es mejor que el carry | La comparación explícita |

**Reglas del Paso C, no negociables:**

1. **Nada que exija dinero real, credenciales ni operar en vivo** en la fase de
   investigación. Datos históricos públicos, sí.
2. **Ninguna candidata se evalúa aquí.** Proponer no es backtestear. En el
   momento en que midas el Sharpe de una señal, consumes un trial y subes `N`
   para todo el expediente (S2). **Esta Fase 0 no evalúa nada.**
3. **Ordenadas por "qué la mata rápido"**, de más barata a más cara. El
   criterio de ordenación **no** es el retorno esperado: es el coste de
   descartarla.
4. Si no encuentras ninguna mejor que el carry, **dilo y defiende el carry**.
   Decir *"no hay nada"* sin haber mirado no es una respuesta; decir *"el carry
   sigue siendo la mejor de las malas"* con argumento, sí.

### Maker/Verifier

Al cerrar el Paso C, invocar un segundo agente que **solo critique este
registro**. En N4 encontró dos CRÍTICOS, en N6 trece hallazgos con uno CRÍTICO
que invertía el veredicto, en N7 **veinte con cinco CRÍTICOS, tres de ellos
bloques de salida fabricados**.

Darle el registro y el brief, nada más. Pegar su crítica **literal**, responder
hallazgo por hallazgo **reverificando con comandos propios**, y aplicar las
correcciones en el documento **y en los scripts**.

**Y una instrucción específica para él:** que juzgue el Paso C con la misma dureza
que el Paso B. Una contrapropuesta mal fundada es peor que ninguna, porque
arrastra otro mes de trabajo.

### NO-GO de la Fase 0

Cada uno **binario**. A N6 se le reprochó graduar frenos que el brief escribió
sin grados, y a N7 declarar disparado lo que su propio JSON decía que no. **Ni
una cosa ni la otra.**

| Condición | Acción |
|---|---|
| A-1 encuentra código o datos de funding ya en el repo | **PARAR**: la tarea pide trabajo hecho (el error de N7) |
| Algún hecho de la §2 sale REFUTADO | **PARAR** |
| B-a concluye que el listón del carry es **más alto** que el de Fase B | **No parar**: es el resultado. Se dice en la primera línea y el Paso C pasa a ser el contenido principal |
| No hay intérprete con numpy/pandas | **PARAR** |
| El Paso C no produce ni una candidata, ni defiende el carry | **ENTREGA INCOMPLETA**: no se cierra el registro |

---

## 4. Alcance (NO EJECUTAR sin OK escrito de Pablo en la §7)

El OK enumerará los pasos que cubre. Un OK sin lista no autoriza nada.

- **4.1 El umbral de viabilidad, analítico.** La función que, dados `N`,
  `T_eff`, *skew*, curtosis y los costes, devuelve **el funding medio por
  periodo de 8 h que hace falta** para superar `max(listón DSR, listón t>3)`.
  Entrada de costes: comisión *taker* y *maker* de las dos patas, y el coste de
  mantener el margen. **Sin ningún dato de mercado**: es una fórmula, y su
  entrega es una tabla de sensibilidad.
- **4.2 La tabla.** El umbral de 4.1 barrido sobre: `N ∈ {16, 20, 30}`,
  curtosis `∈ {30, 150, 400}`, *skew* `∈ {0, −1, −3}`, y `T` de 1, 2 y 5 años
  de historia a 3 observaciones diarias, **con y sin** el ajuste AR(1).
- **4.3 La especificación de datos para el VPS.** Qué serie exacta, de qué
  proveedor, con qué granularidad y qué campos, con el protocolo de congelado
  del repo (`sha256` + `.meta.json`, como `data/multi/`). Un documento que otro
  pueda ejecutar sin volver a pensarlo.
- **4.4 El informe**, en `fix-fase2/docs/carry_funding_umbral.md`: el umbral, la
  tabla, la especificación, y **tres líneas** finales con el veredicto y qué
  queda sin medir.

### Límites de escritura

- Crear: `fix-fase2/fase0_n8/*`, `fix-fase2/src/carry_umbral.py`,
  `fix-fase2/results/carry_umbral_*.json`, `fix-fase2/docs/carry_funding_umbral.md`,
  y el registro al final de **este** archivo.
- **No tocar** ningún fichero existente de `src/`, `results/`, `data/` ni
  `docs/`. Importar `rigor_estadistico`, no modificarlo.
- **No descargar nada.** No hay red para mercado y no se intenta.
- Nada fuera de `fix-fase2/`. Nada en la raíz. Nada en `main`.

---

## 5. Lo que esta tarea NO hace

- **No evalúa ninguna señal, ni el carry ni ninguna candidata del Paso C.** No
  consume trials y **no mueve `N`**. Declararlo con esas palabras en el registro.
- No baja datos, no abre cuentas, no toca credenciales, no opera.
- No resuelve `N`, `V`, el holdout ni `N* = 4.0786`, y **no los necesita**: el
  umbral de 4.1 es paramétrico en `N`.
- No decide nada. Entrega el umbral y la contrapropuesta; decide Pablo.

## 6. Entregables

1. `## Registro de revisión némesis` al final de **este** archivo, con Paso A,
   Paso B, **Paso C** y la crítica literal del Maker/Verifier con sus respuestas.
2. Los scripts en `fix-fase2/fase0_n8/`.
3. **PARAR.** Ni un paso de la §4 sin OK en la §7.
4. PR contra `fase-b-recuperada`. En la descripción: el veredicto de B-a (si la
   palanca de `T` existe o no) y las candidatas del Paso C en una línea cada una.

## 7. Estado de la tarea

| | |
|---|---|
| Fase 0 — Paso A | [pendiente] |
| Fase 0 — Paso B | [pendiente] |
| Fase 0 — **Paso C (contrapropuesta)** | [pendiente] |
| Maker/Verifier invocado | [pendiente] |
| NO-GO disparados | [pendiente] |
| **OK de Pablo para el Alcance** | **[pendiente]** — enumerando los pasos de la §4 que cubre |

---

## Checklist de entrega

- [ ] **Sintaxis:** todo script se ejecuta antes de pegar su salida.
- [ ] **Cifras:** cada una con su comando. Ninguna fabricada (N7 · hallazgos 3, 9).
- [ ] **Tablas:** con unidad y `n`.
- [ ] **Rutas:** cada bloque dice desde dónde corre.
- [ ] **Timeouts:** 30 min repartidos A/B/C/MV; si se agota, se entrega lo hecho
      con lo que falta declarado.
- [ ] **Reproducibilidad:** semilla 43 y `B = 10000` en todo bootstrap.
- [ ] **Reversibilidad:** nada fuera de los límites de escritura.
- [ ] **Sincronía:** el registro va en este archivo; las correcciones también a
      los scripts.
- [ ] **Fase 0:** A, B y **C** separados, cinco objeciones mínimo, Maker/Verifier
      con crítica literal pegada, y el Paso C juzgado con la misma dureza.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
