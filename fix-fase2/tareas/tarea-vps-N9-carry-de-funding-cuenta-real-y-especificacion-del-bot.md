# Tarea N9 (VPS) — Carry de funding: la cuenta con datos reales, y la especificación del bot

**Dónde se ejecuta:** el **VPS** (`ssh bunker`), no la nube. La nube no tiene red
para mercado; el VPS sí, y está verificado en la §2.
**Repo:** `miguezlopezia-a11y/trading-bot`, rama base `fase-b-recuperada`
**Rama de trabajo:** `vps/n9-carry-cuenta-real` · **PR contra:** `fase-b-recuperada`
**Autor del brief:** sesión de escritorio, 2026-11-02 18:50
**Timeout:** Fase 0 ≤ 30 min. El Alcance, sin límite de reloj pero con tope de
descarga (§4.1).

## Qué entrega esta tarea, y en qué unidad

**Un número en euros al año, y la especificación de un bot que los capture.**

No un Sharpe. No una tabla de sensibilidad. No un dictamen. Las ocho tareas
anteriores entregaron documentos; esta entrega la cuenta y el plano.

Si la cuenta sale negativa, la entrega es **el número negativo con sus datos
delante** y el Paso C con la alternativa. Eso también es una respuesta útil: cierra
la vía en una tarde en vez de en un mes.

## Lecturas previas obligatorias

1. `fix-fase2/tareas/tarea-nube-S2-investigacion-literatura-cripto.md`
   (`nube/s2-literatura`), registro némesis: su **§3.2** nombró el carry como la
   familia que mejor encaja, su **B6** explica el bloqueo, y su regla
   **`N = N_vigente + 1`** es la que se aplica aquí.
2. `fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md`
   (`nube/n5-reconocimiento-datos`), **objeción B-c entera**: refutó la versión
   ingenua de esta idea. No la repitas.
3. `fix-fase2/tareas/tarea-nube-N7-benchmark-de-exposicion-igualada.md`
   (`nube/n7-benchmark-exposicion`), **resumen ejecutivo**: N7 pidió medir algo
   que ya estaba publicado el día antes. Antes de medir, comprueba si ya está
   medido.
4. `fix-fase2/src/rigor_estadistico.py` — se importa, no se reescribe.

---

## 1. La operación, en tres frases

Un futuro perpetuo no vence, así que para que su precio siga al spot se paga un
**funding** cada 8 horas entre longs y shorts. Cuando es positivo, los longs
pagan a los shorts.

La operación: **corto en el perpetuo y largo en el spot por el mismo nominal.**
El precio deja de importar —lo que gana una pata lo pierde la otra— y el P&L es
el funding cobrado menos los costes.

**No es un pronóstico, es una tarifa.** Y por eso es la primera cosa de este
expediente que no exige adivinar nada.

### Lo que ya está refutado y este brief NO afirma

N5 · B-c (ALTO), que hay que leer antes de escribir una línea:

- **"No depende de predecir" no baja ningún listón.** `sharpe_min_dsr` no tiene
  ese argumento. El umbral lo fijan `N`, `T_eff`, *skew* y curtosis.
- **Las colas del carry SUBEN el listón**: vol baja y curtosis alta con cola
  izquierda (se cobra años y se devuelve en un desapalancamiento). N5 midió
  0.4723 → 0.4993 al pasar de kurt 32 a kurt 400 con skew −1.
- **`N` arranca en ≥ 16**, no en 1 (regla de S2: el sesgo de selección vive en el
  decisor, no en el dataset). Con el recuento de N6 (`N ≥ 15`, posiblemente 19),
  esta candidata es la siguiente.

**Pero esta tarea no se decide por el listón.** Se decide por la cuenta: si el
funding neto de costes no paga, da igual el Sharpe; y si paga, el Sharpe es la
comprobación posterior, no la pregunta. **El orden importa y es el contrario al
de las ocho tareas anteriores.**

---

## 2. Hechos verificados por mí, vía SSH, el 2026-11-02 a las 18:40

Todo lo de abajo lo ejecuté yo contra el VPS. **Reverifícalo**: si algo no
reproduce, es un hallazgo y va al registro.

### 2.1 Las tres APIs de funding responden desde el VPS, sin credenciales

```
$ ssh bunker
=== BINANCE fundingRate ===
http=200 bytes=379
[{"symbol":"BTCUSDT","fundingTime":1793577600005,"fundingRate":"0.00010000","markPrice":"78314.33068216","rateType":"Regular"},
 {"symbol":"BTCUSDT","fundingTime":1793606400001,"fundingRate":"0.00008758","markPrice":"78083.00000000","rateType":"Regular"},
 {"symbol":"BTCUSDT","fundingTime":1793635200000,"fundingRate":"0.00009118","markPrice":"77490.46959520","rateType":"Regular"}]

=== BYBIT funding history ===
http=200 bytes=364
{"retCode":0,"retMsg":"OK","result":{"category":"linear","list":[
 {"symbol":"BTCUSDT","fundingRate":"0.00009346","fundingRateTimestamp":"1793635200000"},
 {"symbol":"BTCUSDT","fundingRate":"0.00005216","fundingRateTimestamp":"1793606400000"},
 {"symbol":"BTCUSDT","fundingRate":"0.0000959","fundingRateTimestamp":"1793577600000"}]}}

=== OKX funding history ===
http=200 bytes=546
{"code":"0","data":[{"fundingRate":"0.0001","fundingTime":"1793635200000","instId":"BTC-USD-SWAP","realizedRate":"0.0001"}, ...
```

**Esto resuelve el `[no verificado]` de S2 · B6.** Los datos históricos de
funding son públicos, gratuitos y alcanzables sin clave desde el VPS. Es la
diferencia entre esta tarea y las ocho anteriores: **el dato existe y está al
alcance.**

### 2.2 Hay 7,1 años de historia de funding

```
$ curl -s "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1500000000000&limit=2"
[{"symbol":"BTCUSDT","fundingTime":1568102400000,"fundingRate":"0.00010000","markPrice":"","rateType":"Regular"}, ...
```

`fundingTime 1568102400000` = **2019-09-10**. A 3 liquidaciones por día son
**~7.830 observaciones** de aquí a hoy, contra el `T_eff = 4336` de Fase B.
**Confirmar la fecha exacta con `date -d @1568102400` en el Paso A** y calcular
el conteo real, no estimado.

### 2.3 El universo es enorme, y eso es un peligro antes que una ventaja

```
$ curl -s "https://fapi.binance.com/fapi/v1/premiumIndex" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
945
```

**945 perpetuos.** Cribar los mejores por funding realizado es *exactamente* el
error que este expediente lleva ocho tareas pagando: 945 trials disfrazados de
una idea. La §4.1 fija la criba **antes** de mirar un solo funding, y el Paso B
tiene una objeción obligatoria sobre esto.

### 2.4 Límite real de paginación: 500, no 1000

```
$ curl -s ".../fundingRate?symbol=BTCUSDT&limit=1000" | python3 -c "...; print(len(d))"
500 filas por peticion
```

Pedí 1000 y devolvió **500**. ~16 peticiones por símbolo para los 7,1 años.
Dimensiona la descarga con 500, no con el límite documentado.

### 2.5 El entorno del VPS

```
$ ssh bunker
git version 2.43.0 · /usr/bin/curl · /usr/bin/jq · /usr/bin/python3 (3.12.3)
/opt/trading-bot/venv/bin/python → numpy 2.5.3  pandas 3.0.6
/root/trading-bot-fix-fase2/.git → (sin git, confirmado)
df -h / → 150G total, 102G disponibles
```

**Trabaja en un clon nuevo**, `/root/trading-bot-n9`, cortado de
`fase-b-recuperada`. **No toques** `/opt/trading-bot` (producción, con el paper
runner vivo) ni `/root/trading-bot-fix-fase2` (sin git: un error ahí no se
deshace).

### 2.6 El régimen actual del funding, como orden de magnitud y nada más

Los tres valores de 2.1 rondan **0.0001 por 8 h**. Sostenido serían
`0.0001 × 3 × 365` ≈ **10,95 % anual bruto**. **[régimen actual, no media
histórica — no lo uses como entrada de nada]**: medir la media y la distribución
de los 7,1 años es el paso 4.2, y el valor de hoy no la predice.

### 2.7 Lo que esto NO prueba

- No prueba que el carry pague **neto**. El bruto de 2.6 es antes de comisiones,
  *slippage*, coste de margen y episodios de funding negativo.
- No prueba que sea capturable con el capital que haya: hay mínimos de nocional
  y el coste fijo pesa más cuanto menor es el capital.
- No dice nada del riesgo de contraparte, que no es estadístico.

---

## 3. Fase 0 (OBLIGATORIA). Tres pasos

Scripts en `fix-fase2/fase0_n9/`. Cada cifra con su comando: en N7 el
Maker/Verifier encontró tres bloques de salida **fabricados**.

### Paso A — Verificación de hechos (≤ 10 min)

- **A-1.** Reverificar los siete bloques de la §2 con **CONFIRMADO / CONFIRMADO
  con corrección / REFUTADO** y salida pegada.
- **A-2.** `date -d @1568102400` y el conteo exacto de liquidaciones disponibles
  para BTCUSDT. Cifra exacta, no estimada.
- **A-3.** Comprobar si ya hay trabajo de funding en el repo o en el VPS:
  `git grep -i funding` en las nueve ramas, y `grep -rl funding` en
  `/opt/trading-bot` y `/root/trading-bot-fix-fase2`. **Es la comprobación que
  N7 no hizo.** Si aparece algo, PARAR.
- **A-4.** Las comisiones **reales y vigentes**, leídas de la API o de la
  documentación del exchange, no de memoria: *maker* y *taker* de perpetuos, y
  de spot, para el nivel de comisiones sin volumen (VIP 0). Pegar la fuente.
- **A-5.** Qué pide el exchange para la pata corta: margen inicial y de
  mantenimiento del perpetuo, y si el spot comprado sirve de colateral o hay que
  inmovilizar dinero aparte. **Esto decide el capital inmovilizado y por tanto
  el retorno sobre capital, que es el número que importa.**

### Paso B — Ataque adversarial (≤ 10 min)

**Mínimo cinco objeciones con severidad y qué cambia del Alcance.** Cuatro
obligatorias:

- **B-a.** **Los 945 símbolos.** Cualquier criba por funding realizado es
  selección múltiple. ¿Es la criba de 4.1 (liquidez, precomprometida) de verdad
  independiente del funding, o el funding alto y la liquidez están
  correlacionados y la criba lo cuela por la puerta de atrás? Si están
  correlacionados, **dilo y propón la corrección.**
- **B-b.** **El modo de muerte.** El carry no quiebra por el precio: quiebra por
  liquidación de la pata corta en un salto, por desanclaje perp/spot, y por el
  exchange (rehipotecación, cambio de reglas, retiradas congeladas). Nada de eso
  está en el Sharpe ni en el DSR. ¿Qué métrica lo captura? Si la respuesta es
  "ninguna de las que usa el expediente", **dilo**.
- **B-c.** **Por qué iba a pagar algo tan conocido.** El basis trade es la
  operación más explotada del mercado cripto. Si el funding medio histórico neto
  de costes es cercano a cero, la cuenta no cierra ni con `T` infinito. Busca
  este argumento con ganas antes de que lo encuentre el mercado con el dinero de
  Pablo.
- **B-d.** **La supervivencia del universo.** Los 945 símbolos son los listados
  **hoy**. Los perpetuos que se delistaron —con su funding, a menudo
  extremo— no están. Es el mismo sesgo que `portfolio_supervivencia.py` midió
  para el spot. ¿Cuánto sesga?

Y al menos una propia.

### Paso C — Contrapropuesta (≤ 10 min), OBLIGATORIO

Si el Paso B tumba el carry, **devuelve tu propuesta**. Un registro que concluye
*"esto tampoco"* y para ahí es **entrega incompleta y se rechaza**.

Entre **una y tres** candidatas, cada una con: mecanismo económico en una frase ·
predictiva o no · la serie de datos exacta y **si se baja sin clave desde el
VPS** · el `N` que le toca (`N_vigente + 1`) · **qué la mata rápido y en cuántas
horas** · por qué es mejor que el carry · y **cuántos euros al año podría dar con
un capital de 1.000, 10.000 y 100.000 €**, aunque sea un orden de magnitud
declarado como tal.

Ordenadas por **coste de descartarlas**, de más barata a más cara. No por retorno
esperado.

**Nada que exija operar en vivo, credenciales ni dinero real en la fase de
investigación.** Datos históricos públicos, sí. Y **ninguna candidata se
evalúa aquí**: medir el Sharpe de una señal consume un trial y sube `N` para todo
el expediente.

### Maker/Verifier

Segundo agente que **solo critique este registro**. Historial: dos CRÍTICOS en
N4, trece hallazgos con un CRÍTICO que invirtió el veredicto en N6, **veinte con
cinco CRÍTICOS en N7, tres de ellos salidas fabricadas**.

Crítica literal pegada, respuesta hallazgo por hallazgo reverificando con
comandos propios, correcciones en el documento **y en los scripts**. Dile
expresamente que **juzgue el Paso C con la misma dureza que el Paso B**, y que
revise la cuenta de la §4.2 como si fuera a poner su dinero.

### NO-GO de la Fase 0 — binarios

A N6 se le reprochó graduar frenos sin grados; a N7, declarar disparado lo que su
propio JSON decía que no.

