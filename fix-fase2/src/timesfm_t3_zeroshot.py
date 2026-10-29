"""T3 — Zero-shot multi-activo vs naive (nada de entrenamiento).

Un forecast por activo por ventana walk-forward sobre los 10 supervivientes
(data/multi/*_20261009.csv). Salida: dir_acc agregada (h=1..5) + t binomial +
MASE por activo, y agregado. Se compara con los umbrales pre-registrados §2:
  muerte: dir_acc <= 0.52 o t < 2.0
  parcial: dir_acc in (0.52, 0.55] con t in [2.0, 3.0)
  exito H1: dir_acc > 0.55 con t > 3

Este script NO decide solo: escribe results/timesfm_t3_zeroshot.json y el
dictamen se hace en docs/timesfm_fase2_resultado.md contra §2.

Uso (venv del spike, desde la raiz de la copia/rama):
  /root/.openclaw/workspace/timesfm-spike/venv/bin/python src/timesfm_t3_zeroshot.py
"""
import glob
import json
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from timesfm_harness import (load_model, forecast_windows, dir_acc_diaria,  # noqa: E402
                             mase, CTX, H, STEP, TRAIN_FRAC, H_DECISIVO)


def main():
    t0 = time.time()
    model = load_model()
    print(f"modelo cargado ({time.time() - t0:.0f}s)")
    cs = sorted(glob.glob("data/multi/*_20261009.csv"))
    per_activo = {}
    aciertos_total, obs_total = 0, 0
    mase_pond = []
    for path in cs:
        ticker = path.split("/")[-1].replace("_20261009.csv", "").upper()
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df.rename(columns=str.lower)["close"].to_numpy(dtype=np.float64)
        n = len(close)
        split = int(n * TRAIN_FRAC)
        if n - H - CTX <= split:
            per_activo[ticker] = "sin historia suficiente"
            continue
        yt, yp = forecast_windows(model, close, split)
        p, m, t = dir_acc_diaria(yt, yp)
        m_mase = mase(yt, yp)
        per_activo[ticker] = {"dir_acc": round(p, 4), "n_obs": m,
                              "t_binomial": round(t, 2),
                              "mase_naive": round(m_mase, 4),
                              "ventanas": len(yt)}
        aciertos_total += int(round(p * m))
        obs_total += m
        mase_pond.append((m_mase, m))
        print(f"{ticker:<10} dir_acc {p:.4f} t {t:+.2f} MASE {m_mase:.4f} "
              f"({len(yt)} ventanas) [{time.time() - t0:.0f}s]")

    p_agg = aciertos_total / obs_total
    t_agg = (p_agg - 0.5) / np.sqrt(0.25 / obs_total)
    mase_agg = float(np.average([m for m, _ in mase_pond],
                                weights=[w for _, w in mase_pond]))
    out = {"activos": per_activo,
           "agregado": {"dir_acc": round(p_agg, 4), "n_obs": obs_total,
                        "t_binomial": round(float(t_agg), 2),
                        "mase_naive": round(mase_agg, 4),
                        "h_decisivo": H_DECISIVO},
           "tiempo_s": round(time.time() - t0)}
    with open("results/timesfm_t3_zeroshot.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out["agregado"], indent=2))
    print(f"-> results/timesfm_t3_zeroshot.json ({time.time() - t0:.0f}s total)")


if __name__ == "__main__":
    main()
