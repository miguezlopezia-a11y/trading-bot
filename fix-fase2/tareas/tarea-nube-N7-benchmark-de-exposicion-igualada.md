# Tarea N7 (nube) — El benchmark de exposición igualada de Fase B

**Repo:** `miguezlopezia-a11y/trading-bot` · **Rama base:** `fase-b-recuperada`
**Rama de trabajo:** `nube/n7-benchmark-exposicion` · **PR contra:** `fase-b-recuperada`, nunca contra `main`
**Autor del brief:** sesión de escritorio, 2026-11-02 14:21 · **Estado:** parada en Fase 0
**Timeout de la Fase 0:** 25 min de reloj. Si se agota, se entrega lo hecho con lo que falta declarado.

## Lecturas previas obligatorias, enteras y en este orden

1. `fix-fase2/tareas/tarea-nube-N6-holdout-recuento-de-N-y-que-test-aplica.md`
   en la rama `nube/n6-holdout-y-recuento` — **el registro némesis completo,
   incluida la crítica literal del segundo agente y las trece respuestas.**
   Esta tarea nace de su punto ciego.
2. `docs/rigor_estadistico_resultado.md` (árbol de la **raíz**), sección
   *"Benchmark de exposición igualada"*, líneas 77-102.
3. `fix-fase2/src/rigor_estadistico.py`, función `benchmark_exposicion`
   (líneas 185-209).
4. `fix-fase2/src/portfolio_runner.py` entero. Es corto y es el sujeto.

Sin la 1 se repite trabajo ya pagado. Sin la 2 y la 3 no se sabe qué hizo
Fase A, y esta tarea es el análogo de eso para Fase B.

---

## 1. La pregunta

Seis tareas de auditoría han discutido si el Sharpe de Fase B supera el ruido
estadístico. **Ninguna ha preguntado si supera a comprar y aguantar.**

Fase A sí lo preguntó, y fue la prueba que más daño le hizo: con la exposición
igualada, nueve de once variantes perdían contra el buy&hold. Fase B heredó la
batería de cuatro pruebas (DSR, bootstrap, `t>3`, benchmark) pero su benchmark
**no está igualado en exposición**: compara una curva con gross medio 0.156
contra un igual-ponderado al 100 %.

La pregunta de esta tarea: **con la misma exposición y los mismos costes, ¿le
gana Fase B a comprar y aguantar los mismos activos?**

Si la respuesta es no, el expediente se cierra sin necesidad de resolver `N`,
`V`, el holdout ni `N* = 4.0786`. Un test de significancia dice si un resultado
supera el azar; no dice si supera la alternativa trivial. **Esta prueba es
anterior y más barata que todo el debate del DSR.**

---

## 2. Hechos verificados desde el escritorio

Reverificar los siete con comandos propios. **No creerlos.** Cada bloque de
abajo lleva el comando que lo produjo; si la salida no reproduce, es un hallazgo
y va al registro.

Todas las rutas de esta sección son **desde `fix-fase2/`**, salvo las dos que
dicen explícitamente *árbol de la raíz*. (N6 señaló que el brief anterior
rompía su propio convenio de rutas: aquí cada bloque dice desde dónde corre.)

### 2.1 El benchmark de Fase B está al 100 % de exposición y la estrategia al 15,6 %

```
$ git show fase-b-recuperada:fix-fase2/results/portfolio_bateria.json
{"n_trials": 12, "var_trials": 0.0007021947704551833, "sharpe_anual": 1.008,
 "n_obs": 4403, "n_obs_eff": 4336, "skew": 1.037, "kurt": 31.999,
 "sr0_per": 0.04412, "dsr": 0.7191, "t_stat": 3.48, "pasa_t3": true,
 "ic_retorno_anual_pct": [4.47, 20.91], "edge_ic": true, "retorno_pct": 317.52,
 "max_dd_pct": -26.9, "bench_retorno_pct": 132831.04, "bench_sharpe": 1.164,
 "bench_max_dd_pct": -88.96, "dias": 4404,
 "exposicion_media": 0.1559827260735808}
```

`sharpe_anual` 1.008 contra `bench_sharpe` **1.164**. `retorno_pct` 317.52
contra `bench_retorno_pct` **132831.04**. Y `exposicion_media` **0.1560**: la
estrategia compara un sexto de capital invertido contra un capital entero.

El contrapeso, que es real y hay que conservar: `max_dd_pct` −26.9 contra
`bench_max_dd_pct` **−88.96**.

### 2.2 Cómo construye Fase B su benchmark: igual-ponderado con rebalanceo diario, sin costes

```
$ git show fase-b-recuperada:fix-fase2/src/portfolio_runner.py | sed -n '318,328p'
        turnover = float(np.nansum(np.abs(w_prev - w_target)))
        coste = turnover * (COMMISSION + SLIPPAGE)
        equity *= (1 + r_p - coste)
        # benchmark: media de activos elegibles (misma condicion de historia)
        elig = [i for i in range(n) if rets.iloc[:t + 1].iloc[:, i].notna().sum() >= LOOKBACK + 1]
        r_b = float(np.nanmean(r_dia[elig])) if elig else 0.0
        eq_curve.append(equity)
        bench_curve.append((bench_curve[-1] if bench_curve else 1.0) * (1 + r_b))
        exposure.append(float(np.nansum(w_prev)))
```

Dos asimetrías en cinco líneas:

- **La estrategia resta `coste`; el benchmark no resta nada.** `nanmean` sobre
  los activos elegibles cada día es un **rebalanceo diario** al peso igual, y
  ese rebalanceo tiene turnover real que aquí sale gratis. El benchmark está
  idealizado.