| Condición | Acción |
|---|---|
| A-3 encuentra trabajo de funding ya hecho | **PARAR** (el error de N7) |
| Algún hecho de la §2 sale REFUTADO | **PARAR** |
| Las APIs de 2.1 ya no responden 200 | **PARAR** y reportar |
| A-4 o A-5 no se pueden verificar en fuente | **PARAR**: sin comisiones y sin margen reales no hay cuenta, solo una ilusión |
| B-c concluye que el funding neto histórico es ~0 | **No parar**: es el resultado. Va en la primera línea y el Paso C pasa a ser el contenido principal |
| El Paso C no da ni una candidata ni defiende el carry | **ENTREGA INCOMPLETA** |

---

## 4. Alcance (NO EJECUTAR sin OK escrito de Pablo en la §7)

El OK enumerará los pasos que cubre.

### 4.1 La criba, fijada ANTES de mirar un solo funding

Escribir en el registro, **antes de descargar nada**, y con `git commit` propio
que lo feche:

- Los **N símbolos** elegidos y el criterio, que debe ser **solo de liquidez y
  antigüedad** (p. ej.: los 20 de mayor volumen a 24 h con historia completa
  desde 2019-09-10 y cotizados en los tres exchanges). **Nada de funding en el
  criterio.**
- Los tres exchanges, o la razón de usar uno.
- El periodo, completo y sin holdout: aquí no se evalúa una señal, se mide una
  tarifa.

**Tope de descarga:** 500 MB y 2.000 peticiones. Congelar con el protocolo del
repo: un CSV por símbolo y exchange, con `.sha256` y `.meta.json`
(`fecha_descarga`, endpoint, parámetros), igual que `data/multi/`. En
`fix-fase2/data/funding/`.

### 4.2 La cuenta. Es el entregable

Por símbolo y por año natural, y agregado:

| Concepto | Signo |
|---|---|
| Funding cobrado (corto en perp) | + |
| Comisión de apertura y cierre de las dos patas, con las cifras de A-4 | − |
| *Slippage* estimado, declarado como estimación | − |
| Coste de rebalanceo cuando las patas se descuadran | − |
| Coste del capital inmovilizado como margen (A-5) | − |
| **Neto** | **=** |

Y el resultado en las dos unidades que deciden:

1. **% anual sobre el capital total inmovilizado** (las dos patas más el margen).
2. **Euros al año con 1.000, 10.000 y 100.000 €** de capital, diciendo en cuál
   el mínimo de nocional del exchange lo hace imposible.

Más la distribución: percentiles del funding por periodo, **el peor mes y el peor
trimestre de los 7,1 años**, y el porcentaje de periodos en que fue negativo.

### 4.3 El riesgo que realmente mata, cuantificado

- El mayor movimiento adverso de 8 h en la historia descargada, y **qué margen
  habría hecho falta** para no ser liquidado en él, con el nocional de 4.2.
- El mayor desanclaje perp-spot observado.
- Un veto explícito: a partir de qué funding negativo sostenido la operación se
  cierra.

Si 4.3 dice que el margen necesario para sobrevivir al peor episodio deja el
retorno sobre capital por debajo de lo que paga un depósito, **eso es el
veredicto** y hay que escribirlo así.

### 4.4 La especificación del bot, si 4.2 y 4.3 lo sostienen

No código: la especificación que permita escribirlo sin volver a pensar.

- Cuándo abre, con qué tamaño, en qué símbolos, y el límite por símbolo.
- Cuándo cierra: por funding negativo, por desanclaje, por margen.
- Cómo rebalancea las patas y con qué frecuencia (y su coste, ya en 4.2).
- Los vetos de riesgo, en el formato de `risk_veto.py` del repo.
- **Qué necesita que hoy no existe**: credenciales, permisos de API (solo
  *trade*, nunca retirada), y el modo papel previo.
- **Y el criterio de arranque en real**: cuántos meses en papel y con qué
  resultado mínimo antes de poner un euro.

### 4.5 El informe

`fix-fase2/docs/carry_funding_cuenta_real.md`: la criba precomprometida, la
cuenta de 4.2, el riesgo de 4.3, la especificación de 4.4, y **tres líneas**
finales: euros al año esperados, el peor escenario histórico, y qué queda sin
medir.

### Límites de escritura

- Crear: `fix-fase2/fase0_n9/*`, `fix-fase2/src/carry_funding_*.py`,
  `fix-fase2/data/funding/*`, `fix-fase2/results/carry_funding_*.json`,
  `fix-fase2/docs/carry_funding_cuenta_real.md`, y el registro en **este**
  archivo.
- **No tocar** nada existente de `src/`, `results/`, `docs/` ni `data/multi*`.
  `rigor_estadistico` y `risk_veto` se importan.
- **No tocar** `/opt/trading-bot` ni `/root/trading-bot-fix-fase2` en el VPS.
  Clon nuevo en `/root/trading-bot-n9`.
- **Cero credenciales.** Solo endpoints públicos. No crear cuentas, no firmar
  peticiones, no operar.
- Nada en `main`.

---

## 5. Lo que esta tarea NO hace

- **No opera, no abre cuenta, no toca dinero.** Mide con datos históricos
  públicos y especifica.
- **No evalúa ninguna señal.** Medir una tarifa no es backtestear un pronóstico:
  no consume trials y **no mueve `N`**. Declararlo con esas palabras.
- No resuelve `N`, `V`, el holdout ni `N* = 4.0786`, y no los necesita.
- No decide. Entrega la cuenta y el plano; decide Pablo.

## 6. Entregables

1. `## Registro de revisión némesis` en **este** archivo: Paso A, Paso B, Paso C
   y la crítica literal del Maker/Verifier con sus respuestas.
2. Scripts en `fix-fase2/fase0_n9/`.
3. **PARAR.** Ni un paso de la §4 sin OK en la §7.
4. PR contra `fase-b-recuperada`. En la descripción, tres líneas: si las APIs
   siguen en pie, el veredicto de B-c, y las candidatas del Paso C.

## 7. Estado de la tarea

| | |
|---|---|
| Fase 0 — Paso A | **[hecho]** — 7 bloques de la §2 + A-2..A-5, con salida pegada |
| Fase 0 — Paso B | **[hecho]** — 7 objeciones: 2 CRITICAS, 3 ALTAS, 2 MEDIAS |
| Fase 0 — **Paso C (contrapropuesta)** | **[hecho]** — 3 candidatas; C-1 mide 4,949 % neto hoy |
| Maker/Verifier | **[hecho]** — critica literal pegada y respondida |
| NO-GO disparados | **ninguno de los seis** — ver el veredicto de la Fase 0 |
| **OK de Pablo para el Alcance** | **[pendiente]** — enumerando los pasos de la §4 |

---

## Checklist de entrega

- [ ] **Sintaxis:** todo script se ejecuta antes de pegar su salida.
- [ ] **Cifras:** cada una con su comando. Ninguna fabricada (N7 · hallazgos 3, 9).
- [ ] **Datos:** todo CSV descargado con `.sha256` y `.meta.json`, protocolo de
      `data/multi/`. Tope 500 MB / 2.000 peticiones.
- [ ] **Criba:** fijada y commiteada **antes** de la primera descarga de funding.
- [ ] **Comisiones y margen:** de fuente verificable, nunca de memoria.
- [ ] **Rutas:** cada bloque dice desde dónde corre, y nada fuera de
      `/root/trading-bot-n9`.
- [ ] **Timeouts:** Fase 0 ≤ 30 min repartidos A/B/C/MV.
- [ ] **Reproducibilidad:** semilla 43 y `B = 10000` en todo bootstrap.
- [ ] **Credenciales:** cero. Solo endpoints públicos.
- [ ] **Sincronía:** registro en este archivo; correcciones también en los scripts.
- [ ] **Fase 0:** A, B y C separados, cinco objeciones mínimo, Maker/Verifier con
      crítica literal pegada y el Paso C juzgado con la misma dureza.

---

## Registro de revisión némesis

**Fecha:** 2026-11-02 · **Ejecutor:** sesión de escritorio N9 (Claude Code, Opus 5),
trabajando **en el VPS** por SSH.
**Rama:** `vps/n9-carry-cuenta-real`, cortada de `fase-b-recuperada` @ `0f77f9e`.
PR contra `fase-b-recuperada`, nunca contra `main`.
**Alcance ejecutado:** solo la **Fase 0 (§3)**, pasos A, B y C, más el segundo agente
del Maker/Verifier. **Ni un paso de la §4.** La §7 sigue sin firma.
**Scripts:** `fix-fase2/fase0_n9/`, **once** ficheros (nueve `.py`, dos `.sh`), cada
uno con su JSON o TXT de salida. Los once se ejecutan por separado y los once se
han ejecutado así, con `rc=0`, **desde `/root/trading-bot-n9/fix-fase2`**. Inventario
completo al final de este registro.
**Cuerpos congelados:** `fase0_n9/fuentes_a4/`, `fuentes_a4b/` y `fuentes_a5/`, cada
uno con el `sha256` del cuerpo y el del fichero guardado por separado.
**Lecturas previas:** las cuatro del encabezado, en orden. S2 §3.2 y B6 enteras,
N5 · B-c entera, N7 resumen ejecutivo y los veinte hallazgos de su Maker/Verifier,
y `fix-fase2/src/rigor_estadistico.py` completo (270 líneas): expone `psr`, `dsr`,
`expected_max_sharpe`, `ar1_effective_n`, `block_bootstrap_ci` y `PPY`; no se toca.
`sharpe_min_dsr` **no está ahí**, está en `fix-fase2/src/potencia_fase_b.py:34`
(verificado en A-3.6).
**Esta Fase 0 no evalúa ninguna señal: mide tarifas y precios observados. No consume
trials y no mueve `N`.** `N` sigue donde lo dejó N6.
**Reloj real:** 19:30–20:30 UTC, **unos 60 minutos**, no los 30 del encabezado. El
desvío es mío y lo declaro: 25 de esos minutos se fueron en A-4, porque las tres
primeras fuentes de comisiones no sirven y hubo que encontrar una que sí.
**Cero credenciales.** Ninguna petición lleva cabecera de autenticación ni firma; el
campo `credenciales_enviadas` de los nueve JSON está vacío. No se ha creado ninguna
cuenta y no se ha operado.
**No se ha descargado el histórico de la §4.1.** `fix-fase2/data/funding/` **no
existe** (A-3.5). Lo que sí se ha hecho, y se declara como desvío con su razón, está
en «Desvíos declarados», más abajo.

### Resumen ejecutivo

| | Resultado |
|---|---|
| Hechos de la §2 | **3 CONFIRMADOS** (2.1, 2.5, 2.7-como-regla) y **4 CONFIRMADOS con corrección** (2.2, 2.3, 2.4, 2.6). **Ninguno REFUTADO** → ese NO-GO no se dispara. La corrección de **2.3 es material**: los 945 **no son perpetuos** |
| **A-3, el NO-GO que mató a N7** | **NO se dispara, pero encuentra algo:** cero código y cero datos de funding en las diez ramas, en `/opt/trading-bot` y en `/root/trading-bot-fix-fase2`. Lo que hay es **`tarea-nube-N8-carry-de-funding-umbral-de-viabilidad-y-contrapropuesta.md`**, un brief **sin ejecutar** de la misma familia, commiteado **14 minutos antes** que el de N9. Trabajo **encargado**, no trabajo **hecho** → es B-e, no un freno |
| A-2 conteo exacto | **7.832** liquidaciones de BTCUSDT, **0 huecos**, de **2019-09-10 08:00:00 UTC** a 2026-11-02 16:00 UTC. **7,147 años**, **1,806×** el `T_eff = 4336` de Fase B. El brief estimaba ~7.830: diferencia **+2** |
| A-4 comisiones | **Verificadas en fuente para Bybit**, VIP 0, las dos patas: spot **0,1000 % maker y taker**, perp **0,0550 % taker / 0,0200 % maker**. OKX solo da spot en el cuerpo servido; **Binance no es verificable sin clave** (202 vacío, 404, 401). → el NO-GO no se dispara: hay una fuente que sí |
| A-5 margen | **Verificado en API pública.** Bybit BTCUSDT tramo 1: `initialMargin 0.0066`, `maintenanceMargin 0.0033`. OKX BTC-USDT-SWAP: `imr 0.01`, `mmr 0.004`. Y **el spot sí sirve de colateral** en OKX: `discountRate 0.98` para BTC |
| **La cuenta, y es el entregable** | Carry BTCUSDT, **régimen 2026**: bruto **3,171 %** anual, neto de la ida y vuelta de Bybit (0,240 pp) **2,931 %** sobre nocional, **2,66 %** sobre capital con margen del 10 %. **El DFR del BCE de hoy es 2,500 %** (verificado). **La ventaja sobre el activo sin riesgo es 0,16 puntos** |
| **En euros al año** | **27 € / 266 € / 2.665 €** con 1.000, 10.000 y 100.000 €. El depósito del BCE paga **25 € / 250 € / 2.500 €**. La diferencia es **+2 € / +16 € / +165 €** al año, **antes** de *slippage*, rebalanceo, recargas de margen, riesgo de contraparte y el coste de tener el bot en pie |
| Paso B | **Siete objeciones**: **2 CRÍTICAS** (B-b, B-c), **3 ALTAS** (B-a, B-d, B-e), **2 MEDIAS** (B-f, B-g). Ninguna retirada |
| Paso C | **Tres candidatas**, ordenadas por coste de descartarlas. La primera, **la base de los futuros con vencimiento**, da **4,949 %** neto medido hoy contra el **2,931 %** del carry, y su número **se conoce al entrar**, así que no hay inferencia que deflactar |
| Maker/Verifier | Invocado. Crítica literal pegada y respondida hallazgo por hallazgo más abajo |

