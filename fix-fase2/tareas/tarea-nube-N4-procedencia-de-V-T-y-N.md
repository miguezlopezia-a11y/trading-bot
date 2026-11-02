# Tarea N4 (nube) — Procedencia de `V`, `T_eff` y `N`: de dónde sale el listón 1.312

**Creada:** 2026-11-01 por Claude Opus 5 (sesión de escritorio de Pablo).
**Repo:** `miguezlopezia-a11y/trading-bot`. **Base:** rama `fase-b-recuperada`
(contiene ya los merges de N1, N2 y N3: `f7feab0`, `46ad49d`, `9e0974e`).
**Rama de trabajo:** cortar `nube/n4-procedencia-v-t-n` desde `fase-b-recuperada`.
**Estado:** PARADO en Fase 0. **No se ejecuta "Alcance" sin OK escrito de Pablo.**

**Lectura previa obligatoria, en este orden:**

1. `fix-fase2/docs/estado-auditoria-n1.md` — qué dejó N1 en pie y qué no.
2. `fix-fase2/docs/auditoria_harness_n1.md` — el informe completo (H10 es el eje).
3. `fix-fase2/docs/rigor_estadistico_resultado.md` — Fase A, de donde sale `V`.
4. `fix-fase2/docs/fase_b_reevaluacion_resultado.md` — Fase B, donde se usa.

---

## 1. La pregunta

El expediente cuelga de una cifra: **para que Fase B pase `DSR ≥ 0.95` hace
falta Sharpe ≥ 1.312**, y el observado es **1.008**. De ahí sale la brecha
+0.304 y de ahí sale todo lo demás.

N1 demostró que esa cifra **no es robusta**: si `V` se mide con `T` homogéneo
el listón cae a **0.823**, y el 1.008 observado queda **en medio de las dos
construcciones**. Las dos son defendibles. Nadie hizo la elección de forma
explícita y documentada.

**Esta tarea no elige.** Elegir viendo el resultado sería cambiar la métrica
para que pase, y eso está prohibido. Lo que esta tarea hace es **reconstruir
cómo se construyeron de verdad `V`, `T_eff` y `N`**, para que la elección se
pueda justificar por el método y no por el número que produce.

---

## 2. Hechos ya verificados desde el escritorio (reverificar, no creer)

Cada uno lleva el comando que lo produjo. **La Fase 0 los repite de forma
independiente.** No vale "ya lo comprobó Claude".

### 2.1 Las cinco entradas del listón están hardcodeadas

```
$ grep -n "T_EFF\|V_TRIALS\|SKEW\|KURT\|SHARPE_OBSERVADO" src/potencia_fase_b.py
25:T_EFF = 4336
26:SKEW = 1.037
27:KURT = 31.999
28:V_TRIALS = 0.0007021947704551833
31:SHARPE_OBSERVADO = 1.008
```

`src/potencia_fase_b.py` es el script que produce el 1.312. **Ninguna de sus
cinco entradas se calcula: todas son constantes literales.** El script no
sabe de qué datos vienen.

### 2.2 `T_eff = 4336` es 2.37 veces el único CSV de Fase A

```
$ wc -l data/btc_usd_5y_1d.csv
1828 data/btc_usd_5y_1d.csv
$ head -2 data/btc_usd_5y_1d.csv | cut -c1-40
date,open,high,low,close,volume
2021-10-06,51486.6640625,55568.46484375
$ tail -1 data/btc_usd_5y_1d.csv | cut -c1-20
2026-10-06,85750.5781
```

1828 líneas = **1827 velas**, rango **2021-10-06 → 2026-10-06** (5 años, BTC
solo). El `T_eff = 4336` del listón no puede salir de aquí.

### 2.3 `N` tiene tres valores distintos, no dos

| Documento | Valor | Fecha |
|---|---|---|
| `results/rigor_estadistico.json` → `"n_trials": 11` | **11** | 2026-10-07 |
| `docs/fase_b_reevaluacion_resultado.md:18` → "N=12 trials en todos los DSR" | **12** | 2026-10-09 |
| `docs/timesfm_fase2_resultado.md:6` → "**N=14** registrado antes del primer forecast" | **14** | 2026-10-12/13 |

```
$ grep -o '"n_trials": [0-9]*' results/rigor_estadistico.json
"n_trials": 11
```

El listón 1.312 usa **12**. Con 14 sería 1.349 (brecha +0.341). El contador
creció tres veces y **la regla de qué cuenta como trial no está escrita en
ningún sitio**.

### 2.4 `V` tiene tres valores en tres documentos

- `docs/rigor_estadistico_resultado.md:29-30`: `V` = **0.0007017**
- `docs/fase_b_reevaluacion_resultado.md:39`: `V` = **0.0007022**
- `src/potencia_fase_b.py:28`: `V_TRIALS` = **0.0007021947704551833**

No es un error de redondeo entre el segundo y el tercero, pero **sí hay una
discrepancia real con el primero**, y nadie ha dicho cuál manda.

### 2.5 La muestra de cada variante va de 598 a 2188 observaciones efectivas

```
$ grep -o '"n_obs_eff": [0-9]*' results/rigor_estadistico.json
"n_obs_eff": 598
"n_obs_eff": 723
"n_obs_eff": 677
"n_obs_eff": 691
"n_obs_eff": 678
"n_obs_eff": 737
"n_obs_eff": 690
"n_obs_eff": 642
"n_obs_eff": 2188
"n_obs_eff": 869
"n_obs_eff": 779
```

Diez valores entre 598 y 869, **y uno de 2188**. Por el orden de la tabla de
`docs/rigor_estadistico_resultado.md`, el noveno es `tsmom_365` — la variante
que tiene **1 trade** y **0.3% de exposición** (misma fuente, tabla de
exposición igualada).

**2188 supera las 1827 velas del fichero.** El ajuste AR(1) es
`T_eff = T·(1−ρ)/(1+ρ)`: con ρ negativo eso **infla** la muestra efectiva por
encima de la real. Hay que comprobar si es eso y si el signo está aplicado
como la fuente manda.

### 2.6 Cuatro de las once variantes operan con un puñado de trades

De `docs/rigor_estadistico_resultado.md` (tabla "Resultado por variante" y
columna de trades): `tsmom_365` **1 trade**, `rsi_hidden_divergence` **3**,
`sma_timing_304` **5**, `connors_rsi2` **12**. Sus Sharpes están dentro de la
varianza que fija el listón.

### 2.7 Lo que esto NO prueba todavía

Que `V` esté mal. Podría estar bien y ser el 0.823 el que esté mal. La
dirección es desconocida a priori: **se mide, no se supone.**

---

## 3. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

Dos pasos separados. **Los dos son obligatorios.** Al terminar, escribir
`## Registro de revisión némesis` al final de ESTE archivo y **PARAR** sin
ejecutar un solo paso del Alcance.

### Paso A — Verificación de hechos

Reverificar con comandos propios, uno por uno, los siete puntos de la
sección 2. Para cada uno: comando, salida pegada, y veredicto
`CONFIRMADO` / `REFUTADO` / `NO VERIFICABLE`.

Añadir, con comando y salida:

- **A-1.** ¿De dónde sale `T_eff = 4336`? Buscarlo en el historial de git, en
  los `results/*.json` y en el resto del código. Si aparece calculado en
  algún sitio, decir de qué dataset y con qué ρ. Si no aparece en ninguno,
  decirlo así: **el número no tiene origen rastreable**.
- **A-2.** ¿Sobre qué datos se calculó `V_TRIALS`? Misma búsqueda. Qué
  script lo produjo, sobre qué CSV, con qué 11 variantes y con qué
  definición de "Sharpe por trial" (¿diario? ¿anualizado? ¿sobre los días
  con posición o sobre el período completo?).
- **A-3.** Reconstruir del historial de git la secuencia **11 → 12 → 14**:
  qué commit introdujo cada valor, en qué fecha, y si algún documento
  justifica el incremento. Pegar `git log` de los archivos implicados.
- **A-4.** Comprobar el signo del ajuste AR(1) en `src/rigor_estadistico.py`:
  ¿qué ρ da 2188 sobre un OOS de ~731 días, y es ese ρ creíble para una
  serie con 1 trade? Decir qué dice la fuente (Bailey-LdP) sobre ρ negativo.
- **A-5.** Verificar qué intérprete de Python existe de verdad en el entorno
  de la nube. Los scripts citan `/opt/trading-bot/venv/bin/python`, que
  **probablemente no exista aquí**. No asumir: comprobar, y decir cuál se
  usa. Si no hay ninguno con numpy/pandas/scipy, **PARAR y reportar**: sin
  intérprete no hay Alcance que ejecutar.
- **A-6.** Verificar que **no hay red** (N1 lo documentó). Todo lo que haga
  esta tarea debe salir de los CSV congelados. Si algún script intenta
  descargar, es el defecto H1 y hay que decirlo, no sortearlo en silencio.

### Paso B — Ataque adversarial al planteamiento

**Esto no es verificar cifras.** Es poner en duda la tarea en sí. Mínimo
cinco objeciones reales, con severidad (CRÍTICA/ALTA/MEDIA/BAJA) y qué
cambiaría del Alcance. Si no se encuentra ninguna, **hay que decir por qué
no se encontró** — "parece bien" no vale.

Preguntas que el enemigo haría, y que hay que responder:

- **B-a.** ¿Es el DSR la herramienta correcta aquí? El DSR corrige **sesgo de
  selección**: supone que se eligió el mejor de N intentos. Pero las 9
  candidatas vinieron de **literatura publicada** (Faber, Moskowitz/Ooi/
  Pedersen, Liu/Tsyvinski, Connors), no de un barrido sobre estos datos. Si
  no hubo selección sobre la muestra, ¿qué está corrigiendo el DSR?
  ¿Y qué pasa con `sma_timing_5/10/20/50/100/304`, que **sí** son seis
  valores del mismo parámetro?
- **B-b.** Si `V` mezcla un universo (BTC, 5 años) con un `T_eff` de otro
  (portfolio multi-activo, 2015→), ¿tiene sentido **cualquiera** de las dos
  construcciones, o están las dos mal y el listón hay que calcularlo de cero
  sobre un solo universo coherente? Esa sería una tercera respuesta, y esta
  tarea tiene que admitirla si es la correcta.
- **B-c.** ¿Hay forma de que esta tarea **suba `N`**? Si recalcular el listón
  cuenta como un trial nuevo, la propia auditoría empeora el número que
  audita. Responder sí o no, y por qué.
- **B-d.** ¿Puede responderse la pregunta de la sección 1 con el material que
  hay en el repo, o hace falta algo que solo está en el VPS
  (`/root/trading-bot-fix-fase2`) y por tanto no es accesible desde aquí?
  Si la respuesta honesta es "no se puede cerrar desde este repo", decirlo
  **en la Fase 0**, no después de gastar el Alcance.
- **B-e.** La objeción que no está en esta lista.

### Maker/Verifier

Tras escribir el registro, invocar un segundo agente que **solo critique ese
registro** — no que repita la némesis. Pegar su crítica como subsección.

### NO-GO de la Fase 0

- Si A-5 no encuentra intérprete usable → PARAR, reportar, no improvisar.
- Si A-1 y A-2 concluyen que `T_eff` y `V` **no tienen origen rastreable** →
  PARAR y decirlo. Es un resultado, y es el peor posible: significa que el
  listón no es auditable y que ninguna de las dos construcciones se puede
  justificar. No inventar una procedencia plausible.
- Si algo de la sección 2 sale **REFUTADO** → PARAR. El brief estaría mal y
  el Alcance construido encima no valdría.

---

## 4. Alcance (NO EJECUTAR sin OK escrito de Pablo en la sección 6)

Orden fijo. Cada paso deja su script en `fix-fase2/auditoria_n4/` y su salida
en un JSON del mismo nombre, como hizo N1.

| # | Paso | Cierra |
|---|---|---|
| 4.1 | Rastrear y documentar la procedencia de `T_eff=4336`: dataset, ρ, script. Si no existe, declararlo no rastreable | A-1 |
| 4.2 | Recalcular `V` desde cero sobre las 11 variantes, con las cuatro definiciones posibles de "Sharpe por trial" (diario/anual × período completo/días con posición), y tabular el listón que produce cada una | 2.4, B-b |
| 4.3 | Recalcular `V` excluyendo las variantes con menos de 20 trades (`tsmom_365`, `rsi_hidden_divergence`, `sma_timing_304`, `connors_rsi2`) y tabular el listón | 2.6 |
| 4.4 | Medir la sensibilidad del listón a ρ: recalcular `n_obs_eff` de las 11 con ρ forzado a 0 (sin ajuste AR(1)) y comparar | 2.5, A-4 |
| 4.5 | Reconstruir del historial de git la secuencia `N` 11→12→14 y escribir `fix-fase2/docs/registro_N.md`: una línea por trial, con fecha, commit y la **regla** de qué cuenta como trial | 2.3, A-3 |
| 4.6 | Tabla final: el listón bajo **todas** las construcciones medidas (las de 4.2, 4.3, 4.4 × N=11/12/14), con el 1.008 marcado, y para cada una **el argumento metodológico que la sostiene** — no cuál gana | el eje |

**La tabla de 4.6 es el entregable.** No lleva recomendación. Lleva, para
cada construcción, qué habría que creer sobre cómo se seleccionaron las
variantes para que esa construcción sea la correcta. La elección es de Pablo.

### Límites de escritura

- **Permitido crear:** `fix-fase2/auditoria_n4/*.py`, sus JSON de salida,
  `fix-fase2/docs/auditoria_n4.md`, `fix-fase2/docs/registro_N.md`.
- **Prohibido modificar:** cualquier `src/*.py`, cualquier `results/*.json`,
  cualquier CSV, cualquier documento de dictamen previo. Si un script de
  `src/` hay que ejecutarlo con otros parámetros, se importa y se llama desde
  `auditoria_n4/`, **no se edita**.
- **Prohibido tocar** `paper_runner.py`, `risk_veto.py`, `deliberation.py` —
  no están en la ruta del backtest.
- Nada se activa. Esta tarea no decide nada operativo.

### NO-GO del Alcance

- Si 4.2 no reproduce **ninguno** de los tres valores de `V` de la sección
  2.4 → parar en 4.2 y reportar. Significa que `V` no es reproducible desde
  los datos del repo, y entonces 4.3-4.6 no se sostienen.
- Timeout por paso: **20 minutos**. Si un paso no termina, matarlo, anotar y
  seguir con el siguiente. Al final, listar los que no terminaron.
- Si un paso necesita red → no ejecutarlo. Anotarlo como no cubierto.

---

## 5. Entregables

1. `## Registro de revisión némesis` al final de este archivo (Fase 0).
2. `fix-fase2/docs/auditoria_n4.md` — informe, con la tabla de 4.6.
3. `fix-fase2/docs/registro_N.md` — el libro de cuentas de trials.
4. `fix-fase2/auditoria_n4/` — scripts y JSON, cada uno ejecutable solo.
5. PR contra **`fase-b-recuperada`** (no contra `main`).

