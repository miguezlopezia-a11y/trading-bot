# Estado tras la auditoría N1 del harness — lo que el próximo agente debe saber

**Creado:** 2026-11-01 por la sesión N1 en la nube (Claude Code, Opus 5).
**Sustituye a:** el ancla `shared/estado-y-siguiente-paso.md`, que **no existe
en este repo** (decisión de Pablo, §8 de la tarea N1). Pablo replica este
archivo al búnker a mano.
**Informe completo:** `fix-fase2/docs/auditoria_harness_n1.md`.
**Scripts:** `fix-fase2/auditoria_n1/*.py`, cada uno ejecutable por separado.

---

## 1. Lo que cambia en el expediente

**El harness está limpio.** La auditoría no encontró ningún defecto del
instrumento de medida que invalide ningún dictamen: ni look-ahead, ni costes
mal modelados, ni doble contabilización, ni no-determinismo. Fase A se sostiene.
Fase B **queda en duda**, no por el harness, sino por cómo se construye la `V`
que deflacta su Sharpe. TimesFM queda sin verificar por reproducción.

El vínculo código↔resultados quedó **establecido con prueba**, que era la
condición de parada: `rigor_estadistico.py` reejecutado reproduce
`results/rigor_estadistico.json` en **245/245 campos**, dos veces seguidas; y
el portfolio de Fase B reproduce `results/portfolio_runner.json` **exacto**
con el sello `20261007`. Antes de esta auditoría eso no se había comprobado
nunca, y era la asunción más débil de todo el expediente.

**Pero la cifra que ordena el expediente SÍ se mueve.** Los pasos 3.0c y
3.0d, que Pablo añadió el 2026-11-01 desde la némesis de N2, cambian la lectura
de Fase B. Está en el hallazgo H10 de abajo, y es lo primero que hay que leer:
el listón de 1.312 pasa a **0.823** si `V` se mide con `T` homogéneo, y el
Sharpe observado (1.008) cae **en medio** de las dos construcciones. La brecha
+0.304 se reproduce exacta, pero **no es robusta**.

Por eso el veredicto de Fase B en el informe es **QUEDA EN DUDA**, no "se
sostiene": el harness está limpio, el número del que cuelga no.

---

## 2. Los cinco hallazgos que hay que recordar

| id | Qué | Severidad | ¿Invalida algo? |
|---|---|---|---|
| H1 | `load_or_download()` componía el nombre del CSV con la fecha de hoy, así que no alcanzaba los congelados en ningún otro día: sin red reventaba, con red descargaba datos frescos **en silencio**. **Parcheado** en este trabajo. | CRÍTICO (era) | No. Nada publicado salió de datos equivocados: Fase B reproduce exacto. |
| H2 | Los tres criterios **bloqueantes** del `AUDIT_BRIEF.md` previo (AUDIT-A1 look-ahead, AUDIT-A2 drawdown, AUDIT-A3 comisión) **nunca tuvieron script**, mientras los cinco no bloqueantes sí. **Cerrados** en este trabajo. | CRÍTICO (era) | No. Los tres se cierran a favor del harness. |
| H3 | `V` (la otra mitad de `SR0`) **no se puede recalcular por tramo**: las 11 series que la componen cubren 2024-10→2026-10 y no solapan con T1 (2015-2018) ni T2 (2019-2022). La V de los tres tramos se estima en 2 años y se aplica a tramos que empiezan en 2015. | MEDIO | No el veredicto global. Sí la lectura de los **DSR por tramo** (0.824/0.772/0.301), que no son comparables entre sí como el expediente los presenta. |
| H4 | El **benchmark de exposición igualada** de Fase A está sesgado **al alza**: la máscara de posición de la estrategia selecciona días favorables para B&H (percentil medio 71% contra 2000 máscaras aleatorias; `sma_timing_50` al 96.5%). | MEDIO | No. El sesgo va **en contra** de las estrategias y Fase A ya moría por DSR, bootstrap y t de forma independiente. |
| H5 | 4 de los 23 `verificar_*.py` descargaban de yfinance **en tiempo de ejecución**, y ninguno comprobaba que la descarga trajese filas (fallaban con `IndexError` sobre un DataFrame vacío). | ALTO | No, pero hacía la suite no reproducible. Pasan 4/4 con el CSV congelado. |
| **H10** | **El listón del DSR no es robusto.** Pasa de **1.312** a **0.823** si `V` se mide con `T` homogéneo sobre el panel (3.0c), y el Sharpe observado 1.008 cae **en medio**. Las dos construcciones son defendibles y nadie había hecho la elección explícita. | **CRÍTICO** | **Sí: a Fase B.** No la invalida ni la rescata — la deja sin suelo numérico firme. Es el hallazgo más importante de N1. |
| H11 | El benchmark de Fase B **no estaba igualado en exposición**: cartera al 15,6% contra B&H al 100%. Fase A sí aplicó la corrección; Fase B la omitió (3.0d). | ALTO | Al "pierde vs B&H": medido a igual exposición pierde por **0.063**, no por 0.156. El dictamen se sostiene, ahora por la razón correcta. |
| H12 | **`N` no está reconciliado.** `timesfm_fase2_resultado.md:6` declara **N=14** registrado antes del primer forecast; el código y la reevaluación usan **12**. | ALTO | A la aritmética: con N=14 el listón es 1.349 y la brecha +0.341. **Contradicción abierta.** |

