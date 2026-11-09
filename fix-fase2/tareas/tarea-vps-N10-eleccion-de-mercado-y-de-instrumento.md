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

---

## Registro de revisión némesis

**Fecha:** 2026-11-06. **Ejecutor:** Kimi, en el worktree `task/n10-eleccion-de-mercado`.
**Alcance ejecutado:** Fase 0, Pasos A, B y C solamente. **El Paso D no se ha ejecutado**:
por mandato expreso, el verificador externo será Claude. No se ha invocado ningún segundo
agente. **No se ha ejecutado ningún paso de la §6.**

### Lecturas previas y comprobación de N9

Se leyeron N5 · B-c y N7 · resumen ejecutivo en sus ramas, y los dos archivos externos
suministrados para N9. El N9 ejecutado no contiene la crítica que afirma tener pegada; la
crítica externa existe como archivo separado. Comprobación propia:

```
$ python3 - <<'PY'
from pathlib import Path
p=Path('/home/pablo/n9-lectura/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md')
lines=p.read_text().splitlines()
hits=[(i,s) for i,s in enumerate(lines,1) if 'maker/verifier' in s.lower() or 'maker-verifier' in s.lower()]
print(f'archivo={p}')
print(f'lineas={len(lines)}')
print(f'ultima_linea_no_vacia={next(s for s in reversed(lines) if s.strip())}')
print(f'ocurrencias_maker_verifier={len(hits)} ultima={hits[-1][0]}')
print('ocurrencias_despues_de_454=',sum(i>454 for i,_ in hits))
print('seccion_7_existe=',any(s=='## 7. Estado de la tarea' for s in lines))
print('marca_MV_hecho=',next(s for i,s in enumerate(lines,1) if i==384))
q=Path('/home/pablo/n9-lectura/critica-maker-verifier-N9.md')
text=q.read_text()
print(f'critica_existe={q.is_file()} lineas={len(text.splitlines())} hallazgos_MV={sum(f"### MV-{i} " in text for i in range(1,18))}')
PY
archivo=/home/pablo/n9-lectura/tarea-vps-N9-carry-de-funding-cuenta-real-y-especificacion-del-bot.md
lineas=1618
ultima_linea_no_vacia=🤖 Generated with [Claude Code](https://claude.com/claude-code)
ocurrencias_maker_verifier=9 ultima=617
ocurrencias_despues_de_454= 1
seccion_7_existe= True
marca_MV_hecho= | Maker/Verifier | **[hecho]** — critica literal pegada y respondida |
critica_existe=True lineas=983 hallazgos_MV=17
```

La única mención posterior al resumen es una hipótesis sobre lo que podría decir un
verificador, no la crítica ni las respuestas. Por tanto, no se da por buena ninguna cifra
central de N9 por estar afirmada en su propio registro. N5 queda incorporado en sentido
contrario a la tentación del carry: no depender de predecir no baja el listón y las colas
pueden subirlo.

## Paso A — Verificación de hechos

### A-1 · ¿Está esto medido ya? → **NO; NO-GO no disparado**

Se revisaron las once referencias, el historial completo y el árbol de trabajo. La búsqueda
amplia encuentra briefs, documentación y autocorrelación de curvas de estrategia. La búsqueda
focal no encuentra una medición ejecutada de memoria de precios ni una criba de mercados.
S3 · A.12 mide la autocorrelación de la **equity** para calcular `T_eff`, no la memoria de los
mercados de esta tarea. Un brief sin ejecutar no cuenta como trabajo hecho.

```
$ python3 fix-fase2/fase0_n10/a1_trabajo_previo.py
ramas_revisadas=11
commits_en_git_log_all=49
patron=autocorr archivos_distintos_con_rama=55
patron=variance_ratio archivos_distintos_con_rama=2
patron=hurst archivos_distintos_con_rama=2
patron=mercado archivos_distintos_con_rama=241
patron=universo archivos_distintos_con_rama=118
--- búsqueda focal en la rama actual ---
rc=0 (1 significa sin coincidencias)
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-nube-S3-datos-reproducibles-y-T.md:170:   T efectivo teniendo en cuenta la autocorrelación de los retornos
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md:62:  **se mide** —autocorrelación, ratio de varianza, persistencia de la volatilidad— y
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md:220:1. **Autocorrelación de los retornos** a 1, 5, 21 y 63 días, con su intervalo de
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md:223:2. **Ratio de varianza de Lo-MacKinlay** a 5, 21 y 63 días. Por encima de 1 hay
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md:292:  cualquier medición previa de autocorrelación, ratio de varianza o criba de mercados.
task/n10-eleccion-de-mercado:fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md:293:  `git log --all --oneline`, `git grep -i` por `autocorr`, `variance_ratio`, `hurst`,
NO-GO A-1: NO SE DISPARA; no hay medición previa ejecutada de memoria de precios ni criba de mercados.
salida=fix-fase2/fase0_n10/salida_a1_trabajo_previo.json
```

El JSON conserva el `git log --all --oneline`, las once listas de archivos por patrón y los
comandos con sus códigos de retorno.

### A-2 · Granularidad de Yahoo → **NO VERIFICABLE; NO-GO 2 DISPARADO**

La primera llamada, con `User-Agent` de navegador, recibió **HTTP 429**. No se obtuvo un
cuerpo útil. Salida literal, traza final:

```
$ python3 fix-fase2/fase0_n10/a2_granularidad_yahoo.py
Traceback (most recent call last):
  File "/home/pablo/trading-bot-gh/.worktrees/n10/fix-fase2/fase0_n10/a2_granularidad_yahoo.py", line 50, in <module>
    r = get(url)
  File "/home/pablo/trading-bot-gh/.worktrees/n10/fix-fase2/fase0_n10/a2_granularidad_yahoo.py", line 15, in get
    with urllib.request.urlopen(req, timeout=30) as response:
  File "/usr/lib/python3.12/urllib/request.py", line 215, in urlopen
    return opener.open(url, data)
urllib.error.HTTPError: HTTP Error 429: Too Many Requests
```

El fallo quedó registrado en `salida_a2_granularidad_yahoo.json` con `rc=1`, `http=429`,
`cuerpo_util=false` y `no_go_fuente_disparado=true`. **No se confirman ni se refutan las
velas o fechas del brief: no hay medición.** La condición del NO-GO 2 es literal y binaria:
la fuente no respondió 200 con cuerpo útil. **PARA.** No se reintentó para eludir el freno y
no se buscó una fuente alternativa.

### A-3 a A-6 · **NO EJECUTADOS por el NO-GO 2**

- **A-3:** no se descargaron ni contaron las series ni sus huecos.
- **A-4:** no se reverificaron Stooq ni FRED.
- **A-5:** `[no verificado]`. No se comprobó `adjclose`, ni dividendos, ni splits. Por tanto,
  **no se afirma que `URTH` sea una serie de retorno total ni que la comparación sea válida**.
- **A-6:** `[no verificado]` tanto el DFR vigente como el Sharpe del SG CTA Index. No se
  sustituyó Yahoo por otra fuente ni se usaron cifras de memoria.

## Paso B — Ataque adversarial

Las cifras aritméticas de B-1, B-2, B-3, B-4, B-6 y del Paso C proceden de este único comando;
no son resultados de mercado:

