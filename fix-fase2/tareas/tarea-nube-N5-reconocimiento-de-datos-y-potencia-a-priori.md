# Tarea N5 (nube) — Reconocimiento de datos y potencia a priori: ¿existe un universo donde el listón sea alcanzable?

**Creada:** 2026-11-01 por Claude Opus 5 (sesión de escritorio de Pablo).
**Repo:** `miguezlopezia-a11y/trading-bot`. **Base:** rama `fase-b-recuperada`.
**Rama de trabajo:** cortar `nube/n5-reconocimiento-datos` desde `fase-b-recuperada`.
**Estado:** PARADO en Fase 0. **No se ejecuta "Alcance" sin OK escrito de Pablo.**

**Corre en paralelo a N4** (`tarea-nube-N4-procedencia-de-V-T-y-N.md`), que
está en Fase 0 ahora mismo. Son independientes: N4 audita el listón existente,
N5 pregunta si hay otro sitio donde el listón sea alcanzable. **No se pisan**
siempre que N5 respete la sección 5: `fix-fase2/docs/registro_N.md` es de N4,
N5 no lo toca.

**Lectura previa obligatoria:**

1. `fix-fase2/docs/estado-auditoria-n1.md` — qué quedó en pie.
2. `fix-fase2/docs/fase_b_reevaluacion_resultado.md` — el Paquete 2 es el
   molde de lo que esta tarea hace para universos nuevos.
3. `fix-fase2/docs/auditoria_harness_n1.md`, sección de entorno (líneas 7-9).

---

## 1. La pregunta

El expediente lleva doce intentos sobre **un activo y cinco años**, y el
problema de fondo no es que las reglas sean malas: es que **no hay potencia
estadística para probar nada** con esa muestra. Cada intento nuevo sobre los
mismos datos **sube el listón** (el DSR corrige por número de intentos), así
que probar más ideas ahí es gastar presupuesto estadístico sin ganar terreno.

Hay dos salidas que no pagan ese peaje:

- **Cambiar la fuente de datos, no la idea.** Un universo nuevo reinicia `N`
  y es out-of-sample real.
- **Cambiar la pregunta.** El alpha direccional es donde el listón es más
  alto. El edge estructural (funding, fees, ejecución, microestructura) se
  mide contra umbrales alcanzables porque no depende de predecir.

Las dos dependen de algo que **nadie ha comprobado**: qué datos se pueden
conseguir de verdad, y si con ellos el listón sería alcanzable.

**Esta tarea no prueba ninguna estrategia.** No evalúa señales, no mide
retornos de ninguna regla, no busca alpha. Por eso **no consume trials y no
sube `N`** — y esa es la condición que la hace segura. Si en algún momento el
Alcance exige evaluar una señal, el paso está mal diseñado: **parar y
reportarlo**, no ejecutarlo.

---

## 2. Hechos ya verificados desde el escritorio (reverificar, no creer)

### 2.1 Yahoo Finance está bloqueado en el contenedor; PyPI no

`docs/auditoria_harness_n1.md:7-9`, textual: *"`scipy` y `yfinance`
instalados por la sesión. `torch` y `timesfm` no disponibles. Red: la política
del contenedor bloquea Yahoo Finance."*

Luego hay salida a PyPI y **no** a Yahoo. **Qué más alcanza el contenedor es
desconocido.** Nadie lo ha probado. Es el primer paso del Alcance.

### 2.2 Todo lo que hay en el repo es cripto, diario y OHLCV

```
$ find data -name "*.csv" | wc -l
36
$ ls data/multi/*.csv | sed 's/.*multi\///;s/_20261.*//' | sort -u | tr '\n' ' '
ada_usd avax_usd bnb_usd btc_usd doge_usd eth_usd link_usd ltc_usd sol_usd xrp_usd
$ ls data/multi_muertos/*.csv | sed 's/.*muertos\///;s/_20261.*//' | sort -u | tr '\n' ' '
ada_usd avax_usd bch_usd bnb_usd btc_usd doge_usd eos_usd eth_usd fil_usd icp_usd link_usd ltc_usd sol_usd xlm_usd xrp_usd
$ head -1 data/multi/ada_usd_20261009.csv
date,open,high,low,close,volume
$ wc -l data/multi/ada_usd_20261009.csv
3258 data/multi/ada_usd_20261009.csv
$ head -2 data/multi/ada_usd_20261009.csv | tail -1 | cut -c1-11
2017-11-09,
$ tail -1 data/multi/ada_usd_20261009.csv | cut -c1-11
2026-10-09,
```

10 activos vivos, 15 en el universo con caídos, dos sellos (`20261007` y
`20261009`). ADA: 3257 velas, 2017-11-09 → 2026-10-09. **Columnas: solo
`date,open,high,low,close,volume`.**

**No hay en el repo:** ningún activo fuera de cripto, ninguna frecuencia
distinta de la diaria, ni funding rates, ni order book, ni fees por exchange,
ni tipos de interés, ni nada que permita medir edge estructural.

### 2.3 La maquinaria de potencia ya existe y se reutiliza

```
$ grep -n "^def \|^T_EFF\|^V_TRIALS\|^N_TABLA" src/potencia_fase_b.py
25:T_EFF = 4336
28:V_TRIALS = 0.0007021947704551833
30:N_TABLA = [1, 5, 12, 50, 100]
34:def sharpe_min_dsr(n_trials, var_trials=V_TRIALS, n_eff=T_EFF,
50:def sharpe_min_t(n_eff=T_EFF):
55:def main():
```

`sharpe_min_dsr(n_trials, var_trials, n_eff, skew, kurt, conf)` ya acepta los
cuatro parámetros como argumentos. **No hay que reimplementar nada**: se
importa y se llama con los valores del universo candidato. Las constantes del
módulo son solo los valores por defecto de Fase B.

### 2.4 El cálculo a priori es regla de proyecto, no idea nueva

`docs/fase_b_reevaluacion_resultado.md:58-59`, textual: *"**Este es el cálculo
que se exigirá A PRIORI antes de cualquier fase nueva (regla de proyecto).**"*

Nunca se ha aplicado a una fase nueva. Esta tarea es la primera vez.

### 2.5 Lo que esto NO prueba

Que exista un universo mejor. Puede que el reconocimiento concluya que **todo
lo accesible tiene menos historia que la que ya hay**, y entonces la respuesta
honesta es que no hay salida por datos. Eso es un resultado válido y cierra
una vía; no es un fracaso de la tarea.

---

## 3. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

Dos pasos separados, los dos obligatorios. Al terminar, escribir
`## Registro de revisión némesis` al final de ESTE archivo y **PARAR**.

### Paso A — Verificación de hechos

Reverificar con comandos propios los cinco puntos de la sección 2, cada uno
con comando, salida pegada y veredicto `CONFIRMADO`/`REFUTADO`/`NO VERIFICABLE`.

Añadir, con salida pegada:

- **A-1.** Probar la conectividad real del contenedor, una fuente por línea,
  con timeout de **15 segundos** por intento y sin reintentos: Binance
  (`api.binance.com`), Coinbase (`api.exchange.coinbase.com`), Kraken
  (`api.kraken.com`), CoinGecko (`api.coingecko.com`), Bybit, OKX, Stooq,
  Alpha Vantage, FRED (`api.stlouisfed.org`), Nasdaq Data Link. Para cada
  una: alcanzable sí/no, y si sí, **qué devuelve sin API key**.
- **A-2.** Para cada fuente alcanzable: ¿cuánta historia da, con qué
  granularidad, y cuántos símbolos? Bajar **una** serie de prueba y medir:
  primera fecha, última, número de filas. No bajar un universo entero en
  Fase 0.
- **A-3.** ¿Alguna fuente alcanzable da **funding rates**, **fees** u
  **order book histórico**? Esa es la condición necesaria para la vía del
  edge estructural. Si ninguna, decirlo: la vía queda cerrada desde la nube.
- **A-4.** Verificar que `sharpe_min_dsr` de `src/potencia_fase_b.py` se puede
  importar y llamar con parámetros distintos a los del módulo, sin editarlo.
  Pegar una llamada de prueba y su salida.
- **A-5.** Verificar el intérprete de Python disponible y que tiene numpy,
  pandas y scipy. Si no hay ninguno usable → **PARAR y reportar**.