---

## 3. Lo que hay que arreglar y esta tarea NO arregló

Quedó fuera del alcance de escrituras que autorizó el §8. Por orden de
importancia:

1. **Repuntar permanentemente los 4 verificadores de red** (`verificar_a5_indicadores.py`,
   `verificar_a8_adversarial.py`, y `load_data()` de `run_backtest.py`, del
   que dependen `verificar_invariante_h1.py` y `verificar_opus_fase2.py`) a
   los CSV congelados, con aserción de "N filas > 0". El paso 3.7 demuestra
   que pasan 4/4 así; falta hacerlo permanente.
2. **`portfolio_supervivencia.congelar()` tiene el mismo defecto H1** que
   `load_or_download()` tenía (sello = fecha de hoy, descarga si falta). No
   se parcheó porque ese fichero no estaba en el alcance. El paso 3.6 lo
   sortea sustituyéndolo en memoria.
3. **Procedencia del código.** Los 36 CSV tienen hash + meta; los `.py` **no
   tienen ninguna**: llegaron en un solo commit desde un directorio del VPS
   que no estaba bajo git, y los `results/*.json` no registran ni versión ni
   hash del código que los generó. Esta auditoría cerró el agujero *a
   posteriori* reproduciendo las cifras, pero la próxima tendrá el mismo
   problema. Poner `/root/trading-bot-fix-fase2` bajo git y grabar en cada
   `results/*.json` el commit del código.
4. **`btc_usd_5y_1d.csv` no tiene `.sha256` ni `.meta.json`**, y es el único
   insumo de los 11 dictámenes de Fase A. Es el único de los 36 CSV sin ancla
   de integridad.
5. **`portfolio_resultado.md` sigue sin existir** y `REGISTRO_F.md` tampoco
   (sección 4). No se reconstruyen, por decisión de Pablo.

---

## 4. Documentos que no están y que el expediente cita

- **`fix-fase2/docs/portfolio_resultado.md`** — el documento primario del
  dictamen de Fase B. **No existe ni existió** en la historia de git. Por
  decisión de Pablo (§8) **no se reconstruye**. Sus cifras solo son
  recuperables de `fase_b_reevaluacion_resultado.md` (tabla del Paquete 3) y
  de `results/portfolio_runner.json`.
- **`REGISTRO_F.md`** — la evidencia que `fase_b_reevaluacion_resultado.md`
  cita para su "suite completa 15/15 PASS". No existe, ni el commit `9249cf4`
  que ese documento menciona. La afirmación 15/15 queda **no verificable**,
  con esa etiqueta: ni confirmada ni desmentida. Hoy la suite son **23**
  scripts, de los que pasan **20** (los 3 restantes necesitan torch/timesfm o
  un fichero de credenciales en `/root`).
