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
