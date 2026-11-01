# Tarea S3 (sesión en la nube) — Datos reproducibles y ampliación de T

**Estado:** CREADA 2026-10-29 por Sonnet (Claude Code, Windows). Sin ejecutar.
**Ejecutor:** sesión en la nube de Claude Code.
**Repo:** `miguezlopezia-a11y/trading-bot`, rama base `fase-b-recuperada`
(commit `d34b147`), rama de trabajo `nube/s3-datos`.
**Alcance físico:** `fix-fase2/data/` (solo añadir) y `fix-fase2/datos_s3/`
(nuevo). No toca `src/` ni ningún backtest.

> **Actualización 2026-10-29 13:50 — el §1 "Problema 1" está RESUELTO.**
> Los 35 CSV existían en `/root/trading-bot-fix-fase2/data/` del VPS, en un
> directorio sin git. Se recuperaron, se verificaron **35/35 contra su
> sha256 sin un solo fallo** y se subieron a la rama `fase-b-recuperada`.
> El expediente **ya es reproducible**. Consecuencias para esta tarea:
> §3.1 cambia de objetivo — ya no hay que redescargar para recuperar los
> datos, pero **sigue valiendo la pena** redescargar y comparar para medir
> si el proveedor revisa sus históricos (es decir, si el congelado protege
> de verdad). §3.2 a §3.4 siguen igual: la ampliación de T es el objeto
> principal de la tarea.
**Duración estimada:** [estimado] 2-5 h de sesión, dominada por descargas.

---

## 1. Los dos problemas que resuelve

### Problema 1 — El expediente no es reproducible hoy

`data/multi/` y `data/multi_muertos/` contienen los `.meta.json` y los
`.sha256` de los 15 activos, pero **ningún `.csv`** (verificado por Sonnet
2026-10-29 con `git ls-files` y `ls`; reverificar en Fase 0). Los datos
reales viven en `/opt/trading-bot` del VPS, que no tiene remoto git.

Consecuencia: **los resultados de la Fase B no se pueden reejecutar desde
este repo por nadie.** Un expediente con esa cantidad de rigor metodológico
que no se puede reproducir tiene un agujero en la base, y además es el único
backup de ese trabajo.

### Problema 2 — T es la única palanca que juega a favor

`fase_b_reevaluacion_resultado.md`, Paquete 2: con N=12 trials hace falta
Sharpe ≥ 1.312 para DSR ≥ 0.95, y el observado es 1.008. De las tres
palancas (subir T, no subir N, encontrar más Sharpe), **subir T es la única
que no depende de tener suerte**: más observaciones efectivas bajan el
Sharpe mínimo exigido sin cambiar la estrategia ni añadir un trial.

Con datos diarios, T_eff = 4336 y el techo está puesto: no hay más historia
de cripto que la que hay. Con datos **horarios** desde 2017, el número de
observaciones sube en torno a un orden de magnitud [estimado, a calcular en
§3.4 con el dato real, no con esta estimación].

**Esta tarea prepara los datos y calcula el efecto. No ejecuta la estrategia
sobre ellos.** Ejecutarla sería un trial nuevo y exige pre-registro previo
aprobado por Pablo (regla del proyecto, `fase_b_reevaluacion_resultado.md`
Paquete 2: el cálculo de potencia se exige **a priori**).

---

## 2. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

### Paso A — Verificación de hechos

- [ ] Confirmar la ausencia de los `.csv` en `data/multi/` y
      `data/multi_muertos/`, y la presencia de `btc_usd_5y_1d.csv` y
      `paper_btc_usd_20261006T132915Z.csv`. Pegar el `ls` real.
- [ ] Verificar el sha256 de `btc_usd_5y_1d.csv` contra su `.sha256` y
      contra el campo `sha256` de su `.meta.json`. Si los tres no coinciden,
      es hallazgo CRÍTICO: significa que el procedimiento de congelado del
      proyecto no es fiable, y todo lo demás de esta tarea se apoya en él.
- [ ] Leer los 15 `.meta.json` y tabular: ticker, `period`, `interval`,
      `auto_adjust`, `n_velas`, `primera_fecha`, `ultima_fecha`,
      `fecha_descarga`. De ahí sale la fuente: son descargas de **yfinance**.
- [ ] **Comprobar que la sesión tiene red saliente** hacia: el servicio que
      usa yfinance, y la API pública de klines de Binance. Si no la hay,
      **parar y reportar**: sin red esta tarea no existe. Pegar la prueba.
- [ ] Confirmar que `fix-fase2/src/potencia_fase_b.py` se ejecuta (es la
      herramienta de §3.4) y pegar su salida actual.

### Paso B — Ataque adversarial al planteamiento de ESTA tarea

- ¿Cuál es la asunción más débil? (candidata honesta: que los datos
  horarios son "los mismos datos con más resolución". No lo son. A escala
  horaria el coste de transacción pesa muchísimo más, la microestructura
  importa, la autocorrelación cambia y el T_eff real **no** es el número de
  filas — hay solapamiento y los retornos horarios no son independientes.
  Si T_eff se calcula ingenuamente como "número de barras", el umbral de
  Sharpe saldrá artificialmente bajo y el DSR será una mentira cómoda.
  **Este punto es el riesgo central de la tarea y hay que atacarlo, no
  mencionarlo.**)
- ¿Qué alternativa se descartó sin justificar? (candidata: pedirle a Pablo
  los CSV del VPS por otra vía en lugar de redescargarlos, que daría
  reproducción exacta en vez de aproximada).
- ¿Es legítimo que una misma regla evaluada a otra frecuencia cuente como el
  mismo trial, o es un trial nuevo que sube N? Argumentar las dos lecturas y
  recomendar una. De esto depende si el esfuerzo tiene sentido.
- Si no encuentras objeción real, **di por qué no la encontraste**.

### Salida de la Fase 0

`## Registro de revisión némesis — S3` al final de este archivo, y **PARAR**.
Commit + push. La §3 no se ejecuta sin OK escrito de Pablo en §7.

---

## 3. Alcance (NO ejecutar hasta OK escrito de Pablo)

### 3.1 Reconstruir el dataset diario y medir si es reproducible

Para los 15 tickers de los `.meta.json` (10 supervivientes + 5 caídos):

1. Redescargar con **los mismos parámetros** que registra cada `.meta.json`
   (`period`, `interval`, `auto_adjust`).
2. **Recortar** al rango `[primera_fecha, ultima_fecha]` del meta, porque
   hoy es 2026-10-29 y las descargas originales son del 7 y 9 de octubre:
   sin recortar, el hash no puede casar nunca y la comparación no diría nada.
3. Comparar el sha256 del recorte con el `.sha256` congelado.
4. Para cada ticker donde no case, comparar **fila a fila** y reportar:
   cuántas filas difieren, en qué columnas, y de qué magnitud.

El resultado esperado honesto es que **no casen todos**: los proveedores
revisan históricos, y `auto_adjust` recalcula. Si es así, eso es un hallazgo
de primer orden sobre la reproducibilidad del expediente y hay que
documentarlo con esa importancia, no como una nota al pie. Si casan todos,
mejor: el expediente queda reproducible y hay que decirlo igual de claro.

Los CSV reconstruidos se guardan en `data/multi_reconstruido_20261029/` con
su `.sha256` y su `.meta.json` propios. **No se sobrescribe ni se toca nada
de `data/multi/` ni de `data/multi_muertos/`**: son evidencia congelada.

### 3.2 Datos horarios: evaluar fuentes antes de descargar