### Paso B — Ataque adversarial al planteamiento

Mínimo cinco objeciones reales, con severidad y qué cambiaría del Alcance. Si
no se encuentra ninguna, **decir por qué no se encontró**.

Preguntas que el enemigo haría:

- **B-a.** ¿De verdad `N` se reinicia en un universo nuevo? Un escéptico diría
  que los doce trials ya gastados **son conocimiento sobre qué tipo de regla
  probar**, y que llevarse ese aprendizaje a otro mercado arrastra el sesgo de
  selección con él. ¿Es defendible reiniciar `N`, o hay que arrancar de `N=12`?
  **Responder esto es más importante que cualquier otro paso de esta tarea**:
  si `N` no se reinicia, la vía del universo nuevo no sirve para nada.
- **B-b.** Si el contenedor alcanza un exchange, ¿los datos que da son
  comparables con los de yfinance que ya hay, o vienen con otro sesgo
  (supervivencia de símbolos listados hoy, precios de un solo venue, huecos)?
  Un universo nuevo con sesgo nuevo no es progreso.
- **B-c.** El edge estructural se mide contra umbrales más bajos, sí — pero
  ¿se puede **backtestear** con datos diarios OHLCV, o exige datos de
  ejecución que no van a estar? Si exige lo segundo, la vía es teórica.
- **B-d.** ¿Cuánta historia haría falta de verdad? Hacer el cálculo al revés
  en la Fase 0, a mano y con un ejemplo: con `N=1` y una `V` plausible, qué
  `T` deja el listón por debajo de 1.0. Si la respuesta son décadas, el
  Alcance entero sobra y hay que decirlo ya.
- **B-e.** La objeción que no está en esta lista.

### NO-GO de la Fase 0

- Si A-5 no encuentra intérprete usable → PARAR.
- Si A-1 concluye que **ninguna** fuente de datos es alcanzable → PARAR y
  reportar. El Alcance no se puede ejecutar y las dos vías quedan cerradas
  desde la nube (habría que bajar los datos en el VPS y volver a subirlos).
- Si B-a concluye que `N` **no** se reinicia → PARAR. El Alcance estaría
  construido sobre una premisa falsa.
- Si algo de la sección 2 sale **REFUTADO** → PARAR.

---

## 4. Alcance (NO EJECUTAR sin OK escrito de Pablo en la sección 7)

Orden fijo. Scripts en `fix-fase2/auditoria_n5/`, salida en JSON del mismo
nombre. Timeout **20 minutos** por paso; si uno no termina, matarlo, anotarlo
y seguir.

| # | Paso | Entrega |
|---|---|---|
| 5.1 | Inventario de fuentes: para cada una alcanzable en A-1, tabla con granularidad, historia máxima, número de símbolos, necesidad de API key y límites de rate | `salida_5_1_fuentes.json` |
| 5.2 | Para las 3 fuentes con más historia: bajar **una** serie larga de prueba cada una y medir huecos, duplicados, saltos de precio imposibles y fechas anteriores al listado real del activo (el defecto de FIL que el expediente ya documentó) | `salida_5_2_calidad.json` |
| 5.3 | Potencia a priori, universo por universo: `sharpe_min_dsr` con el `T` real de cada universo candidato, `N` ∈ {1, 3, 5, 12}, y `V` barrida en un rango plausible (tres valores, justificados) | `salida_5_3_potencia.json` |
| 5.4 | Cálculo inverso: para cada universo, el `T` mínimo que haría el listón < 1.0 con `N=1` y con `N=5`. Expresado en **años de historia**, no en observaciones | `salida_5_4_t_minimo.json` |
| 5.5 | Mismo cálculo para la vía del edge estructural, **si** A-3 encontró datos: qué umbral aplica cuando la hipótesis no es predictiva, y con qué `T` se alcanza | `salida_5_5_estructural.json` |
| 5.6 | Informe `fix-fase2/docs/auditoria_n5.md`: la tabla de universos ordenados por **holgura** (Sharpe alcanzable menos listón exigido), y para cada uno qué habría que comprometer por escrito antes de tocarlo | el entregable |

**El entregable es 5.6, y es una criba, no una recomendación de estrategia.**
Dice qué universos tienen potencia suficiente para que valga la pena diseñar
una hipótesis, y cuáles no. No dice qué estrategia usar: eso sería evaluar
señales, y está prohibido en esta tarea.

Si 5.6 concluye que **ningún** universo accesible tiene potencia suficiente,
ese es el resultado y se escribe tal cual. Cierra las dos vías de la
sección 1 y la decisión de Pablo se simplifica.

---

## 5. Límites de escritura

- **Permitido crear:** `fix-fase2/auditoria_n5/*.py`, sus JSON,
  `fix-fase2/docs/auditoria_n5.md`. Datos nuevos descargados, si los hay, en
  `fix-fase2/data/reconocimiento_n5/` **con su `.sha256` y su `.meta.json`**,
  igual que los 36 CSV existentes — un CSV sin ancla de integridad es
  exactamente el defecto que el expediente ya tiene con `btc_usd_5y_1d.csv`.
- **Prohibido modificar:** cualquier `src/*.py`, cualquier `results/*.json`,
  cualquier CSV existente, cualquier documento de dictamen previo.
- **`fix-fase2/docs/registro_N.md` es de N4. N5 no lo crea ni lo toca.**
- **Prohibido evaluar cualquier señal o estrategia**, incluidas las 11 de
  Fase A y la regla de Fase B, sobre datos nuevos o viejos. Esta tarea mide
  disponibilidad de datos y aritmética de umbrales. Nada más.
- No descargar universos completos en el Alcance sin decir antes cuántos MB
  son. Tope: **200 MB** en total. Si hace falta más, parar y preguntar.
- Nada se activa.

---

## 6. Entregables

1. `## Registro de revisión némesis` al final de este archivo (Fase 0).
2. `fix-fase2/docs/auditoria_n5.md` — informe con la criba de 5.6.
3. `fix-fase2/auditoria_n5/` — scripts y JSON.
4. Datos de reconocimiento, si los hay, con hash y meta.
5. PR contra **`fase-b-recuperada`**, nunca contra `main`.

**Dónde va cada hallazgo:** mecánica de ejecución (conectividad, intérprete,
timeouts, rate limits) al registro némesis de este archivo. Resultados a
`auditoria_n5.md`. No mezclar.

`shared/` no existe en este repo y no va a existir. Pablo replica a mano al
búnker lo que haga falta.

---

## 7. Estado de la tarea

**PARADO EN FASE 0.** Pablo escribe aquí el OK, con fecha, cuando haya leído
el registro némesis.

```
OK para ejecutar el Alcance: [pendiente]
```

---

## Registro de revisión némesis

**Ejecutado:** 2026-11-01, sesión en la nube de Claude Code (contenedor
efímero, Linux 6.18.44, Python 3.13.18).
**Rama base:** `fase-b-recuperada` @ `3fe18c8`. **Rama de trabajo:**
`nube/n5-reconocimiento-datos`.
**Alcance ejecutado:** solo la §3 (Fase 0), pasos A y B. **La §4 (Alcance) NO
se ha ejecutado**: falta el OK escrito de Pablo en la §7 y, además, está
bloqueada por red (A-1).
**Trials consumidos: 0.** No se ha evaluado ninguna señal, ni sobre datos
viejos ni nuevos, ni se ha medido el retorno de ninguna regla. `N` no se mueve.
**Datos descargados: 0 bytes.** No había de dónde (A-1).

---

### Paso A — Verificación de hechos

#### A.0 — Desviación de forma en los comandos de la §2.2: son relativos a `fix-fase2/`, no a la raíz

Los comandos pegados en la §2.2 no corren desde la raíz del repo. Los datos
viven en `fix-fase2/data/`, no en `data/`.

```
$ cd /home/user/trading-bot && find data -name "*.csv" | wc -l
0
$ find . -path ./.git -prune -o -name "*.csv" -print | sed 's|/[^/]*$||' | sort | uniq -c
      1 ./fix-fase2/data
     20 ./fix-fase2/data/multi
     15 ./fix-fase2/data/multi_muertos
      4 ./fix-fase2/results
```

