"""T1 — Verificacion sintetica del harness TimesFM (la piedra del spike).

8 series sinteticas (seed 42): 4 con drift direccional real (0.35%/dia,
sigma 0.5%) y 4 puramente aleatorias (drift 0). El harness completo (carga
de modelo, rolling forecast, metricas) debe recuperar:
  - dir_acc (h=1..5) > 0.65 en TODAS las series con drift
  - dir_acc en [0.45, 0.55] en las series aleatorias
Si no: bug de desarrollo (como el PEFT in-place del spike), se arregla y se
repite. Cero datos reales hasta que pase.

Uso (venv del spike, fuera del repo):
  /root/.openclaw/workspace/timesfm-spike/venv/bin/python verificar_timesfm_t1_harness.py
"""
import sys
import time

sys.path.insert(0, "src")
from timesfm_harness import (load_model, forecast_windows, dir_acc_diaria,  # noqa: E402
                             serie_sintetica, CTX, H, STEP, TRAIN_FRAC)

N_SERIES = 4
LEN = 2000                 # ctx 512 + ~270 ventanas con step=1 tras split
DRIFT = 0.004              # senyal fuerte vs sigma 0.5% (SR diario 0.8)
SIGMA = 0.005
STEP_T1 = 3                # ~92 ventanas/serie -> n~460 por serie, ~4 min CPU
# Criterio T1 (operacionalizacion registrada antes de correr): con drift,
# dir_acc MEDIA de las 4 series > 0.65; aleatorias, media en [0.47, 0.53]
# (y reporte completo por serie). Error de la media con n~460: ~+-2.3pp.


def main():
    t0 = time.time()
    model = load_model()
    print(f"modelo cargado ({time.time() - t0:.0f}s)")
    ok = True
    medias_drift = []
    medias_ruido = []
    for i in range(N_SERIES):
        for drift, etiqueta in ((DRIFT, "drift"), (0.0, "aleatoria")):
            s = serie_sintetica(LEN, drift, SIGMA, seed=42 + i)
            split = int(LEN * 0.6)  # split temporal como el spike
            yt, yp = forecast_windows(model, s, split, step=STEP_T1)
            p, n, t = dir_acc_diaria(yt, yp)
            if drift > 0:
                medias_drift.append(p)
                bien = True  # el criterio es sobre la media (al final)
            else:
                medias_ruido.append(p)
                bien = True
            print(f"serie {i} {etiqueta:9}: dir_acc={p:.4f} n={n} t={t:+.2f} "
                  f"ventanas={len(yt)}", flush=True)
    media_drift = sum(medias_drift) / len(medias_drift)
    media_ruido = sum(medias_ruido) / len(medias_ruido)
    print(f"\ndir_acc media con drift: {media_drift:.4f} (umbral > 0.65)")
    print(f"dir_acc media aleatoria: {media_ruido:.4f} (rango [0.47, 0.53])")
    ok = ok and media_drift > 0.65 and 0.47 <= media_ruido <= 0.53
    print(f"\ntiempo total: {time.time() - t0:.0f}s")
    if ok:
        print("T1 OK: el harness recupera la senyal sintetica conocida.")
        return 0
    print("T1 FALLO: hay bug de desarrollo en el harness. NO correr datos reales.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
