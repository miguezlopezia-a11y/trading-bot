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
| Fase 0 — Paso A | [pendiente] |
| Fase 0 — Paso B | [pendiente] |
| Fase 0 — **Paso C (contrapropuesta)** | [pendiente] |
| Maker/Verifier | [pendiente] |
| NO-GO disparados | [pendiente] |
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

🤖 Generated with [Claude Code](https://claude.com/claude-code)