Comparar al menos dos fuentes públicas sin credenciales (la API pública de
klines de Binance es la candidata obvia por cobertura desde 2017; buscar y
evaluar al menos una segunda, p. ej. Kraken o Coinbase). Para cada una
documentar: cobertura temporal real por activo, límites de petición, si los
términos de uso permiten este uso, y formato.

Comprobar la cobertura **activo por activo** antes de dar por bueno nada: un
dataset horario que empieza en 2019 para la mitad de los activos no da el
T que esta tarea busca, y eso cambia la aritmética de §3.4.

Criterio de parada: si ninguna fuente gratuita cubre al menos los mismos 10
activos supervivientes desde 2018 con velas horarias, **la vía de subir T
por frecuencia no es viable**; se documenta y se termina ahí. Es un
resultado válido.

### 3.3 Descargar, congelar y decidir qué se commitea

- Descargar las velas horarias de los activos que superen §3.2.
- Congelar cada archivo con `.sha256` y `.meta.json` del mismo formato que
  los existentes (misma estructura de campos; coherencia con lo que ya hay).
- **Medir el tamaño total antes de commitear.** Decisión fijada de antemano,
  no a ojo: si el conjunto supera **50 MB**, no se commitean los CSV. Se
  commitea el script de descarga reproducible más los `.sha256` y
  `.meta.json`, y los CSV se dejan como artefacto del PR o se documenta cómo
  regenerarlos. Si queda por debajo de 50 MB, se commitean también los CSV.
- Sea cual sea el caso, el script de descarga **sí** se commitea siempre, es
  determinista y acepta un rango de fechas explícito. Esto es lo que evita
  repetir el problema 1 de §1.

### 3.4 Calcular el efecto real sobre el umbral (obligatorio)

Esta sección es la que justifica todo lo demás; sin ella la tarea no vale.

Con `fix-fase2/src/potencia_fase_b.py`:

1. Reproducir la tabla actual (N=12, T_eff=4336, skew 1.037, curtosis 32)
   y confirmar el 1.312.
2. Calcular el Sharpe mínimo exigido con el T de los datos horarios.
3. **No usar el número de barras como T_eff sin justificarlo.** Estimar el
   T efectivo teniendo en cuenta la autocorrelación de los retornos
   horarios, y documentar el método usado y de dónde sale. Dar las dos
   cifras —T ingenuo y T efectivo— y usar la conservadora.
4. Recalcular skew y curtosis sobre los retornos horarios: las colas a esa
   frecuencia no son las diarias, y entran directamente en la fórmula del
   DSR.
5. Entregar la comparación: umbral con datos diarios vs umbral con datos
   horarios, y **cuánta brecha cierra realmente**.

Si la conclusión es que apenas cierra brecha, o que la cierra solo bajo un
cálculo optimista de T_eff, decirlo así. Es información que ahorra semanas.

### 3.5 Lo que NO entra

- **No ejecutar ninguna estrategia sobre los datos nuevos.** Ni un backtest
  exploratorio, ni "solo por ver". Eso es un trial y exige pre-registro
  aprobado. Es la restricción más importante de esta tarea.
- No modificar ni borrar ningún archivo existente en `data/`.
- No cambiar métricas, umbrales ni parámetros del expediente.
- No usar ninguna API que exija credenciales, de pago o cuenta.

---

## 4. Restricciones NO-GO (bloqueantes)

- **NO-GO** — Ninguna credencial, API key, cuenta ni registro en ningún
  servicio. Solo endpoints públicos sin autenticación.
- **NO-GO** — No sobrescribir `data/multi/`, `data/multi_muertos/`,
  `btc_usd_5y_1d.csv` ni sus `.sha256` / `.meta.json`.
- **NO-GO** — No commitear datos sin su `.sha256` y su `.meta.json`. Un CSV
  sin procedencia registrada no entra en este repo.
- **NO-GO** — No ejecutar backtests (§3.5).
- **NO-GO** — No mergear a `main`. PR y nada más.
- **NO-GO** — No ejecutar §3 sin OK escrito de Pablo en §7.
- **NO-GO** — Si no hay red saliente, parar en Fase 0 y reportar. No
  sustituir datos reales por sintéticos para "poder continuar".

---

## 5. Definition of Done

- [ ] `## Registro de revisión némesis — S3` con los pasos A y B.
- [ ] `fix-fase2/docs/datos_reproducibilidad_s3.md` con: tabla ticker a
      ticker de §3.1 (¿casa el hash? si no, cuántas filas difieren y cuánto),
      comparativa de fuentes de §3.2, inventario de lo descargado en §3.3 con
      tamaños, y la tabla de umbrales de §3.4.
- [ ] Script de descarga determinista commiteado, con su documentación de uso.
- [ ] Veredicto explícito sobre las dos preguntas de la tarea:
      **¿es reproducible el expediente hoy?** y **¿cuánta brecha de DSR
      cierra realmente subir la frecuencia?**
- [ ] PR abierto contra `main`, sin mergear.

---

## 6. Decisiones bajo presión

- Descarga que tarda más de **30 minutos** para un solo activo: abortarla,
  anotar el caso, seguir con el siguiente.
- Fuente que devuelve error 429 o equivalente: respetar el límite con espera
  y reintentos acotados (**máximo 3**), y si sigue fallando, anotar el activo
  como no descargado. No forzar ni paralelizar para esquivar el límite.
- Discrepancia de hash en §3.1: **no es motivo de parada**, es el hallazgo.
  Se documenta y se sigue.
- Si el tamaño total queda entre 40 y 60 MB (zona de duda alrededor del
  umbral de §3.3): aplicar la regla conservadora, no commitear los CSV, y
  decirlo.

---

## 7. OK de Pablo

> Pendiente. Sin texto aquí, la §3 no se ejecuta.

---

## 8. Sincronía entre documentos

El hallazgo de §3.1 sobre reproducibilidad afecta a la credibilidad de los
cuatro dictámenes del expediente. Si no es reproducible, se anota en
`shared/estado-y-siguiente-paso.md` y en `shared/mapa-de-informacion.md`
—que es donde se registra que `/opt/criteria` y `/opt/trading-bot` no tienen
remoto git— además de en el informe de esta tarea.

---

## Registro de revisión némesis — S3

**Ejecutado:** 2026-11-01, sesión en la nube de Claude Code (contenedor
efímero, Linux 6.18, python 3.13.18).
**Rama base:** `fase-b-recuperada` @ `adad9e7`. **Rama de trabajo:**
`nube/s3-datos`.
**Alcance ejecutado:** solo §2 (Fase 0). §3 NO ejecutada: sin OK de Pablo en
§7 y, además, bloqueada por red (ver A.9 y B2).

---

### Paso A — Verificación de hechos

Cada afirmación del brief que depende de un hecho del repositorio, con el
comando real y su salida literal.

#### A.1 — El commit base del brief no es el HEAD de la rama

El brief declara base `d34b147`. Es el padre, no la punta.

```
$ git log --oneline -3
adad9e7 Anade los tres briefs de las sesiones en la nube (S1 auditoria del harness, S2 literatura, S3 ampliacion de T)
d34b147 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
663db2c Fase A rigor estadistico: DSR (Bailey-LdP 2014), block bootstrap, t>3, benchmark exposicion igualada — ninguna de las 11 variantes sobrevive
```

**Veredicto:** desviación menor, sin consecuencia. Se trabaja sobre `adad9e7`.

#### A.2 — Los CSV SÍ están en git: el "Problema 1" del §1 es falso por el lado de los datos

El §1 afirma: *"contienen los `.meta.json` y los `.sha256` de los 15
activos, pero **ningún `.csv`**"*. Falso.

