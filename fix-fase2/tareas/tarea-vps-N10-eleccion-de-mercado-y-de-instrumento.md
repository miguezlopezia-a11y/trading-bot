# Tarea N10 (VPS) — En qué mercado y con qué instrumento se gana dinero: la criba antes de construir nada

**Ejecutor previsto:** Kimi, en el VPS. **Entorno:** `/root/.worktrees/trading-bot-n10`.
**Rama:** `task/n10-eleccion-de-mercado`, cortada de `fase-b-recuperada`.
**Fase 0 obligatoria. El Alcance (§5) NO se ejecuta sin el OK escrito de Pablo en la §8.**

## Qué entrega esta tarea, y en qué unidad

Dos cosas, y ninguna es un dictamen:

1. **Una tabla ordenada** de 18 mercados reales, cada uno con: cuánta memoria tiene su
   serie de precios (medida, no opinada), cuánto cuesta operarlo, qué capital mínimo
   pide, su peor caída histórica y cuánto tardó en recuperarla, y su exceso neto sobre
   la alternativa accesible —un ETF mundial y un depósito al tipo del BCE— **después de
   comisiones y después del IRPF del ahorro español**.
2. **Un plan de acción de tres pasos** para el mercado que gane esa tabla, con el
   criterio que lo mata y en cuántas horas se sabe.

**Lo que NO entrega:** una estrategia, un backtest, un Sharpe, ni un retorno esperado.
Esta tarea elige el terreno. Lo que se construya encima es otra tarea.

## Lecturas previas obligatorias, en este orden

1. **§1 de este archivo.** El error que corrige. Sin eso, lo demás parece burocracia.
2. **`fix-fase2/tareas/tarea-nube-N5-reconocimiento-de-datos-y-potencia-a-priori.md`,
   objeción B-c.** Refutó que «no depende de predecir» baje ningún listón, y que las
   colas gordas lo bajen: lo **suben**. Si esta tarea reintroduce ese error, no vale nada.
3. **`fix-fase2/tareas/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md`,
   su registro némesis y la crítica de su Maker/Verifier.** N9 midió una renta y la
   presentó sin la tasa sin riesgo al lado: parecía un 2,66 % de retorno y era un
   empate con el banco. Y su cuenta mezclaba el funding de un exchange con las
   comisiones de otro. Los dos son errores de **unidad y de coherencia**, no de cálculo.
4. **`fix-fase2/tareas/tarea-nube-N7-benchmark-de-exposicion-igualada.md`, resumen
   ejecutivo.** Pidió medir algo que ya estaba publicado el día anterior. De ahí sale
   el Paso A-1 de esta tarea: antes de medir, comprobar si ya está medido.

---

## 1. El error que corrige esta tarea

En `fix-fase2/src/portfolio_runner.py:3-20` hay un panel de diez criptomonedas y un
docstring que dice *«Plan aprobado (tarea rigor estadistico, Fase 0, 2026-10-07)»*.

**Ese plan no existe como archivo en el repositorio.** Se verificó en N6. Y **por qué
esos diez activos no está escrito en ninguna parte**: la línea `ACTIVOS = [...]` no
tiene una sola palabra de criterio al lado, y es la decisión con más grados de libertad
de todo el expediente.

Nueve tareas —S1, S2, S3, N1 a N7, N9— han discutido si la estrategia supera al ruido,
qué `N` corresponde, si el holdout es legítimo y si el listón del DSR está bien
calculado. **Ninguna preguntó si el mercado elegido es el mercado donde hay algo que
coger.** Se optimizó dentro de una elección que nadie justificó por escrito.

Esta tarea invierte el orden: primero el terreno, con criterio escrito antes de ver los
datos; después la herramienta.

### Lo que esta tarea NO afirma, y por qué importa

- **No afirma que cripto sea mala.** Puede ganar la tabla. Lo que no vale es que gane
  por defecto, que es como entró.
- **No afirma que exista un mercado «predecible».** Afirma que la memoria de una serie
  **se mide** —autocorrelación, ratio de varianza, persistencia de la volatilidad— y
  que esa medición no se había hecho.