**Veredicto:** desviación menor, sin consecuencia sobre el contenido. Toda la
§2.2 se reverifica abajo con `cwd=fix-fase2` y entonces casa exacto. Queda
anotado porque cualquier script del Alcance escrito contra `data/` desde la
raíz escribiría en el sitio equivocado — y, además, `data/*.csv` está en
`.gitignore` anclado a la raíz, así que se perdería en silencio (hallazgo A.13
de N3, sigue vigente).

#### A.1 — Conectividad real del contenedor: **NINGUNA de las diez fuentes es alcanzable**

Una fuente por línea, `--max-time 15 --connect-timeout 15 --retry 0`, sin
reintentos, como pedía el brief.

```
=== A-1 CONECTIVIDAD (timeout 15s, sin reintentos) ===
fecha: 2026-11-01T20:28:35Z  |  via HTTPS_PROXY=http://127.0.0.1:39241

Binance          | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
Coinbase         | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
Kraken           | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
CoinGecko        | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
Bybit            | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
OKX              | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
Stooq            | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
AlphaVantage     | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
FRED             | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
NasdaqDL         | curl_exit=56 | http=000   |   0.3s | curl: (56) CONNECT tunnel failed, response 403

=== control: Yahoo (debe estar bloqueado segun 2.1) ===
YahooFinance     | curl_exit=56 | http=000   |   0.2s | curl: (56) CONNECT tunnel failed, response 403
=== control: PyPI (debe estar permitido segun 2.1) ===
PyPI             | curl_exit=0  | http=200   |   0.4s | <!DOCTYPE html><html lang="en">  <head> ... <title>Links
```

URLs exactas probadas (endpoints públicos, sin credenciales):
`api.binance.com/api/v3/klines`, `api.exchange.coinbase.com/products/BTC-USD/candles`,
`api.kraken.com/0/public/OHLC`, `api.coingecko.com/api/v3/ping`,
`api.bybit.com/v5/market/kline`, `www.okx.com/api/v5/market/candles`,
`stooq.com/q/d/l/`, `www.alphavantage.co/query` (apikey=demo),
`api.stlouisfed.org/fred/series/observations`, `data.nasdaq.com/api/v3/datasets/LBMA/GOLD.json`.

No es un fallo transitorio ni un problema de TLS: el propio proxy del entorno
registra la denegación de política, host por host.

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"   (recentRelayFailures)
{"kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)", "host": "api.binance.com:443"}
{"kind": "connect_rejected", ... "host": "api.exchange.coinbase.com:443"}
{"kind": "connect_rejected", ... "host": "api.kraken.com:443"}
{"kind": "connect_rejected", ... "host": "api.coingecko.com:443"}
{"kind": "connect_rejected", ... "host": "api.bybit.com:443"}
{"kind": "connect_rejected", ... "host": "www.okx.com:443"}
{"kind": "connect_rejected", ... "host": "stooq.com:443"}
{"kind": "connect_rejected", ... "host": "www.alphavantage.co:443"}
{"kind": "connect_rejected", ... "host": "api.stlouisfed.org:443"}
{"kind": "connect_rejected", ... "host": "data.nasdaq.com:443"}
{"kind": "connect_rejected", ... "host": "query1.finance.yahoo.com:443"}
```

Caracterización de la política, con controles (no son rodeos: son diagnóstico):

```
github.com (API)       | curl_exit=0  | 200
files.pythonhosted     | curl_exit=0  | 404   (responde: alcanzable)
raw.githubusercontent  | curl_exit=0  | 301
anthropic API          | curl_exit=0  | 404   (responde: alcanzable)
example.com            | curl_exit=56 | CONNECT tunnel failed, response 403
```

La política es **lista blanca**, no lista negra: `example.com` también cae.
Lo único que pasa es lo que la sesión necesita para funcionar (GitHub,
Anthropic) más los gestores de paquetes.

**Matiz que corrige el razonamiento de la §2.1 del brief.** El brief infiere
*"luego hay salida a PyPI y no a Yahoo"*. El resultado es correcto, la
inferencia no generaliza: PyPI, `files.pythonhosted.org`, npm, crates y
`proxy.golang.org` están en la variable `no_proxy` del contenedor, o sea que
**no pasan por el proxy de política en absoluto**. Que PyPI responda no es una
concesión de la política; es un *bypass* preexistente. De ahí no se deduce nada
sobre qué más podría alcanzar el contenedor, y por eso A-1 había que probarlo
una fuente a una, como hizo el brief. Bien planteado ese paso.

**Veredicto: CONFIRMADO que el contenedor está cerrado, y NO-GO del brief
activado.** Ninguna de las diez fuentes es alcanzable. El NO-GO de la §3 dice
literal: *"Si A-1 concluye que **ninguna** fuente de datos es alcanzable →
PARAR y reportar. El Alcance no se puede ejecutar y las dos vías quedan
cerradas desde la nube."* Es el caso. **Se para aquí.**

Lo que haría falta para reabrirlo: la política de red del entorno deniega esos
hosts. Se cambia en los ajustes del entorno en la nube (menú del entorno en la
barra de título de la sesión → Edit → Network access): o un nivel de acceso más
amplio, o añadir esos hosts en *Allowed domains* dejando marcada la casilla de
gestores de paquetes. Documentado en
`https://code.claude.com/docs/en/cloud-environments#network-access`.
La alternativa, que el brief ya contempla, es bajar los datos en el VPS y
subirlos. **No he sustituido nada por datos sintéticos ni por cifras de memoria.**

#### A.2 — No ejecutable: **NO VERIFICABLE por ausencia de fuente alcanzable**

A-2 pedía, para cada fuente alcanzable, cuánta historia da, con qué
granularidad, cuántos símbolos, y bajar una serie de prueba midiendo primera
fecha / última / número de filas. **El conjunto de fuentes alcanzables está
vacío (A-1), así que A-2 no tiene dominio sobre el que operar.** No se
responde con conocimiento de memoria sobre lo que "suele dar" cada API: eso
sería exactamente el relleno que el brief prohíbe. Queda `NO VERIFICABLE`
**desde este contenedor**, no refutado.

#### A.3 — Funding rates / fees / order book: **NO VERIFICABLE, y la vía del edge estructural queda cerrada desde la nube**

Misma razón que A-2. La condición necesaria que A-3 declaraba —que alguna
fuente alcanzable dé funding, fees u order book— **no se cumple, porque no hay
ninguna fuente alcanzable.** Por el camino de A-1, la vía del edge estructural
queda cerrada desde la nube sin necesidad de discutir su mérito.

Lo que **sí** es verificable en local, y acota la vía con independencia de la
red: las 36 series congeladas del repo tienen **una sola cabecera, idéntica en
las 36**, y no hay nada estructural en ellas.

```
$ cd fix-fase2 && for f in $(find data -name "*.csv"); do head -1 $f; done | sort | uniq -c
     36 date,open,high,low,close,volume
```

Ni funding, ni fees, ni libro, ni tipos, ni nada que permita medir edge
estructural. Confirma la §2.2 del brief por el lado de la carencia.

#### A.4 — `sharpe_min_dsr` se importa y se llama con parámetros ajenos al módulo, sin editarlo: **CONFIRMADO**

```
$ cd fix-fase2 && python3 -I a4_import.py
PPY (periodos/anio) = 365
defaults del modulo: T_EFF=4336  V_TRIALS=0.0007021948  SKEW=1.037  KURT=31.999

[control] N=12 defaults -> Sharpe min anual = 1.312   (publicado: 1.312)
[control] N=1  defaults -> Sharpe min anual = 0.472   (publicado: 0.472)
[control] t>3  defaults -> Sharpe min anual = 0.870   (publicado: 0.870)

[A-4] llamadas con parametros ajenos al modulo:
  N= 1 V=0.0002 T= 2500 skew= 0.0 kurt= 3.0  ->  SR0=0.00000  Sharpe_min_anual=0.629
  N= 3 V=0.0010 T= 8000 skew=-0.5 kurt=10.0  ->  SR0=0.02697  Sharpe_min_anual=0.871
  N=12 V=0.0020 T=15000 skew= 0.3 kurt= 6.0  ->  SR0=0.07445  Sharpe_min_anual=1.677

[A-4] git status de src/potencia_fase_b.py tras las llamadas:
  (sin cambios)
```