```
$ git ls-files fix-fase2 | grep -ci '\.csv$'
40

$ git ls-files fix-fase2 | grep -i '\.csv$'
fix-fase2/data/btc_usd_5y_1d.csv
fix-fase2/data/multi/ada_usd_20261007.csv
fix-fase2/data/multi/ada_usd_20261009.csv
fix-fase2/data/multi/avax_usd_20261007.csv
fix-fase2/data/multi/avax_usd_20261009.csv
fix-fase2/data/multi/bnb_usd_20261007.csv
fix-fase2/data/multi/bnb_usd_20261009.csv
fix-fase2/data/multi/btc_usd_20261007.csv
fix-fase2/data/multi/btc_usd_20261009.csv
fix-fase2/data/multi/doge_usd_20261007.csv
fix-fase2/data/multi/doge_usd_20261009.csv
fix-fase2/data/multi/eth_usd_20261007.csv
fix-fase2/data/multi/eth_usd_20261009.csv
fix-fase2/data/multi/link_usd_20261007.csv
fix-fase2/data/multi/link_usd_20261009.csv
fix-fase2/data/multi/ltc_usd_20261007.csv
fix-fase2/data/multi/ltc_usd_20261009.csv
fix-fase2/data/multi/sol_usd_20261007.csv
fix-fase2/data/multi/sol_usd_20261009.csv
fix-fase2/data/multi/xrp_usd_20261007.csv
fix-fase2/data/multi/xrp_usd_20261009.csv
fix-fase2/data/multi_muertos/ada_usd_20261009.csv
fix-fase2/data/multi_muertos/avax_usd_20261009.csv
fix-fase2/data/multi_muertos/bch_usd_20261009.csv
fix-fase2/data/multi_muertos/bnb_usd_20261009.csv
fix-fase2/data/multi_muertos/btc_usd_20261009.csv
fix-fase2/data/multi_muertos/doge_usd_20261009.csv
fix-fase2/data/multi_muertos/eos_usd_20261009.csv
fix-fase2/data/multi_muertos/eth_usd_20261009.csv
fix-fase2/data/multi_muertos/fil_usd_20261009.csv
fix-fase2/data/multi_muertos/icp_usd_20261009.csv
fix-fase2/data/multi_muertos/link_usd_20261009.csv
fix-fase2/data/multi_muertos/ltc_usd_20261009.csv
fix-fase2/data/multi_muertos/sol_usd_20261009.csv
fix-fase2/data/multi_muertos/xlm_usd_20261009.csv
fix-fase2/data/multi_muertos/xrp_usd_20261009.csv
fix-fase2/results/portfolio_benchmark.csv
fix-fase2/results/portfolio_benchmark_muertos.csv
fix-fase2/results/portfolio_equity.csv
fix-fase2/results/portfolio_equity_muertos.csv
```

Desglose: 20 en `data/multi/` + 15 en `data/multi_muertos/` = **35 CSV de
datos congelados**, más `btc_usd_5y_1d.csv` y 4 CSV de resultados.

**Veredicto:** confirmado lo que dice la nota de N1. El `ls` que el brief
pedía pegar desmiente al propio brief.

#### A.3 — 35/35 verifican contra su `.sha256`

```
$ cd fix-fase2/data/multi && for f in *.csv; do exp=$(cut -d' ' -f1 "$f.sha256"); got=$(sha256sum "$f" | cut -d' ' -f1); [ "$exp" = "$got" ] && echo "OK   $f" || echo "FAIL $f"; done
OK   ada_usd_20261007.csv
OK   ada_usd_20261009.csv
OK   avax_usd_20261007.csv
OK   avax_usd_20261009.csv
OK   bnb_usd_20261007.csv
OK   bnb_usd_20261009.csv
OK   btc_usd_20261007.csv
OK   btc_usd_20261009.csv
OK   doge_usd_20261007.csv
OK   doge_usd_20261009.csv
OK   eth_usd_20261007.csv
OK   eth_usd_20261009.csv
OK   link_usd_20261007.csv
OK   link_usd_20261009.csv
OK   ltc_usd_20261007.csv
OK   ltc_usd_20261009.csv
OK   sol_usd_20261007.csv
OK   sol_usd_20261009.csv
OK   xrp_usd_20261007.csv
OK   xrp_usd_20261009.csv
---
OK=20 FAIL=0

$ cd fix-fase2/data/multi_muertos && (mismo bucle)
OK   ada_usd_20261009.csv
OK   avax_usd_20261009.csv
OK   bch_usd_20261009.csv
OK   bnb_usd_20261009.csv
OK   btc_usd_20261009.csv
OK   doge_usd_20261009.csv
OK   eos_usd_20261009.csv
OK   eth_usd_20261009.csv
OK   fil_usd_20261009.csv
OK   icp_usd_20261009.csv
OK   link_usd_20261009.csv
OK   ltc_usd_20261009.csv
OK   sol_usd_20261009.csv
OK   xlm_usd_20261009.csv
OK   xrp_usd_20261009.csv
---
OK=15 FAIL=0
```

**Veredicto:** 35/35, reverificado de forma independiente a N1. El
procedimiento de congelado es fiable **donde existe** (ver A.4).

#### A.4 — `btc_usd_5y_1d.csv` NO tiene `.sha256` ni `.meta.json`: la comprobación "CRÍTICA" del brief es inejecutable

El Paso A del brief pide verificar el sha256 de este fichero *"contra su
`.sha256` y contra el campo `sha256` de su `.meta.json`"*, y declara hallazgo
CRÍTICO si los tres no coinciden. No hay tres: hay uno.

```
$ ls -la fix-fase2/data/
total 164
drwxr-xr-x 5 root root   4096 Oct 31 10:45 .
drwxr-xr-x 7 root root   4096 Oct 31 10:45 ..
drwxr-xr-x 2 root root   4096 Oct 31 10:45 brain
-rw-r--r-- 1 root root 144506 Oct 31 10:45 btc_usd_5y_1d.csv
drwxr-xr-x 2 root root   4096 Oct 31 10:45 multi
drwxr-xr-x 2 root root   4096 Oct 31 10:45 multi_muertos
-rw-r--r-- 1 root root      0 Oct 31 10:45 paper_journal.db

$ sha256sum fix-fase2/data/btc_usd_5y_1d.csv
1c393a0095688754c8e5eeeca222077ca7f03eb493e080b50fc33c03b5dfc725  btc_usd_5y_1d.csv

$ head -2 fix-fase2/data/btc_usd_5y_1d.csv; tail -1 fix-fase2/data/btc_usd_5y_1d.csv; awk 'END{print "filas:", NR-1}' fix-fase2/data/btc_usd_5y_1d.csv
date,open,high,low,close,volume
2021-10-06,51486.6640625,55568.46484375,50488.19140625,55361.44921875,49034730168
2026-10-06,85750.578125,86368.796875,85133.7109375,86152.7109375,26399729664
filas: 1827
```

**Veredicto:** hallazgo real, distinto del que el brief anticipaba. Este CSV
está en el repo **sin procedencia registrada**, que es exactamente lo que el
§4 NO-GO nº3 prohíbe. El NO-GO ya está incumplido por el estado actual del
repo, no por nada que haga esta tarea. No es crítico para la Fase B (no lo
consume `portfolio_runner.py`, que usa `data/multi/`), pero sí para la
coherencia de la regla.

#### A.5 — `paper_btc_usd_20261006T132915Z.csv` no existe

El brief pide confirmar su presencia.

