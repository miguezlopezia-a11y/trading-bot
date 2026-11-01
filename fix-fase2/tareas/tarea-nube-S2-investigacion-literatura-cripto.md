# Tarea S2 (sesión en la nube) — Investigación: qué vías tienen evidencia publicada

**Estado:** CREADA 2026-10-29 por Sonnet (Claude Code, Windows). Sin ejecutar.
**Ejecutor:** sesión en la nube de Claude Code. Trabajo de búsqueda y lectura.
**Repo:** `miguezlopezia-a11y/bunker-2026`, rama `nube/s2-literatura`.
**Alcance físico:** solo escribe en `shared/trading-bot-fase1/fix-fase2/docs/`.
No toca código ni datos.
**Duración estimada:** [estimado] 2-4 h de sesión.

---

## 1. El problema que esta tarea tiene que resolver

El expediente está bloqueado en un punto **cuantificado**, no vago
(`fix-fase2/docs/fase_b_reevaluacion_resultado.md`, Paquete 2):

| N trials | Sharpe anual mínimo para DSR ≥ 0.95 |
|---|---|
| 1 | 0.472 |
| 5 | 1.073 |
| **12 (actual)** | **1.312** |
| 50 | 1.622 |
| 100 | 1.751 |

Sharpe observado de la Fase B: **1.008**. Brecha: **+0.304**.

De ahí salen las tres únicas palancas reales, y conviene tenerlas delante
antes de proponer nada:

1. **Subir T** (más observaciones efectivas) → baja el Sharpe exigido.
2. **No subir N** → cada variante nueva que se pruebe sube el umbral para
   todas. Probar 38 ideas más llevaría el listón de 1.31 a ~1.62.
3. **Encontrar una fuente de retorno con Sharpe genuinamente mayor**.

La consecuencia incómoda, y que esta tarea debe asumir como premisa: **la
estrategia de "probar muchas ideas a ver cuál sale" está matemáticamente
condenada en este expediente.** Cada intento encarece el siguiente. Solo
vale traer hipótesis con respaldo externo previo, porque una hipótesis
justificada por literatura independiente no es una búsqueda a ciegas sobre
los mismos datos.

**Esta tarea no prueba nada ni toca datos. Entrega una lista corta de
candidatas defendibles, con su coste estadístico calculado.**

---

## 2. Fase 0 — Revisión némesis (OBLIGATORIA, antes de tocar nada de "Alcance")

### Paso A — Verificación de hechos

Con comandos reales y salida pegada. No aceptar ninguna cifra de este
documento sin comprobarla en la fuente del repo:

- [ ] Leer entero `fix-fase2/docs/fase_b_reevaluacion_resultado.md` y
      confirmar la tabla de potencia de §1 (N, SR₀, Sharpe mínimo) y el
      Sharpe observado 1.008.
- [ ] Leer entero `fix-fase2/docs/rigor_estadistico_resultado.md` y
      `fix-fase2/docs/portfolio_resultado.md`. Anotar qué estrategia concreta
      es la de Fase B (regla, parámetros, sizing, σ_target) — el resto de la
      tarea depende de describirla bien.
- [ ] Leer `fix-fase2/docs/timesfm_fase2_resultado.md`: qué se descartó
      exactamente y con qué evidencia, para no reproponerlo.
- [ ] Confirmar que `fix-fase2/src/potencia_fase_b.py` existe y se ejecuta.
      Es la herramienta con la que se calcula el §3.4 de esta tarea.
- [ ] Verificar las 4 citas que el expediente ya da por buenas
      (`tarea-trading-bot-rigor-estadistico.md`): Bailey & López de Prado
      2014; White 2000; Bailey/Borwein/López de Prado/Zhu 2017;
      Harvey/Liu/Zhu 2016. Si alguna no existe tal como está citada, es
      hallazgo CRÍTICO: el método entero se apoya en ellas.

### Paso B — Ataque adversarial al planteamiento de ESTA tarea

- ¿Cuál es la asunción más débil? (candidata honesta: que la literatura
  académica sobre anomalías de cripto es aprovechable por un operador
  retail — la mayoría de esos papers no descuentan comisiones realistas, ni
  slippage, ni el coste de financiación de los perpetuos, y varios están
  medidos sobre 2014-2018, un régimen que no vuelve).
- ¿Qué alternativa se descartó sin justificar? (candidata: aceptar que no
  hay edge accesible y reorientar el proyecto a control de riesgo, que es
  justamente lo que el dictamen de Fase B dice que sí funciona —
  "el valor es control de riesgo, no retorno ajustado"). Esa alternativa
  tiene que aparecer evaluada en el entregable, no omitida.
- ¿Por qué buscar literatura no es simplemente otra forma de inflar N, con
  el buscador haciendo de optimizador? Responder de verdad: si la respuesta
  honesta es que sí lo es, decirlo y proponer cómo acotarlo.
- Si no encuentras objeción real, **di por qué no la encontraste**.

### Salida de la Fase 0

`## Registro de revisión némesis — S2` al final de este archivo, con ambos
pasos, y **PARAR**. Commit + push de la rama. La §3 no se ejecuta hasta el
OK escrito de Pablo en §7.

---

## 3. Alcance (NO ejecutar hasta OK escrito de Pablo)

### 3.1 Qué dice la literatura sobre lo que YA se hizo

Antes de buscar vías nuevas, situar el resultado propio. La Fase B es
time-series momentum con volatility targeting sobre un portfolio cripto, y
obtiene Sharpe 1.01 frente a 1.16 del buy-and-hold igual-ponderado.

Buscar y contrastar:

- La literatura original de TSMOM y su réplica crítica posterior. ¿Es
  conocido que TSMOM con vol-targeting reduzca drawdown sin batir al
  benchmark en Sharpe? Si es el resultado **esperado** según la literatura,
  entonces la Fase B no es una señal débil: es una reproducción correcta de
  un fenómeno ya documentado, y eso cambia qué significa el DSR 0.72.
- Qué dice la literatura sobre vol-targeting específicamente: ¿mejora el
  Sharpe o solo la forma de la distribución? Hay trabajo publicado en ambos
  sentidos; traer los dos lados.
- Evidencia sobre si el momentum en cripto sobrevive fuera del período
  2017-2021.

### 3.2 Vías candidatas con evidencia publicada

Buscar fuentes de retorno en cripto con evidencia **fuera de muestra** y
**con costes**, no solo backtests publicados. Líneas a cubrir como mínimo —
la lista no es exhaustiva y se agradece lo que aparezca fuera de ella:

- Momentum **cross-sectional** (ordenar activos entre sí) frente al
  time-series que ya se probó. Son fenómenos distintos y la evidencia no es
  la misma.
- Factores de riesgo específicos de cripto (tamaño, momentum, y los que la
  literatura haya establecido).
- **Carry / funding rate / basis** en futuros perpetuos: es una fuente de
  retorno estructural, medible, con mecanismo económico identificable, y no
  depende de predecir el precio. Evaluar con atención: es la familia que
  mejor encaja con un expediente que ya demostró no poder predecir dirección.
- Señales on-chain, si hay evidencia OOS seria.
- Cualquier anomalía con mecanismo económico explicable. Una regla sin
  mecanismo es una regla que no se sabe por qué funcionaría.

**Para cada candidata, una fila con:**