**Veredicto: CONFIRMADO.** Los cuatro parámetros son argumentos de verdad, las
constantes del módulo son solo defaults, y los tres valores publicados del
Paquete 2 (1.312, 0.472, 0.870) reproducen exactos. `git status` limpio: no se
tocó `src/`. La §2.3 del brief es correcta y el *grep* que pega casa literal:

```
$ grep -n "^def \|^T_EFF\|^V_TRIALS\|^N_TABLA" src/potencia_fase_b.py
25:T_EFF = 4336
28:V_TRIALS = 0.0007021947704551833
30:N_TABLA = [1, 5, 12, 50, 100]
34:def sharpe_min_dsr(n_trials, var_trials=V_TRIALS, n_eff=T_EFF,
50:def sharpe_min_t(n_eff=T_EFF):
55:def main():
```

#### A.5 — Intérprete: usable. **scipy y yfinance NO están**, y da igual para lo que esta tarea necesita

```
$ which python3 && python3 -VV
/usr/local/bin/python3
Python 3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3]

python 3.13.18
numpy      OK   2.5.3
pandas     OK   3.0.5
scipy      NO   ModuleNotFoundError
yfinance   NO   ModuleNotFoundError
requests   OK   2.34.2
torch      NO   ModuleNotFoundError
timesfm    NO   ModuleNotFoundError
```

A-5 pedía numpy, pandas **y scipy**. scipy no está. Pero la cadena del DSR no
lo usa, verificado leyendo los imports de punta a punta:

```
$ grep -n "^import\|^from" src/potencia_fase_b.py
17:import json / 18:import sys / 20:import numpy as np
23:from rigor_estadistico import psr, expected_max_sharpe, PPY
$ grep -n "^import\|^from" src/rigor_estadistico.py
26:import json / 27:import math / 28:import sys / 30:import numpy as np / 31:import pandas as pd
34:from strategies import STRATEGIES
35:from backtester import run_backtest, compute_metrics
$ grep -c scipy src/rigor_estadistico.py
0
$ grep -n "^import\|^from" src/strategies.py src/backtester.py src/indicators.py
(solo functools, numpy, pandas y los modulos propios)
```

**Veredicto: el intérprete es usable y el NO-GO de A-5 NO se activa.** La
aritmética de umbrales, que es lo único que esta tarea calcula, corre con
numpy. scipy es instalable (PyPI responde, A-1) y **no lo he instalado**: nada
de la Fase 0 lo necesita y el Alcance no está autorizado. Concuerda con el
hallazgo A.10 de N3, reverificado de forma independiente.

#### A.6 (§2.1) — El texto citado existe y es literal: **CONFIRMADO**

```
$ sed -n '7,9p' fix-fase2/docs/auditoria_harness_n1.md
**Entorno:** Python 3.13.18, numpy 2.5.3, pandas 3.0.5. `scipy` y `yfinance`
instalados por la sesión. `torch` y `timesfm` no disponibles. Red: la política
del contenedor bloquea Yahoo Finance.
```

La cita es exacta. Yahoo sigue bloqueado hoy (A-1, control). El *"instalados
por la sesión"* es literal y hay que leerlo así: los instaló N1, **no vienen en
la imagen** (A.5). El brief acierta en el hecho y la §2.1 queda `CONFIRMADO`,
con el matiz de inferencia de A-1 (PyPI es *bypass*, no permiso).

#### A.7 (§2.2) — Inventario de datos: **CONFIRMADO exacto**, con `cwd=fix-fase2`

```
$ cd fix-fase2
$ find data -name "*.csv" | wc -l
36
$ ls data/multi/*.csv | sed 's/.*multi\///;s/_20261.*//' | sort -u | tr '\n' ' '
ada_usd avax_usd bnb_usd btc_usd doge_usd eth_usd link_usd ltc_usd sol_usd xrp_usd
$ ls data/multi_muertos/*.csv | sed 's/.*muertos\///;s/_20261.*//' | sort -u | tr '\n' ' '
ada_usd avax_usd bch_usd bnb_usd btc_usd doge_usd eos_usd eth_usd fil_usd icp_usd link_usd ltc_usd sol_usd xlm_usd xrp_usd
$ head -1 data/multi/ada_usd_20261009.csv
date,open,high,low,close,volume
$ wc -l data/multi/ada_usd_20261009.csv
3258 data/multi/ada_usd_20261009.csv
$ head -2 data/multi/ada_usd_20261009.csv | tail -1 | cut -c1-11
2017-11-09,
$ tail -1 data/multi/ada_usd_20261009.csv | cut -c1-11
2026-10-09,
```

Las seis salidas casan carácter a carácter con lo que pega el brief. 10 vivos,
15 con caídos, dos sellos, ADA 3257 velas 2017-11-09 → 2026-10-09, cabecera de
seis columnas en las 36. **CONFIRMADO.**

Rangos reales por activo, que el brief no pega y el Alcance necesitaría:

```
ada   2017-11-09 -> 2026-10-09  (3257 filas)     fil  2017-12-13 -> 2026-10-09  (3223)
avax  2020-07-13 -> 2026-10-09  (2211 filas)     icp  2021-05-10 -> 2026-10-09  (1979)
bnb   2017-11-09 -> 2026-10-09  (3257 filas)     eos  2017-11-09 -> 2026-10-09  (3257)
btc   2014-09-17 -> 2026-10-09  (4406 filas)     xlm  2017-11-09 -> 2026-10-09  (3257)
doge  2017-11-09 -> 2026-10-09  (3257 filas)     bch  2017-11-09 -> 2026-10-09  (3257)
eth   2017-11-09 -> 2026-10-09  (3257 filas)
link  2017-11-09 -> 2026-10-09  (3257 filas)
ltc   2014-09-17 -> 2026-10-09  (4406 filas)
sol   2020-04-10 -> 2026-10-09  (2374 filas)
xrp   2017-11-09 -> 2026-10-09  (3257 filas)
```

Dos cosas que saltan y que importan para B-b: **once de los quince activos
arrancan el mismo día, 2017-11-09**, y BTC y LTC el mismo 2014-09-17. Eso no
son fechas de listado: son los suelos del proveedor. BNB se lanzó en julio de
2017, LINK en septiembre, ADA en octubre — y los tres "empiezan" el mismo día.

#### A.8 (§2.4) — La regla a priori está escrita y es literal: **CONFIRMADO**

```
$ sed -n '55,62p' fix-fase2/docs/fase_b_reevaluacion_resultado.md
Sharpe mínimo para **t>3: 0.870** (anual). Observado Fase B: **1.008**.
**Brecha vs DSR≥0.95: +0.304** — el DSR exigente sigue sin alcanzarse; el
t>3 se supera con holgura (y también explica por qué Fase A nunca pudo
ver nada: con T~700 y N=11, el umbral t era inalcanzable).

**Dictamen P2:** cálculo entregado y verificado (sintético: curvas encima/
debajo del umbral clasificadas bien, 3/3). Conclusión: con N=12 y estas
colas, un Sharpe 1.0 no basta para DSR 0.95 — hacen falta ~1.31, o menos
trials, o más T. **Este es el cálculo que se exigirá A PRIORI antes de
cualquier fase nueva (regla de proyecto).**
```

La frase está, con ese énfasis, y el brief la cita bien (está en las líneas
62-63 del fichero de hoy, no 58-59; desviación de forma sin consecuencia).
Que nunca se haya aplicado a una fase nueva es coherente con el expediente.
**CONFIRMADO.**

#### A.9 (§2.5) — "Lo que esto NO prueba": **CONFIRMADO, y A-1 lo ha materializado**

La §2.5 advertía que el reconocimiento podía concluir que no hay salida por
datos, y que eso sería un resultado válido. Es exactamente lo que ha pasado,
por una razón que la §2.5 no anticipaba: no es que lo accesible tenga menos
historia que lo que ya hay — es que **no hay nada accesible**. La advertencia
era correcta y está bien que estuviera escrita antes de mirar.

---

### Resumen del Paso A

