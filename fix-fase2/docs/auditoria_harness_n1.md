# Auditoría N1 del harness de backtesting — informe

**Fecha:** 2026-11-01 · **Ejecutor:** sesión N1 en la nube (Claude Code, Opus 5).
**Rama:** `nube/s1-auditoria-harness`, PR contra `fase-b-recuperada`.
**Brief:** `fix-fase2/tareas/tarea-nube-S1-auditoria-harness-trading.md`, con la
Fase 0 némesis y el OK de Pablo (§8) que fija el orden ejecutado.
**Entorno:** Python 3.13.18, numpy 2.5.3, pandas 3.0.5. `scipy` y `yfinance`
instalados por la sesión. `torch` y `timesfm` no disponibles. Red: la política
del contenedor bloquea Yahoo Finance.
**Scripts:** `fix-fase2/auditoria_n1/*.py`, uno por paso, cada uno ejecutable
por separado y determinista.
**Ancla:** `fix-fase2/docs/estado-auditoria-n1.md`.

Esta auditoría no buscaba una estrategia. Buscaba errores en el instrumento de
medida. Encontró cinco cosas reales, ninguna de las cuales invalida ningún
dictamen, y cerró con prueba el agujero que de verdad importaba: que nadie
había comprobado nunca que el código de este repo fuese el que generó las
cifras del expediente.

---

## 1. Veredicto sobre los cuatro dictámenes

| Dictamen | Veredicto | Qué lo justifica |
|---|---|---|
| **Fase A** — 11 variantes, BTC 5 años: NINGUNA sobrevive. DSR máx 0.66, t máx 1.52 | **SE SOSTIENE** | Reproduce en 245/245 campos (3.0b). Los tres criterios bloqueantes del audit previo cierran a favor del harness (3.1). Sin look-ahead en 14/14 estrategias (3.2). El único sesgo encontrado (H4, benchmark de exposición igualada inflado) va **en contra** de las estrategias, y Fase A ya moría por DSR, bootstrap y t de forma independiente del benchmark. |
| **Fase B** — portfolio 10 activos, 12 años: SEÑAL DÉBIL. Sharpe 1.008, t 3.48, DSR 0.72 | **QUEDA EN DUDA** | El harness está limpio: reproduce exacto con el sello `20261007` (3.0b-bis), la curva es invariante al futuro (3.2), el coste de rebalanceo se cobra y el edge resiste costes ×2 (3.3), y el dictamen es robusto a todo N ≥ 5 (3.4). **Pero el número del que cuelga no lo está:** el listón de 1.312 se mueve a **0.823** si `V` se mide con `T` homogéneo (3.0c), y el Sharpe observado 1.008 cae **en medio** de las dos construcciones defendibles. Y el "pierde vs B&H" era un veredicto no medido: a igual exposición el B&H gana por 0.063, no por 0.156 (3.0d). El dictamen no se invalida — se queda sin un suelo numérico firme. |
| **Fase B-reevaluación** — P1 y P3 superados, DSR sigue 0.72 | **SE SOSTIENE en P1 y P3; el DSR QUEDA EN DUDA** | P3 reproduce exacto y es robusto a quitar cualquiera de los 5 caídos (3.6). P1 reproduce (IC95 de los tres tramos). **Salvedad:** los **DSR por tramo** (0.824/0.772/0.301) descansan en una `V` estimada en 2024-2026 y aplicada a tramos que empiezan en 2015 (H3), porque recalcularla por tramo es imposible. No afecta al dictamen P1, que se decide por IC95 y no por DSR. |
| **TimesFM 2.5 (H1/H2)** — MUERTA. dir_acc 0.4925 agregada | **QUEDA SIN VERIFICAR POR REPRODUCCIÓN** | La cifra 0.4925 se confirmó en el documento, pero `results/timesfm_t3_zeroshot.json` **no se regeneró**: hace falta `torch` y `timesfm`, no instalables en este entorno. No hay motivo para dudar del dictamen, y no hay prueba de reproducción. Se declara el límite en vez de darlo por bueno. |

**Nada se activa.** La brecha +0.304 sigue ahí, reproducida exacta.

---

## 2. Tabla de hallazgos