| Campo | Exigencia |
|---|---|
| Hipótesis | En una frase falsable |
| Mecanismo económico | Por qué debería existir ese retorno. "El backtest sale bien" no es un mecanismo |
| Cita | Autores, año, revista, identificador. **Verificada con búsqueda real**, nunca de memoria |
| Período y mercado del estudio | Y si incluye post-2022 |
| ¿Descuenta costes? | Sí/no, y cuáles |
| Datos que haría falta | Fuente concreta, frecuencia, disponibilidad gratuita |
| Coste de probarla | Esfuerzo y cómputo [estimado] |
| **Coste estadístico** | Ver §3.4 |

### 3.3 Criterio de descarte explícito

Una candidata se descarta, y se dice por qué, si:

- la evidencia es solo in-sample o solo del período 2014-2018;
- no sobrevive a costes realistas en el propio paper;
- requiere datos que no se pueden conseguir gratis y reproducibles;
- requiere infraestructura de ejecución que este proyecto no tiene
  (latencia baja, colocación, acceso a book);
- o su mecanismo es indistinguible de "el mercado subió".

Un descarte bien argumentado vale tanto como una candidata. Lo que no vale
es una lista larga sin filtro.

### 3.4 El coste estadístico de cada candidata (obligatorio)

Esta es la parte que convierte la investigación en algo accionable y la que
no se puede saltar.

Con `fix-fase2/src/potencia_fase_b.py`, calcular y tabular el Sharpe anual
mínimo exigido para DSR ≥ 0.95 con N = 13, 14, 15, 20 y 30, manteniendo el
resto de parámetros del expediente (T_eff, skew, curtosis declarados en
`fase_b_reevaluacion_resultado.md`).

Después, para cada candidata: **"probar esto sube N de 12 a 13, lo que eleva
el listón de 1.312 a X — ¿es creíble, según su propia literatura, que esta
vía dé un Sharpe ≥ X con costes?"** Si la respuesta es no, la candidata se
descarta por aritmética, por muy elegante que sea.

Si alguna vía permite subir T de forma sustancial (datos de mayor
frecuencia, más años, más activos), calcular también cuánto **baja** el
umbral, porque esa es la única palanca que juega a favor.

### 3.5 Recomendación final

Terminar con una recomendación de **una sola** vía, o con la recomendación
explícita de no seguir ninguna. Con su justificación y, si procede, con un
pre-registro borrador listo para que Pablo lo apruebe: hipótesis, datos,
regla exacta, métrica decisiva fijada **antes** de ver resultados, y umbral
de muerte.

Si la conclusión honesta es "ninguna candidata supera el listón aritmético",
**esa es la entrega**, y es una entrega válida. No rellenar con alternativas
flojas para que el documento parezca productivo.

### 3.6 Lo que NO entra

- No ejecutar backtests. No tocar datos. No escribir código de estrategia.
- No cambiar ninguna métrica ni umbral existente.
- No proponer nada que exija dinero real, broker o API con credenciales.

---

## 4. Restricciones NO-GO (bloqueantes)

- **NO-GO** — Ninguna cita sin verificar con búsqueda real. Inventar una
  referencia, o citar de memoria sin comprobar, invalida la tarea entera.
  El estándar del proyecto ya es ese: las 4 citas de la Fase B se
  verificaron una por una.
- **NO-GO** — Ningún paper de pago descargado por vías irregulares. Si solo
  hay abstract, se dice que solo se leyó el abstract.
- **NO-GO** — No confundir blog, vendedor de curso o hilo de foro con
  evidencia. Pueden citarse como contexto, marcados como tales y nunca como
  respaldo de una candidata.
- **NO-GO** — No mergear a `main`. PR y nada más.
- **NO-GO** — No ejecutar §3 sin OK escrito de Pablo en §7.

---

## 5. Definition of Done

- [ ] `## Registro de revisión némesis — S2` con los pasos A y B.
- [ ] `fix-fase2/docs/investigacion_vias_s2.md` con: situación de la Fase B
      en la literatura (§3.1), tabla de candidatas (§3.2), descartes
      razonados (§3.3), tabla de umbrales por N (§3.4) y recomendación única
      (§3.5).
- [ ] Toda cita con su verificación anotada: qué se buscó, qué devolvió,
      si se leyó el texto completo o solo el abstract.
- [ ] Recomendación final explícita, incluida la posibilidad de "ninguna".
- [ ] PR abierto contra `main`, sin mergear.

---

## 6. Decisiones bajo presión

- Si una búsqueda no da resultados tras **tres** reformulaciones distintas,
  anotarlo como "sin evidencia encontrada" y seguir. No insistir
  indefinidamente ni rebajar el criterio de calidad para llenar la tabla.
- Si una candidata parece excelente pero su paper no es accesible: marcarla
  como **pendiente de lectura completa**, nunca como verificada.
- Si aparece evidencia que **contradice** un resultado ya cerrado del
  expediente (por ejemplo, que TimesFM sí funciona en otro marco):
  documentarla con la cita y señalar el conflicto. No reabrir el expediente
  por cuenta propia; eso lo decide Pablo.

---

## 7. OK de Pablo

> Pendiente. Sin texto aquí, la §3 no se ejecuta.

---

## 8. Sincronía entre documentos

Si la recomendación de §3.5 cambia la dirección del proyecto, se refleja en
`shared/estado-y-siguiente-paso.md` además de en el informe. El ancla es lo
que lee el siguiente agente.

---

## Registro de revisión némesis — S2

**Ejecutor:** sesión en la nube (Claude Code), rama `nube/s2-literatura`
(cortada de `fase-b-recuperada` @ `adad9e7`). **Fecha:** 2026-11-01.
**Entorno:** contenedor efímero, `python3` 3.13 + numpy 2.5.3, `scipy` 1.18.1
instalado en la sesión (no estaba). No existe `/opt/trading-bot/venv` que
citan los docstrings: se ejecutó con `python3` del sistema.
**Alcance ejecutado:** solo §2. §3 NO ejecutada (sin OK de Pablo en §7).

---

### Paso A — Verificación de hechos

Cada afirmación con su comando y su salida literal. Veredictos: **OK**
(confirmado), **DISCREPA** (la fuente dice otra cosa), **NO EXISTE** (la
fuente que el brief manda leer no está en el repo), **NO LO SÉ**.

---

#### A1. Tabla de potencia de §1 y Sharpe observado 1.008 — **OK**

`fix-fase2/src/potencia_fase_b.py` existe, se ejecuta y reproduce la tabla
exacta del brief y del expediente:

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
```

Reproducibilidad bit a bit: tras reescribir el JSON, el árbol de git queda
limpio — la salida es idéntica a la commiteada.

```
$ git status --short && git diff --stat
(sin salida)
```

Verificación sintética del módulo, también OK:

```
$ cd fix-fase2 && python3 verificar_potencia_sintetico.py
umbral DSR(N=12) = Sharpe anual 1.312
curva en 1.574 -> DSR 0.9521 (esperado >=0.95)
curva en 1.049 -> DSR 0.6767 (esperado <0.95)
curva en 1.574 -> t 4.57 (esperado >3)