| # | Punto | Veredicto |
|---|---|---|
| §2.1 | Yahoo bloqueado, PyPI no | **CONFIRMADO** (con matiz: PyPI es *bypass* de `no_proxy`, no permiso de política) |
| §2.2 | Todo es cripto, diario, OHLCV | **CONFIRMADO** exacto, 6/6 salidas |
| §2.3 | La maquinaria de potencia existe y se reutiliza | **CONFIRMADO**, reproduce 1.312 / 0.472 / 0.870 |
| §2.4 | El cálculo a priori es regla de proyecto | **CONFIRMADO**, cita literal |
| §2.5 | Lo que esto NO prueba | **CONFIRMADO**, y materializado por A-1 |
| A-1 | Conectividad, 10 fuentes | **CERRADO: 0 de 10 alcanzables. NO-GO ACTIVADO** |
| A-2 | Historia/granularidad/símbolos por fuente | **NO VERIFICABLE** (dominio vacío por A-1) |
| A-3 | Funding / fees / order book | **NO VERIFICABLE** (ídem). Vía estructural cerrada desde la nube |
| A-4 | `sharpe_min_dsr` reutilizable sin editar | **CONFIRMADO** |
| A-5 | Intérprete y librerías | **USABLE.** scipy y yfinance ausentes, irrelevantes para esta tarea |

Nada de la §2 sale **REFUTADO**. El NO-GO que se activa es el de A-1.

---

### Paso B — Ataque adversarial al planteamiento

Ocho objeciones. Dos de ellas (B-a y B-d) cambian la lectura de la tarea
entera; una (B-e1) dispara el autocontrol que el propio brief escribió en su
§1. Severidades: **BLOQUEANTE** (invalida el paso tal como está escrito),
**ALTO** (hay que rediseñar el paso), **MEDIO** (hay que acotarlo).

---

#### B-a — ¿Se reinicia `N` de verdad en un universo nuevo? **SÍ, pero condicionado. Severidad: ALTO (no BLOQUEANTE)**

Es la pregunta que decide la tarea, así que la respondo con el argumento, no
con una preferencia.

**Qué corrige exactamente el DSR.** `SR0 = sqrt(V)·E[max de N normales
estándar]` (Bailey–López de Prado 2014, Ec. 2; implementado en
`rigor_estadistico.py:93-101`). Lo que ese término descuenta es **el sesgo de
selección del máximo**: si se calculan `N` Sharpes **sobre la misma muestra** y
se reporta el mayor, su esperanza bajo la nula es positiva, porque se ha
elegido el ruido de estimación más favorable de `N` realizaciones. `SR0` es
precisamente la esperanza de ese máximo. No es una penalización moral por
haber tenido muchas ideas: es la media de una distribución de máximos.

**Por qué eso se reinicia.** El sesgo vive en el ruido de estimación de *esa*
muestra. Si los doce intentos se hicieron sobre la muestra X, y después se
evalúa **una** regla precomprometida sobre una muestra Y independiente, el
ruido de estimación de Y es independiente del proceso de selección que ocurrió
en X. Formalmente: `E[SR_Y | regla seleccionada en X] = SR_verdadero(regla)`.
No hay inflación que arrastrar. El estimador sobre Y es insesgado y el test
mantiene su tamaño nominal. **Con `N=1` sobre Y, `SR0 = 0` es la cifra
correcta, no una concesión.**

**Dónde el escéptico tiene razón, y dónde se equivoca.** Tiene razón en que los
doce trials son conocimiento: la regla que uno se lleva no es un sorteo del
espacio de hipótesis, es el argmax de doce pruebas. Pero eso contamina **el
prior sobre si la regla es verdadera**, no el **p-valor sobre la muestra
nueva**. Son dos cosas distintas y solo la segunda entra en el DSR. Y el efecto
del prior contaminado va en la dirección contraria a la que teme: si el
aprendizaje de los doce trials era señal real, ayuda; si era ruido, la regla
tiene SR verdadero 0 y la muestra nueva lo estimará en torno a 0 con cobertura
correcta al 95%. **En ningún caso infla la estimación nueva.** El escéptico
está pidiendo que se pague dos veces por el mismo sesgo.

**Y aquí está la condición que sí muerde.** El argumento de arriba cuelga
íntegro de una palabra: **independiente**. Y es ahí donde esta tarea se juega
el cuello, porque la §1 del brief dice *"Un universo nuevo reinicia `N` y es
out-of-sample real"* como si fuesen lo mismo, y no lo son:

- Si el "universo nuevo" son los mismos majors de cripto bajados de Binance en
  vez de Yahoo, **no es una muestra nueva**: son los mismos activos, el mismo
  calendario, el mismo ciclo 2017-2021-2025, correlacionados 0.7-0.9 entre sí y
  con lo ya minado. El ruido de estimación de Y está en buena parte realizado
  también en X. `N` **no se reinicia**; como mucho se reinicia a medias, y no
  hay forma limpia de decir a cuántas medias.
- El reinicio solo es defendible contra un universo con **baja correlación con
  lo ya minado**: renta variable, divisas, tipos, materias primas. Otro *venue*
  de las mismas monedas no vale.

**Las tres condiciones para que el reinicio sea real:**

1. **Independencia de muestra**, no de proveedor. Universo poco correlacionado
   con lo ya minado, y la correlación **medida y escrita** antes de evaluar, no
   asumida. Bajar BTC de Binance en vez de Yahoo es cambiar de proveedor, no de
   universo, y no da derecho a `N=1`.
2. **Un solo disparo precomprometido.** Regla, parámetros, universo, ventana y
   criterio de decisión congelados **por escrito antes de la primera
   evaluación**. Si se mira el universo nuevo y luego se decide la regla, `N` es
   el número de miradas, no 1. El reinicio compra exactamente un tiro.
3. **Que el contador exista.** El expediente **no sabe contar su propio `N`
   hoy**: el hallazgo H12 de N1 tiene abierta la contradicción 12 contra 14. Un
   proyecto que no sabe si lleva 12 o 14 no va a sostener un `N=1` declarado.
   El libro de cuentas de N4 (`registro_N.md`) es **prerrequisito** de esta vía,
   no un complemento. *(No lo toco: es de N4, §5.)*

**Veredicto B-a: `N` se reinicia. La premisa del Alcance NO es falsa, y el
NO-GO de B-a NO se activa.** Pero se reinicia bajo tres condiciones, y la
primera de ellas elimina de la criba a la mayoría de las fuentes que el propio
A-1 iba a inventariar: de las diez, seis son *exchanges* de cripto (Binance,
Coinbase, Kraken, Bybit, OKX, CoinGecko) y **no dan derecho al reinicio**.
Solo Stooq (renta variable, divisas, índices), FRED (tipos y macro) y Nasdaq
Data Link cualificarían. Las tres están bloqueadas (A-1).

**Qué cambia del Alcance:** el paso 5.1 deja de ser "inventario de fuentes
alcanzables" y pasa a ser "inventario de **universos con independencia
demostrable** respecto a lo ya minado", con la correlación como columna
obligatoria y criterio de exclusión. Y el 5.6 tiene que exigir por escrito las
tres condiciones de arriba para cada universo que pase la criba.

---

#### B-d — El cálculo inverso contesta lo contrario de lo que el brief esperaba: `T` **no es** la restricción. **Severidad: ALTO**

B-d pedía el cálculo al revés, a mano, en la Fase 0: con `N=1` y una `V`
plausible, qué `T` deja el listón por debajo de 1.0. Y advertía: *"Si la
respuesta son décadas, el Alcance entero sobra."*

**La respuesta no son décadas. Son 2.6 años — menos de los 11.9 que ya están
en el repo.**