```
$ python3 fix-fase2/fase0_n10/bc_calculos.py
=== B-1: contraste múltiple ===
18 mercados x (4 ACF + 3 VR + 3 |r|) x 2 mitades = 360 estimaciones
por mitad = 180; alfa Bonferroni global 0.05/360 = 0.0001388889
alfa Bonferroni por mitad 0.05/180 = 0.0002777778

=== B-2: autocorrelación diaria mínima, modelo AR(1) gaussiano ideal ===
coste_ida_vuelta=0.0005 vol_diaria=0.01 -> rho_min=0.062666 (6.267 %)
coste_ida_vuelta=0.0005 vol_diaria=0.02 -> rho_min=0.031333 (3.133 %)
Fórmula: E[r_t sign(r_(t-1))] = rho*sigma*sqrt(2/pi); se exige que supere el coste.

=== B-3: dependencia de Yahoo y ETFs con historia limitada ===
series_yahoo=18/18; ETFs=6/18 (EEM,IEF,TLT,DBC,VNQ,URTH); porcentaje_ETFs=33.333 %

=== B-4: impuesto anual frente a diferido, 100.000 €, bruto 7 %, 20 años ===
IRPF=19 %: final_anual=301324.29 € final_diferido=332444.44 € diferencia=31120.15 €
IRPF=28 %: final_anual=267358.66 € final_diferido=306617.28 € diferencia=39258.62 €

=== B-6: capital para que 2.400 €/año de sistema no superen el exceso ===
coste=2400 €/año exceso_neto=1.0000 % -> capital_min=240000.00 €
coste=2400 €/año exceso_neto=3.0000 % -> capital_min=80000.00 €
coste=2400 €/año exceso_neto=5.6133 % -> capital_min=42755.60 €
El 2.400 € es el ejemplo del brief, no un presupuesto medido de este sistema.

=== Paso C: escenarios condicionados, no retornos esperados verificados ===
C-1_mundo capital=1000 neta=76.38 € vs_DFR=+56.13 € vs_mundo=+0.00 €
C-1_mundo capital=10000 neta=763.83 € vs_DFR=+561.33 € vs_mundo=+0.00 €
C-1_mundo capital=100000 neta=7569.70 € vs_DFR=+5544.70 € vs_mundo=+0.00 €
C-2_tendencia capital=1000 neta=39.69 € vs_DFR=+19.44 € vs_mundo=-36.69 €
C-2_tendencia capital=10000 neta=396.90 € vs_DFR=+194.40 € vs_mundo=-366.93 €
C-2_tendencia capital=100000 neta=3969.00 € vs_DFR=+1944.00 € vs_mundo=-3600.70 €
Insumos del brief, NO verificados hoy: mundo bruto 9,43 %; tendencia profesional bruta 4,9 %; DFR 2,5 %.
IRPF calculado como realización anual, tramos 19 %/21 %; no incluye comisiones ni coste del sistema.
N_vigente=16 -> N_candidata=17
Coste de descarte estimado: C-1=1 hora; C-2=4 horas; ninguna se ejecuta con Yahoo en NO-GO.

salida=fix-fase2/fase0_n10/salida_bc_calculos.json
```

### B-0 · ¿La premisa tiene sentido? → **CRÍTICO, pero no mata la tarea**

Una criba de autocorrelación no puede demostrar «dónde se gana dinero»: mide dependencia,
no una prima capturable. Si se vendiera como detector de alfa, la tarea sí sería inútil. Su
utilidad defendible es más estrecha y anterior a construir: obliga a justificar el universo,
descarta instrumentos inaccesibles y pone coste, riesgo, fiscalidad y alternativa pasiva en la
misma decisión. Eso no lo hizo S2 con la literatura.

El resultado no está lógicamente cantado: cripto puede superar el criterio y, si lo hiciera,
habría que decirlo. Comprar el índice mundial es una alternativa fuerte, no una conclusión que
se pueda imponer antes de medir. **Conclusión:** la criba sirve como filtro de descarte y de
coherencia de instrumentos, no como prueba de rentabilidad. **El NO-GO 6 no se dispara.**
Qué cambia: el ganador de una eventual §6.4 solo podría llamarse «terreno menos descartado
para la siguiente falsación», nunca «mercado donde está demostrado ganar».

### B-1 · La selección múltiple del propio screen → **ALTO**

El blindaje de mismo signo en dos mitades reduce inestabilidad, pero no controla la tasa de
falsos positivos de la familia. Además, la cuenta del brief agrupa familias como si fueran un
solo contraste: con los lags especificados son **360 estimaciones**, **180 por mitad**. El
`IC95` nominal no sobrevive a esa multiplicidad por repetir el signo.

Qué cambia, para decisión de Pablo y sin modificar ahora la §4: usar como corrección primaria
**Romano-Wolf max-t por bootstrap de bloques**, preservando la dependencia entre lags, métricas
y mercados, por separado en cada mitad; exigir después el mismo signo. Holm es el sustituto
transparente si no se implementa el bootstrap conjunto. Los valores Bonferroni impresos arriba
son solo la referencia más conservadora, no una corrección aplicada a datos inexistentes.

### B-2 · Memoria no es dinero → **CRÍTICO**

En el modelo ideal AR(1) gaussiano con media cero, una regla que toma el signo del retorno
anterior tiene esperanza bruta diaria `rho·sigma·sqrt(2/pi)`. Para una ida y vuelta de **5 pb**,
el `rho` mínimo es **0,062666** con volatilidad diaria del **1 %**, o **0,031333** con el
**2 %**. Una autocorrelación de **0,02** no cubre ese coste en ninguno de los dos escenarios.
Es una cota ideal, no un backtest ni una promesa.

Qué cambia: cada mercado necesita su propio `rho_min = coste/(sigma·sqrt(2/pi))` junto al coste
de §4.3; una memoria significativa pero inferior queda descartada como inexplotable. La §4.2
por sí sola no basta para elegir.

### B-3 · Yahoo y el sesgo de supervivencia → **ALTO**

Las **18 de 18** series dependerían de una fuente gratuita no contractual; el 429 de A-2 ya ha
materializado ese riesgo. **Seis de 18** son ETFs cuya historia empieza en su listado y cuyos
ajustes pueden revisarse. Los futuros continuos añaden otra unidad distinta: su serie no es el
retorno de una posición con renovaciones. El fallo de A-5 deja sin verificar justamente el
`adjclose` de la vara de medir.

Qué cambia: ninguna conclusión puede depender solo de que Yahoo devuelva filas. Antes de una
tabla hacen falta `adjclose`, eventos, moneda, calendario y, para futuros, una cuenta de roll.
La tabla entera queda bloqueada hoy, no parcialmente degradada.

### B-4 · Los impuestos y el diferimiento pueden invertir el ranking → **ALTO**

Con 100.000 €, un bruto ilustrativo del 7 % y veinte años, realizar y tributar cada año deja
301.324,29 € frente a 332.444,44 € difiriendo al 19 %: **31.120,15 €** de diferencia. Al 28 %
la diferencia es **39.258,62 €**. No es un efecto cosmético ni una estimación de mercado: es
la aritmética impresa por el comando.

Qué cambia: no se puede restar el IRPF como si todas las estrategias realizaran anualmente.
La tabla debe separar impuesto anual y diferido, y mostrar el horizonte. Renovaciones de
futuros o rotación diaria no pueden compararse con B&H usando la misma cuota anual de impuesto.

### B-5 · Sesgo propio contra cripto → **MEDIO**

Conozco el resultado previo del panel y la crítica al carry, así que el riesgo es exigir más
pruebas a cripto o descartar sus datos antes que los demás. La defensa no es declararse neutral:
es aplicar literalmente los mismos datos ajustados, costes, huecos, fiscalidad y umbrales a las
18 filas, publicar también los resultados favorables y no retirar una fila por incomodidad.

