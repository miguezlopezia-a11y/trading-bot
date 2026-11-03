"""N7 · A-2 — Reproducir sharpe_anual=1.008 y bench_sharpe=1.164 con
implementacion propia, desde results/portfolio_equity.csv y
results/portfolio_benchmark.csv.  Corre DESDE fix-fase2/.

Sharpe reescrito a mano (media/sd muestral de los retornos simples * sqrt(365)),
sin importar nada de src/.  Salida: a2_salida.json
NO-GO del brief: si no reproducen al TERCER DECIMAL, PARAR.
"""
import json
import math

import numpy as np
import pandas as pd

PPY = 365
OBJ_ST = 1.008
OBJ_BE = 1.164
TOL = 5e-4          # "al tercer decimal": |mio - publicado| < 0.0005


def sharpe_anual(serie):
    """Sharpe anualizado de una curva de equity: pct_change, media/sd, *sqrt(365).
    sd con ddof=1 (pandas por defecto), que es lo que usa el codigo publicado
    via pd.Series.std()."""
    r = serie.pct_change().dropna()
    x = np.asarray(r.values, dtype=float)
    sd = float(np.std(x, ddof=1))
    return (float(np.mean(x)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0, len(x)


def sharpe_anual_ddof0(serie):
    r = serie.pct_change().dropna()
    x = np.asarray(r.values, dtype=float)
    sd = float(np.std(x, ddof=0))
    return (float(np.mean(x)) / sd * math.sqrt(PPY)) if sd > 0 else 0.0, len(x)


def main():
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    be = pd.read_csv("results/portfolio_benchmark.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    out = {}
    print("=== A-2.1 las dos curvas ===")
    for nom, s in [("equity", eq), ("benchmark", be)]:
        print(f"  {nom:<10} {len(s)} dias  {s.index[0].date()} -> "
              f"{s.index[-1].date()}  {s.iloc[0]} -> {s.iloc[-1]}")
        out[nom] = {"dias": len(s), "ini": str(s.index[0].date()),
                    "fin": str(s.index[-1].date()),
                    "v0": float(s.iloc[0]), "vN": float(s.iloc[-1])}
    print(f"  mismas fechas: {bool((eq.index == be.index).all())}")
    out["mismas_fechas"] = bool((eq.index == be.index).all())

    print("=== A-2.2 Sharpe anualizado, implementacion propia ===")
    s_st, n_st = sharpe_anual(eq)
    s_be, n_be = sharpe_anual(be)
    s_st0, _ = sharpe_anual_ddof0(eq)
    s_be0, _ = sharpe_anual_ddof0(be)
    print(f"  estrategia  ddof=1: {s_st:.6f}  (publicado {OBJ_ST})  n={n_st}")
    print(f"  estrategia  ddof=0: {s_st0:.6f}")
    print(f"  benchmark   ddof=1: {s_be:.6f}  (publicado {OBJ_BE})  n={n_be}")
    print(f"  benchmark   ddof=0: {s_be0:.6f}")

    print("=== A-2.3 retornos totales ===")
    r_st = (eq.iloc[-1] / eq.iloc[0] - 1) * 100
    r_be = (be.iloc[-1] / be.iloc[0] - 1) * 100
    print(f"  retorno_pct       mio={r_st:.2f}   publicado=317.52")
    print(f"  bench_retorno_pct mio={r_be:.2f}   publicado=132831.04")

    print("=== A-2.4 max drawdown ===")
    def mdd(s):
        return float(((s - s.cummax()) / s.cummax()).min() * 100)
    print(f"  max_dd_pct        mio={mdd(eq):.2f}   publicado=-26.9")
    print(f"  bench_max_dd_pct  mio={mdd(be):.2f}   publicado=-88.96")

    ok_st = abs(round(s_st, 3) - OBJ_ST) < TOL
    ok_be = abs(round(s_be, 3) - OBJ_BE) < TOL
    out.update({
        "sharpe_estrategia_ddof1": s_st, "sharpe_estrategia_ddof0": s_st0,
        "sharpe_benchmark_ddof1": s_be, "sharpe_benchmark_ddof0": s_be0,
        "publicado_estrategia": OBJ_ST, "publicado_benchmark": OBJ_BE,
        "retorno_pct": round(r_st, 2), "bench_retorno_pct": round(r_be, 2),
        "max_dd_pct": round(mdd(eq), 2), "bench_max_dd_pct": round(mdd(be), 2),
        "reproduce_estrategia": bool(ok_st), "reproduce_benchmark": bool(ok_be),
        "n_retornos_estrategia": n_st, "n_retornos_benchmark": n_be,
    })
    print("=== A-2.5 veredicto del NO-GO ===")
    print(f"  1.008 reproduce al 3er decimal: {ok_st}  (round={round(s_st,3)})")
    print(f"  1.164 reproduce al 3er decimal: {ok_be}  (round={round(s_be,3)})")
    veredicto = "NO-GO NO SE DISPARA" if (ok_st and ok_be) else "NO-GO SE DISPARA: PARAR"
    out["veredicto_nogo"] = veredicto
    print(f"  -> {veredicto}")

    json.dump(out, open("fase0_n7/a2_salida.json", "w"), indent=2)
    print("-> fase0_n7/a2_salida.json")


if __name__ == "__main__":
    main()