**La frase que resume la tarea:** el carry de funding **sí paga**, y **sí es
capturable sin clave y con datos públicos** —eso queda resuelto y es lo que ocho
tareas no habían podido decir—, pero en el régimen de 2026 paga **0,16 puntos por
encima de un depósito en euros**, y la cuenta se la come cualquiera de los cuatro
costes que todavía no están medidos. **Lo que estaba mal no era la idea: era la
unidad.** Sin la tasa sin riesgo delante, 2,66 % parece un retorno.

**Lo que esta Fase 0 añade y no estaba en ningún sitio del expediente:** que los
datos de funding son públicos y gratuitos (resuelve el `[no verificado]` de
S2 · B6), que son **7.832** observaciones y no una estimación, que la paginación
real es de **1000** filas con `startTime` y no de 500, que los «945 perpetuos» son
**565**, que la cola de la tarifa está **acotada por regla** y no por el mercado,
que **465 de 820** símbolos liquidan cada **4 horas** y no cada 8, que **solo 3**
perpetuos vivos son anteriores a 2020 —así que la criba que el brief propone tiene
un universo elegible de tres—, que **el histórico de funding sobrevive al
delistado** y por tanto el sesgo de supervivencia sí es parcialmente acotable, y
que existe un instrumento mejor que el perpetuo para la misma idea.

---

## Paso A — Verificación de hechos

Cada cifra con su comando. Todos los bloques corren desde
`/root/trading-bot-n9/fix-fase2`.

### A-1 · §2.1 — Las tres APIs de funding responden 200 sin credenciales → **CONFIRMADO**

`fase0_n9/a1_hechos_seccion2.py`, salida literal:

```
=== 2.1 — las tres APIs de funding, sin credenciales ===

--- BINANCE ---
url   = https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=3
http=200 bytes=379 ms=302
[{"symbol":"BTCUSDT","fundingTime":1793577600005,"fundingRate":"0.00010000","markPrice":"78314.33068216","rateType":"Regular"},{"symbol":"BTCUSDT","fundingTime":1793606400001,"fundingRate":"0.00008758","markPrice":"78083.00000000","rateType":"Regular"},{"symbol":"BTCUSDT","fundingTime":1793635200000,"fundingRate":"0.00009118","markPrice":"77490.46959520","rateType":"Regular"}]

--- BYBIT ---
url   = https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=3
http=200 bytes=364 ms=214
{"retCode":0,"retMsg":"OK","result":{"category":"linear","list":[{"symbol":"BTCUSDT","fundingRate":"0.00009346","fundingRateTimestamp":"1793635200000"},{"symbol":"BTCUSDT","fundingRate":"0.00005216","fundingRateTimestamp":"1793606400000"},{"symbol":"BTCUSDT","fundingRate":"0.0000959","fundingRateTimestamp":"1793577600000"}]},"retExtInfo":{},"time":1793648951362}

--- OKX ---
url   = https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USD-SWAP&limit=3
http=200 bytes=546 ms=277
{"code":"0","data":[{"formulaType":"withRate","fundingRate":"0.0001","fundingTime":"1793635200000","instId":"BTC-USD-SWAP","instType":"SWAP","method":"current_period","realizedRate":"0.0001"}, ...], "msg":""}

2.1 -> CONFIRMADO (los tres http==200: True)
```

Las tres cifras de BTCUSDT del brief (`0.00010000`, `0.00008758`, `0.00009118` en
Binance; `0.00009346`, `0.00005216`, `0.0000959` en Bybit) **reproducen al dígito**.
El campo `credenciales_enviadas` del JSON está vacío y la única cabecera enviada es
`User-Agent`. **Esto resuelve, con medición propia, el `[no verificado]` de
S2 · B6:** los datos históricos de funding son públicos, gratuitos y alcanzables sin
clave desde el VPS, y por tanto la familia del carry **entra** sin necesidad de
cuenta para la fase de investigación. La contradicción que B6 encontró entre §3.2 y
§3.6 de S2 queda cerrada por el lado empírico.

### A-1 · §2.2 — Hay 7,1 años de historia → **CONFIRMADO con corrección**, y A-2 pone la cifra exacta

### A-2 — La fecha exacta y el conteo exacto, enumerando

`fase0_n9/a2_fecha_y_conteo_exacto.py`, salida literal:

```
=== A-2.1 — fecha exacta de fundingTime 1568102400000 ===
$ date -u -d @1568102400 +%Y-%m-%d %H:%M:%S %Z
2019-09-10 08:00:00 UTC
python (UTC) = 2019-09-10T08:00:00+00:00
brief dice 2019-09-10 -> coincide: True

=== A-2.2 — enumeracion completa de las liquidaciones de BTCUSDT ===
  peticion  1  http=200  filas=1000  hasta 2020-08-08T08:00:00+00:00
  peticion  2  http=200  filas=1000  hasta 2021-07-07T16:00:00.008000+00:00
  peticion  3  http=200  filas=1000  hasta 2022-06-06T00:00:00+00:00
  peticion  4  http=200  filas=1000  hasta 2023-05-05T08:00:00+00:00
  peticion  5  http=200  filas=1000  hasta 2024-04-02T16:00:00+00:00
  peticion  6  http=200  filas=1000  hasta 2025-03-02T00:00:00+00:00
  peticion  7  http=200  filas=1000  hasta 2026-01-29T08:00:00.009000+00:00
  peticion  8  http=200  filas=832  hasta 2026-11-02T16:00:00+00:00

  peticiones usadas       = 9 (tope del script 60)
  filas crudas            = 7832  duplicadas = 0
  CONTEO EXACTO           = 7832
  primera                 = 2019-09-10T08:00:00+00:00
  ultima                  = 2026-11-02T16:00:00+00:00
  dias cubiertos          = 2610.33  (7.147 anos)
  esperadas si todo 8h    = 7832  -> huecos = 0
  brief estima ~7.830 ; exacto = 7832 ; diferencia = 2
  T_eff de Fase B = 4336 ; ratio = 1.806x
```

La fecha del brief es correcta y la hora, que no estaba, es **08:00:00 UTC**. El
conteo exacto es **7.832** y la serie **no tiene ni un hueco**: las 7.831
diferencias consecutivas son de 8 horas (los `intervalos != 8h` que lista el JSON
son de 28.799.9xx ms, o sea 8 h menos unas decenas de milisegundos: desviación del
sello del servidor, no un hueco).

**Corrección sobre la consecuencia que el brief saca, y es la que importa:** el
brief convierte las 7.832 observaciones en «contra el `T_eff = 4336` de Fase B», lo
que insinúa una ganancia de potencia de 1,8×. **Esa ganancia es bruta y
probablemente no existe**, por lo que N8 · B-a ya anticipaba: el funding está
autocorrelacionado por construcción, los regímenes duran días, y `ar1_effective_n`
se come esa ganancia. **No lo he medido** —medir `T_eff` del funding es el §4.1 de
N8, no de esta tarea— y por tanto **no afirmo nada sobre el listón**. Lo que sí
afirmo es que **esta tarea no se decide por ahí**, como dice su propia §1.

### A-1 · §2.3 — «945 perpetuos» → **CONFIRMADO con corrección, y la corrección es material**

`fase0_n9/a1_hechos_seccion2.py` y `fase0_n9/b1_transversal_y_basis.py`:

```
=== 2.3 — tamano del universo de perpetuos (premiumIndex) ===
url   = https://fapi.binance.com/fapi/v1/premiumIndex
http=200 bytes=209741 -> len = 945
brief dice 945 ; medido = 945 ; diferencia = 0

=== 2.3 corregido — que son exactamente los 945 de premiumIndex ===
premiumIndex devuelve                  = 945 instrumentos
por contractType de exchangeInfo       = {'PERPETUAL': 703, 'TRADIFI_PERPETUAL': 235, 'CURRENT_QUARTER': 2, 'NEXT_QUARTER': 2, '(no esta en exchangeInfo)': 3}
PERPETUAL con status TRADING           = 565
ticker/24hr devuelve                   = 804
```

El **945** reproduce al dígito. Lo que no se sostiene es la etiqueta: **no son 945
perpetuos**. Son 945 instrumentos, y de ellos **703 son `PERPETUAL`**, de los cuales
**565 están en `TRADING`**; **235 son `TRADIFI_PERPETUAL`** (acciones y materias
primas tokenizadas, con `deliveryDate` ficticio en el año 2100), **4 son
trimestrales con vencimiento real** y **3 no están en `exchangeInfo`** (`EOSUSDT`,
`FRONTUSDT`, `MATICUSDT`: ya delistados, y aun así con funding vivo — ver B-d).

**Qué cambia:** la objeción obligatoria B-a del brief está construida sobre «945
trials disfrazados de una idea». El número correcto de trials potenciales del
universo cripto de perpetuos es **565**, no 945. El argumento no se cae —565 sigue
siendo una máquina de selección— pero la cifra que lo cuantifica estaba inflada un
**67 %**, y la §4.1 que diga «los N de mayor volumen de los 945» estaría cribando
sobre un universo que incluye 235 perpetuos de acciones de Nvidia y Tesla.

### A-1 · §2.4 — «Límite real de paginación: 500, no 1000» → **CONFIRMADO con corrección**

Medición del brief, reproducida al bit:

```
=== 2.4 — limite real de paginacion (se pide 1000) ===
url   = https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000
http=200 bytes=63044 -> filas devueltas = 500
```

Pedir 1000 **sin `startTime`** devuelve 500: el brief tiene razón. Pero con
`startTime` el `limit=1000` **se respeta**: las siete primeras peticiones de A-2.2
devolvieron **1000 filas cada una**. La consecuencia que el brief deriva —«~16
peticiones por símbolo para los 7,1 años. Dimensiona la descarga con 500»— es
**falsa**: fueron **9 peticiones**, y el tope de 2.000 peticiones de la §4.1 da para
unos **220 símbolos**, no 125.

**Nota sobre si esto dispara el NO-GO de «algún hecho de la §2 REFUTADO».** No lo
dispara, y el criterio que aplico es el que el propio brief escribe: la §2 ordena
«reverifícalo: si algo **no reproduce**, es un hallazgo». El comando reproduce al
bit. Lo que falla es una estimación que el brief marca con `~` y que él mismo manda
sustituir por la cifra real (igual que el `~7.830` de la §2.2). Sustituirla es lo
que se me pidió, no una refutación. **Si el Maker/Verifier lee el NO-GO de otra
manera, que lo diga: el criterio está escrito aquí para que se pueda atacar.**

### A-1 · §2.5 — El entorno del VPS → **CONFIRMADO**

`fase0_n9/a6_entorno.sh`, salida literal:

```
=== 2.5 — entorno del VPS ===
cwd    = /root/trading-bot-n9/fix-fase2
host   = bunker-2026
fecha  = 2026-11-02T19:49:10Z

--- git / curl / jq / python3 ---
git version 2.43.0
/usr/bin/curl
/usr/bin/jq
/usr/bin/python3
Python 3.12.3

--- interprete con numpy y pandas ---
python 3.12.3 numpy 2.5.3 pandas 3.0.6

--- /root/trading-bot-fix-fase2/.git ---
no existe -> sin git, CONFIRMADO

--- df -h / ---
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       150G   43G  102G  30% /

--- el clon de trabajo ---
rama   = vps/n9-carry-cuenta-real
base   = 0f77f9e4b49ac837bb33472967f36157bbf66bc7
HEAD   = 0f77f9e
limpio = SI
```

Los siete datos del bloque reproducen: `git 2.43.0`, `curl`, `jq`, `python3 3.12.3`,
venv con `numpy 2.5.3` y `pandas 3.0.6`, `/root/trading-bot-fix-fase2/.git`
inexistente, y `150G / 102G disponibles`. `/opt/trading-bot` está presente y **no se
ha tocado**: los únicos procesos que `pgrep` devolvió son los de este propio script.

### A-1 · §2.6 — El régimen actual del funding → **CONFIRMADO, y A-2 demuestra por qué su propio aviso era necesario**

```
=== 2.6 — regimen actual del funding (orden de magnitud, NO media historica) ===
binance_btcusdt        [0.0001, 8.758e-05, 9.118e-05]  -> anualizado x3x365: [10.95, 9.59, 9.98] %
bybit_btcusdt          [9.346e-05, 5.216e-05, 9.59e-05]  -> anualizado x3x365: [10.23, 5.71, 10.5] %
okx_btc_usd_swap       [0.0001, 0.0001, 0.0001]  -> anualizado x3x365: [10.95, 10.95, 10.95] %
```

El `0.0001 × 3 × 365 ≈ 10,95 %` del brief reproduce. Y el aviso que el brief se pone
a sí mismo —**«[régimen actual, no media histórica — no lo uses como entrada de
nada]»**— resulta estar **completamente justificado**: la media medida de 2026 es
**0,00002896 por 8 h = 3,171 % anual**, así que las tres cifras de hoy están
**3,5 veces por encima** del año en curso. Quien hubiera usado el 10,95 % como
entrada se habría equivocado por un factor de 3,5.

**Hallazgo adicional sobre el 10,95 %, y no es casualidad:** `0.0001` por periodo es
el **valor por defecto** que el exchange aplica cuando el índice de prima está dentro
de la banda del componente de interés. En el corte transversal de B-a, la **mediana**
del funding anualizado de los 565 perpetuos es **exactamente 10,950 %** en los cuatro
bloques de liquidez, para símbolos de 4 h y de 8 h por igual. La moda del funding no
es un precio de mercado: es una constante administrativa.