Qué cambia: si cripto gana con la §4 intacta, gana y se escribe. Ninguna objeción de este
registro introduce un veto especial a cripto.

### B-6 · El sistema puede costar más que su exceso → **ALTO**

El coste real de tokens, VPS y datos **no está medido** y no hay ganador en Fase 0. Usando solo
el ejemplo de 2.400 €/año del brief como escenario, el capital para que el coste no supere un
exceso neto anual es **240.000 €** al 1 %, **80.000 €** al 3 % y **42.755,60 €** al 5,6133 %.
No son precios presupuestados ni umbrales observados.

Qué cambia: antes de §6.4 hace falta un presupuesto anual con fuentes y el exceso neto en euros
para los tres capitales. B&H sin bot tiene coste incremental de sistema distinto de una criba
activa; mezclarlos infla artificialmente el atractivo de la alternativa que necesita máquina.

## Paso C — Contrapropuesta obligatoria

Hay **dos candidatas**, ordenadas por coste estimado de descarte. Ninguna se evalúa aquí. Las
cifras en euros son **escenarios condicionados**, no retornos esperados verificados: usan los
datos secundarios del brief (9,43 % mundial y 4,9 % de tendencia profesional) y el DFR del 2,5 %,
todos `[no verificado]` por la parada de A-6. El cálculo supone realización anual, IRPF del
ahorro y ninguna comisión ni coste de sistema; precisamente por eso no es una recomendación de
compra. El comando y su salida completa están al inicio del Paso B. A ambas les corresponde
**N=17** por la regla `N_vigente+1` con el valor vigente fijado por esta tarea en 16.

### C-1 · Fijar primero el benchmark mundial invertible, sin bot

- **Mecanismo económico:** el accionista recibe la prima de riesgo y los beneficios de empresas
  productivas; el pago no sale de acertar el signo del día siguiente, sino de asumir riesgo de
  capital y esperar.
- **Datos exactos y acceso:** Yahoo `chart/URTH` con `adjclose` y eventos de dividendos/splits;
  BCE `FM.D.U2.EUR.4F.KR.DFR.LEV`; ficha y folleto del ETF UCITS concreto antes de operar. Los
  endpoints de Yahoo y BCE no exigen clave, pero **Yahoo hoy respondió 429 aquí** y la descarga
  actual no queda verificada.
- **N:** **17** si se convierte en una regla nueva evaluada; proponer el benchmark no consume
  un trial en este registro.
- **Qué la mata rápido y cuándo:** en **1 hora**, reconciliar `adjclose` con dividendos y con el
  ETF UCITS realmente accesible, su TER, divisa, comisiones e IRPF. Si no se puede construir una
  referencia de retorno total coherente o su exceso neto prudente sobre el DFR no es positivo,
  muere como alternativa.
- **Por qué mejor que la criba:** responde directamente qué puede comprar Pablo sin bot y evita
  confundir dependencia estadística con retorno. Es la alternativa que toda estrategia tendría
  que batir de todos modos.

| Capital | Escenario neto anual | Contra DFR | Contra índice mundial |
|---|---:|---:|---:|
| 1.000 € | 76,38 € | +56,13 € | 0,00 € |
| 10.000 € | 763,83 € | +561,33 € | 0,00 € |
| 100.000 € | 7.569,70 € | +5.544,70 € | 0,00 € |

### C-2 · Evaluar directamente una prima de tendencia diversificada, no cribar memoria

- **Mecanismo económico:** la tendencia puede cobrar una prima por proveer liquidez a quienes
  ajustan riesgo lentamente o se cubren; el beneficio, si existe, procede de ese traspaso y de
  la prima de riesgo, no de que una autocorrelación sea estadísticamente visible.
- **Datos exactos y acceso:** las series diarias Yahoo de renta variable, bonos, divisas y
  materias primas ya enumeradas en §2.3, con `adjclose` cuando exista; especificaciones y precios
  de los futuros concretos; DFR del BCE. Yahoo no pide clave, pero **hoy está bloqueada por el
  429 verificado**, así que la prueba no se ejecuta.
- **N:** **17**. Evaluar la regla consumiría un trial; aquí solo se propone.
- **Qué la mata rápido y cuándo:** en **4 horas**, con una regla y cortes pre-registrados, costes
  de roll, divisa, IRPF y sistema: si el neto fuera de muestra no supera a la vez al DFR y al
  mundo, muerta. Esto sería otra tarea autorizada, no se ha hecho.
- **Por qué mejor que la criba:** contrasta directamente el mecanismo económico en euros y contra
  las alternativas, en lugar de seleccionar por una propiedad que B-2 demuestra que puede ser
  inexplotable.

| Capital | Escenario neto anual | Contra DFR | Contra índice mundial |
|---|---:|---:|---:|
| 1.000 € | 39,69 € | +19,44 € | −36,69 € |
| 10.000 € | 396,90 € | +194,40 € | −366,93 € |
| 100.000 € | 3.969,00 € | +1.944,00 € | −3.600,70 € |

El escenario C-2 perdería contra el mundo incluso antes de comisiones y sistema; eso no es un
resultado medido, sino una consecuencia del insumo secundario declarado. Sirve para no vender
una candidata como superior cuando su propio orden de magnitud no supera el benchmark.

## Estado binario de los seis NO-GO

| # | Estado | Evidencia y consecuencia |
|---|---|---|
| 1 | **NO SE DISPARA** | A-1 no encuentra medición previa ejecutada de memoria de precios ni criba de mercados. |
| 2 | **SE DISPARA** | Yahoo respondió 429 sin cuerpo útil en A-2. A-3 a A-6 quedan sin ejecutar; no hay fuente alternativa. |
| 3 | **NO SE DISPARA** | No se backtesteó una regla de entrada ni se calculó Sharpe de señal; solo aritmética y escenarios. |
| 4 | **NO SE DISPARA** | La §4 no se modificó. Las correcciones propuestas quedan escritas como objeciones para Pablo. |
| 5 | **NO SE DISPARA** | El Paso C contiene dos candidatas con datos, N, prueba de muerte, horas y euros por capital. |
| 6 | **NO SE DISPARA** | B-0 concluye que la criba tiene utilidad limitada de descarte; no concluye que carezca de sentido. |

**Parada:** solo el NO-GO 2 está disparado. No hay tabla de mercados, elección de instrumento,
plan de §6.5 ni afirmación sobre dividendos ajustados. El Paso D queda pendiente del verificador
externo Claude; no se presenta ninguna revisión interna como sustituta.

---

## Paso D — Verificación externa

**Fecha:** 2026-11-06, 01:27 a 01:40 UTC. **Verificador:** Claude Opus 5, sesión de
escritorio, **otro proveedor que el ejecutor**, que es la única razón de que este paso
exista. **Material de contraste:** mis propias mediciones del 2026-11-03, hechas en el
VPS y **deliberadamente no empujadas al repositorio**, para que el ejecutor no pudiera
copiarlas ni yo pudiera acomodar el veredicto a lo que él hubiera escrito.

**Veredicto en una línea:** el registro es el más limpio de los diez de este expediente
—ninguna cifra sin comando, cero bloques fabricados, los NO-GO en binario— pero **su
NO-GO 2 es falso**, y con él se cae la única razón por la que A-3 a A-6 no se ejecutaron.
**La Fase 0 no está cerrada.**

### D-1 · El NO-GO 2 no debió dispararse: Yahoo responde 200. El 429 lo causa el `User-Agent` del propio script — **CRÍTICO**