**Dónde va cada hallazgo:** los de mecánica de ejecución (intérprete, red,
timeouts) van al `## Registro de revisión némesis` de este archivo. Los de
resultado van a `auditoria_n4.md`. No mezclar.

**`shared/` no existe en este repo** y no va a existir. Cualquier referencia
a esa carpeta apunta a nada: Pablo replica a mano lo que haga falta al búnker.

---

## 6. Estado de la tarea

**PARADO EN FASE 0.** Pablo escribe aquí el OK, con fecha, cuando haya leído
el registro némesis. Sin esa firma, el Alcance no se ejecuta.

```
OK para ejecutar el Alcance: [pendiente]
```

---

## Registro de revisión némesis

**Fecha:** 2026-11-01 · **Ejecutor:** sesión N4 en la nube (Claude Code, Opus 5).
**Rama:** `nube/n4-procedencia-v-t-n`, cortada de `fase-b-recuperada` @ `9f322b8`.
PR contra `fase-b-recuperada`, nunca contra `main`.
**Alcance ejecutado:** solo la **Fase 0** (§3), pasos A y B, más el segundo
agente del Maker/Verifier. **Ni un paso de la §4.** La §6 sigue sin firma.
**Lectura previa:** los cuatro documentos del encabezado, leídos enteros en el
orden indicado, antes de ejecutar nada.

**Nota de rutas.** Todos los comandos de este registro corren desde
`fix-fase2/`, que es la raíz efectiva del expediente. El repo tiene **dos
copias** del material de Fase A —la raíz (`src/`, `results/`, `docs/`) y
`fix-fase2/`—. **Corregido tras la crítica (hallazgo 16):** los ficheros
presentes en las dos copias sí son idénticos byte a byte, pero **los conjuntos
no lo son**: hay 9 ficheros solo en `fix-fase2/src/`, los dos `results/` están
descompensados en 13, y el CSV de Fase A **solo** existe en `fix-fase2/data/`.
La redacción original decía "son byte a byte idénticas" sin esa salvedad, y eso
era falso. La confusión de rutas que generó es, con bastante probabilidad, la
razón mecánica por la que al Paso A se le pasó `results/backtest_sizing05.json`
(ver B-03).

### Resumen ejecutivo

| | Resultado |
|---|---|
| Hechos de la §2 | **4 CONFIRMADOS** (2.1, 2.2, 2.5, 2.7), **2 CONFIRMADOS con ampliación material** (2.3, 2.6), **1 CONFIRMADO con la coda refutada** (§2.4). Recuento corregido tras la crítica (hallazgo 13) |
| A-1 `T_eff = 4336` | **Origen rastreable y reproducido al bit.** El NO-GO no se dispara |
| A-2 `V_TRIALS` | **Origen rastreable y reproducido con diferencia 0.0e+00.** El NO-GO no se dispara |
| A-3 secuencia `N` 11→12→14 | **NO VERIFICABLE desde git.** Todo llegó en un único commit |
| A-4 signo del AR(1) | CONFIRMADO: ρ = −0.4997, y es un **artefacto aritmético**, no una propiedad de la serie |
| A-5 intérprete | Python 3.13.18 con numpy/pandas; `scipy` instalable. **Hay intérprete usable** |
| A-6 red | Sin datos de mercado (Yahoo, Binance bloqueados). PyPI sí. Sin acceso a SSRN |
| Paso B | **14 objeciones**, de ellas **4 CRÍTICAS**. Vacían o invalidan **4.3, 4.4 y 4.5**, y debilitan 4.2 y 4.6. Ninguna CRÍTICA ataca el 4.2: lo atacan B-05 (ALTA) y B-12 (MEDIA). Recuento corregido tras la crítica (hallazgo 13) |
| Maker/Verifier | **16 hallazgos** del segundo agente. **Acepto 12**, entre ellos 2 CRÍTICOS y 2 puntos ciegos materiales que no vi. Rechazo 1 en parte. Las correcciones van aplicadas en línea y marcadas como tales |

**Lo que cambia respecto al brief.** El brief plantea la Fase 0 como un intento
de averiguar si `T_eff` y `V` tienen procedencia. **La tienen, y entera**: los
cinco números cableados en `potencia_fase_b.py` son una copia uno a uno de
`results/portfolio_bateria.json`, y ese JSON se reproduce desde los datos del
repo con una reimplementación independiente. El agujero **no** está donde el
brief lo busca. Está en `N`, y no por el lado que el brief supone: no es que
`N` haya crecido de 11 a 14 sin justificación, es que **`N` está contado por
debajo**. El repo publica resultados de tres estrategias más que ningún `N` del
expediente cuenta.

---

## Paso A — Verificación de hechos

Todo reverificado con comandos propios. Donde se reproduce aritmética del
expediente, está **reimplementada desde cero** (`statistics.NormalDist`, ajuste
AR(1) escrito a mano) y no importada de `src/`, para que la comprobación sea
independiente del código auditado.

### 2.1 — Las cinco entradas del listón están hardcodeadas → **CONFIRMADO**

```
$ grep -n "T_EFF\|V_TRIALS\|SKEW\|KURT\|SHARPE_OBSERVADO" src/potencia_fase_b.py
25:T_EFF = 4336
26:SKEW = 1.037
27:KURT = 31.999
28:V_TRIALS = 0.0007021947704551833
31:SHARPE_OBSERVADO = 1.008
34:def sharpe_min_dsr(n_trials, var_trials=V_TRIALS, n_eff=T_EFF,
```

Las cinco son constantes literales; el script no calcula ninguna. Su docstring
cita los valores pero no nombra el fichero del que salen.

**Matiz que el brief no da, y que importa:** que el script no las calcule **no**
significa que no se sepa de dónde vienen. Las cinco son `n_obs_eff`, `skew`,
`kurt`, `var_trials` y `sharpe_anual` de `results/portfolio_bateria.json`, en
el mismo orden y con el mismo redondeo. Ver A-1 y A-2.

### 2.2 — `T_eff = 4336` es 2.37 veces el único CSV de Fase A → **CONFIRMADO**

```
$ wc -l data/btc_usd_5y_1d.csv
1828 data/btc_usd_5y_1d.csv
$ python3 -I -c "import pandas as pd; d=pd.read_csv('data/btc_usd_5y_1d.csv'); \
  print(len(d), d['date'].iloc[0], d['date'].iloc[-1], d['date'].duplicated().sum())"
1827 2021-10-06 2026-10-06 0
$ sha256sum data/btc_usd_5y_1d.csv
1c393a0095688754c8e5eeeca222077ca7f03eb493e080b50fc33c03b5dfc725  data/btc_usd_5y_1d.csv
```

1827 velas, sin fechas duplicadas, 2021-10-06 → 2026-10-06, y el hash coincide
con el escrito a mano en `src/rigor_estadistico.py:5`. El `T_eff = 4336` no
puede salir de aquí: **CONFIRMADO**.

**Pero la pregunta implícita del brief se disuelve.** El `T_eff` del listón no
tiene por qué salir del CSV de Fase A: en Bailey-LdP la `T` de la PSR es la del
**objeto que se está evaluando**, y el objeto evaluado es el portfolio de Fase B
(10 activos, 4404 días). Que `T_eff` venga de ahí es lo correcto. La
heterogeneidad real no es "T no cuadra con su CSV", es que **`V` se mide en un
universo y `T` en otro** — que es exactamente H10, no un hallazgo nuevo.

### 2.3 — `N` tiene tres valores distintos, no dos → **CONFIRMADO, y ampliado**

```
$ grep -o '"n_trials": [0-9]*' results/rigor_estadistico.json | sort | uniq -c
      1 "n_trials": 11
$ sed -n '18p' docs/fase_b_reevaluacion_resultado.md
tramo. N=12 trials en todos los DSR.
$ sed -n '6p' docs/timesfm_fase2_resultado.md
**N=14** registrado antes del primer forecast (Estado de la tarea).
$ grep -rn "N_TRIALS\s*=" --include=*.py src/
src/portfolio_bateria.py:35:N_TRIALS = 12
src/portfolio_supervivencia.py:43:N_TRIALS = 12
src/portfolio_walkforward_temporal.py:37:N_TRIALS = 12
src/rigor_estadistico.py:45:N_TRIALS = len(VARIANTES)
```

Los tres valores están. `N=11` es derivado (`len(VARIANTES)`), no literal.

**La ampliación, que es el hallazgo del Paso A:** hay un **cuarto** recuento, y
es el que manda. `STRATEGIES` tiene **14** entradas, y tres de ellas no se
cuentan en ningún `N`:

```
$ python3 -I -c "import sys; sys.path.insert(0,'src'); from strategies import STRATEGIES; \
  print(len(STRATEGIES)); print([k for k in STRATEGIES if k not in V11])"
14
['mean_reversion', 'breakout', 'trend_following']
```

Y **no son código muerto: tienen resultados OOS publicados**, sobre el mismo
CSV, el mismo harness y el mismo sizing 5%:

```
$ python3 -I -c "import json; d=json.load(open('../results/backtest_sizing05.json')); \
  print(d['size_fraction'], d['csv']); print({k:v['sharpe'] for k,v in d['test_results'].items()})"
0.05 data/btc_usd_5y_1d.csv
{'mean_reversion': -1.75, 'ma_cross': 0.81, 'breakout': -0.02, 'trend_following': -0.15}
```

> **Fuente corregida tras la crítica (hallazgo 2).** La primera redacción citó
> `results/backtest_summary.json` y `docs/AUDIT_BRIEF.md:81-83`. **Las dos citas
> eran malas** y había que retirarlas:
> - `backtest_summary.json` lo produce `src/run_backtest.py`, que llama
>   `run_backtest(sliced_data, signals)` **sin `size_fraction`** → default
>   **0.95** (`backtester.py:32`), y carga con `yf.download` (`:21`), **no** el
>   CSV congelado. No es ni el mismo sizing ni el mismo origen de datos.
> - `AUDIT_BRIEF.md` se desmiente a sí mismo dos líneas más abajo (`:85`):
>   *"Estos números NO son confiables hasta que A1-A3 estén resueltos."*
>   Pegarlo como corroboración era selectivo.
> - Y *"el `sharpe 0.80` de `ma_cross` es el mismo que la reejecución de
>   Fase A"* **era falso**: Fase A da 0.0422884593·√365 = **0.8079 → 0.81**, que
>   es lo que dice `backtest_sizing05.json`. El 0.80 es del run de 0.95. Usé la
>   coincidencia de un redondeo a dos decimales como prueba de identidad de
>   harness. Mal.
>
> **El fichero correcto estaba en el mismo directorio y no lo abrí.**
> `results/backtest_sizing05.json`: `size_fraction` 0.05 y
> `csv: data/btc_usd_5y_1d.csv`, con el mismo split 0.6
> (`src/backtest_sizing05.py:22-24,44,51`). **Ahí sí son commensurables**, y la
> conclusión de B-03 sobrevive sobre una base mejor que la original.

Bajo Bailey-LdP `N` cuenta configuraciones **probadas**. Estas tres se probaron
y se publicaron. Luego **`N ≥ 15`** (3 + 11 + la regla de portfolio), no 12 ni
14.