### A-1 · §2.7 — «Lo que esto NO prueba» → **CONFIRMADO como regla, y las tres se han materializado**

Las tres advertencias del brief se cumplen, y las tres están ahora medidas:

1. «No prueba que el carry pague **neto**» → correcto: el bruto de 2026 es 3,171 % y
   el neto sobre capital 2,66 %, contra 2,500 % sin riesgo (A-7, B-c).
2. «No prueba que sea capturable con el capital que haya» → el mínimo de nocional
   **no** es la restricción (`minNotionalValue 5` USDT en Bybit, `MIN_NOTIONAL 50` en
   Binance): con 1.000 € se puede abrir. Lo que mata al capital pequeño es que
   2 € al año de ventaja no pagan nada (A-7).
3. «No dice nada del riesgo de contraparte» → correcto, y B-b sostiene que **ninguna
   métrica del expediente lo dice**.

### A-3 — ¿Hay ya trabajo de funding en el repo o en el VPS? → **el NO-GO no se dispara, pero hay hallazgo**

`fase0_n9/a3_trabajo_previo_funding.sh`. Salida literal, abreviada en las ramas sin
coincidencias:

```
--- A-3.1  git grep -il funding en las ramas remotas ---
origin/main : 0 archivos con 'funding'
origin/fase-b-recuperada : 4 archivos con 'funding'
      fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md
      fix-fase2/tareas/tarea-nube-N8-carry-de-funding-umbral-de-viabilidad-y-contrapropuesta.md
      fix-fase2/tareas/tarea-nube-S2-investigacion-literatura-cripto.md
      fix-fase2/tareas/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md
origin/feat/estrategias-candidatas : 0 archivos con 'funding'
origin/nube/n4-procedencia-v-t-n : 1 archivos con 'funding'
origin/nube/n5-reconocimiento-datos : 2 archivos con 'funding'
origin/nube/n6-holdout-y-recuento : 2 archivos con 'funding'
origin/nube/n7-benchmark-exposicion : 2 archivos con 'funding'
origin/nube/s1-auditoria-harness : 1 archivos con 'funding'
origin/nube/s2-literatura : 1 archivos con 'funding'
origin/nube/s3-datos : 1 archivos con 'funding'

--- A-3.2  codigo o datos de funding (no solo la palabra) en las ramas ---
origin/fase-b-recuperada : 2 rutas cuyo NOMBRE contiene funding/carry/basis/perp
      fix-fase2/tareas/tarea-nube-N8-carry-de-funding-umbral-de-viabilidad-y-contrapropuesta.md
      fix-fase2/tareas/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md
(las otras nueve ramas: 0)

--- A-3.3  grep -rl -i funding en /opt/trading-bot (produccion, solo lectura) ---
/opt/trading-bot/venv/lib/python3.12/site-packages/curl_cffi/_wrapper.abi3.so
/opt/trading-bot/venv/lib/python3.12/site-packages/lxml/.../iso_schematron_skeleton_for_xslt1.xsl
/opt/trading-bot/venv/lib/python3.12/site-packages/websockets-17.2.dist-info/METADATA
coincidencias: 3

--- A-3.4  grep -rl -i funding en /root/trading-bot-fix-fase2 (solo lectura) ---
coincidencias: 0

--- A-3.5  datos de funding ya descargados en el VPS ---
data/funding/ existe? NO
(los ficheros con 'funding' en el nombre bajo /root y /opt son 7: los dos briefs
 N8 y N9, y cinco FUNDING.yml de node_modules de /opt/criteria)

--- A-3.6  donde vive sharpe_min_dsr ---
origin/fase-b-recuperada:fix-fase2/src/potencia_fase_b.py:34:def sharpe_min_dsr(n_trials, var_trials=V_TRIALS, n_eff=T_EFF,
```

**Veredicto, y es binario.** El NO-GO dice «A-3 encuentra trabajo de funding **ya
hecho** → PARAR». **No hay trabajo hecho:** cero `.py`, cero CSV, cero JSON, cero
registro. Las tres coincidencias de `/opt/trading-bot` son binarios y metadatos de
`site-packages`, y las cinco de `/opt/criteria` son `FUNDING.yml` de GitHub
Sponsors en `node_modules`: ninguna es trabajo del expediente. El NO-GO **no se
dispara**.

**Lo que sí ha encontrado A-3**, y va al Paso B como **B-e (ALTA)**, es
`tarea-nube-N8-carry-de-funding-umbral-de-viabilidad-y-contrapropuesta.md`:

```
$ git log --format=%H %ad %s --date=iso -- fix-fase2/tareas/tarea-nube-N8-...md
05d1ebf98afaf6dc6147bbdb5207828e0ecd7f70 2026-11-02 18:36:34 +0100 Anade el brief de N8: carry de funding, umbral de viabilidad y contrapropuesta
$ wc -l fix-fase2/tareas/tarea-nube-N8-...md
361
$ grep -c 'Registro de revisión némesis' fix-fase2/tareas/tarea-nube-N8-...md   # (sección ausente)
$ git branch -a | grep n8                                                        # (sin salida)
```

Un brief de **361 líneas**, de la **misma familia**, commiteado a las **18:36**,
**14 minutos antes** que el de N9 (18:50, commit `0f77f9e`), con su §7 entera en
`[pendiente]`, **sin sección de registro** y **sin rama `nube/n8-carry-funding`**.
Es trabajo **encargado y no empezado**, no trabajo hecho — y por eso no es un freno.
Pero es el error de N7 girado 90 grados, y necesita una decisión de Pablo. Ver B-e.

### A-4 — Las comisiones reales y vigentes, de fuente, nunca de memoria

Tres rondas. `fase0_n9/a4_comisiones.py` sondea diez fuentes y congela cada cuerpo;
`fase0_n9/a4b_comisiones_extraccion.py` extrae de forma estructurada y sondea siete
más; `fase0_n9/a7_cuenta_minima.py` saca la cifra final del cuerpo congelado.

**Lo que no sirve, con su código de respuesta:**

```
binance_web_fee_futuros   https://www.binance.com/en/fee/futureFee            http=202 bytes=0
binance_web_fee_spot      https://www.binance.com/en/fee/trading              http=202 bytes=0
binance_bapi_vip_fee      .../bapi/accounts/v1/public/account/vip/fee/rate    http=404
binance_bapi_trade_fee    .../bapi/composite/v1/public/future/common/trade-fee http=404
binance_fapi_commission   https://fapi.binance.com/fapi/v1/commissionRate?symbol=BTCUSDT
                                                                              http=401 {"code":-2014,"msg":"API-key format invalid."}
okx_priapi_fee_tier       https://www.okx.com/priapi/v5/public/fee-rate-tier  http=404
okx_help_trading_fees     https://www.okx.com/help/trading-fees               http=404
okx_docs_trading_fee      https://www.okx.com/help/okx-trading-fees           http=404
```

**Binance no es verificable sin clave:** sus dos páginas de tarifas devuelven **202
con cuerpo vacío** desde el VPS, sus dos endpoints `bapi` candidatos devuelven 404, y
el endpoint oficial de comisiones exige clave (401, `-2014`). **No pongo ninguna cifra
de Binance**, ni de memoria ni interpolada.

**OKX da solo el spot.** El cuerpo servido de `https://www.okx.com/fees` (http 200,
71.806 bytes) trae las pestañas declaradas pero **solo los datos de la activa**:

```
pestanas declaradas en el cuerpo: [{'feeClazz': 12, 'instType': 1, ..., 'tabName': 'Spot'},
                                   {'feeClazz': 11, 'instType': 1, ..., 'tabName': 'Spot'},
                                   {'feeClazz': 4,  'instType': 4, ..., 'tabName': 'Futures'},
                                   {'feeClazz': 1,  'instType': 5, ..., 'tabName': 'Options'}]
filas 'Regular user' halladas: 1
  tradeType=6 assetType=6 maker=0.0008 taker=0.001 (std 0.0008/0.001)
```

OKX, usuario sin volumen, **spot**: maker **0,0800 %**, taker **0,1000 %**. La
pestaña `Futures` **no viene en el cuerpo**, así que **no tengo el perp de OKX** y no
lo invento.

**Bybit sí da las dos patas, con VIP 0 explícito.** Cuerpo congelado de
`https://www.bybit.com/en/help-center/article/Trading-Fee-Structure` (http 200,
455.483 bytes), tabla destagueada:

```
VIP Level | Spot Trading*(Crypto-Crypto) | Perpetual & Futures Contracts Trading | Options Trading |
Taker Fee Rate | Maker Fee Rate | Taker Fee Rate | Maker Fee Rate | Taker Fee Rate | Maker Fee Rate |
VIP 0 | 0.1000% | 0.1000% | 0.0550% | 0.0200% | 0.0300% | 0.0200% |
VIP 1 | 0.0800% | 0.0675% | 0.0400% | 0.0180% | 0.0200% | 0.0150% |
...
Supreme VIP | 0.0450% | 0.0300% | 0.0300% | 0.0000% | 0.0150% | 0.0050% |
```

Y la extracción determinista que produce la cifra que usa la cuenta
(`a7_cuenta_minima.py`):

```
=== A-4 cerrado — Bybit VIP 0, extraido del cuerpo congelado ===
fuente  = fase0_n9/fuentes_a4/bybit_help_fee.raw
sha256 del fichero = 00d56a3b873202d42bb953fb793ae6621e903773328049e2c67d3c5848fb4135
fila literal: VIP 0 | 0.1000% | 0.1000% | 0.0550% | 0.0200% |
spot  VIP0  taker=0.001000  maker=0.001000
perp  VIP0  taker=0.000550  maker=0.000200
la pata spot cuesta lo mismo maker o taker: True

ida+vuelta taker/taker = 0.310 % del nocional
ida+vuelta mejor caso   = 0.240 % del nocional (maker en perp; el spot no mejora)
```

**El dato de A-4 que no estaba en ninguna parte y que cambia la cuenta:** en Bybit
VIP 0 la pata spot cuesta **0,1000 % sea maker o taker**. Ser paciente en el libro no
abarata la pata larga. Así que el suelo del coste de rotación es
`2 × (0,1000 % + 0,0200 %) = 0,240 %` del nocional, y el escenario realista
(taker en las dos patas, porque abrir las dos a la vez exige cruzar) es **0,310 %**.
La cuenta de abajo usa **0,240 %**, el mejor caso, **a favor del carry**.

**Veredicto del NO-GO de A-4:** «no se pueden verificar en fuente → PARAR». **Sí se
pueden**: Bybit publica las dos patas con VIP 0 explícito, el cuerpo está congelado
con su `sha256`, y Bybit es además uno de los tres exchanges cuyo funding histórico
es público (A-1 §2.1). La §4.1 permite «los tres exchanges, **o la razón de usar
uno**»: la razón de usar Bybit está medida. **El NO-GO no se dispara.** Queda
declarado que Binance no es verificable y que de OKX falta el perp.

### A-5 — Qué pide el exchange para la pata corta, y si el spot sirve de colateral

`fase0_n9/a5_margen.py` y `fase0_n9/a7_cuenta_minima.py`. Todo de API pública.

**Bybit, BTCUSDT, tramos de riesgo** (`/v5/market/risk-limit`, http 200):

```
{"id":1,"symbol":"BTCUSDT","riskLimitValue":"300000","maintenanceMargin":"0.0033","initialMargin":"0.0066","isLowestRisk":1,"maxLeverage":"150.00","mmDeduction":""}
{"id":2,"symbol":"BTCUSDT","riskLimitValue":"2000000","maintenanceMargin":"0.005","initialMargin":"0.01","maxLeverage":"100.00","mmDeduction":"510"}
{"id":9,"symbol":"BTCUSDT","riskLimitValue":"8500000","maintenanceMargin":"0.01","initialMargin":"0.02","maxLeverage":"50.00","mmDeduction":"21010"}
```

**OKX, BTC-USDT-SWAP, tramos de posición** (`/api/v5/public/position-tiers`,
`tdMode=cross`, http 200, 99 tramos):

```
tier          maxSz      imr      mmr  maxLever
   1           1000     0.01    0.004       100
   2           5000    0.015    0.005     66.66
   3          20000     0.02   0.0075        50
   ...
  99        1940000      0.5   0.4875         2

tramo 1: imr=0.01 -> apalancamiento maximo efectivo = 100.0x ; mmr=0.004
```

**Binance, BTCUSDT, de `exchangeInfo`** (http 200): `maintMarginPercent 2.5000`,
`requiredMarginPercent 5.0000`, `liquidationFee 0.012500`, `MIN_NOTIONAL 50`,
`LOT_SIZE minQty 0.001`.

**Mínimos de orden de Bybit** (del cuerpo congelado de `instruments-info`):

```
lotSizeFilter = {"maxOrderQty": "1500.000", "minOrderQty": "0.001", "qtyStep": "0.001",
                 "postOnlyMaxOrderQty": "1500.000", "maxMktOrderQty": "150.000",
                 "minNotionalValue": "5"}
leverageFilter = {"minLeverage": "1", "maxLeverage": "150.00", "leverageStep": "0.01"}
```

**¿Sirve el spot comprado de colateral?** En OKX, **sí**, y está en API pública
(`/api/v5/public/discount-rate-interest-free-quota?ccy=BTC`, http 200):

