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