| id | archivo:línea | tipo | ¿real? | ¿afecta a qué dictamen? | severidad |
|---|---|---|---|---|---|
| **H1** | `portfolio_runner.py:122` (antes del parche) | reproducibilidad / datos | **sí**, probado empíricamente | A ninguno *a posteriori* (Fase B reproduce exacto), pero impedía auditar y abría la puerta a descargas silenciosas | **CRÍTICO** (resuelto en este trabajo) |
| **H2** | ausencia de `verificar_a1*.py`, `a2*`, `a3*` | cobertura de verificación | **sí** | A los cuatro, indirectamente: el expediente se apoyaba en un harness cuyos tres criterios bloqueantes nunca se cerraron | **CRÍTICO** (resuelto en este trabajo) |
| **H3** | `portfolio_walkforward_temporal.py:38` + `portfolio_bateria.py:54-69` | metodología estadística | **sí** | A la lectura de los **DSR por tramo** de la reevaluación. No al veredicto global ni a P1 | **MEDIO** |
| **H4** | `rigor_estadistico.py:188-190` | sesgo de selección en el benchmark | **sí**, medido | A la comparación con benchmark de Fase A. Dirección conservadora (en contra de las estrategias) | **MEDIO** |
| **H5** | `verificar_a5_indicadores.py:8`, `verificar_a8_adversarial.py:8`, `run_backtest.py:20-24` | reproducibilidad de la suite | **sí** | A ninguno directamente; hacía la suite no congelada | **ALTO** |
| **H6** | `fix-fase2/data/btc_usd_5y_1d.csv` | integridad de datos | **sí** | A Fase A: su único insumo es el único de los 36 CSV sin `.sha256` ni `.meta.json` | **MEDIO** |
| **H7** | `portfolio_supervivencia.py:57` | reproducibilidad / datos | **sí** | Igual que H1, en el módulo de supervivencia. No parcheado (fuera de alcance) | **ALTO** |
| **H8** | `portfolio_runner.py:246` vs `:229` | asimetría de información | **sí**, medido | A ninguno: 10 decisiones de 44.030 (0,023%), +0.0041 de Sharpe en el benchmark | **BAJO** |
| **H9** | `potencia_fase_b.py:4,25-28` | etiqueta | **sí** | A ninguno. Se presenta como potencia "A PRIORI" y cablea `T_EFF`, `SKEW`, `KURT`, `V` tomados del run ya observado | **BAJO** |
| **H10** | `portfolio_bateria.py:54-69` + `potencia_fase_b.py:28` | metodología estadística | **sí**, medido | **Al número central del expediente.** El listón pasa de 1.312 a 0.823 según cómo se construya `V`, y el Sharpe observado (1.008) cae entre los dos. La brecha +0.304 no es robusta | **CRÍTICO** |
| **H11** | ausencia de corrección en Fase B frente a `rigor_estadistico.py:185-209` | benchmark no igualado | **sí**, medido | Al "pierde vs B&H" de Fase B: medido a igual exposición pierde por 0.063 en vez de 0.156. Fase A sí aplicó esta corrección; Fase B la omitió | **ALTO** |
| **H12** | `timesfm_fase2_resultado.md:6` vs `portfolio_bateria.py:35` | contabilidad de `N` | **sí** | A la aritmética de todo el expediente: con N=14 el listón es 1.349 y la brecha +0.341. **Contradicción abierta, no reconciliada** | **ALTO** |

Lo que **no** se encontró, declarado como tal: ningún look-ahead, ningún coste
mal modelado, ninguna doble contabilización, ningún no-determinismo, ninguna
discrepancia entre código y resultados publicados en Fase A ni en Fase B.

---

## 3. La prueba de cada hallazgo

### H1 — el loader no alcanzaba los datos congelados
`portfolio_runner.py:122` componía el nombre del CSV con `datetime.now()`. Los
congelados llevan sello `20261007` / `20261009`; hoy es otro día.

```
$ ls fix-fase2/data/multi/*.csv | sed 's/.*_\([0-9]\{8\}\)\.csv/\1/' | sort -u
20261007
20261009
$ date -u +%Y%m%d
20261101
```

Prueba empírica, con los 20 CSV verificados delante:

```
$ ls data/multi/*.csv | wc -l
20
$ python3 -c "... load_or_download() ..."
Failed to get ticker 'BTC-USD' reason: ... CONNECT tunnel failed, response 403 ...
EXCEPCION: IndexError index 0 is out of bounds for axis 0 with size 0
```

Los ignora y va a la red. **Parcheado** (paso 3.0): sello explícito,
verificación del `.sha256` de al lado, fallo en duro si falta, descarga
prohibida salvo `PERMITIR_DESCARGA=1`.

```
$ python3 -c "from portfolio_runner import load_or_download; load_or_download()"
faltan 10 CSV congelados con sello 20261101 en data/multi: [...]
sellos disponibles en ese directorio: ['20261007', '20261009']
La descarga esta PROHIBIDA durante la auditoria.

$ STAMP_CONGELADO=20261009 python3 -c "..."
  BTC-USD     4406 velas  sello 20261009  sha256 af0979202092… [verificado]
  ... (10/10 verificado)
```

### H2 — los tres criterios bloqueantes sin verificador
`fix-fase2/docs/AUDIT_BRIEF.md` (2026-10-05) marca `AUDIT-A1`, `A2` y `A3`
como los únicos que **bloquean**, y dice: *"Estos números NO son confiables
hasta que A1-A3 estén resueltos."* `brain.py:75-78` lo tiene grabado en el
segundo cerebro.

```
$ ls fix-fase2/verificar_a*.py
fix-fase2/verificar_a4_a7_cierre.py
fix-fase2/verificar_a5_indicadores.py
fix-fase2/verificar_a6_metricas.py
fix-fase2/verificar_a8_adversarial.py
$ ls fix-fase2/verificar_a1*.py fix-fase2/verificar_a2*.py fix-fase2/verificar_a3*.py
ls: cannot access ...: No such file or directory  (x3)
```

Los cinco no bloqueantes tenían script. Los tres bloqueantes, ninguno.
**Cerrados** en el paso 3.1 (§4 de este informe).