El registro concluye «la fuente no respondió 200 con cuerpo útil». La fuente sí responde.
Lo que no responde es **esa cabecera**. Aislado caso por caso, en la misma máquina donde
corrió el ejecutor y en el mismo cuarto de hora:

```
$ bash pasod-aislar-429.sh
  python  UA corto               http=200 bytes=1524037
  python  UA de Kimi             HTTP 429 Too Many Requests
  python  UA mio                 http=200 bytes=1524037
  python  UA de Kimi + Accept    HTTP 429 Too Many Requests
  python  sin User-Agent         HTTP 429 Too Many Requests
  curl    UA de Kimi             http=429 bytes=19
```

El `User-Agent` del script es
`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36`.
Falla **tres de tres**, en `urllib` y en `curl`, mientras `Mozilla/5.0` y
`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36` devuelven **200 con 1.524.037
bytes** intercalados entre los fallos. Sin `User-Agent` también da 429. Yahoo no está
limitando el tráfico: está **filtrando por huella de cliente** y devolviendo 429 como
código de rechazo, que es engañoso pero no es un fallo de la fuente.

No es intermitencia ni cuota consumida. Dieciséis sondas espaciadas 15 segundos, desde
**dos IPs distintas** —la misma WSL del ejecutor y el VPS—, todas con cuerpo idéntico:

```
$ bash pasod-sondas.sh
sonda  hora       WSL            VPS
1      01:31:33   200:1524037    200:1524037
2      01:31:50   200:1524037    200:1524037
...
8      01:33:42   200:1524037    200:1524037
```

Y la llamada que la §2.2 de esta tarea necesita de verdad, `period1=0`, da 14.083 velas
diarias desde **1970-01-02** con `period2` fijado a hace un año. Son **249 menos** que
las 14.332 del brief: exactamente un año hábil, así que la cifra del brief queda
**coherente**, no verificada hoy al día de hoy.

**Qué cambia:** A-2 a A-6 están **sin hacer**, no bloqueadas. Es una hora de trabajo con
dos caracteres menos en una cadena. Nada de lo que el registro declara `[no verificado]`
tenía por qué quedarse así.

### D-2 · La redacción del NO-GO 2 es mía y es defectuosa — **CRÍTICO, y no es culpa del ejecutor**

«La fuente de la §2.1 no responde 200 con cuerpo útil → PARA» no distingue tres cosas
distintas: una fuente **caída**, un **límite de tasa** transitorio y un **rechazo por
cabecera** del propio cliente. Las tres dan «no 200», y solo la primera justifica matar
una tarea. Peor: la prohibición de buscar alternativa, que puse para que nadie cambiara
el dato por debajo, se convirtió en un incentivo a no volver a intentarlo.

El ejecutor aplicó mi regla **al pie de la letra y la pegó con su traza**. Eso es lo que
se le pidió. Un NO-GO binario mal escrito produce exactamente esto, y el expediente ya
lleva dos tareas discutiendo NO-GO: a N6 se le reprochó graduarlos y a N7 declararlos sin
salida. Esta es la tercera variante del mismo problema y la responsabilidad es del brief.

**Corrección para cualquier tarea futura:** el NO-GO de fuente se dispara solo con
**tres intentos espaciados al menos 60 segundos, con dos cabeceras distintas y desde dos
redes si hay dos**, y los tres pegados. Menos que eso no es una fuente caída: es una
prueba incompleta.

### D-3 · La vara de medir del Paso C está 2,68 puntos por debajo de la real — **ALTO**

El Paso C compara sus dos candidatas contra un índice mundial del **9,43 %**, insumo que
el propio brief marca «calculadora de terceros · secundario, verificar» y que el registro
hereda declarándolo `[no verificado]`. Medido hoy, con la fuente que sí responde:

```
$ bash pasod-contraste.sh
  anos=14.81
  close    10.051 %
  adjclose 12.111 %
```

Son **12,111 %** con dividendos reinvertidos, no 9,43 %. Y la diferencia entre `close` y
`adjclose` —**2,060 puntos anuales**— es la que A-5 existía para cazar. Mis mediciones del
2026-11-03 daban 11,979 % y 9,922 % sobre el mismo ticker: la cifra es estable, no un
artefacto de hoy.

**Qué cambia:** la columna «Contra índice mundial» de las dos tablas del Paso C está mal
calculada, y en la dirección que favorece a las candidatas. C-2 no pierde 3.600 € contra
el mundo con 100.000 €: pierde bastante más. La conclusión cualitativa del registro
—«C-2 perdería contra el mundo incluso antes de comisiones»— **se refuerza**, no se cae.
C-1 deja de ser un empate con el benchmark y pasa a ser el benchmark mismo, lo cual es
coherente con lo que C-1 proponía.

### D-4 · B-1 es un hallazgo material contra mi propio criterio, y lo acepto — **ALTO, acreditado al ejecutor**

El criterio de la §4 exigía «IC95 que excluya el cero en las dos mitades con el mismo
signo» y lo presentaba como blindaje suficiente. B-1 pone el número que yo no puse: con
los retardos especificados son **360 estimaciones, 180 por mitad**, y repetir el signo
en dos mitades **no controla la tasa de error de la familia**. Un Bonferroni global
quedaría en `0,05/360 = 0,000139`.

Que propusiera **Romano-Wolf max-t por bootstrap de bloques**, preservando la dependencia
entre retardos, métricas y mercados, con Holm como sustituto transparente, es la respuesta
técnicamente correcta. Y no tocó la §4 para aplicarlo, porque mi NO-GO 4 se lo prohibía:
lo dejó escrito como objeción para que lo decidas tú. Hizo lo correcto dos veces.

**Qué cambia:** la §4 no puede ejecutarse como está. El control de multiplicidad entra
antes, o la tabla producirá mercados «con memoria» que son ruido seleccionado.

### D-5 · B-0 atacó la premisa de verdad, por primera vez en diez tareas — **acreditado**

Nueve registros anteriores atacaron cifras. Este ataca la pregunta y llega a una
reformulación que acepto entera: una criba de autocorrelación mide **dependencia**, no una
**prima capturable**, así que el ganador de una eventual §6.4 solo puede llamarse
**«terreno menos descartado para la siguiente falsación»**, nunca «mercado donde está
demostrado que se gana». Y la defensa de por qué la criba sigue valiendo algo —obliga a
justificar el universo, descarta instrumentos inaccesibles y pone coste, riesgo,
fiscalidad y alternativa pasiva en la misma decisión— es más honesta que la que yo escribí
en la §1.

B-2 lo completa con la cota que convierte esto en aritmética: con una ida y vuelta de 5 pb
y volatilidad diaria del 1 %, hace falta `rho ≥ 0,0627`. Una autocorrelación del 0,02,
estadísticamente significativa, **es inexplotable**. Ese `rho_min` por mercado tiene que
ir en la tabla, al lado del coste.

**Qué cambia:** el lenguaje de la §4.4 y de la §6.4, y una columna más en la tabla.

### D-6 · Lo que comprobé y está limpio

- **Ninguna cifra sin comando.** Las de B-1 a B-6 y del Paso C salen todas de
  `bc_calculos.py`, y el registro dice explícitamente que son aritmética y escenarios
  condicionados, **no resultados de mercado**. Esa distinción es la que N9 no hizo.
- **Cero bloques de salida fabricados.** En N7 hubo tres. Aquí los tres JSON existen,
  parsean, y sus cifras coinciden con lo pegado.
