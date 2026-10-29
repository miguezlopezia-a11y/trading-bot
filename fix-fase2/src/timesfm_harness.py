"""Harness compartido TimesFM 2.5 para la tarea timesfm-fase2 (rama
fase2/timesfm-multiactivo). Pesos 2.5 Apache-2.0 UNICAMENTE (Fase 0 §4).

Sin LLM dentro. El venv es el del spike (timesfm 3.0.2 + torch CPU), fuera
del repo. Este modulo solo define funciones puras de carga/forecast/metricas.

Metrica decisiva direccional: dir_acc por DIA de horizonte h=1..5 (signo del
retorno diario real vs predicho), agregada sobre ventanas y activos. La
t-stat es la binomial bajo H0 p=0.5: t = (p - 0.5) / sqrt(0.25 / n_obs).
"""
import numpy as np

CTX = 512
H = 14
STEP = 7
TRAIN_FRAC = 0.6
H_DECISIVO = 5          # horizontes h=1..5 para la metrica decisiva
SEED = 42


def load_model():
    import timesfm
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        "google/timesfm-2.5-200m-pytorch")
    model.compile(forecast_config=timesfm.ForecastConfig(
        max_context=CTX, max_horizon=H, normalize_inputs=True,
        force_flip_invariance=True, infer_is_positive=True,
        fix_quantile_crossing=True))
    return model


def forecast_windows(model, series, split_idx, ctx=CTX, h=H, step=STEP):
    """Rolling forecast sobre las ventanas [start, start+ctx+h) con
    start >= split_idx. Devuelve (y_true, y_pred) de shape (W, h)."""
    n = len(series)
    y_true, y_pred = [], []
    for start in range(split_idx, n - h - ctx, step):
        c = series[start:start + ctx]
        fut = series[start + ctx:start + ctx + h]
        point, _ = model.forecast(horizon=h, inputs=[c])
        y_true.append(fut)
        y_pred.append(point[0])
    return np.array(y_true), np.array(y_pred)


def dir_acc_diaria(y_true, y_pred, h_dec=H_DECISIVO):
    """dir_acc por dia de horizonte 1..h_dec: acierto del signo del retorno
    diario. Devuelve (accuracy, n_obs, t_binomial)."""
    yt = y_true[:, 1:h_dec + 1]
    yp = y_pred[:, 1:h_dec + 1]
    y0_t = y_true[:, 0:h_dec]
    y0_p = y_pred[:, 0:h_dec]
    sign_t = np.sign(yt / y0_t - 1)
    sign_p = np.sign(yp / y0_p - 1)
    mask = (sign_t != 0)
    acierto = (sign_t == sign_p) & mask
    n = int(mask.sum())
    p = float(acierto.sum()) / n if n else 0.0
    t = (p - 0.5) / np.sqrt(0.25 / n) if n else 0.0
    return p, n, float(t)


def mase(y_true, y_pred, seasonality=1):
    """MASE vs naive de paso=seasonality sobre todos los puntos."""
    num = np.abs(y_true - y_pred).mean()
    den = np.abs(y_true[:, seasonality:] - y_true[:, :-seasonality]).mean()
    return float(num / den) if den > 0 else float("nan")


def serie_sintetica(n, drift, sigma, seed):
    """Serie de niveles con drift y ruido lognormal suave (seed fija)."""
    rng = np.random.default_rng(seed)
    rets = drift + rng.normal(0, sigma, n)
    return 100.0 * np.exp(np.cumsum(rets))