### H3 — `V` no se puede recalcular por tramo
`SR0 = sqrt(V) · E[max_N]`. `portfolio_walkforward_temporal.py:38` aplica la
misma `V` congelada a los tres tramos. Al intentar recalcularla:

```
  Cobertura temporal de las 12 series que componen V:
    ma_cross                 2024-10-07 -> 2026-10-06  (730 obs)
    ...  (las 11 de Fase A, todas iguales)
    portfolio_fase_b         2014-09-18 -> 2026-10-07  (4403 obs)

  tramo              dias   series con >=30 obs    V del tramo  DSR cableada
  T1_2015-2018       1218                     1  no calculable        0.8244
  T2_2019-2022       1461                     1  no calculable        0.7719
  T3_2023-fin        1376                    12     0.00063995        0.3013
```

Las 11 series de Fase A son el tramo OOS de un CSV de 2021-2026 y **no
solapan** con T1 ni T2. En los dos tramos que sostienen P1, 11 de los 12
intentos no existen. Usar una `V` congelada no es comodidad: es la única
opción. Pero se estima en 2 años y se aplica a tramos que empiezan en 2015.

`V` **sí es reproducible** (diferencia 3.25e-19 con la constante cableada), y
el DSR es **más sensible a `V` que a `N`**:

```
                 V   factor   SR0 diario      DSR
      0.0001755487    x0.25      0.02206   0.9802
      0.0003510974     x0.5      0.03119   0.9258
      0.0007021948     x1.0      0.04412   0.7191
      0.0014043895     x2.0      0.06239   0.2600
```

No se corrige: cambiar `V` después de ver el resultado sería cambiar la
métrica, prohibido por §3.6 y por el OK.

### H4 — el benchmark de exposición igualada está inflado
`rigor_estadistico.py:188-190` selecciona los días de B&H con la **máscara de
posición de la estrategia**. Contraste contra 2000 máscaras aleatorias de la
misma tasa de exposición, semilla 20261101:

```
  variante                 exp %  B&H real  B&H aleat. medio  percentil  estrategia
  ma_cross                   3.8     4.121             0.433      83.5%       4.221
  sma_timing_20             52.4     1.355             0.578      87.9%       1.089
  sma_timing_50             55.1     1.772             0.560      96.5%       1.504
  sma_timing_100            50.8     1.717             0.576      94.5%       1.410
  connors_rsi2               5.2     4.843             0.512      92.2%       4.069
  tsmom_7                   53.2     0.102             0.582      23.5%      -0.354
  ...
  Percentil medio: 71.0% (50% seria seleccion neutra)
```

La máscara selecciona días favorables para B&H. Tiene sentido: son estrategias
de tendencia, están largas cuando el activo sube, y B&H también gana esos
días. Es inherente al diseño del benchmark, no un bug — pero significa que no
es un test limpio de habilidad, y que la comparación de Fase A es **más dura
de lo que debería**. Como el sesgo va en contra de las estrategias y Fase A ya
moría por DSR, bootstrap y t, el dictamen de Fase A sale **reforzado**, no
debilitado.

### H5 — 4 verificadores descargaban en vivo
```
verificar_a5_indicadores.py:8   yf.download("BTC-USD", period="2y", ...)
verificar_a8_adversarial.py:8   yf.download("BTC-USD", period="5y", ...)
run_backtest.py:20-24           load_data() -> yf.download  (lo usan
                                verificar_invariante_h1.py y verificar_opus_fase2.py)
```

Ninguno comprobaba que la descarga trajese filas: fallan con `IndexError`
sobre un DataFrame vacío. Con el origen redirigido al CSV congelado **pasan
4/4** (paso 3.7). La suite efectiva es **20/23**.

### H6 — el CSV de Fase A no tiene ancla de integridad
```
$ find . -name "*btc_usd_5y*" -not -path "./.git/*"
./fix-fase2/data/btc_usd_5y_1d.csv
```
Ni `.sha256` ni `.meta.json`. Es el único de los 36 CSV sin ancla, y es el
único insumo de los 11 dictámenes de Fase A. El único corroborante es el hash
escrito a mano en `rigor_estadistico.py:5`, que **coincide**
(`1c393a0095688754c8e5eeeca222077ca7f03eb493e080b50fc33c03b5dfc725`) — pero un
hash en un comentario vive en el mismo commit que el CSV.

### H7, H8, H9
H7: `portfolio_supervivencia.py:57` repite el defecto de H1. No parcheado por
alcance; el paso 3.6 lo sortea sustituyendo `congelar()` en memoria.

H8: `portfolio_runner.py:246` usa `rets.iloc[:t+1]` para el elegible del
benchmark y `:229` usa `rets[tk].iloc[:t]` para el de la estrategia. Medido:
**10 decisiones divergentes de 44.030** (0,023%), exactamente una por activo
—el día en que cruza el umbral de historia—, y mueve el Sharpe del benchmark
de 1.1644 a 1.1603 (**+0.0041**). Real, inmaterial, y de dirección
conservadora.

