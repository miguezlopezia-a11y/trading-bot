# TimesFM fase 2 multi-activo — resultado y dictamen

**Fecha:** 2026-10-12/13 · **Executor:** Kimi Code · **Rama:** `fase2/timesfm-multiactivo`
(cortada desde `fase-b-multiactivo` @ `3ad4795`; main intacto en `663db2c`).
**Pesos:** TimesFM 2.5 (Apache-2.0) únicamente — licencia leída en Fase 0.
**N=14** registrado antes del primer forecast (Estado de la tarea).
**Modelo:** API `TimesFm2_5ModelForPrediction` (transformers), venv del spike
(timesfm 3.0.2 + torch 2.14.1+cpu), todo CPU.

## Fase 0 — Revisión némesis (todo confirmado, ver `## Registro de revisión némesis` en la tarea)

Incluye el hueco real: el pre-registro `hipotesis-timesfm-fase2.md` no estaba
en el repo local de tareas (sí en el VPS), y el bug PEFT in-place del spike
confirmado físicamente (`zeroshot == lora_ft` en su JSON).

## T1 — Verificación sintética del harness — VERDE

8 series sintéticas (4 con drift real 0.4%/día, 4 aleatorias; seed 42;
n=1370 observaciones por serie; drift fuerte para que el umbral sea
evaluable). Salida real:

```
serie 0 drift    : dir_acc=0.6599 t=+11.83  -> OK      serie 0 aleatoria: 0.5161
serie 1 drift    : dir_acc=0.7058 t=+15.24  -> OK      serie 1 aleatoria: 0.5073
serie 2 drift    : dir_acc=0.7044 t=+15.13  -> OK      serie 2 aleatoria: 0.5168
serie 3 drift    : dir_acc=0.6715 t=+12.70  -> OK      serie 3 aleatoria: 0.5299
dir_acc media con drift: 0.6854 (umbral > 0.65)   tiempo total: 653s
T1 OK: el harness recupera la senyal sintetica conocida.
```

El harness es sano: recupera señal conocida y no inventa señal en ruido.

## T2 — Test diferencial anti-contaminación — VERDE

Base y base+adapter en **dos procesos independientes** (el forward del modelo
reserva ~4.1 GB de golpe y el VPS tiene 7 GB — dos instancias simultáneas
mueren por OOM; la solución son procesos secuenciales, que además es lo que
la tarea pide literalmente). Adapter entrenado 3 steps (ctx 64, lr 1e-3 —
hiperparámetros del *test de aplicación*, no del protocolo §4, documentado en
el propio script). Salida real:

```
proceso base OK [15s]   proceso ft OK [68s]
predicciones base : [1045.3  1044.03 1045.33 1046.15]
predicciones +lora: [1049.41 1049.45 1050.01 1049.43]
rel_diff = 0.003620 (umbral > 1e-3)
T2 OK: base y base+adapter difieren en procesos separados — el bug del spike esta cerrado.
```

## T3 — Zero-shot multi-activo vs naive — MUERTE INMEDIATA (H1)

10 supervivientes, walk-forward 60/40, 5665 observaciones direccionales
(h=1..5). Salida real:

| Activo | dir_acc | t | MASE | ventanas |
|---|---|---|---|---|
| ADA | 0.4378 | -2.93 | 2.75 | 111 |
| AVAX | 0.5423 | +1.36 | 3.21 | 52 |
| BNB | 0.5261 | +1.23 | 2.64 | 111 |
| BTC | 0.4904 | -0.57 | 3.02 | 177 |
| DOGE | 0.4865 | -0.64 | 2.75 | 111 |
| ETH | 0.4901 | -0.47 | 2.60 | 111 |
| LINK | 0.4649 | -1.66 | 2.43 | 111 |
| LTC | 0.4927 | -0.44 | 2.74 | 177 |
| SOL | 0.5279 | +0.97 | 2.80 | 61 |
| XRP | 0.5099 | +0.47 | 2.62 | 111 |
| **AGREGADO** | **0.4925** | **-1.13** | **2.75** | 1118 ventanas |

**Contra los umbrales pre-registrados de §2 (los únicos decisorios):**
- Muerte inmediata: dir_acc ≤ 0.52 o t < 2.0 → **dir_acc 0.4925, t -1.13 → H1 MUERTA.**
- Ni siquiera supervivencia parcial (que exigiría > 0.52): el agregado está
  por debajo de 0.50 — peor que el azar.
- MASE 2.75 vs naive: el modelo empeora ~2.7x el pronóstico de persisencia.
  8 de 10 activos con dir_acc < 0.53.

## Dictamen

**H1: MUERTA. H0 confirmada. El expediente TimesFM queda CERRADO.**

- La potencia no era el problema: 5665 observaciones direccionales (frente a
  ~420 del spike single-asset) y la señal sigue sin aparecer. La Fase 0 de la
  tarea lo anticipaba: "re-testear no es esperanza, es la corrección del
  déficit estadístico" — corregido el déficit, la respuesta es negativa con
  claridad.
- **H2 no se evalúa y queda muerta por condición**: la regla dura de §3
  ("si T1-T3 no están en verde, NO se ejecuta §4") y la muerte inmediata de
  §2 cierran el experimento antes del LoRA multi-activo. Entrenar un LoRA
  sobre un modelo cuyo zero-shot es peor que el azar, sin señal H1, sería
  exactamente el error de proceso que esta tarea existía para impedir.
- Cierre permanente según §4.7: solo se reabriría con un cambio de universo
  de datos (timeframe intradía, otra clase de activos), no con otra seed.

## Coste real

T1 653s + T2 ~80s + T3 190s ≈ **16 min de CPU** (muy por debajo del límite de
30 min de §3). Cero pipelines de entrenamiento ejecutados (§4 no arrancó).

## Qué se commitea

`src/timesfm_harness.py`, `verificar_timesfm_t1_harness.py`,
`verificar_timesfm_t2_diferencial.py`, `src/timesfm_t3_zeroshot.py`,
`results/timesfm_t3_zeroshot.json`, este documento. Nada toca
`paper_runner.py`, `risk_veto.py` ni `deliberation.py`. Sin push, sin merge.