VERIFICACION POTENCIA SINTETICA OK.
```

**Las 5 cifras del brief (0.472 / 1.073 / 1.312 / 1.622 / 1.751), el Sharpe
1.008 y la brecha +0.304 son correctas.**

---

#### A2. Parámetros del cálculo (T_eff, skew, curtosis, V) — **OK**

```
$ python3 -c "import json;d=json.load(open('fix-fase2/results/portfolio_bateria.json'));print({k:d[k] for k in ['n_trials','var_trials','sharpe_anual','n_obs','n_obs_eff','skew','kurt','sr0_per','dsr','t_stat','exposicion_media','bench_sharpe','retorno_pct','max_dd_pct']})"
{'n_trials': 12, 'var_trials': 0.0007021947704551833, 'sharpe_anual': 1.008, 'n_obs': 4403, 'n_obs_eff': 4336, 'skew': 1.037, 'kurt': 31.999, 'sr0_per': 0.04412, 'dsr': 0.7191, 't_stat': 3.48, 'exposicion_media': 0.1559827260735808, 'bench_sharpe': 1.164, 'retorno_pct': 317.52, 'max_dd_pct': -26.9}
```

Coinciden con los hardcodeados en `potencia_fase_b.py` (T_EFF=4336,
SKEW=1.037, KURT=31.999, V_TRIALS=0.0007021947704551833). **Dato nuevo que
el brief no menciona y que resulta decisivo en el Paso B: la exposición
media del portfolio de Fase B es 0.156** (suma de pesos, long-only —
`portfolio_runner.py:249`). El 84% del capital está en caja.

---

#### A3. `potencia_fase_b.py` sirve para lo que §3.4 exige — **OK**

`N_TABLA` está hardcodeada a `[1,5,12,50,100]`, pero `sharpe_min_dsr()` es
importable y acepta `n_trials`, `n_eff`, `skew`, `kurt` y `var_trials`. §3.4
se puede ejecutar **sin tocar código** (el brief prohíbe tocar código):

```
$ cd fix-fase2 && python3 -c "
import sys; sys.path.insert(0,'src')
from potencia_fase_b import sharpe_min_dsr, PPY
import numpy as np
for n in [12,13,14,15,20,30]:
    s,sr0 = sharpe_min_dsr(n)
    print(f'N={n:>3}  SR0={sr0:.5f}  Sharpe_min_anual={s*np.sqrt(PPY):.3f}')"
N= 12  SR0=0.04412  Sharpe_min_anual=1.312
N= 13  SR0=0.04514  Sharpe_min_anual=1.331
N= 14  SR0=0.04607  Sharpe_min_anual=1.349
N= 15  SR0=0.04692  Sharpe_min_anual=1.365
N= 20  SR0=0.05037  Sharpe_min_anual=1.431
N= 30  SR0=0.05494  Sharpe_min_anual=1.519
```

*Nota de alcance: esto es verificación instrumental de que la herramienta
responde para los N que §3.4 pide. **No es la entrega de §3.4**, que exige
además atar cada candidata a su N y a su literatura. Eso no se ha hecho.*

---

#### A4. Paquete 1 — walk-forward temporal — **OK, con dos anomalías**

```
$ python3 -c "import json;d=json.load(open('fix-fase2/results/portfolio_walkforward_temporal.json'));print(d['tramos_definicion']);[print(k,v['sharpe_anual'],v['dsr'],v['t_stat'],v['ic95_retorno_anual_pct'],v['pnl_pct'],v['exposicion_media'],v['bench_sharpe']) for k,v in d['resultados'].items() if k!='_dictamen'];print(d['resultados']['_dictamen'])"
[['T1_2015-2018', '2015-09-01', '2018-12-31'], ['T2_2019-2022', '2019-01-01', '2022-12-31'], ['T3_2023-fin', '2023-01-01', '2262-12-31']]
T1_2015-2018 1.328 0.8244 2.34 [0.57, 38.51] 81.72 0.186 1.467
T2_2019-2022 1.219 0.7719 2.49 [1.13, 30.71] 82.42 0.141 1.294
T3_2023-fin 0.572 0.3008 1.1 [-5.86, 20.3] 25.95 0.184 0.802
{'superado': True, 'tramos_positivos': 2, 'tramos_claramente_negativos': 0, 'n_tramos': 3}
```

Coincide con la tabla del expediente (1.33/1.22/0.57, DSR 0.824/0.772/0.301,
t 2.34/2.49/1.10, ICs idénticos). Anomalías: (a) fecha centinela
`2262-12-31` para el fin de T3 — inocua pero sucia; (b) los tramos empiezan
en 2015-09-01 mientras la métrica global usa el panel completo desde
2014-09-17 (ver A6), así que la suma de `n_obs_eff` por tramo (1136+1524+
1356 = 4016) no cuadra con el T_eff global 4336. Documentado, no es error.

---

#### A5. Paquete 3 — supervivencia — **OK**

```
$ python3 -c "import json;d=json.load(open('fix-fase2/results/portfolio_supervivencia.json'));print(d['muertos'],d['n_activos']);print(d['metricas'])"
['EOS-USD', 'XLM-USD', 'BCH-USD', 'FIL-USD', 'ICP-USD'] 15
{'retorno_pct': 266.13, 'sharpe': 0.916, 'max_dd_pct': -27.18, 'dsr': 0.6014, 't_stat': 3.18, 'pasa_t3': True, 'ic95_retorno_anual_pct': [3.27, 19.9], 'edge_ic': True, 'bench_retorno_pct': 54913.98, 'bench_sharpe': 1.068, 'supera_bench_sharpe': False}
```

Coincide (0.92 / t 3.18 / DSR 0.60 / IC [+3.27,+19.90] / B&H 1.07).

---

#### A6. Qué estrategia es exactamente la Fase B — **DISCREPA con el brief**

El brief (§3.1) dice: *"La Fase B es time-series momentum con volatility
targeting sobre un portfolio cripto"*. Es verdad a grandes rasgos y **falso
en el detalle que importa para buscar literatura**. La regla que corrió:

```
$ sed -n '212,219p' fix-fase2/src/portfolio_runner.py
        if t > 0:
            for i, tk in enumerate(tickers):
                s = rets[tk].iloc[:t]
                if s.notna().sum() < LOOKBACK + 1:
                    continue
                mom = closes[tk].iloc[t - 1] / closes[tk].iloc[t - 1 - LOOKBACK] - 1
                if not (mom > 0):
                    continue
```

```
$ sed -n '123,127p' fix-fase2/src/strategies.py
def tsmom(df: pd.DataFrame, period: int = 365) -> pd.DataFrame:
    """Adaptacion spot (sin cortos): largo en el cambio de signo del retorno de N velas, fuera cuando vuelve a <=0."""
    out = pd.DataFrame(index=df.index)
    ret_n = df["close"].pct_change(period)
    out["entry_long"] = (ret_n > 0) & (ret_n.shift(1) <= 0)