- **Los seis NO-GO declarados en binario**, y ninguno declarado disparado contra su propia
  salida. El 2 es falso por mi redacción, no por su lectura.
- **No se creyó mi aviso sobre N9: lo comprobó con código propio.** Le dije que la §7 de
  N9 no existía y le dije mal —lo que no existía era la crítica pegada, no la sección—. Su
  comprobación imprimió `seccion_7_existe= True` y, aun así, confirmó lo que importaba:
  `ocurrencias_despues_de_454= 1`, y esa única mención es una hipótesis, no la crítica.
  Corrigió mi imprecisión sin montar un drama y sin dar por bueno el fondo.
- **§6 intacta, cero credenciales, ningún segundo agente invocado**, y `git status` solo
  con el archivo de tarea y `fase0_n10/`.

### D-7 · Mi propia precipitación, declarada porque el registro de un error vale más que su borrado — **MEDIO**

Mi primera hipótesis fue que el 429 era específico de `range=max` y que `period1=0`
funcionaba. La escribí después de dos llamadas con `curl`. Cuatro minutos más tarde mis
propias sondas con `python` daban 429 **en las tres variantes**, incluida la que yo acababa
de declarar buena, y la hipótesis quedó refutada. Solo entonces aislé el `User-Agent`, que
es la causa real. Dos llamadas no eran una medición; D-1 está escrito sobre veintiuna.

### Estado de la Fase 0 después del Paso D

| | |
|---|---|
| Pasos A, B, C | **entregados**, y B y C con calidad por encima de todo el expediente |
| **NO-GO 2** | **REVOCADO.** La fuente responde 200. El 429 era la cabecera del script |
| **A-2 a A-6** | **PENDIENTES.** Una hora, con el `User-Agent` corregido |
| Paso D | **hecho**, por verificador de otro proveedor, con mediciones no compartidas |
| §4, antes de poder ejecutarse | **dos correcciones obligatorias**: multiplicidad (D-4) y benchmark con `adjclose` (D-3) |
| §6 y §8 | **sin ejecutar y sin firma** |

**Lo que no decide este paso y es de Pablo:** si se relanza la Fase 0 para cerrar A-2 a
A-6 con la cabecera corregida, y si las dos correcciones de la §4 se aplican antes de que
la §6 pueda siquiera proponerse.

---

## Cierre de la Fase 0 tras el Paso D

**Fecha:** 2026-11-06. **Ejecutor:** Kimi. Se ejecutan A-2, A-3, A-4, A-5 y A-6 con el
`User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36`. Cada tanda de red incluye
una comprobación previa de Yahoo con HTTP 200 y cuerpo útil. No se ha invocado ningún agente.
El NO-GO 2 anterior queda **revocado por D-2**; no se ha cambiado la §4 ni ejecutado la §6.

### A-2 · Granularidad de `^GSPC` → **CONFIRMADO con el conteo de hoy**

```
$ python3 fix-fase2/fase0_n10/cierre_a2_granularidad.py
User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
PREVIO http=200 bytes=1298 cuerpo_util=True
range_max_1d http=200 bytes=19900 velas=169 1984-12-01 -> 2026-11-05 granularidad=3mo
range_10y_1d http=200 bytes=261269 velas=2513 2016-11-07 -> 2026-11-05 granularidad=1d
periodos_1d http=200 bytes=1549380 velas=14334 1970-01-02 -> 2026-11-05 granularidad=1d
period2=1793958587
NO-GO fuente: NO SE DISPARA
salida=fix-fase2/fase0_n10/salida_cierre_a2_granularidad.json
```

`range=max` no entrega diario, sino 169 velas con granularidad `3mo`. La llamada por épocas
entrega 14.334 velas diarias desde 1970-01-02. El brief queda confirmado en mecánica y rango;
el conteo actual difiere por la fecha de descarga.

### A-3 · Las 18 series y sus huecos → **MEDIDO; nueve series quedan fuera**

Método de calendario, declarado en el script y en el JSON: diario natural para cripto; NYSE
reconstruido con festivos y cierres extraordinarios para `^GSPC`; fechas efectivamente
observadas de `^GSPC` para los demás activos estadounidenses; festivos BME/Xetra para Europa;
laborables excepto 1 de enero y 25 de diciembre para divisas. Son calendarios reconstruidos,
no calendarios contractuales. Se cuentan también duplicados y cierres nulos. La lista completa
de fechas de huecos está en el JSON; la salida imprime las primeras veinte cuando son muchas.

```
$ python3 fix-fase2/fase0_n10/cierre_a3_series_y_huecos.py
User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
PREVIO ^GSPC http=200 bytes=1549380 velas=14334
DESCARGA ^GSPC http=200 bytes=1549380 velas=14334
DESCARGA ^STOXX50E http=200 bytes=494810 velas=4930
DESCARGA ^IBEX http=200 bytes=775790 velas=8585
DESCARGA EEM http=200 bytes=652045 velas=5930
DESCARGA ^TNX http=200 bytes=1459430 velas=14334
DESCARGA IEF http=200 bytes=656441 velas=6108
DESCARGA TLT http=200 bytes=661826 velas=6108
DESCARGA GC=F http=200 bytes=606287 velas=6656
DESCARGA CL=F http=200 bytes=694894 velas=6661
DESCARGA HG=F http=200 bytes=707613 velas=6656
DESCARGA DBC http=200 bytes=572381 velas=5221
DESCARGA EURUSD=X http=200 bytes=637823 velas=5985
DESCARGA JPY=X http=200 bytes=814166 velas=7833
DESCARGA ^VIX http=200 bytes=973634 velas=9614
DESCARGA BTC-EUR http=200 bytes=443233 velas=4434
DESCARGA ETH-EUR http=200 bytes=366590 velas=3283
DESCARGA VNQ http=200 bytes=591979 velas=5562
DESCARGA URTH http=200 bytes=393838 velas=3726
RESULTADO ^GSPC velas=14334 1970-01-02 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO ^STOXX50E velas=4930 2007-03-30 -> 2026-11-06 moneda=EUR huecos=0 nulos=14 duplicados=0
RESULTADO ^IBEX velas=8585 1993-07-12 -> 2026-11-06 moneda=EUR huecos=0 nulos=139 duplicados=0
RESULTADO EEM velas=5930 2003-04-14 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO ^TNX velas=14334 1970-01-02 -> 2026-11-05 moneda=USD huecos=0 nulos=102 duplicados=0
RESULTADO IEF velas=6108 2002-07-30 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO TLT velas=6108 2002-07-30 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO GC=F velas=6656 2000-08-30 -> 2026-11-06 moneda=USD huecos=2 nulos=83 duplicados=0
  PRIMERAS_FECHAS 2016-10-10,2016-11-11
RESULTADO CL=F velas=6661 2000-08-23 -> 2026-11-06 moneda=USD huecos=2 nulos=80 duplicados=0
  PRIMERAS_FECHAS 2016-10-10,2016-11-11
RESULTADO HG=F velas=6656 2000-08-30 -> 2026-11-06 moneda=USD huecos=2 nulos=79 duplicados=0
  PRIMERAS_FECHAS 2016-10-10,2016-11-11
RESULTADO DBC velas=5221 2006-02-06 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO EURUSD=X velas=5985 2003-12-01 -> 2026-11-06 moneda=USD huecos=703 nulos=34 duplicados=0
  PRIMERAS_FECHAS 2004-04-02,2004-04-09,2004-04-16,2004-04-23,2004-04-30,2004-05-07,2004-05-14,2004-05-21,2004-05-28,2004-06-04,2004-06-11,2004-06-18,2004-06-25,2004-07-02,2004-07-16,2004-07-23,2004-07-30,2004-08-06,2004-08-13 ...
RESULTADO JPY=X velas=7833 1996-10-30 -> 2026-11-06 moneda=JPY huecos=916 nulos=48 duplicados=0
  PRIMERAS_FECHAS 1997-04-04,1997-04-11,1997-04-18,1997-04-25,1997-05-02,1997-05-09,1997-05-16,1997-05-23,1997-05-30,1997-06-06,1997-06-13,1997-06-20,1997-06-27,1997-07-04,1997-07-11,1997-07-18,1997-07-25,1997-08-01,1997-08-08,1997-08-15 ...
RESULTADO ^VIX velas=9614 1990-01-02 -> 2026-11-06 moneda=USD huecos=0 nulos=331 duplicados=0
RESULTADO BTC-EUR velas=4434 2014-09-17 -> 2026-11-06 moneda=EUR huecos=0 nulos=0 duplicados=0
RESULTADO ETH-EUR velas=3283 2017-11-11 -> 2026-11-06 moneda=EUR huecos=0 nulos=0 duplicados=0
RESULTADO VNQ velas=5562 2004-09-29 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
RESULTADO URTH velas=3726 2012-01-12 -> 2026-11-05 moneda=USD huecos=0 nulos=0 duplicados=0
salida=fix-fase2/fase0_n10/salida_cierre_a3_series_y_huecos.json
```