```
{"amt":"0.23","ccy":"BTC","collateralRestrict":false,"details":[
  {"disCcyEq":"19.6","discountRate":"0.98","liqPenaltyRate":"0.02","maxAmt":"20","minAmt":"0","tier":"1"},
  {"disCcyEq":"24.4875","discountRate":"0.9775","liqPenaltyRate":"0.0225","maxAmt":"25","minAmt":"20","tier":"2"}, ...]}
```

El BTC comprado cuenta como colateral al **98 %** de su valor hasta 20 BTC, con una
penalización de liquidación del **2 %**. Esa es la razón estructural para montar la
operación en una cuenta unificada y no en dos cuentas separadas: el capital
inmovilizado baja casi a una sola pata. **Para Bybit UTA no lo he verificado y no lo
afirmo.**

**Qué significa para el capital inmovilizado, que es el número que decide.** El
margen inicial mínimo del tramo 1 (0,66 % en Bybit, 1 % en OKX) **no es el margen con
el que se opera un carry**: a 150× cualquier salto al alza liquida la pata corta. La
cuenta de abajo usa **m = 10 %** del nocional (apalancamiento 10× en la pata corta),
que con un `mmr` de 0,33 % tolera un movimiento adverso de ~9,7 % antes de
liquidación, y da la tabla completa para m ∈ {5 %, 10 %, 20 %, 50 %}. **La elección de
m es mía, no está medida, y la declaro como supuesto.** Cuál es el m que sobrevive al
peor episodio de 8 h de la historia es exactamente la §4.3, **que no se ejecuta**.

### A-7 — La cuenta mínima, y la referencia que faltaba

`fase0_n9/a7_cuenta_minima.py`, salida literal:

```
=== referencia sin riesgo: tipo de la facilidad de depositos del BCE ===
url  = https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=1&format=csvdata
http=200
FM.D.U2.EUR.4F.KR.DFR.LEV,D,U2,EUR,4F,KR,DFR,LEV,2026-11-02,2.5,A,F,... Deposit facility - date of changes (raw data) - Leve
DFR leido = 2026-11-02 -> 2.500 % anual

=== insumo de B-c — retorno sobre capital con los regimenes medidos en A-2 ===
regimen               bruto %  neto rt-maker % m=0.05  m=0.1   m=0.2   m=0.5
media 7,15 anos        11.455           11.215   10.68   10.20    9.35    7.48
mediana 7,15 anos      10.258           10.018    9.54    9.11    8.35    6.68
ano 2019                7.482            7.242    6.90    6.58    6.03    4.83
ano 2020               17.193           16.953   16.15   15.41   14.13   11.30
ano 2021               30.608           30.368   28.92   27.61   25.31   20.25
ano 2022                4.165            3.925    3.74    3.57    3.27    2.62
ano 2023                7.866            7.626    7.26    6.93    6.35    5.08
ano 2024               11.924           11.684   11.13   10.62    9.74    7.79
ano 2025                5.126            4.886    4.65    4.44    4.07    3.26
ano 2026                3.171            2.931    2.79    2.66    2.44    1.95

=== euros al ano, margen m=0.10, neto de comisiones (orden de magnitud) ===
   capital    media 7,15 anos           ano 2026
      1000                102                 27
     10000               1020                266
    100000              10195               2665

comparacion: el DFR del BCE paga 2.500 % -> 25 / 250 / 2500 EUR al ano, sin riesgo de contraparte cripto
```

Y la distribución de la tarifa, de `a2_fecha_y_conteo_exacto.py`:

```
=== A-2.3 — insumo de B-c: la tarifa medida (bruta, un solo simbolo) ===
  media por 8h            = 0.00010461  -> x3x365 = 11.455 % anual
  mediana por 8h          = 0.00009368  -> x3x365 = 10.258 % anual
  periodos negativos      = 1113 / 7832 = 14.21 %
  minimo observado 8h     = -0.00300000
  maximo observado 8h     = 0.00300000

  ano   n     media 8h      bruto anual %   % periodos negativos
  2019   338   0.00006833      7.482         18.34
  2020  1098   0.00015701     17.193         14.30
  2021  1095   0.00027953     30.608          7.31
  2022  1095   0.00003804      4.165         22.10
  2023  1095   0.00007183      7.866         10.14
  2024  1098   0.00010890     11.924          8.38
  2025  1095   0.00004682      5.126         12.88
  2026   918   0.00002896      3.171         24.84
```

### Resumen del Paso A

| Bloque | Veredicto | Lo que cambia |
|---|---|---|
| §2.1 tres APIs a 200 sin clave | **CONFIRMADO** | Cierra el `[no verificado]` de S2 · B6 |
| §2.2 7,1 años de historia | **CONFIRMADO con corrección** | 7.832 exactas, 0 huecos, desde 2019-09-10 **08:00 UTC** |
| §2.3 «945 perpetuos» | **CONFIRMADO con corrección** | Son **565** perpetuos cripto en TRADING, no 945 |
| §2.4 límite 500 | **CONFIRMADO con corrección** | Con `startTime` son **1000**: 9 peticiones/símbolo, no 16 |
| §2.5 entorno | **CONFIRMADO** | Nada |
| §2.6 régimen actual | **CONFIRMADO** | Su propio aviso era necesario: hoy está 3,5× sobre 2026 |
| §2.7 lo que no prueba | **CONFIRMADO como regla** | Las tres se han materializado |
| A-3 trabajo previo | **NO-GO no se dispara** | Pero aparece el brief N8 → B-e |
| A-4 comisiones | **Verificado en fuente (Bybit)** | La pata spot no mejora con maker |
| A-5 margen y colateral | **Verificado en API pública** | El spot sí es colateral en OKX, al 98 % |

### Desvíos declarados, y por qué

1. **He bajado el histórico de funding de BTCUSDT (9 peticiones, 7.832 filas).** El
   brief prohíbe la descarga de la §4.1 y A-2 exige «el conteo exacto de
   liquidaciones disponibles. Cifra exacta, no estimada». No hay forma de contar
   exactamente sin enumerar. Hecho: **un solo símbolo**, el que la propia §2.2 del
   brief pre-especifica, **sin criba** (así que sin selección), **nada congelado**:
   `fix-fase2/data/funding/` sigue sin existir, no hay CSV, ni `.sha256`, ni
   `.meta.json`. Consumidas **9 de las 2.000** peticiones del tope. Lo que **no** se
   ha hecho es la §4.2: no hay tabla por símbolo y por año natural con *slippage*,
   rebalanceo y coste de margen, ni percentiles, ni peor mes, ni peor trimestre.
2. **He medido la media histórica del funding de ese símbolo.** Es el insumo que la
   objeción obligatoria B-c necesita para no ser una opinión, y el propio NO-GO del
   brief la anticipa («B-c concluye que el funding neto histórico es ~0 → no parar,
   es el resultado»). Medir una tarifa no es backtestear un pronóstico: **no consume
   trial y no mueve `N`**.
3. **He traído el DFR del BCE.** El brief no lo pide en la Fase 0, pero la §4.3 lo usa
   como veto («lo que paga un depósito») sin ninguna cifra, y sin él la cuenta no se
   puede leer. Una petición, endpoint público, sin clave.
4. **La Fase 0 ha durado ~60 minutos, no 30.** Declarado arriba con su causa.

### Correcciones que me he hecho a mí mismo antes de que las encontrara nadie

Cuatro defectos en mis propios scripts, encontrados y corregidos **en el script y en
este documento**:

1. **`sha256` que no era del fichero que etiquetaba.** `a4` y `a5` guardaban el cuerpo
   truncado a 400.000 bytes pero reportaban el `sha256` del cuerpo **completo**, así
   que el hash no verificaba el fichero. Corregido: ahora se registran
   `sha256_cuerpo` y `sha256_fichero` por separado más un `truncado: true/false`, y el
   tope es de 2 MB. Los dos scripts se han vuelto a ejecutar.
2. **Anualización errónea para la mayoría del universo.** La primera versión de
   `b1` anualizaba todo el corte transversal a `×3×365`, pero **465 de 820** símbolos
   liquidan cada **4 horas** y dos cada hora. Corregido a `×(24/intervalo_h)×365`,
   leyendo el intervalo de `/fapi/v1/fundingInfo` símbolo por símbolo.
3. **Medias de bloque dominadas por los topes.** La primera versión de B-a comparaba
   **medias**, y una sola observación (`HOTUSDT`, **−2190 %/año**) movía la media del
   top-50 a −46,6 %. Corregido: ahora se reportan media, **mediana** y media recortada
   al 10 %, y la conclusión se saca de la mediana.
4. **230 contratos falsos en la tabla de la base.** La primera versión de C-1 listaba
   «239 contratos con vencimiento», pero 235 eran `TRADIFI_PERPETUAL` con
   `deliveryDate` en el **año 2100**. Corregido con un horizonte de 400 días: quedan
   **4** contratos con vencimiento real. Y el coste se anualizaba como **una** ida y
   vuelta al año cuando hay que renovar en cada vencimiento: corregido a
   `365/días` rolls al año.

---

## Paso B — Ataque adversarial

Siete objeciones. Las cuatro obligatorias del brief, más tres propias. Severidad y
qué cambia del Alcance en cada una.

### B-c (obligatoria) · Por qué iba a pagar algo tan conocido: paga 0,16 puntos por encima de un depósito en euros — **CRÍTICA**

Esta es la objeción que decide la tarea, y el brief tenía razón en hacerla
obligatoria. Pero no se resuelve con el argumento teórico de la compresión
institucional: se resuelve con la serie, y la serie está medida.

**El bruto, por año natural** (`a2_fecha_y_conteo_exacto.py`, 7.832 observaciones,
0 huecos):

| Año | n | media 8 h | **bruto anual** | % periodos negativos |
|---|---|---|---|---|
| 2019 (desde 10-sep) | 338 | 0,00006833 | 7,482 % | 18,34 % |
| 2020 | 1098 | 0,00015701 | **17,193 %** | 14,30 % |
| 2021 | 1095 | 0,00027953 | **30,608 %** | 7,31 % |
| 2022 | 1095 | 0,00003804 | 4,165 % | 22,10 % |
| 2023 | 1095 | 0,00007183 | 7,866 % | 10,14 % |
| 2024 | 1098 | 0,00010890 | 11,924 % | 8,38 % |
| 2025 | 1095 | 0,00004682 | 5,126 % | 12,88 % |
| **2026** (hasta 02-nov) | 918 | 0,00002896 | **3,171 %** | **24,84 %** |

**La compresión está medida, no supuesta.** El 11,455 % de media de los 7,15 años es
un artefacto de 2020 y 2021 —los dos años de apalancamiento minorista—, que entre
los dos aportan **1.038 €** de cada 1.000 € de los 100.000 € del ejemplo. Quitando
esos dos años, la media de los otros 5,15 años es del orden del **6 %**, y la
tendencia desde 2024 es monótona a la baja: 11,924 → 5,126 → **3,171**. Y el **24,84 %
de periodos negativos de 2026** es la cifra más alta de toda la muestra: no es solo
que pague menos, es que **paga al revés más a menudo que nunca**.

**La cuenta en el régimen vigente, con las comisiones de A-4 y el margen de A-5:**

| | Sobre nocional | Sobre capital (m = 10 %) |
|---|---|---|
| Funding bruto 2026 | 3,171 % | — |
| Ida y vuelta Bybit VIP 0, mejor caso | −0,240 pp | — |
| **Neto** | **2,931 %** | **2,66 %** |
| **DFR del BCE, 2026-11-02** | **2,500 %** | **2,500 %** |
| **Ventaja sobre el activo sin riesgo** | +0,431 pp | **+0,16 pp** |

En euros al año, y es el entregable que el brief pide:

| Capital | Carry 2026 | Depósito BCE | **Diferencia** |
|---|---|---|---|
| 1.000 € | 27 € | 25 € | **+2 €** |
| 10.000 € | 266 € | 250 € | **+16 €** |
| 100.000 € | 2.665 € | 2.500 € | **+165 €** |

**Y esos 165 € son antes de cuatro costes que todavía no están medidos:** *slippage*,
rebalanceo cuando las patas se descuadran, recargas de margen en los episodios
adversos, y el coste de tener el bot y el VPS en pie. Cualquiera de los cuatro se los
come. Con el escenario realista de comisiones (taker en las dos patas, 0,310 % de ida
y vuelta en vez de 0,240 %) la ventaja baja a **+0,10 pp**, es decir **+104 € al año
sobre 100.000 €**.

**Veredicto de B-c, literal:** el funding neto histórico **no** es ~0 —la media de
7,15 años da 10,20 % sobre capital, que es mucho—, pero **el funding neto vigente
es indistinguible de un depósito**. La compresión que el brief plantea como hipótesis
teórica es un hecho medido, y es reciente. **El NO-GO dice «no parar: es el
resultado. Va en la primera línea y el Paso C pasa a ser el contenido principal».
Eso es exactamente lo que se hace.**

**Qué cambia del Alcance.** La §4.2 debe tener una fila más, **obligatoria**: «neto
menos la tasa sin riesgo del periodo». Y el informe de la §4.5 no puede entregar
«euros al año esperados» sin su diferencial contra el activo sin riesgo del mismo
año; el DFR del BCE es descargable sin clave (verificado, http 200), así que no hay
excusa de datos. Y la §4.1 debe fijar el periodo de medición **sabiendo** que incluir
2020-2021 dobla el resultado: el periodo «completo y sin holdout» que la §4.1
prescribe es defendible, pero entonces el informe tiene que dar **también** el
régimen de los últimos 24 meses, porque es el que se va a operar.

### B-b (obligatoria) · El modo de muerte: la cola de la tarifa está acotada por regla, la de la operación no, y ninguna métrica del expediente la mide — **CRÍTICA**