H9: `potencia_fase_b.py` se titula potencia *"A PRIORI"* y cablea `T_EFF=4336`,
`SKEW=1.037`, `KURT=31.999`, `V_TRIALS=0.0007021947704551833`, todos tomados
del run ya observado. La aritmética es correcta (reproduce exacto); la etiqueta
es incorrecta: es un cálculo a posteriori con parámetros observados.

---

## 4. Los tres criterios bloqueantes, cerrados

### AUDIT-A1 — look-ahead en fills: **RESUELTO (5/5)**
`fix-fase2/auditoria_n1/paso_3_1_audit_a1_lookahead.py`

La señal de la vela `i` crea un `pending` que se rellena en `open[i+1]`
(`backtester.py:68-71`). Probado: el fill ocurre en `i+1`; el precio es
`open[i+1]·(1+slippage)`; **cambiar `close[i]` por ×1000 no mueve ni la fecha,
ni el precio, ni el tamaño**; una señal en la última vela no abre posición; y
lo mismo en corto.

### AUDIT-A2 — el drawdown idéntico train/test: **EXPLICADO**
`fix-fase2/auditoria_n1/paso_3_1_audit_a2_drawdown.py`

Hipótesis de bug en `compute_metrics`: **descartada 4/4**. Es una función pura,
sin estado, con `cummax` correcto, independiente del orden de llamada
(verificado con drawdown calculado a mano, llamadas cruzadas y repetidas).

Y el `-2.18% / -2.18%` **no se reproduce** desde el CSV congelado:

```
  TRAIN (2021-10-06 -> 2024-10-05, 1096 velas)
    retorno 9.5%  Sharpe 0.53  DD -4.24%  trades 20
    minimo del drawdown el 2022-11-02   dd exacto -4.238861601656479 %
  TEST  (2024-10-06 -> 2026-10-06, 731 velas)
    retorno 7.96% Sharpe 0.8   DD -3.75%  trades 12
    minimo del drawdown el 2025-09-26   dd exacto -3.7539785033150945 %
```

Los DD son distintos, los mínimos caen en fechas distintas y los números de
trade difieren. La coincidencia que `AUDIT_BRIEF.md` §6 reporta venía de una
descarga en vivo de yfinance del 2026-10-05, no de este CSV. No hay bug que
corregir.

### AUDIT-A3 — dimensionalidad de la comisión: **RESUELTO (6/6)**
`fix-fase2/auditoria_n1/paso_3_1_audit_a3_comision.py`

Trade manual con la respuesta calculada aparte, y el backtester coincide a
precisión de float (diferencia 0.000e+00). El coste es
`qty·entrada·c + qty·salida·c`, es decir **comisión por lado sobre el nominal
de cada lado** — que es exactamente lo que `AUDIT-S3` preguntaba. El slippage
entra **una sola vez por lado** (`entrada/open = 1.0005` exacto, no
`1.00100025`). El coste escala **con el nominal, no con el capital**: a medio
nominal, medio coste. Y `commission=0` cambia el pnl en exactamente el coste,
así que no hay doble contabilización escondida en otra parte del bucle.

---

## 5. Look-ahead: la prueba corregida

`fix-fase2/auditoria_n1/paso_3_2_lookahead_invariancia_prefijo.py`

El brief original pedía multiplicar `close[t+1]` por 3. El registro némesis lo
rechazó (B-05): rompe la coherencia OHLC (`close > high`) y podía disparar las
ramas de gap dando un falso positivo; una sola barra solo comprueba un `t`; y
comparar curvas completas da siempre diferencia. Se sustituyó por
**invariancia de prefijo**: para cada `t` de una rejilla se perturban **todas**
las barras `> t` con un paseo multiplicativo de semilla fija que escala los
cuatro precios de cada barra por el mismo factor —conservando
`high ≥ max(o,c)` y `low ≤ min(o,c)`— y se exige bit-identidad en `[0..t]`.

**14/14 estrategias invariantes en 40 valores de `t`**, incluida
`rsi_hidden_divergence`, que usa `_swings_confirmados` con ventana **centrada**
(`strategies.py:168`, `rolling(2*order+1, center=True)`) — el único constructo
no causal por construcción del código, que el brief original no listaba
(B-06). Es causal porque emite la señal con retraso en `conf2 = p + order`.

**La curva del portfolio de Fase B, invariante en 10 valores de `t`**: cubre el
sizing Carver con EWMA de volatilidad (`s2_path[t-1]`), la covarianza EWMA
completa (`cov_path[t-1]`), el momentum (`closes[t-1]`), la elegibilidad
(`rets[:t]`) y el veto de vol de portfolio.

### Cuánto inflaba el look-ahead que AUDIT-S1 denunciaba

Medición controlada, mismo CSV y mismos costes, única diferencia dónde se
rellena la señal:

```
  sesgo medio      -0.025 Sharpe
  |sesgo| medio     0.082 Sharpe
  |sesgo| maximo    0.210 Sharpe  (signo MIXTO: 5 positivos, 9 negativos)
```

**No es material.** La razón, medida:

```
  |gap| medio open[i+1] vs close[i]   0.000195  (0.0195%)
  |retorno| medio                     0.018363
  ratio |gap|/|retorno|               0.011
```