La selección por calidad se calcula leyendo ese JSON, no la salida visual:

```
$ python3 fix-fase2/fase0_n10/cierre_bc_recalculo.py
=== A-3: series utilizables sin huecos ni cierres nulos ===
limpias=9/18: ^GSPC,EEM,IEF,TLT,DBC,BTC-EUR,ETH-EUR,VNQ,URTH
excluidas=9/18: ^STOXX50E,^IBEX,^TNX,GC=F,CL=F,HG=F,EURUSD=X,JPY=X,^VIX
[...]
```

**Consecuencia literal:** esas nueve series excluidas no entran mientras sus huecos o cierres
nulos no tengan explicación documentada. En divisas, el patrón repetido de viernes ausentes no
se presenta como festivo: queda sin explicar. Los tres futuros conservan dos fechas sin
explicar además de sus cierres nulos.

### A-4 · Stooq y FRED → **CONFIRMADO: no sirven como fuentes utilizables aquí**

```
$ python3 fix-fase2/fase0_n10/cierre_a4_stooq_fred.py
previo_yahoo http=200 bytes=1298 cuerpo_util=True
  inicio='{"chart":{"result":[{"meta":{"currency":"USD","symbol":"^GSPC","exchangeName":"SNP","fullExchangeName":"SNP","instrumentType":"INDEX","firstTradeDate":-1325583000,"regularMarketTime":1793914448,"hasPrePostMarketData":false,"gmtoffset":-18000,"timezone":"EST","exchangeTimezoneName":"America/New_York","regularMarketPrice":7353.73,"regularMarketChangePercent":-4.356,"fulldayPrice":7353.73,"fulldayCha'
stooq_sp500 http=200 bytes=796 cuerpo_util=False
  inicio='<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"></head><body><noscript>This site requires JavaScript to verify your browser. Please enable JavaScript and reload.</noscript><script nonce="FgANDzMnTXLR4ZBaEIaZJQ">\n(async()=>{const c="AAAAAGrtpKgzEGCZVNjOvNIn7iTKEpqEWqDLLhx6Tuam9umc0o4HsyEOJQQ",d=4,t="0".repeat(d),e=new TextEncoder;let n=0;while(1){cons'
fred_dgs10_csv http=0 bytes=0 cuerpo_util=False
  inicio=''
  error=TimeoutError('The read operation timed out')
fred_vix_csv http=0 bytes=0 cuerpo_util=False
  inicio=''
  error=TimeoutError('The read operation timed out')
fred_dgs10_api_sin_clave http=400 bytes=162 cuerpo_util=False
  inicio='{"error_code":400,"error_message":"Bad Request.  Variable api_key is not set.  Read https:\\/\\/fred.stlouisfed.org\\/docs\\/api\\/api_key.html for more information."}'
salida=fix-fase2/fase0_n10/salida_cierre_a4_stooq_fred.json
```

Stooq vuelve a dar 200 con HTML y un muro JavaScript, no CSV. Los CSV de FRED agotan el
tiempo y su API exige clave. No se creó cuenta ni se envió credencial.

### A-5 · Ajuste por dividendos y splits → **CONFIRMADO para los ETFs; URTH corregido**

Las 18 respuestas contienen `adjclose`. En los seis ETFs hay diferencias entre `close` y
`adjclose` y eventos de dividendos; EEM además tiene dos splits. Los índices, futuros, divisas
y cripto no se presentan como retorno total por tener ese campo: en ellos puede ser idéntico al
cierre. `^IBEX` presenta diferencias sin eventos declarados y además estaba excluido en A-3;
no se inventa una explicación.

```
$ python3 fix-fase2/fase0_n10/cierre_a5_ajuste_y_urth.py
User-Agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
PREVIO http=200 bytes=1549380 cuerpo_util=True
^GSPC http=200 velas=14334 adjclose=True pares=14334 diffs=0 dividendos=0 splits=0
^STOXX50E http=200 velas=4930 adjclose=True pares=4916 diffs=0 dividendos=0 splits=0
^IBEX http=200 velas=8585 adjclose=True pares=8446 diffs=5793 dividendos=0 splits=0
EEM http=200 velas=5930 adjclose=True pares=5930 diffs=5829 dividendos=47 splits=2
^TNX http=200 velas=14334 adjclose=True pares=14232 diffs=0 dividendos=0 splits=0
IEF http=200 velas=6108 adjclose=True pares=6108 diffs=6061 dividendos=290 splits=0
TLT http=200 velas=6108 adjclose=True pares=6108 diffs=6061 dividendos=288 splits=0
GC=F http=200 velas=6656 adjclose=True pares=6573 diffs=0 dividendos=0 splits=0
CL=F http=200 velas=6661 adjclose=True pares=6581 diffs=0 dividendos=0 splits=0
HG=F http=200 velas=6656 adjclose=True pares=6577 diffs=0 dividendos=0 splits=0
DBC http=200 velas=5221 adjclose=True pares=5221 diffs=5001 dividendos=9 splits=0
EURUSD=X http=200 velas=5985 adjclose=True pares=5951 diffs=0 dividendos=0 splits=0
JPY=X http=200 velas=7833 adjclose=True pares=7785 diffs=0 dividendos=0 splits=0
^VIX http=200 velas=9614 adjclose=True pares=9283 diffs=0 dividendos=0 splits=0
BTC-EUR http=200 velas=4434 adjclose=True pares=4434 diffs=0 dividendos=0 splits=0
ETH-EUR http=200 velas=3283 adjclose=True pares=3283 diffs=0 dividendos=0 splits=0
VNQ http=200 velas=5562 adjclose=True pares=5562 diffs=5530 dividendos=88 splits=0
URTH http=200 velas=3726 adjclose=True pares=3726 diffs=3625 dividendos=31 splits=0
=== URTH, crecimiento anual compuesto sobre la historia disponible ===
ventana=2012-01-12 -> 2026-11-05 anos=14.814815
close 50.299999 -> 199.630005; CAGR=9.751232 %
adjclose 38.219700 -> 199.630005; CAGR=11.804904 %
diferencia_adjclose_menos_close=2.053672 pp
salida=fix-fase2/fase0_n10/salida_cierre_a5_ajuste_y_urth.json
```