```

**Son dos reglas distintas con el mismo nombre.** `strategies.tsmom_365`
(Fase A) entra solo en el **cruce** de signo — y por eso dio 0 trades en 57
folds (`estrategias_candidatas_resultado.md:50`). `portfolio_runner.py`
(Fase B) usa un filtro de **estado**: dentro mientras `mom > 0`, fuera si
no. El docstring de `portfolio_runner.py:4` las confunde: *"Regla:
tsmom_365 (long-only)"*.

Parámetros reales de Fase B, verificados:

```
$ sed -n '30,40p' fix-fase2/src/portfolio_runner.py
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
```

Descripción correcta, para que §3.1 busque el objeto correcto: **momentum
absoluto a 12 meses (filtro de estado, signo del retorno a 365 días),
long-only, sin cortos, idéntico en 10 criptos, sin optimizar por activo;
sizing inverso a la volatilidad EWMA(λ=0.94) con σ_target=10% anual, w_max
0.20, gross ≤ 1.0, escalado si la vol de portfolio (covarianza EWMA
completa) supera 1.25·σ_target; rebalanceo diario; costes 0.1% comisión +
0.05% slippage sobre turnover.** Esto es más cercano a *absolute momentum /
tactical asset allocation* que al TSMOM long/short de Moskowitz-Ooi-Pedersen.

Rango de datos:

```
$ head -2 fix-fase2/data/multi/btc_usd_20261009.csv; tail -1 fix-fase2/data/multi/btc_usd_20261009.csv; wc -l fix-fase2/data/multi/btc_usd_20261009.csv
date,open,high,low,close,volume
2014-09-17,465.864013671875,468.17401123046875,452.4219970703125,457.3340148925781,21056800
2026-10-09,81690.4921875,82630.640625,81602.40625,82606.96875,41854283776
4407 fix-fase2/data/multi/btc_usd_20261009.csv
```

Sharpe calculado en bruto, sin tasa libre de riesgo, PPY=365:

```
$ sed -n '191,193p' fix-fase2/src/rigor_estadistico.py
    def sharpe(x):
        x = np.asarray(x, dtype=float)
        return float(x.mean() / x.std() * math.sqrt(PPY)) if x.std() > 0 else 0.0