```
$ cd fix-fase2 && python3 -I bd_inverso.py

2) LISTON ANUAL con las colas de Fase B (skew=1.037, kurt=32), T_eff=4336
   T_eff=4336 = 11.9 anos de ventana, los datos QUE YA ESTAN EN EL REPO
     N |   SR0_per | liston anual |  <1.0?
     1 |   0.00000 |       0.4723 |     SI
     2 |   0.01377 |       0.7336 |     SI
     3 |   0.02260 |       0.9014 |     SI
     5 |   0.03160 |       1.0729 |     no
    12 |   0.04412 |       1.3118 |     no
    14 |   0.04607 |       1.3491 |     no
  t>3 (criterio propio del proyecto, invariante a N) = 0.8704  -> SI

3) B-d LITERAL: T minimo (en anos de ventana) para liston < 1.0
     N |  T_eff min |    anos |  vs 11.9 anos actuales
     1 |        956 |     2.6 |            YA CUBIERTO
     2 |       1760 |     4.8 |            YA CUBIERTO
     3 |       2959 |     8.1 |            YA CUBIERTO
     5 |       6084 |    16.7 |        faltan 4.8 anos
    12 |      38657 |   105.9 |       faltan 94.0 anos

  Mismo calculo con el criterio t>3 (no depende de N ni de V):
    T_eff min para que 3/sqrt(T)*sqrt(365) < 1.0 : 3285 obs = 9.0 anos

4) ROBUSTEZ: el resultado de N=1 no depende de las colas supuestas
    skew   kurt |  liston N=1 (T=4336) |  T min anos p/ <1.0
     0.0    3.0 |               0.4774 |                 2.7
   1.037   32.0 |               0.4723 |                 2.6
     0.0  150.0 |               0.4829 |                 3.0
    -1.0  400.0 |               0.4993 |                 3.6
     0.0 1000.0 |               0.5195 |                 4.6

5) CONTROL: reproduce la tabla publicada del Paquete 2
  N=  1  SR0=0.00000  liston=0.472
  N=  5  SR0=0.03160  liston=1.073
  N= 12  SR0=0.04412  liston=1.312
  N= 50  SR0=0.06032  liston=1.622
  N=100  SR0=0.06706  liston=1.751
  t>3 = 0.870   |  Sharpe observado Fase B = 1.008
```

El control reproduce la tabla publicada entera, así que las cifras nuevas salen
de la misma maquinaria que las viejas.

**Lectura.** La fila `N=12 → 105.9 años` es el "96 años" de N3·B1 (la
diferencia es el objetivo: N3 apuntaba al 1.008 observado, yo al 1.0 redondo).
Pero esa cifra **nunca fue una propiedad de `T`**: era una propiedad de `N=12`.
En cuanto `N` baja a 3 o menos, **la historia que ya está en el repositorio
sobra** para poner el listón por debajo de 1.0. Y el resultado es robusto a las
colas: entre curtosis 3 y curtosis 1000, el `T` mínimo se mueve de 2.7 a 4.6
años, siempre muy por debajo de los 11.9 disponibles.

**Consecuencia para el Alcance, y es grande.** La §1 del brief junta dos cosas
en una sola frase —*"cambiar la fuente de datos"* reinicia `N` **y** es
out-of-sample— y el Alcance desarrolla la mitad equivocada. Los pasos 5.1
(historia máxima por fuente), 5.3 (potencia universo por universo) y sobre todo
5.4 (*"el `T` mínimo que haría el listón < 1.0 … expresado en años de
historia"*) están construidos para resolver una escasez de `T` **que no
existe**. Ejecutados tal cual, 5.4 devolvería "2.6 años" para todo universo con
tres años de datos y produciría una falsa sensación de hallazgo: parecería que
se ha encontrado un universo con potencia, cuando lo único que se ha hecho es
declarar `N=1`. **La holgura de 5.6 no la daría el universo: la daría la
declaración de `N`.** Y esa declaración se puede hacer sobre los datos que ya
hay, sin bajar nada.

**Qué cambia del Alcance:** 5.4 sobra tal como está escrito (su respuesta es
una constante, no una propiedad del universo). 5.3 pierde casi todo su valor
(ver B-e2). 5.1 y 5.2 **conservan** el suyo, pero por otro motivo: no por
cuánta historia dan las fuentes, sino por la independencia de B-a·1 y la
calidad de B-b. El criterio de ordenación de 5.6 deja de ser "años de historia"
y pasa a ser "independencia demostrable respecto a lo ya minado".

Y hay un corolario incómodo que conviene que esté escrito: **si `N` se reinicia,
la vía más barata no es un universo nuevo, es un `N=1` precomprometido sobre los
datos que ya hay** — con el agravante de que esos datos ya están minados, así
que el reinicio ahí es precisamente el que B-a·1 no concede. Las dos mitades de
la tarea se sostienen juntas o no se sostienen: hace falta el universo nuevo
**por la independencia**, no por la historia.

---

#### B-e1 — El paso 5.6 exige evaluar una señal. Dispara el autocontrol del propio brief. **Severidad: BLOQUEANTE para 5.6**

La §1 del brief ordena: *"Si en algún momento el Alcance exige evaluar una
señal, el paso está mal diseñado: **parar y reportarlo**, no ejecutarlo."* Lo
reporto, porque es el caso del entregable.

El paso 5.6 pide *"la tabla de universos ordenados por **holgura** (Sharpe
alcanzable menos listón exigido)"*. El listón exigido es aritmética pura: sale
de `sharpe_min_dsr` con `N`, `T`, `V` y las colas. **El "Sharpe alcanzable" no
es aritmética: es una propiedad desconocida del universo, y no hay forma de
estimarlo sin evaluar algo sobre esos datos.** Cualquier camino para rellenar
esa columna es un trial:

- backtestear una regla cualquiera → trial explícito, prohibido por la §5;
- usar el Sharpe del *buy & hold* del universo como proxy → es evaluar una
  estrategia (la más simple que hay), y además no informa sobre el Sharpe
  alcanzable por una regla activa;
- copiar un Sharpe de la literatura → no es una medida de **este** universo, y
  la §1 dice que la tarea no busca alpha;
- ponerlo a ojo → entonces la columna no mide nada y la ordenación de 5.6 es
  arbitraria.

No es un defecto de redacción: es que **la holgura no es computable bajo las
restricciones de esta tarea**. Las colas (`skew`, `kurt`) tienen el mismo
problema en menor grado: entran en la fórmula del DSR y son propiedades de los
retornos *de la estrategia*, no del activo, así que para un universo sin
estrategia definida solo se pueden barrer por supuesto — y eso hay que decirlo
como supuesto, no como medida.

**Qué cambia del Alcance:** 5.6 se reescribe sin la columna de holgura. Lo que
sí se puede entregar, y sigue siendo útil, es la **criba de admisibilidad**:
para cada universo, (a) ¿es independiente de lo ya minado, con la correlación
medida? (b) ¿tiene `T` suficiente para el listón bajo `N=1`, que B-d cifra en
~3 años? (c) ¿qué sesgos nuevos trae, de B-b? (d) ¿qué habría que comprometer
por escrito antes de tocarlo, de B-a? Eso es una criba de verdad y no exige
evaluar nada. **La ordenación por holgura hay que retirarla.**

---

#### B-e2 — La barrida de `V` del paso 5.3 es vacua precisamente en el `N` que importa. **Severidad: ALTO**

El paso 5.3 pide `N ∈ {1, 3, 5, 12}` con `V` *"barrida en un rango plausible
(tres valores, justificados)"*. En `N=1`, `V` no entra en el cálculo. No es una
aproximación: está en el código.

```
$ grep -n "def expected_max_sharpe" -A 9 src/rigor_estadistico.py
93:def expected_max_sharpe(n_trials, var_trials):
94-    """SR0 = sqrt(V) * E[max de N normales estandar] (Bailey-LdP Ec. 2).
95-    N=1 -> sin seleccion: E[max] = 0, SR0 = 0."""
96-    if n_trials <= 1:
97-        return 0.0, 0.0
```

Y verificado numéricamente, con `V` moviéndose en un factor 500:

```
  V=0.0001                 SR0=0.000000   liston anual (T=4336) = 0.4723
  V=0.0007021947704551833  SR0=0.000000   liston anual (T=4336) = 0.4723
  V=0.005                  SR0=0.000000   liston anual (T=4336) = 0.4723
  V=0.05                   SR0=0.000000   liston anual (T=4336) = 0.4723
```

Hay además un problema conceptual encima del mecánico: `V` **es** la varianza
cruzada de los Sharpes de los trials. Con `N=1` no hay trials entre los que
variar, así que `V` no solo no entra: **no está definida**. Barrerla en tres
valores "justificados" para `N=1` es decorar una celda que no existe.