- **El benchmark no se llama "buy & hold" en el código, pero sí en el docstring**
  (`portfolio_bateria.py:6`: *"benchmark = portfolio igual-ponderado buy&hold de
  los mismos 10 activos"*). Un igual-ponderado rebalanceado a diario **no es**
  buy & hold. Son dos curvas distintas y en 12 años de cripto la diferencia no
  es cosmética.

### 2.3 Cómo lo hizo Fase A: binario, y restringiendo también la estrategia

```
$ git show fase-b-recuperada:fix-fase2/src/rigor_estadistico.py | sed -n '185,192p'
def benchmark_exposicion(data, rets):
    """B&H con la misma exposicion: retornos de BTC solo en dias con posicion."""
    pos = data["pos"]
    aligned = data["bh"].reindex(pos.index).fillna(0.0)
    bh_exp = aligned[pos.values]
    st_exp = rets.reindex(pos.index).fillna(0.0)[pos.values]
```

Fase A tenía exposición **binaria** (dentro o fuera), así que igualar era
seleccionar los días con posición. Hizo dos cosas bien que hay que conservar:
tomó el mismo subconjunto de días para las dos series (`bh_exp` y `st_exp`), y
reportó Sharpe **y** Calmar.

Lo que no hizo, y es el defecto a no repetir: **comparó dos Sharpes a ojo, sin
intervalo de confianza sobre la diferencia.**

### 2.4 La exposición de Fase B es continua, así que "igualar" no tiene una sola traducción

```
$ git show fase-b-recuperada:fix-fase2/src/portfolio_runner.py | sed -n '31,42p'
ACTIVOS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
           "ADA-USD", "AVAX-USD", "LINK-USD", "DOGE-USD", "LTC-USD"]
LOOKBACK = 365
LAMBDA = 0.94
SIGMA_TARGET = 0.10          # anual
W_MAX = 0.20
GROSS_MAX = 1.0
VOL_TOPE_MULT = 1.25
PPY = 365
COMMISSION = 0.001
SLIPPAGE = 0.0005
DATA_DIR = "data/multi"
```

`exposure(t) = Σ w_i(t)` es un número real en `[0, 1]`, no un booleano. Hay al
menos tres formas de igualar y **dan resultados distintos**. La elección entre
ellas es el punto donde esta tarea puede hacer trampa, y por eso la §4 obliga a
las tres (ver también B-a).

### 2.5 No hay tasa libre de riesgo en ninguna parte del código

```
$ git grep -n -i -E "risk_free|risk-free|libre de riesgo|\brf\b|tasa" fase-b-recuperada -- fix-fase2/src/
(sin salida)
```

Importa porque al igualar exposición al 15,6 % queda un **84,4 % del capital sin
invertir**, y qué renta ese efectivo cambia el Sharpe del benchmark. Entre 2014
y 2026 la tasa pasó de ~0 % a ~5 %: no es un detalle.

### 2.6 La curva del benchmark existe y es auditable

```
$ git show fase-b-recuperada:fix-fase2/results/portfolio_benchmark.csv | head -3
date,0
2014-09-17,1.0
2014-09-18,1.0
$ git show fase-b-recuperada:fix-fase2/results/portfolio_benchmark.csv | tail -2
2026-10-06,1383.4857540084936
2026-10-07,1329.310356355764
$ ... | wc -l
4405
```

4404 filas de datos, `2014-09-17` → `2026-10-07`, de 1.0 a 1329.31 (= el
`bench_retorno_pct` 132831.04 de 2.1). Mismo rango que la equity. No hace falta
re-simular para la construcción (b) y (c); para (a) sí hace falta `exposure`,
que **no está en results/** y hay que regenerar.

### 2.7 Hay un segundo panel y tiene su propio benchmark

```
$ git show fase-b-recuperada:fix-fase2/src/portfolio_supervivencia.py | sed -n '6,13p'
UNIVERSO ALTERNATIVO (criterio fijado ANTES de correr, sin mirar la senal):
activos que estuvieron en el top-20 de market-cap en 2017-2021 y hoy cotizan
>85% por debajo de su maximo historico, con datos diarios congelables desde
el mismo proveedor (yfinance):
  EOS-USD  (top-5 en 2017-2018 por ICO; ~-95% desde ATH 2018)
  XLM-USD  (top-10 2017-2018; ~-90% desde ATH 2018)
  BCH-USD  (top-5 desde el fork 2017; ~-90% desde ATH 2017)
  FIL-USD  (top-15 en 2020; ~-98% desde ATH 2021)
  ICP-USD  (top-10 en 2021; ~-98% desde ATH 2021)
```

`results/portfolio_benchmark_muertos.csv` y `portfolio_equity_muertos.csv`
existen. El panel de 15 es donde el benchmark igual-ponderado debería sufrir más
(cinco activos a −90 %), así que es la construcción **más favorable a Fase B** y
hay que medirla igual, no en su lugar.

### 2.8 Lo que esto NO prueba

- No prueba que Fase B pierda. Prueba que **la comparación publicada no es
  comparable**, y que la que sí lo sería no está hecha.
- No dice nada sobre `N`, `V`, el holdout ni `N* = 4.0786`. Esta tarea es
  ortogonal a todo eso, y ahí está su valor: si Fase B pierde a igual
  exposición, aquel debate deja de importar.
- Un Sharpe más bajo que el benchmark **no cierra** el expediente por sí solo si
  el drawdown es un tercio: eso es una decisión de preferencia de riesgo, no un
  hecho. La tarea mide; no decide por Pablo.

---

## 3. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de la §4)

Los scripts de esta fase van en **`fix-fase2/fase0_n7/`**, nunca en
`auditoria_n7/` ni en `src/`. Cada uno ejecutable por separado, cada uno con su
JSON de salida o declarando por qué no lo tiene.

### Paso A — Verificación de hechos

Comandos propios, salida pegada literal. **Una cifra sin comando detrás es una
cifra inventada.**

- **A-1.** Reverificar los ocho bloques de la §2, uno por uno, con el veredicto
  **CONFIRMADO / CONFIRMADO con corrección / REFUTADO** y la salida al lado.
- **A-2.** Reproducir `sharpe_anual = 1.008` y `bench_sharpe = 1.164` desde
  `portfolio_equity.csv` y `portfolio_benchmark.csv` con implementación propia.
  Si no reproducen al tercer decimal, PARAR y reportar.
- **A-3.** Regenerar la serie `exposure(t)` ejecutando `portfolio_runner.py` con
  `STAMP_CONGELADO=20261009`, y verificar que su media da **0.1559827260735808**
  al bit. Es la entrada de la construcción (a) y de (b); si no reproduce, las dos
  quedan sin base.
- **A-4.** Medir el **turnover real del benchmark igual-ponderado** (el que el
  código no cobra): `Σ|w_bench(t) − w_bench(t−1)|` día a día, y cuánto le habría
  costado al 0.15 % por unidad. Es la cifra que dice si la asimetría de 2.2 es
  material o anecdótica.
- **A-5.** Verificar que el igual-ponderado del código **no** es buy & hold:
  construir el B&H puro (comprar a peso igual el primer día elegible de cada
  activo y no tocar) y dar las dos curvas con sus dos Sharpes y sus dos
  retornos. Si la diferencia es menor del 5 % en Sharpe, decirlo y seguir.
- **A-6.** Leer `portfolio_walkforward_temporal.py` y **copiar de ahí** los
  cortes de T1/T2/T3 con su código, en vez de asumirlos. El brief no los
  transcribe a propósito: no los he verificado.
- **A-7.** Intérprete y red: versión de Python, numpy, pandas. Y confirmar que
  **no hay red para datos de mercado** (N5 midió 0 de 10 fuentes). Si algún
  módulo de `src/` intentaría descargar al importarse, reportarlo sin parchearlo.

### Paso B — Ataque adversarial al planteamiento

**Mínimo cinco objeciones, con severidad (CRÍTICA / ALTA / MEDIA / BAJA) y con
qué cambia del Alcance si la objeción se sostiene.** Si una objeción resulta
falsa al medirla, se retira por escrito y se dice que era del revisor.

Dos están obligadas porque son donde esta tarea puede engañarse:

- **B-a (obligatoria).** Las tres construcciones de la §4.1 no son equivalentes
  y **una de ellas favorece a Fase B por construcción**: la (a), escalada día a
  día, le entrega al benchmark el timing de volatilidad que la propia estrategia
  decidió, así que mide la regla de señal con el acierto del vol-targeting ya
  regalado. ¿Es eso igualar exposición o es contaminar el benchmark? Y al revés:
  la (b), con `k` constante, ignora que la estrategia **eligió** estar poco
  expuesta en los días malos, lo que la castiga de más. Decidir **cuál de las
  tres es la comparación honesta** es el contenido de esta objeción, y la
  respuesta puede ser "ninguna sola, hay que leer las tres juntas".

- **B-b (obligatoria).** Busca activamente la construcción que **favorezca a
  Fase B** y mídela. El brief ya apunta dos candidatas (el panel de 15 de 2.7, y
  el drawdown de −26.9 contra −88.96 de 2.1); encuentra una tercera si existe.
  Un brief que solo halla pruebas en un sentido está mal construido, y este lo
  escribió alguien que ya dijo en voz alta que cree que Fase B pierde. **Esa
  predisposición es un hecho del expediente: trátala como sesgo del autor.**

Y al menos tres más de cosecha propia. Sugerencias no limitativas, por si el
material no da para cinco: la elección de `PPY = 365` para cripto; si el Sharpe
del diferencial tiene sentido cuando las dos series comparten los mismos
retornos subyacentes; si 4404 días de una sola clase de activo correlacionada
son 4404 observaciones de algo; qué pasa con los días en que `exposure = 0`.

### Maker/Verifier

Al acabar el Paso B, **invocar un segundo agente que solo critique este
registro.** En N4 encontró dos errores CRÍTICOS y en N6 trece hallazgos, uno
CRÍTICO que invertía el veredicto. Darle el registro y el brief, nada más.

Pegar su crítica **literal**, responderla hallazgo por hallazgo, y
**reverificar con comandos propios antes de aceptar nada**. Las correcciones se
aplican en el documento **y en los scripts**: un registro que corrige en prosa y
deja el script malo no ha corregido nada.

### NO-GO de la Fase 0

Cada uno es **binario**. N6 fue reprendido por graduar frenos que el brief
escribió sin grados: no lo repitas. Si uno se dispara, se para y se dice.

| Condición | Acción |
|---|---|
| No hay intérprete con numpy/pandas | PARAR |
| A-2 no reproduce `1.008` y `1.164` al tercer decimal | PARAR |
| A-3 no reproduce `exposicion_media` al bit | PARAR: (a) y (b) no tienen base |
| Algún hecho de la §2 sale REFUTADO | PARAR |
| B-a concluye que ninguna de las tres construcciones es honesta | PARAR y proponer la cuarta |
| Hace falta descargar datos de mercado | PARAR (no hay red; N5 · A-1) |

---

## 4. Alcance (NO EJECUTAR sin el OK escrito de Pablo en la §7)

Los pasos se numeran 4.x. **El OK de la §7 enumerará qué pasos cubre**; un OK
sin lista no autoriza nada (N6 · B-e2).

### 4.1 Las tres construcciones, las tres medidas

Para el panel de 10 y para el de 15, con el sello `20261009`:

- **(a) Escalado día a día:** `r_bench_a(t) = exposure(t−1) · r_bench(t)`.
- **(b) Escalado por constante:** `r_bench_b(t) = k · r_bench(t)`, con
  `k = 0.1559827260735808` (la media verificada en A-3).
- **(c) Binario tipo Fase A:** días con `exposure(t−1) > 0`, benchmark al 100 %
  esos días, y la estrategia restringida **al mismo subconjunto de días**, como
  hizo `benchmark_exposicion`.

Las tres en la misma tabla, con la **misma** batería: retorno total, Sharpe
anualizado, Calmar, max drawdown, y días efectivos.

**Prohibido elegir una y reportar solo esa.** Si el registro recomienda una, lo
dice aparte, con el argumento, y las otras dos siguen en la tabla.

### 4.2 Los cuatro hilos que decidirían el resultado si se dejan sueltos

Cada fila de 4.1 se emite **dos veces**, variando un hilo a la vez:

1. **Costes del benchmark:** sin coste (como hoy) y con el coste real del
   rebalanceo medido en A-4.
2. **Efectivo no invertido:** `rf = 0` y `rf` real. Si no hay serie de tasas
   congelada en el repo —y no la hay, 2.5—, usar `rf = 0` y **una cota
   superior declarada** (p. ej. 2 % anual plano sobre el capital no invertido),
   diciendo que es una cota y no un dato.
3. **Rebalanceo del benchmark:** el igual-ponderado diario del código y el B&H
   puro de A-5.
4. **Regla de entrada:** confirmar que `LOOKBACK + 1` se aplica igual a la
   estrategia y al benchmark en las tres construcciones. Si no, corregirlo y
   decir cuánto movió.

No es un menú del que elegir: es una tabla con todas las filas. (N6 · B-d llamó
a eso *"una máquina de metric-shopping"* cuando se deja a elección.)

### 4.3 El test, que es lo que Fase A no hizo

No comparar dos Sharpes a ojo. Para cada construcción:

- La serie diferencial `d(t) = r_estrategia(t) − r_bench_igualado(t)`.
- Su media anualizada, su Sharpe, y el **IC al 95 % por block bootstrap**
  (bloque 21 días, B = 10000, misma semilla y mismo estimador que
  `block_bootstrap_ci` de `rigor_estadistico.py`, importándolo, no
  reimplementándolo).
- El `t` del diferencial con `T_eff` por AR(1), coherente con el resto del
  expediente.

**La lectura:** si el IC del diferencial cruza cero, Fase B no tiene ventaja
demostrable sobre comprar y aguantar a igual exposición. Eso es un resultado, no
un fracaso.

### 4.4 Por tramos

Repetir 4.3 sobre T1/T2/T3 tal como A-6 los lea del código. Reportar, **sin
usarlo como criterio de decisión**: N6 · B-a estableció que comparar un tramo
contra un listón es un test elegido a posteriori. Aquí se reporta para ver
estabilidad, y se dice explícitamente que no decide.

### 4.5 Informe

`fix-fase2/docs/benchmark_exposicion_fase_b.md`, con la tabla completa, los
comandos, y un apartado final de **tres líneas**: qué dice el diferencial, qué
construcción lo dice, y qué queda sin medir.

### Límites de escritura

- Crear libremente: `fix-fase2/fase0_n7/*`, `fix-fase2/src/benchmark_exposicion_fase_b.py`,
  `fix-fase2/results/benchmark_exposicion_*.json`, `fix-fase2/docs/benchmark_exposicion_fase_b.md`,
  y el registro al final de **este** archivo.
- **No tocar** ningún fichero existente de `src/`, `results/`, `data/` ni
  `docs/`. Si `portfolio_runner.py` necesita un cambio para exponer `exposure`,
  **no se cambia**: se importa y se recalcula en el script nuevo, o se reporta
  como bloqueo.
- **No tocar** `data/` ni regenerar ningún CSV. Sello `20261009`, el congelado.
- Nada en la raíz del repo. Nada fuera de `fix-fase2/`.

### NO-GO del Alcance

| Condición | Acción |
|---|---|
| Un paso exige modificar un fichero existente | PARAR y reportar |
| El bootstrap no reproduce el IC `[4.47, 20.91]` de 2.1 como control | PARAR |
| Las tres construcciones dan veredictos opuestos entre sí | **No parar**: reportarlo como el resultado, que es informativo |
| Tentación de añadir una variante de señal o un parámetro nuevo | PARAR: esta tarea no evalúa señales |

---

## 5. Lo que esta tarea NO hace

- **No evalúa ninguna señal nueva ni ninguna variante de parámetro.** Mide lo ya
  medido contra otro benchmark. **No consume trials y no mueve `N`.** Declararlo
  en el registro con esas palabras.
- No resuelve `N`, `V`, el holdout, `N* = 4.0786` ni H10. Es ortogonal.
- No decide si Fase B se activa o se abandona. Eso es de Pablo.
- No toca `main`, ni el paper runner, ni nada del pipeline operativo.

## 6. Entregables

1. `## Registro de revisión némesis` al final de **este** archivo: Paso A con
   salidas, Paso B con las objeciones y severidades, la crítica literal del
   Maker/Verifier y las respuestas una por una, y el veredicto con el estado de
   cada NO-GO.
2. Los scripts en `fix-fase2/fase0_n7/`.
3. **PARAR.** Ni un paso de la §4 sin OK escrito en la §7.
4. PR contra `fase-b-recuperada` con el registro. En la descripción, las tres
   cifras que más muevan la aguja y nada más.

## 7. Estado de la tarea

| | |
|---|---|
| Fase 0 ejecutada | [pendiente] |
| Maker/Verifier invocado | [pendiente] |
| NO-GO disparados | [pendiente] |
| **OK de Pablo para ejecutar el Alcance** | **[pendiente]** — y cuando lo dé, enumerando los pasos de la §4 que cubre |

---

## Checklist de entrega (las nueve, sin excepción)

- [ ] **Sintaxis:** todo script citado se ejecuta antes de pegarlo; ningún
      fragmento inventado.
- [ ] **Hashes y sellos:** `STAMP_CONGELADO=20261009` explícito en cada
      ejecución; los `.sha256` de `data/multi/` verificados, no asumidos.
- [ ] **Tablas:** cada tabla con su unidad y su `n`; ninguna cifra sin comando.
- [ ] **Rutas:** cada bloque dice desde dónde corre (`fix-fase2/` o la raíz).
      Es el error que N6 heredó del brief anterior.
- [ ] **Timeouts:** 25 min de Fase 0; si se agota, se entrega lo hecho con lo
      que falta declarado.
- [ ] **Reproducibilidad:** semilla fija (43, la del expediente) y `B = 10000`
      en todo bootstrap; el IC `[4.47, 20.91]` como control de que la
      implementación importada es la misma.
- [ ] **Reversibilidad:** nada fuera de los límites de escritura; el árbol queda
      limpio salvo los ficheros nuevos.
- [ ] **Sincronía tarea↔registro:** el registro va **en este archivo**, no en
      otro; las correcciones se aplican también a los scripts.
- [ ] **Fase 0 némesis:** Paso A y Paso B separados, cinco objeciones mínimo,
      Maker/Verifier invocado y su crítica pegada literal.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Registro de revisión némesis

**Fecha:** 2026-11-02 · **Ejecutor:** sesión N7 en la nube (Claude Code, Opus 5).
**Rama:** `nube/n7-benchmark-exposicion`, cortada de `fase-b-recuperada` @ `80e41d4`.
PR contra `fase-b-recuperada`, nunca contra `main`.
**Alcance ejecutado:** solo la **Fase 0** (§3), pasos A y B, más el segundo agente
del Maker/Verifier. **Ni un paso de la §4.** La §7 sigue sin firma.
**Scripts:** `fix-fase2/fase0_n7/`, **once** ficheros `.py`, **once** JSON de salida
(uno por script) y **seis** CSV de caché. Los once se ejecutan por separado y los
once se han ejecutado así antes de pegar nada. Ninguno está en `auditoria_n7/` ni
en `src/`.
**Rutas:** los once corren **desde `fix-fase2/`**. Los dos bloques que leen el
árbol de la **raíz** (`docs/rigor_estadistico_resultado.md` y el `git grep` de
§2.5) lo dicen en su propia línea y lo hacen con `cwd=".."` dentro del script.
**Lecturas previas:** las cuatro del encabezado, enteras y en orden. El registro
némesis de N6 completo (2306 líneas), incluida la crítica literal de su segundo
agente y las **trece** respuestas.
**Esta tarea no evalúa ninguna señal nueva ni ninguna variante de parámetro. Mide
lo ya medido contra otro benchmark. No consume trials y no mueve `N`.**

---

### Resumen ejecutivo

| | Resultado |
|---|---|
| Hechos de la §2 | **6 CONFIRMADOS** (2.1, 2.2, 2.3, 2.5, 2.6, 2.8-como-regla) y **2 CONFIRMADOS con corrección** (2.4 y 2.7: etiquetas de línea desplazadas). **Ninguno REFUTADO** → ese NO-GO no se dispara. Lo que **sí** sale REFUTADA es la **§1**, que no es §2: *"Ninguna [tarea] ha preguntado si supera a comprar y aguantar"* es falso |
| A-2 Sharpes | **REPRODUCEN los dos al tercer decimal** con implementación propia: 1.008268 → **1.008** y 1.164273 → **1.164**. NO-GO no se dispara |
| A-3 `exposicion_media` | **NO reproduce al bit con el sello que el brief manda (`20261009`)**: da `0.15591192138630272`, diferencia −7.08e-05. Reproduce **al bit** (diferencia 0.0e+00) con el sello **`20261007`**, que es el del número publicado (`dias: 4404`). **El NO-GO de A-3 SE DISPARA tal como está escrito** |
| A-4 turnover del bench | La fórmula del brief mide **0**: 2.92 total en **4 días** de 4404, porque los pesos objetivo del igual-ponderado son constantes. El turnover **real** del rebalanceo diario es **68.81** (0.0156/día), **0.855 %/año**, **−9.70 %** del valor final y **−0.0110** de Sharpe. **Material en retorno, anecdótica en Sharpe** |
| A-5 B&H puro | El igual-ponderado **no es** buy & hold: 132831 % contra **75765 %** (ratio 0.571). En Sharpe 1.1643 contra **1.1078**, **−4.85 % relativo: por debajo del 5 % que el propio brief fija**, así que se dice y se sigue |
| A-6 tramos | Copiados del código (`portfolio_walkforward_temporal.py:34-36`), no asumidos. T3 cierra con el centinela `2262-12-31`, que **revienta** como cortador de `.loc` en pandas 3.0.5 |
| A-7 entorno y red | Python 3.13.18, numpy 2.5.3, pandas 3.0.5. **0 de 10 fuentes de mercado**, PyPI sí. **FRED inalcanzable** → no hay forma de traer una serie de tasas, confirmando §2.5 por el otro lado. 5 módulos de `src/` descargarían si se ejecutasen: reportados, no parcheados |
| Paso B | **Seis objeciones**, de ellas **1 CRÍTICA** (B-c), **2 ALTAS** (B-a, B-d), **2 MEDIAS** (B-b, B-e), **1 RETIRADA** (B-f.1, era mía) |
| **B-c, la que decide** | **La comparación que el brief dice que no existe YA ESTÁ HECHA, MEDIDA, PUBLICADA Y AUDITADA**, un día antes del brief: `fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py` + `salida_3_0d_exposicion.json`, commit `1713e13` del **2026-11-01**, documentada como **H11** en `docs/estado-auditoria-n1.md` y como **3.0d** y **5-bis** en `docs/auditoria_harness_n1.md` |
| B-a | De las tres construcciones, **(b) no es una comparación**: es un no-op para el Sharpe, idéntico a 1e-12 al 1.164 publicado. La honesta es **(a) alineada**, y el brief la escribe **mal alineada** |
| B-b | **Diez construcciones medidas. Fase B gana en una, y esa una no está igualada en exposición.** La más favorable de las honestas (panel de 15 + B&H puro + igual exposición) da **−0.0022**: empate técnico, no victoria |
| Maker/Verifier | Invocado. Crítica literal pegada y respondida hallazgo por hallazgo más abajo |

**La cifra que decide la tarea, y es una resta:** a igual exposición Fase B pierde
por **0.063** de Sharpe (1.0083 contra 1.0711), no por los 0.156 del par
publicado. Esa cifra **ya estaba publicada el 2026-11-01**. El brief la vuelve a
pedir sin saber que existe.

**Lo que esta Fase 0 añade y no estaba:** el coste real del rebalanceo del
benchmark (A-4), la curva del B&H puro (A-5), que (b) es un no-op (B-a.2), que el
brief duplica el retardo de `exposure` (B-a.3), que el contrapeso del drawdown
**se evapora** a igual exposición (B-b.3), que `Sharpe(d)` y
`Sharpe(est) − Sharpe(bench)` son dos cantidades distintas que la §4.3 confunde
(B-d), y que el sello que el brief manda en A-3 no es el del número que manda
verificar.

---

## Paso A — Verificación de hechos

Todo con comandos propios y salida pegada literal. El Sharpe, el Calmar, el
drawdown, el turnover, el B&H puro y las permutaciones están **reimplementados a
mano** (`numpy`/`pandas` desnudos); de `src/` se importa **solo**
`portfolio_runner.cargar_congelados` y `portfolio_runner.simulate`, porque el
brief prohíbe editar `src/` y reimplementar el simulador sería medir otra cosa,
no reverificar.

**Aviso de límite de escritura que el brief se contradice a sí mismo.** A-3 manda
*"regenerar la serie `exposure(t)` **ejecutando** `portfolio_runner.py`"*. Su
`main()` escribe en `results/portfolio_equity.csv`, `results/portfolio_benchmark.csv`
y `results/portfolio_runner.json` (líneas 370-372), que los **Límites de escritura**
del propio brief prohíben tocar. Aquí se **importa** `simulate()` y no se llama a
`main()`: `git diff --stat` queda vacío y `git status --short` solo muestra
`?? fix-fase2/fase0_n7/`.

### §2.1 — El benchmark está al 100 % y la estrategia al 15,6 % → **CONFIRMADO**

`python3 -I fase0_n7/a1_hechos_seccion2.py`, desde `fix-fase2/`. Los **veinte**
campos que el brief pega coinciden con el JSON, uno por uno:

```
  n_trials                 brief=12                       json=12                       OK
  var_trials               brief=0.0007021947704551833    json=0.0007021947704551833    OK
  sharpe_anual             brief=1.008                    json=1.008                    OK
  n_obs                    brief=4403                     json=4403                     OK
  n_obs_eff                brief=4336                     json=4336                     OK
  skew                     brief=1.037                    json=1.037                    OK
  kurt                     brief=31.999                   json=31.999                   OK
  sr0_per                  brief=0.04412                  json=0.04412                  OK
  dsr                      brief=0.7191                   json=0.7191                   OK
  t_stat                   brief=3.48                     json=3.48                     OK
  pasa_t3                  brief=True                     json=True                     OK
  ic_retorno_anual_pct     brief=[4.47, 20.91]            json=[4.47, 20.91]            OK
  edge_ic                  brief=True                     json=True                     OK
  retorno_pct              brief=317.52                   json=317.52                   OK
  max_dd_pct               brief=-26.9                    json=-26.9                    OK
  bench_retorno_pct        brief=132831.04                json=132831.04                OK
  bench_sharpe             brief=1.164                    json=1.164                    OK
  bench_max_dd_pct         brief=-88.96                   json=-88.96                   OK
  dias                     brief=4404                     json=4404                     OK
  exposicion_media         brief=0.1559827260735808       json=0.1559827260735808       OK
  sharpe_anual 1.008 vs bench_sharpe 1.164 -> el bench GANA por +0.156
  retorno 317.52 vs bench 132831.04 -> ratio 418.3x
  maxDD -26.9 vs bench -88.96 -> el contrapeso es real, ratio 3.31x
  -> §2.1 CONFIRMADO
```

**Pero el contrapeso del drawdown que el brief llama *"real y hay que
conservar"* no sobrevive a su propia corrección.** Medido en B-b.3: a igual
exposición el benchmark escalado tiene `maxDD −27.07 %` contra los `−26.90 %` de
Fase B. El 3.31× se convierte en 1.006×. El brief lo presenta como contrapeso a
favor de Fase B y, a igual exposición, **se evapora**. Es un hallazgo **en contra**
de Fase B que el brief no vio, y va anotado aquí porque está en el bloque que
manda reverificar.

### §2.2 — Igual-ponderado con rebalanceo diario, sin costes → **CONFIRMADO**

Las nueve líneas que el brief pega están literales en el fichero. **Desviación de
forma:** el brief etiqueta el bloque `sed -n '318,328p'` —once líneas— y pega
nueve; las dos que falta son `318` y `319`. Lo anoto con la misma vara con la que
el registro de N6 fue obligado a anotar las desviaciones de la §2.1 de su brief:
*"importan porque están en la sección que manda reverificar"*.

```
  318:         r_dia = rets.iloc[t].values
  319:         r_p = float(np.nansum(w_prev * r_dia))
  320:         turnover = float(np.nansum(np.abs(w_prev - w_target)))
  321:         coste = turnover * (COMMISSION + SLIPPAGE)
  322:         equity *= (1 + r_p - coste)
  323:         # benchmark: media de activos elegibles (misma condicion de historia)
  324:         elig = [i for i in range(n) if rets.iloc[:t + 1].iloc[:, i].notna().sum() >= LOOKBACK + 1]
  325:         r_b = float(np.nanmean(r_dia[elig])) if elig else 0.0
  326:         eq_curve.append(equity)
  327:         bench_curve.append((bench_curve[-1] if bench_curve else 1.0) * (1 + r_b))
  328:         exposure.append(float(np.nansum(w_prev)))
  lineas citadas por el brief que NO estan en 318-328: []
  portfolio_bateria.py:6 = 'benchmark = portfolio igual-ponderado buy&hold de los mismos 10 activos'
  el docstring dice 'buy&hold': True
  el codigo rebalancea a diario (nanmean del dia) -> NO es buy&hold
  -> §2.2 CONFIRMADO (magnitud medida en A-4 y A-5)
```

Las **dos asimetrías del brief se confirman y las dos están cuantificadas**: el
coste en A-4, el "no es buy&hold" en A-5. Y hay una **tercera que el brief no ve**
y que sale de la línea 324, medida en A-4.1.

### §2.3 — Fase A lo hizo binario y restringiendo también la estrategia → **CONFIRMADO**

```
  185: def benchmark_exposicion(data, rets):
  186:     """B&H con la misma exposicion: retornos de BTC solo en dias con posicion."""
  reporta Sharpe B&H igual-expo : True
  reporta Calmar B&H igual-expo : True
  mismo subconjunto de dias para las dos series: True
  calcula IC sobre la DIFERENCIA de Sharpes: False   (el brief dice que no, y es el defecto a no repetir)
  ---- §1: '9 de 11 variantes perdian contra el B&H' (arbol de la RAIZ) ----
  variantes tabuladas: 11   pierden en Sharpe: 9
  -> §2.3 CONFIRMADO (9 de 11, como dice la §1)
```

Las tres cosas que el brief afirma de Fase A salen: mismo subconjunto de días, se
reporta Sharpe **y** Calmar, y **no** hay intervalo de confianza sobre la
diferencia. Y el "nueve de once" de la §1 se reverifica contando la tabla del
árbol de la raíz: 9 de 11.

### §2.4 — La exposición es continua → **CONFIRMADO con corrección**

Las diez constantes salen exactas. **Corrección de forma:** el brief etiqueta
`sed -n '31,42p'` y pega `ACTIVOS` completo, pero `ACTIVOS` **empieza en la línea
30**; la 31 es su segunda línea y la 42 es `RESULTS`, que el brief no pega.

```
  32: LOOKBACK = 365
  33: LAMBDA = 0.94
  34: SIGMA_TARGET = 0.10          # anual
  35: W_MAX = 0.20
  36: GROSS_MAX = 1.0
  37: VOL_TOPE_MULT = 1.25
  38: PPY = 365
  39: COMMISSION = 0.001
  40: SLIPPAGE = 0.0005
  41: DATA_DIR = "data/multi"
  42: RESULTS = "results/portfolio_runner.json"
  constantes que difieren del brief: ninguna
```

Y la afirmación sustantiva —`exposure(t) ∈ [0,1]` real, no booleano— se confirma
con la medida: `min 0.000000`, `max 0.430286`, media `0.155983`, y **915 días a
cero exacto** (20,78 %). O sea: la exposición es continua **y además** tiene una
masa del 20 % en el cero, que es un hecho que el brief no menciona y que importa
para (c) y para B-e.

### §2.5 — No hay tasa libre de riesgo en el código → **CONFIRMADO**

```
  salida del grep del brief: ''   rc=1
  ficheros con pinta de serie de tasas en data/: ninguno
```

El `git grep` del brief sale vacío (`rc=1`). Las únicas apariciones del patrón en
toda la rama son **el propio brief de N7** y la tarea S2. Y A-7 cierra el caso
por el otro lado: **FRED es inalcanzable** (`http=000`), así que no hay manera de
traer una serie de tasas ni con permiso.

**Consecuencia que el brief no saca, y que vacía uno de sus cuatro hilos.** El
hilo 2 de la §4.2 (`rf = 0` contra `rf` real) es **exactamente nulo en la
construcción (a)**: si el benchmark se escala a `exposure(t)`, las dos series
tienen el **mismo** efectivo no invertido todos los días, luego `rf` suma lo
mismo a las dos y **se cancela al restar**. Solo importa contra el benchmark al
100 %, que es el par que (a) sustituye.

### §2.6 — La curva del benchmark existe y es auditable → **CONFIRMADO**

```
  head -3:
    date,0
    2014-09-17,1.0
    2014-09-18,1.0
  tail -2:
    2026-10-06,1383.4857540084936
    2026-10-07,1329.310356355764
  wc -l = 4405   filas de datos = 4404
  2014-09-17 -> 2026-10-07, 1.0 -> 1329.310356355764
  retorno implicito = 132831.04 %  (brief: 132831.04)
  ¿hay serie exposure en results/? False
```

Los cinco números del brief salen, incluido que `exposure` **no** está en
`results/`.

### §2.7 — Hay un segundo panel con su propio benchmark → **CONFIRMADO con corrección**

```
  6: UNIVERSO ALTERNATIVO (criterio fijado ANTES de correr, sin mirar la senal):
  ...
  13:   FIL-USD  (top-15 en 2020; ~-98% desde ATH 2021)
  OJO: el brief etiqueta '6,13p' y pega NUEVE lineas: ICP-USD es la 14.
  ficheros: {'portfolio_benchmark_muertos.csv': True, 'portfolio_equity_muertos.csv': True, 'portfolio_supervivencia.json': True}
  portfolio_supervivencia.json: {'n_activos': 15, 'n_vetos_wmax': 2724, 'n_vetos_vol': 3190, 'exposicion_media': 0.15711804729336995}
  data/multi_muertos: 15 CSV, sellos ['20261009']
```

Tercera etiqueta de líneas desplazada del brief. Y **un hecho operativo que el
brief no dice y que condiciona la §4.1**: el panel de 15 **solo existe con sello
`20261009`**. No hay `20261007`. Luego la §4.1 no puede correr los dos paneles
con el mismo sello que el `k` que ella misma fija, y eso es la otra mitad del
problema de A-3.

### §2.8 — Lo que esto NO prueba → **CONFIRMADO como regla. La §1 del brief, REFUTADA**

La §2.8 es una regla de método y se cumple. Lo comprobable de ella es su premisa,
y la premisa es falsa:

```
  ficheros de fix-fase2/ que mencionan igual exposicion:
    fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py
    fix-fase2/docs/auditoria_harness_n1.md
    fix-fase2/docs/estado-auditoria-n1.md
    fix-fase2/docs/rigor_estadistico_resultado.md
    fix-fase2/src/rigor_estadistico.py
  PERO: portfolio_walkforward_temporal.json YA publica
    supera_bench_sharpe = {'T1_2015-2018': False, 'T2_2019-2022': False, 'T3_2023-fin': False}
```

La §1 dice, en negrita: *"**Ninguna ha preguntado si supera a comprar y
aguantar.**"* **Es falso dos veces.** `portfolio_walkforward_temporal.py:100`
calcula `supera_bench_sharpe` y lo publica para los tres tramos (`False`, `False`,
`False`), sin igualar exposición; y el 3.0d de N1 lo preguntó **con** la exposición
igualada. Lo que la §1 quería decir —que no existe la comparación a igual
exposición para Fase B— también es falso, y eso es **B-c**.

---

### A-2 — Reproducir 1.008 y 1.164 con implementación propia → **REPRODUCEN. NO-GO no se dispara**

`python3 -I fase0_n7/a2_sharpes_propios.py`, desde `fix-fase2/`:

```
=== A-2.1 las dos curvas ===
  equity     4404 dias  2014-09-17 -> 2026-10-07  1.0 -> 4.175151198990724
  benchmark  4404 dias  2014-09-17 -> 2026-10-07  1.0 -> 1329.310356355764
  mismas fechas: True
=== A-2.2 Sharpe anualizado, implementacion propia ===
  estrategia  ddof=1: 1.008268  (publicado 1.008)  n=4403
  estrategia  ddof=0: 1.008383
  benchmark   ddof=1: 1.164273  (publicado 1.164)  n=4403
  benchmark   ddof=0: 1.164405
=== A-2.3 retornos totales ===
  retorno_pct       mio=317.52   publicado=317.52
  bench_retorno_pct mio=132831.04   publicado=132831.04
=== A-2.4 max drawdown ===
  max_dd_pct        mio=-26.90   publicado=-26.9
  bench_max_dd_pct  mio=-88.96   publicado=-88.96
=== A-2.5 veredicto del NO-GO ===
  1.008 reproduce al 3er decimal: True  (round=1.008)
  1.164 reproduce al 3er decimal: True  (round=1.164)
  -> NO-GO NO SE DISPARA
```

**Los dos reproducen al tercer decimal.** Se dan las dos convenciones de `sd`
porque el expediente usa las dos: `metrics()` de `portfolio_runner.py:344` usa
`pd.Series.std()` (ddof=1) y da 1.008268; `rigor_estadistico.py:192` usa
`np.std()` (ddof=0) y da 1.008383, que es el número que N6 verificó al bit en su
A-5.3. **Las dos redondean a 1.008**, así que no hay conflicto, pero conviene que
esté dicho antes de que alguien compare 1.0083 con 1.0082 y crea que algo no
cuadra.

### A-3 — `exposicion_media` al bit → **NO REPRODUCE CON EL SELLO QUE EL BRIEF MANDA. EL NO-GO SE DISPARA**

`python3 -I fase0_n7/a3_exposure_regenerada.py`, desde `fix-fase2/`:

```
=== A-3.1 re-simulacion con STAMP_CONGELADO=20261007 ===
  dias                 : 4404  2014-09-17 -> 2026-10-07
  exposicion_media     : 0.1559827260735808
  objetivo publicado   : 0.1559827260735808
  diferencia           : 0.000e+00
  identica al bit      : True
  exposure min/max     : 0.000000 / 0.430286
  dias con exposure==0 : 915  (20.78%)
  equity final         : 4.175151198990724
  bench final          : 1329.310356355764

=== A-3.1 re-simulacion con STAMP_CONGELADO=20261009 ===
  dias                 : 4406  2014-09-17 -> 2026-10-09
  exposicion_media     : 0.15591192138630272
  objetivo publicado   : 0.1559827260735808
  diferencia           : -7.080e-05
  identica al bit      : False
  exposure min/max     : 0.000000 / 0.430286
  dias con exposure==0 : 917  (20.81%)
  equity final         : 4.175151198990724
  bench final          : 1277.6180579816871

=== A-3.2 contraste con la equity congelada de results/ ===
  sello 20261007: 4404 fechas comunes, max|dif equity| = 0.000e+00
  sello 20261009: 4404 fechas comunes, max|dif equity| = 0.000e+00

=== A-3.3 veredicto del NO-GO ===
  reproduce AL BIT con el sello: ['20261007']
  OJO: el brief manda el sello 20261009 explicitamente en A-3.
```

**El brief manda, literal:** *"Regenerar la serie `exposure(t)` ejecutando
`portfolio_runner.py` con `STAMP_CONGELADO=20261009`, y verificar que su media da
**0.1559827260735808** al bit."* Hecho: da `0.15591192138630272`. **No reproduce.**

**Y el NO-GO de la §3 es binario:** *"A-3 no reproduce `exposicion_media` al bit →
PARAR: (a) y (b) no tienen base"*. **Se dispara.** No lo gradúo, no lo declaro
"parcialmente disparado" y no lo muevo a un paso en vez de a la tarea: el brief
lo escribió sin grados y N6 fue reprendido por exactamente eso.

**El diagnóstico, que es lo que Pablo necesita y no cambia el estado del NO-GO.**
La constante `0.1559827260735808` es del run con sello **`20261007`**, como
declara el propio JSON del brief (`"dias": 4404`, y el 20261009 tiene 4406). El
brief **empareja un sello con una constante de otro sello**, que es el mismo
defecto `(N, V)` descolocado que el segundo agente de N6 le encontró a N6 en su
hallazgo 2. Con el sello coherente la cifra reproduce con diferencia **0.0e+00**,
y las dos curvas coinciden a **0.0e+00** en las 4404 fechas comunes.

**Consecuencia para la §4.1, que no es cosmética.** La §4.1 dice *"Para el panel
de 10 y para el de 15, **con el sello `20261009`**"* y acto seguido fija
`k = 0.1559827260735808`, que es del `20261007`. Las dos instrucciones no pueden
cumplirse a la vez. Y §2.7 cierra el cerco: **el panel de 15 solo existe con sello
`20261009`**, así que no hay un sello que sirva para las dos mitades de la §4.1
tal como está escrita. Hay que reescribirla antes de cualquier firma.

### A-4 — Turnover real del benchmark igual-ponderado → **la fórmula del brief mide cero**

`python3 -I fase0_n7/a4_turnover_benchmark.py`, desde `fix-fase2/`, sello `20261007`:

```
=== A-4.1 sello 20261007: elegibilidad bench vs estrategia ===
  dias 4404, activos 10
  dias en que los dos conjuntos difieren : 4
  celdas (dia,activo) que difieren        : 10
  celdas en que el BENCH admite y la estrategia NO: 10
  celdas en que la ESTRATEGIA admite y el bench NO: 0
  -> el benchmark usa rets.iloc[:t+1]: cuenta el retorno DEL DIA t
     para decidir si el activo entra el dia t. La estrategia usa
     [:t]. El benchmark admite cada activo UN DIA ANTES.
=== A-4.2 sello 20261007: turnover del benchmark ===
  (1) formula del brief  Sum|w(t)-w(t-1)| :
      total=2.922222  medio/dia=0.00066354  dias con turnover>0=4
      coste total acumulado (suma simple) = 0.4383 %
  (2) turnover REAL del rebalanceo diario (vuelta de la deriva):
      total=68.8117  medio/dia=0.01562481  dias con turnover>0=4038
      coste medio/dia = 0.2344 bps   anualizado = 0.855 %/ano
=== A-4.3 sello 20261007: efecto compuesto sobre la curva ===
  bench sin coste (como hoy) : final=1329.3104  retorno=132831.04 %
  bench con coste real       : final=1200.3827  retorno=119938.27 %
  factor de reduccion        : 0.903012  (-9.70 % del valor final)
  Sharpe bench sin coste     : 1.1643
  Sharpe bench con coste real: 1.1533   (delta -0.0110)
  -> la asimetria de 2.2 es ANECDOTICA en Sharpe (|delta| 0.0110)
```

**La fórmula que el brief escribe no mide el turnover del rebalanceo.** Los pesos
objetivo del igual-ponderado son `1/|elig|`, constantes mientras el conjunto
elegible no cambie, así que `Σ|w(t) − w(t−1)|` vale **0 en 4400 de 4404 días** y
da un total de 2.92. Lo que de verdad paga un rebalanceo diario es devolver la
**deriva** del día a `1/|elig|`: eso da **68.81**, veintitrés veces más.

**Respuesta a la pregunta que A-4 hace** (*"la cifra que dice si la asimetría de
2.2 es material o anecdótica"*): **las dos cosas, y hay que decirlo con los dos
números.** En Sharpe es **anecdótica**: −0.0110, y no cambia ningún signo. En
retorno acumulado es **material**: el benchmark pierde el **9,70 %** de su valor
final, y como la §4.1 pide retorno total en la misma tabla que el Sharpe, la fila
"sin coste" sobreestima el benchmark en un 9,7 % de los doce años.

**Y la tercera asimetría, que el brief no ve** (es su hilo 4 de la §4.2, que pide
*"confirmar que `LOOKBACK + 1` se aplica igual a la estrategia y al benchmark"*):
**no se aplica igual.** La línea 324 usa `rets.iloc[:t + 1]` —el retorno del día
`t` incluido— y la 293-294 usa `rets[tk].iloc[:t]`. El benchmark decide la
elegibilidad **mirando el día que va a cobrar**. Son **10 celdas en 4 días** de
44 040 posibles, así que el efecto es despreciable, pero la respuesta al hilo 4
es *"no, y aquí está la línea"*, no *"sí"*.

### A-5 — El igual-ponderado no es buy & hold → **CONFIRMADO en retorno, por debajo del umbral del brief en Sharpe**

`python3 -I fase0_n7/a5_bh_puro_vs_igualponderado.py`, desde `fix-fase2/`:

```
=== A-5 sello 20261007  (4404 dias, 2014-09-17 -> 2026-10-07) ===
  dias de ENTRADA de algun activo: 4  -> ['2015-09-18', '2018-11-10', '2021-04-11', '2021-09-22']
  construccion                                    retorno %   Sharpe   maxDD %   Calmar
  igual-ponderado diario (EL DEL CODIGO)          132831.04   1.1643    -88.96  123.754
  B&H puro (reparto solo al entrar)                75764.91   1.1078    -89.45   70.197
  B&H universo fijo del 1er dia elegible           19158.17   0.9869    -89.26   17.789
  diferencia en Sharpe EW vs B&H puro : -0.0565  (4.85 % relativo)
  -> MENOR del 5 %: se dice y se sigue
  ratio de retorno final B&H/EW : 0.5707
```

Definición del B&H puro, declarada porque **no es única**: un activo entra el
primer día en que es elegible con la misma condición del código; el día en que
entra alguien la cartera se reparte a peso igual entre los elegibles de ese día y
**no se toca** hasta la siguiente entrada. Son **cuatro** entradas en doce años.
Se da también la variante de universo fijo (solo los elegibles del primer día),
que es más limpia y es otro universo.

**El brief dice** *"en 12 años de cripto la diferencia no es cosmética"*. **En
retorno acierto y de sobra: el B&H puro vale 0.571× el igual-ponderado**, o sea
que el rebalanceo diario gratis le regala al benchmark un 75 % más de retorno
final. **En Sharpe, el propio umbral del brief la declara cosmética:** 4,85 %
relativo, y el brief fija *"si la diferencia es menor del 5 % en Sharpe, decirlo y
seguir"*. Se dice: **4,85 %, por debajo del 5 %. Y se sigue.** Es un filo
estrecho y conviene que conste que está del lado de "cosmética" por 0,15 puntos
porcentuales, no por margen.

### A-6 — Los tramos T1/T2/T3, copiados del código

`python3 -I fase0_n7/a6_tramos_desde_codigo.py`, desde `fix-fase2/`:

```
=== A-6.1 las lineas literales del codigo ===
  34: TRAMOS = [("T1_2015-2018", "2015-09-01", "2018-12-31"),
  35:           ("T2_2019-2022", "2019-01-01", "2022-12-31"),
  36:           ("T3_2023-fin", "2023-01-01", "2262-12-31")]
=== A-6.4 contraste con el JSON publicado ===
  coincide con el codigo: True
=== A-6.5 dias reales de cada tramo sobre la equity congelada ===
  T1_2015-2018     2015-09-01 -> 2018-12-31  dias= 1218 retornos= 1217
  T2_2019-2022     2019-01-01 -> 2022-12-31  dias= 1461 retornos= 1460
  T3_2023-fin      2023-01-01 -> 2026-10-07  dias= 1376 retornos= 1375
=== A-6.6 el walkforward publicado YA tiene campos de benchmark ===
  T1_2015-2018 {'sharpe_anual': 1.328, 'bench_sharpe': 1.467, 'supera_bench_sharpe': False}
  T2_2019-2022 {'sharpe_anual': 1.219, 'bench_sharpe': 1.294, 'supera_bench_sharpe': False}
  T3_2023-fin  {'sharpe_anual': 0.572, 'bench_sharpe': 0.802, 'supera_bench_sharpe': False}
```

Copiados, no asumidos, y coinciden con `tramos_definicion` del JSON publicado.
**Dos avisos para quien escriba la §4.4:**

1. **T3 cierra con el centinela `"2262-12-31"`**, no con la fecha real de fin. El
   código lo usa en una **máscara booleana** (`eq.index <= fin`, línea 84) y eso
   funciona; usarlo como cortador de `.loc[a:b]` **revienta** en pandas 3.0.5 con
   `OutOfBoundsDatetime: Cannot cast 2263-01-01 to unit='ns'`. Lo encontré
   escribiendo este script y está corregido en él. Quien escriba la §4.4 lo va a
   encontrar igual.
2. **La §4.4 ya está medio hecha y da tres `False`.** El walkforward publica
   `supera_bench_sharpe` en los tres tramos, contra el benchmark **sin igualar**.
   Lo que la §4.4 añadiría es igualar la exposición, no preguntar.

### A-7 — Intérprete y red → **hay intérprete; 0 de 10 fuentes de mercado**

`python3 -I fase0_n7/a7_entorno_y_red.py`, desde `fix-fase2/`:

```
=== A-7.1 interprete ===
  sys.executable : /usr/local/bin/python3
  version        : 3.13.18 (main, Oct 26 2026, 14:08:19) [Clang 23.1.3 ]
=== A-7.2 modulos ===
  numpy          OK   2.5.3
  pandas         OK   3.0.5
  scipy          NO   ModuleNotFoundError
  statsmodels    NO   ModuleNotFoundError
  yfinance       NO   ModuleNotFoundError
  statistics     OK   (stdlib)
=== A-7.3 red: solo codigo HTTP, sin descargar cuerpo ===
  Yahoo chart BTC-USD    http=000  NO
  Binance ping           http=000  NO
  Coinbase               http=000  NO
  Kraken                 http=000  NO
  Bitstamp               http=000  NO
  OKX                    http=000  NO
  Bybit                  http=000  NO
  Stooq                  http=000  NO
  FRED DGS3MO            http=000  NO
  PyPI simple            http=200  ALCANZABLE
  fuentes de MERCADO alcanzables: 0 de 10
=== A-7.4 que descargaria si se EJECUTASE (grep, no ejecucion) ===
  src/paper_runner.py:59
  src/portfolio_runner.py:212
  src/portfolio_supervivencia.py:67
  src/run_backtest.py:21
  src/walkforward_stability.py:42
  (reportados, NO parcheados)
=== A-7.5 import de portfolio_runner: ¿descarga al importarse? ===
  import OK. PERMITIR_DESCARGA = False
```

**0 de 10 fuentes de mercado, confirmando N5 y N6.** El NO-GO *"hace falta
descargar datos de mercado → PARAR"* **no se dispara**, porque nada de esta Fase 0
necesita descargar: todo sale de los CSV congelados y los **35 sidecars `.sha256`
de `data/multi` y `data/multi_muertos` están verificados, no asumidos** (ninguno
descuadra). Ningún script de esta Fase 0 ha corrido con `PERMITIR_DESCARGA`, así
que el loader parcheado por N1 habría fallado en duro antes de bajar un byte.

**Y FRED inalcanzable cierra el hilo 2 de la §4.2 por el lado práctico:** no hay
forma de traer una serie de tasas congelada ni con permiso. Combinado con la
cancelación exacta de `rf` en la construcción (a) (§2.5), ese hilo no tiene
contenido.

---

## Paso B — Ataque adversarial al planteamiento

**Seis objeciones: 1 CRÍTICA, 2 ALTAS, 2 MEDIAS, 1 RETIRADA.** Ninguna ataca que
la pregunta de la §1 sea la correcta —lo es—, ni la aritmética del expediente, que
A-2 reproduce. Lo que atacan es que la pregunta **ya tiene respuesta publicada**,
y que de las tres construcciones del brief una no es una comparación y otra está
mal escrita.

---

### B-c · La comparación que el brief dice que no existe ya está hecha, medida, publicada y auditada — **CRÍTICA**

*(Va primero porque decide la tarea, aunque la letra la ponga detrás de B-a y B-b.)*

La §1 del brief es, en negrita: *"Seis tareas de auditoría han discutido si el
Sharpe de Fase B supera el ruido estadístico. **Ninguna ha preguntado si supera a
comprar y aguantar.**"* Y la §2.8: *"Prueba que **la comparación publicada no es
comparable**, y que la que sí lo sería **no está hecha**."*

**Está hecha.** `fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py`,
con su JSON de salida al lado, en el mismo árbol que todo lo demás de esta tarea:

```
$ python3 -I -c "import json;print(open('auditoria_n1/salida_3_0d_exposicion.json').read())"
{
  "sello": "20261007",
  "dias": 4404,
  "exposicion_media": 0.1559827260735808,
  "dias_exposicion_cero": 915,
  "sharpe_fase_b": 1.0082678270225074,
  "sharpe_bh_100": 1.164272064204635,
  "sharpe_bh_igual_exposicion": 1.07121204755227,
  "gana_con_benchmark_igualado": false,
  "mascara_binaria": {
    "sharpe_estrategia": 1.1358747566407752,
    "sharpe_bh": 1.1566971275382782
  },
  "percentil_seleccion": 73.55000000000001
}
```

Su docstring describe la tarea de N7 antes de que N7 existiera, incluido el
razonamiento que el brief presenta como propio en su §2.4:

```
    1: """Paso 3.0d — benchmark de exposicion igualada sobre la equity de Fase B.
    2:    (objecion B3 de la nemesis de N2, rama nube/s2-literatura)
    ...
   14: Cuatro construcciones, porque la exposicion de Fase B es CONTINUA (no binaria
   15: como en Fase A) y no hay una sola traduccion honesta:
   16:
   17:   A) perfil de exposicion: que hay que igualar exactamente.
   18:   B) mascara binaria, la traduccion literal de Fase A: B&H solo los dias con
   19:      exposicion > 0.
   20:   C) benchmark escalado, la traduccion correcta para sizing continuo: mismo
   21:      gross que la estrategia cada dia, resto en caja.
   22:   D) test de seleccion (objecion B-09 del registro nemesis de N1): ¿el camino
   23:      de exposicion real elige dias favorables para el benchmark?
```

**Y está en los documentos de dictamen, con severidad y respuesta:**

```
$ grep -n 'H11' docs/estado-auditoria-n1.md
49:| H11 | El benchmark de Fase B **no estaba igualado en exposición**: cartera al
15,6% contra B&H al 100%. Fase A sí aplicó la corrección; Fase B la omitió (3.0d).
| ALTO | Al "pierde vs B&H": medido a igual exposición pierde por **0.063**, no por
0.156. El dictamen se sostiene, ahora por la razón correcta. |

$ grep -n '3.0d' docs/auditoria_harness_n1.md | head -4
 27:| **Fase B** … Y el "pierde vs B&H" era un veredicto no medido: a igual
     exposición el B&H gana por 0.063, no por 0.156 (3.0d).
324:## 5-bis. El número central del expediente no es robusto (3.0c y 3.0d)
413:### 3.0d — benchmark de exposición igualada sobre Fase B
```

**Y es anterior al brief:**

```
$ git log -1 --format='%h %ad %s' --date=iso -- fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py
1713e13 2026-11-01 11:17:54 +0000 N1 pasos 3.0c y 3.0d: el liston del DSR no es robusto y el benchmark no estaba igualado
$ grep -n '2026-11-01' docs/estado-auditoria-n1.md | head -2
 3:**Creado:** 2026-11-01 por la sesión N1 en la nube (Claude Code, Opus 5).
28:3.0d, que Pablo añadió el 2026-11-01 desde la némesis de N2, cambian la lectura
```

**El brief declara `2026-11-02 14:21`.** El material es del día anterior, lo añadió
Pablo, y viene de la némesis de N2. No es material perdido en un árbol ajeno: está
en `fix-fase2/`, el mismo directorio donde el brief pone sus propios scripts, y
citado en dos documentos de dictamen.

**Esto es el punto ciego de N6 repetido con el signo cambiado.** A N6 su segundo
agente le cobró (hallazgos 3 y 4) haber inventariado `results/` y **no haber
abierto `docs/`** del mismo árbol. El brief de N7 inventarió `results/`, `src/` y
`tareas/`, y **no abrió `auditoria_n1/`** del mismo árbol, que es donde estaba su
respuesta. Y el brief hereda la vara: su §2 presume *"reverificar los siete con
comandos propios. **No creerlos.**"* — pero su §1 y su §2.8 afirman una **ausencia**,
y una ausencia no se verifica con los comandos que el brief trae, que solo miran
donde él ya miró.

**Qué de la §4 sobrevive, medido fila por fila:**

| Paso de la §4 | Estado real |
|---|---|
| §4.1 (a) escalado día a día | **HECHO** en 3.0d PARTE C: `sharpe_bh_igual_exposicion = 1.07121` |
| §4.1 (b) escalado por constante `k` | **INNECESARIO**, y 3.0d ya lo demuestra imprimiendo `Sharpe(k·r)` para `k = 0.5, 1, 2`. Ver B-a |
| §4.1 (c) binario tipo Fase A | **HECHO** en 3.0d PARTE B: `1.13587` contra `1.15670` |
| §4.2 hilo 1, costes del benchmark | **NO hecho.** Lo mide A-4 de esta Fase 0 |
| §4.2 hilo 2, `rf` del efectivo | **VACÍO.** En (a) las dos series tienen el mismo efectivo: `rf` se cancela al restar (§2.5). Y FRED es inalcanzable (A-7) |
| §4.2 hilo 3, B&H puro vs EW diario | **NO hecho.** Lo mide A-5 de esta Fase 0 |
| §4.2 hilo 4, regla de entrada | **NO hecho**, y la respuesta es *no*: A-4.1 encuentra la asimetría de `:t+1` contra `:t` |
| §4.3 IC del diferencial por block bootstrap | **NO hecho. Es la única aportación genuina de la §4** |
| §4.4 por tramos | **PARCIAL.** `supera_bench_sharpe` ya está publicado, `False` en los tres, sin igualar exposición |
| Test de selección por permutaciones | **HECHO** en 3.0d PARTE D (percentil 73.55) **y el brief no lo contempla** |

**Un defecto en el material existente, para que conste con la misma vara.** 3.0d
imprime en su PARTE B: *"Matiz: con 99%+ de días con exposición>0 esta
construcción apenas corrige nada"*. Su propio JSON dice `dias_exposicion_cero:
915` de `4404`, o sea **79,2 % con exposición > 0, no 99 %+**. La conclusión
("apenas corrige nada") sigue siendo defendible por otra razón —el benchmark sigue
al 100 % en los días que conserva—, pero la cifra que la apoya está mal.

**Qué cambia del Alcance.** La §1, la §2.8 y la §4.1 hay que reescribirlas antes
de cualquier firma. **Lo que queda de la §4 es: el coste del benchmark (hilo 1),
el B&H puro (hilo 3), la regla de entrada (hilo 4), el panel de 15, y la §4.3 —el
IC del diferencial, que es lo único verdaderamente nuevo y es exactamente el
defecto que el brief le reprocha a Fase A.** Eso es trabajo real y vale la pena;
el resto es volver a correr lo que ya está corrido. Y la §4.5 tiene que citar 3.0d
y H11 como procedencia, no presentar el resultado como primicia.

---

### B-a (obligatoria) · De las tres construcciones, (b) no es una comparación, y la honesta es (a) — pero el brief la escribe mal alineada — **ALTA**

`python3 -I fase0_n7/b_a_tres_construcciones.py`, desde `fix-fase2/`, sello `20261007`.

**(1) La (b) es un no-op para el Sharpe. Demostrado, no argumentado.**

```
=== B-a.2 (b) ES UN NO-OP PARA EL SHARPE. Demostrado ===
    Sharpe(k*r_bench) con k=0.1559827260735808   = 1.1641398732
    Sharpe(k*r_bench) con k=0.5                  = 1.1641398732
    Sharpe(k*r_bench) con k=1.0                  = 1.1641398732
    Sharpe(k*r_bench) con k=2.0                  = 1.1641398732
    Sharpe(k*r_bench) con k=37.0                 = 1.1641398732
  Sharpe(r_bench) sin escalar            = 1.1641398732
  identicos a 1e-12: True
```

El Sharpe es invariante a multiplicar por una constante positiva. La construcción
(b) **devuelve exactamente el 1.164 publicado**. No es una tercera forma de
igualar: es el par que el brief denuncia como no comparable, con otra etiqueta.
Sí mueve retorno total, maxDD y Calmar, que no son invariantes a escala (386.12 %,
−25.02 %, 1.279), y por ahí tiene un uso; como comparación de Sharpe, no.

Y el brief se contradice en esto consigo mismo: su B-a dice que *"la (b), con `k`
constante, ignora que la estrategia **eligió** estar poco expuesta en los días
malos, lo que **la castiga de más**"*. **No la castiga de nada:** el Sharpe del
benchmark en (b) es el mismo que al 100 %, al bit.

**(2) La (c) corrige poco, y no por ser binaria.**

```
  (c) mask exposure[t]>0  ALINEADO  n=3489 dias (79.22 %)
    estrategia, esos dias                         319.01   1.1357    -26.81    1.245
    B&H 100 %, LOS MISMOS dias                  34484.34   1.1565    -89.49   40.312
```

La máscara conserva el **79,2 %** de los días, y en ellos el benchmark **sigue al
100 %** mientras la estrategia está al **19,7 %** de media. (c) no iguala
exposición: descarta los días de caja total y deja el resto desigualado. Es un
control de robustez útil —y da el mismo signo, −0.021— pero no es la comparación
que la tarea busca.

**(3) La (a) es la única que iguala de verdad. Y su objeción está medida.**

El brief pregunta si (a) *"le entrega al benchmark el timing de volatilidad que la
propia estrategia decidió"*. **Es una pregunta empírica y tiene respuesta:**

```
=== B-a.4 ¿contamina (a) el benchmark con el timing de vol? ===
  Sharpe (a) camino REAL        : 1.0711
  permutados: media 0.9683  sd 0.1596
  percentil del real            : 73.25 %   z = +0.644
  Sharpe del bench SIN escalar  : 1.1641
  lectura: seleccion NO significativa (z=+0.64); el leve sesgo va en contra
           de Fase B pero no se distingue del ruido
```

2000 permutaciones del propio camino de exposición (misma distribución exacta,
orden aleatorio, semilla 43). El camino real deja al benchmark en el **percentil
73,2 %**, a **+0.64 sd** de la media de sus permutaciones. Reproduce el `73.55` que
3.0d ya había publicado con otra semilla. **El sesgo que el brief teme existe, es
pequeño, y va EN CONTRA de Fase B**, no a su favor: escalar por el camino real
sube el Sharpe del benchmark frente a un camino aleatorio equivalente. Luego (a)
es la construcción **dura**, no la blanda, y la objeción del brief apunta al revés.

**(4) El brief escribe (a) con un día de retardo de más. Medido.**

```
=== B-a.0 que es exactamente exposure(t) en el codigo ===
  portfolio_runner.py:318-328, en la iteracion t:
    r_dia   = rets.iloc[t]            <- retorno del dia t
    r_p     = nansum(w_prev * r_dia)  <- w_prev son los pesos de t-1
    exposure.append(nansum(w_prev))   <- el gross QUE GANO r(t)
  autocorrelacion lag-1 de exposure: 0.979879

=== B-a.3 cuanto cuesta el desfase del brief ===
  Sharpe (a) alineado      : 1.071090
  Sharpe (a') del brief    : 1.076682
  delta por el retardo de mas: +0.005591
  dias de mascara (c) alineado: 3489   (c') del brief: 3489   difieren en 34 dias
  diferencial Fase B - (a) alineado : -0.062937
  diferencial Fase B - (a') brief   : -0.068528
  el desfase mueve el diferencial en -0.005591  -> EN CONTRA de Fase B
```

`exposure[t]` **ya está retardado**: es `Σ w_prev`, el gross que ganó `r(t)`.
Alinearlo con `r_bench(t)` exige `exposure[t]`. El brief escribe
`r_bench_a(t) = exposure(t−1) · r_bench(t)` en la §4.1(a) y
`exposure(t−1) > 0` en la §4.1(c): **duplica el retardo** en las dos. Cuesta
**+0.0056** de Sharpe al benchmark y **34 días** de máscara, los dos **en contra**
de Fase B. Con la autocorrelación a 0.98 el error es pequeño, pero es un error, y
va en la dirección de la tesis del autor.

**Respuesta a lo que B-a pregunta.** La comparación honesta es **(a), alineada
con `exposure[t]`, leída junto al percentil de selección**, que es exactamente lo
que 3.0d ya hace. **No** es "ninguna sola, hay que leer las tres juntas" en pie de
igualdad, porque **(b) no es una comparación**: incluirla como tercera columna de
Sharpe sería publicar el número que la tarea existe para corregir. (c) entra como
control de robustez, y (b) solo en las columnas de retorno y Calmar, con la
invariancia declarada al lado.

**¿Dispara el NO-GO?** El NO-GO dice: *"B-a concluye que ninguna de las tres
construcciones es honesta → PARAR y proponer la cuarta"*. **No se dispara:** una
de las tres sí es honesta —(a), alineada—, y la cuarta que haría falta ya existe y
es la PARTE D de 3.0d. Lo digo sin graduar: la conclusión es que (a) es honesta,
luego la condición del NO-GO es falsa y el freno no se acciona.

**Qué cambia del Alcance.** §4.1 tiene que (i) corregir `exposure(t−1)` a
`exposure(t)` en (a) y en (c), (ii) sacar (b) de las columnas de Sharpe o marcarla
como idéntica al par publicado, y (iii) incorporar el test de permutaciones, que
no está en el brief y sin el cual la lectura de (a) no se puede defender.

---

### B-b (obligatoria) · Busqué la construcción favorable a Fase B. De diez medidas, gana en una, y esa una no está igualada — **MEDIA**

`python3 -I fase0_n7/b_b_favorable_a_fase_b.py`, desde `fix-fase2/`.

El brief lo pide bien y con el motivo correcto: *"este lo escribió alguien que ya
dijo en voz alta que cree que Fase B pierde. **Esa predisposición es un hecho del
expediente: trátala como sesgo del autor.**"* Tratada. Candidatas del brief: el
panel de 15 y el drawdown. **Tercera de cosecha propia: el B&H de BTC solo**, que
es el benchmark que usó Fase A (`rigor_estadistico.py:188`, `data["bh"]`) y es lo
que "comprar y aguantar" significa para quien no construye una cesta
igual-ponderada rebalanceada a diario. Más dos variantes del benchmark que lo
debilitan: cobrarle su coste real y quitarle el rebalanceo diario.

**Todas sobre la construcción (a) ALINEADA, que B-a establece como la honesta.**

```
=== B-b.1 panel de 10, sello 20261007 ===
  Fase B (neto de costes): Sharpe 1.0082  Calmar 0.978  maxDD -26.90 %

  benchmark igualado a exposure[t]                   Sharpe       dif   Calmar   maxDD %  ¿gana FaseB?
  EW diario, sin coste (el del expediente)           1.0711   -0.0629    1.144    -27.07         False
  EW diario, CON su coste real de rebalanceo         1.0610   -0.0528    1.118    -27.14         False
  B&H PURO (sin rebalanceo diario)                   1.0392   -0.0310    1.050    -27.18         False

=== B-b.2 candidata (5) propia: B&H de BTC SOLO ===
  BTC B&H, 100 %                                     0.9860   +0.0221   17.999    -83.40          True
  BTC B&H igualado a exposure[t]                     1.0481   -0.0399    0.998    -21.45         False

=== B-b.4 candidata (1) del brief: el panel de 15, sello 20261009 ===
  Fase B panel 15: Sharpe 0.9155  exposicion media 0.157118  dias 4406
  EW 100 % (el publicado del panel 15)               1.0679   -0.1524   50.224    -90.58         False
  EW igualado a exposure[t]                          0.9507   -0.0352    0.869    -28.56         False
  EW igualado + coste real                           0.9396   -0.0241    0.847    -28.62         False
  B&H PURO igualado a exposure[t]                    0.9177   -0.0022    0.815    -28.29         False

=== B-b.5 veredicto de B-b ===
  construcciones medidas: 10
  construcciones en que Fase B GANA: 1
    - BTC B&H, 100 %: diferencial +0.0221
```

**Resultado, con la predisposición del autor controlada: Fase B gana en una de
diez, y la única en que gana es la única que NO está igualada en exposición** —el
BTC B&H al 100 %, que es el defecto que la tarea existe para corregir. En cuanto
se iguala, BTC pasa a ganar por 0.040.

**La más favorable de las honestas es la que el brief predijo, y es un empate
técnico:** panel de 15 + B&H puro + igual exposición da **−0.0022** de Sharpe.
Dos milésimas. Eso no es "Fase B pierde": es **indistinguible de cero**, y es
exactamente la situación para la que sirve el IC de la §4.3. La escalera de
candidatas va de −0.0629 (la del expediente) a −0.0022 (la más benigna), y **las
tres correcciones que debilitan al benchmark suman en la misma dirección**:
cobrarle el coste (+0.010), quitarle el rebalanceo diario (+0.032), y meter los
cinco muertos (+0.028 adicional en el panel de 15). Juntas se comen los 0.063.

**Eso es la corrección contraria que el brief pide, existe, y es lo bastante
grande como para llevar el diferencial a cero. No para darle la vuelta.**

**Y la candidata (2) del brief sale al revés de como él la presenta:**

```
=== B-b.3 candidata (2) del brief: el drawdown y el Calmar ===
  maxDD Fase B -26.90 % vs (a) EW igualado -27.07 %  -> Fase B GANA
  maxDD Fase B -26.90 % vs bench PUBLICADO al 100 % -88.96 %  -> Fase B GANA por +62.06 pp
  Calmar Fase B 0.978 vs (a) EW igualado 1.144  -> Fase B pierde
```

El `−26.9` contra `−88.96` que la §2.1 llama *"el contrapeso, que es real y hay
que conservar"* **es un artefacto de la misma asimetría de exposición que la tarea
denuncia**. A igual exposición el benchmark escalado tiene `−27.07 %`: Fase B gana
por **17 puntos básicos**, no por 62 puntos porcentuales. Y en Calmar pierde. El
único argumento que el brief ofrece a favor de Fase B **se evapora al aplicarle la
corrección del propio brief**, y eso hay que decirlo con esa letra porque va en
contra de la tesis que me conviene como objeción: **el sesgo del autor no infló su
lado, infló el lado contrario y lo dejó sin ver.**

**Qué cambia del Alcance.** §4.1 tiene que tabular las filas que debilitan al
benchmark —coste, B&H puro, panel de 15— porque son las que mueven el diferencial
de −0.063 a −0.002, y sin ellas el informe solo encuentra pruebas en un sentido.
Y la §2.1 tiene que retirar el drawdown como contrapeso, o declararlo medido a
igual exposición.

---

### B-d · `Sharpe(d)` y `Sharpe(est) − Sharpe(bench)` son dos cantidades distintas, y la §4.3 las confunde — **ALTA**

`python3 -I fase0_n7/b_def_diferencial_ceros_ppy.py`, desde `fix-fase2/`:

```
=== B-d el Sharpe del diferencial no es la diferencia de Sharpes ===
  Sharpe(estrategia)            = 1.008268
  Sharpe((a) bench igualado)    = 1.071090
  Sharpe(estrategia) - Sharpe(a)= -0.062821   <- la lectura de B-a
  Sharpe(d), d = r_est - r_a    = -0.354465   <- la lectura de la §4.3
  LAS DOS CIFRAS NO SON LA MISMA. Difieren en -0.291644
  correlacion entre las dos series: rho = 0.733060
  sd diaria: estrategia 0.009761  (a) 0.009018  diferencial 0.006651
  el diferencial tiene 0.681x la sd de la estrategia
  media anualizada de d: -1.0801 %/ano
  signo: Sharpe(d) < 0  y  Sharpe(est)-Sharpe(a) < 0  -> COINCIDEN
```

La §4.3 pide *"la serie diferencial `d(t)`, su media anualizada, su Sharpe, y el
IC al 95 %"*, y la §4.1 pide en la misma tabla *"Sharpe anualizado"* de cada
construcción. **Son dos cantidades con dos escalas distintas y la tabla las va a
poner juntas.** Aquí: `−0.063` por un lado, `−0.354` por el otro. Un factor 5,6.

La razón es que las dos series comparten los mismos diez activos: `rho = 0.733`,
y al restar se cancela el factor común, así que `d(t)` tiene `0.68×` la desviación
de la estrategia pero una media mucho más pequeña en términos absolutos. **Eso
hace a `Sharpe(d)` más informativo, no menos** —mide la ventaja de ponderación con
el beta de mercado neutralizado— pero es otra cantidad, con otro umbral y otra
interpretación. Los dos signos coinciden aquí, lo cual es suerte y no teorema: la
diferencia de Sharpes y el Sharpe de la diferencia **pueden tener signos
opuestos** cuando las volatilidades difieren.

**En esta tarea la §4.3 es la buena, y es más dura para Fase B que la lectura de
B-a:** `−0.354` de Sharpe en el diferencial, `−1.08 %/año` de media. Pero el
informe no puede poner `−0.063` y `−0.354` en la misma tabla sin decir que son dos
cosas, porque un lector —o Pablo— va a leer la pequeña y creer que es la grande, o
al revés.

**Qué cambia del Alcance.** La §4.1 y la §4.3 tienen que separar explícitamente
las dos columnas y nombrarlas por lo que son: *"diferencia de Sharpes"* y
*"Sharpe de la serie diferencial"*. Y la §4.5, que son tres líneas, tiene que
decir **cuál de las dos** es la que dice lo que dice.

---

### B-e · Los 915 días con `exposure = 0` no comparan nada, y su efecto va a favor de Fase B — **MEDIA (bajada de ALTA: mi objeción tenía el signo al revés)**

```
=== B-e los dias con exposure = 0 ===
  dias con exposure=0 : 915 de 4404  (20.78 %)
  en esos dias:  r_bench_igualado = exposure*r_bench = 0 SIEMPRE
                 r_estrategia     = r_p - coste = 0 - coste
  suma de costes en dias de exposure=0 : 0.003576  (0.3576 %)
  dias de exposure=0 con coste > 0     : 17
  r_p en dias de exposure=0: max|r_p| = 0.000e+00  (debe ser 0)
  d<0 por construccion en 17 de 915 dias de exposure=0
  Sharpe(d) con TODOS los dias        : -0.354465
  Sharpe(d) SOLO dias con exposure>0  : -0.387331
  los 915 ceros mueven el Sharpe(d) en +0.032866
```

**Planteé esta objeción esperando que los ceros fueran un diferencial negativo
garantizado que castigase a Fase B. Medido, es lo contrario y hay que decirlo.**
Solo **17 de 915** días a cero llevan coste; en los otros **898**, `d(t)` es
**exactamente 0**. Y el efecto neto de los ceros **favorece a Fase B**: suben el
`Sharpe(d)` en **+0.0329**, porque diluyen una media negativa con ceros. La
objeción baja a MEDIA y queda con la dirección corregida.

**Lo que sí sobrevive, y es real:** la §4.3 define `d(t)` sobre 4403 días sin
decir que en **898 de ellos vale 0 por construcción**. Un IC de block bootstrap
sobre una serie con el 20 % de ceros exactos no tiene la misma lectura que uno
sobre 4403 comparaciones efectivas. **El `n` efectivo de comparación es 3489, no
4404**, y el brief no lo menciona en ninguna de sus nueve casillas de checklist
("cada tabla con su unidad y su `n`").

---

### B-f.1 · `PPY = 365` para cripto — **RETIRADA. La objeción era mía, no del expediente**

```
=== B-f.1 PPY = 365 para cripto: ¿correcto? ===
  rango 2014-09-17 -> 2026-10-07 = 4404 dias naturales
  filas en la serie                      = 4404
  huecos de calendario                   = 0
  dias por ano implicitos                = 365.33
```

El brief la sugiere como posible objeción. **No lo es, por dos razones
independientes.** Cripto cotiza los 365 días y la serie no tiene **ni un hueco de
calendario** en doce años, así que `PPY = 365` es la cifra correcta. Y además es
**irrelevante para el veredicto**: `√365` escala por igual las dos series, luego
no cambia el signo de ningún diferencial. **Retirada por escrito, y era del
revisor.**

### B-f.2 · La §4.2 es una tabla de 96 filas, y eso es un menú aunque estén todas — **MEDIA**

```
=== B-f.2 el contador de construcciones de metrica ===
  esta Fase 0 ha medido 10 construcciones de benchmark
  La §4.2 del brief multiplica cada fila de la §4.1 por 2^4 hilos:
    2 paneles x 3 construcciones x 2 costes x 2 rf x 2 rebalanceo
    x 2 regla de entrada = 96 filas.
```

El brief se defiende por adelantado: *"No es un menú del que elegir: es una tabla
con todas las filas. (N6 · B-d llamó a eso 'una máquina de metric-shopping'
cuando se deja a elección.)"* **La defensa no funciona.** Una tabla de 96 filas
cuyo rango medido va de −0.063 a −0.002 es un menú **con todas las entradas
visibles**, que es la versión educada del mismo problema: quien lee elige la fila,
y el brief no fija de antemano **cuál decide**. N6 · B-d ya estableció que
"ofrecer las dos filas después de conocer el resultado es el menú; que lo elija
Pablo y no el agente no lo convierte en otra cosa".

Y hay dos hilos que no deberían generar filas porque no tienen contenido: el hilo
2 (`rf`) **se cancela exactamente** en (a) y FRED es inalcanzable; el hilo 4
(regla de entrada) mueve **10 celdas de 44 040**. Quitándolos, la tabla baja a 24
filas, que es manejable y honesto.

**Qué cambia del Alcance.** La §4.1/§4.2 tienen que fijar **antes de correr** cuál
es la fila que decide —la (a) alineada, panel de 10, con el coste del benchmark
cobrado, es mi propuesta— y presentar las demás como sensibilidad alrededor de
ella, no como alternativas de igual rango. Y hay que llevar el contador de
construcciones de métrica que N6 abrió: iba por **5**, y esta Fase 0 le añade
**10**.

---

### Lo que NO se encontró, declarado

- **Ningún error aritmético en el expediente.** Los veinte campos de
  `portfolio_bateria.json`, el Sharpe 1.008, el 1.164, el retorno 317.52, el
  132831.04, los dos drawdowns y `exposicion_media` reproducen todos con
  implementación propia, el último con diferencia **0.0e+00**. Y el
  `sharpe_bh_igual_exposicion = 1.07121` de 3.0d reproduce desde cero (1.071090 con
  ddof=1, 1.071212 con ddof=0, que es la convención de 3.0d).
- **Ninguna manipulación.** Las asimetrías de 2.2 están en el código, declaradas
  en comentarios, y su magnitud es la que es: −0.011 de Sharpe por el coste,
  −0.057 por el rebalanceo, 10 celdas por la regla de entrada.
- **Ninguna descarga.** 0 de 10 fuentes de mercado, `PERMITIR_DESCARGA` sin poner
  en los once scripts, y los 35 sidecars `.sha256` verificados.
- **Ningún fichero existente tocado.** `git diff --stat` vacío;
  `git status --short` solo `?? fix-fase2/fase0_n7/`. Nada en `auditoria_n7/`,
  nada en `src/`, nada en `results/`, nada en `data/`, nada en la raíz.
- **Ninguna objeción a la pregunta de la §1.** *"¿Con la misma exposición y los
  mismos costes, le gana Fase B a comprar y aguantar?"* sigue siendo la pregunta
  correcta y sigue siendo anterior y más barata que el debate del DSR. Lo que no
  sobrevive es que esté sin contestar.
- **Nada que invalide el trabajo de N6.** Su `N* = 4.0786` y su conclusión de
  indecidibilidad no se tocan: esta tarea es ortogonal, como el brief dice.

---

## Veredicto de la Fase 0 y estado de los seis NO-GO

**Los seis son binarios. Ninguno se gradúa, ninguno se mueve de la tarea a un
paso, ninguno se declara "parcialmente disparado".**

| NO-GO de la §3 | Estado |
|---|---|
| *No hay intérprete con numpy/pandas → PARAR* | **NO se dispara.** Python 3.13.18, numpy 2.5.3, pandas 3.0.5 (A-7) |
| *A-2 no reproduce `1.008` y `1.164` al tercer decimal → PARAR* | **NO se dispara.** 1.008268 → 1.008 y 1.164273 → 1.164 (A-2) |
| *A-3 no reproduce `exposicion_media` al bit → PARAR: (a) y (b) no tienen base* | **SE DISPARA.** Con el sello `20261009` que el brief manda da `0.15591192138630272`, no `0.1559827260735808`. Diferencia −7.08e-05 (A-3) |
| *Algún hecho de la §2 sale REFUTADO → PARAR* | **NO se dispara.** 6 CONFIRMADOS y 2 CONFIRMADOS con corrección. Lo REFUTADO es la **§1**, que no es la §2 |
| *B-a concluye que ninguna de las tres construcciones es honesta → PARAR y proponer la cuarta* | **NO se dispara.** (a), alineada con `exposure[t]`, es honesta y su sesgo de selección está medido (percentil 73,2 %, z +0.64, en contra de Fase B) |
| *Hace falta descargar datos de mercado → PARAR* | **NO se dispara.** Nada se descargó; 0 de 10 fuentes y 35 sidecars verificados (A-7) |

**Un NO-GO disparado: el de A-3.** Y su consecuencia escrita en el propio brief es
*"(a) y (b) no tienen base"* **tal como la §4.1 las define**, porque la §4.1 pide
el sello `20261009` y la `k` del `20261007`, y el panel de 15 solo existe con
`20261009`. El dato subyacente **sí** es reproducible al bit; lo que no es
coherente es el par (sello, constante) que el brief escribió. Es un defecto del
brief, reparable en una línea, y hay que repararlo antes de la firma.

**Lo que esta Fase 0 deja establecido, sin gastar el Alcance:**

1. **La pregunta de la tarea ya tiene respuesta publicada y auditada, del
   2026-11-01:** a igual exposición Fase B pierde por **0.063** de Sharpe
   (1.0083 contra 1.0711), no por 0.156. Está en
   `auditoria_n1/salida_3_0d_exposicion.json`, en `docs/estado-auditoria-n1.md`
   como **H11 (ALTO)** y en `docs/auditoria_harness_n1.md` como **3.0d** y
   **5-bis**. Reproducido aquí desde cero.
2. **De las tres construcciones de la §4.1, (b) no es una comparación:** es
   idéntica a 1e-12 al 1.164 publicado, porque el Sharpe es invariante a escala.
   La honesta es **(a)**, y el brief la escribe con un día de retardo de más, que
   cuesta +0.0056 de Sharpe al benchmark, en contra de Fase B.
3. **El sesgo que el brief teme en (a) existe, está medido y va en contra de
   Fase B:** percentil 73,2 % contra 2000 permutaciones del propio camino de
   exposición, z = +0.64, no significativo. (a) es la construcción dura.
4. **Buscada activamente la construcción favorable a Fase B: de diez medidas gana
   en una, y esa una no está igualada en exposición.** La más benigna de las
   honestas —panel de 15 + B&H puro + igual exposición— da **−0.0022**, que es un
   empate técnico. Las tres correcciones que debilitan al benchmark (coste
   +0.010, sin rebalanceo diario +0.032, panel de 15 +0.028) **se comen los
   0.063 y dejan el diferencial en cero, no lo invierten.**
5. **El contrapeso del drawdown que la §2.1 declara "real y hay que conservar" se
   evapora a igual exposición:** −26.90 % contra −27.07 %, no contra −88.96 %. Y
   en Calmar Fase B pierde (0.978 contra 1.144). El sesgo del autor no infló su
   propio lado: dejó sin ver el lado contrario.
6. **La fórmula de turnover del brief mide cero** (4 días de 4404). El turnover
   real del rebalanceo diario del benchmark es **0.855 %/año**, **−9.70 %** del
   valor final y **−0.0110** de Sharpe: material en retorno, anecdótica en Sharpe.
7. **El igual-ponderado no es buy & hold, y el filo está en el umbral que el
   brief mismo fijó:** 0.571× de retorno final (material), **4,85 %** relativo en
   Sharpe, justo por debajo del 5 % que el brief declara cosmético.
8. **Dos hilos de la §4.2 no tienen contenido.** El `rf` del efectivo **se cancela
   exactamente** en (a) porque las dos series tienen la misma exposición y por
   tanto el mismo efectivo; y FRED es inalcanzable. La regla de entrada mueve
   **10 celdas de 44 040** — y la respuesta al hilo 4 es *no*, el benchmark admite
   cada activo un día antes usando el retorno del día que va a cobrar.
9. **`Sharpe(d)` no es `Sharpe(est) − Sharpe(bench)`:** −0.354 contra −0.063, un
   factor 5,6, con `rho = 0.733` entre las dos series. La §4.3 es la lectura
   correcta y es **más dura** para Fase B; la §4.1 va a poner las dos cifras en la
   misma tabla y hay que separarlas.
10. **El `n` efectivo de comparación es 3489, no 4404:** en 898 días `d(t)` vale
    cero exacto, y esos ceros suben el `Sharpe(d)` en +0.033 **a favor** de Fase B.

**Lo que hace falta antes de cualquier OK:**

- **Reescribir la §1 y la §2.8**, que afirman una ausencia que no existe, y **citar
  3.0d y H11** como procedencia (B-c).
- **Arreglar el par (sello, constante) de A-3 y de la §4.1**: o `20261007` con
  `k = 0.1559827260735808`, o `20261009` con `k = 0.15591192138630272`. No las dos
  mitades cruzadas. Y declarar que el panel de 15 solo existe con `20261009`.
- **Corregir `exposure(t−1)` a `exposure(t)`** en la §4.1 (a) y (c).
- **Sacar (b) de las columnas de Sharpe**, o marcarla como idéntica al par
  publicado.
- **Añadir el test de permutaciones** a la §4.1, que no está y sin el cual (a) no
  se puede defender.
- **Borrar los hilos 2 y 4 de la §4.2** o reducirlos a una línea de constancia, y
  **fijar antes de correr cuál es la fila que decide** (B-f.2).
- **Separar en la §4.1/§4.3** la diferencia de Sharpes del Sharpe del diferencial,
  y dar el `n` efectivo de 3489 (B-d, B-e).
- **Reescribir la §2.1** retirando el drawdown como contrapeso o midiéndolo a igual
  exposición (B-b.3).
- **Corregir la fórmula de turnover de A-4** en cualquier reescritura del brief.

**Con eso, lo que queda del Alcance es:** el coste del benchmark (hilo 1), el B&H
puro (hilo 3), el panel de 15, y **la §4.3 — el IC del diferencial por block
bootstrap**, que es la única aportación genuina y es exactamente el defecto que el
brief le reprocha a Fase A. **Y el resultado que ese IC va a tener que decidir ya
está acotado por esta Fase 0: el diferencial va de −0.063 a −0.002 según la
construcción, con `Sharpe(d) = −0.354`. Si el IC cruza cero, la lectura es "sin
ventaja demostrable en ninguna dirección", que es un resultado y no un fracaso —
igual que dice el brief.**

**No se ha ejecutado ni un paso de la §4. La §7 sigue sin firma.**
