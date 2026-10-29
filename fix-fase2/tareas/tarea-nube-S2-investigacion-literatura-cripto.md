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