```
$ ls -la fix-fase2/data/paper_btc_usd_*
ls: cannot access 'paper_btc_usd_*': No such file or directory

$ git ls-files | grep -i 'paper_'
docs/paper_dashboard.html
docs/paper_runner_operacion.md
fix-fase2/data/paper_journal.db
fix-fase2/docs/paper_dashboard.html
fix-fase2/docs/paper_runner_operacion.md
fix-fase2/src/paper_runner.py
fix-fase2/verificar_paper_no_dinero_real.py
src/paper_runner.py
verificar_paper_no_dinero_real.py
```

`paper_journal.db` existe y pesa **0 bytes**.

**Veredicto:** afirmación falsa del brief. El fichero nunca llegó al repo
(lo escribiría `paper_runner.py:66`, que también sella con la fecha de
ejecución).

#### A.6 — Tabla de los `.meta.json`: son 35, no 15

El brief dice *"leer los 15 `.meta.json`"*. Hay **35** ficheros meta (uno por
CSV), que cubren **15 tickers distintos**: 10 en `multi/` (sellados dos veces,
20261007 y 20261009) y esos 10 más BCH, EOS, FIL, ICP y XLM en
`multi_muertos/`.

Comando: script python que lee cada meta, recuenta las filas del CSV
correspondiente y compara meta ↔ CSV. Salida literal:

```
dir           | ticker   | period | interval | auto_adj | n_velas_meta | filas_csv | 1a_meta    | 1a_csv     | ult_meta   | ult_csv    | descarga            | coherencia
--------------|----------|--------|----------|----------|--------------|-----------|------------|------------|------------|------------|---------------------|-----------
multi         | ADA-USD  | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:52 | OK
multi         | ADA-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:55 | OK
multi         | AVAX-USD | max    | 1d       | True     | 2209         | 2209      | 2020-07-13 | 2020-07-13 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:53 | OK
multi         | AVAX-USD | max    | 1d       | True     | 2211         | 2211      | 2020-07-13 | 2020-07-13 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:55 | OK
multi         | BNB-USD  | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:52 | OK
multi         | BNB-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:55 | OK
multi         | BTC-USD  | max    | 1d       | True     | 4404         | 4404      | 2014-09-17 | 2014-09-17 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:51 | OK
multi         | BTC-USD  | max    | 1d       | True     | 4406         | 4406      | 2014-09-17 | 2014-09-17 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:54 | OK
multi         | DOGE-USD | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:53 | OK
multi         | DOGE-USD | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:56 | OK
multi         | ETH-USD  | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:51 | OK
multi         | ETH-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:54 | OK
multi         | LINK-USD | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:53 | OK
multi         | LINK-USD | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:56 | OK
multi         | LTC-USD  | max    | 1d       | True     | 4404         | 4404      | 2014-09-17 | 2014-09-17 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:53 | OK
multi         | LTC-USD  | max    | 1d       | True     | 4406         | 4406      | 2014-09-17 | 2014-09-17 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:56 | OK
multi         | SOL-USD  | max    | 1d       | True     | 2372         | 2372      | 2020-04-10 | 2020-04-10 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:51 | OK
multi         | SOL-USD  | max    | 1d       | True     | 2374         | 2374      | 2020-04-10 | 2020-04-10 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:54 | OK
multi         | XRP-USD  | max    | 1d       | True     | 3255         | 3255      | 2017-11-09 | 2017-11-09 | 2026-10-07 | 2026-10-07 | 2026-10-07T18:33:52 | OK
multi         | XRP-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:09:55 | OK
multi_muertos | ADA-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:38 | OK
multi_muertos | AVAX-USD | max    | 1d       | True     | 2211         | 2211      | 2020-07-13 | 2020-07-13 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:39 | OK
multi_muertos | BCH-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:41 | OK
multi_muertos | BNB-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:38 | OK
multi_muertos | BTC-USD  | max    | 1d       | True     | 4406         | 4406      | 2014-09-17 | 2014-09-17 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:37 | OK
multi_muertos | DOGE-USD | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:39 | OK
multi_muertos | EOS-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:40 | OK
multi_muertos | ETH-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:37 | OK
multi_muertos | FIL-USD  | max    | 1d       | True     | 3223         | 3223      | 2017-12-13 | 2017-12-13 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:41 | OK
multi_muertos | ICP-USD  | max    | 1d       | True     | 1979         | 1979      | 2021-05-10 | 2021-05-10 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:41 | OK
multi_muertos | LINK-USD | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:39 | OK
multi_muertos | LTC-USD  | max    | 1d       | True     | 4406         | 4406      | 2014-09-17 | 2014-09-17 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:39 | OK
multi_muertos | SOL-USD  | max    | 1d       | True     | 2374         | 2374      | 2020-04-10 | 2020-04-10 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:37 | OK
multi_muertos | XLM-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:40 | OK
multi_muertos | XRP-USD  | max    | 1d       | True     | 3257         | 3257      | 2017-11-09 | 2017-11-09 | 2026-10-09 | 2026-10-09 | 2026-10-09T10:10:38 | OK

cabecera unica en todos: {'date,open,high,low,close,volume'}
```

**Veredicto:** coherencia meta ↔ CSV 35/35 (`n_velas`, `primera_fecha` y
`ultima_fecha` cuadran con el contenido real en todos). Todos los metas:
`period=max`, `interval=1d`, `auto_adjust=true`. Esquema de columnas idéntico
en los 35. La fuente es yfinance, como el brief supone (campos y convención de
`auto_adjust` son los de `yf.download`, y es lo que `portfolio_runner.py:131`
invoca).

**Techo real de historia diaria:** 2014-09-17 (BTC, LTC), 2017-11-09 (la
mayoría), 2020-04-10 (SOL), 2020-07-13 (AVAX), 2021-05-10 (ICP).

#### A.7 — Tamaño del conjunto

```
$ du -sh fix-fase2/data/multi fix-fase2/data/multi_muertos
6.2M	data/multi
4.5M	data/multi_muertos

$ find fix-fase2/data -name '*.csv' -printf '%s\n' | awk '{s+=$1} END {printf "CSV: %d ficheros, %.2f MB\n", NR, s/1048576}'
CSV: 36 ficheros, 10.40 MB

$ git count-objects -vH
count: 10
size-pack: 3.39 MiB
```

**Veredicto:** 10.40 MB de CSV, 3.39 MiB empaquetados. Muy por debajo del
umbral de 50 MB del §3.3. El diario cabe sin discusión; lo horario es otra
aritmética (ver B1, aunque B1 hace que sea irrelevante).

#### A.8 — El loader ignora los congelados y se va a la red: reverificado

La nota de la sesión lo señala en `portfolio_runner.py:122`. Reverificado aquí,
y además **el mismo defecto está en un segundo fichero**.

```
$ grep -rn "datetime.now(timezone.utc).strftime" fix-fase2/src/
src/portfolio_runner.py:122:        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
src/paper_runner.py:66:    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
src/portfolio_supervivencia.py:57:        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")

$ grep -rn "^DATA_DIR" fix-fase2/src/
src/portfolio_runner.py:41:DATA_DIR = "data/multi"
src/paper_runner.py:48:DATA_DIR = "data"
src/portfolio_supervivencia.py:42:DATA_DIR = "data/multi_muertos"
```

Código de `portfolio_runner.py:120-137`:

```
def load_or_download() -> dict:
    """Un CSV congelado por activo (+ sha256 + meta). Devuelve {ticker: df}."""
    os.makedirs(DATA_DIR, exist_ok=True)
    import yfinance as yf
    out = {}
    for ticker in ACTIVOS:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = os.path.join(DATA_DIR, f"{ticker.lower().replace('-', '_')}_{stamp}.csv")
        if os.path.exists(path):
            # ya congelado hoy: reutilizar (no re-descargar, hash preservado)
            ...
            continue
        df = yf.download(ticker, period="max", interval="1d",
                         auto_adjust=True, progress=False)
```

