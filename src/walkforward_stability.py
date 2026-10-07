"""1.4 — Walk-forward de ESTABILIDAD de ma_cross (post-fix, Fase 2).

Solo mide estabilidad: MISMO codigo, MISMO parametros, distintas ventanas.
Prohibido optimizar parametros. Para cada configuracion (train_days, test_days)
rueda ventanas a lo largo de todo el dataset y reporta por fold el retorno OOS.

Salida: tabla por configuracion (folds, % positivos, media, mediana, std,
min, max) y dictamen final: estable / fragil. El dictamen lo consume
paper_runner.py (modo observacion si fragil).

Fix 2026-10-07 (hallazgo de Opus, decision de Pablo): un fold sin operaciones
tiene oos_return_pct=0.0, que no es >0 -- antes se contaba en el denominador
de pct_positivos como si fuera un fold perdedor. Ahora pct_positivos y las
estadisticas de retorno se calculan solo sobre folds con >=1 trade; la
cobertura real (que fraccion de folds tuvo alguna operacion) se reporta
aparte. Si ninguna configuracion llega a 5 folds con operaciones, el
dictamen por defecto es FRAGIL, nunca ESTABLE por ausencia de datos.

Uso: /opt/trading-bot/venv/bin/python src/walkforward_stability.py
     (desde /root/trading-bot-fix-fase2/ o /opt/trading-bot/)
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest, compute_metrics  # noqa: E402

PPY = 365
WARMUP = 200
STRATEGY = "ma_cross"
# (train_days, test_days) — medir estabilidad, no buscar la mejor ventana.
CONFIGS = [(365, 90), (730, 180), (180, 60), (365, 180)]


def load_data() -> pd.DataFrame:
    import yfinance as yf
    df = yf.download("BTC-USD", period="5y", interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()


def signals_with_warmup(df_full, start, end, fn):
    a = max(0, start - WARMUP)
    full_signals = fn(df_full.iloc[a:end])
    return df_full.iloc[start:end], full_signals.iloc[start - a:]


def run_config(df_full, strategy_fn, train_d, test_d):
    folds = []
    start = 0
    while start + train_d + test_d <= len(df_full):
        test_start = start + train_d
        test_end = test_start + test_d
        test_data, sig_v = signals_with_warmup(df_full, test_start, test_end, strategy_fn)
        res = run_backtest(test_data, sig_v)
        m = compute_metrics(res["equity"], res["trades"], PPY)
        folds.append({"fold": len(folds) + 1,
                      "test_start": str(test_data.index[0].date()),
                      "oos_return_pct": m["total_return_pct"],
                      "oos_sharpe": m["sharpe"], "trades": m["trades"]})
        start += test_d
    return folds


def summarize(folds):
    con_trades = [f for f in folds if f["trades"] > 0]
    rets = [f["oos_return_pct"] for f in con_trades]
    pos = sum(1 for r in rets if r > 0)
    arr = np.array(rets, dtype=float)
    return {
        "n_folds": len(folds),
        "n_folds_con_trades": len(con_trades),
        "cobertura_pct": round(len(con_trades) / len(folds) * 100, 1) if folds else 0.0,
        "pct_positivos": round(pos / len(con_trades) * 100, 1) if con_trades else 0.0,
        "media_pct": round(float(arr.mean()), 2) if len(arr) else 0.0,
        "mediana_pct": round(float(np.median(arr)), 2) if len(arr) else 0.0,
        "std_pct": round(float(arr.std(ddof=1)), 2) if len(arr) > 1 else 0.0,
        "min_pct": round(float(arr.min()), 2) if len(arr) else 0.0,
        "max_pct": round(float(arr.max()), 2) if len(arr) else 0.0,
    }


def verdict(summaries):
    """Dictamen estricto y reproducible: ESTABLE solo si TODA configuracion con
    folds suficientes es consistentemente positiva (>=60% folds positivos y
    media > 0). Si alguna ventana es debil/mixta -> FRAGIL (modo observacion).
    Con señales de baja frecuencia (~1 trade por fold de 90d) una ventana mixta
    basta para no confiar en modo aprobacion. Umbral de 5 sobre folds CON
    operaciones; sin ninguna configuracion evaluable, FRAGIL por defecto."""
    evaluables = [s for s in summaries if s["n_folds_con_trades"] >= 5]
    if not evaluables:
        return "fragil"
    for s in evaluables:
        if not (s["pct_positivos"] >= 60 and s["media_pct"] > 0):
            return "fragil"
    return "estable"


def main():
    df = load_data()
    fn = STRATEGIES[STRATEGY]
    print(f"Walk-forward estabilidad {STRATEGY} — {len(df)} velas "
          f"({df.index[0].date()} -> {df.index[-1].date()}). Sin optimizar parametros.")

    out = {"estrategia": STRATEGY, "configs": {}, "folds": {}, "dictamen": None}
    summaries = []
    for train_d, test_d in CONFIGS:
        folds = run_config(df, fn, train_d, test_d)
        s = summarize(folds)
        summaries.append(s)
        out["configs"][f"{train_d}/{test_d}"] = s
        out["folds"][f"{train_d}/{test_d}"] = folds
        print(f"\n[train {train_d}d / test {test_d}d] folds={s['n_folds']} "
              f"con_trades={s['n_folds_con_trades']} (cobertura {s['cobertura_pct']}%) "
              f"positivos={s['pct_positivos']}% media={s['media_pct']}% "
              f"mediana={s['mediana_pct']}% std={s['std_pct']}% "
              f"min={s['min_pct']}% max={s['max_pct']}%")
        for f in folds:
            print(f"    fold {f['fold']:>2} ({f['test_start']}): {f['oos_return_pct']:>7.2f}%  "
                  f"Sharpe {f['oos_sharpe']:>5}  trades {f['trades']}")

    v = verdict(summaries)
    out["dictamen"] = v
    print(f"\nDICTAMEN: ma_cross es {v.upper()} en walk-forward post-fix "
          f"({'modo observacion' if v == 'fragil' else 'modo aprobacion'} en paper runner).")
    with open("results/walkforward_stability.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("-> results/walkforward_stability.json guardado")


if __name__ == "__main__":
    main()