- **No afirma que medir memoria sea medir rentabilidad.** Un mercado con memoria puede
  ser inexplotable si el coste de operarlo se la come. Por eso el coste va en la misma
  tabla y no en un apéndice.

---

## 2. Hechos verificados por mí vía SSH el 2026-11-03, entre las 17:05 y las 17:12 UTC

Los comandos están pegados. **Tú los reverificas con comandos propios en el Paso A**;
no los des por buenos porque estén aquí.

### 2.1 La fuente que sirve: Yahoo Finance v8, sin clave, y cubre todas las clases de activo

```
yahoo_sp500      http=200  bytes=261269  {"chart":{"result":[{"meta":{"currency":"USD","symbol":"^GSPC",...
yahoo_oro_fut    http=200  bytes=239898  {"chart":{"result":[{"meta":{"currency":"USD","symbol":"GC=F",...
```

Endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/<ticker>`.
**Requiere cabecera `User-Agent` de navegador**; sin ella puede responder 429.

### 2.2 El detalle que decide si hay datos o no: `range=max` MIENTE

`range=max&interval=1d` **no devuelve diario**: Yahoo degrada la granularidad al rango.
Medido sobre el mismo ticker, la misma hora:

```
^GSPC   range=max&interval=1d        velas=   169   1984-12-01 -> 2026-11-03
^GSPC   range=10y&interval=1d        velas=  2513   2016-11-03 -> 2026-11-03
^GSPC   period1=0&period2=hoy&1d     velas= 14332   1970-01-02 -> 2026-11-03
```

**La forma correcta es `period1=0&period2=<epoch de hoy>&interval=1d`.** Con eso el
S&P 500 da **14.332 días desde 1970-01-02**, que son **3,3 veces** el `T_eff = 4336`
sobre el que se ha discutido nueve tareas. Quien pida `range=max` y cuente 169 filas
concluirá que no hay datos, y la conclusión será falsa.

Más historia disponible, medida igual:

```
BTC-EUR   velas= 4431   2014-09-17 -> 2026-11-03
GC=F      velas= 6653   2000-08-30 -> 2026-11-03
^VIX      velas= 9611   1990-01-02 -> 2026-11-03
EURUSD=X  velas= 5982   2003-12-01 -> 2026-11-03
```

### 2.3 El universo que responde, con su historia y su moneda

Las 18 series respondieron 200 desde el VPS. La tabla da la primera fecha a resolución
degradada; la historia real en diario se obtiene con `period1=0` (§2.2).

| Clase | Ticker | Desde | Moneda |
|---|---|---|---|
| Acciones EEUU | `^GSPC` | 1970 (diario) | USD |
| Acciones Europa | `^STOXX50E` | 2007 | EUR |
| Acciones España | `^IBEX` | 1993 | EUR |
| Acciones emergentes | `EEM` | 2003 | USD |
| Tipo del bono 10 años EEUU | `^TNX` | 1985 | USD |
| Bono EEUU 7-10 años | `IEF` | 2002 | USD |
| Bono EEUU 20+ años | `TLT` | 2002 | USD |
| Oro | `GC=F` | 2000 (diario) | USD |
| Petróleo WTI | `CL=F` | 2000 | USD |
| Cobre | `HG=F` | 2000 | USD |
| Materias primas | `DBC` | 2006 | USD |
| EURUSD | `EURUSD=X` | 2003 (diario) | USD |
| USDJPY | `JPY=X` | 1996 | JPY |
| Volatilidad | `^VIX` | 1990 (diario) | USD |
| Bitcoin en euros | `BTC-EUR` | 2014 (diario) | EUR |
| Ether en euros | `ETH-EUR` | 2017 | EUR |
| Inmobiliario EEUU | `VNQ` | 2004 | USD |
| Mundo | `URTH` | 2012 | USD |

### 2.4 Lo que NO llega desde el VPS, medido

```
stooq_sp500   http=200  bytes=796   <!DOCTYPE html>...This site requires JavaScript to verify y
fred_dgs10    http=000  bytes=0
fred_vix      http=000  bytes=0
```

**Stooq está bloqueado** por un muro de JavaScript: responde 200 con 796 bytes de HTML,
no un CSV. **FRED no es alcanzable** (`http=000`), igual que en la nube (N5 · A-1).
Quien use `http=200` como prueba de que una fuente sirve, se equivoca: hay que mirar el
cuerpo. Sí llegan, con 200 y cuerpo bueno: el **BCE** (`data-api.ecb.europa.eu`),
**Binance**, **Bybit** y **Coinbase** (`BTC-EUR`, 21.220 bytes).

### 2.5 El entorno

```
python 3.12.3 numpy 2.5.3 pandas 3.0.6     (/opt/trading-bot/venv/bin/python)
kimi  192482496 bytes  /root/.kimi-code/bin/kimi
/dev/sda1  150G  43G usados  102G libres  30%
```

**No toques** `/opt/trading-bot` (paper runner en producción) ni
`/root/trading-bot-fix-fase2` (no tiene git: un error ahí no se deshace).

---

## 3. El contexto externo, con su etiqueta de fiabilidad

Esto no lo he medido yo: lo he buscado. Cada línea lleva su etiqueta y **el Paso A-6 te
obliga a verificar las dos que deciden el criterio**.

| Hecho | Cifra | Fuente | Etiqueta |
|---|---|---|---|
| Cuentas minoristas de CFD que pierden dinero en la UE | **74 %–89 %** | Advertencia estandarizada obligatoria de ESMA (intervención de producto, 2018, vigente en España por BOE de 2023) | **oficial** |
| Clientes de CFD con pérdidas en España | **82 %** | Estudio CNMV, datos 2015 a sept. 2016 | **oficial** |
| Sharpe del sector profesional de futuros gestionados desde 2000 | **0,56** (S&P 500 TR: 0,51 en la misma ventana) | SG CTA Index, citado en blog de CFM | **secundario, verificar** |
| Retorno anualizado del seguimiento de tendencia profesional 2000-2025 | **4,9 %** con 13,4 % de volatilidad | SG Trend Index, fuente de segunda mano | **secundario, verificar** |
| Anomalías publicadas que no pasan un `t` de 1,96 | **65 %** de 452 | Hou, Xue y Zhang, vía resúmenes | **secundario, verificar** |
| Atenuación fuera de muestra de las que sí pasan | **≈ 36 %** | Harvey y Liu, vía resumen | **secundario, verificar** |
| Retorno anualizado del índice mundial de acciones, ~57 años | **9,43 %**, peor caída **−54 %** | Calculadora de terceros sobre MSCI World | **secundario, verificar** |
| El fondo sistemático con mejor historial está **cerrado a dinero de fuera desde 1993** por **límite de capacidad** | — | Medallion (Renaissance), prensa financiera | **secundario, pero el hecho del cierre es público** |
| IRPF español del ahorro, 2026 | 19 % hasta 6.000 €, 21 % hasta 50.000 €, 23 % hasta 200.000 €, 27 % hasta 300.000 €, **28 % o 30 %** por encima (las fuentes discrepan) | Guías fiscales, no AEAT | **secundario, verificar en AEAT** |

### Por qué estas cifras cambian el criterio, y no son adorno

**El Sharpe 0,56 es la línea que reordena el expediente.** El sector profesional
entero, con equipos de doctores, datos de pago e infraestructura, lleva 26 años
sacando un Sharpe de aproximadamente 0,5 en futuros gestionados. Las nueve tareas de
este expediente han estado exigiendo a una estrategia doméstica que supere un listón
del DSR por encima de **1,0** —y declarando fracaso cuando no lo hacía—. Se medía
contra un estándar que la industria no cumple.

**Y el 74-89 % de ESMA es la otra mitad.** Lo que mata al minorista no es no tener
señal: es el apalancamiento y el coste. Por eso el criterio de la §4 mide coste y
riesgo en la misma tabla que la señal, y no después.

---

## 4. El criterio, fijado AQUÍ y AHORA, antes de ver un solo dato

**Esta sección es el corazón de la tarea y está cerrada.** Si después de ver los datos
quieres cambiar un umbral, **no lo cambias**: lo escribes como hallazgo del Paso B con
su justificación, y lo decide Pablo. Tocar el criterio después de ver los resultados es
exactamente lo que ha invalidado seis de las nueve tareas anteriores.

### 4.1 La vara de medir no es el ruido: es lo que Pablo puede hacer sin bot

Todo mercado se compara contra **las dos alternativas accesibles**, no contra cero y no
contra el azar:

- **El depósito**: tipo de la facilidad de depósito del BCE, **verificado hoy en
  2,500 %** (`data-api.ecb.europa.eu`, serie `FM.D.U2.EUR.4F.KR.DFR.LEV`, observación
  `2026-11-03`).
- **El índice mundial**: `URTH`, comprado y mantenido, en euros.

Un mercado solo entra en el plan si su exceso es positivo **después** de: comisiones de
ida y vuelta, horquilla, cambio de divisa si cotiza fuera del euro, y el **IRPF del
ahorro** del tramo correspondiente.

### 4.2 «Predecible» se mide así, y solo así

Cuatro métricas por serie, sobre retornos logarítmicos diarios:

1. **Autocorrelación de los retornos** a 1, 5, 21 y 63 días, con su intervalo de
   confianza por bootstrap de bloques (bloque 21, B = 10.000, semilla 43 — las mismas
   que usa `fix-fase2/src/rigor_estadistico.py`, para que sean comparables).
2. **Ratio de varianza de Lo-MacKinlay** a 5, 21 y 63 días. Por encima de 1 hay
   tendencia; por debajo, reversión.
3. **Persistencia de la volatilidad**: autocorrelación de `|r|` a 1, 5 y 21 días. Esto
   mide si la calma y la tormenta se agrupan, que es lo único que en cripto se sostuvo.
4. **Estabilidad**: las tres anteriores calculadas en la **primera y la segunda mitad**
   de la muestra, por separado. Una métrica que cambia de signo entre mitades **no
   cuenta como memoria**, cuenta como ruido.

**Umbrales, fijados ahora:** una métrica cuenta como memoria si su IC95 excluye el cero
**en las dos mitades** y **con el mismo signo**. No hay nota, no hay gradación, no hay
«casi». Es binario.

### 4.3 El coste y el acceso, en la misma tabla

Por cada mercado, el instrumento **concreto** con el que un residente en España lo
operaría: ETF UCITS, futuro, CFD, spot de cripto o contado. Y para cada uno: coste de
ida y vuelta en puntos básicos, capital mínimo por operación, horario de mercado, si
exige estar delante, y si el bróker es accesible desde España.

**Un mercado sin instrumento accesible queda fuera de la tabla, tenga la memoria que
tenga.** El `^VIX` no se compra; se compran futuros sobre él, que es otra cosa y tiene
su propio coste de renovación.

**Y una columna más, que ninguna tarea de este expediente ha puesto nunca: el coste de
tener el sistema en pie.** Tokens de los modelos que lo operen, VPS, datos de pago si
hacen falta, en euros al año. Un desk de seis agentes anunciado públicamente declara
**2.400 € al año** de coste operativo sobre una cuenta de **280 €**: el sistema cuesta
ocho veces y media el capital que gestiona. **Regla, fijada ahora:** un mercado cuyo
coste operativo anual supere el **exceso esperado sobre el DFR** no entra en el plan,
por mucha memoria que tenga su serie. Se mide en euros, no en porcentaje.

### 4.4 El riesgo, en la unidad que duele

Peor caída histórica, **cuántos meses tardó en recuperar el máximo anterior**, y la
peor caída en un solo día. Ese segundo número es el que decide si un humano aguanta: el
panel de cripto de este expediente cayó un 88,96 %, y eso es la diferencia entre tener
1.000 € y ver 110 € en pantalla.

### 4.5 La capacidad

Si una ventaja desaparece al meter dinero, no es una ventaja: es una anécdota. Por cada
mercado, el volumen diario medio en euros, y qué fracción de él sería una posición de
10.000 €. **El fondo con mejor historial del mundo está cerrado desde 1993 por esta
razón** y conviene no olvidarlo.

### 4.6 Esta tarea no consume trials, y aquí está por qué

Medir la autocorrelación de una serie de precios **no es backtestear un pronóstico**:
es medir una propiedad estructural del mercado, como medir su volumen o su horquilla.
No se estima ninguna esperanza de beneficio y no se optimiza ninguna regla. Igual que
medir una tarifa de funding en N9, **no sube `N`**, que sigue en **16** tras N6.

**En el momento en que se mida el Sharpe de una regla de entrada, sube `N` para todo el
expediente.** Esta tarea tiene prohibido hacerlo (NO-GO 3 de la §5).

**La trampa que hay que ver:** cribar 18 mercados × 4 métricas × 2 mitades son 144
contrastes. Si de ahí se saca «el mercado que mejor puntúa», eso **sí** es selección
múltiple. Por eso el criterio exige el **mismo signo en las dos mitades** y por eso el
orden de la tabla es por **coste de descartar**, no por puntuación.

---

## 5. Fase 0 (OBLIGATORIA). Cuatro pasos y un verificador

### Paso A — Verificación de hechos (≤ 20 min)

Cada cifra con su comando y la salida pegada. Nada de memoria.

- **A-1 · ¿Está esto medido ya?** Busca en las once ramas del repositorio y en el VPS
  cualquier medición previa de autocorrelación, ratio de varianza o criba de mercados.
  `git log --all --oneline`, `git grep -i` por `autocorr`, `variance_ratio`, `hurst`,
  `mercado`, `universo`. **Si aparece trabajo hecho —no un brief sin ejecutar—, PARA y
  dilo.** Esto es lo que N7 no hizo y le costó la tarea entera.
- **A-2 · La granularidad de la §2.2.** Reproduce las tres llamadas a `^GSPC` y confirma
  o refuta las 14.332 velas desde 1970. Si `range=max` te da 169, está confirmado.
- **A-3 · Las 18 series.** Cuántas velas diarias da cada una con `period1=0`, su primera
  y su última fecha, y **cuántos huecos** tiene cada serie respecto al calendario de su
  mercado. Una serie con huecos sin explicar no entra.
- **A-4 · Lo que no llega.** Reverifica Stooq y FRED. **Mira el cuerpo, no el código
  HTTP**: Stooq responde 200 con un muro de JavaScript.
- **A-5 · El ajuste de los precios.** Comprueba si las series de ETFs y acciones vienen
  ajustadas por dividendos y splits, y si el campo `adjclose` existe. Una serie sin
  ajustar subestima el retorno del índice mundial, que es la vara de medir: ese error
  te invertiría la tabla entera.
- **A-6 · Las dos cifras externas que deciden el criterio.** Verifica en fuente
  primaria: (a) el **DFR del BCE** de hoy, y (b) el **Sharpe del SG CTA Index** desde
  2000, o el dato público más cercano que encuentres. Si no puedes verificar la segunda,
  **dilo y márcala `[no verificado]`** — no la borres, porque el argumento de la §3
  depende de ella y Pablo tiene derecho a saber sobre qué se apoya.

### Paso B — Ataque adversarial (≤ 20 min)

**Mínimo seis objeciones**, cada una con severidad (`CRÍTICO` / `ALTO` / `MEDIO` /
`BAJO`) y **qué cambia** del criterio o del Alcance. Seis son obligatorias:

- **B-0 · «¿Esta tarea es una mierda?»** Ataca la premisa, no los detalles. ¿Un screen
  de mercados sirve de algo, o es el décimo documento de un expediente que no ha ganado
  un euro? ¿El resultado está cantado de antemano —gana el índice mundial y punto— y
  entonces las horas sobran? ¿Esto ya lo hizo S2 con la literatura? **Si tu respuesta
  honesta es que la tarea no tiene sentido, dilo con argumento, no la ejecutes, y pasa
  directo al Paso C.** Esta objeción existe porque en nueve tareas ningún némesis atacó
  nunca la pregunta: solo las cifras.
- **B-1 · La selección múltiple del propio screen.** 144 contrastes. ¿El blindaje de la
  §4.6 —mismo signo en las dos mitades— aguanta? ¿O hace falta además una corrección por
  contrastes múltiples, y entonces cuál?
- **B-2 · Memoria no es dinero.** Una autocorrelación significativa de 0,02 no paga una
  horquilla de 5 puntos básicos. ¿La §4.2 mide algo explotable, o solo algo que existe?
  Pon el número: cuánta autocorrelación hace falta para cubrir el coste de la §4.3.
- **B-3 · Los datos de Yahoo.** Es una fuente gratuita y no contractual: tickers que
  desaparecen, ETFs que no existían al principio de la muestra, precios ajustados
  retroactivamente, y **sesgo de supervivencia** en los ETFs. ¿Cuánto de la tabla
  depende de eso?
- **B-4 · Los impuestos y los costes pueden invertir el ranking.** Un mercado que
  obliga a renovar posiciones genera plusvalías cada año y tributa cada año; comprar y
  mantener difiere el impuesto décadas. A tipos del 19-28 %, eso es más que cualquier
  diferencia de señal que vayas a encontrar. Cuantifícalo.
- **B-5 · Tu propio sesgo.** Ya sabes que cripto perdió en este expediente y que el
  carry empató con el banco. **No busques datos que confirmen lo que ya sabes.** Si
  cripto gana la tabla con el criterio de la §4 aplicado tal como está escrito, lo dices.
- **B-6 · El coste del sistema contra el capital.** Pon el número: cuánto cuesta al año
  operar el mercado que ganaría la tabla —tokens, VPS, datos— y con qué capital mínimo
  ese coste baja del exceso esperado. Si la respuesta es que hacen falta 100.000 € para
  que el sistema se pague a sí mismo, **eso es el hallazgo**, y vale más que la tabla.

### Paso C — Contrapropuesta (≤ 20 min), OBLIGATORIO

Si tumbas esta tarea, **devuelves la tuya**. Entre una y tres candidatas, cada una con:

- el mecanismo económico en una frase —de dónde sale el dinero y quién lo pierde—;
- los datos exactos y si se bajan sin clave desde el VPS;
- el `N` que le toca (`N_vigente + 1`, regla de S2; `N` está en 16);
- **qué la mata rápido y en cuántas horas**;
- por qué es mejor que esta criba;
- y **cuántos euros al año daría con 1.000, 10.000 y 100.000 €**, contra el DFR del
  2,500 % y contra el índice mundial, aunque sea un orden de magnitud declarado como tal.

Ordenadas **por coste de descartarlas**, no por retorno esperado.

**Un registro que concluya «esto tampoco funciona» y pare ahí es una entrega incompleta
y se rechaza.** Si no encuentras nada mejor, defiende esta criba con argumento.

### Paso D — Maker/Verifier, y esta vez EXTERNO

Al terminar los pasos A, B y C, invoca un **segundo agente** que **solo critique tu
registro**. No repite la Fase 0: la revisa.

**El verificador tiene que ser de otro proveedor que tú.** Si ejecutas esta tarea con
Kimi, el verificador es Claude; si la ejecutas con Claude, el verificador es Kimi. Un
modelo revisando su propio trabajo comparte sus puntos ciegos: en nueve tareas, ningún
némesis atacó nunca la premisa de la tarea, solo sus cifras —y por eso existe ahora el
Paso B-0—. **Declara en el registro qué modelo hizo cada papel.** Si no puedes invocar
un modelo distinto, dilo explícitamente y marca la revisión como `[interna]`: no la
presentes como lo que no es.

Historial de este verificador en el expediente, para que calibres: 2 CRÍTICOS en N4;
13 hallazgos con 1 CRÍTICO que **invirtió el veredicto** en N6; **20 con 5 CRÍTICOS en
N7, tres de ellos bloques de salida fabricados**; y **17 con 5 CRÍTICOS en N9, que
tumbaron su titular** al descubrir que la cuenta mezclaba datos de dos exchanges.

Pega su crítica **literal**, respóndela **hallazgo por hallazgo reverificando con
comandos propios** antes de aceptar nada, y aplica las correcciones **en el documento y
en los scripts**. Dile expresamente que juzgue **el Paso C con la misma dureza que el
Paso B**, y que **el criterio de la §4 no se puede haber tocado** después de ver datos.

**Si dices que lo has invocado, su crítica tiene que estar pegada en el archivo.** En N9
el resumen decía «pegada más abajo» y no existía: fue uno de los cinco CRÍTICOS.

### NO-GO de la Fase 0 — binarios, sin grados

Un NO-GO se dispara o no se dispara. No se «dispara parcialmente», no se gradúa, y no
se declara disparado lo que tu propia salida dice que no lo está. A N6 se le reprochó
lo primero; a N7, lo segundo.

1. **A-1 encuentra medición previa ya hecha** de la memoria de estos mercados → PARA.
2. **La fuente de la §2.1 no responde 200 con cuerpo útil** → PARA y dilo. No busques
   una fuente alternativa por tu cuenta: eso cambia el dato del que depende todo.
3. **Se backtestea cualquier regla de entrada o se calcula el Sharpe de cualquier
   señal** → NO-GO. Sube `N` para todo el expediente y esta tarea no tiene permiso.
4. **El criterio de la §4 se modifica después de ver los datos** → NO-GO.
5. **El Paso C no da ni una candidata ni defiende la criba** → entrega incompleta.
6. **B-0 concluye con argumento que la tarea no tiene sentido** → PARA, entrega ese
   argumento y el Paso C. Eso **no** es un fracaso: es la entrega más valiosa posible si
   es verdad, y cierra la vía en una tarde en vez de en un mes.

---

## 6. Alcance (NO EJECUTAR sin OK escrito de Pablo en la §8)

### 6.1 Descargar y congelar

Las 18 series en diario con `period1=0`, a `fix-fase2/data/mercados/`, una por CSV, cada
una con su `.sha256` y su `.meta.json` (ticker, URL exacta, fecha y hora UTC de
descarga, número de velas, primera y última fecha, moneda). **El `sha256` se calcula
sobre el fichero sin la última línea en blanco y se reproduce de forma independiente
antes de citarlo.** Tope: **200 peticiones** y **500 MB**.

### 6.2 Medir

Las cuatro métricas de la §4.2 por serie, en las dos mitades. Un script por métrica, un
JSON de salida por script, y el `rc` de cada ejecución registrado. Sin regla de entrada,
sin Sharpe de señal, sin optimizar un parámetro.

### 6.3 Costear

La tabla de la §4.3 para el instrumento concreto de cada mercado, **con la fuente de
cada comisión congelada** igual que los datos. Una comisión de memoria no vale: en N9
las tres primeras fuentes de comisiones no servían y encontrar una que sirviera costó
25 minutos. Cuéntalos.

### 6.4 Ordenar y elegir

La tabla completa, ordenada por **coste de descartar**, y la elección aplicando el
criterio de la §4 **tal como está escrito**, no como te gustaría que estuviera. Si el
ganador es el índice mundial comprado y mantenido, ese es el resultado y se entrega.

### 6.5 El plan de acción

Tres pasos para el mercado ganador, cada uno con: qué se hace, qué datos necesita, qué
lo mata, en cuántas horas se sabe, y **cuántos euros al año** se espera que dé con
1.000, 10.000 y 100.000 € contra el DFR y contra el índice mundial.

Y tres condiciones que el plan tiene que llevar escritas, vengan de donde vengan las
ideas que lo inspiren:

- **Reglas duras que ningún componente puede doblar**, fijadas antes de operar: tamaño
  máximo por posición, pérdida a la que se corta, y a partir de qué ganancia se protege.
  Números, no criterio.
- **Un registro con la razón de cada decisión**, incluidas las de no hacer nada. El
  pecado original de este expediente es que la elección de diez activos no tiene una
  sola línea de criterio escrita al lado (§1); un sistema que no registra su porqué
  repite ese error todos los días.
- **Un papel que argumenta en contra** antes de cada operación, con un número de razones
  exigido y la operación bloqueada si no se rebaten. La némesis que esta tarea aplica al
  documento, aplicada a cada decisión.

#### La arquitectura, decidida por Pablo el 2026-11-03: reglas primero, modelo al lado

**El camino crítico de cada decisión es código determinista.** Ni una llamada a un
modelo para decidir entrar, salir o dimensionar. Tres razones, y las tres son de dinero:
el coste por operación es **cero**, la latencia es cero, y la misma entrada da siempre
la misma salida —sin eso no se puede auditar por qué el sistema hizo lo que hizo, que es
justo el agujero de la §1—.

**El modelo trabaja al lado, nunca en medio.** Donde no bloquea ni cobra por operación:
construir y revisar el código, hacer de *bear* **en lote** sobre las decisiones del día,
leer noticias o informes que no caben en una regla, y escribir el parte diario. Las dos
capas van juntas para producción; lo que no se mezcla es quién decide.

**Las reglas de riesgo —tamaño máximo, corte de pérdida, protección de ganancia— son
código y solo código.** Ningún modelo las puede doblar, ni «explicar» por qué esta vez
no aplican. Esa es la regla que el desk de seis agentes anunciado públicamente dice
tener, y la única parte de él que merece copiarse.

**Vía de escape, para que esto no sea dogma:** si al medir aparece una decisión concreta
que mejora con un modelo en caliente, se cuantifica **en euros por operación** lo que
cuesta y lo que aporta, y entra solo si se paga a sí misma. Nunca porque sea más lista.

### Límites de escritura

- Escribes **solo** en `fix-fase2/data/mercados/`, `fix-fase2/fase0_n10/` y en este
  archivo. Nada más.
- **Cero credenciales.** Solo endpoints públicos. No crees cuentas, no firmes
  peticiones, no operes, no abras ninguna posición real.
- No toques `/opt/trading-bot` ni `/root/trading-bot-fix-fase2`.
- Rama `task/n10-eleccion-de-mercado`, PR contra **`fase-b-recuperada`**, nunca contra
  `main`.
- Si algo no cuadra o no encuentras un archivo: **para y dilo**. Nunca «sigue como
  puedas»: improvisar sobre un documento no encontrado ya costó once archivos borrados
  una vez.

---

## 7. Entregables

1. `## Registro de revisión némesis` al final de este archivo: Pasos A, B, C, la crítica
   literal del Maker/Verifier y tus respuestas.