Prueba empírica del fallo de acceso:

```
$ date -u +%Y%m%d
20261101

$ python3 -c "from datetime import datetime,timezone; print('btc_usd_'+datetime.now(timezone.utc).strftime('%Y%m%d')+'.csv')"
btc_usd_20261101.csv

$ ls fix-fase2/data/multi/btc_usd_20261101.csv
ls: cannot access 'data/multi/btc_usd_20261101.csv': No such file or directory
```

**Veredicto:** confirmado, y ampliado. El sello congelado es `20261007` /
`20261009`; el que compone el loader hoy es `20261101`. `os.path.exists()`
devuelve False para los 10 activos, el `continue` no se ejecuta y la rama que
corre es `yf.download`. Con los 35 CSV delante y verificados, el harness los
ignora. El defecto afecta a **dos** scripts (`portfolio_runner.py:122` y
`portfolio_supervivencia.py:57`), no a uno; `paper_runner.py:66` tiene el mismo
patrón con sello de segundo, lo que lo hace irreproducible por construcción.

**Este es el verdadero "Problema 1".** No es que los datos falten: es que el
camino de lectura es una función de la fecha de ejecución. La reproducibilidad
del expediente está roto en el código, no en los datos.

#### A.9 — NO hay red saliente hacia ninguna de las dos fuentes: NO-GO del §4 activado

```
$ curl -sS -o /tmp/bn.json -w "HTTP %{http_code}\n" --max-time 25 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=2'
curl: (56) CONNECT tunnel failed, response 403
HTTP 000

$ curl -sS -o /tmp/yf.json -w "HTTP %{http_code}\n" --max-time 25 'https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD?range=5d&interval=1d'
curl: (56) CONNECT tunnel failed, response 403
HTTP 000
```

Confirmado por el propio proxy del entorno:

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
  "recentRelayFailures": [
    {
      "ts": "2026-11-01T10:29:32.943Z",
      "kind": "connect_rejected",
      "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
      "host": "api.binance.com:443"
    },
    {
      "ts": "2026-11-01T10:29:33.171Z",
      "kind": "connect_rejected",
      "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)",
      "host": "query1.finance.yahoo.com:443"
    }
  ]
```

**Veredicto:** la política de red de este entorno deniega `api.binance.com` y
`query1.finance.yahoo.com`. El §2 Paso A lo pedía como condición de existencia
de la tarea y el §4 lo declara NO-GO bloqueante: **§3 no es ejecutable en este
contenedor**, ni §3.1 ni §3.2 ni §3.3. Se para, como manda el brief, y no se
sustituye nada por datos sintéticos.

#### A.10 — Las dependencias de descarga tampoco están instaladas

```
$ python3 -c "import sys; print(sys.version.split()[0])
for m in ('pandas','numpy','scipy','yfinance','requests'): ..."
python   3.13.18
pandas     3.0.5
numpy      2.5.3
scipy      NO DISPONIBLE (ModuleNotFoundError)
yfinance   NO DISPONIBLE (ModuleNotFoundError)
requests   2.34.2
```

**Veredicto:** `yfinance` no está instalado, así que `portfolio_runner.py` ni
arrancaría aquí (importa yfinance dentro de `load_or_download`). `scipy`
tampoco, y aun así `potencia_fase_b.py` corre (A.11): la cadena DSR no lo
necesita. Segundo bloqueo independiente para §3.1.

#### A.11 — `potencia_fase_b.py` se ejecuta y reproduce el 1.312 de forma bit a bit

```
$ cd fix-fase2 && python3 src/potencia_fase_b.py
N=  1: SR0=0.00000 (diario)  Sharpe min para DSR>=0.95: 0.472 (anual)
N=  5: SR0=0.03160 (diario)  Sharpe min para DSR>=0.95: 1.073 (anual)
N= 12: SR0=0.04412 (diario)  Sharpe min para DSR>=0.95: 1.312 (anual)
N= 50: SR0=0.06032 (diario)  Sharpe min para DSR>=0.95: 1.622 (anual)
N=100: SR0=0.06706 (diario)  Sharpe min para DSR>=0.95: 1.751 (anual)

Sharpe min para t>3: 0.870 (anual) [t = SR*sqrt(T_eff), T_eff=4336]
Sharpe observado Fase B: 1.008 | brecha vs umbral N=12: +0.304
-> results/potencia_fase_b.json guardado
[exit=0]

$ git status --short
(vacío)
```

**Veredicto:** reproduce 1.312, 0.870 y la brecha +0.304. Y el
`results/potencia_fase_b.json` reescrito es **byte a byte idéntico** al
commiteado (`git status` limpio tras la reejecución): esta herramienta sí es
determinista. Contrasta con A.8.

#### A.12 — De dónde sale T_eff=4336, y qué autocorrelación supone

El 4336 no es un número puesto a mano: sale de `rigor_estadistico.py:110-120`,
corrección AR(1) del tamaño muestral.

```
def ar1_effective_n(returns):
    r = np.asarray(returns); r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0: return len(r)
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho = min(max(rho, -0.95), 0.95)
    n = len(r)
    return n * (1 - rho) / (1 + rho)
