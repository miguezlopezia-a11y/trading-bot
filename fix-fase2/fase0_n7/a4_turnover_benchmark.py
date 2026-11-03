"""N7 · A-4 — Turnover REAL del benchmark igual-ponderado y su coste.
Corre DESDE fix-fase2/.  Salida: a4_salida.json

El brief pide `Sum|w_bench(t) - w_bench(t-1)|`. Esa formula mide el cambio del
VECTOR OBJETIVO, y los pesos objetivo del igual-ponderado son constantes
(1/|elig|): da 0 salvo los dias en que el conjunto elegible cambia. El turnover
que de verdad paga un rebalanceo diario es la vuelta de la DERIVA: los pesos se
mueven con los retornos del dia y hay que devolverlos a 1/|elig|. Se miden las
DOS y se dice cual es la buena.

Se replica la elegibilidad exacta de portfolio_runner.py:324
  elig = [i : rets.iloc[:t+1].iloc[:,i].notna().sum() >= LOOKBACK+1]
y la de la ESTRATEGIA, portfolio_runner.py:293-294
  s = rets[tk].iloc[:t] ; s.notna().sum() >= LOOKBACK+1
que NO es la misma ventana (hilo 4 de la §4.2 del brief).
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLOS = ["20261007", "20261009"]
COSTE_UNIT = pr.COMMISSION + pr.SLIPPAGE      # 0.0015


def series_elegibilidad(rets, lookback):
    """Devuelve (elig_bench, elig_estr): matrices booleanas (T, n).
    elig_bench replica :t+1 ; elig_estr replica :t ."""
    notna = (~np.isnan(rets)).astype(np.int64)
    cum = np.cumsum(notna, axis=0)                  # cum[t] = conteo en [:t+1]
    elig_bench = cum >= (lookback + 1)              # usa el dia t
    prev = np.vstack([np.zeros((1, rets.shape[1]), dtype=np.int64), cum[:-1]])
    elig_estr = prev >= (lookback + 1)              # usa solo [:t]
    return elig_bench, elig_estr


def main():
    out = {"coste_unitario": COSTE_UNIT, "sellos": {}}
    for sello in SELLOS:
        datos = pr.cargar_congelados(pr.ACTIVOS, stamp=sello, verbose=False)
        closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
        rets = closes.pct_change()
        R = rets.values
        T, n = R.shape
        eb, ee = series_elegibilidad(R, pr.LOOKBACK)

        print(f"\n=== A-4.1 sello {sello}: elegibilidad bench vs estrategia ===")
        dif_dias = int((eb != ee).any(axis=1).sum())
        dif_celdas = int((eb != ee).sum())
        bench_antes = int((eb & ~ee).sum())
        print(f"  dias {T}, activos {n}")
        print(f"  dias en que los dos conjuntos difieren : {dif_dias}")
        print(f"  celdas (dia,activo) que difieren        : {dif_celdas}")
        print(f"  celdas en que el BENCH admite y la estrategia NO: {bench_antes}")
        print(f"  celdas en que la ESTRATEGIA admite y el bench NO: "
              f"{int((ee & ~eb).sum())}")
        print("  -> el benchmark usa rets.iloc[:t+1]: cuenta el retorno DEL DIA t")
        print("     para decidir si el activo entra el dia t. La estrategia usa")
        print("     [:t]. El benchmark admite cada activo UN DIA ANTES.")

        # --- turnover (1) como lo escribe el brief: cambio del vector objetivo
        wt = np.zeros((T, n))
        for t in range(T):
            idx = np.where(eb[t])[0]
            if len(idx):
                wt[t, idx] = 1.0 / len(idx)
        tv_brief = np.abs(np.diff(np.vstack([np.zeros((1, n)), wt]), axis=0)).sum(axis=1)

        # --- turnover (2) el real: deriva del dia devuelta a 1/|elig|
        tv_real = np.zeros(T)
        w_hold = np.zeros(n)
        for t in range(T):
            r = np.nan_to_num(R[t], nan=0.0)
            # el bench del codigo invierte en los elegibles de t con peso 1/|elig|
            # y cobra el retorno del dia; la deriva se mide contra el objetivo de t+1
            val = w_hold * (1.0 + r)
            s = val.sum()
            w_drift = val / s if s > 0 else np.zeros(n)
            tv_real[t] = float(np.abs(wt[t] - w_drift).sum())
            w_hold = wt[t].copy()

        coste_brief = tv_brief * COSTE_UNIT
        coste_real = tv_real * COSTE_UNIT
        # drag compuesto sobre la curva del benchmark
        be = pd.Series(1.0, index=closes.index)
        bench_sin = [1.0]
        bench_con = [1.0]
        for t in range(T):
            idx = np.where(eb[t])[0]
            r_b = float(np.nanmean(R[t][idx])) if len(idx) else 0.0
            if np.isnan(r_b):
                r_b = 0.0
            bench_sin.append(bench_sin[-1] * (1 + r_b))
            bench_con.append(bench_con[-1] * (1 + r_b - coste_real[t]))
        bench_sin, bench_con = bench_sin[1:], bench_con[1:]

        print(f"=== A-4.2 sello {sello}: turnover del benchmark ===")
        print(f"  (1) formula del brief  Sum|w(t)-w(t-1)| :")
        print(f"      total={tv_brief.sum():.6f}  medio/dia={tv_brief.mean():.8f}"
              f"  dias con turnover>0={int((tv_brief>1e-12).sum())}")
        print(f"      coste total acumulado (suma simple) = "
              f"{100*coste_brief.sum():.4f} %")
        print(f"  (2) turnover REAL del rebalanceo diario (vuelta de la deriva):")
        print(f"      total={tv_real.sum():.4f}  medio/dia={tv_real.mean():.8f}"
              f"  dias con turnover>0={int((tv_real>1e-12).sum())}")
        print(f"      coste medio/dia = {1e4*coste_real.mean():.4f} bps"
              f"   anualizado = {100*coste_real.mean()*365:.3f} %/ano")
        print(f"=== A-4.3 sello {sello}: efecto compuesto sobre la curva ===")
        print(f"  bench sin coste (como hoy) : final={bench_sin[-1]:.4f}"
              f"  retorno={100*(bench_sin[-1]-1):.2f} %")
        print(f"  bench con coste real       : final={bench_con[-1]:.4f}"
              f"  retorno={100*(bench_con[-1]-1):.2f} %")
        fac = bench_con[-1] / bench_sin[-1]
        print(f"  factor de reduccion        : {fac:.6f}"
              f"  ({100*(fac-1):.2f} % del valor final)")

        def sharpe(curva):
            x = pd.Series(curva).pct_change().dropna().values
            sd = float(np.std(x, ddof=1))
            return float(np.mean(x) / sd * np.sqrt(pr.PPY)) if sd > 0 else 0.0
        s_sin, s_con = sharpe(bench_sin), sharpe(bench_con)
        print(f"  Sharpe bench sin coste     : {s_sin:.4f}")
        print(f"  Sharpe bench con coste real: {s_con:.4f}   (delta {s_con-s_sin:+.4f})")
        print(f"  -> la asimetria de 2.2 es {'MATERIAL' if abs(s_con-s_sin)>=0.05 else 'ANECDOTICA'}"
              f" en Sharpe (|delta| {abs(s_con-s_sin):.4f})")

        out["sellos"][sello] = {
            "T": int(T), "n": int(n),
            "elig_dias_difieren": dif_dias,
            "elig_celdas_difieren": dif_celdas,
            "elig_celdas_bench_admite_antes": bench_antes,
            "turnover_brief_total": float(tv_brief.sum()),
            "turnover_brief_medio": float(tv_brief.mean()),
            "turnover_brief_dias_no_cero": int((tv_brief > 1e-12).sum()),
            "turnover_real_total": float(tv_real.sum()),
            "turnover_real_medio": float(tv_real.mean()),
            "turnover_real_dias_no_cero": int((tv_real > 1e-12).sum()),
            "coste_real_bps_dia": float(1e4 * coste_real.mean()),
            "coste_real_pct_anual": float(100 * coste_real.mean() * 365),
            "bench_final_sin_coste": float(bench_sin[-1]),
            "bench_final_con_coste": float(bench_con[-1]),
            "bench_sharpe_sin_coste": s_sin,
            "bench_sharpe_con_coste": s_con,
            "delta_sharpe": s_con - s_sin,
            "material_en_sharpe": bool(abs(s_con - s_sin) >= 0.05),
        }
        np.savetxt(f"fase0_n7/a4_coste_bench_{sello}.csv", coste_real,
                   delimiter=",", header="coste_rebalanceo_diario", comments="")
    json.dump(out, open("fase0_n7/a4_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/a4_salida.json y fase0_n7/a4_coste_bench_*.csv")


if __name__ == "__main__":
    main()