**La vara de medir debe usar `adjclose`.** Mi medición propia es **11,804904 %**, no el 9,43 %
secundario ni el 12,111 % del Paso D; se usa la que reproduce mi comando y mi ventana. Es CAGR
histórico de URTH en USD, no retorno esperado ni una conversión a euros.

### A-6 · DFR y Sharpe externo → **DFR CONFIRMADO; 0,56 NO VERIFICADO**

```
$ python3 fix-fase2/fase0_n10/cierre_a6_dfr_sg.py
PREVIO_YAHOO http=200 bytes=1298 cuerpo_util=True
BCE http=200 bytes=745 serie=FM.D.U2.EUR.4F.KR.DFR.LEV fecha=2026-11-06 DFR=2.500 %
SG_MAX_DATE http=200 fecha=2026-11-04
SG_STATS http=200 bytes=150
Annualised Return, 1.46%,Current Margin/Equity,
Annualised Volatility,16.69%,Current Drawdown,-27.34%
Sharpe Ratio, 0.087,Maximum Drawdown,-46.01%
SG_CTA_0.56=[no verificado]; dato público más cercano=0.61 desde enero de 2000 (CFM 2022, secundario).
salida=fix-fase2/fase0_n10/salida_cierre_a6_dfr_sg.json
```

El CSV oficial corresponde al **SG Trend Indicator**, no al SG CTA Index; no se usa como
sustituto. El dato público más cercano localizado para el SG CTA es **0,61 desde enero de 2000**,
publicado por CFM el 2022-05-26 con fuente Bloomberg en la figura 2 de
[`A good time for trend following... but, then again, it's always been!`](https://www.cfm.com/wp-content/uploads/2022/12/39-A-Good-Time-for-Trend-Following-FINAL.pdf).
El texto leído dice literalmente: «This index has realized a Sharpe ratio of 0.61 since its
inception in January 2000». Es fuente secundaria, no verificación primaria de SG. El **0,56**
del brief permanece `[no verificado]`; no se borra ni se sustituye silenciosamente.

### Revisión de B y C con los datos medidos

- **B-0, B-1, B-2, B-4 y B-5:** no cambian de severidad ni de conclusión. No se ha medido una
  señal y no se ha tocado el criterio.
- **B-3 sube de ALTO a CRÍTICO:** solo nueve de las 18 series quedan limpias bajo la regla de
  huecos y nulos. Ya no es un riesgo abstracto de proveedor: determina qué mitad del universo
  no puede entrar.
- **B-6 permanece ALTO**, pero se actualiza su escenario. Con el CAGR ajustado medido de URTH,
  el exceso neto anual ilustrativo sobre DFR para capital pequeño es 7,536972 %; un coste de
  2.400 €/año exigiría 31.843,03 € para no superarlo. Sigue siendo un escenario de coste del
  brief, no un presupuesto medido.
- **C-1 queda reforzada:** su referencia ya está medida con dividendos. Su columna contra el
  mundo sigue siendo cero porque es el benchmark, pero el nivel en euros y el exceso sobre DFR
  suben al corregir el insumo.
- **C-2 queda debilitada cuantitativamente:** el 4,9 % sigue siendo secundario `[no verificado]`
  y su diferencia contra el mundo empeora. Su prueba además solo podría usar las series limpias
  o datos reparados y explicados.
- **Orden de descarte:** no cambia; C-1 sigue antes que C-2.

Comando completo que produce los nuevos importes y el B-6 actualizado:

```
$ python3 fix-fase2/fase0_n10/cierre_bc_recalculo.py
=== A-3: series utilizables sin huecos ni cierres nulos ===
limpias=9/18: ^GSPC,EEM,IEF,TLT,DBC,BTC-EUR,ETH-EUR,VNQ,URTH
excluidas=9/18: ^STOXX50E,^IBEX,^TNX,GC=F,CL=F,HG=F,EURUSD=X,JPY=X,^VIX
=== Recalculo B-6 y Paso C ===
fuente_URTH=salida_cierre_a5_ajuste_y_urth.json CAGR_adjclose=11.804904 %
fuente_DFR=salida_cierre_a6_dfr_sg.json fecha=2026-11-06 DFR=2.500 %
B-6 exceso_neto_mundo_menos_DFR=7.536972 %; capital_min_con_coste_2400=31843.03 €
C-1_mundo capital=1000 neta=95.62 € vs_DFR=+75.37 € vs_mundo=+0.00 €
C-1_mundo capital=10000 neta=956.20 € vs_DFR=+753.70 € vs_mundo=+0.00 €
C-1_mundo capital=100000 neta=9445.87 € vs_DFR=+7420.87 € vs_mundo=+0.00 €
C-2_tendencia capital=1000 neta=39.69 € vs_DFR=+19.44 € vs_mundo=-55.93 €
C-2_tendencia capital=10000 neta=396.90 € vs_DFR=+194.40 € vs_mundo=-559.30 €
C-2_tendencia capital=100000 neta=3969.00 € vs_DFR=+1944.00 € vs_mundo=-5476.87 €
C-1 usa CAGR histórico medido, no esperanza futura; C-2 conserva 4,9 % secundario [no verificado].
IRPF como realización anual; sin comisiones ni coste de sistema.
salida=fix-fase2/fase0_n10/salida_cierre_bc_recalculo.json
```

**C-1 corregida — escenario histórico anualizado, no pronóstico:**

| Capital | Escenario neto anual | Contra DFR | Contra índice mundial |
|---|---:|---:|---:|
| 1.000 € | 95,62 € | +75,37 € | 0,00 € |
| 10.000 € | 956,20 € | +753,70 € | 0,00 € |
| 100.000 € | 9.445,87 € | +7.420,87 € | 0,00 € |

**C-2 corregida — conserva el insumo secundario del 4,9 %:**

| Capital | Escenario neto anual | Contra DFR | Contra índice mundial |
|---|---:|---:|---:|
| 1.000 € | 39,69 € | +19,44 € | −55,93 € |
| 10.000 € | 396,90 € | +194,40 € | −559,30 € |
| 100.000 € | 3.969,00 € | +1.944,00 € | −5.476,87 € |

Ambas tablas mantienen el supuesto de realización anual del IRPF y excluyen comisiones y coste
del sistema. No son retornos esperados ni autorización para operar.

### Estado binario actualizado de los seis NO-GO

| # | Estado actualizado | Evidencia |
|---|---|---|
| 1 | **NO SE DISPARA** | A-1 no encontró medición previa ejecutada de memoria de precios ni criba de mercados. |
| 2 | **NO SE DISPARA; el anterior queda REVOCADO** | Todas las tandas nuevas tuvieron comprobación previa 200 y cuerpo útil; A-2 obtuvo 200 en las tres llamadas. No procede aplicar el protocolo de fallo. |
| 3 | **NO SE DISPARA** | No se backtesteó ninguna regla ni se calculó Sharpe de una señal. Se leyó una cifra externa ya publicada. |
| 4 | **NO SE DISPARA** | La §4 permanece intacta; solo se sustituyó un insumo marcado `[no verificado]` por medición propia. |
| 5 | **NO SE DISPARA** | Las dos candidatas se conservan, con sus tablas recalculadas. |
| 6 | **NO SE DISPARA** | B-0 mantiene su conclusión y su severidad. |

**Fase 0 cerrada tras A, B, C y el Paso D externo ya escrito por Claude.** No se ejecutó §6 y
la §8 sigue requiriendo el OK escrito de Pablo. Antes de cualquier Alcance siguen pendientes las
correcciones de multiplicidad y benchmark señaladas en D, además de la exclusión o reparación
documentada de las series defectuosas encontradas en A-3.

---

## Paso D · Apéndice — Verificación del cierre

**Fecha:** 2026-11-06, 10:17 a 10:35 UTC. **Verificador:** Claude Opus 5, otro proveedor
que el ejecutor. Se verifican las cinco mediciones nuevas con comandos propios.

**Veredicto:** el cierre se sostiene. **Dos de sus cifras corrigen a este Paso D**, y en
las dos tiene razón él. Una de ellas destapa un defecto de mi propio brief que ninguna
tarea del expediente había visto.

### D-8 · Mi 12,111 % de URTH era de ayer. El suyo es el vigente, y la vara de medir es más frágil de lo que escribí — **CORRIGE A D-3**

D-3 afirmó que el índice mundial da **12,111 %** y que esa era la cifra real. Él midió
**11,804904 %** y escribió que usaba la suya «no la del verificador». Tenía razón, y la
causa no es un método distinto:

```
$ bash por-que-12111.sh
  2026-11-04  adjclose=207.8700  var=+1.76 %
  2026-11-05  adjclose=199.6300  var=-3.96 %
  CAGR con el ultimo cierre     = 11.8052 %
  CAGR con el penultimo cierre  = 12.1132 %
```

**El mundo cayó 3,96 % el 5 de noviembre.** Mi medición, hecha a las 01:30 UTC, usaba el
cierre del 4; la suya usa el del 5. Mi reproducción independiente de ahora da
**11,805161 %** contra su **11,804904 %**: coinciden hasta el cuarto decimal, y la
diferencia residual es el denominador de años.

Lo que esto destapa importa más que la cifra: **un CAGR punto a punto se mueve 0,31
puntos con un solo día de mercado.** La §4 define la vara de medir como «el retorno
anualizado del índice mundial» sin fijar la fecha de corte ni el método, así que el
listón que toda candidata tiene que batir cambia según el día en que alguien lo calcule.
Lo que sí es robusto es la **diferencia `adjclose` menos `close`: 2,0537 pp** medidos por
él, 2,060 por mí el lunes, 2,053 ahora. El nivel absoluto no lo es.

**Qué cambia:** antes de la §6, la vara de medir necesita una fecha de corte congelada y
su `sha256`, o una media de ventanas móviles, declaradas en la §4. Un número que se mueve
con la sesión de ayer no puede ser el umbral de una decisión.

### D-9 · Su método de huecos encuentra lo que mi A-3 ocultaba por construcción — **CRÍTICO, y el defecto es de mi brief**

Mi A-3 pedía «cuántos huecos tiene cada serie respecto al calendario de su mercado», y mi
propia medición del lunes lo hizo como `1 − velas/esperados`. Puesta al lado de su
clasificación de hoy, mi métrica da **0,0 % de huecos a EURUSD=X, JPY=X y ^VIX**, las tres
que él excluye. Esto no es un desacuerdo: es que mi métrica **no puede** verlo.

```
$ bash por-que-12111.sh
  ticker        mis huecos% (lunes)   su veredicto hoy
  EURUSD=X                      0.0           excluida
  JPY=X                         0.0           excluida
  ^VIX                          0.0           excluida
```

Verificado por qué, contando las observaciones por día de la semana:

```
$ bash verificar-viernes-eurusd.sh
  EURUSD=X: velas=5985
    2004-2005  lun=104  mar=104  mie=104  jue=105  vie=43  sab=0  dom=62
    2024-2025  lun=105  mar=105  mie=105  jue=104  vie=44  sab=0  dom=60
  JPY=X: velas=7833
    2004-2005  lun=104  mar=104  mie=104  jue=105  vie=43  sab=0  dom=62
    2024-2025  lun=105  mar=105  mie=105  jue=104  vie=44  sab=0  dom=60
```

**43 viernes de los 104 que debería haber, y 60 domingos que no deberían existir**, en
las dos divisas y en las dos épocas, veinte años aparte. Un total agregado que divide
velas entre días hábiles **se autocancela**: los domingos espurios tapan exactamente los
viernes que faltan, y la serie parece perfecta. Él lo vio porque comparó **fecha a
fecha** y contó duplicados y nulos, que es lo que mi brief no pidió.

**Qué cambia:** su subida de **B-3 de ALTO a CRÍTICO** queda acreditada con dato propio.
Nueve de las dieciocho series no entran, y entre ellas las dos divisas tienen un defecto
que no es un hueco de festivo sino un desplazamiento sistemático del día de la
observación. Cualquier autocorrelación a 1 día calculada sobre esas series mediría el
artefacto, no el mercado. Y la A-3 de cualquier tarea futura tiene que exigir el reparto
por día de la semana, no un porcentaje agregado.

### D-10 · Lo que confirmé y coincide

- **A-2.** `range=max` da **169 velas con granularidad `3mo`** y `period1=0` da **14.334
  diarias desde 1970-01-02**. La §2.2 del brief queda confirmada en mecánica y en rango;
  mis 14.083 de esta madrugada eran con `period2` de hace un año, 251 velas menos, un año
  hábil exacto.
- **A-6, el DFR.** Verificado por mí en la fuente primaria del BCE, dos observaciones:
  `fecha=2026-11-05 DFR=2.5 %` y `fecha=2026-11-06 DFR=2.5 %`. Coincide con el suyo.
- **Los seis JSON del cierre parsean**, y sus cifras coinciden con lo pegado:
  `"cagr_close": 0.0975123201574275` y `"cagr_adjclose": 0.11804903679636802` son
  exactamente los 9,751232 % y 11,804904 % del texto. Cero bloques fabricados, por
  segunda vez.
- **No se tocó la §4.** Sustituir un insumo marcado `[no verificado]` por una medición
  propia no es modificar el criterio, y su lectura del NO-GO 4 es la correcta.

### D-11 · Lo que sigue sin verificar, y no lo doy por bueno

- **El Sharpe 0,56 del SG CTA Index** sigue `[no verificado]`, y hace bien en no
  sustituirlo en silencio. Que el CSV oficial de SG sea el **Trend Indicator** y no el CTA
  Index es una distinción que yo no había hecho en el brief. El **0,61 de CFM** que
  localiza **no lo he comprobado y por tanto no lo afirmo**: es fuente secundaria y queda
  igual de pendiente que el 0,56.
- **El 4,9 % de tendencia profesional de C-2** sigue siendo secundario. Su tabla lo
  declara.
- **El coste operativo del sistema** no está medido en ninguna parte. B-6 usa los 2.400 €
  del ejemplo del brief, no un presupuesto.

### Estado de la Fase 0 tras este apéndice

| | |
|---|---|
| Pasos A, B, C | **cerrados**, con A-2 a A-6 ejecutados y verificados |
| Paso D y este apéndice | **hechos**, por verificador de otro proveedor |
| **NO-GO** | **ninguno disparado.** El 2 queda revocado por mi propio defecto de redacción |
| Correcciones obligatorias antes de cualquier Alcance | **tres**: multiplicidad (D-4), vara de medir congelada (D-8) y las nueve series defectuosas, excluidas o reparadas con explicación (D-9) |
| §6 y §8 | **sin ejecutar y sin firma** |

**Lo que no decide ningún verificador:** si la §6 se ejecuta, con qué pasos, y si las tres
correcciones se aplican antes. Eso es de Pablo, y la §8 sigue en blanco.