```

**r_f = 0 implícito en todo el expediente** (estrategia y benchmark con la
misma convención, así que la comparación interna es consistente; la cifra
que entra al DSR no es un Sharpe de exceso).

---

#### A7. `fix-fase2/docs/portfolio_resultado.md` — **NO EXISTE**

El brief ordena leerlo entero en el Paso A. No está:

```
$ ls -la fix-fase2/docs/portfolio_resultado.md; echo "exit=$?"
ls: cannot access 'fix-fase2/docs/portfolio_resultado.md': No such file or directory
exit=2
$ ls fix-fase2/docs/
AUDIT_BRIEF.md
deliberacion_sombra.md
estrategias_candidatas_resultado.md
fase_b_reevaluacion_resultado.md
paper_dashboard.html
paper_runner_operacion.md
rigor_estadistico_resultado.md
sizing_05_resultado.md
supabase_esquema.sql
timesfm_fase2_resultado.md
walkforward_stability.md
$ grep -rl "portfolio_resultado" --include=*.md .
./fix-fase2/tareas/tarea-nube-S2-investigacion-literatura-cripto.md
./fix-fase2/tareas/tarea-nube-S1-auditoria-harness-trading.md
```

La única referencia al fichero son los dos briefs que lo mandan leer.
**No hay documento de resultado de Fase B**: la descripción de la estrategia
hubo que reconstruirla del código (A6). Esto es un agujero del expediente,
no un detalle: la Fase B es el único resultado vivo del proyecto y no tiene
documento propio.

---

#### A8. `timesfm_fase2_resultado.md` — **OK, y contiene una bomba**

Leído entero. Qué se descartó, con qué evidencia:

- **H1 (zero-shot multi-activo vs naive): MUERTA.** Agregado dir_acc 0.4925,
  t −1.13, MASE 2.75 sobre 1118 ventanas / 5665 observaciones direccionales,
  10 activos. Umbral pre-registrado de muerte inmediata: dir_acc ≤ 0.52 o
  t < 2.0. 8 de 10 activos con dir_acc < 0.53.
- **H2 (LoRA multi-activo): muerta por condición**, no evaluada.
- Reapertura solo con **cambio de universo de datos** (timeframe intradía u
  otra clase de activos), no con otra seed.

```
$ grep -rn "N=1[0-9]\|N_TRIALS = " --include=*.md --include=*.py fix-fase2/ | grep -v tarea-nube
fix-fase2/src/portfolio_bateria.py:35:N_TRIALS = 12
fix-fase2/src/portfolio_supervivencia.py:43:N_TRIALS = 12
fix-fase2/src/portfolio_walkforward_temporal.py:37:N_TRIALS = 12
fix-fase2/docs/timesfm_fase2_resultado.md:6:**N=14** registrado antes del primer forecast (Estado de la tarea).
fix-fase2/docs/fase_b_reevaluacion_resultado.md:18:tramo. N=12 trials en todos los DSR.
```

**TimesFM registró N=14 el 2026-10-12/13 — tres días DESPUÉS de la
reevaluación del 2026-10-09 que fijó N=12.** El código sigue con 12. Ver
objeción B2.

---

#### A9. Las 4 citas del expediente — **2 veredictos distintos**

**(a) El fichero fuente que el brief cita no está en el repo:**

```
$ find . -name "*rigor-estadistico*" -o -name "tarea-trading-bot*"
(sin salida)
$ grep -rn "White\|Harvey\|Borwein\|Bailey" --include=*.md --include=*.py fix-fase2/ | grep -v tarea-nube
fix-fase2/src/personas/simons.md:26:Modera el sombrero **White** (hechos): si los datos no sostienen la tesis, el resto del debate
fix-fase2/src/rigor_estadistico.py:11:  - DSR (Bailey & López de Prado 2014, SSRN 2460551) corrigiendo por N=11
fix-fase2/src/rigor_estadistico.py:14:  - t-stat de los retornos diarios (umbral exigido: t>3, Harvey/Liu/Zhu 2016)
fix-fase2/src/rigor_estadistico.py:94:    """SR0 = sqrt(V) * E[max de N normales estandar] (Bailey-LdP Ec. 2).
fix-fase2/verificar_rigor_sintetico.py:4:  1. VALIDACION CRUZADA del paper: ejemplo impreso de Bailey & López de Prado
fix-fase2/docs/rigor_estadistico_resultado.md:10:- **Paper original:** Bailey, D.H. & López de Prado, M. (2014), *The Deflated
fix-fase2/docs/fase_b_reevaluacion_resultado.md:40:invirtiendo la PSR de Bailey-LdP (reutilizada de `rigor_estadistico.py`):
```

`tarea-trading-bot-rigor-estadistico.md` **no existe en esta rama**. En todo
el repo hay **una sola** cita completa (Bailey & LdP 2014, con SSRN).
Harvey/Liu/Zhu aparece como comentario de código sin coordenadas. White 2000
y Bailey/Borwein/LdP/Zhu 2017 **no aparecen en ninguna parte**. La
afirmación del brief *"las 4 citas de la Fase B se verificaron una por una"*
**no es verificable desde este repo**: no hay registro de esa verificación.

**(b) Las 4 citas, verificadas con búsqueda real en esta sesión — las 4
existen y las coordenadas son correctas.** Solo abstracts y registros
bibliográficos; no se leyó ningún texto completo.

| Cita del expediente | Veredicto | Coordenadas confirmadas |
|---|---|---|
| Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*, JPM 40(5), 94-107, SSRN 2460551 | **EXISTE, exacta** | JPM vol. 40, núm. 5, pp. 94-107, 2014 (número del 40º aniversario), DOI 10.3905/jpm.2014.40.5.094; preprint SSRN 2460551 fechado 31-jul-2014 |
| White (2000), *A Reality Check for Data Snooping* | **EXISTE** | Econometrica 68(5), sept. 2000, pp. 1097-1126, DOI 10.1111/1468-0262.00152 |
| Bailey, Borwein, López de Prado & Zhu (2017), *The Probability of Backtest Overfitting* | **EXISTE** | Journal of Computational Finance 20(4), DOI 10.21314/JCF.2016.322; preprint SSRN 2326253 (2015). Los 4 autores correctos |
| Harvey, Liu & Zhu (2016), *…and the Cross-Section of Expected Returns* | **EXISTE** | Review of Financial Studies 29(1), pp. 5-68, DOI 10.1093/rfs/hhv059; working paper NBER 20592 (2014). El umbral t > 3.0 está en el abstract |

Matiz sobre Harvey/Liu/Zhu, relevante porque el proyecto usa su umbral como
regla fija: en el working paper NBER el 3.0 se presenta como **salida de su
modelo de contraste múltiple, no como constante universal**, y los autores
dan cortes históricos crecientes en el tiempo. Usarlo como "t > 3 y listo"
es una simplificación del propio paper. *(Verificado solo contra abstract y
registros; no se leyó el texto completo.)*

Hallazgo crítico asociado: la **validación cruzada numérica** del DSR se
apoya en un paquete de terceros, `deflated_sharpe` /
`https://daru.finance/projects/deflated-sharpe`
(`rigor_estadistico_resultado.md:14-15`). **No verificado en esta sesión**
que esa URL o ese paquete existan — ese es el único eslabón que conecta la
implementación con los números impresos del paper. [no verificado]

---

#### A10. Discrepancias de identidad y rutas entre el brief y el repo — **DISCREPA**

```
$ git remote -v
origin  https://github.com/miguezlopezia-a11y/trading-bot (fetch)
origin  https://github.com/miguezlopezia-a11y/trading-bot (push)
$ ls shared 2>&1
ls: cannot access 'shared': No such file or directory
$ git ls-tree --name-only origin/main | head
.gitignore
REGISTRO_D.md
data
docs
migrar_journal_supabase.py
results
smoke_kimi_real.py
smoke_openrouter_real.py
src
verificar_a4_a7_cierre.py
$ find . -name "REGISTRO_F.md"
(sin salida)
```

| Afirmación del brief | Realidad |
|---|---|
| Repo `miguezlopezia-a11y/bunker-2026` | Es `miguezlopezia-a11y/trading-bot` |
| Escribir en `shared/trading-bot-fase1/fix-fase2/docs/` | No existe `shared/`. La ruta real es `fix-fase2/docs/` |
| §5 DoD: *"PR abierto contra `main`"* | `origin/main` **no contiene `fix-fase2/`**. Un PR contra main sería un PR que añade todo el directorio. La instrucción de Pablo (PR contra `fase-b-recuperada`) es la correcta; la del brief es inejecutable |
| §8: reflejar en `shared/estado-y-siguiente-paso.md` | No existe en el repo |
| `fase_b_reevaluacion_resultado.md`: *"Salidas en `REGISTRO_F.md`"* y *"suite completa 15/15 PASS"* | `REGISTRO_F.md` no existe. **La evidencia de los 15/15 no es verificable: NO LO SÉ** |

---

#### A11. Dos valores de V en el expediente — **OK, no es error**

```
$ python3 -c "import json;print(json.load(open('fix-fase2/results/rigor_estadistico.json'))['var_trials'], json.load(open('fix-fase2/results/portfolio_bateria.json'))['var_trials'])"
0.0007016935642058066 0.0007021947704551833
```

`rigor_estadistico_resultado.md` dice 0.0007017 (11 variantes de Fase A);
`fase_b_reevaluacion_resultado.md` dice 0.0007022 (las 11 + la regla de Fase
B). Cada documento es consistente con su propio JSON. No hay contradicción
— pero ver B1, que es donde esta cifra revienta el expediente.

---

### Paso B — Ataque adversarial al planteamiento de esta tarea

Nueve objeciones. Las dos primeras, si se confirman, hacen innecesaria la
tarea entera.

---

#### B1. El listón de 1.312 está probablemente inflado por un defecto de escala en V, y arreglarlo podría cerrar la brecha sin buscar nada — **CRÍTICO**

Esta es la objeción más grave que he encontrado y no está en el brief.

El listón depende de `SR₀ = √V · E[max de N normales]`, donde V es la
varianza **across-trial** de los Sharpes diarios. Los 12 trials no se
midieron en la misma escala temporal: 11 vienen de Fase A (BTC solo, T_eff
entre 598 y 2188) y el 12º de Fase B (panel de 10 activos, T_eff 4336).

```
$ cd fix-fase2 && python3 -c "
import sys, json; sys.path.insert(0,'src')
import numpy as np
from potencia_fase_b import sharpe_min_dsr, PPY
d=json.load(open('results/rigor_estadistico.json'))
sh=[v['sharpe_per'] for v in d['variantes'].values()]
nobs=[v['n_obs_eff'] for v in d['variantes'].values()]
print('Fase A: sharpes diarios n=%d, sd=%.5f, var=%.7f' % (len(sh), np.std(sh,ddof=1), np.var(sh,ddof=1)))
print('Fase A n_obs_eff: min=%d max=%d -> sd muestral de un Sharpe NULO: %.4f..%.4f' % (min(nobs),max(nobs),1/np.sqrt(max(nobs)),1/np.sqrt(min(nobs))))
for V in [0.0007022, 0.0003, 0.0001365, 0.0001]:
    s,sr0=sharpe_min_dsr(12, var_trials=V)
    print('  V=%.7f  SR0=%.5f  liston_anual=%.3f' % (V, sr0, s*np.sqrt(PPY)))"
Fase A: sharpes diarios n=11, sd=0.02649, var=0.0007017
Fase A n_obs_eff: min=598 max=2188 -> sd muestral de un Sharpe NULO: 0.0214..0.0409
  V=0.0007022  SR0=0.04412  liston_anual=1.312
  V=0.0003000  SR0=0.02884  liston_anual=1.020
  V=0.0001365  SR0=0.01638  liston_anual=0.842
  V=0.0001000  SR0=0.01665  liston_anual=0.788
```

La dispersión observada entre los 12 trials (sd 0.0265 diaria) **cae de
lleno dentro del rango de ruido muestral de un Sharpe con habilidad cero a
esos tamaños de muestra (0.021–0.041)**. Es decir: V no mide dispersión de
habilidad entre las reglas, mide **error de estimación de muestras cortas**.
Y ese V se usa para deflactar un Sharpe estimado con 4336 observaciones, es
decir con una precisión 5–7× mayor. Reescalando el ruido de Fase A al T_eff
del estadístico que se está deflactando (media `n_obs_eff` de Fase A = 843;
V·843/4336 ≈ 0.0001365), el listón cae a **0.842 anual — por debajo del
1.008 observado**. Es decir: **DSR ≥ 0.95 pasaría y el veredicto "SEÑAL
DÉBIL" sería un artefacto de medición.**

Lo que **no** afirmo: que 0.842 sea el listón correcto. Reestimar las 11
reglas de Fase A sobre el panel de 12 años podría aumentar su dispersión
*verdadera* (los tramos 2015-2018 y 2019-2022 son muy favorables al
momentum), y entonces V no bajaría tanto. La dirección neta es desconocida a
priori. La interpretación de que Bailey-LdP exige trials de longitud
homogénea para que V sea comparable **no la he verificado contra el texto
del paper** (solo contra el abstract) — [no verificado].

Lo que **sí** afirmo, y es suficiente: **el V actual mezcla dos escalas de
ruido distintas, y hasta que eso se resuelva el número 1.312 no es fiable ni
en un sentido ni en el otro. Todo el expediente, los tres briefs y la
premisa "solo quedan dos salidas" cuelgan de esa cifra.**

**Propuesta.** Antes de §3, y antes de S1 y S3: **reestimar las 11 reglas de
Fase A sobre el mismo panel de 10 activos y 12 años, recalcular V con T
homogéneo y recalcular el DSR de Fase B.** No es una hipótesis nueva: son
las 11 reglas ya contadas, medidas otra vez. **N sigue siendo 12, no sube.**
Coste: minutos de CPU, cero trials nuevos, cero datos nuevos. Es, con
diferencia, la acción de mayor valor esperado por euro de cómputo disponible
en este expediente, y no aparece en ninguno de los tres briefs.

---

#### B2. N ya no es 12, y nadie lo ha registrado — **CRÍTICO**

`timesfm_fase2_resultado.md:6` declara **N=14 registrado antes del primer
forecast**, con fecha 2026-10-12/13. La reevaluación que fija N=12 es del
2026-10-09. El código sigue con `N_TRIALS = 12` en los tres módulos (A8).

Una de dos: o el expediente contabilizó dos trials (H1 y H2 de TimesFM) que
nunca debieron contarse así, o **el N vigente es 14 y el listón real es
1.349, con brecha +0.341 en lugar de +0.304**. No es un detalle contable: la
regla central del proyecto es "cada variante nueva sube el umbral para todas
las anteriores". Si el propio expediente no sabe cuántas variantes ha
probado, esa regla no se está aplicando — se está recitando.

Y hay un segundo problema de contabilidad, peor: ¿cuentan como trials las
**configuraciones** que ya se barrieron? `estrategias_candidatas_resultado.md`
documenta 57 folds sobre **4 configuraciones de ventana** (365/90, 730/180,
180/60, 365/180) por variante. Si cada configuración de ventana evaluada es
una comparación, N no es 12 ni 14, es bastante más alto. Si no lo es, hay
que decir por qué, y la justificación no está escrita en ninguna parte.

**Propuesta.** Un fichero `fix-fase2/docs/registro_N.md` con **una línea por
trial**, fecha, quién lo registró y qué se evaluó, y la regla explícita de
qué cuenta como trial (¿una regla? ¿una regla × configuración? ¿una
hipótesis pre-registrada?). Sin ese libro de cuentas, **todo §3.4 es
aritmética sobre un número inventado** y S2 no debería ejecutarse.

---

#### B3. El brief pide a la literatura que responda una pregunta que solo una medición ausente puede responder — **ALTO**

§3.1 plantea bien la pregunta: *¿es conocido que TSMOM con vol-targeting
reduzca drawdown sin batir al benchmark en Sharpe? Si es el resultado
esperado, la Fase B no es señal débil, es una reproducción correcta.*

El problema es que la Fase B **no tiene medido lo que haría falta para
responder eso**, y la literatura no puede suplirlo. Fase A sí lo midió, y
fue justo esa medición la que mató a las variantes de régimen:

```
$ grep -n "Benchmark de exposición igualada" -A 2 fix-fase2/docs/rigor_estadistico_resultado.md | head -4
77:## Benchmark de exposición igualada
78-
79-Sharpe/Calmar de la estrategia vs buy&hold de BTC **solo en los días con
```

Con ese benchmark, el dictamen de Fase A fue literal: *"el Sharpe
'respetable' del período completo de sma_timing_50/100 viene de estar ~50%
del tiempo fuera del mercado — es reducción de exposición/drawdown, no edge
de retorno"*.

**La Fase B tiene exposición media 0.156 (A2) y se compara contra un
benchmark 100% invertido.** El par "1.008 vs 1.164" no es comparable, y el
expediente aplicó en Fase A exactamente la corrección que en Fase B omitió.
Si el B&H a igual exposición gana, Fase B es el mismo cadáver que
sma_timing_50 con otro nombre, "SEÑAL DÉBIL" es un veredicto no medido, y
S2 entera sobra.

Nota de rigor, para no exagerar: **la exposición baja no infla el Sharpe por
sí sola** (el Sharpe es invariante a escala, y apalancar la misma señal no lo
cambia). El problema no es el nivel de exposición, es que el benchmark no
está igualado. Y por el mismo argumento, la caja al 0% (r_f=0, A6) tampoco
regala Sharpe: en términos de exceso de retorno es neutral. No hay atajo por
ahí.

**Propuesta.** Correr el benchmark de exposición igualada sobre la curva de
equity de Fase B antes de §3. La función ya existe en
`rigor_estadistico.py`. **Es un benchmark, no una variante: no sube N.**
Junto con B1, son las dos cosas gratis que hay que hacer antes de gastar un
trial o una hora de búsqueda.

---

#### B4. "Ampliar T" no es una palanca con datos diarios: hace falta 8× la historia que existe — **CRÍTICO**

El brief lista subir T como una de las tres palancas reales y S3 entera se
dedica a ella. Cuantificado con la propia herramienta:

```
$ cd fix-fase2 && python3 -c "
import sys; sys.path.insert(0,'src')
import numpy as np
from potencia_fase_b import sharpe_min_dsr, PPY, SKEW, KURT
from rigor_estadistico import psr, expected_max_sharpe
for t in [687,1500,3000,4336,6000,8672,13008]:
    s,_=sharpe_min_dsr(12, n_eff=t); print('  T_eff=%6d  liston_anual=%.3f' % (t, s*np.sqrt(PPY)))
sr0,_=expected_max_sharpe(12, 0.0007021947704551833)
print('suelo asintotico (T->inf) = %.3f anual' % (sr0*np.sqrt(PPY)))
obs=1.008/np.sqrt(PPY)
lo,hi=100,4000000
for _ in range(200):
    mid=(lo+hi)//2
    if psr(obs, mid, sr0, SKEW, KURT)>=0.95: hi=mid
    else: lo=mid
print('T_eff necesario con Sharpe 1.008 y N=12: %d obs = %.1f anos (factor %.1fx)' % (hi, hi/365, hi/4336))"
  T_eff=   687  liston_anual=2.029
  T_eff=  1500  liston_anual=1.641
  T_eff=  3000  liston_anual=1.407
  T_eff=  4336  liston_anual=1.312
  T_eff=  6000  liston_anual=1.241
  T_eff=  8672  liston_anual=1.174
  T_eff= 13008  liston_anual=1.114
suelo asintotico (T->inf) = 0.843 anual
T_eff necesario con Sharpe 1.008 y N=12: 35000 obs = 95.9 anos (factor 8.1x)
```

Con N=12 y el Sharpe observado, cerrar la brecha solo con T exige **~35.000
observaciones diarias efectivas, unos 96 años**. Con N=14 (B2) son ~160
años. Duplicar la historia (24 años de cripto, imposible: Bitcoin cotiza
desde 2010) solo baja el listón de 1.312 a 1.174, todavía por encima de
1.008.

Y lo peor: **añadir activos no aumenta T.** T es la longitud de la serie de
retornos de la estrategia, y hay una sola curva de equity con capital
compartido:

```
$ sed -n '264p' fix-fase2/src/portfolio_runner.py
    rets = eq.pct_change().dropna()
```

Pasar de 10 a 30 activos cambia *qué* serie es, no *cuántas* observaciones
tiene. Luego la única vía real para multiplicar T por 8 es **frecuencia
intradía** — que multiplica el turnover contra un coste de 0.15% por unidad
de turnover, y que además reabriría el expediente TimesFM (su condición de
reapertura es exactamente "timeframe intradía", A8).

**Propuesta.** S3 debe empezar demostrando que puede alcanzar ~35.000
observaciones efectivas con costes realistas, y no ejecutarse si no. Si no
puede, la frase del brief *"solo quedan dos salidas"* es falsa: queda una
(un Sharpe genuinamente ≥ 1.33), y S2 pasa de ser la primera de dos a ser la
única — lo que **aumenta** su importancia, no la reduce. Esta objeción no
mata S2; mata S3 y reescribe el mapa.

---

#### B5. §3.4 calcula el coste estadístico con los momentos equivocados, y eso puede matar a la mejor candidata y salvar a la peor — **ALTO**

§3.4 ordena variar **solo N**, manteniendo *"el resto de parámetros del
expediente (T_eff, skew, curtosis declarados en
`fase_b_reevaluacion_resultado.md`)"*. Eso es un error de método, no de
cálculo.

El listón de una candidata depende de **cuatro** cosas, no de una: N, T_eff,
skew y curtosis. Y las tres últimas son propiedades de **la candidata**, no
del expediente. Un carry de funding en perpetuos es una serie de retornos
pequeños, muy frecuentes, con cola izquierda gruesa (cascadas de
liquidación): skew negativo, curtosis alta y T potencialmente 24× mayor si
se mide por hora. Valorar su trial con `skew=1.037, kurt=32, T_eff=4336`
—los momentos de un momentum long-only diario— no es conservador, es
simplemente otra serie.

La magnitud del error es grande en ambas direcciones (ver B4: 1.312 a
T=4336, 1.174 a T=8672, 2.029 a T=687). Un candidato de alta frecuencia
tendría un listón **más bajo** que 1.331, y el procedimiento tal como está
escrito nunca lo mostraría: lo descartaría "por aritmética" con un número
que no es el suyo. Inversamente, una candidata con pocas observaciones
efectivas (señales on-chain mensuales, p. ej.) tendría un listón **mucho más
alto** que 1.331 y el procedimiento la aprobaría indebidamente.

La herramienta ya soporta hacerlo bien: `sharpe_min_dsr(n, var_trials, n_eff,
skew, kurt)` acepta los cuatro (A3). No hay excusa técnica.

Sobre la pregunta directa del brief —*¿la regla de descartar "por
aritmética" es correcta o se pasa de rígida?*— mi respuesta: **la regla es
correcta como condición necesaria y está mal instrumentada.** No es
demasiado rígida; es demasiado tosca. Y hay una tentación que conviene
cerrar por escrito antes de que aparezca en §3: alguien argumentará que una
candidata sobre un universo de datos nuevo (funding rates, on-chain) es
"trial 1 sobre un panel nuevo" y le corresponde el listón de 0.472, no 1.331.
**Eso es falso y es el agujero por el que se escapa todo el rigor del
expediente.** El sesgo de selección múltiple vive en el decisor, no en el
dataset: si Pablo ha mirado 12 ideas y reportaría la que funcione, N=13 al
probar la 13ª, venga de donde vengan los datos. Lo que sí cambia con el
universo es **V**, y V hay que reestimarlo, no resetearlo a conveniencia.

**Propuesta.** Reescribir §3.4 así: para cada candidata, (i) N = N_vigente+1
siempre, sin excepción por universo de datos; (ii) T_eff, skew y curtosis
estimados o acotados para *esa* candidata, con la fuente de la estimación
declarada; (iii) V justificada explícitamente. Y dejar escrito en el brief
que el universo de datos no resetea N.

---

#### B6. §3.2 prioriza con énfasis la familia que §3.6 prohíbe proponer — **ALTO**

§3.2 dice de carry/funding/basis: *"Evaluar con atención: es la familia que
mejor encaja con un expediente que ya demostró no poder predecir
dirección."* Estoy de acuerdo: es la respuesta correcta a este expediente,
porque es la única con un mecanismo que no requiere pronóstico.

§3.6 dice: *"No proponer nada que exija dinero real, broker o API con
credenciales."*

El funding rate solo existe en futuros perpetuos de exchanges. Capturarlo
exige, como mínimo, cuenta en un exchange de derivados. **Las dos secciones
del mismo brief se contradicen sobre la misma familia**, y la contradicción
no está señalada. Tal como está escrito, §3 obliga a investigar a fondo una
vía que su propia sección de exclusiones impide recomendar, lo que garantiza
que §3.5 ("una sola vía, o ninguna") acabe en "ninguna" por una razón
administrativa y no por una razón empírica. Eso es un gasto de 2-4 horas con
el resultado predeterminado.

Hay una salida, pero hay que decidirla **antes**: separar *investigar el
mecanismo con datos históricos públicos de funding* (que no exige dinero ni
credenciales, si esos datos son descargables sin clave — **[no verificado]**,
no lo he comprobado y §3 no se ejecuta) de *operarlo* (que sí). Si se acepta
la primera, la familia entra. Si no, sale antes de buscar nada.

**Propuesta.** Pablo decide esto en §7 junto con el OK, en una línea: ¿se
admite una candidata cuyo backtest es reproducible con datos públicos pero
cuya ejecución exigiría un exchange de derivados? Sin esa decisión, §3 no
debería arrancar.

---

#### B7. ¿Es buscar literatura el mismo sesgo de búsqueda múltiple disfrazado? Parcialmente sí, y el repo lo demuestra — **MEDIO-ALTO**

Respuesta honesta a la pregunta del brief, en tres partes.

**Dónde no lo es.** La literatura aporta una cosa que este proyecto no puede
fabricar: evidencia fuera de muestra sobre datos que este expediente nunca
ha tocado. Un resultado replicado en 2010-2024 por autores independientes no
es un grado de libertad consumido sobre el panel de Pablo. Eso es real y es
el argumento válido del brief.

**Dónde sí lo es.** El sesgo no está en el origen de la hipótesis, está en
**cuál paper se decide creer**. Si se leen veinte papers y se elige el que
mejor encaja con este panel, el buscador ha hecho de optimizador y el grado
de libertad se ha consumido igual, solo que sin registrarlo. La forma de
acotarlo es trivial y el brief la tiene **en el orden equivocado**: §3.3
(criterios de descarte) debe estar **congelado antes** de ejecutar §3.2
(búsqueda). Tal como está numerado, se busca primero y se filtra después, que
es precisamente cómo se racionaliza un hallazgo.

**Dónde el repo ya lo refuta como novedad.** Las reglas de Fase A ya venían
de literatura, y el expediente lo dice:

```
$ grep -n "Moskowitz\|Liu/Tsyvinski" fix-fase2/docs/estrategias_candidatas_resultado.md
50:**tsmom_365 (Moskowitz/Ooi/Pedersen, 12 meses)** — **inactiva de verdad**:
58:**tsmom_7 (Liu/Tsyvinski, 1 semana)** — cobertura completa (100%), pero
```

Es decir: **el proyecto ya probó hipótesis con respaldo en literatura —
incluida Liu/Tsyvinski, que es exactamente la referencia de factores cripto
que §3.2 quiere buscar— y murieron igual.** Luego "venir de un paper" no es
un predictor de supervivencia aquí, y presentarlo como el nuevo estándar de
rigor es una promesa que el propio historial del repo no respalda. Lo que de
verdad acota el gasto de trials es el **pre-registro** de §3.5, no la
bibliografía.

**Propuesta.** Invertir el orden: congelar §3.3 antes de buscar; registrar
cuántas candidatas se *miraron*, no solo cuántas se reportan (una tabla
larga leída contra el mismo panel es una búsqueda); y declarar que el
entregable real de S2 es **un pre-registro de §3.5**, con la literatura como
justificación de esa única elección y nada más. Si S2 produce una tabla
bonita de ocho candidatas y ningún pre-registro, ha fallado.

---

#### B8. La alternativa descartada sin justificar: reorientar a control de riesgo — y §3.5 la hace imposible de recomendar — **MEDIO**

El brief acierta al identificarla y la cita bien: el dictamen de Fase B dice
que el valor está en el control de riesgo. Verificado:

```
$ grep -n "max_dd" fix-fase2/results/portfolio_bateria.json fix-fase2/results/portfolio_supervivencia.json
fix-fase2/results/portfolio_bateria.json:19:  "max_dd_pct": -26.9,
fix-fase2/results/portfolio_bateria.json:22:  "bench_max_dd_pct": -88.96,
fix-fase2/results/portfolio_supervivencia.json:14:    "max_dd_pct": -27.18,
```

−26.9% contra −88.96% del B&H, con un Sharpe solo 0.16 inferior. Eso es un
resultado, medido, reproducible y sobre 12 años. Es el único resultado sólido
que tiene el proyecto.

El problema es estructural: §2 Paso B exige que esa alternativa *"aparezca
evaluada en el entregable, no omitida"*, pero §3.5 exige terminar con *"una
sola vía"* de fuente de retorno, o ninguna. **Una reorientación a control de
riesgo no es una vía de retorno y por tanto no es expresable en el formato
que §3.5 impone.** Quedará en un párrafo de cortesía y luego se descartará
por no caber en la tabla.

Y hay un punto que ni el brief ni el expediente han escrito: **si el
objetivo es control de riesgo, el DSR no es la métrica decisiva y el listón
de 1.312 es irrelevante.** El bloqueo entero del expediente es un bloqueo
sobre una pregunta (¿hay edge de retorno?) que puede no ser la pregunta del
negocio. Nadie ha escrito qué decisión depende de la respuesta.

**Propuesta.** Antes del OK de §7, que Pablo escriba en una línea qué
decisión real depende de que haya o no edge de retorno. Si la respuesta es
"ninguna, lo que quiero es no perder el 89%", el expediente ya está resuelto
y S2 sobra. Si la respuesta es "quiero que esto genere retorno", entonces
S2 tiene sentido y el formato de §3.5 es el correcto.

---

#### B9. El brief no es ejecutable tal como está escrito — **BAJO en gravedad, ALTO en consecuencia**

Resumen de A7 y A10: manda leer un fichero que no existe
(`docs/portfolio_resultado.md`), nombra un repo que no es este
(`bunker-2026`), escribe en una ruta que no existe
(`shared/trading-bot-fase1/…`), fija un PR contra una rama que no contiene
el directorio (`main`), cita como fuente de las 4 referencias un fichero que
no está en la rama, y referencia dos documentos ausentes (`REGISTRO_F.md`,
`shared/estado-y-siguiente-paso.md`).

Ninguno es grave por separado. Juntos sí: un DoD que no se puede satisfacer
literalmente obliga al ejecutor a improvisar sustituciones, y cada
improvisación es una decisión de alcance tomada por quien menos contexto
tiene. Así es como una tarea de 2-4 h se convierte en otra cosa.

**Propuesta.** Corregir las seis rutas del brief en el mismo commit que el
OK de §7. Y una regla de proyecto: un brief que cita un fichero del repo
cita también su ruta verificada.

---

### Qué haría que esta investigación entera no sirviera de nada

Respuesta directa a la pregunta del paso B, en orden de probabilidad:

1. **Que B1 sea cierto.** Si el listón real con V homogéneo está por debajo
   de 1.008, Fase B ya pasa DSR ≥ 0.95, no hay brecha que cerrar y S2 busca
   una solución a un problema que no existe. **Es comprobable en minutos y
   nadie lo ha comprobado.**
2. **Que B3 sea cierto.** Si el B&H a igual exposición bate a Fase B, no hay
   señal que extender, "SEÑAL DÉBIL" es un veredicto no medido, y S2 estaría
   buscando una segunda fuente de retorno para un sistema cuya primera
   fuente no existe. **También comprobable en minutos.**
3. **Que B2 no se resuelva.** Con el libro de cuentas de N roto, todo número
   que §3.4 produzca es aritmética sobre una cifra desconocida. El documento
   parecería rigoroso y no lo sería.
4. **Que §3.4 se ejecute como está escrito (B5).** Produciría una tabla de
   costes estadísticos que no son los costes de las candidatas. Peor que no
   tenerla, porque invita a decidir.
5. **Que la contradicción de B6 no se resuelva antes.** El resultado de §3.5
   sería "ninguna" por motivo administrativo, con 2-4 h gastadas.
6. **Que B8 sea el caso.** Si ninguna decisión real de Pablo depende de que
   exista edge de retorno, S2 es un ejercicio.

**No encontré ninguna objeción a una cosa: la premisa aritmética central del
brief es correcta.** Probar ideas a voleo encarece cada intento siguiente, el
cálculo que lo demuestra se reproduce bit a bit (A1), su verificación
sintética pasa, y exigir respaldo externo antes de gastar un trial es la
respuesta correcta a ese hecho. El problema del brief no es su lógica: es que
tres de los cuatro números sobre los que razona (el listón 1.312, el N=12 y
la comparabilidad del Sharpe 1.008 con su benchmark) no están verificados, y
dos de los tres se pueden verificar antes de buscar un solo paper.

---

### Recomendación de secuencia (para el OK de §7)

Por orden, y todo lo de abajo **sin gastar un solo trial nuevo**:

1. **B1** — reestimar las 11 reglas de Fase A sobre el panel de 12 años,
   recalcular V con T homogéneo, recalcular el DSR de Fase B. N sigue en 12.
2. **B3** — benchmark de exposición igualada sobre la equity de Fase B.
3. **B2** — `docs/registro_N.md` con una línea por trial y la regla de qué
   cuenta como trial.
4. **B8** — Pablo escribe qué decisión depende de que exista edge de retorno.
5. Solo si 1-4 dejan la brecha viva y la decisión de 4 lo justifica:
   corregir §3.4 según **B5**, resolver **B6**, invertir el orden §3.3/§3.2
   según **B7**, y entonces ejecutar §3.

**PARADA.** §3 no ejecutada. Sin búsqueda de literatura, sin evaluación de
candidatas, sin cálculo de costes estadísticos por candidata. Esperando OK
escrito de Pablo en §7.