2. `fix-fase2/fase0_n10/` con un script por medición y su salida.
3. La tabla de la §6.4 y el plan de la §6.5, dentro del registro.
4. Rama empujada y **PR abierto** contra `fase-b-recuperada`. Si no hay PR, no hay
   entrega: en N9 el trabajo se quedó en un solo clon del VPS y no existía en GitHub.

---

## 8. Estado de la tarea

| Fase | Estado |
|---|---|
| Fase 0 — Paso A | [pendiente] |
| Fase 0 — Paso B | [pendiente] |
| Fase 0 — Paso C | [pendiente] |
| Fase 0 — Maker/Verifier | [pendiente] |
| Alcance §6 | **[bloqueado: necesita el OK escrito de Pablo aquí]** |

**OK de Pablo para el Alcance:** _(sin firmar. Enumerar qué pasos se autorizan.)_

---

## Checklist de entrega

- [ ] **Sintaxis y comandos:** cada snippet probado en shell antes de pegarlo; el
  `User-Agent` incluido en toda llamada a Yahoo; umbrales con margen, nunca un valor
  medido hoy.
- [ ] **Datos citados:** todo `sha256` con su normalización declarada y reproducido de
  forma independiente; los JSON leídos con un parser, no con `grep`.
- [ ] **Coherencia interna:** si un paso dice «después de X», su posición lo refleja.
- [ ] **Mecánica de la plataforma:** la degradación de granularidad de Yahoo (§2.2)
  verificada en vivo, no asumida; enumeradas todas las firmas de fallo de una fuente
  (200 con cuerpo HTML, 429, 000).
- [ ] **Decisiones bajo presión:** cada NO-GO con su consecuencia explícita; ningún
  «usar criterio» sin número.
- [ ] **Continuidad:** si la sesión cae a mitad, el registro ya pegado basta para que
  otro continúe.
- [ ] **Rutas y reversibilidad:** todo lo escrito está bajo las tres rutas permitidas y
  en una rama propia; nada fuera del repositorio.
- [ ] **Sincronía entre documentos:** cada corrección nombra su documento destino, y
  tras aplicar un lote se relee el archivo entero buscando el mismo error en otro sitio.
- [ ] **Componentes inactivos:** una fuente que responde 200 no está viva; se comprueba
  el cuerpo (§2.4).

**Categorías del checklist que no aplican y por qué:** *hot-reload* y *reinicio de
máquina* — esta tarea no toca ningún servicio ni proceso en marcha, solo descarga
ficheros y los mide. *Vigilancia programada* — la tarea no deja nada corriendo que
haya que observar después.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