**Primera mitad, y es un hallazgo a favor del carry.** El mínimo y el máximo de 8 h
observados en los 7.832 periodos son **exactamente −0,00300000 y +0,00300000**. No es
casualidad: es el tope de regla del exchange (`fase0_n9/b1_transversal_y_basis.py`):

```
BTCUSDT = {"symbol": "BTCUSDT", "adjustedFundingRateCap": "0.00300",
           "adjustedFundingRateFloor": "-0.00300", "fundingIntervalHours": 8,
           "disclaimer": true, "updateTime": null}
```

La cola de **la tarifa** está acotada administrativamente a ±0,3 % por 8 h, o sea
±328 % anualizado. Eso contradice en parte la premisa de curtosis 150-400 que
N5 · B-c usa para decir que las colas suben el listón: en la tarifa de BTCUSDT las
colas están **recortadas por el exchange**. Para los 723 símbolos con tope `0.02`
(±2 % por intervalo) la cota es mucho más laxa, pero sigue siendo una cota.

**Segunda mitad, y es la que importa: lo que no está acotado no está en la serie.**
El P&L de un carry delta-neutral no es la serie de funding. Es la serie de funding
**condicionada a que la posición siga viva**, y los tres sucesos que la matan no
aparecen en ella:

1. **Liquidación de la pata corta.** Con `mmr = 0,0033` (Bybit tramo 1) y margen del
   10 %, un salto al alza del ~9,7 % en el perp sin que llegue a tiempo la recarga
   deja la pata corta liquidada y al operador largo en spot y desnudo. Y la pata
   larga, que sube, **no está en la cuenta de margen de la corta** salvo en cuenta
   unificada: es justo lo que el `discountRate 0.98` de OKX resuelve (A-5), y por eso
   el montaje importa tanto como la tarifa.
2. **Desanclaje perp/spot.** El carry supone que las dos patas se cancelan. Cuando el
   perp se desancla del índice, la cancelación falla precisamente en el momento en que
   el margen está más tenso.
3. **El exchange.** Rehipotecación, cambio de reglas, retiradas congeladas. Es una
   pérdida total del capital de las dos patas, con una probabilidad que no es
   estimable con datos de precios.

**¿Qué métrica del expediente captura esto? Ninguna.** Y no es una limitación de
calibración, es estructural: el DSR es
`PSR(SR₀)` sobre la distribución de los retornos **observados**, y los tres sucesos
son eventos que terminan la serie en vez de aportarle una observación. Una
distribución estimada sobre trayectorias supervivientes no puede contener la
probabilidad de no sobrevivir. El `t > 3` tiene el mismo problema. El `max_dd_pct`
que el expediente usa tampoco: mide la peor racha **dentro** de la muestra, no la
ruina.

**Lo que sí lo capturaría, y hay que escribirlo antes de medir nada:** no una
métrica, un **escenario**. (i) el margen que habría hecho falta para sobrevivir al
peor movimiento adverso de 8 h de la historia descargada, con el nocional real
—que es la §4.3 y **no se ejecuta aquí**—; y (ii) una pérdida de contraparte
declarada como supuesto: «un p % anual de probabilidad de perder el 100 % del capital
en el exchange», con el p puesto por Pablo, no por mí. Sin (ii) la cuenta de la §4.2
está sobrestimada por construcción, y con los 165 € de ventaja de B-c bastaría un
p del **0,17 %** anual para borrarla entera.

**Qué cambia del Alcance.** La §4.3 pasa de ser el tercer paso a ser **condición de
la §4.2**: mientras no esté el margen de supervivencia, el denominador «capital total
inmovilizado» de la §4.2 es un supuesto, no una medida — y es exactamente el
denominador del número que se entrega. Y la §4.4 necesita una línea más en los vetos:
el **límite de capital por exchange**, que es la única defensa contra (3).

### B-a (obligatoria) · Los «945 símbolos»: son 565, y la criba de liquidez no cuela funding por detrás — selecciona *contra* él — **ALTA**

Dos cosas, y la primera es un error de hecho del brief ya cubierto en A-1 · §2.3:
**no hay 945 perpetuos**. Hay **565** perpetuos cripto en `TRADING` (703
`PERPETUAL` en total, 138 en `SETTLING`), más 235 perpetuos de acciones tokenizadas y
4 trimestrales. La objeción sigue en pie —565 es una máquina de selección múltiple—
pero la cifra que la cuantifica estaba inflada un **67 %**.

**La pregunta que el brief hace, medida.** ¿Están el funding alto y la liquidez
correlacionados, de modo que una criba «solo de liquidez» cuele el funding por la
puerta de atrás? Corte transversal del 2026-11-02, 565 perpetuos con funding y
volumen, anualizando **con el intervalo real de cada símbolo**
(`b1_transversal_y_basis.py`):

```
pearson(funding anual, log10 volumen)   = -0.1184
spearman(funding anual, volumen)        = -0.0757

bloque        media %  mediana %  recort10 % | resto media  resto mediana  resto recort10
top-10         14.114     10.950       9.438 |      -2.101         10.950           9.460
top-20         -5.237     10.950       9.459 |      -1.689         10.950           9.460
top-50        -46.586     10.950       7.291 |       2.533         10.950           9.583
top-100       -42.480     10.950       7.166 |       6.931         10.950           9.741

diferencia top-resto en MEDIANA (pp anuales), que es la robusta:
  top10    +0.000 pp
  top20    +0.000 pp
  top50    +0.000 pp
  top100   +0.000 pp

extremos que descolocan la media: HOTUSDT -2190.0 %/ano (intervalo 8 h) ;
                                  ARIAUSDT +228.0 %/ano (intervalo 4 h)
```

**Tres lecturas, y las tres importan.**

1. **En la mediana, la diferencia es exactamente cero**, en los cuatro bloques. No
   porque no haya señal, sino porque la mediana de los 565 está **pinchada en
   10,950 %** —el valor por defecto `0.0001` por periodo— tanto para símbolos de 4 h
   como de 8 h. La mediana no discrimina aquí: es un dato sobre la administración del
   exchange, no sobre el mercado.
2. **En la media recortada al 10 %, que sí discrimina, el signo va al contrario de lo
   que el brief teme:** el top-50 por volumen tiene **7,291 %** contra **9,583 %** del
   resto, y el top-100 **7,166 %** contra **9,741 %**. Los símbolos líquidos pagan
   **2,3-2,6 puntos menos** de funding. Económicamente es lo que cabe esperar y es la
   otra cara de B-c: **la compresión institucional está concentrada exactamente donde
   hay liquidez para entrar con tamaño**. Así que la criba por liquidez no infla el
   funding: lo **recorta**, y lo recorta en la dirección que empeora la cuenta.
3. **La media cruda es inservible como estadístico aquí.** `HOTUSDT` a −2190 %
   anualizado mueve la media del top-50 a −46,6 %. Cualquier cifra de «funding medio»
   calculada como media sobre un corte transversal con topes de ±2 % por intervalo es
   una cifra sobre uno o dos símbolos.

**Honestidad sobre el alcance de esto:** es **un solo corte transversal de un
instante**. No acota nada sobre la relación en el tiempo, que es la que importaría
para la criba. Lo que sí hace es quitar la base a la versión fuerte de la objeción
(«la criba cuela funding alto») y dejar en pie la débil («la criba no es neutral»).

**Qué cambia del Alcance.** Tres cosas concretas en la §4.1: (i) el universo se
describe como **565 perpetuos cripto**, excluyendo explícitamente
`TRADIFI_PERPETUAL`; (ii) la criba se pre-registra solo con **volumen y antigüedad**,
se commitea antes de bajar nada —esto ya lo exige el brief y hay que cumplirlo—, y
(iii) se añade una **comprobación falsable** que no estaba: una vez bajado el panel,
medir la correlación de Spearman funding-liquidez **en la serie temporal** y
publicarla, pase lo que pase. Si sale positiva y material, la criba está contaminada
y la cuenta no vale; si sale como hoy, queda registrado que la criba juega en contra.

### B-d (obligatoria) · La supervivencia del universo: la criba que el brief propone tiene tres símbolos elegibles, y el sesgo sí es parcialmente acotable — **ALTA**

**El hallazgo que rompe la §4.1 tal como está escrita.** El brief propone como
ejemplo de criba «los 20 de mayor volumen a 24 h **con historia completa desde
2019-09-10** y cotizados en los tres exchanges». Medido
(`b1_transversal_y_basis.py`):

```
=== B-d — edad del universo de perpetuos vivos ===
  vivos hoy que ya existian antes de 2020-01-01:    3 de 565 (  0.5 %)
  vivos hoy que ya existian antes de 2021-01-01:   56 de 565 (  9.9 %)
  vivos hoy que ya existian antes de 2022-01-01:   89 de 565 ( 15.8 %)
  vivos hoy que ya existian antes de 2023-01-01:  105 de 565 ( 18.6 %)
  vivos hoy que ya existian antes de 2024-01-01:  172 de 565 ( 30.4 %)
  vivos hoy que ya existian antes de 2025-01-01:  291 de 565 ( 51.5 %)
  vivos hoy que ya existian antes de 2026-01-01:  506 de 565 ( 89.6 %)

  los 3 anteriores a 2020-01-01: ['BCHUSDT', 'BTCUSDT', 'ETHUSDT']
```

**El universo elegible de la criba del brief es de tres símbolos: BCHUSDT, BTCUSDT y
ETHUSDT.** No 20. Y con el corte en 2021-01-01 son **56**. La §4.1 hay que reescribirla
o la descarga no tiene a quién bajar.

**La pregunta del brief —«¿cuánto sesga?»— y la respuesta, que no es «no se
puede».** Los 565 son los vivos; los delistados no están en `exchangeInfo`. Pero el
funding **sobrevive al delistado** (`b2_supervivencia_acotable.py`):

```
exchangeInfo  = 942 simbolos ; estados = {'TRADING': 804, 'SETTLING': 137, 'PENDING_TRADING': 1}
en premiumIndex y NO en exchangeInfo = 3 -> ['EOSUSDT', 'FRONTUSDT', 'MATICUSDT']

=== B-d.2 — sobrevive el historico de funding al delistado? ===
  EOSUSDT                http=200 filas=3  [{"symbol":"EOSUSDT","fundingTime":1793577600005,"fundingRate":"0.00010000", ...
  FRONTUSDT              http=200 filas=3  [{"symbol":"FRONTUSDT","fundingTime":1793577600005,"fundingRate":"0.00010000", ...
  MATICUSDT              http=200 filas=3  [{"symbol":"MATICUSDT","fundingTime":1793577600005,"fundingRate":"0.00010000", ...

=== B-d.3 — un simbolo que ya no cotiza pero esta en exchangeInfo ===
simbolos con status != TRADING: 138
  1000000BOBUSDT         status=SETTLING  http=200 filas=3  [{"symbol":"1000000BOBUSDT","fundingTime":1791158400002,"fundingRate":"0.01054137", ...
  1000WHYUSDT            status=SETTLING  http=200 filas=3  [{"symbol":"1000WHYUSDT","fundingTime":1773705600000,"fundingRate":"0.00019659", ...
  1000XUSDT              status=SETTLING  http=200 filas=3  [{"symbol":"1000XUSDT","fundingTime":1763078400000,"fundingRate":"-0.00014703", ...
```

**Tres consecuencias.**

1. **El sesgo es parcialmente acotable hoy:** hay **137 símbolos en `SETTLING`** cuyo
   funding se puede bajar sin clave, más los que ya salieron de `exchangeInfo` y
   siguen respondiendo (`MATICUSDT` es el caso evidente). Lo que **no** es acotable
   retroactivamente es la lista completa de delistados de 2019-2026: haría falta un
   histórico de snapshots que no existe, o los anuncios de delistado del exchange.
2. **La dirección del sesgo es la contraria de la que el brief supone, y es
   importante.** `1000000BOBUSDT` estaba pagando **+0,01054137 por 8 h** —**+1,05 %
   cada 8 horas**, unos **+1.154 % anualizados**— cuando lo estaban delistando. Los
   perpetuos que mueren pagaban funding **extremo y positivo**, o sea **a favor** de
   un corto en perp. Excluirlos no infla la cuenta del carry: la **deprime**. El sesgo
   de supervivencia del carry apunta al revés que el del spot que midió
   `portfolio_supervivencia.py`.
3. **Y aun así no es dinero capturable.** Ese +1.154 % estaba en un símbolo sin libro,
   con el tope de funding al máximo y un delistado forzoso por delante: la posición se
   cierra cuando lo decide el exchange, al precio que haya. Es el mismo patrón de
   «retorno enorme en el sitio donde no cabe el capital» que B-a mide en el corte
   transversal.

**Qué cambia del Alcance.** La §4.1 cambia su criterio de antigüedad —no hay 20
símbolos con historia desde 2019— y **añade** los 137 `SETTLING` al panel como
contrapeso explícito del sesgo, declarando que el panel resultante es de vivos más
moribundos y no de delistados históricos. Y la §4.2 reporta la cuenta **con y sin**
ellos, que es la única manera de que el sesgo tenga un número en vez de un párrafo.

### B-e (propia) · N8 y N9 son dos briefs vivos de la misma familia escritos con 14 minutos de diferencia, y N9 no lista N8 — **ALTA**

El error de N7 fue pedir trabajo **ya hecho**. Este es el mismo error girado: pedir
trabajo **ya encargado**, y por partida doble.

Lo medido en A-3:

| | N8 | N9 |
|---|---|---|
| Fichero | `tarea-nube-N8-carry-de-funding-umbral-de-viabilidad-y-contrapropuesta.md` | `tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md` |
| Commit | `05d1ebf`, **2026-11-02 18:36:34** | `0f77f9e`, **2026-11-02 18:50** |
| Líneas | 361 | 409 |
| Dónde se ejecuta | la **nube** | el **VPS** |
| Rama | `nube/n8-carry-funding` — **no existe** | `vps/n9-carry-cuenta-real` |
| §7 | toda `[pendiente]` | toda `[pendiente]` |
| Registro némesis | **no existe** | este |

**Los solapamientos no son menores, son el núcleo.** El Paso C de N8 y el Paso C de
N9 piden **lo mismo**: una a tres candidatas, mecanismo en una frase, `N = N_vigente+1`,
qué la mata rápido, por qué es mejor que el carry, ordenadas por coste de descarte.
Las objeciones obligatorias B-b y B-c de N8 son, palabra por palabra en el fondo, las
B-b y B-c de N9. Y las cuatro lecturas previas obligatorias son **idénticas**.

**Y hay una incoherencia de asignación.** N8 está asignada a la nube, que **no tiene
red para mercado** (0 de 10 fuentes, medido dos veces: N5 · A-1 y N7 · A-7), algo que
el propio brief de N8 reconoce en su §2.5. Su §4.3 es «la especificación de datos
**para el VPS**: qué serie exacta, de qué proveedor, con qué granularidad». Es decir:
**N8 existe para redactar el brief de la §4.1 de N9**, y N9 se escribió 14 minutos
después sin esperarla y sin citarla. Si N8 se lanza ahora, producirá una segunda
Fase 0 sobre la misma familia, con una contrapropuesta posiblemente distinta a la de
este registro, y el expediente tendrá dos veredictos sobre el carry.

**Lo que N8 sí tiene y N9 no, y conviene no perder:** su §2.3 fija por escrito que
`N` arranca en **≥ 16** por la regla de S2 con el recuento de N6, y su **B-a** manda
medir el `T_eff` del funding **contra las colas y contra el AR(1)**, que es el único
sitio del expediente donde está apuntado que la ganancia de `T` de las 3
observaciones diarias puede no existir. Eso no está en N9 y es trabajo útil que no
duplica nada de aquí.

**Qué cambia del Alcance, y es decisión de Pablo, no mía.** Tres opciones, en orden
de lo que yo recomendaría:

1. **Marcar N8 como superada por N9 en su §7 y no lanzarla.** Su Paso C ya está
   contestado por este registro y su §4.3 ya está contestada por la §4.1 de N9.
2. **Reducir N8 a su §4.1 y §4.2 analíticas** —el umbral paramétrico y la tabla de
   sensibilidad, incluido el `T_eff` con AR(1)—, borrando su Paso C y su §4.3. Eso no
   duplica nada y responde lo único que esta tarea ha dejado sin tocar a propósito.
3. Lanzarla tal cual y aceptar dos Fases 0 sobre la misma familia. **No lo
   recomiendo.**

### B-f (propia) · La unidad del entregable está mal elegida, y eso es lo que oculta el resultado — **MEDIA**

El brief acierta en pedir «un número en euros al año» en vez de un Sharpe: es la
corrección correcta después de ocho tareas de métricas. Pero se queda a un paso.
**«Euros al año» no es una unidad decidible sin la alternativa.** 2,66 % parece un
retorno; 2,66 % contra 2,500 % es un empate técnico con riesgo de contraparte
añadido. Y la alternativa aparece **una sola vez** en las 409 líneas del brief, en la
§4.3, sin cifra: «lo que paga un depósito».

La diferencia no es retórica. Con la unidad del brief, la respuesta de esta tarea
sería «el carry da 2.665 € al año sobre 100.000 €», que suena a negocio. Con la
unidad corregida es «**165 € al año sobre 100.000 €**, antes de cuatro costes sin
medir», que es la verdad.

**Qué cambia del Alcance.** La §4.2 añade una fila obligatoria, «menos la tasa sin
riesgo del periodo», y la §4.5 entrega las tres líneas finales **en diferencial**, no
en bruto. La serie está disponible sin clave y verificada:
`https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV`, http 200,
2026-11-02 → **2,5**.

### B-g (propia) · 465 de 820 símbolos liquidan cada 4 horas, no cada 8, y todo el brief está escrito sobre «3 al día» — **MEDIA**

```
entradas en fundingInfo = 820
intervalos (h -> n)     = {4: 465, 8: 353, 1: 2}
topes (tope -> n), top6 = {'0.02000000': 723, '0.01000000': 22, '0.00375': 22,
                           '0.01875': 15, '0.00500000': 11, '0.0075': 7}
```

**La mayoría del universo no liquida cada 8 horas.** El brief anualiza en tres sitios
con `×3×365` (§2.2, §2.6 y el conteo de observaciones), y eso solo vale para los 353
símbolos de 8 h. Para los 465 de 4 h el factor es `×6×365`, y para 2 símbolos
`×24×365`. Es un error de **factor 2** en la mitad larga del universo, en las dos
direcciones a la vez: infla el funding anualizado de un símbolo de 4 h si se aplica
su tasa con el factor 3, y **subestima su `T`** si se cuentan 3 observaciones diarias
donde hay 6.

Lo encontré porque mi propio primer `b1` tenía el mismo defecto, y está corregido en
el script (ver «Correcciones que me he hecho a mí mismo», punto 2).

**Qué cambia del Alcance.** La §4.1 añade `fundingIntervalHours` a los campos
obligatorios del `.meta.json` de cada símbolo, y la §4.2 anualiza **por símbolo** con
su intervalo, nunca con una constante. Y para N8, si se mantiene: su única palanca es
`T`, y para 465 símbolos `T` es el **doble** de lo que su §1 supone — lo que hace su
cálculo más interesante, no menos.

### Resumen del Paso B

| Objeción | Severidad | Qué cambia del Alcance |
|---|---|---|
| **B-c** · el carry vigente paga 0,16 pp sobre un depósito | **CRÍTICA** | §4.2 añade la fila «menos tasa sin riesgo»; §4.5 entrega en diferencial; §4.1 reporta también el régimen de 24 meses |
| **B-b** · el modo de muerte no está en ninguna métrica del expediente | **CRÍTICA** | §4.3 pasa a ser condición de la §4.2; §4.4 añade límite de capital por exchange; hace falta un escenario de contraparte con `p` puesto por Pablo |
| **B-a** · son 565, no 945, y la criba selecciona *contra* el funding | **ALTA** | §4.1 excluye `TRADIFI_PERPETUAL` y añade una comprobación falsable de independencia criba-funding, publicada pase lo que pase |
| **B-d** · la criba propuesta tiene 3 símbolos elegibles; el sesgo sí es acotable | **ALTA** | §4.1 cambia el criterio de antigüedad y añade los 137 `SETTLING`; §4.2 reporta con y sin ellos |
| **B-e** · N8 y N9 son dos briefs vivos de la misma familia | **ALTA** | Decisión de Pablo: marcar N8 como superada, reducirla a su umbral analítico, o aceptar dos Fases 0 |
| **B-f** · la unidad «euros al año» oculta el resultado sin la alternativa | **MEDIA** | §4.2 y §4.5 en diferencial contra el DFR |
| **B-g** · 465 de 820 símbolos liquidan cada 4 h | **MEDIA** | `fundingIntervalHours` obligatorio en el `.meta.json`; anualización por símbolo |

Ninguna objeción retirada. Dos de las mías (B-f, B-g) son MEDIAS y lo digo: no
cambian el veredicto, cambian cómo se escribe la §4.

### Lo que busqué y no encontré, declarado

- **Un argumento para que el carry pague más de lo medido.** Lo busqué por tres
  vías: que la media de 7,15 años fuera la buena y 2026 una anomalía (no se sostiene:
  la caída es monótona desde 2024 y 2026 tiene el récord de periodos negativos); que
  el maker abaratara la pata spot (no: 0,1000 % maker y taker, A-4); y que la cuenta
  unificada bajara el capital inmovilizado lo suficiente (ayuda —98 % de colateral en
  OKX— pero sube el retorno sobre capital como mucho de 2,66 % a 2,93 %, y el DFR
  sigue a 2,50 %).
- **Comisiones de Binance en fuente.** Ocho URLs probadas, ninguna sirve sin clave.
- **El perp de OKX en fuente.** La pestaña `Futures` no viene en el cuerpo servido.
- **Una cota retroactiva del sesgo de supervivencia.** Hoy sí (137 símbolos),
  retroactivamente no con estas APIs.
- **`sharpe_min_dsr` en `rigor_estadistico.py`.** No está ahí: está en
  `potencia_fase_b.py:34`. La lectura previa 4 del brief apunta al módulo equivocado
  para esa función, aunque sí es el módulo correcto para `dsr`, `psr`,
  `ar1_effective_n` y `block_bootstrap_ci`.

---

## Paso C — Contrapropuesta

B-c no tumba el carry del todo: lo deja empatado con un depósito en euros. Así que la
contrapropuesta no es «esto no vale», es **«hay una forma mejor de cobrar lo mismo, y
dos cosas distintas que valen más»**.

Tres candidatas, **ordenadas por coste de descartarlas**, de la más barata a la más
cara. **Ninguna se evalúa aquí**: proponer no es backtestear, y en el momento en que
se mida el Sharpe de una señal se consume un trial y sube `N` para todo el
expediente. Las cifras en euros son **órdenes de magnitud declarados como tales**,
salvo las de C-1, que están **medidas hoy**.

### C-1 · La base de los futuros con vencimiento, en lugar del funding del perpetuo

| Campo | |
|---|---|
| **Mecanismo** | Un futuro con vencimiento **converge al spot por contrato**, así que comprar spot y vender el futuro fija al entrar un rendimiento **conocido**; no se cobra una tarifa flotante que se descubre después, se compra un descuento cierto |
| **Predictiva** | **No**, y además **no necesita media histórica**: el número se lee en pantalla antes de arriesgar nada |
| **Datos** | `fapi/v1/premiumIndex` (`markPrice`, `indexPrice`) + `fapi/v1/exchangeInfo` (`deliveryDate`, `contractType`) para el presente, y `fapi/v1/klines?symbol=BTCUSDT_YYMMDD` para el histórico. **Sin clave desde el VPS, verificado hoy** |
| **`N` que le toca** | **16** (`N_vigente + 1`, regla de S2 con el recuento de N6). Pero **medir la base es medir un precio, no backtestear un pronóstico**: no consume trial, igual que el funding. `N = 16` solo entra si se mide una regla de *cuándo* entrar |
| **Qué la mata rápido** | Bajar las velas de los trimestrales **ya vencidos** y calcular la base anualizada a 90-140 días de vencimiento, día a día, de 2024 a hoy. **Si el percentil 25 cae por debajo del DFR, está muerta.** ~50 peticiones, **~2 horas** |
| **Por qué es mejor que el carry** | **4,949 % neto contra 2,931 %** (medido hoy, abajo), y sobre todo: **elimina la inferencia**. No hay `N`, ni `V`, ni `T`, ni DSR, ni holdout, porque no se estima una esperanza: se lee un precio de entrega |
| **Euros al año** (m = 10 %) | **45 € / 450 € / 4.499 €** con 1.000, 10.000 y 100.000 €. Contra el DFR: **+20 € / +200 € / +1.999 €** |

**La medición, hoy** (`b1_transversal_y_basis.py`, los únicos **4** contratos con
vencimiento real que existen):

```
symbol                      venc    dias         mark        index   base %   anual %  rolls/ano  coste/ano   neto %   vs DFR
BTCUSDT_261225        2026-12-25   52.49     77564.04     76932.26    0.821     5.710       6.95      1.669    4.042   +1.542
BTCUSDT_270326        2027-03-26  143.49     78613.69     76932.26    2.186     5.560       2.54      0.610    4.949   +2.449
ETHUSDT_270326        2027-03-26  143.49      2290.23      2252.45    1.677     4.267       2.54      0.610    3.657   +1.157
ETHUSDT_261225        2026-12-25   52.49      2265.50      2252.45    0.579     4.028       6.95      1.669    2.359   -0.141
```

Y la verificación de que el histórico que necesita su prueba de muerte **se baja sin
clave, incluidos contratos vencidos** (`c1_datos_de_la_candidata.py`):

```
symbol              http  filas  primera/ultima vela
BTCUSDT_261225       200      5  t0=1793232000000 cierre0=78633.6 tN=1793577600000 cierreN=77635.7
BTCUSDT_270326       200      5  t0=1793232000000 cierre0=79619.4 tN=1793577600000 cierreN=78691.5
BTCUSDT_260327       200      5  t0=1775952000000 cierre0=69260.0 tN=1776297600000 cierreN=69260.0
BTCUSDT_260626       200      5  t0=1782086400000 cierre0=64033.7 tN=1782432000000 cierreN=59681.2
BTCUSDT_260925       200      5  t0=1789948800000 cierre0=86645.3 tN=1790294400000 cierreN=83981.8
BTCUSDT_251226       200      5  t0=1768521600000 cierre0=88721.0 tN=1768867200000 cierreN=88721.0
ETHUSDT_260925       200      5  t0=1789948800000 cierre0=2778.96 tN=1790294400000 cierreN=2673.50
```

Los cuatro contratos **ya vencidos** (`260327`, `260626`, `260925`, `251226`)
devuelven velas: la prueba de muerte es ejecutable sin clave y sin cuenta.