- **`shared/`** — no existe en este repo y no va a existir. Cualquier brief
  que apunte ahí (como hacía la §2 de la tarea N1) está apuntando a nada.

---

## 5. Nomenclatura: no confundir las dos numeraciones

Decisión de Pablo (§8), porque colisionaban y el segundo cerebro tiene
grabada la vieja:

- **`AUDIT-S1`…`AUDIT-S6`** y **`AUDIT-A1`…`AUDIT-A8`** = las sospechas y los
  criterios de `fix-fase2/docs/AUDIT_BRIEF.md` (2026-10-05). Ahí `AUDIT-S1`
  es *look-ahead en fills* y `AUDIT-S3` es *comisión*.
- **`N1`** (esta auditoría del harness), **`N2`** (literatura), **`N3`**
  (ampliación de T) = las tareas en la nube.

`brain.py:75-78` sigue diciendo *"NO FIABLE hasta resolver S1 (look-ahead) y
S3 (comisión)"* con el significado **viejo**. Ese `S1`/`S3` es `AUDIT-S1` /
`AUDIT-S3`, y **ambos quedan resueltos** por los pasos 3.1 y 3.2 de N1. La
nota de `brain.py` está obsoleta; no se tocó porque está fuera de alcance.

---

## 6. Lo que esta auditoría NO cubrió

- **El vínculo código↔resultados de TimesFM.** `results/timesfm_t3_zeroshot.json`
  no se regeneró: hace falta `torch` y `timesfm`, que no están instalables en
  este entorno. El dictamen "TimesFM MUERTA" queda **sin verificar** por
  reproducción, aunque su cifra (dir_acc 0.4925) sí se confirmó en el
  documento.
- **El camino de paper trading.** `risk_veto.py`, `paper_runner.py` y
  `deliberation.py` **no están en la ruta del backtest** y no contribuyeron a
  ninguno de los cuatro dictámenes. No se auditaron (y el §3.6 original lo
  prohibía).
- **La fecha real de listado de FIL** (y de cualquier otro activo). Sin fuente
  externa no es acotable. Queda como límite declarado, igual que en el
  expediente.
- **Look-ahead en barras no probadas.** La invariancia de prefijo se probó en
  una rejilla de 40 valores de `t` (single-asset) y 10 (portfolio), no en
  todas las barras.

---

## 7. Siguiente paso, según lo que esta auditoría deja en pie

**El harness no es el problema. La métrica sí.** Y eso reordena lo que viene.

Lo que esta auditoría deja decidido:

- La conclusión es **robusta al alza de `N`** (se sostiene para todo N ≥ 5, y
  solo caería si los intentos reales hubiesen sido ≤ 4).
- El DSR es **más sensible a `V` que a `N`**: subir `N` de 12 a 50 mueve el
  listón +0.31, mientras cambiar la construcción de `V` lo mueve −0.49.
- **La palanca `T` está cerrada.** N3 demostró que `t` es exactamente
  invariante a la frecuencia de muestreo, que el umbral DSR **sube** al pasar
  a horario (1.312 → 1.317…1.325) y que cerrar la brecha por ventana de
  calendario exigiría **~96 años** de historia. **Más datos no es la salida**,
  y este informe no la propone.

Lo que queda abierto, y es una decisión de Pablo, no un resultado:

1. **Cuál es la `V` correcta.** Es la pregunta que decide si hay brecha o no la
   hay. Las dos construcciones están medidas en 3.0c con sus sesgos a la vista.
   Cambiarla después de ver el resultado sería cambiar la métrica —prohibido—,
   así que la decisión tiene que justificarse por el método, no por el número
   que produce.
2. **Reconciliar `N`**: 12 o 14. Y escribir la regla de qué cuenta como trial.
   N2 · B2 propone `fix-fase2/docs/registro_N.md` con una línea por trial.
   Sin ese libro de cuentas, toda la aritmética del DSR es sobre un número que
   nadie puede auditar.

Nada se activa. Fase B sigue siendo candidata — pero ya no "a más datos", sino
a que se cierre cómo se mide su propio listón.