**Qué cambia del Alcance:** 5.3 solo tiene contenido para `N ≥ 2`, y
exactamente ahí es donde B-d dice que la respuesta ya está decidida. Se reduce
a una tabla de dos ejes (`N`, `T`) con las colas barridas como supuesto
declarado, y `V` solo en las filas `N ≥ 3`. Y si el universo nuevo va a operar
bajo `N=1` precomprometido, 5.3 se queda en una sola celda.

---

#### B-e3 — Con `N` bajo, el DSR deja de ser la restricción activa: la restricción es `t>3`, y `t>3` no depende de `N`. **Severidad: ALTO**

Con `N=1`, `SR0=0` y la PSR degenera en `P(SR_verdadero > 0)`, que es el
contraste t de una cola. Numéricamente: el listón DSR≥0.95 con `N=1` es **0.472
anual**, y `1.645/√4336 · √365 = 0.477`. Son el mismo test.

O sea que el listón DSR con `N=1` (0.472) está **por debajo** del propio
criterio `t>3` del proyecto (**0.870**). En un universo con `N=1`, el DSR al
0.95 ya no es el filtro exigente: es el más flojo de los dos, y el que decide
pasa a ser `t>3` — **que es invariante a `N` y no se reinicia con nada**.

Esto tiene dos consecuencias que la criba tiene que recoger:

1. El listón real de un universo nuevo con `N=1` **no es 0.472, es 0.870**, y
   sale de `3/√T_eff·√PPY`, no del DSR. El `T` mínimo pasa de 2.6 años a
   **9.0 años** (calculado arriba). Sigue por debajo de los 11.9 disponibles,
   pero **triplica** el requisito y descarta cualquier universo con menos de
   una década. Si la criba de 5.6 se construye sobre el listón DSR con `N=1`,
   admitirá universos de tres años que después morirán por `t`.
2. El `N=1` no es un almuerzo gratis presentado como rigor: el DSR al 0.95 con
   `N=1` es **un contraste t de una cola al 95%** sobre una única regla. Eso es
   mucho más débil de lo que la etiqueta "DSR ≥ 0.95" sugiere a quien la lea en
   un informe, y es exactamente la cifra que un escéptico externo atacaría. Si
   se declara `N=1`, hay que declarar también que el listón que lo acompaña es
   `t>3`, no 0.472, o el dictamen será indefendible.

**Qué cambia del Alcance:** la criba de 5.6 tiene que usar **el máximo de los
dos listones**, no el DSR solo. Y el `T` mínimo de referencia es 9.0 años, no
2.6.

---

#### B-c — El edge estructural: ni el listón es más bajo por no predecir, ni se puede backtestear con OHLCV diario. **Severidad: ALTO**

Dos cosas, y la primera es un error de razonamiento en la §1, no una
limitación de datos.

**1) "No depende de predecir" no baja ningún listón.** La §1 afirma que el edge
estructural *"se mide contra umbrales alcanzables porque no depende de
predecir"*. El listón sale de `sharpe_min_dsr(N, V, T, skew, kurt)`. Esa
función **no tiene ningún argumento sobre la naturaleza de la hipótesis**: no
distingue predictiva de estructural, y no hay por dónde entrar ese argumento.
El listón de una estrategia de funding carry con `N=1`, `T=4336` y colas
normales es 0.477 — el mismo que el de una estrategia direccional con esos
mismos parámetros. **El umbral lo fijan `N`, `T` y las colas. Nada más.**

Y por el lado de las colas el efecto es **adverso**, no favorable: el carry de
funding y el basis tienen volatilidad baja y curtosis alta con riesgo de cola
izquierda (el carry se paga durante años y se devuelve en un desapalancamiento).
En el denominador de la PSR, `√(1 − skew·SR + (kurt−1)/4·SR²)`, una curtosis de
150-400 con *skew* negativo **sube** el listón, como se ve en la tabla de
robustez de B-d (0.4723 → 0.4993 al pasar de kurt 32 a kurt 400 con skew −1).
La vía estructural no tiene el umbral más bajo: tiene **el mismo umbral y peores
colas**.

Lo que sí es verdad, y es otra cosa, es que el edge estructural puede tener un
**Sharpe verdadero más alto** por unidad de riesgo porque no necesita acertar
una dirección. Eso hace más fácil **superar** el listón, no que el listón baje.
Es una distinción que tiene que estar escrita, porque de ella depende cómo se
justifica la vía.

**2) Con OHLCV diario no se puede medir.** Desglosado, porque no todo cae igual:

| Edge | ¿Backtesteable con OHLCV diario? |
|---|---|
| Funding / basis perp-spot | **Parcial.** El carry **bruto** sí, si existe una serie de funding (es 8-horaria) más precio perp y spot. El **neto** no: exige comisiones por *venue*, financiación del margen y un supuesto de ejecución que a resolución diaria no se valida. |
| Fees / rebates de maker | **No.** Exige el calendario de tarifas por *venue* y nivel, y saber si la orden cruza o descansa. |
| Microestructura, posición en cola, impacto | **No.** Exige libro de órdenes. |
| Ejecución / slippage | **No.** Exige, como mínimo, intradía. |

Y **ninguna** de las series congeladas tiene nada de eso: 36 ficheros, una sola
cabecera `date,open,high,low,close,volume` (A-3). Sumado a A-1 —cero fuentes
alcanzables, así que tampoco hay funding de donde sacarlo— **la vía estructural
es hoy teórica desde la nube, y lo seguiría siendo con OHLCV diario aunque se
abriese la red.** Si se persigue, el requisito mínimo que hay que escribir antes
es: serie histórica de funding por *venue* + precio perp y spot alineados +
calendario de tarifas. Sin las tres, el paso 5.5 no se puede ejecutar aunque
esté autorizado.

**Qué cambia del Alcance:** 5.5 queda condicionado a esas tres series, no solo
a "si A-3 encontró datos". Y la frase de la §1 sobre umbrales alcanzables hay
que corregirla antes de que se convierta en doctrina del expediente.

---

#### B-b — Un universo nuevo trae sesgo nuevo, y el repositorio ya tiene la prueba en casa. **Severidad: MEDIO-ALTO**

La objeción es correcta y se puede sostener **sin red**, con los datos que ya
están, que es lo que la hace fuerte.

**El defecto que el expediente ya documentó, reverificado:**

```
$ cat fix-fase2/data/multi_muertos/fil_usd_20261009.csv.meta.json
  "ticker": "FIL-USD", "period": "max", "interval": "1d", "auto_adjust": true,
  "n_velas": 3223, "primera_fecha": "2017-12-13", "ultima_fecha": "2026-10-09"
```

FIL arranca el **2017-12-13** en el proveedor. La *mainnet* de Filecoin se lanzó
en octubre de 2020: son ~3 años de precios anteriores al activo. El expediente
lo tenía declarado como límite; queda reverificado.

**Y el patrón de fondo, que es peor que el caso FIL** (A.7): once de los quince
activos empiezan **el mismo día**, 2017-11-09, y BTC y LTC el mismo 2014-09-17.
BNB se lanzó en julio de 2017, LINK en septiembre, ADA en octubre, y los tres
"empiezan" el 9 de noviembre. **Ese no es un hecho de los activos: es el suelo
del proveedor.** O sea que el sesgo de yfinance en el expediente actual no es un
caso aislado en FIL, es una firma sistemática en todo el panel.

**Qué traería un universo nuevo, y por qué no es progreso automático:**

- **Supervivencia por lista de símbolos.** La API de un *exchange* devuelve los
  pares **listados hoy**. Los pares deslistados desaparecen del catálogo, no
  aparecen como caídos. Eso es el mismo sesgo que el Paquete 3 se tomó el
  trabajo de medir, reintroducido por la puerta de atrás — y peor, porque esta
  vez es invisible: no hay un `multi_muertos/` que construir si el proveedor no
  te dice qué dejó de existir.
- **Precio de un solo *venue***, con sus propias detenciones, sus huecos y su
  liquidez, en vez de un compuesto.
- **Sin ajuste por *forks* ni *airdrops***, donde yfinance sí aplicaba
  `auto_adjust: true` — así que las series **no son comparables** con las
  congeladas ni se pueden empalmar.
- **Suelo del proveedor distinto**, que desplaza la primera fecha de cada activo
  y por tanto el `T` de cada uno.