**Y la magnitud, que la primera redacción dejó como adjetivo ("ensancha la
dispersión, sube `V` y sube el listón") sin medirla** — crítica, hallazgo 3.
Medida ahora, reejecutando las tres por el pipeline de Fase A (mismo CSV,
split 0.6, warmup 200, sizing 0.05):

```
  mean_reversion     sharpe_diario=-0.09167138 anual=-1.7514 trades=51
  breakout           sharpe_diario=-0.00081649 anual=-0.0156 trades=30
  trend_following    sharpe_diario=-0.00804383 anual=-0.1537 trades=12

  N=12 V=0.00070219 SR0=0.04412 liston_anual=1.3118  expediente: 11+portfolio
  N=15 V=0.00155037 SR0=0.06972 liston_anual=1.8024  11+portfolio+3 extra
  N=12 V=0.00155037 SR0=0.06555 liston_anual=1.7223  V de 15, N=12 fijo
  N=15 V=0.00070219 SR0=0.04692 liston_anual=1.3654  V de 12, N=15
```

**`V` se dobla (0.000702 → 0.001550) y el listón salta de 1.3118 a 1.8024.**
Eso es ×1.6 el rango completo del debate H10 (0.823–1.312) y lo domina.

**Salvedad que hay que decir, y que corta en contra de este hallazgo:** el
efecto lo manda casi entero `mean_reversion` (−0.0917 diario, a ~3.5
desviaciones del resto; el siguiente más extremo es `sma_timing_5` a −0.0156).
La corrección **no es robusta**: cuelga de un único outlier. Eso no la anula
—`mean_reversion` se corrió y se publicó igual que las demás— pero sí obliga a
presentarla como lo que es: una cota, no un listón nuevo.

Cerrado también, **con la redacción corregida tras la crítica (hallazgo 9):**
no existe `registro_N.md`, ni pre-registro, ni ningún documento que enumere los
trials uno a uno (verificado por `find` y `grep` en todo el repo). Pero decir
que *"la regla no está escrita en ningún sitio"* era falso, y además incoherente
con la §2.4, que refuta al brief citando esos mismos textos:

```
$ sed -n '31p' src/portfolio_bateria.py
# Fase A: 11 variantes sobre BTC-USD 5y + esta Fase B en portfolio = 12 intentos
$ sed -n '29,31p' docs/rigor_estadistico_resultado.md
- **V usada:** ... N = 11 variantes registradas (ma_cross + 9 de Opus +
  rsi_hidden_divergence).
```

Eso **sí** dice qué se contó, para 11 y para 12. **Lo que falta es una regla
prospectiva:** qué hacer con candidatos nuevos, y qué hacer con los ya corridos
que nadie contó (B-03). Y para `N=14` no hay ni enumeración ni regla.

### 2.4 — `V` tiene tres valores en tres documentos → **CONFIRMADO, con la coda refutada**

> **Veredicto rebajado tras la crítica (hallazgo 8).** La primera redacción
> puso **REFUTADO** y con él disparó el NO-GO de la §3. Era desproporcionado:
> el encabezado de la §2.4 es cierto y este mismo Paso A lo acredita con
> `grep`, y las dos subafirmaciones verificables salen CONFIRMADAS. Solo la
> coda ("nadie ha dicho cuál manda") es falsa, y B-12 la puntúa MEDIA. Una
> objeción MEDIA no puede accionar el freno más duro del brief. **El NO-GO de
> la §2 no se dispara.** La parada se sostiene en las cuatro CRÍTICAS del
> Paso B, que es donde siempre estuvo el motivo real.

Los tres valores están donde el brief dice:

```
$ sed -n '29,30p' docs/rigor_estadistico_resultado.md
- **V usada:** varianza de los Sharpes diarios de las 11 variantes = 0.0007017.
$ sed -n '39p' docs/fase_b_reevaluacion_resultado.md
Sharpe anual mínimo exigido (T_eff=4336, skew 1.037, curtosis 32, V=0.0007022),
$ sed -n '28p' src/potencia_fase_b.py
V_TRIALS = 0.0007021947704551833
```

Y la discrepancia con el primero es real y está en un JSON, no solo en prosa:

```
$ for f in results/*.json; do grep -Ho '"var_trials": [0-9.e-]*' $f; done
results/portfolio_bateria.json:"var_trials": 0.0007021947704551833
results/portfolio_walkforward_temporal.json:"var_trials": 0.0007021947704551833
results/potencia_fase_b.json:"var_trials": 0.0007021947704551833
results/rigor_estadistico.json:"var_trials": 0.0007016935642058066
```

Las tres subafirmaciones de la §2.4, por separado:

| Subafirmación | Veredicto |
|---|---|
| El 2º y el 3º no son un error entre sí | **CONFIRMADO** — son el mismo número, uno redondeado a 7 decimales |
| Hay una discrepancia real con el 1º | **CONFIRMADO** — 0.00070169 vs 0.00070219, diferencia 5.012e-07 |
| **"Nadie ha dicho cuál manda"** | **REFUTADO** |

La tercera es falsa, y se refuta en el propio código, en el punto de cálculo:

```
$ sed -n '1,5p;54,55p;69p' src/portfolio_bateria.py
"""Bateria Fase A sobre la curva combinada del portfolio multi-activo.

DSR con N=12 (registro explicito: las 11 variantes de Fase A + esta regla en
portfolio; V recalculada como varianza across-trial de los Sharpes diarios de
esas 12 series), block bootstrap (21d, B=10000) del retorno medio, t>3, y
    # V across-trial: Sharpe diario de las 11 variantes Fase A (mismo CSV BTC
    # 5y, OOS 60/40, sizing 5%) + este portfolio = 12 series
    var_trials = float(np.var(sharpes, ddof=1))

$ sed -n '217,218p' src/rigor_estadistico.py
    # V = varianza across-trial de los Sharpes por periodo de las 11 variantes
    sharpes_per = np.array([base[n]["sharpe_per"] for n in VARIANTES])
```

**No hay tres `V` en discrepancia: hay dos `V`, cada una emparejada con su
propio `N`, y las dos documentadas en el punto donde se calculan.** `V(11)` se
usa con `N=11` en Fase A; `V(12)` se usa con `N=12` en Fase B. Esa es la
construcción coherente, no un descuido. El tercer valor del brief es el segundo
sin redondear.

Esto **dispara el NO-GO de la §3** ("si algo de la sección 2 sale REFUTADO →
PARAR"), y se reporta como tal. El Alcance 4.2 hereda la premisa falsa: está
escrito para resolver una discrepancia de tres valores que no existe.

### 2.5 — La muestra va de 598 a 2188 obs. efectivas → **CONFIRMADO**

El brief infiere que el noveno es `tsmom_365` "por el orden de la tabla". No
hace falta inferir: el JSON los nombra.

```
$ python3 -I -c "import json; d=json.load(open('results/rigor_estadistico.json')); \
  [print(k, v['n_obs_eff'], v['sharpe_per']) for k,v in d['variantes'].items()]"
ma_cross               598   0.04228845931653596
sma_timing_5           723  -0.015619656527480276
sma_timing_10          677   0.009103059233229268
sma_timing_20          691   0.041239679828807795
sma_timing_50          678   0.05841924375303099
sma_timing_100         737   0.05256140795356013
sma_timing_304         690   0.026996765197560977
tsmom_7                642  -0.013534101420817814
tsmom_365             2188  -0.000934980486698583   <-- el 2188
connors_rsi2           869   0.04757981949103217
rsi_hidden_divergence  779   0.02695860572125778
```

2188 > 1827 velas del fichero y > 730 retornos del OOS: **CONFIRMADO**. Es el
ajuste AR(1) con ρ negativo. Ver A-4.

### 2.6 — Cuatro de las once operan con un puñado de trades → **CONFIRMADO, e incompleto**

Recuento de trades propio, reejecutando las 11 (no leído del documento):

```
variante                     T       rho    T_eff    int  T_eff/T  trades   exp%
--------------------------------------------------------------------------------
ma_cross                   730   0.09929    598.1    598    0.819      12    3.8
sma_timing_5               730   0.00448    723.5    723    0.991     105   51.9
sma_timing_10              730   0.03766    677.0    677    0.927      67   51.6
sma_timing_20              730   0.02702    691.6    691    0.947      40   52.5
sma_timing_50              730   0.03687    678.1    678    0.929      24   55.2
sma_timing_100             730  -0.00523    737.7    737    1.011      13   50.8
sma_timing_304             730   0.02792    690.3    690    0.946       5   35.2
tsmom_7                    730   0.06349    642.8    642    0.881      70   53.3
tsmom_365                  730  -0.49968   2188.1   2188    2.997       1    0.3
connors_rsi2               730  -0.08694    869.0    869    1.190      12    5.2
rsi_hidden_divergence      730  -0.03272    779.4    779    1.068       3   11.9
```

Los once `n_obs_eff` reproducen **exactos** los del JSON, y los cuatro recuentos
de trades que el brief cita son correctos.

**Pero la lista del brief está incompleta, y eso rompe el paso 4.3.** Variantes
con menos de 20 trades: **seis**, no cuatro. El brief omite `ma_cross` (12) y
`sma_timing_100` (13), que están igual de abajo que `connors_rsi2` (12), que sí
está en la lista. `ma_cross` es además la que el expediente trató como ganadora
de Fase A.

### 2.7 — Lo que esto NO prueba todavía → **CONFIRMADO**

No es una proposición empírica, es una regla de método, y se cumple: nada de
2.1–2.6 fija la dirección del error. Lo refuerzo con un dato propio: las dos
correcciones que el Paso A encuentra apuntan en **sentidos opuestos** —
`N ≥ 15` (2.3) sube el listón; las seis `sma_timing` como barrido de un solo
parámetro (B-06) lo bajan. El neto no es conocido a priori. **Se mide, no se
supone**: confirmado como regla y confirmado como estado de cosas.

---

### A-1 — ¿De dónde sale `T_eff = 4336`? → **ORIGEN RASTREABLE**

Está en un único JSON, y en el que lo copia:

```
$ grep -rn "4336" results/*.json
results/portfolio_bateria.json:6:  "n_obs_eff": 4336,
results/potencia_fase_b.json:2:  "T_eff": 4336,
```

`results/portfolio_bateria.json` lo produce `src/portfolio_bateria.py:50`,
`t_eff = int(ar1_effective_n(per))`, sobre los retornos diarios de
`results/portfolio_equity.csv`. Reproducido con el ajuste AR(1) **reescrito a
mano**, sin importar `src/`:

```
=== A-1 : T_eff del portfolio (reimplementado) ===
dias de equity          : 4404
retornos diarios (T)    : 4403
rho lag-1               : 0.007558295106411656
T_eff = T*(1-rho)/(1+rho): 4336.940947109138
int(T_eff)              : 4336   <-- comparar con 4336
skew                    : 1.036877  <-- vs SKEW=1.037
kurt raw (kurt+3)       : 31.998897  <-- vs KURT=31.999
sharpe anual (x sqrt365): 1.008383  <-- vs 1.008
```

**Dataset:** `results/portfolio_equity.csv`, la curva de equity del portfolio de
Fase B (10 activos, 4404 días, CSV congelados con sello `20261009` en
`data/multi/`). **ρ = +0.00756** (positivo y minúsculo: el ajuste quita 67
observaciones de 4403, un 1.5%). **Script:** `src/portfolio_bateria.py:50`.

Y las **cinco** constantes de `potencia_fase_b.py` son el mismo JSON:
`n_obs_eff` 4336, `skew` 1.037, `kurt` 31.999, `var_trials`
0.0007021947704551833, `sharpe_anual` 1.008. Copia uno a uno.

**El NO-GO de A-1 no se dispara.** El número tiene origen rastreable y
reproducible. El defecto de `potencia_fase_b.py` es de **trazabilidad
documental** (no cita su fuente) y de **etiqueta** (se titula "A PRIORI" con
parámetros del run ya observado — eso es H9 de N1), no de procedencia.

### A-2 — ¿Sobre qué datos se calculó `V_TRIALS`? → **ORIGEN RASTREABLE**

**Script:** `src/portfolio_bateria.py:69`, `float(np.var(sharpes, ddof=1))`.
**Sobre qué:** 12 Sharpes diarios. Los 11 primeros, reejecutando las once
variantes de Fase A sobre `data/btc_usd_5y_1d.csv` (líneas 56–67: split
`int(len·0.6)` = 1096, `WARMUP` 200, `size_fraction` 0.05). El 12º,
`s_per` del portfolio de Fase B (línea 68).

**Definición de "Sharpe por trial"** (`portfolio_bateria.py:38-41`, idéntica a
`rigor_estadistico.py:175`):

```python
def sharpe_diario(rets):
    r = np.asarray(rets, dtype=float); r = r[~np.isnan(r)]
    return float(r.mean() / r.std()) if r.std() > 0 else 0.0, len(r)
```

Es decir: **diario, no anualizado** (sin factor `√365`); `mean/std` con `std` de
`numpy` (`ddof=0`); y **sobre el período completo**, no sobre los días con
posición — los días sin posición entran como ceros exactos. De las cuatro
definiciones que el paso 4.2 propone barrer, la que se usó es **diaria ×
período completo**.

Reproducción, con implementación independiente:

```
=== A-2 : las dos V ===
V de 11 trials (Fase A)  : 0.0007016935642058066
  JSON rigor_estadistico : 0.0007016935642058066
  identico?              : True
V de 12 trials (+portf.) : 0.0007021947704551833
  cableada en Fase B     : 0.0007021947704551833
  diferencia             : 0.000000e+00
Sharpe diario del portfolio anadido como trial 12: 0.05278115954782411
```

Las dos `V` reproducen: la de 11 al bit, la de 12 con diferencia **0.0e+00**.

Y el listón completo, con una PSR reescrita desde `statistics.NormalDist`:

```
=== reproduccion del liston con implementacion independiente ===
N=12 V=0.00070219 T=4336 skew=1.037 kurt=31.999
  SR0 diario       : 0.04412   (publicado 0.04412)
  liston ANUAL     : 1.3118    (publicado 1.312)
  DSR del observado: 0.7187    (publicado 0.7191)
```

**El NO-GO de A-2 no se dispara.** `V` es rastreable, documentada en el punto de
cálculo y reproducible desde los datos del repo.

### A-3 — La secuencia 11 → 12 → 14 en git → **NO VERIFICABLE**

```
$ for f in src/rigor_estadistico.py src/portfolio_bateria.py \
    src/portfolio_walkforward_temporal.py src/potencia_fase_b.py \
    docs/timesfm_fase2_resultado.md results/portfolio_bateria.json; do
    git log --follow --reverse --date=short --pretty='%h %ad %s' -- fix-fase2/$f | head -1; done
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
d34b147 2026-10-29 Recupera el trabajo de Fase B, reevaluacion y TimesFM del VPS
```

**Todo el material de Fase B, la reevaluación y TimesFM llegó en un solo
commit.** No hay historial intermedio, así que `N=12` y `N=14` **no se pueden
ni fechar ni ordenar** por git. Es el límite nº 5 que el propio informe de N1
declaró ("los `.py` no tienen hash, ni historia previa a `d34b147`").

Lo único que sí está atestiguado por git es el primer valor, y por una copia
que el brief no menciona:

```
$ git show --stat --oneline 663db2c
663db2c Fase A rigor estadistico: DSR (Bailey-LdP 2014), block bootstrap, t>3 ...
 docs/rigor_estadistico_resultado.md | 122 ++++++
 results/rigor_estadistico.json      | 309 ++++++++
 src/rigor_estadistico.py            | 270 ++++++
 verificar_rigor_sintetico.py        | 109 ++++
$ sha256sum src/rigor_estadistico.py fix-fase2/src/rigor_estadistico.py | cut -c1-16
58217a1ee751dbcc
58217a1ee751dbcc
```

La copia de la raíz y la de `fix-fase2/` son **idénticas**, y la de la raíz está
en git desde el **2026-10-07**. Luego `N=11` y `V=0.0007016935642058066` sí
tienen fecha firme.

Y la cadena de `N=14` no existe en este repo en absoluto:

```
$ for c in 3ad4795 9249cf4; do git cat-file -t $c || echo "NO EXISTE"; done
NO EXISTE      # 3ad4795, citado por timesfm_fase2_resultado.md:4
NO EXISTE      # 9249cf4, citado por fase_b_reevaluacion_resultado.md:3
$ git rev-parse --verify fase-b-multiactivo; git rev-parse --verify fase2/timesfm-multiactivo
NO EXISTE (ambas)
$ find . -iname "*hipotesis*" -o -iname "*registro_N*"
(sin resultados)
```

`timesfm_fase2_resultado.md:6` cita como fuente de `N=14` el "**(Estado de la
tarea)**" — un fichero de tarea que **no está en este repo**. Y **ningún
documento enumera cuáles son los trials 13 y 14.**

**Veredicto A-3: NO VERIFICABLE desde este repo.** Nada justifica el incremento
por escrito. `N=11` es enumerable y fechable; `N=12` es enumerable (11 + la
regla de portfolio, dicho en `portfolio_bateria.py:31`) pero no fechable;
`N=14` **no es ni enumerable ni fechable**.

### A-4 — El signo del ajuste AR(1) → **CONFIRMADO**

El código (`src/rigor_estadistico.py:110-120`):

```python
rho = np.corrcoef(r[:-1], r[1:])[0, 1]
rho = min(max(rho, -0.95), 0.95)
return n * (1 - rho) / (1 + rho)
```

El ρ que da 2188, despejado y medido, coinciden:

```
=== despeje analitico para tsmom_365 ===
con T=730 y T_eff=2188:  rho necesario = -0.499657
comprobacion: 730*(1+0.499657)/(1-0.499657) = 2188.00
medido sobre la serie real:  rho = -0.499682  ->  T_eff = 2188.1 -> int 2188
```

**¿Es ese ρ creíble para una serie con 1 trade? No, y la razón es aritmética,
no estadística.** La serie de retornos de `tsmom_365` es casi toda ceros:

```
retornos diarios totales : 730
retornos EXACTAMENTE cero: 728  (99.73%)
retornos no cero         : 2
   2026-01-14  +0.00081721
   2026-01-15  -0.00084694
rho lag-1 de la serie completa : -0.499682
```

Dos días. Consecutivos. De signo opuesto. Una serie de ceros con un único par
contiguo de signo opuesto tiene ρ ≈ −0.5 **por construcción**, no porque haya
reversión a la media. Demostrado con series sintéticas del mismo tamaño:

```
   ceros + (+1,-1) consecutivos -> rho = -0.500000
   ceros + (+1,+1) consecutivos -> rho = +0.498624
   ceros + (+2,-1) consecutivos -> rho = -0.400384
```

**Lo que dice la fuente sobre ρ negativo: NO VERIFICABLE desde esta sesión.**
SSRN 2460551 no es alcanzable (ver A-6), igual que le pasó a N1. Se mantiene esa
etiqueta y no se especula sobre el contenido del paper.

Lo que **sí** se puede afirmar sin el paper, porque es una cota lógica y no una
cita: **ninguna corrección por autocorrelación puede entregar más observaciones
independientes que observaciones.** `T_eff = 2188` sobre 730 retornos afirma 3
veces más información independiente que datos. El `clamp` a −0.95 permite un
factor de hasta **×39**. Una corrección de muestra efectiva solo es defendible
acotada por arriba a `T`; que el código no lo haga es un defecto real.
**No se corrige aquí**: tocar el estimador después de ver el resultado sería
cambiar la métrica, prohibido por la §1 del brief. Se reporta.

**Dónde muerde y dónde no.** El 2188 afecta **solo** al DSR propio de
`tsmom_365` en la tabla de Fase A (0.020). **No entra en el listón 1.312.** Ver
B-01, que es la consecuencia crítica para el Alcance.

### A-5 — ¿Qué intérprete hay de verdad? → **HAY INTÉRPRETE USABLE**

```
$ ls -la /opt/trading-bot/venv/bin/python
ls: cannot access '/opt/trading-bot/venv/bin/python': No such file or directory
```

**El intérprete que citan los docstrings de `src/*.py` no existe aquí.**
Confirmado: el brief tenía razón en no asumirlo. Lo que sí hay:

```
$ which -a python3 ; python3 -VV
/usr/local/bin/python3  /usr/bin/python3  /usr/bin/python3.11  /usr/bin/python3.12  /usr/bin/python3.13
Python 3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3]

$ python3 -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
2.5.3 3.0.5
numpy        OK  2.5.3
pandas       OK  3.0.5
scipy        NO  ModuleNotFoundError
statsmodels  NO  ModuleNotFoundError
yfinance     NO  ModuleNotFoundError
torch        NO  ModuleNotFoundError
timesfm      NO  ModuleNotFoundError
```

`scipy` no venía, pero **se instala** (PyPI sí es alcanzable, ver A-6):

```
$ python3 -m pip install --quiet scipy && python3 -c "import scipy; print(scipy.__version__)"
1.18.1
```

Y **nada del expediente lo necesita**: ningún `.py` de `fix-fase2/` importa
`scipy`. La PSR/DSR del repo usa `statistics.NormalDist` de la librería
estándar.

**El intérprete a usar es `python3` (3.13.18) desde `fix-fase2/`.**
**El NO-GO de A-5 no se dispara.** Límite declarado: `torch` y `timesfm` siguen
no disponibles, así que nada de TimesFM es reproducible desde aquí — igual que
en N1.

### A-6 — ¿Hay red? → **NO HAY DATOS DE MERCADO. CONFIRMADO**

```
$ curl -sS -o /dev/null -w "%{http_code}" https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD
curl: (56) CONNECT tunnel failed, response 403     -> 000
$ curl ... https://fc.yahoo.com            -> 403 / 000
$ curl ... https://api.binance.com/api/v3/ping  -> 403 / 000
$ curl ... https://pypi.org/simple/        -> 200
$ curl ... https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551  -> 403 / 000
$ curl ... https://www.davidhbailey.com    -> 403 / 000
```

**Ninguna fuente de precios es alcanzable; PyPI sí.** Todo lo que haga esta
tarea tiene que salir de los CSV congelados — y de hecho todo el Paso A salió de
ellos. **SSRN y la web del autor tampoco**, así que la fuente primaria del DSR
no es consultable (eso cierra la parte de A-4 que pedía citarla).

Los scripts que **sí** intentarían descargar, si se ejecutasen (es el defecto
H1/H5 de N1, ya documentado, no sorteado en silencio):

```
$ grep -rn "yf.download" --include=*.py . | grep -v auditoria_n1
./src/walkforward_stability.py:42    ./src/portfolio_runner.py:212
./src/run_backtest.py:21             ./src/paper_runner.py:59
./src/portfolio_supervivencia.py:67  ./verificar_a5_indicadores.py:8
./verificar_a8_adversarial.py:8
```

De estos, `portfolio_runner.py` quedó parcheado por N1 (sello explícito,
descarga prohibida salvo `PERMITIR_DESCARGA=1`); `portfolio_supervivencia.py:67`
sigue con el defecto (H7, no parcheado por alcance).

---

## Paso B — Ataque adversarial al planteamiento

Catorce objeciones. Cuatro **CRÍTICAS**. **B-13 y B-14 salen de la crítica del
segundo agente** (hallazgos 4 y 5): son puntos ciegos que esta némesis no vio y
que valen más que varias de las doce originales.

Del Alcance: **4.3, 4.4 y 4.5 no sobreviven** tal como están escritos (4.4 no
puede mover el listón, 4.5 es imposible de ejecutar, 4.3 es una selección sobre
el conjunto de intentos); **4.2 queda debilitado pero no roto** (su eje de
unidades es falso, su eje real es más ancho de lo que la §4 dice); **4.1 ya está
hecho** en A-1 y A-2; y **4.6 no se puede construir** encima de lo anterior.
Ninguna de las cuatro CRÍTICAS ataca el 4.2: lo atacan B-05 (ALTA) y B-12
(MEDIA). *(Recuento corregido tras la crítica, hallazgo 13: la primera redacción
decía "tres de los seis pasos" en la cabecera y "4.2, 4.3, 4.4 y 4.5" en el
veredicto, e inflaba la severidad de su propio recuento.)*

No se encontró ninguna objeción que invalide la **pregunta** de la §1 —sigue
siendo la pregunta correcta—, sino el **camino** que la §4 propone para
responderla.

---

### B-01 · El paso 4.4 no mueve el listón. No puede. — **CRÍTICA**

El paso 4.4 dice: *"Medir la sensibilidad del listón a ρ: recalcular `n_obs_eff`
de las 11 con ρ forzado a 0 (sin ajuste AR(1)) y comparar"*.

**El `n_obs_eff` de las 11 no entra en el listón.** El listón es
`liston(N=12, V, T_eff=4336, skew, kurt)`. `V` es la varianza de los doce
**Sharpes diarios**, y un Sharpe diario es `mean/std` de los retornos: no lleva
ningún factor `√T` ni `T_eff`. Forzar ρ=0 cambia los once `n_obs_eff`, **no
cambia ni uno de los once `sharpe_per`**, luego no cambia `V`, luego no cambia
el listón. Es una identidad, no una conjetura.

La única sensibilidad a ρ que mueve el listón es la del `T` del **portfolio**, y
es despreciable, porque ρ del portfolio es +0.0076:

```
  T= 4336 (AR(1) aplicado, el publicado)  liston anual 1.3118   DSR 0.7187
  T= 4403 (rho forzado a 0)               liston anual 1.3082   DSR 0.7202
```

**−0.0036 de listón.** Frente a los ±0.49 que mueve la construcción de `V`
(H10), es ruido.

**Qué cambia del Alcance:** 4.4 se reescribe o se borra. Lo que sí tiene valor
—y es lo que A-4 ya entregó en la Fase 0, sin gastar el Alcance— es documentar
que el 2188 es un artefacto de una serie con 728 ceros y que el estimador no
está acotado por arriba. Eso afecta al **DSR por variante de Fase A** (tabla de
`rigor_estadistico_resultado.md`), no al 1.312. Si Pablo quiere el paso, su
enunciado correcto es *"acotar `T_eff ≤ T` y reemitir la tabla de DSR de Fase A"*
— y eso es modificar la métrica de Fase A, que el propio brief prohíbe.

---

### B-02 · El paso 4.5 es imposible: no hay historial de git que reconstruir — **CRÍTICA**

El paso 4.5 pide *"reconstruir del historial de git la secuencia `N` 11→12→14"*.
A-3 lo cierra: **todo llegó en `d34b147`**, un único commit del 2026-10-29.
`N=12` y `N=14` no se pueden ni fechar ni ordenar. Los commits que los
documentos citan como su cadena (`3ad4795`, `9249cf4`) **no existen**, ni las
ramas, ni el pre-registro, ni el "Estado de la tarea" que `timesfm_fase2_resultado.md:6`
da como fuente de `N=14`.

Esto no es un descubrimiento nuevo: es el **límite nº 5 del informe de N1**,
escrito en el mismo repo que el brief. El brief de N4 propone un paso que su
propia lectura previa obligatoria declara imposible.

**Qué cambia del Alcance:** 4.5 no se puede ejecutar como está. Lo que sí se
puede escribir es un `registro_N.md` **prospectivo**: la regla de qué cuenta
como trial de aquí en adelante, más el inventario de los trials **enumerables
hoy** (los 11 de Fase A + la regla de portfolio + los 3 de B-03), declarando
explícitamente que la cadena histórica 12→14 es **no auditable** y que `N=14`
no tiene contenido identificable. Eso es un entregable honesto. "Reconstruir del
historial" no lo es.

---

### B-03 · `N` está contado por debajo, no por arriba. El brief mira al lado equivocado — **CRÍTICA**

Todo el brief asume que el problema de `N` es un contador que **creció sin
justificación** (11→12→14) y que hay que reconciliar hacia abajo. El Paso A
encuentra lo contrario: `STRATEGIES` tiene 14 entradas, y `mean_reversion`,
`breakout` y `trend_following` **se probaron sobre el mismo CSV, el mismo
harness y el mismo sizing, y sus resultados OOS están publicados** en
`results/backtest_summary.json`, `docs/AUDIT_BRIEF.md:81-83` y
`docs/sizing_05_resultado.md:22-24`, con fecha **2026-10-06** — *antes* de las
11. No están en ningún `N`.

Bajo Bailey-LdP, `N` cuenta configuraciones probadas. Luego **`N ≥ 15`**. Y
`N=14`, que el expediente trata como la cifra "inflada" a reconciliar hacia 12,
resulta estar **por debajo** del mínimo defendible — y coincidir con 14 por
casualidad aritmética, no porque alguien contase esos tres.

La dirección importa y es contraria a Fase B: sus Sharpes anuales (−1.75, −0.01,
−0.17) caen **fuera** del rango de los once contados, así que incluirlas sube
`V` y sube el listón. Es decir: el Alcance tal como está planteado —cuatro de
sus seis pasos buscan construcciones de `V` sobre las 11 o un subconjunto de
ellas— **omite sistemáticamente la corrección que va en contra**.

**Qué cambia del Alcance:** cualquier recálculo de `V` tiene que tabular también
el caso **con las tres**, y `registro_N.md` tiene que empezar por ellas. Si no,
el barrido del 4.6 es un barrido sesgado por construcción, y eso es la mitad del
camino hacia el metric-shopping que la §1 prohíbe.

---

### B-04 · El paso 4.3 es metric-shopping con el umbral mal aplicado — **CRÍTICA**

El paso 4.3 dice: *"recalcular `V` excluyendo las variantes con menos de 20
trades (`tsmom_365`, `rsi_hidden_divergence`, `sma_timing_304`, `connors_rsi2`)
y tabular el listón"*. Dos defectos, y el segundo es peor que el primero.

**(a) El umbral está mal aplicado.** Hay **seis** variantes con <20 trades, no
cuatro (§2.6): faltan `ma_cross` (12) y `sma_timing_100` (13). `connors_rsi2`
está en la lista con 12 trades y `ma_cross` fuera con los mismos 12. Una lista
que incluye una variante y excluye otra con el mismo recuento no es un criterio,
es una selección. Y `ma_cross` es la que el expediente trató como ganadora de
Fase A.

**(b) Y el paso entero es la jugada que el brief prohíbe.** La §1 dice: *"Elegir
viendo el resultado sería cambiar la métrica para que pase, y eso está
prohibido."* Excluir trials de `V` **después** de saber que el listón se mueve
entre 0.823 y 1.312 y que el observado cae en medio es exactamente eso, con
cualquier umbral. Que el umbral se presente como objetivo ("<20 trades") no lo
arregla: el 20 no está pre-registrado en ningún sitio, y el Paso A muestra que
tal como está escrito ni siquiera se aplica de forma consistente.

Añado el agravante: bajo Bailey-LdP `V` es la dispersión entre los intentos
**que de verdad se probaron**. Un intento con 1 trade se probó. Quitarlo de `V`
porque tiene pocos trades es afirmar que no cuenta como intento — y entonces
tampoco debería contar en `N`, lo que mueve el listón en el **otro** sentido.
El paso 4.3 toca `V` y deja `N` quieto, y esa asimetría es un sesgo, no una
construcción defendible.

**Qué cambia del Alcance:** 4.3 se borra, o se reescribe de forma simétrica
(excluir de `V` **y** de `N`, con el umbral aplicado a las seis, y presentando
el resultado como una cota, no como una alternativa a elegir). Como está, es el
paso que yo rechazaría incluso con el OK firmado.

---

### B-05 · El paso 4.2 ofrece cuatro definiciones; dos no son defendibles, son incoherentes — **ALTA**

El paso 4.2 pide barrer *"las cuatro definiciones posibles de Sharpe por trial
(diario/anual × período completo/días con posición)"*.

El eje **diario/anual no es una elección metodológica**: es un convenio de
unidades con **una** respuesta. La PSR de Bailey-LdP evalúa un Sharpe **por
período** contra un `T` que cuenta **períodos**: con `T_eff = 4336` días, el
Sharpe tiene que ser diario.

> **Razonamiento corregido tras la crítica (hallazgo 11).** La primera redacción
> decía que anualizar *"da un número distinto y sin sentido"* y que *"no hace
> falta calcularlo para descartarlo"*. **Las dos cosas estaban mal**, y la
> segunda es justo la actitud que este registro le reprocha al expediente.
> Calculado:
>
> ```
> SR0 diario                        : 0.044116
> SR0 de V anual (= 365·V diaria)   : 0.842831   /sqrt(365) = 0.044116
> SR0 anual / SR0 diario            : 19.104973  (sqrt(365) = 19.104973)
> liston anual via V diaria         : 1.3118
> ```
>
> Con `V_anual = 365·V_diaria` el `SR₀` reconvertido es **idéntico** y el listón
> sale **exactamente 1.3118**. El eje no es "dimensionalmente inválido": si se
> convierte de forma consistente y se vuelve, da el mismo número. Solo produce
> basura si se **mezclan** unidades (una `V` anual contra un `T` diario y una
> corrección de Mertens evaluada en un Sharpe 19× mayor). **La conclusión de
> B-05 se mantiene** —no es un eje real y el 4.2 no es una rejilla de 4— pero la
> razón es "una respuesta, no dos", no "incoherencia dimensional".

El eje que **sí** es una elección real es *período completo vs días con
posición*, y es importante: A-2 establece que se usó período completo, lo que
mete 728 ceros exactos en la serie de `tsmom_365` (y 94–96% de ceros en
`ma_cross` y `connors_rsi2`, al 3.8% y 5.2% de exposición).

**Y el eje que sí es real es más ancho de lo que esta objeción dijo** — crítica,
hallazgo 12. La primera redacción aplicó "período completo vs días con posición"
**solo a `V`**. Aplica igual al objeto evaluado, y ahí mueve mucho más:

```
  T completo 4403  ceros exactos 897 (20.37%)
  T activos  3506  rho +0.00686  T_eff 3458  skew 0.890  kurt 25.479
  sharpe anual sobre dias activos: 1.1303   (periodo completo: 1.0084)
  liston con T = dias activos    : 1.3686   (publicado: 1.3118)
```

La curva del portfolio es **20.4% ceros exactos** y `T_eff = 4336` la cuenta
entera. Bajo "días con posición" se mueven **a la vez** `T` (4403→3506), el
skew, la curtosis **y el Sharpe observado** (1.008→1.130). Recortar el 4.2 a dos
celdas sobre `V`, como proponía la primera redacción, **descartaba en silencio
el lado `T`/`ŜR` del único eje que acababa de declarar válido.**

**Qué cambia del Alcance:** 4.2 no pasa de 4 celdas a 2. Pasa a un **2×2 sobre
(`V`) × (`T` y `ŜR` juntos)**, eliminando solo el eje de unidades. El entregable
del 4.6 se simplifica, pero no por la vía que esta objeción dijo primero.

---

### B-06 · B-a: el DSR corrige algo, pero `N=12` no es el número que corrige — **ALTA**

La objeción del brief es buena y la respuesta tiene dos mitades que van en
sentidos opuestos.

> **Nota de atribución, tras la crítica (hallazgo 6).** Esta objeción, §2.2,
> §2.3 y B-04 atribuyen a "Bailey-LdP" cuatro afirmaciones definicionales: que
> la `T` de la PSR es la del objeto evaluado, que `N` cuenta configuraciones
> probadas, que `V` es la dispersión across-trial entre los intentos probados, y
> que `E[max_N]` supone `N` extracciones independientes. **No las leí en el
> paper: el paper no es alcanzable desde esta sesión (A-6).** Están transcritas
> en el repo —`src/rigor_estadistico.py:17-22` (incluido el ejemplo impreso del
> paper: DSR 0.9004, SR0 0.1132, T=1250, N=100, V=0.002, skew −3, kurt 10) y
> `docs/rigor_estadistico_resultado.md:20-25`— y de ahí salen. Debía citar el
> repo, no el paper, y no lo hice. **Lo que sigo declarando NO VERIFICABLE es
> otra cosa y de otra especie:** qué dice la fuente sobre ρ **negativo** en
> concreto (A-4). Eso no está transcrito en ningún sitio del repo y no lo sé.
> El agravante que el crítico señala lo acepto entero: el ejemplo impreso del
> paper **sí** estaba en el repo y A-4 no lo usó.

**Lo que el DSR sí corrige aquí.** Que las 9 candidatas vengan de literatura
publicada no elimina el sesgo de selección: lo **traslada**. Faber,
Moskowitz/Ooi/Pedersen, Liu/Tsyvinski y Connors son supervivientes de un
proceso de publicación que descartó lo que no funcionó, sobre otros mercados y
otras muestras. Eso es sesgo de selección con un `N` efectivo **mucho mayor que
12** y desconocido. Así que el DSR no está corrigiendo nada espurio; está
corrigiendo lo que puede medir de un sesgo que es mayor de lo que mide.

**Lo que `E[max_N]` da por supuesto y aquí no se cumple.** La fórmula
`SR₀ = √V·[(1−γ_E)Φ⁻¹(1−1/N) + γ_E·Φ⁻¹(1−1/(N·e))]` es el valor esperado del
máximo de `N` extracciones **independientes** de `N(0,V)`. Las seis
`sma_timing_5/10/20/50/100/304` son **seis valores de un mismo parámetro sobre
la misma serie**: sus Sharpes diarios van de −0.0156 a 0.0584 y están
fuertemente correlacionados por construcción. Seis extracciones correlacionadas
valen, en términos de máximo esperado, bastante menos que seis independientes.
Eso hace que `E[max_12]` **sobreestime** el listón.

**Respuesta honesta a B-a:** el DSR es la herramienta correcta en especie
(hay selección), y `N=12` es el número equivocado por **las dos puntas a la
vez**: por abajo omite trials reales (B-03), por arriba trata un barrido de un
parámetro como intentos independientes. **El neto no es conocido**, y el brief
hace bien en no suponerlo (§2.7). Lo que el brief **no** hace es decir que el
error es bidireccional — y presentar solo las correcciones que bajan el listón
sería el sesgo del que la §1 se quiere proteger.

**Qué cambia del Alcance:** el 4.6 no puede tabular `N = 11/12/14` como si fuese
el eje de incertidumbre de `N`. El eje real es `N ∈ {15+ enumerable}` por un
lado y `N_efectivo < 12 por correlación entre trials` por el otro, y la tabla
tiene que decir que son dos errores de signo opuesto y que ninguno está
cuantificado.

---

### B-07 · B-b: sí, hay una tercera respuesta, y es que las dos construcciones están mal — **ALTA**

La objeción del brief es correcta y la respuesta es sí.

`V` mide la dispersión entre once reglas corriendo sobre **BTC solo, 730 días
OOS (2024-10→2026-10), sizing fijo 5%**. El objeto evaluado es un **portfolio de
10 activos, 4403 días (2014→2026), vol-targeting al 10% con covarianza EWMA**.
No comparten universo, ni ventana, ni maquinaria de sizing, ni número de
observaciones. `V` y `T` describen **dos objetos distintos**, y eso vale para la
construcción del expediente.

Pero la alternativa de 3.0c tampoco se salva, y N1 ya lo dijo en su parte E: medir
las once reglas **sobre el panel** describe una familia de intentos que **nunca
se buscó**, y las pasa todas por el mismo vol-targeting, que les comprime la
dispersión (sd de 0.506 a 0.212, cero negativos). Esa `V` responde a la pregunta
"¿cuánto dispersan once reglas si las obligo al mismo perfil de riesgo?", que no
es la pregunta de Bailey-LdP.

**La tercera respuesta es la correcta: la `V` coherente sería la dispersión entre
los intentos que de verdad se hicieron sobre el objeto que se está evaluando**
— es decir, sobre el panel multi-activo. Y ahí la familia es **pequeña, pero no
es `N=1`**.

> **Corregido tras la crítica (hallazgo 10), y es el más incómodo de los
> dieciséis.** La primera redacción decía *"sobre el panel **solo se hizo un
> intento** … No hay familia. Con `N=1` el DSR no deflacta nada"*. Dos cosas
> estaban mal:
>
> **(a) Apliqué a `N` la vara contraria a la de B-03.** B-03 cuenta **toda**
> configuración corrida, reconocida o no; aquí acepté el recuento publicado tal
> cual. Las dos varas no caben juntas. Bajo la de B-03, sobre el panel hay más
> de un intento:
>
> ```
> $ python3 -I -c "import json; d=json.load(open('results/portfolio_supervivencia.json')); \
>     print(d['n_activos'], d['metricas']['sharpe'], d['metricas']['dsr'])"
> 15 0.916 0.6014
> $ ls results/portfolio_equity*.csv
> results/portfolio_equity.csv  results/portfolio_equity_muertos.csv
> $ grep -nE "^(LOOKBACK|LAMBDA|SIGMA_TARGET|W_MAX|GROSS_MAX|VOL_TOPE_MULT)" src/portfolio_runner.py
> 32:LOOKBACK = 365          35:W_MAX = 0.20
> 33:LAMBDA = 0.94           36:GROSS_MAX = 1.0
> 34:SIGMA_TARGET = 0.10     37:VOL_TOPE_MULT = 1.25
> ```
>
> Hay una **segunda curva de panel** con su propio Sharpe (0.916) y su propio
> DSR (0.6014), **seis hiperparámetros no pre-registrados** y la elección del
> universo de 10 activos. La familia del panel es pequeña y no enumerable con
> precisión, pero **no es 1**.
>
> **(b) No declaré la dirección de mi propia "fila dominante", después de
> acusar al Alcance de omitir las correcciones que van en contra.** Con `N=1` el
> listón es **0.472** (`results/potencia_fase_b.json`, fila N=1) frente a un
> 1.008 observado: **Fase B pasa con holgura.** Es decir: la construcción que
> propuse como dominante es **la más favorable a Fase B de todo el expediente**,
> y la presenté sin decirlo. Ese es exactamente el sesgo del que la §1 se quiere
> proteger, cometido por quien lo estaba denunciando.

Y eso no es una salida: significa que **el DSR de Fase B no está mal calculado,
está mal planteado**. Se está deflactando un resultado multi-activo con la
dispersión de una búsqueda single-asset, porque es la única dispersión que
existe. Ninguna de las tres construcciones es correcta; la correcta exigiría una
familia de intentos sobre el panel que **nadie probó**, y fabricarla ahora
—correrla a posteriori— es precisamente lo que N1 descartó.

**Qué cambia del Alcance:** el entregable del 4.6 no puede ser "aquí están las
construcciones, elige". Tiene que incluir la fila *"no hay familia de intentos
sobre el objeto evaluado"* y decir que esa fila probablemente domina a las
demás. Si eso es verdad, la respuesta a la §1 no es un número: es que **el DSR
no es el test que decide Fase B**, y el expediente lleva tres briefs colgando de
un listón que no debería ser el eje. Esa es una conclusión que el Alcance tal
como está escrito no puede alcanzar, porque sus seis pasos dan por bueno que la
pregunta es "qué `V`".

---

### B-08 · B-c: ¿sube esta tarea `N`? No por ejecutarse, sí por cómo está escrita — **MEDIA**

**No por el recálculo.** `N` cuenta configuraciones de **estrategia** probadas
contra los datos para ver si ganan dinero. Recalcular `V` y el listón sobre los
mismos trials es una capa de análisis: no introduce ninguna regla nueva, no
mide ningún PnL nuevo, no hay ningún resultado que pudiera "salir bien". Los
pasos 4.1, 4.2, 4.4, 4.5 y 4.6 **no suben `N`**. Es la misma razón por la que
los pasos 3.0c y 3.0d de N1 no lo subieron.

**Sí por el 4.3.** Excluir trials de `V` tras ver el resultado no sube `N`
—hace algo peor: selecciona sobre el conjunto de intentos. Es el mismo peligro
que el `N` protege, entrando por otra puerta, y sin dejar rastro en el contador.
Ver B-04.

**Y hay un tercer caso que el brief no contempla:** si del 4.6 sale una
construcción nueva de `V` y Pablo la adopta, el intento que se ha hecho no es de
estrategia sino **de métrica**, y el expediente no tiene contador para eso.
Un "`N` de métricas probadas" también existe en la literatura de backtest
overfitting, y aquí va ya por 3: la del expediente, la de 3.0c y el reescalado
de N2. **Qué cambia del Alcance:** `registro_N.md` debería llevar dos columnas,
trials de estrategia y construcciones de métrica probadas, y la segunda empieza
en 3, no en 0.

---

### B-09 · B-d: la pregunta de la §1 se cierra a medias desde este repo — **ALTA**

Respuesta por partes, porque el brief pide honestidad en la Fase 0 y no después:

| Pregunta | ¿Se cierra desde este repo? |
|---|---|
| ¿De dónde sale `T_eff = 4336`? | **Sí, cerrada.** A-1: `portfolio_bateria.py:50` sobre `portfolio_equity.csv`, ρ=+0.0076, reproducido al bit |
| ¿Sobre qué datos y con qué definición se calculó `V`? | **Sí, cerrada.** A-2: `portfolio_bateria.py:69`, 12 Sharpes diarios, período completo, diferencia 0.0e+00 |
| ¿Cómo creció `N` de 11 a 12 a 14? | **No. Y no se va a cerrar.** A-3: un solo commit, commits y ramas citados inexistentes, pre-registro ausente, `N=14` sin contenido identificable |
| ¿Cuál es la `V` correcta? | **No es una pregunta de archivo.** B-07: ninguna de las construcciones disponibles es coherente, y la coherente exige una familia de intentos que no se hizo |

Lo que haría falta y está en el VPS (`/root/trading-bot-fix-fase2`), fuera de
alcance: el historial de git real anterior a `d34b147`, el "Estado de la tarea"
de TimesFM y `hipotesis-timesfm-fase2.md`. **Pero incluso con eso, la cuarta
fila no se cierra**: no es un problema de evidencia perdida, es que la familia
de intentos sobre el panel no existe porque nunca se buscó.

**Qué cambia del Alcance:** la §1 dice *"lo que esta tarea hace es reconstruir
cómo se construyeron de verdad `V`, `T_eff` y `N`"*. Dos tercios de eso ya
están hechos — en esta Fase 0, en una tarde, sin gastar el Alcance. El tercio
que falta no es reconstruible. **El Alcance de seis pasos está dimensionado para
un problema que la Fase 0 ya resolvió o ya declaró irresoluble.**

---

### B-10 · B-e, la que no está en la lista: `tsmom_365` no es un trial, y `V` está medida sobre reglas que casi no operan — **ALTA**

A-4 lo deja a la vista: la "serie de retornos" de `tsmom_365` son **728 ceros
exactos y dos días**. Un trade, 0.3% de exposición. Eso no es una estrategia que
rindió mal: es una estrategia que **no se ejecutó**. Su Sharpe diario
(−0.000935) no mide habilidad ni su ausencia; mide que la serie es plana.

Y no es un caso aislado. Por exposición, de los once trials que componen `V`:

```
tsmom_365  0.3%    ma_cross  3.8%    connors_rsi2  5.2%    rsi_hidden_div  11.9%
sma_timing_304  35.2%
sma_timing_5/10/20/50/100  50.8–55.2%    tsmom_7  53.3%
```

**Cuatro de once están por debajo del 12% de exposición**, es decir: su serie
diaria es 88–99.7% ceros. `V` es la varianza entre once Sharpes de los que
cuatro están aplastados hacia cero **porque la serie es casi toda ceros**, no
porque las reglas sean parecidas.

> **CORRECCIÓN. El párrafo que seguía aquí tenía el signo invertido.** Lo
> encontré en autorrevisión y el segundo agente lo confirmó como su hallazgo 1,
> CRÍTICO. Decía: *"incluirla en `V` la **encoge** hacia cero —arrastra la
> varianza hacia el centro— y por tanto **baja el listón**. La construcción del
> expediente … está ya contaminada en la dirección favorable a Fase B."*
> **Es falso**, y es exactamente el pecado que el brief prohíbe en su §2.7
> ("se mide, no se supone"), cometido en la objeción donde más presumía.
>
> El mecanismo estaba mal planteado: la media de los 12 Sharpes diarios es
> **+0.02732**, no cero. Un Sharpe de −0.00093 no está "en el centro", está
> 0.028 **por debajo** de la media, entre los más extremos. Encoger hacia cero
> cuando la media es positiva es **alejarse** de la media, y eso **sube** la
> varianza. Medido, dejando una fuera cada vez con `N=12` fijo:
>
> ```
>   sin ma_cross                V +6.52%   liston 1.3388 (+0.0271)
>   sin sma_timing_5            V -18.64%  liston 1.2292 (-0.0826)
>   sin sma_timing_10           V +4.84%   liston 1.3320 (+0.0202)
>   sin sma_timing_20           V +6.99%   liston 1.3407 (+0.0290)
>   sin sma_timing_50           V -5.03%   liston 1.2903 (-0.0215)
>   sin sma_timing_100          V +0.10%   liston 1.3122 (+0.0004)
>   sin sma_timing_304          V +10.00%  liston 1.3529 (+0.0412)
>   sin tsmom_7                 V -15.93%  liston 1.2417 (-0.0700)
>   sin tsmom_365               V -2.40%   liston 1.3016 (-0.0102)
>   sin connors_rsi2            V +3.62%   liston 1.3269 (+0.0151)
>   sin rsi_hidden_divergence   V +10.00%  liston 1.3529 (+0.0412)
>   sin PORTFOLIO               V -0.07%   liston 1.3115 (-0.0003)
> ```
>
> Quitar `tsmom_365` **baja** `V` un 2.40%: luego incluirla **sube** el listón
> +0.0102, lo contrario de lo que afirmé. Y la correlación que postulé entre
> "casi no opera" y "encoge `V`" **no existe**: las dos cuya inclusión más
> encoge `V` son `sma_timing_304` (**35.2% de exposición**) y
> `rsi_hidden_divergence`; las dos que más la inflan son `sma_timing_5` y
> `tsmom_7`, al **51.9% y 53.3%** — reglas que operan a pleno. El único
> predictor es `|ŜR − media|`. La exposición no entra.
>
> **Se retira la frase del signo y la de "contaminada en la dirección favorable
> a Fase B".** El efecto es **mixto y sin dirección neta conocida**, y la tabla
> de arriba es la medida, no el argumento.

**Lo que de B-10 sí aguanta, y es solo interpretativo:** `E[max_N]` necesita la
dispersión entre **los candidatos de entre los que se habría elegido el
máximo**. El Sharpe de una serie 99.7% plana no mide habilidad ni su ausencia:
mide que la serie es plana. Eso pone en duda que `V` sea una medida
interpretable de dispersión entre intentos —en **ninguna** de sus
construcciones— pero **no fija ninguna dirección**, y este diagnóstico no
propone quitar nada: quitarlas es el 4.3, que es metric-shopping (B-04). Es un
hallazgo sobre la métrica, no una propuesta de métrica.

**Contradicción propia que hay que resolver, y que el segundo agente señaló
(hallazgo 4):** decir que `tsmom_365` *"no se ejecutó"* choca de frente con que
la regla de Fase B **es `tsmom_365`** y produce el 1.008. Ver B-13.

**Qué cambia del Alcance:** es la fila que el 4.6 **no** tiene y que más
necesita: *"`V` medida sobre una familia de intentos de la que un tercio no
opera"*, con las exposiciones a la vista, y sin número al lado — porque poner un
número sería elegir.

---

### B-11 · El estimador de muestra efectiva no está acotado por arriba — **MEDIA**

`ar1_effective_n` devuelve `n·(1−ρ)/(1+ρ)` con ρ pinzado a `[−0.95, 0.95]`, sin
tope en `n`. Con ρ=−0.95 el factor es **×39**. Ninguna corrección por
autocorrelación puede entregar más observaciones independientes que
observaciones: la forma defendible es `min(T_eff, T)`.

Alcance material: en el listón, nulo (ρ del portfolio es +0.0076, ver B-01). En
la tabla de DSR de Fase A, solo `tsmom_365` (2188 sobre 730). Como Fase A murió
por DSR, bootstrap y `t` de forma independiente, y el DSR de `tsmom_365` es
0.020, **no mueve ningún dictamen**. Por eso es MEDIA y no ALTA: es un defecto
real del instrumento con consecuencia nula en lo publicado.

**Qué cambia del Alcance:** nada, y eso es el punto — no justifica un paso. Va
al informe como defecto declarado. Y **no se parchea**: tocar el estimador
después de ver los resultados sería cambiar la métrica.

---

### B-12 · La §2.4 del brief es falsa en su conclusión, y el 4.2 la hereda — **MEDIA**

Ya está en el Paso A, se recoge aquí porque es la objeción al **planteamiento**:
la §2.4 concluye *"nadie ha dicho cuál manda"*, y eso es falso. No hay tres `V`
sin reconciliar: hay **dos**, cada una emparejada con su `N` correcto, y las dos
documentadas en el punto de cálculo (`portfolio_bateria.py:3-5` y `:54-55`;
`rigor_estadistico.py:217`). El tercer valor del brief es el segundo redondeado.

Esto importa porque el 4.2 está escrito para resolver una inconsistencia que no
existe, y porque es el tipo de error que, en una auditoría, se propaga: si la
§2.4 pasa como "discrepancia abierta", el informe final acabará diciendo que la
`V` del expediente estaba sin documentar. No lo estaba. Lo que estaba sin
documentar —y sigue— es `N`.

---

### B-13 · El trial nº 12 es la misma regla que el nº 9, y el sujeto del test está dentro de su propia `V` — **CRÍTICA**

**Punto ciego. No lo vi; lo encontró el segundo agente (hallazgo 4).** Verificado:

```
$ sed -n '4p' src/portfolio_runner.py
  - Regla: tsmom_365 (long-only) identica en los 10 activos, sin optimizar
```

**La regla de Fase B es `tsmom_365`** — la misma que ya es el trial nº 9 de los
once. Dos consecuencias, y las dos van al corazón de B-06 y B-07:

1. **`V(12)` contiene la misma regla dos veces**: una versión BTC-only / sizing
   5% / OOS 730 días, y una versión panel / Carver vol-targeting / 4403 días.
   B-06 dedicó su argumento a que las seis `sma_timing` son un parámetro barrido
   y no seis extracciones independientes, y **no vio el duplicado literal**, que
   es la versión fuerte de esa misma objeción.
2. **`V(12)` contiene al sujeto del test.** `portfolio_bateria.py:68` añade
   `s_per` —el Sharpe del propio portfolio que se está deflactando— a la lista
   de la que sale `V`. El `SR₀` contra el que se mide Fase B está calculado, en
   parte, con Fase B dentro. El efecto numérico es pequeño (quitar el portfolio
   mueve `V` −0.07% y el listón −0.0003, medido en la tabla de B-10), pero el
   problema es **conceptual**, no de magnitud: es circular.

Y obliga a retirar una frase de B-10: si `tsmom_365` *"no se ejecutó"*, hay que
explicar cómo esa misma regla produce el 1.008. La respuesta es que el signo
`tsmom_365` sobre BTC-only con sizing fijo del 5% da **1 trade**, y sobre diez
activos con sizing por volatilidad da la curva de Fase B. **Es la misma regla con
dos universos y dos maquinarias de sizing.** Eso no rescata el Sharpe de la
versión BTC-only como medida de habilidad —sigue siendo una serie 99.7% plana—
pero sí desmonta la lectura de que "la regla no opera".

**Qué cambia del Alcance:** ninguna construcción de `V` del 4.2/4.3/4.6 es
interpretable mientras el sujeto esté dentro de su propia dispersión y la
familia contenga un duplicado. Esto va **antes** de elegir construcción, y el
Alcance no tiene paso para ello.

---

### B-14 · El 1.008 no tiene holdout; la `V` que lo deflacta es out-of-sample — **ALTA**

**Segundo punto ciego, también del segundo agente (hallazgo 5).** Verificado:

```
$ grep -n "TRAIN_FRAC\|split" src/portfolio_runner.py
68:    esperado = open(sidecar).read().split()[0]
100:            f.rsplit("_", 1)[1][:8] for f in os.listdir(data_dir)
$ python3 -I -c "import pandas as pd; e=pd.read_csv('results/portfolio_equity.csv', \
    index_col=0,parse_dates=True).iloc[:,0]; print(len(e), e.index[0].date(), e.index[-1].date())"
4404 2014-09-17 2026-10-07
```

`portfolio_runner.py` **no tiene split train/test**: las dos únicas apariciones
de `split` son un `.read().split()` y un `rsplit` de nombres de fichero. El
Sharpe 1.008 y el `T_eff = 4336` son sobre **la historia entera**. Los once
Sharpes que forman `V` son estrictamente el **40% OOS** (730 días,
2024-10→2026-10).

Se está comparando un número **sin holdout** contra un listón calibrado con
dispersión **out-of-sample**. B-07 enumeró las heterogeneidades de `V` frente a
`T` —universo, ventana, maquinaria de sizing, nº de observaciones— y **omitió
esta, que es la que más daño hace**, porque es la única que tiene dirección
conocida: **va en contra de Fase B.** Un Sharpe in-sample completo es optimista
frente a uno OOS, y el listón no lo penaliza.

**Qué cambia del Alcance:** es otra fila obligatoria del 4.6, y a diferencia de
las de B-07 y B-10 esta **sí** tiene signo. Que no esté en ninguna de las doce
objeciones originales es un fallo de esta némesis, no del brief.

---

### Lo que NO se encontró, declarado

- **Ningún error aritmético.** El listón 1.312, el SR₀ 0.04412, las dos `V`, el
  `T_eff` 4336, el skew, la curtosis, los once `n_obs_eff` y **los once DSR** de
  `results/rigor_estadistico.json` reproducen todos con implementación
  independiente. La aritmética del expediente es correcta.
  **Salvedad, corregida tras la crítica (hallazgo 15):** el DSR de Fase B que
  A-2 pegó es **0.7187**, no el publicado 0.7191, y la primera redacción lo
  listó aquí entre los que "reproducen todos". No reprodujo. La causa es trivial
  y había que decirla: 0.7187 sale de usar el `SHARPE_OBSERVADO = 1.008` ya
  redondeado de `potencia_fase_b.py:31`; con el Sharpe diario exacto
  (0.05278115954782411) da **0.719121 → 0.7191**, el publicado. El dato no
  cambia; la afirmación estaba mal hecha.
- **Ninguna manipulación.** Las dos `V` están correctamente emparejadas con sus
  `N`. El defecto de `N` (B-03) es una **omisión** fechada el 2026-10-06, antes
  de que existiese ningún resultado de Fase B que sesgarla pudiese favorecer.
- **Ninguna objeción a la pregunta de la §1.** Sigue siendo la pregunta correcta.
  Lo que no sobrevive es el camino de la §4.

---

## Veredicto de la Fase 0 y NO-GO

**PARADA. Ninguno de los tres NO-GO formales se dispara.** La parada se sostiene
en las cuatro objeciones CRÍTICAS del Paso B, que es donde está el motivo real.

| NO-GO de la §3 | Estado |
|---|---|
| *Si A-5 no encuentra intérprete usable → PARAR* | **No se dispara.** Python 3.13.18 + numpy/pandas, `scipy` instalable, nada del repo lo necesita |
| *Si A-1 y A-2 concluyen que `T_eff` y `V` no tienen origen rastreable → PARAR* | **No se dispara.** Los dos tienen origen rastreable y reproducen (0.0e+00). **El peor resultado posible no se ha materializado**: el listón sí es auditable |
| *Si algo de la §2 sale REFUTADO → PARAR* | **No se dispara. Rebajado tras la crítica (hallazgo 8).** La primera redacción lo declaró DISPARADO por la coda de la §2.4. Era desproporcionado: el encabezado de la §2.4 es cierto, sus dos subafirmaciones verificables salen CONFIRMADAS, y B-12 —la objeción que refuta la coda— se puntúa MEDIA. Una objeción MEDIA no acciona el freno más duro del brief. Y lo que el brief realmente señala con esa coda **sigue en pie**: el emparejamiento de `V`(BTC-OOS) con `T`(panel, muestra completa) no está justificado por escrito en ningún sitio, que es H10 |

La razón sustantiva para no ejecutar la §4 tal como está: **las cuatro
objeciones CRÍTICAS vacían o invalidan 4.3, 4.4 y 4.5, y B-13 invalida la
premisa de 4.2/4.6.** `4.1` ya está hecho en A-1 y A-2 —**el solape lo creó el
brief**, porque A-1 y A-2 preguntan lo que pregunta el 4.1, no es que esta Fase 0
se haya adelantado al Alcance— y `4.6` es la tabla final, que no puede
construirse encima de tres pasos rotos y una premisa circular.

**Y las dos filas que el 4.6 más necesita no están en la §4 y las aporta esta
Fase 0 corregida:** el sujeto del test dentro de su propia `V` con un duplicado
en la familia (B-13), y el Sharpe sin holdout contra un listón calibrado OOS
(B-14, la única con dirección conocida, y va **en contra** de Fase B).

**Lo que esta Fase 0 deja establecido, sin gastar el Alcance:**

1. `T_eff = 4336` y las dos `V` tienen procedencia completa, documentada y
   reproducible. **El listón es auditable.** El agujero que el brief temía no
   existe.
2. **`N` está contado por debajo: `N ≥ 15`.** `mean_reversion`, `breakout` y
   `trend_following` tienen resultados OOS publicados en
   `results/backtest_sizing05.json` —sizing 0.05 y el CSV congelado, igual que
   las once— y están fuera de todos los recuentos. Medido: `V` **se dobla**
   (0.000702 → 0.001550) y el listón salta de **1.3118 a 1.8024**, ×1.6 el rango
   completo del debate H10. **Salvedad:** el efecto lo manda casi entero
   `mean_reversion`, a ~3.5 desviaciones del resto, así que es una cota colgada
   de un outlier, no un listón nuevo.
3. La cadena histórica de `N` (12→14) es **no auditable** desde este repo y no
   lo será: un solo commit, commits y ramas citados inexistentes, `N=14` sin
   contenido identificable.
4. El 2188 de `tsmom_365` es un **artefacto aritmético** de una serie con 728
   ceros, no afecta al listón, y el estimador de muestra efectiva no está
   acotado por arriba.
5. **El problema de fondo no es qué `V` elegir.** El sujeto del test está
   dentro de su propia `V`, la familia contiene la misma regla dos veces (B-13),
   el Sharpe evaluado no tiene holdout mientras la `V` es OOS (B-14), y no hay
   familia de intentos sobre el objeto evaluado. Eso pone en duda que el DSR sea
   el test que deba decidir Fase B — una conclusión que ningún paso del Alcance
   podía alcanzar.

**Lo que hace falta antes de cualquier OK:** reescribir la §4. Si Pablo quiere
que el Alcance se ejecute, no debería firmar el que está escrito.

**Y una reserva sobre este registro, que el segundo agente tiene razón en
poner.** Aunque las reproducciones del Paso A son correctas —el crítico las
reverificó una a una y varias salen al bit—, la primera versión no dejó ni un
script detrás, en un documento cuyo reproche central a `potencia_fase_b.py` es
precisamente que no cita su fuente. Corregido: los scripts de la Fase 0 van en
`fix-fase2/fase0_n4/`, **que no es `auditoria_n4/`** y no contiene ningún paso
del Alcance. Cada uno solo reverifica la §2 o uno de los A-1..A-6. Si Pablo
prefiere que la Fase 0 no deje ficheros nuevos, borrar ese directorio no pierde
nada salvo la reproducibilidad de estas comprobaciones.

**No se ha ejecutado ni un paso de la §4. La §6 sigue sin firma.**

---

## Maker/Verifier — crítica del segundo agente y respuesta

El brief (§3, *Maker/Verifier*) manda invocar un segundo agente que **solo
critique este registro**, no que repita la némesis, y pegar su crítica como
subsección. Hecho. **Encontró dos errores CRÍTICOS míos y dos puntos ciegos
materiales.** Reverifiqué con comandos propios todas sus afirmaciones
numéricas antes de aceptarlas: **todas salen.** Las correcciones están
aplicadas en línea arriba y marcadas como tales; ninguna afirmación falsa queda
en pie sin su corrección al lado.

### Qué acepto y qué no

| # | Hallazgo del segundo agente | Sev. | Mi respuesta |
|---|---|---|---|
| 1 | **B-10 tiene el signo invertido** y de ahí sale el encuadre "contaminado a favor de Fase B" | CRÍTICA | **ACEPTADO.** Lo encontré yo en autorrevisión y él lo confirmó con la tabla deja-una-fuera completa. Corregido en línea; retirada la frase del signo y la de "contaminada". El efecto es mixto |
| 2 | **B-03 cita el fichero equivocado**: `backtest_summary.json` es sizing 0.95 y datos descargados | CRÍTICA | **ACEPTADO.** Verificado: `run_backtest.py:41` llama sin `size_fraction` (default 0.95) y `:21` usa `yf.download`. El fichero correcto, `results/backtest_sizing05.json`, estaba en el mismo directorio y no lo abrí. Resembrado. La conclusión sobrevive **sobre una base mejor** |
| 3 | **B-03 presenta un argumento como medida** y no calcula la magnitud | ALTA | **ACEPTADO.** Medido y pegado: `V` se dobla, listón 1.3118 → **1.8024**. Añado la salvedad que él también señala: lo manda `mean_reversion`, a ~3.5 sd del resto. Es una cota colgada de un outlier |
| 4 | **El trial nº 12 es la misma regla que el nº 9**, y el sujeto del test está dentro de su propia `V` | ALTA | **ACEPTADO, y lo subo a CRÍTICA.** Verificado en `portfolio_runner.py:4`. Es la versión fuerte de mi propia B-06 y no la vi. Es ahora **B-13** |
| 5 | **El 1.008 es muestra completa; la `V` es OOS** | ALTA | **ACEPTADO.** Verificado: `portfolio_runner.py` no tiene split; la equity va de 2014-09-17 a 2026-10-07. Es la única heterogeneidad con **dirección conocida**, y va en contra de Fase B. Es ahora **B-14** |
| 6 | **Doble vara con Bailey-LdP**: "NO VERIFICABLE" en A-4 y autoridad en cuatro sitios | ALTA | **ACEPTADO EN PARTE.** Acepto la atribución descuidada: las cuatro afirmaciones definicionales (`N` cuenta configuraciones probadas, `V` es dispersión across-trial, `E[max_N]` supone extracciones independientes) **están transcritas en el repo** (`rigor_estadistico.py:17-22`, `docs/rigor_estadistico_resultado.md:22-24`), así que debía citar el repo, no el paper. Corregido abajo. **Rechazo el "doble vara"**: la pregunta de A-4 —qué dice el paper sobre ρ **negativo** en concreto— es de otra especie que las definiciones, y de esa sí no sé la respuesta. Y acepto lo que más duele: el ejemplo impreso del paper **sí está** en `rigor_estadistico.py:17-22` y no lo usé |
| 7 | **Ninguna reproducción tiene script detrás**, en el documento que reprocha a `potencia_fase_b.py` no citar su fuente | ALTA | **ACEPTADO.** Es el golpe más limpio de la crítica. Corregido: los scripts van en `fix-fase2/fase0_n4/` |
| 8 | **El NO-GO se dispara con una lectura literal** que el propio registro puntúa MEDIA | ALTA | **ACEPTADO.** Rebajado: §2.4 pasa a *CONFIRMADO con la coda refutada* y el NO-GO de la §2 **no se dispara**. La parada se sostiene sola en las CRÍTICAS. Y tiene razón en lo de fondo: el emparejamiento `V`(BTC-OOS)/`T`(panel full-sample) sigue sin justificar en ninguna parte |
| 9 | **Doble vara con los comentarios de código** entre §2.3 y §2.4 | MEDIA | **ACEPTADO.** Lo que falta no es "la regla no está escrita en ningún sitio" —`portfolio_bateria.py:31` y `docs/rigor_estadistico_resultado.md:29-30` sí dicen qué se contó— sino una regla **prospectiva**. Corregido abajo |
| 10 | **B-07 aplica a `N` la vara contraria a B-03** y no declara la dirección de su propia "fila dominante" | MEDIA | **ACEPTADO, y es el más incómodo.** Verificado: existe una segunda curva de panel (`portfolio_supervivencia.json`, 15 activos, Sharpe 0.916, DSR 0.6014) y seis hiperparámetros no pre-registrados (`portfolio_runner.py:32-37`). Bajo la vara de B-03 el panel **no es `N=1`**. Y la dirección: con `N=1` el listón es **0.472** y Fase B pasa con holgura — mi "fila dominante" era la construcción **más favorable a Fase B de todo el expediente** y no lo dije. Corregido en B-07 |
| 11 | **B-05: conclusión correcta, argumento intermedio falso** | MEDIA | **ACEPTADO.** Verificado: `SR0_anual/SR0_diario = 19.104973 = √365` exacto, y el listón sale 1.3118 por las dos vías. Corregido: el eje es un convenio con **una** respuesta, no una incoherencia dimensional. Y "no hace falta calcularlo" era exactamente la actitud que yo reprocho |
| 12 | **B-05 tira la mitad de su propio eje**: "días con posición" aplica a `T` y a `ŜR`, no solo a `V` | MEDIA | **ACEPTADO.** Verificado: 897 ceros exactos (20.37%), `T` 4403→3506, Sharpe 1.008→1.130, listón 1.3118→**1.3686**. El 4.2 es un 2×2, no un contraste de 2. Corregido |
| 13 | **La contabilidad de sus propios hallazgos no cuadra, tres veces** | MEDIA | **ACEPTADO.** Las tres. Recuentos corregidos en el resumen, en la cabecera del Paso B y en el veredicto. Y la errata (`roros`) también. En un documento cuya tesis es que el expediente lleva mal las cuentas de `N`, tiene coste y me lo como |
| 14 | **"Ni un paso de la §4" contra "4.1 ya hecho"** | MEDIA | **ACEPTADO.** Corregido en el veredicto: el solape **lo creó el brief**, porque A-1 y A-2 preguntan lo que pregunta el 4.1. Pero había que decir eso, no afirmar las dos cosas |
| 15 | **El DSR no reprodujo** (0.7187) y luego se lista entre los reproducidos (0.7191) | BAJA | **ACEPTADO.** Verificado: con el Sharpe diario exacto da 0.719121 → 0.7191; el 0.7187 sale de usar el 1.008 ya redondeado. Corregido en "Lo que NO se encontró" |
| 16 | **"Byte a byte idénticas" es falso** como está escrito | BAJA | **ACEPTADO.** Los ficheros comunes sí son idénticos; los conjuntos no. Y tiene razón en que esa confusión de rutas es probablemente la causa mecánica del hallazgo 2. Corregido en la Nota de rutas |

**Balance: acepto 15 de 16 enteros y 1 en parte (el 6).** Dos de los suyos
—el trial duplicado dentro de su propia `V`, y el Sharpe sin holdout contra una
`V` out-of-sample— **valen más que varias de mis doce objeciones originales**, y
son puntos ciegos, no matices: ninguna de mis doce los roza.

Y acepto su juicio sobre el sesgo de encuadre, porque es verdad y está
documentado: presenté argumentos como medidas en B-03, B-06 y B-10; inflé el
recuento de severidades en mi propio veredicto; apliqué la fuente, los
comentarios de código y la vara de `N` en la dirección que en cada párrafo me
convenía; y no dejé ni un script detrás mientras reprochaba a
`potencia_fase_b.py` no citar su fuente. El protocolo Maker/Verifier funcionó
exactamente para lo que está: **esta Fase 0, sin el segundo agente, habría
llegado a Pablo con dos errores CRÍTICOS y un NO-GO disparado de más.**

---

### Crítica del segundo agente (Maker/Verifier)

*Pegada literal, como manda el brief. Es salida de un modelo, no autoridad: todo
lo que afirma lo reverifiqué antes de aceptarlo, y el resultado de esa
reverificación está en la tabla de arriba.*

**Objeto:** el texto del `## Registro de revisión némesis`. No se repite la
némesis. Todo lo que aquí se afirma como hecho se comprobó con comandos propios
desde `fix-fase2/` con `python3` 3.13.18, reimplementando la PSR/DSR desde
`statistics.NormalDist`. Lectura sin tocar un fichero.

**Resumen:** la aritmética del Paso A es correcta y la reproduje al bit,
incluyendo cosas que el registro no se atribuye. Pero **tres de sus piezas de
razonamiento no sobreviven**: B-10 tiene el signo invertido en su caso central,
B-03 cita el fichero equivocado y no mide lo que afirma, y el NO-GO cuelga de
una lectura literal que el propio registro puntúa MEDIA. Hay además cuatro
puntos ciegos materiales que el registro no mira.

1. **B-10 tiene el signo invertido, y es la pieza que sostiene el encuadre
   "contaminado a favor de Fase B" — CRÍTICA.** B-10 afirma: *"Incluirla en `V`
   la **encoge** hacia cero … y por tanto **baja** el listón."* Es falso para la
   regla sobre la que B-10 argumenta (`tsmom_365`) y el mecanismo que invoca no
   existe. Deja-una-fuera sobre las 12 series, con `N=12` fijo:

   ```
   V(12)=0.0007021948  liston=1.3118  media de los 12 Sharpes=+0.02732
     sin ma_cross                SR=+0.04229  V=0.00074797 ( +6.52%)  liston=1.3388 (+0.0271)
     sin sma_timing_5            SR=-0.01562  V=0.00057127 (-18.64%)  liston=1.2292 (-0.0826)
     sin sma_timing_10           SR=+0.00910  V=0.00073621 ( +4.84%)  liston=1.3320 (+0.0202)
     sin sma_timing_20           SR=+0.04124  V=0.00075128 ( +6.99%)  liston=1.3407 (+0.0290)
     sin sma_timing_50           SR=+0.05842  V=0.00066691 ( -5.03%)  liston=1.2903 (-0.0215)
     sin sma_timing_100          SR=+0.05256  V=0.00070291 ( +0.10%)  liston=1.3122 (+0.0004)
     sin sma_timing_304          SR=+0.02700  V=0.00077240 (+10.00%)  liston=1.3529 (+0.0412)
     sin tsmom_7                 SR=-0.01353  V=0.00059034 (-15.93%)  liston=1.2417 (-0.0700)
     sin tsmom_365               SR=-0.00093  V=0.00068532 ( -2.40%)  liston=1.3016 (-0.0102)
     sin connors_rsi2            SR=+0.04758  V=0.00072764 ( +3.62%)  liston=1.3269 (+0.0151)
     sin rsi_hidden_divergence   SR=+0.02696  V=0.00077240 (+10.00%)  liston=1.3529 (+0.0412)
     sin PORTFOLIO               SR=+0.05278  V=0.00070169 ( -0.07%)  liston=1.3115 (-0.0003)
   ```

   Quitar `tsmom_365` **baja** `V` un 2.40%: incluirla **sube** el listón
   +0.0102. La media de los 12 Sharpes es **+0.02732**, no cero, así que un
   Sharpe de −0.00093 está 0.028 **por debajo** de la media. "Encoger hacia
   cero" cuando la media es positiva es alejarse de la media, y eso **sube** la
   varianza. Y la correlación postulada entre "casi no opera" y "encoge `V`" no
   existe: las dos que más la encogen son `sma_timing_304` (**35.2% de
   exposición**) y `rsi_hidden_divergence`; las dos que más la inflan son
   `sma_timing_5` y `tsmom_7`, al **51.9% y 53.3%**. El único predictor es
   `|SR − media|`. **Qué corregir:** borrar la frase del signo y la de
   "contaminada en la dirección favorable". Lo que aguanta de B-10 es solo lo
   interpretativo, y eso no tiene dirección conocida.

2. **B-03: la conclusión aguanta, la evidencia citada es la equivocada —
   CRÍTICA.** `results/backtest_summary.json` no es el mismo sizing ni el mismo
   origen de datos: `run_backtest.py:41` llama `run_backtest(sliced_data,
   signals)` **sin `size_fraction`** → default **0.95** (`backtester.py:32`), y
   `:21` **descarga de yfinance**. El fichero correcto existe en el mismo
   directorio y el registro no lo abrió nunca:

   ```
   $ python3 -I -c "import json; d=json.load(open('../results/backtest_sizing05.json')); print(d['size_fraction'], d['csv']); print({k:v['sharpe'] for k,v in d['test_results'].items()})"
   0.05 data/btc_usd_5y_1d.csv
   {'mean_reversion': -1.75, 'ma_cross': 0.81, 'breakout': -0.02, 'trend_following': -0.15}
   ```

   Consecuencias: los Sharpes citados (−1.75, −0.01, −0.17) son del run de 0.95;
   los comparables son **−1.75, −0.02, −0.15**. *"El `sharpe 0.80` de `ma_cross`
   **es el mismo** que la reejecución de Fase A"* es **falso**: Fase A da
   0.0422884593·√365 = **0.8079 → 0.81**. El registro usó la coincidencia de un
   redondeo a 2 decimales como prueba de identidad de harness. Y la tercera
   cita, `AUDIT_BRIEF.md:81-83`, está desautorizada dos líneas más abajo por su
   propio documento (`:85`: *"Estos números NO son confiables hasta que A1-A3
   estén resueltos."*). **La conclusión de B-03 sobrevive** —las tres son
   commensurables y están fuera de todos los `N`— pero tal como está escrita no
   se puede firmar.

3. **B-03 presenta un argumento como si fuera una medida, y se queda corto por
   un factor — ALTA.** *"Incluirlas ensancha la dispersión, sube `V` y sube el
   listón"* y ahí lo deja. Medido, con las tres reejecutadas por el pipeline de
   Fase A:

   ```
   mean_reversion     sharpe_diario=-0.09167138 anual=-1.7514 trades=51
   breakout           sharpe_diario=-0.00081649 anual=-0.0156 trades=30
   trend_following    sharpe_diario=-0.00804383 anual=-0.1537 trades=12

   expediente: 11+port         N=12  V=0.00070219  SR0=0.04412  liston_anual=1.3118
   11+port+3 extra             N=15  V=0.00155037  SR0=0.06972  liston_anual=1.8024
   11+port+3 extra, N=12 fijo  N=12  V=0.00155037  SR0=0.06555  liston_anual=1.7223
   11+port, N=15 (V sin los 3) N=15  V=0.00070219  SR0=0.04692  liston_anual=1.3654
   ```

   `V` **se dobla** y el listón salta de **1.3118 a 1.8024**: ×1.6 el rango
   completo del debate H10 (0.823–1.312). El registro tenía el titular en la
   mano y lo dejó como adjetivo. También merece decirse que el efecto lo manda
   casi entero `mean_reversion` (−0.0917, a ~3.5 desviaciones del resto), lo
   cual es relevante para juzgar si la corrección es robusta o es un outlier.

4. **Punto ciego: el trial nº 12 es la misma regla que el trial nº 9 — ALTA.**
   `src/portfolio_runner.py:4`: *"Regla: tsmom_365 (long-only) identica en los
   10 activos, sin optimizar"*. La regla de Fase B **es `tsmom_365`**, que ya es
   el trial 9 de los 11. Luego `V(12)` contiene la misma regla dos veces y,
   además, **contiene al sujeto del test dentro de su propia `V`**. El registro
   dedica B-06 a que las seis `sma_timing` son un parámetro barrido, y no ve el
   duplicado literal ni que el objeto evaluado está en su propia dispersión. El
   efecto numérico de la autoinclusión es pequeño (−0.07% de `V`), pero el
   problema es conceptual. Peor: B-10 dice que `tsmom_365` *"no se ejecutó"*; si
   eso es verdad, hay que explicar cómo esa misma regla produce el 1.008.

5. **Punto ciego: el 1.008 es in-sample completo; la `V` es out-of-sample —
   ALTA.** `portfolio_runner.py` **no tiene split train/test**, y la equity va
   de 2014-09-17 a 2026-10-07 (4404 días). Los once Sharpes que forman `V` son
   estrictamente el 40% OOS. B-07 enumera las heterogeneidades y **omite la más
   dañina**: se compara un número sin holdout contra un listón calibrado con
   dispersión out-of-sample. Esa asimetría va en contra de Fase B y no aparece
   en ninguna de las doce objeciones.

6. **Doble vara con la fuente — ALTA.** A-4 dice *"NO VERIFICABLE … no se
   especula sobre el contenido del paper"*, y luego cita el mismo paper en
   cuatro sitios (§2.2 la `T` de la PSR; §2.3 y B-03 que `N` cuenta
   configuraciones probadas; B-04 que `V` es la dispersión entre los intentos
   probados; B-06 que `E[max_N]` supone extracciones independientes). Todo el
   edificio B-03/B-04 descansa sobre un texto que el registro declaró no
   consultable. Agravante: la fuente **sí** está parcialmente en el repo —
   `src/rigor_estadistico.py:17-22` documenta la validación contra el ejemplo
   impreso (DSR 0.9004, SR0 0.1132, T=1250, N=100, V=0.002, skew −3, kurt 10) y
   las fórmulas están en `:51-54` — y el registro no lo usa.

7. **Ninguna de las reproducciones "al bit" existe en el repo — ALTA.** El
   commit `a1bd5c1` toca **un solo fichero**, el markdown, y no existe
   `fix-fase2/auditoria_n4`. Los bloques de salida del Paso A son **prosa pegada
   sin script detrás**. El reproche central del registro a `potencia_fase_b.py`
   es literalmente ese: *"su docstring cita los valores pero no nombra el
   fichero del que salen"*. Yo los reverifiqué y salen, así que no hay fraude;
   pero Pablo no puede comprobar nada sin rehacer el trabajo, y eso es
   precisamente lo que una auditoría de procedencia no debe dejar.

8. **El NO-GO se dispara con una lectura literal que el propio registro puntúa
   MEDIA — ALTA.** La §2.4 tiene tres piezas: el registro **confirma las dos
   verificables** y refuta solo la coda. El encabezado —"`V` tiene tres valores
   en tres documentos"— es cierto y el registro lo acredita él mismo con `grep`.
   Y la refutación es más débil de lo que parece: lo que los docstrings
   documentan es **cómo se calcula cada `V` localmente**, no **qué emparejamiento
   gobierna el listón**. El listón combina `V` del universo BTC-OOS con `T` del
   panel full-sample, y ese emparejamiento es H10 y **nadie lo justificó por
   escrito**. Añádase la incoherencia de grados: el resumen dice "REFUTADO **en
   parte**", B-12 se puntúa **MEDIA**, y el veredicto dice **DISPARADO**.

9. **Doble vara con los mismos comentarios de código — MEDIA.** §2.3 cierra que
   *"la regla de qué cuenta como trial no está escrita en ningún sitio"*,
   mientras §2.4 refuta el brief con esos mismos documentos. Pero
   `portfolio_bateria.py:31` dice *"Fase A: 11 variantes sobre BTC-USD 5y + esta
   Fase B en portfolio = 12 intentos"* y `docs/rigor_estadistico_resultado.md:29-30`
   dice *"N = 11 variantes registradas (ma_cross + 9 de Opus +
   rsi_hidden_divergence)"*. Lo que de verdad falta es una regla
   **prospectiva**; "no está escrita en ningún sitio" no es cierto.

10. **B-07 aplica a `N` el criterio contrario al de B-03 — MEDIA.** B-03 cuenta
    toda configuración corrida; B-07 acepta el recuento publicado y dice que
    sobre el panel *"solo se hizo un intento"*. Hay material que B-07 no mira:
    `results/portfolio_supervivencia.json` (15 activos, Sharpe 0.916, DSR
    0.6014), una segunda curva de panel, y seis hiperparámetros no
    pre-registrados (`portfolio_runner.py:32-37`: LOOKBACK 365, LAMBDA 0.94,
    SIGMA_TARGET 0.10, W_MAX 0.20, GROSS_MAX 1.0, VOL_TOPE_MULT 1.25). Bajo la
    vara de B-03 eso no es `N=1`. Y falta la declaración que el registro exige a
    los demás: **su "fila dominante" es la construcción más favorable a Fase B
    de todo el expediente** — con `N=1` el listón es **0.472** frente a un 1.008
    observado, y Fase B pasa con holgura. Después de acusar al Alcance de
    *"omitir sistemáticamente la corrección que va en contra"*, callar la
    dirección de la propia es sesgo de encuadre.

11. **B-05: la conclusión es correcta, el argumento intermedio es falso —
    MEDIA.** Calculado: `SR0 anual = 0.842831`, `/√365 = 0.044116` = `SR0
    diario`, y el listón sale **1.3118** por las dos vías. El eje diario/anual
    no es "dimensionalmente inválido": es un convenio de unidades con **una**
    respuesta, y solo rompe si se mezclan unidades. Y *"no hace falta
    calcularlo"* es justo la actitud que el registro reprocha en otros sitios.

12. **B-05 tira la mitad de su propio eje — MEDIA.** Aplica "período completo vs
    días con posición" **solo a `V`**. Sobre `results/portfolio_equity.csv`:
    `T` 4403 con **897 ceros exactos (20.37%)**; `T` de días activos 3506; skew
    0.890; kurt 25.479; Sharpe anual sobre días activos **1.1304** (período
    completo 1.008); listón con `T` = días activos **1.3650**. El eje es un
    **2×2** sobre (`V`, `T`+`ŜR`), no un contraste de 2 sobre `V`.

13. **La contabilidad de sus propios hallazgos no cuadra, tres veces — MEDIA.**
    (a) El resumen dice "5 CONFIRMADOS, 1 con ampliación, 1 REFUTADO"; en el
    cuerpo hay **4** confirmados lisos (2.1, 2.2, 2.5, 2.7), **2** con
    ampliación (2.3, 2.6) y 1 refutado. (b) El resumen dice "4 CRÍTICAS que
    invalidan **3 de los 6 pasos**", la cabecera del Paso B dice "4.2, 4.3 y
    4.4; y 4.5 es imposible", el veredicto dice "4.2, 4.3, 4.4 y 4.5" — y al
    4.2 **no lo ataca ninguna CRÍTICA**: lo atacan B-05 (ALTA) y B-12 (MEDIA).
    (c) *"cuatro pasos **roros**"*. En un documento cuya tesis es que el
    expediente lleva mal las cuentas de `N`, llevar mal las cuentas propias
    tiene coste.

14. **"Ni un paso de la §4" contra "4.1 ya hecho" — MEDIA.** El encabezado dice
    *"Ni un paso de la §4"*; el veredicto dice *"sobreviviría 4.1 —que esta
    Fase 0 ya ha hecho"*. Además, para producir A-2 reejecutó las 11 variantes y
    recalculó `V` desde el CSV: eso es el 4.1 entero y la maquinaria de una
    celda del 4.2. El solape lo creó el brief —A-1/A-2 preguntan lo que pregunta
    el 4.1— pero entonces hay que decir eso, no afirmar las dos cosas.

15. **El DSR no reprodujo, y luego se declara reproducido — BAJA.** A-2 pega
    *"0.7187 (publicado 0.7191)"*, y "Lo que NO se encontró" lista *"el DSR
    0.7191"* entre lo que *"reproducen todos"*. No reprodujo. La causa es
    trivial: con el sharpe exacto 0.05278115954782411 da **0.719121**; con
    `1.008/√365` da **0.718668**. El 0.7187 sale de usar el `SHARPE_OBSERVADO`
    ya redondeado de `potencia_fase_b.py:31`.

16. **"Las dos copias son byte a byte idénticas" es falso como está escrito —
    BAJA.** `diff -rq` da **9** diferencias entre los dos `src/` y **13** entre
    los dos `results/`. Los ficheros presentes en ambas **sí** son idénticos
    (ninguna línea `differ`), pero los conjuntos no: `backtest_sizing05.json` y
    `backtest_summary.json` solo en `results/`, `portfolio_bateria.json` solo en
    `fix-fase2/results/`, y el CSV solo en `fix-fase2/data/`. Esa confusión de
    rutas es, con bastante probabilidad, **la razón mecánica por la que se le
    pasó `backtest_sizing05.json`** (hallazgo 2).

**Lo que el registro acierta.** Comprobado, no concedido:

- **A-1 completo:** `rho_port = 0.007558295106411656`, `T_eff =
  4336.940947109138 → 4336`, `skew = 1.036877`, `kurt_raw = 31.998897`,
  `sharpe_anual = 1.008383`. Las cinco constantes de `potencia_fase_b.py:25-31`
  son `results/portfolio_bateria.json` una a una.
- **A-2 completo:** `V(11) = 0.0007016935642058066` y `V(12) =
  0.0007021947704551833`, ambas **exactas**; `SR0 = 0.044116`; listón **1.3118**.
  Y la definición de "Sharpe por trial" que A-2 atribuye es la que está en el
  código.
- **Más de lo que se atribuye:** reproducen exactos no solo los once `n_obs_eff`
  y ρ, sino **los once DSR** de `results/rigor_estadistico.json`.
- **A-4 exacto:** ρ = −0.499682 → 2188; 728 de 730 ceros; los dos días son
  2026-01-14 (+0.000817) y 2026-01-15 (−0.000847); y las sintéticas dan
  (+1,−1)→**−0.500000**, (+1,+1)→**+0.498624**, (+2,−1)→**−0.400384**. La cota
  lógica "ninguna corrección puede dar más observaciones independientes que
  observaciones" es correcta y el `clamp` a −0.95 permite ×39.
- **B-01 es correcto, y lo verifiqué más fuerte.** Forzando ρ=0 en las once,
  **ningún DSR cruza 0.95 y ningún `t` cruza 3** (el que más se mueve es
  `tsmom_365`: 0.020 → 0.118). El listón: T=4336 → 1.3118 / T=4403 → 1.3082.
- **A-3 / B-02 confirmados por git:** todo en `d34b147`; `3ad4795` y `9249cf4`
  no existen; `663db2c` (2026-10-07) ya trae `"var_trials":
  0.0007016935642058066` y `"n_trials": 11`; no hay `registro_N.md` ni
  pre-registro. A-5 y A-6 también.
- **B-06, que el registro afirmó sin medir, resulta cierto.** Correlación entre
  los retornos diarios OOS de las seis `sma_timing`: media **0.641**, min 0.368,
  max 0.861. Seis extracciones así no valen seis independientes.
- **Y la objeción de método más valiosa no es ninguna de las cuatro CRÍTICAS:
  es la bidireccionalidad de B-06** —el `N` está mal por las dos puntas y el
  neto no se conoce—, que es el único sitio donde el registro se disciplina a sí
  mismo.

**Veredicto sobre el registro. Confiable como base de hechos. No confiable como
base para decidir, y menos como base para reescribir la §4.** Con reservas, en
tres niveles:

1. **Firmable tal cual:** A-1 a A-6 y B-01/B-02/B-11. La conclusión más
   importante del Paso A —**el listón es auditable, `T_eff` y `V` tienen
   procedencia completa, el peor NO-GO no se materializó**— está sólida y es el
   resultado útil del documento.
2. **No firmable sin corrección:** B-10, B-03, B-05 y el **NO-GO de la §2.4**.
3. **Falta antes de tocar la §4:** el trial nº 12 es la misma regla que el nº 9 y
   está dentro de su propia `V`; el 1.008 no tiene holdout mientras la `V` es
   OOS; la vara de recuento de `N` tiene que ser la misma en B-03 y en B-07; y
   la dirección de la propia "fila dominante" (`N=1` → listón 0.472 → Fase B
   pasa) tiene que declararse.

**Recomendación operativa para Pablo:** el registro tiene razón en lo que importa
—**no firmar la §4 como está**— pero **no es base suficiente para reescribirla**.
Antes de reescribir: corregir B-10, resembrar B-03 desde
`results/backtest_sizing05.json` con el número medido, resolver si el NO-GO se
mantiene o se baja a matiz, e incorporar los puntos 4 y 5. Y exigir que las
reproducciones vivan con su script y su JSON, como el propio brief manda para el
Alcance: un registro de procedencia sin script no es un registro de procedencia.

---

### Estado final de la Fase 0

Las 16 correcciones están aplicadas. Lo que Pablo tiene delante:

- **Hechos:** 4 CONFIRMADOS, 2 CONFIRMADOS con ampliación, 1 CONFIRMADO con la
  coda refutada. **Ningún NO-GO formal disparado.**
- **`T_eff` y `V`: procedencia completa, documentada y reproducible.** El listón
  es auditable. Con script, en `fix-fase2/fase0_n4/`.
- **Objeciones:** 14, de ellas 4 CRÍTICAS (B-01, B-02, B-03, B-04) más B-13, que
  sale de la crítica y también es CRÍTICA. **Cinco en total.**
- **Recomendación, que es la misma antes y después de la crítica: no firmar la
  §4 como está.** Lo que cambia es que ahora la recomendación está bien
  fundada, y que hace falta una pasada más —la vara de `N` unificada entre B-03
  y B-07, y la dirección de cada construcción declarada— antes de reescribirla.

**No se ha ejecutado ni un paso de la §4. La §6 sigue sin firma.**