En un mercado 24/7 el cierre de la vela `i` y la apertura de la `i+1` son casi
el mismo precio. `AUDIT-S1` era **estructuralmente correcta** —señal y fill no
deben compartir vela— pero su efecto **numérico** sobre cripto diario es
despreciable.

Consecuencia que hay que decir: **la brecha entre la línea base pre-auditoría
(ma_cross OOS +24.4%, Sharpe 1.63) y la reejecución de hoy (+7.96%, Sharpe
0.80) NO queda explicada por el arreglo del look-ahead.** Tampoco por señales
`exit_*`: `ma_cross` no las tiene. Queda **sin explicar** desde este repo.
*[no verificado]* La causa candidata es que la línea base se calculó sobre una
descarga en vivo del 2026-10-05 y no sobre este CSV: mismo número de velas
(1827) pero ventana desplazada un día y precios sujetos a revisión por
`auto_adjust`. No es comprobable sin esos datos, que no están en el repo.

---

## 5-bis. El número central del expediente no es robusto (3.0c y 3.0d)

Pasos añadidos por Pablo el 2026-11-01 a partir de la némesis de N2 (rama
`nube/s2-literatura`, objeciones **B1** y **B3**). Son de cómputo, sin red, sin
datos nuevos y **sin gastar un trial**: `N` sigue en 12 en ambos.

### 3.0c — `V` con `T` homogéneo
`fix-fase2/auditoria_n1/paso_3_0c_v_con_t_homogeneo.py`

N2 observó que `SR₀ = √V·E[max_N]` usa una `V` estimada sobre 11 trials con
`n_obs_eff` entre 598 y 2188 y la aplica a un estadístico medido con
`T_eff = 4336`.

**Diagnóstico (parte A).** Confirmado y **matizado**: la dispersión observada
no solo cae dentro del ruido muestral, es **menor** que el ruido medio de
estimación.

```
  var observada 0.00070217  vs  ruido medio 0.00133815
  ratio 0.525
  var_verdadera estimada = -0.0006359790  -> NEGATIVA
```

Bajo un modelo de errores independientes la dispersión verdadera entre reglas
se estima en **cero**. Pero ese modelo no se sostiene y es el matiz que N2 no
incluyó: las 11 reglas corren sobre **la misma serie de precios de BTC**, en el
mismo tramo OOS, así que sus errores están fuertemente correlacionados y la
varianza entre ellas puede ser mucho menor que la suma de ruidos
independientes. De ahí el ratio 0.525 < 1. El reescalado `V·843/4336` que N2
propone es **un** modelo posible, no el correcto.

**Medición (partes B–D).** Se replicó el bucle del portfolio con la regla
desacoplada y **la réplica reproduce Fase B con diferencia 0.0e+00** punto a
punto en la equity — sin esa validación nada de lo demás valdría. Después se
midieron las 11 reglas de Fase A sobre el mismo panel (10 activos, 12 años,
misma maquinaria Carver + cov EWMA + mismos costes), con un control
anti-colapso que aborta si dos trials dan el mismo Sharpe:

```
  T_eff de los 12 trials: min 3850 max 5695 ratio 1.48
  (antes: min 598 max 4336 ratio 7.25)

                                    V vieja        V nueva
  SR0 diario                        0.04412        0.01850
  liston Sharpe DSR>=0.95             1.312          0.823
  Sharpe observado                    1.008          1.008
  brecha                             +0.304         -0.185
  DSR de Fase B                      0.7190         0.9891
  ¿DSR >= 0.95?                          no             SI
```

**El sesgo que corta en contra (parte E).** No se puede quedar con el 0.823 sin
más, por dos razones medidas:

```
  familia de trials                       min      max        sd    rango
  Fase A single-asset + Fase B         -0.298    1.116     0.506    1.415
  11 reglas sobre el panel + Fase B     0.535    1.267     0.212    0.733
  negativos en la familia                   3        0
```

1. Los 12 trials nuevos pasan **todos** por la misma maquinaria de
   vol-targeting al 10%, que los comprime hacia un mismo perfil de riesgo:
   ninguno queda negativo y la sd cae de 0.506 a 0.212. Parte de la caída de
   `V` no es "quitar ruido de muestras cortas".
2. En Bailey-LdP, `V` es la dispersión entre los intentos **que de verdad se
   probaron**. La búsqueda real fue 11 reglas sobre BTC solo y después una
   regla de portfolio. Medir esas 11 sobre el panel describe una familia de
   intentos que **nunca se buscó**.

```
  construccion de V                                    V    liston      DSR
  la del expediente (T heterogeneo)           0.00070219     1.312   0.7190
  T homogeneo sobre el panel (3.0c)           0.00012351     0.823   0.9891
  reescalado de N2 (V·843/4336)               0.00013652     0.842   0.9872
```

**El hallazgo, por encima de la dirección (H10):** el listón se mueve entre
**0.823 y 1.312** según una elección metodológica defendible que nadie había
hecho explícita, y el Sharpe observado (1.008) **cae en medio**. La cifra 1.312
—y con ella la brecha +0.304 de la que cuelgan el expediente entero, los tres
briefs y la premisa "solo quedan dos salidas"— **no es robusta**. Eso vale
cualquiera de las dos construcciones que se prefiera. Lo que queda establecido
es que **la brecha no es fiable**, no que sea cero.