**Lo que NO mejora, y hay que decirlo.** El modo de muerte es **idéntico** al del
carry: liquidación de la pata corta en un salto al alza. B-b se le aplica entera. Y
tiene dos debilidades propias: **solo existen 4 contratos** (BTC y ETH), así que no
hay universo que cribar —lo cual es a la vez su ventaja estadística y su techo de
capacidad—, y **el vencimiento cercano de ETH ya está por debajo del DFR** (−0,141
pp), lo que demuestra que esto no es una renta garantizada: es un precio que unos días
compensa y otros no. El contrato que paga es el **lejano**, porque la base se reparte
entre menos renovaciones: 2,54 rolls al año a 0,240 pp contra 6,95.

### C-2 · Dejar de buscar un retorno y abaratar el que ya se tiene

| Campo | |
|---|---|
| **Mecanismo** | El expediente **ya posee** un activo de retorno esperado positivo —el panel de 10, con Sharpe de B&H **1,164** y retorno **132.831 %** (N7)— cuyo problema no es el retorno sino el **−88,96 %** de *drawdown*. Convertir *drawdown* en supervivencia vale más euros que cualquier alfa que estas ocho tareas han buscado, porque el retorno **ya está** y lo que falta es poder aguantarlo sin cerrar |
| **Predictiva** | **Parcialmente, y es justo la excepción que merece defenderse**: un objetivo de volatilidad predice **volatilidad**, no dirección. La volatilidad tiene memoria y la dirección no, y las siete tareas fracasadas apostaron todas a la dirección |
| **Datos** | **Ninguno nuevo.** `data/multi/` ya está en el repo, congelado con `sha256`. **Cero peticiones, cero red, cero descarga** |
| **`N` que le toca** | **16**, y **esta sí consume un trial** y sube `N` para todo el expediente. Es su coste real y por eso no va primera |
| **Qué la mata rápido** | Un objetivo de volatilidad a 30 días sobre el panel congelado, con el split 60/40 **ya pre-registrado**: si no mejora el Calmar fuera de muestra, muerta. **~4 horas**, 0 peticiones. El coste no son las horas: es el trial |
| **Por qué es mejor que el carry** | No necesita exchange de derivados, **no añade riesgo de contraparte**, no tiene modo de muerte por liquidación, no tiene que cribar 565 símbolos, y los datos están **ya auditados** por este mismo expediente |
| **Euros al año** | **No añade renta anual y no lo voy a presentar como si lo hiciera.** Convierte pérdida en capital conservado: la diferencia entre un *drawdown* máximo de **−88,96 %** y uno de **−26,9 %** son **≈620 € / 6.200 € / 62.000 €** de capital que no se pierde en el peor episodio, sobre 1.000, 10.000 y 100.000 €. Es capital conservado, no renta, y así hay que leerlo |

**Precedente en el expediente, que es lo que la hace fuerte y no una ocurrencia:**
S2 · **B8 (MEDIO)** ya identificó «la alternativa descartada sin justificar:
reorientar a control de riesgo», y encontró que la §3.5 de S2 la hacía imposible de
recomendar por una razón administrativa. Esta candidata es esa, dos meses después,
con el dato de N7 que entonces no existía: **el B&H del panel gana a Fase B en Sharpe
y en retorno, y pierde por un factor de 3,3 en *drawdown*.** Ahí está el hueco.

### C-3 · La dispersión transversal del funding, no su nivel

| Campo | |
|---|---|
| **Mecanismo** | El capital institucional comprime el **nivel** del funding allí donde puede entrar con tamaño —y B-a lo mide: el top-100 por volumen paga **2,6 puntos menos** que el resto—, pero **no comprime la cola** de los 565 perpetuos, donde no cabe. Un *long-short* en funding (corto el perp de funding más alto, largo el de más negativo, las dos patas delta-neutras) cobra el **diferencial** y es neutral a la compresión del nivel |
| **Predictiva** | No, pero **es una máquina de selección**: B-a se le aplica entera y con más fuerza que al carry, porque la regla de selección *es* la estrategia |
| **Datos** | `fundingRate` por símbolo (1000 filas/petición con `startTime`, verificado) + `ticker/24hr` + `fundingInfo` para el intervalo real. Sin clave. **~9 peticiones × 56 símbolos** con historia desde 2021 ≈ **500 peticiones**, dentro del tope de 2.000 |
| **`N` que le toca** | **16**, y **aquí el listón sí aplica de verdad**, porque hay una regla de selección transversal que se optimiza. Es la candidata más expuesta al DSR de las tres |
| **Qué la mata rápido** | Mediana del diferencial decil-superior menos decil-inferior sobre los 56 símbolos con historia desde 2021, **neta de la rotación de dos patas alt**. **Si el diferencial mediano no supera 4× el coste de rotación, muerta.** ~5 horas |
| **Por qué es mejor que el carry** | El carry cobra el nivel, comprimido a **3,171 %**; la dispersión no está comprimida (hoy, extremos de **−2190 %** y **+228 %** anualizados en el corte transversal, con topes de regla a ±2 % por intervalo) |
| **Euros al año** | **Binario, y con su aritmética delante**: la rotación de dos patas alt cuesta ≥ **0,310 %** por vuelta, y a rotación mensual son **3,72 %** anuales de coste. Así que el diferencial bruto tiene que superar **~8 %** anuales para dejar **~4 %** netos. O da del orden de **40 € / 400 € / 4.000 €**, o **no da nada**. La prueba de 5 horas resuelve cuál de las dos |

**Peor que el carry en tres cosas, y las digo:** dos patas *alt* ilíquidas en vez de
una de BTC; **137 símbolos en `SETTLING` ahora mismo** (B-d), o sea que el riesgo de
delistado forzoso con la posición abierta no es hipotético; y es la única de las tres
que es una regla de selección, con todo lo que eso le cuesta en el listón.

### Las tres juntas, y el orden

| | Horas | Peticiones | ¿Consume trial? | Euros/año (100.000 €) | Contra el DFR |
|---|---|---|---|---|---|
| **C-1** base de futuro con vencimiento | ~2 | ~50 | **No** | **4.499 €** | **+1.999 €** |
| **C-2** overlay de riesgo sobre el beta | ~4 | 0 | **Sí** | 62.000 € de capital **conservado**, no renta | n/a |
| **C-3** dispersión transversal del funding | ~5 | ~500 | **Sí** | 4.000 € **o nada** | +1.500 € o −2.500 € |
| *(referencia)* carry de funding, régimen 2026 | — | — | No | 2.665 € | **+165 €** |
| *(referencia)* depósito en euros al DFR | 0 | 0 | No | 2.500 € | 0 |

**El orden es por coste de descartarlas, no por retorno esperado**, como manda el
brief: C-1 cuesta 2 horas y ningún trial; C-2 cuesta 4 horas y un trial; C-3 cuesta 5
horas, 500 peticiones y un trial. Si el orden fuera por retorno, C-2 iría primera por
los 62.000 €, y sería la decisión equivocada: es la que compromete el `N` del
expediente con el experimento más caro de deshacer.

**Y la recomendación, que el brief no pide pero la decisión necesita:** empezar por
**C-1**, porque dos horas y cincuenta peticiones compran la respuesta a la pregunta
que ocho tareas no han contestado —*¿hay en este mercado un rendimiento conocido de
antemano que supere al sin riesgo?*— **sin gastar un solo trial**. Si C-1 sobrevive,
el carry de funding de la §4 de esta tarea queda subsumido: es la misma operación con
peor instrumento.

---

## Veredicto de la Fase 0 y estado de los seis NO-GO

| Condición del brief | Estado | Por qué |
|---|---|---|
| A-3 encuentra trabajo de funding **ya hecho** | **NO se dispara** | Cero `.py`, cero CSV, cero JSON, cero registro en las diez ramas, en `/opt/trading-bot` y en `/root/trading-bot-fix-fase2`. Lo que hay es un brief **sin ejecutar** (N8): trabajo encargado, no hecho → va a B-e |
| Algún hecho de la §2 sale **REFUTADO** | **NO se dispara** | 3 CONFIRMADOS y 4 CONFIRMADOS con corrección. Los comandos de la §2 reproducen todos; lo que se corrige son las estimaciones que el propio brief marca con `~` y manda sustituir, y la etiqueta «perpetuos» de la §2.3 |
| Las APIs de 2.1 **ya no responden 200** | **NO se dispara** | Las tres a 200, sin credenciales, con los cuerpos pegados en A-1 |
| **A-4 o A-5** no se pueden verificar en fuente | **NO se dispara** | A-4 verificado en fuente para **Bybit**, VIP 0, las dos patas, con el cuerpo congelado y su `sha256`. A-5 verificado en **API pública** en Bybit, OKX y Binance. Declarado: Binance no da comisiones sin clave y de OKX falta el perp |
| B-c concluye que el funding neto histórico es **~0** | **Se cumple en su variante de régimen, y por diseño no para** | El histórico de 7,15 años **no** es ~0 (10,20 % sobre capital). El **vigente sí es indistinguible de un depósito**: +0,16 pp. Va en la primera línea y el Paso C es el contenido principal |
| El Paso C no da ni una candidata ni defiende el carry | **NO se dispara** | Tres candidatas, con mecanismo, datos, `N`, prueba de muerte con horas, comparación con el carry y euros. C-1 con cifras **medidas hoy** |

**Ningún NO-GO obliga a parar. La Fase 0 se cierra completa.**

**Lo que esta tarea deja decidido, y no necesita a nadie más:**

1. El funding histórico de los perpetuos es **público, gratuito y descargable sin
   clave desde el VPS**. Cierra el `[no verificado]` de S2 · B6 y abre la familia.
2. BTCUSDT tiene **7.832** observaciones de funding sin un hueco, de 2019-09-10
   08:00 UTC a hoy.
3. Las comisiones que la cuenta necesita son **0,1000 %** en spot (maker y taker) y
   **0,0550 % / 0,0200 %** en perp, Bybit VIP 0, de fuente congelada.
4. El spot comprado **sirve de colateral** en cuenta unificada de OKX, al **98 %**.
5. **El carry vigente paga 2,66 % sobre capital contra un DFR del 2,500 %.**
6. Existe **un instrumento mejor para la misma idea**, con el rendimiento conocido al
   entrar, que hoy paga **4,949 %** neto y cuya prueba de muerte cuesta 2 horas.

**Lo que queda para Pablo, y no lo decide esta tarea:**

1. **Si se ejecuta la §4 y con qué pasos.** El OK de la §7 tiene que enumerarlos.
   Mi recomendación: **no ejecutar la §4 tal como está**, y en su lugar autorizar la
   prueba de muerte de **C-1** (2 horas, 50 peticiones, ningún trial), porque si C-1
   sobrevive la §4 cambia de instrumento, y si no sobrevive la §4 se ejecuta sabiendo
   que el techo es +165 € al año sobre 100.000 €.
2. **Qué se hace con N8** (B-e): marcarla como superada, reducirla a su umbral
   analítico, o lanzarla tal cual.
3. **El `p` del escenario de contraparte** (B-b): con la ventaja de +165 € sobre
   100.000 €, un `p` del **0,17 %** anual de pérdida total la borra. Ese número es de
   Pablo.
4. Las cinco correcciones de la §4 que salen del Paso B: la fila de la tasa sin
   riesgo (B-c, B-f), la §4.3 como condición de la §4.2 (B-b), la exclusión de
   `TRADIFI_PERPETUAL` y la comprobación falsable de la criba (B-a), el criterio de
   antigüedad y los 137 `SETTLING` (B-d), y `fundingIntervalHours` por símbolo (B-g).

### Inventario de scripts y salidas

| Script | Qué produce | Salida |
|---|---|---|
| `fase0_n9/a1_hechos_seccion2.py` | §2.1, §2.3, §2.4, §2.6 | `salida_a1_hechos_seccion2.json` |
| `fase0_n9/a2_fecha_y_conteo_exacto.py` | A-2: fecha, 7.832, y la tarifa por año | `salida_a2_fecha_y_conteo_exacto.json` |
| `fase0_n9/a3_trabajo_previo_funding.sh` | A-3 en diez ramas y dos árboles del VPS | `salida_a3_trabajo_previo_funding.txt` |
| `fase0_n9/a4_comisiones.py` | A-4, sondeo de diez fuentes + cuerpos congelados | `salida_a4_comisiones.json`, `fuentes_a4/` |
| `fase0_n9/a4b_comisiones_extraccion.py` | A-4, extracción estructurada + siete fuentes más | `salida_a4b_comisiones_extraccion.json`, `fuentes_a4b/` |
| `fase0_n9/a5_margen.py` | A-5, margen y colateral de API pública | `salida_a5_margen.json`, `fuentes_a5/` |
| `fase0_n9/a6_entorno.sh` | §2.5, el entorno del VPS | `salida_a6_entorno.txt` |
| `fase0_n9/a7_cuenta_minima.py` | La cuenta, el DFR y los euros al año | `salida_a7_cuenta_minima.json` |
| `fase0_n9/b1_transversal_y_basis.py` | B-a, B-b (topes), B-d (edad) y C-1 (base) | `salida_b1_transversal_y_basis.json` |
| `fase0_n9/b2_supervivencia_acotable.py` | B-d: el funding sobrevive al delistado | `salida_b2_supervivencia_acotable.json` |
| `fase0_n9/c1_datos_de_la_candidata.py` | C-1: el histórico se baja sin clave | `salida_c1_datos_de_la_candidata.json` |

Once ficheros: nueve `.py` y dos `.sh`, los once ejecutados con `rc=0` desde
`/root/trading-bot-n9/fix-fase2`.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
