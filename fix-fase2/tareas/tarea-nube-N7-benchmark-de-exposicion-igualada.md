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