*[no verificado]* Que Bailey-LdP exija `T` homogéneo entre trials para que `V`
sea comparable no se pudo comprobar contra SSRN 2460551 desde esta sesión
(sin acceso). Se mantiene la etiqueta que N2 le puso.

### 3.0d — benchmark de exposición igualada sobre Fase B
`fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py`

Fase B está al **15,6%** de exposición media y se compara contra un B&H **100%
invertido**. Fase A sí aplicó la corrección (`rigor_estadistico.py:185-209`) y
fue esa medición la que mató a `sma_timing_50/100`. **B3 de N2 es correcta: en
Fase B se omitió.**

```
  serie                                         Sharpe    Calmar  exp. media
  Fase B (con costes)                            1.008     0.978       0.156
  B&H 100% invertido (el publicado)              1.164   123.754       1.000
  B&H a IGUAL exposicion                         1.071     1.144       0.156

  Fase B vs B&H 100%          -0.156  (pierde) <- el par publicado
  Fase B vs B&H igualado      -0.063  (pierde) <- la comparacion justa
```

**Fase B sigue perdiendo, pero por 0.063 en vez de 0.156.** El dictamen se
sostiene por el lado del benchmark, y ahora por la razón correcta en vez de por
una comparación no igualada. Contra lo que B3 temía, la corrección **no**
convierte a Fase B en "el mismo cadáver que `sma_timing_50` con otro nombre".

Se verificó el matiz de N2 sobre la invariancia de escala: el Sharpe del B&H
×0.5, ×1 y ×2 es idéntico (1.164). Lo que mueve el Sharpe es escalar por un
camino de exposición **variable en el tiempo**, que es de lo que va la
corrección. Y el test de selección (objeción B-09 del registro némesis): el
camino real queda a **+0.62 sd** de la media de 2000 permutaciones del propio
camino (percentil 73,6%) — si hay sesgo va en contra de la estrategia, y a esa
distancia no se distingue del ruido.

### La palanca `T` está cerrada (dato de N3, no recalculado aquí)

Por indicación de Pablo, y para no recalcularlo: N3 (`nube/s3-datos`) demostró
que el estadístico `t` es **exactamente invariante** a la frecuencia de muestreo
(delta 0.000000 verificado), que el umbral DSR **sube** al pasar a horario
(1.312 → 1.317…1.325) y que cerrar la brecha por ventana de calendario exigiría
**~96 años** de historia. **Este informe no propone más datos como salida.**

## 6. Costes

`fix-fase2/auditoria_n1/paso_3_3_costes.py`

El agregado que `results/portfolio_runner.json` no guarda:

```
  dias simulados                     4404
  dias con rebalanceo (turnover>0)   3322  (75.4% de los dias)
  turnover total (suma de |dw|)      67.6
  coste acumulado                    9.64% de la equity
  contrafactual sin costes: retorno 317.52% -> 362.06%, Sharpe 1.008 -> 1.075
```

**El coste de rebalanceo se cobra.** El miedo del brief original —"rebalancea
10 activos a diario durante 4404 días y no paga esos ajustes"— no se cumple.

Sensibilidad, contra los umbrales que el expediente **ya tenía fijados**
(`potencia_fase_b.json`: Sharpe 0.870 para t>3; 1.312 para DSR≥0.95 con N=12):

```
   mult   retorno %   Sharpe       t     DSR  coste acum %
     x1      317.52    1.008    3.48   0.719          9.64
     x2      277.26    0.941    3.24   0.635         18.36
     x5      178.28    0.739    2.55   0.358         39.78
    x10       67.53    0.403    1.39   0.063         63.75
```

Barrido fino: el umbral de **t>3 se cruza entre ×3 y ×4**, y el **retorno se
vuelve negativo entre ×15 y ×20**. Con costes ×2 el Sharpe baja a 0.941 y
sigue por encima del umbral de t>3.

**El edge no es una ilusión de fricción barata: resiste duplicar los costes.**

*Límite declarado:* el modelo de fricción es proporcional al turnover, sin
impacto de mercado ni profundidad de libro. Un ×10 no es lo mismo que operar
size grande en un activo ilíquido.

---

## 7. El DSR como función de N

`fix-fase2/auditoria_n1/paso_3_4_dsr_funcion_de_n_y_v.py`

**Contradicción abierta sobre `N` (N2 · B2, sin reconciliar).**
`timesfm_fase2_resultado.md:6` declara **N=14** registrado antes del primer
forecast (2026-10-12/13); el código y la reevaluación del 2026-10-09 usan **12**.
Nadie lo ha reconciliado y esta tarea no lo arregla. Con N=14 el listón es
**1.349** y la brecha **+0.341** en lugar de +0.304.

**`N=12` es una [ASUNCIÓN NO VERIFICABLE].** `N` en Bailey-LdP cuenta
configuraciones **probadas**, no publicadas. El repo solo registra las
publicadas. Cualquier parámetro tanteado mirando un resultado (`LAMBDA` 0.94,
`SIGMA_TARGET` 0.10, `W_MAX` 0.2, `VOL_TOPE_MULT` 1.25, `LOOKBACK` 365) sube
`N`. Está **contado de forma consistente** en los cuatro módulos de Fase B
(11 variantes de Fase A + la regla de portfolio), pero consistente no es lo
mismo que correcto.