```

Reconstruido desde la equity commiteada:

```
$ python3 (lee results/portfolio_equity.csv, retornos simples, aplica ar1_effective_n)
PPY del proyecto = 365
1) ratio T_eff/T = 0.98478  ->  rho_AR1 implicito = 0.00767
2) retornos de results/portfolio_equity.csv: T=4403  rho_lag1=0.00756  ar1_effective_n=4336.9
```

Y en `results/portfolio_bateria.json`: `"n_obs": 4403, "n_obs_eff": 4336`.

**Veredicto:** T_eff=4336 reproducido exactamente desde los artefactos
commiteados. **La autocorrelación diaria de la estrategia es ρ=0.0076**: la
corrección AR(1) recorta 67 de 4403 observaciones (1.5 %). A frecuencia diaria
el ajuste es prácticamente inoperante. Este dato es la bisagra del Paso B.

#### A.13 — `.gitignore` protege la raíz, no `fix-fase2/`

```
$ cat .gitignore
venv/
__pycache__/
*.pyc
*.bak-*
trading-bot-fase1-audit.tar.gz
data/*.csv
data/*.db

$ git check-ignore -v fix-fase2/data/multi/btc_usd_20261009.csv
NO ignorado

$ git check-ignore -v data/btc_usd_5y_1d.csv
.gitignore:6:data/*.csv	data/btc_usd_5y_1d.csv
```

**Veredicto:** el patrón `data/*.csv` lleva `/`, así que está anclado a la raíz
del repo y no alcanza `fix-fase2/data/`. Por eso los 35 CSV pudieron
commitearse. Mina pendiente para §3.3: cualquier script de descarga que
escriba en `data/` **desde la raíz** será ignorado en silencio y recreará el
problema original. No hay `fix-fase2/.gitignore`.

#### A.14 — Contradicciones internas del brief

| Dónde | Dice | Contradice |
|---|---|---|
| §1 Problema 1 | datos en `/opt/trading-bot` del VPS | la actualización del 2026-10-29 13:50 dice `/root/trading-bot-fix-fase2/data/` |
| §5 DoD | "PR abierto contra `main`" | cabecera y §4 NO-GO ("No mergear a `main`"), e instrucción de esta sesión: PR contra `fase-b-recuperada` |
| §3.1 paso 2 | "hoy es 2026-10-29" | hoy es 2026-11-01 |
| §2 Paso A | "los 15 `.meta.json`" | hay 35 (A.6) |
| §2 Paso A | presencia de `paper_btc_usd_…csv` | no existe (A.5) |
| §2 Paso A | ausencia de los `.csv` | están los 35 (A.2) |

Se resuelve el PR contra `fase-b-recuperada`, según la instrucción de esta
sesión.

#### A.15 — Qué parte del "Problema 1" sigue en pie

| Afirmación del §1 | Estado |
|---|---|
| No hay CSV en `data/multi/` ni `data/multi_muertos/` | **FALSA** (A.2) |
| El congelado no es fiable | **FALSA** donde existe: 35/35 (A.3) |
| El expediente no se puede reejecutar desde este repo | **CIERTA, por otra causa**: el loader no encuentra los CSV (A.8) y no hay red para la alternativa (A.9) |
| Es el único backup de ese trabajo | ya resuelto: está en git |

Sobra: todo el §3.1 en su función de recuperación, y la justificación del
"único backup".
Sigue en pie: la no-reproducibilidad, con causa distinta. El §3.1 en su función
de *medir si el proveedor revisa históricos* conserva sentido, pero es
secundario y aquí es inejecutable (A.9, A.10).

---

### Paso B — Ataque adversarial

#### B1 — BLOQUEANTE. El objetivo de la tarea es nulo: cambiar de frecuencia no mueve el umbral. Lo mueve el error de unidades

El brief apuesta a que pasar de diario a horario sube T un orden de magnitud y
baja el Sharpe exigido. **Es falso, y es demostrable con el código que ya hay.**

**Demostración algebraica.** Para la misma ventana de calendario, remuestreada
a frecuencia k veces mayor, con retornos aproximadamente i.i.d.:
media_h = media_d/k, desv_h = desv_d/√k, T_h = k·T_d. Entonces

```
t_h = (media_d/k)/(desv_d/√k) · √(k·T_d) = (media_d/desv_d)·√T_d = t_d
```

El estadístico t es **exactamente invariante** a la frecuencia de muestreo. El
Sharpe anualizado también lo es por construcción. Lo único que cambia es el par
(T_eff, PPY), y cambia de forma compensada: T_eff ×k y PPY ×k.

**Verificación numérica con el umbral t>3 del expediente:**

```
3) Sharpe anual min para t>3:  diario(T=4336,PPY=365) = 0.8704   horario(T=104064,PPY=8760) = 0.8704   delta = +0.000000
```

Cero. No se cierra ni una milésima.

**Y el umbral DSR, recalculado con las funciones reales de
`rigor_estadistico.py`** (`psr`, `expected_max_sharpe`), N=12, reescalando a
unidades horarias lo que hay que reescalar (`var_trials` → V/24, porque la
varianza cross-trial de Sharpes por periodo escala con 1/k; `PPY` → 8760):

```
caso                                                              T_eff    PPY    sr0_per  Sharpe_min_anual
DIARIO (expediente)                                                4336    365   0.044116             1.312
HORARIO, misma ventana, colas=diarias [hipotetico]               104064   8760   0.009005             1.317
HORARIO, colas horarias kurt=150 skew=0.5 [no verificado]        104064   8760   0.009005             1.320
HORARIO, colas horarias kurt=400 skew=0.0 [no verificado]        104064   8760   0.009005             1.325
HORARIO con T_eff INGENUO (sin reescalar V ni PPY) [el error]     104064    365   0.044116            0.939

Observado Fase B: 1.008 anual
```

Tres lecturas, todas importantes:

1. **Bien calculado, el umbral horario SUBE** (1.312 → 1.317…1.325). No baja.
   El motivo es exacto: el numerador de la PSR, (SR_per − SR₀_per)·√(T−1), es
   invariante (SR₀_per cae justo √24: 0.044116/√24 = 0.009005, comprobado). Lo
   único que se mueve es el denominador
   √(1 − skew·SR_per + (kurt−1)/4·SR_per²): a frecuencia horaria SR_per es 24
   veces más pequeño en varianza, el denominador tiende a 1, y el skew diario
   positivo (1.037) que hoy **baja** el denominador y por tanto **ayuda** deja
   de ayudar. El efecto neto de ir a horario es **adverso**.
2. **La única manera de obtener el beneficio que el brief promete es el error
   exacto que el propio brief advierte**: inflar T_eff ×24 dejando `PPY` y
   `var_trials` en unidades diarias. Da 0.939 — por debajo del 1.008 observado.
   Es decir: el atajo "aprueba" la estrategia, y aprueba por un fallo de
   unidades, no por información nueva. Si alguien ejecuta §3.4 sin cuidado, el
   resultado no será un umbral bajo: será un DSR falso que da luz verde a una
   estrategia que no la tiene.
3. **La razón de fondo:** la precisión con la que se estima un Sharpe está
   dominada por la deriva, no por la volatilidad. Muestrear más fino mejora
   mucho la estimación de σ (la varianza realizada converge con la frecuencia)
   y **no mejora nada** la de μ, cuya precisión depende solo de la longitud de
   la ventana de calendario. El Sharpe hereda ese límite. Más resolución sobre
   la misma ventana no es más información sobre si hay edge: es la misma
   información escrita con más decimales.

**Qué palanca queda realmente.** T_eff solo sube con **ventana de calendario**.
Cuánta haría falta para que el umbral baje al 1.008 observado, con N=12:

```
T_eff diario necesario para umbral = 1.008 anual: 35000  (95.9 anos de ventana)
T_eff actual: 4336 (11.9 anos). Factor necesario: x8.07

  T_eff=  4336 ( 11.9 anos)  umbral = 1.312
  T_eff=  6000 ( 16.4 anos)  umbral = 1.241
  T_eff=  8000 ( 21.9 anos)  umbral = 1.188
  T_eff= 10950 ( 30.0 anos)  umbral = 1.138
  T_eff= 20000 ( 54.8 anos)  umbral = 1.061
  T_eff= 50000 (137.0 anos)  umbral = 0.981
```

**96 años de historia.** No existen, ni los va a haber en cripto, ni los compra
ningún forward test. **La palanca T está muerta, no limitada.** El §2 del brief
("subir T es la única que no depende de tener suerte") es verdad en la forma y
falso en el fondo: es la única que no depende de la suerte *y* la única que es
aritméticamente inalcanzable.

**Gravedad: BLOQUEANTE.** Invalida el objetivo entero de la tarea. §3.2, §3.3 y
§3.4 no deben ejecutarse: gastarían horas de descarga y almacenamiento para
llegar a un umbral igual o peor.

**Propuesta:**
- Cancelar §3.2 y §3.3 (fuentes horarias y descarga). No hay nada que comprar.
- Reescribir §3.4 como lo que sí vale: documentar esta invariancia con la tabla
  de arriba, dejarla en `fase_b_reevaluacion_resultado.md` y cerrar la palanca T
  por escrito, para que no se reabra en tres meses.
- Conservar §3.1 **solo** en su función de medir revisiones del proveedor, y
  degradarla de prioridad.
- Aceptar que con N=12 y Sharpe 1.008 el DSR≥0.95 es inalcanzable por datos. Lo
  que queda sobre la mesa son dos cosas honestas, y ninguna es técnica: (a)
  justificar a priori un umbral de confianza distinto de 0.95 y re-dictaminar
  con esa regla, o (b) sostener el veredicto "SEÑAL DÉBIL" y dejar de buscar
  palancas. Decisión de Pablo, no de esta tarea.

#### B2 — BLOQUEANTE. Sin red, §3 no existe en este entorno

Verificado en A.9: la política de red deniega `api.binance.com` y
`query1.finance.yahoo.com` con 403 al CONNECT. El §2 Paso A lo exigía como
condición y el §4 lo declara NO-GO.

**Gravedad: BLOQUEANTE** (de ejecución, independiente de B1). Aunque Pablo
escribiera el OK en §7, §3.1/§3.2/§3.3 fallarían aquí.

**Propuesta:** no abrir la red. B1 hace que no valga la pena: habilitar hosts
para descargar datos que no compran nada es coste sin retorno. Si en algún
momento se quiere solo §3.1 (medir revisiones del proveedor), hace falta
habilitar `query1.finance.yahoo.com` en los dominios permitidos del entorno
(menú del entorno en la barra de título → Edit → Network access) e instalar
`yfinance`. No antes de que Pablo decida sobre B1.

#### B3 — GRAVE. El estimador de T_eff: qué está mal y qué propongo

El riesgo que el brief señala es real, pero está mal localizado. No es que
"contar barras infle T": es que **el estimador actual no detectaría el
problema si existiera**.

Estado actual (A.12): `ar1_effective_n` aplica T·(1−ρ)/(1+ρ) con ρ el lag-1 de
los **retornos de la estrategia**. Eso es correcto *en especie* — mide el
solapamiento efectivo de la serie que entra en el Sharpe, no de los precios —
pero tiene dos defectos:

1. **Solo ve el lag 1.** La corrección de Bartlett/Lo completa es
   T_eff = T / (1 + 2·Σ_{j=1}^{q} (1−j/(q+1))·ρ_j). Una estrategia que mantiene
   posición h periodos induce autocorrelación positiva en **todos** los lags
   hasta h, no solo en el primero. A diario, con ρ₁=0.0076 y una señal de
   lookback 365 y rebalanceo diario, el AR(1) da 4336 y el truncamiento no
   importa porque todos los ρ_j son ruido. A horario, con la misma regla en
   tiempo de reloj, los ρ_j serían grandes hasta j≈24 y el AR(1) los ignoraría:
   devolvería un T_eff próximo al número de barras y **ahí sí** se produciría el
   T inflado. El estimador actual es seguro solo por accidente de la frecuencia.
2. **No está acotado por el número de episodios independientes.** El límite duro
   no es estadístico: una estrategia con h horas de tenencia media sobre una
   ventana de H horas tiene del orden de H/h episodios independientes, y ese
   número **no cambia** al remuestrear más fino.

**Estimador que propongo**, en este orden:

- **Primario — HAC / Newey-West con ancho de banda por regla de Andrews.**
  T_eff = T / (1 + 2·Σ_{j=1}^{q} w_j·ρ̂_j), pesos de Bartlett w_j = 1 − j/(q+1),
  q seleccionado por la regla automática de Andrews (1991) o, como mínimo,
  q = ⌈frecuencia × tenencia_media_en_dias⌉. Es la corrección de Lo (2002) para
  el Sharpe con retornos autocorrelados y es la referencia estándar; encaja con
  el linaje Bailey-López de Prado que ya usa el expediente y se implementa en
  veinte líneas sobre `rigor_estadistico.py` sin tocar `psr`.
- **Cota superior obligatoria — recuento de episodios.**
  T_eff ≤ ventana_total / tenencia_media. Se toma el **mínimo** entre el HAC y
  esta cota. Es la que impide que un remuestreo fino compre T de la nada.
- **Validación — block bootstrap.** El repo ya tiene `block_bootstrap_ci`.
  Comparar la desviación típica del Sharpe que da el bootstrap por bloques
  (bloque = 2×tenencia) con la implícita en el T_eff elegido. Si el bootstrap
  da una desviación mayor, el T_eff es optimista y se usa el del bootstrap.
- **Criterio de aceptación:** ninguna cifra de T_eff vale sin las tres juntas,
  y se usa la más conservadora. La regla ya está en el §3.4 punto 3 del brief;
  lo que falta es el estimador, y es este.

**Gravedad: GRAVE.** Es un defecto latente del harness, no solo de esta tarea:
`ar1_effective_n` se usa en `rigor_estadistico.py:174`,
`portfolio_bateria.py:83` y `portfolio_walkforward_temporal.py:61`. A frecuencia
diaria no hace daño (ρ₁=0.0076, A.12); a cualquier frecuencia intradía sería un
inflador de DSR.

**Matiz honesto:** aplicar este estimador **no rescata** la tarea. Refuerza B1.
El HAC bien aplicado a datos horarios devolvería un T_eff cercano al diario
(mismos episodios, misma ventana), y el umbral se quedaría en ~1.31. La
pregunta "qué estimador de T_eff propondrías" tiene respuesta, pero la respuesta
no es un rescate: es la confirmación de que no había nada que estimar.

#### B4 — GRAVE. El test de hash del §3.1 no puede distinguir su propia hipótesis del ruido de formato

§3.1 propone redescargar, recortar al rango del meta, comparar sha256 y, si no
casa, concluir que el proveedor revisa históricos. El test no aísla esa
hipótesis. Un hash puede fallar por: versión de pandas al serializar float64
(los congelados llevan `465.864013671875`, repr completo), orden de columnas,
`index_label`, final de línea, zona horaria del índice, o `auto_adjust`
recalculando. Los congelados se escribieron con el entorno del VPS; este
contenedor trae pandas 3.0.5 y numpy 2.5.3 (A.10) [no verificado qué versiones
escribieron los originales: los metas no registran versión de librería]. Un
fallo de hash sería el resultado esperado **sin que el proveedor haya tocado
nada**, y el brief lo leería como "hallazgo de primer orden".

**Gravedad: GRAVE** si §3.1 llega a ejecutarse: produciría una conclusión falsa
con aire de rigor.

**Propuesta:** invertir el orden. Test primario = comparación numérica fila a
fila sobre `(date, open, high, low, close, volume)` con tolerancia relativa
explícita (p. ej. 1e-9) e informe de filas discrepantes, columnas y magnitud —
que ya es el paso 4 del §3.1. El hash pasa a secundario y solo se interpreta
**si** la comparación numérica casa: hash distinto + números idénticos = ruido
de serialización, y entonces la conclusión correcta es que **el `.sha256` no es
un verificador de reproducibilidad entre entornos**, solo de integridad del
fichero. Y añadir al `.meta.json` las versiones de python/pandas/yfinance, que
hoy no están.

#### B5 — GRAVE. §3 no arregla el defecto que de verdad rompe la reproducibilidad, y lo recrearía

Verificado en A.8: lo que impide reejecutar la Fase B es que
`portfolio_runner.py:122` y `portfolio_supervivencia.py:57` construyen la ruta
del CSV con `datetime.now()`. El §3 entero no toca eso — su alcance físico
excluye `src/` explícitamente. Y el §3.3 pide "un script de descarga
determinista" que, escrito con el mismo patrón, nacería con el mismo defecto.
Súmese A.13: si ese script escribe en `data/` desde la raíz, `.gitignore:6` lo
ignora en silencio.

**Gravedad: GRAVE.** El brief dice que el §3.3 "es lo que evita repetir el
problema 1", y es la afirmación que menos se sostiene: el problema 1 no fue de
descarga, fue de ruta y de git.

**Propuesta:** tarea aparte, pequeña y de valor inmediato, independiente de
B1 y de la red:
1. En `portfolio_runner.py` y `portfolio_supervivencia.py`, sustituir el sello
   `datetime.now()` por un `--as-of AAAAMMDD` explícito, con *fallback* al sello
   más reciente que exista en `DATA_DIR` y fallo ruidoso si no hay ninguno. No
   descargar nunca de forma implícita: `--download` explícito.
2. Añadir `fix-fase2/verificar_congelados.py`: recorre `data/**`, comprueba los
   35 sha256 y la coherencia meta ↔ CSV. Es el bucle de A.3 + A.6, ya escrito.
3. Dar a `btc_usd_5y_1d.csv` su `.sha256` y su `.meta.json`, o sacarlo del repo
   (A.4).
4. Crear `fix-fase2/.gitignore` que **no** herede el patrón de la raíz, o
   cambiar el de la raíz a `/data/*.csv` para dejar la intención explícita.

Esto sí deja el expediente reproducible, cuesta poco y no gasta un trial.

#### B6 — MEDIO. ¿Es la misma regla a otra frecuencia el mismo trial?

Las dos lecturas, como pide el brief:

**Es el mismo trial.** La hipótesis económica no cambia: misma señal, mismo
universo, mismos parámetros en tiempo de reloj. La frecuencia de muestreo es
detalle de implementación, igual que no se cuenta un trial nuevo por cambiar de
precios de cierre a VWAP diario. Bajo esta lectura N sigue en 12.

**Es un trial nuevo.** El DSR penaliza el número de configuraciones **probadas
sobre los datos**. Cambiar de frecuencia cambia la serie de retornos, cambia el
coste de transacción efectivo, cambia qué señales disparan y cambia el
resultado. Si el resultado puede ser distinto, es una configuración distinta, y
el que se mire después del diario es precisamente la definición de data
snooping que el DSR corrige. Bajo esta lectura N pasa a 13 y el umbral **sube**.

**Recomendación: es un trial nuevo.** Dos razones. La formal: Bailey-López de
Prado cuentan configuraciones evaluadas, no hipótesis económicas, porque es el
número de evaluaciones lo que genera el sesgo de selección. La práctica: la
lectura "mismo trial" tiene un incentivo evidente — es la que no castiga — y
eso ya es motivo para desconfiar de ella. Con N=13 el umbral sería algo mayor
que 1.312, lo que combinado con B1 significa que ejecutar la variante horaria
**empeora** el veredicto por dos vías a la vez: sube el umbral por N y lo sube
por colas. El cálculo de 13 no lo he hecho porque B1 hace la variante
inejecutable de todos modos.

Consecuencia operativa: la pregunta del brief ("de esto depende si el esfuerzo
tiene sentido") tiene respuesta clara y es **no**.

#### B7 — MEDIO. El §4 NO-GO nº3 ya está incumplido por el repo

"No commitear datos sin su `.sha256` y su `.meta.json`."
`fix-fase2/data/btc_usd_5y_1d.csv` está commiteado, pesa 144 506 bytes, cubre
2021-10-06 → 2026-10-06 con 1827 filas y **no tiene ninguno de los dos** (A.4).
No es grave en sustancia — no lo consume la Fase B — pero una regla NO-GO que
el propio repo viola deja de funcionar como regla.

**Propuesta:** punto 3 de B5.

#### B8 — MEDIO. Aunque T funcionara, el coste de transacción horario se come el edge

Fuera del alcance de esta tarea medirlo, pero condiciona el valor de §3.3: la
exposición media del expediente es 0.156
(`results/portfolio_bateria.json: "exposicion_media": 0.1559827260735808`) con
rebalanceo diario. La misma regla evaluada sobre barras horarias rebalancearía
hasta 24 veces más a menudo salvo que se congele la frecuencia de rebalanceo —
y si se congela, los retornos horarios son los diarios interpolados y no hay
observaciones nuevas, que es B1 por otro camino. Es una tenaza: o se rebalancea
más y el coste mata el Sharpe, o no se rebalancea más y no hay T nuevo.

**Gravedad: MEDIO.** Cierra la última salida de B1.

**Propuesta:** si alguien insiste en la vía horaria pese a B1, exigir como
pre-registro el coste por vuelta y la rotación implícita **antes** de descargar
nada, y el criterio de parada: si el coste estimado reduce el Sharpe por debajo
de 1.008, no se descarga.

#### B9 — LEVE. La alternativa que el brief dice no haberse justificado ya es irrelevante

El brief pregunta por "pedirle a Pablo los CSV del VPS en lugar de
redescargarlos". Esa alternativa **ya se ejecutó** y es la que resolvió el
problema: los 35 CSV están en git y verifican (A.2, A.3). La objeción es
correcta en el fondo y llega tarde.

**Gravedad: LEVE**, histórica. Sirve como lección: la pregunta "¿se puede
conseguir el dato exacto en vez de una aproximación?" se contestó sola y la
respuesta era sí.

#### B10 — LEVE. Seis afirmaciones de hecho falsas o desactualizadas en el brief

Tabuladas en A.14. Tres de ellas (ausencia de CSV, los 15 metas, el
`paper_btc_usd_*`) son instrucciones del propio Paso A que piden verificar
hechos que no se cumplen. Una (PR contra `main`) contradice un NO-GO del mismo
documento.

**Gravedad: LEVE** por sí misma, pero con un patrón detrás: el brief se escribió
sin ejecutar un solo comando contra el repo. Es lo que la Fase 0 existe para
atrapar, y lo ha atrapado dos veces seguidas (N1 y esta).

**Propuesta:** regla para los briefs futuros — ninguna afirmación de hecho sobre
el estado del repo entra en un brief sin su comando y su salida pegados, igual
que se exige en los registros némesis.

---

### Veredicto de la Fase 0

**§3 NO debe ejecutarse.** No por falta de OK, y no solo por la red: porque el
objetivo es nulo.

1. **La palanca T está muerta, no limitada** (B1). Pasar a horario no baja el
   umbral: lo deja igual en t>3 (invariancia exacta, delta 0.000000) y lo sube
   en DSR (1.312 → 1.317…1.325). El único cálculo que produce la mejora
   prometida (0.939) es un error de unidades que daría luz verde falsa a una
   estrategia con Sharpe 1.008. Cerrar la brecha por ventana de calendario
   exigiría **96 años** de historia.
2. **El expediente no es reproducible hoy, y la causa no es la que el brief
   supone** (A.8, B5). Los datos están y verifican 35/35. Lo que está roto es
   el loader, que compone la ruta con `datetime.now()` en dos scripts. Se
   arregla en una tarea pequeña que no necesita red ni descargas.
3. **El estimador de T_eff del harness es seguro por accidente** (A.12, B3).
   ρ₁=0.0076 a diario hace que el AR(1) sea inocuo; a cualquier frecuencia
   intradía inflaría T. Propuesta en B3: HAC/Newey-West con ancho de Andrews,
   acotado por recuento de episodios y validado con el block bootstrap que ya
   existe.
4. **Evaluar la misma regla a otra frecuencia sería un trial nuevo** (B6), lo
   que subiría N a 13 y el umbral con él.

Lo que esta sesión recomienda, por orden de valor:

- **Decidir sobre B1 antes que nada.** Es una decisión de Pablo: o se cambia la
  regla de decisión con justificación a priori, o se sostiene el "SEÑAL DÉBIL".
  No hay tercera vía por datos.
- **Autorizar la tarea de B5** (arreglar loader + verificador + procedencia de
  `btc_usd_5y_1d.csv` + `.gitignore`). Barata, no gasta trial, y es lo único que
  deja el expediente reproducible de verdad.
- **Arreglar B3** cuando se toque cualquier cosa intradía. Hoy no urge.
- **Cancelar §3.2 y §3.3.** Reescribir §3.4 como el acta de cierre de la palanca
  T, con la tabla de B1.

Nada de esto se ha ejecutado. Esta rama solo añade este registro.
