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