```
      N   SR0 diario      DSR   Sharpe min DSR>=0.95  ¿DSR>=0.95?
      1      0.00000   0.9998                  0.472           SI
      2      0.01377   0.9955                  0.734           SI
      3      0.02260   0.9784                  0.901           SI
      4      0.02788   0.9523                  1.002           SI
      5      0.03160   0.9219                  1.073           no
      8      0.03866   0.8278                  1.208           no
     12      0.04412   0.7191                  1.312           no <-- N del expediente
     20      0.05037   0.5642                  1.431           no
     30      0.05494   0.4425                  1.519           no
     50      0.06032   0.3069                  1.622           no
    100      0.06706   0.1695                  1.751           no
```

**`N` máximo para el que el Sharpe observado (1.008) aún da DSR ≥ 0.95: N = 4.**

Es decir: el dictamen "no alcanza DSR 0.95" **se sostiene para cualquier
N ≥ 5**, y solo se revertiría si los intentos reales hubiesen sido ≤ 4. La
conclusión **no es frágil al alza de N** —subirlo solo la refuerza— y a la baja
es implausible: el repo documenta 11 variantes más la regla de portfolio.

### ¿A partir de qué N "SEÑAL DÉBIL" pasaría a "MUERTA"?

Respuesta explícita, leída de los criterios del propio expediente: **no existe
ninguno.** `MUERTA` está definida por el fallo de P1 o P3. P1 se decide por
IC95 del retorno (*"≥2 de 3 tramos con IC95 positivo y ningún tramo con IC
claramente negativo"*, `portfolio_walkforward_temporal.py:66-74`); P3 por t>3,
IC positivo y comparación con B&H. **Ninguno depende de `N`.** El DSR no entra
en P1 ni en P3.

Lo que `N` sí hace es alejar la señal de ACTIVABLE:

```
    N=12   DSR 0.7191   brecha de Sharpe hasta 0.95: +0.303
    N=20   DSR 0.5642   brecha: +0.423
    N=30   DSR 0.4425   brecha: +0.511
    N=50   DSR 0.3069   brecha: +0.614
```

Cada variante nueva que se pruebe encarece el umbral.

---

## 8. Correspondencia entre las dos numeraciones

Decisión de Pablo (§8). `AUDIT-S*`/`AUDIT-A*` son del `AUDIT_BRIEF.md`
(2026-10-05); los pasos son de esta auditoría N1.

| Criterio previo | Qué era | ¿Bloqueaba? | Dónde se cierra en N1 | Resultado |
|---|---|---|---|---|
| `AUDIT-S1` / `AUDIT-A1` | look-ahead en fills | **SÍ** | 3.1 (`audit_a1`) + 3.2 | **RESUELTO** 5/5, y cuantificado |
| `AUDIT-S2` / `AUDIT-A2` | drawdown idéntico train/test | **SÍ** | 3.1 (`audit_a2`) | **EXPLICADO**, sin bug |
| `AUDIT-S3` / `AUDIT-A3` | comisión mal aplicada | **SÍ** | 3.1 (`audit_a3`) | **RESUELTO** 6/6 |
| `AUDIT-S4` / `AUDIT-A4` | salidas intravela | no | ya cubierto por `verificar_a4_a7_cierre.py` | PASS |
| `AUDIT-A5` | indicadores vs referencia | no | `verificar_a5_indicadores.py`, recuperado en 3.7 | PASS (12 indicadores, dif. máx 1.4e-08) |
| `AUDIT-A6` | métricas a mano | no | `verificar_a6_metricas.py` | PASS |
| `AUDIT-A7` | resultados post-fix reejecutados | no | 3.0b / 3.0b-bis | PASS, 245/245 y exacto |
| `AUDIT-A8` | adversarial coin-flip ≈ 0 menos costes | no | `verificar_a8_adversarial.py`, recuperado en 3.7 | PASS (30 semillas: retorno medio −22.9%, Sharpe −0.454, t −5.19) |
| `AUDIT-S5` | walk-forward sin optimización | no | no auditado | fuera de alcance |
| `AUDIT-S6` | datos yfinance y reproducibilidad | no | H1, H5, H6, H7 | **cuatro hallazgos** |

`brain.py:75-78` dice *"NO FIABLE hasta resolver S1 (look-ahead) y S3
(comisión)"*. Esos son `AUDIT-S1` y `AUDIT-S3`, y **ambos quedan resueltos**.
La nota está obsoleta; no se tocó por alcance.

---

## 9. Límites de esta auditoría

Una auditoría que no encuentra nada y no declara sus límites no es una
auditoría. Esta encontró nueve cosas, y estos son sus límites:

1. **TimesFM no se reprodujo.** Falta `torch` y `timesfm`. El dictamen
   "MUERTA" queda sin verificar por reproducción.
2. **La invariancia de prefijo se probó en una rejilla**, no en todas las
   barras: 40 valores de `t` en single-asset, 10 en el portfolio. Un
   look-ahead que solo actuase en una `t` no probada escaparía.
3. **La fecha real de listado de FIL no es comprobable** sin fuente externa.
   Ninguna de las tres firmas de backfill buscadas (volumen cero, precios
   constantes, sigma inicial anómala) aparece en los 15 activos.
4. **El sesgo residual del universo de caídos solo está acotado por un lado.**
   Se midió la sensibilidad a **quitar** caídos (P3 resiste quitar cualquiera
   de los cinco: Sharpe entre 0.916 y 0.955, t>3 e IC positivo en los 6
   universos). No se puede medir el efecto de los caídos que **nunca entraron**
   en la lista: el universo completo de 2017 sigue sin construirse, y eso
   necesita datos nuevos (tarea N3).
5. **La procedencia del código sigue sin cerrarse *a priori*.** Esta auditoría
   la cerró *a posteriori*, reproduciendo las cifras. Pero los `.py` no tienen
   hash, ni historia previa a `d34b147`, ni los `results/*.json` registran el
   commit que los generó. La próxima auditoría tendrá el mismo problema.
6. **El camino de paper trading no se auditó.** `risk_veto.py`,
   `paper_runner.py` y `deliberation.py` no están en la ruta del backtest
   —verificado— y no contribuyeron a ninguno de los cuatro dictámenes.
7. **El modelo de fricción no tiene impacto de mercado.** La sensibilidad ×N
   multiplica una tasa proporcional, no simula profundidad de libro.
8. **La brecha de la línea base pre-auditoría (1.63 vs 0.80) queda sin
   explicar** desde este repo. *[no verificado]*
9. **No se resuelve cuál es la `V` correcta.** 3.0c establece que el listón no
   es robusto a esa elección y mide las dos construcciones; decidir cuál vale
   es una decisión metodológica de Pablo, no un resultado de esta auditoría. Y
   cambiarla después de ver el resultado sería cambiar la métrica, prohibido.
10. **No se reconcilia `N`=12 frente a `N`=14.** Queda anotado como
   contradicción abierta, con el listón de ambos.

---

## 10. Lo que no se hizo, y por qué

Por el alcance de escrituras que fija el §8 (`fix-fase2/auditoria_n1/`, los dos
documentos, y el parche de `portfolio_runner.py`):

- **No se repuntaron permanentemente los 4 verificadores de red** (H5). El
  paso 3.7 demuestra que pasan 4/4 con el CSV congelado redirigiendo
  `yfinance.download` en memoria, sin editar esos ficheros. Hacerlo permanente
  exige editarlos y editar `load_data()` de `run_backtest.py`. **Propuesto.**
- **No se parcheó `portfolio_supervivencia.congelar()`** (H7). El paso 3.6 lo
  sortea sustituyéndolo en memoria. **Propuesto.**
- **No se reconstruyó `portfolio_resultado.md`** — decisión expresa de Pablo.
  Queda constancia de que el documento primario del dictamen de Fase B no
  existe ni existió, y que sus cifras solo son recuperables de
  `fase_b_reevaluacion_resultado.md` y `results/portfolio_runner.json`.
- **No se tocó ninguna métrica, umbral ni criterio.** Todos los umbrales
  usados (0.870 para t>3, 1.312 para DSR≥0.95, N=12, V) son los que el
  expediente ya tenía publicados. Donde se encontró una elección metodológica
  discutible (H3, H4, H9) se documentó como hallazgo y **no se sustituyó**.
- **No se modificó ningún `.csv`, `.sha256` ni `.meta.json`.** Las
  reejecuciones corrieron en sandbox o con `simulate()` en memoria, sin
  sobrescribir `fix-fase2/results/`.
- **No se ejecutó nada contra el VPS ni contra dinero real.** Ninguna conexión
  a ningún exchange.

---

## 11. Cómo reproducir esto

Sin red, con los CSV congelados del repo. Ninguno pasa de 20 minutos; el más
largo es 3.2 (~150 s).

```bash
cd fix-fase2
python3 auditoria_n1/paso_3_0b_reproducibilidad.py
python3 auditoria_n1/paso_3_0b_bis_reproducibilidad_fase_b.py
python3 auditoria_n1/paso_3_0c_v_con_t_homogeneo.py
python3 auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py
python3 auditoria_n1/paso_3_1_audit_a1_lookahead.py
python3 auditoria_n1/paso_3_1_audit_a2_drawdown.py
python3 auditoria_n1/paso_3_1_audit_a3_comision.py
python3 auditoria_n1/paso_3_2_lookahead_invariancia_prefijo.py
python3 auditoria_n1/paso_3_3_costes.py
python3 auditoria_n1/paso_3_4_dsr_funcion_de_n_y_v.py
python3 auditoria_n1/paso_3_5_simetria_benchmark.py
python3 auditoria_n1/paso_3_6_supervivencia.py
python3 auditoria_n1/paso_3_7_verificadores_sin_red.py
```

`paso_3_0b` devuelve código de salida 1 si el harness deja de reproducir
`results/rigor_estadistico.json`. Es la condición de parada: si algún día
falla, nada de lo demás significa nada.