**Qué cambia del Alcance:** el paso 5.2 pide medir *"huecos, duplicados, saltos
de precio imposibles y fechas anteriores al listado real"*. Falta lo que más
importa: **la supervivencia por catálogo**. Hay que añadir, como columna
obligatoria, si la fuente permite reconstruir la lista de símbolos **vigente en
una fecha pasada**; si no lo permite, el universo entra marcado con sesgo de
supervivencia no acotable, y eso tiene que pesar en la criba. Y la lista de
símbolos hay que congelarla desde una fuente histórica independiente del
proveedor de precios, no desde el catálogo de hoy.

---

#### B-e4 — La criba heredaría una elección de `V` que el propio expediente tiene abierta como CRÍTICA. **Severidad: MEDIO**

El hallazgo H10 de N1 está abierto: el listón de Fase B es **1.312 o 0.823**
según cómo se construya `V`, las dos construcciones son defendibles, y el
Sharpe observado (1.008) **cae en medio**. N1 lo califica de CRÍTICO y lo deja
como decisión de Pablo, no como resultado.

Los pasos 5.3 y 5.4 calcularían potencia para universos nuevos usando una
construcción de `V` que **para el universo viejo todavía no está decidida**. Se
estarían dando holguras con tres decimales sobre una cantidad cuya construcción
la mueve ±0.5. Si luego Pablo resuelve H10 en el otro sentido, la criba entera
hay que recalcularla.

Atenúa esto —y por eso es MEDIO y no ALTO— que bajo `N=1` la elección de `V` es
**irrelevante** (B-e2). Pero si la criba contempla `N ≥ 3`, hereda H10 entero.

**Qué cambia del Alcance:** o la criba se restringe a `N=1` (y entonces `V` no
entra y H10 no contamina), o 5.3 y 5.4 esperan a que H10 esté cerrado. Mezclar
las dos cosas produce números que parecen firmes y no lo son.

---

### Resumen del Paso B

| id | Objeción | Severidad | Efecto sobre el Alcance |
|---|---|---|---|
| **B-a** | ¿Se reinicia `N`? **Sí**, pero solo con independencia de muestra demostrada, un tiro precomprometido y un contador auditable | **ALTO** | 5.1 pasa a ordenar por independencia, no por historia. **NO-GO no activado.** Las 6 fuentes cripto de A-1 no darían derecho al reinicio |
| **B-d** | `T` no es la restricción: con `N≤3` la historia del repo ya basta (2.6-8.1 años). El "105.9 años" era una propiedad de `N=12`, no de `T` | **ALTO** | 5.4 sobra tal como está (su respuesta es constante). 5.3 casi vacío. El criterio de criba cambia |
| **B-e1** | 5.6 exige el "Sharpe alcanzable", que no es computable sin evaluar una señal — **dispara el autocontrol de la §1** | **BLOQUEANTE (5.6)** | Retirar la columna de holgura. 5.6 se reescribe como criba de admisibilidad |
| **B-e2** | La barrida de `V` de 5.3 es vacua en `N=1`: `SR0=0` por código, y `V` ni está definida sin trials | **ALTO** | 5.3 solo tiene contenido para `N≥2`; con `N=1` es una celda |
| **B-e3** | Con `N` bajo el DSR no es la restricción activa: lo es `t>3`, que no se reinicia. Listón real 0.870, no 0.472; `T` mínimo 9.0 años, no 2.6 | **ALTO** | La criba debe usar el **máximo** de los dos listones |
| **B-c** | "No depende de predecir" **no baja el listón** (la fórmula no tiene ese argumento) y las colas del carry lo **suben**. Y el edge estructural no se backtestea con OHLCV diario | **ALTO** | 5.5 condicionado a tres series concretas. Corregir la afirmación de la §1 |
| **B-b** | Sesgo nuevo: supervivencia por catálogo de hoy, un solo *venue*, sin ajuste por *forks*. El patrón ya está en casa: 11 de 15 activos arrancan el mismo día del proveedor | **MEDIO-ALTO** | 5.2 necesita una columna de supervivencia por catálogo histórico |
| **B-e4** | 5.3/5.4 heredarían la construcción de `V` que H10 tiene abierta como CRÍTICA (1.312 vs 0.823) | **MEDIO** | O criba restringida a `N=1`, o esperar a que H10 cierre |

---

### NO-GO: cuál se ha activado

| NO-GO de la §3 | Estado |
|---|---|
| A-5 sin intérprete usable → PARAR | **No activado.** Python 3.13.18 + numpy + pandas; la cadena DSR no necesita scipy (A.5) |
| **A-1 ninguna fuente alcanzable → PARAR** | **ACTIVADO.** 0 de 10, denegación de política registrada por el proxy (A.1) |
| B-a concluye que `N` no se reinicia → PARAR | **No activado.** `N` se reinicia, con tres condiciones (B-a) |
| Algo de la §2 REFUTADO → PARAR | **No activado.** 5/5 CONFIRMADO, con dos desviaciones de forma sin consecuencia (A.0, A.8) |

**Se para por A-1.** Y se para con un resultado negativo que es informativo: el
Alcance no es ejecutable en este contenedor, no por diseño sino por red, y las
dos vías de la §1 quedan cerradas **desde la nube**. Para abrirlas hay que
cambiar la política de red del entorno o bajar los datos en el VPS.

---

### Lo que esta Fase 0 deja decidido, y lo que deja para Pablo

**Decidido, con prueba:**

1. **El contenedor está cerrado a datos de mercado.** 0 de 10 fuentes, más
   Yahoo. Lista blanca, no incidencia. El Alcance tal como está escrito no se
   puede ejecutar aquí ni con el OK de la §7.
2. **`N` se reinicia en un universo nuevo** (B-a). La premisa del Alcance no es
   falsa. Pero el reinicio exige independencia de **muestra**, no de proveedor,
   y eso descarta las seis fuentes cripto de la lista de A-1.
3. **`T` no es la restricción** (B-d). Con `N ≤ 3`, los 11.9 años que ya están
   en el repositorio sobran. El listón inalcanzable de Fase B era `N=12`
   disfrazado de escasez de datos. Esto reordena la tarea: **el universo nuevo
   hace falta por la independencia, no por la historia.**
4. **El listón real de un universo con `N=1` es `t>3` = 0.870, no el DSR =
   0.472** (B-e3), y eso triplica el `T` mínimo, de 2.6 a 9.0 años.
5. **La vía del edge estructural no tiene un listón más bajo** (B-c). La
   fórmula no sabe si la hipótesis predice. Y no se backtestea con OHLCV
   diario.
6. **El entregable 5.6, tal como está escrito, exige evaluar una señal**
   (B-e1), y el propio brief manda pararlo y reportarlo. Reportado.

**Para Pablo, y no son cosas que esta tarea pueda decidir:**

1. **Si se abre la red del entorno** o se baja en el VPS. Sin una de las dos, no
   hay Alcance. Y conviene decidirlo **después** del punto 2, porque puede que
   no haga falta abrir nada.
2. **Si el Alcance se reescribe con lo que dice B-d**, que es la pregunta de
   fondo: ya no "¿qué universo tiene más historia?" sino "¿qué universo es
   suficientemente independiente de lo ya minado para justificar `N=1`?". Son
   cribas distintas, con fuentes candidatas distintas (Stooq, FRED, Nasdaq DL
   antes que los seis *exchanges*) y entregable distinto.
3. **Si se acepta el paquete de B-a** como condición escrita del reinicio:
   correlación medida antes de evaluar, un solo disparo precomprometido, y el
   libro de cuentas de `N` existiendo de verdad **antes** (eso depende de N4).
4. **H10** sigue mandando. Mientras la construcción de `V` del universo viejo
   esté abierta, cualquier criba con `N ≥ 3` la hereda (B-e4).

**No he ejecutado ni un paso de la §4.** No he evaluado ninguna señal ni
estrategia, sobre ningún dato. No he descargado nada. No he creado
`fix-fase2/auditoria_n5/` ni `fix-fase2/docs/auditoria_n5.md`: son entregables
del Alcance. No he tocado `src/`, ni `results/`, ni ningún CSV, ni
`registro_N.md` (es de N4). `git status` lo confirma en el commit de este
registro: el único fichero modificado es este.
