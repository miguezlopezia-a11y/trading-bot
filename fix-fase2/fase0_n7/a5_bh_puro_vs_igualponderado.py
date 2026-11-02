"""N7 · A-5 — El igual-ponderado del codigo NO es buy & hold. Construir el B&H
puro y dar las dos curvas con sus dos Sharpes y sus dos retornos.
Corre DESDE fix-fase2/.  Salida: a5_salida.json

Definicion del B&H puro, declarada porque no es unica:
  un activo entra el primer dia en que es elegible (misma condicion que el
  codigo, rets.iloc[:t+1].notna().sum() >= LOOKBACK+1). El dia en que entra
  alguien, la cartera se reparte a peso igual entre los elegibles de ese dia y
  NO SE TOCA hasta la siguiente entrada. Esa es la lectura literal de "comprar
  a peso igual el primer dia elegible de cada activo y no tocar".
  Variante B declarada aparte: B&H solo sobre los activos elegibles el PRIMER
  dia (universo fijo, cero entradas posteriores).
"""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLOS = ["20261007", "20261009"]


def sharpe(curva):
    x = pd.Series(np.asarray(curva, dtype=float)).pct_change().dropna().values
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x) / sd * np.sqrt(pr.PPY)) if sd > 0 else 0.0


def mdd(curva):
    s = pd.Series(np.asarray(curva, dtype=float))
    return float(((s - s.cummax()) / s.cummax()).min())


def calmar(curva):
    s = pd.Series(np.asarray(curva, dtype=float))
    d = mdd(curva)
    anos = len(s) / pr.PPY
    return float((s.iloc[-1] / s.iloc[0] - 1) / abs(d) / anos) if d != 0 and anos > 0 else 0.0


def main():
    out = {"definicion_bh": "entra el 1er dia elegible, reparto a peso igual "
                            "ese dia, sin tocar hasta la siguiente entrada",
           "sellos": {}}
    for sello in SELLOS:
        datos = pr.cargar_congelados(pr.ACTIVOS, stamp=sello, verbose=False)
        closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
        R = closes.pct_change().values
        T, n = R.shape
        notna = (~np.isnan(R)).astype(np.int64)
        cum = np.cumsum(notna, axis=0)
        elig = cum >= (pr.LOOKBACK + 1)

        # --- (1) igual-ponderado con rebalanceo diario = EL DEL CODIGO
        ew = [1.0]
        for t in range(T):
            idx = np.where(elig[t])[0]
            r_b = float(np.nanmean(R[t][idx])) if len(idx) else 0.0
            if np.isnan(r_b):
                r_b = 0.0
            ew.append(ew[-1] * (1 + r_b))
        ew = ew[1:]

        # --- (2) B&H puro: reparto solo en los dias de ENTRADA
        valores = np.zeros(n)
        bh, entradas = [], []
        for t in range(T):
            r = np.nan_to_num(R[t], nan=0.0)
            valores = valores * (1 + r)
            idx = np.where(elig[t])[0]
            entra = bool(t == 0 or (elig[t] != elig[t - 1]).any())
            if entra and len(idx):
                total = valores.sum() if valores.sum() > 0 else 1.0
                nuevo = np.zeros(n)
                nuevo[idx] = total / len(idx)
                valores = nuevo
                entradas.append(str(closes.index[t].date()))
            bh.append(valores.sum() if valores.sum() > 0 else 1.0)
        bh = np.asarray(bh)
        bh = bh / bh[0] if bh[0] > 0 else bh

        # --- (3) variante B: universo fijo de los elegibles el primer dia
        idx0 = np.where(elig[0])[0]
        if len(idx0) == 0:
            # primer dia con algun elegible
            t0 = int(np.argmax(elig.any(axis=1)))
            idx0 = np.where(elig[t0])[0]
        else:
            t0 = 0
        val = np.zeros(n)
        val[idx0] = 1.0 / len(idx0)
        bhfix = []
        for t in range(T):
            if t >= t0:
                val = val * (1 + np.nan_to_num(R[t], nan=0.0))
            bhfix.append(val.sum())
        bhfix = np.asarray(bhfix)
        bhfix = bhfix / bhfix[t0] if bhfix[t0] > 0 else bhfix

        print(f"\n=== A-5 sello {sello}  ({T} dias, "
              f"{closes.index[0].date()} -> {closes.index[-1].date()}) ===")
        print(f"  dias de ENTRADA de algun activo: {len(entradas)}  -> {entradas}")
        filas = [("igual-ponderado diario (EL DEL CODIGO)", ew),
                 ("B&H puro (reparto solo al entrar)", bh),
                 ("B&H universo fijo del 1er dia elegible", bhfix)]
        print(f"  {'construccion':<42} {'retorno %':>14} {'Sharpe':>8}"
              f" {'maxDD %':>9} {'Calmar':>8}")
        res = {}
        for nom, c in filas:
            r = 100 * (c[-1] / c[0] - 1)
            print(f"  {nom:<42} {r:>14.2f} {sharpe(c):>8.4f}"
                  f" {100*mdd(c):>9.2f} {calmar(c):>8.3f}")
            res[nom] = {"retorno_pct": float(r), "sharpe": sharpe(c),
                        "max_dd_pct": float(100 * mdd(c)), "calmar": calmar(c),
                        "final": float(c[-1])}
        s_ew, s_bh = sharpe(ew), sharpe(bh)
        dif_rel = abs(s_bh - s_ew) / abs(s_ew) if s_ew else float("nan")
        print(f"  diferencia en Sharpe EW vs B&H puro : {s_bh - s_ew:+.4f}"
              f"  ({100*dif_rel:.2f} % relativo)")
        print(f"  -> {'MENOR del 5 %: se dice y se sigue' if dif_rel < 0.05 else 'MAYOR del 5 %: NO son la misma curva'}")
        print(f"  ratio de retorno final B&H/EW : {bh[-1]/ew[-1]:.4f}")
        out["sellos"][sello] = {
            "T": int(T), "dias_entrada": entradas,
            "curvas": res,
            "delta_sharpe_bh_menos_ew": s_bh - s_ew,
            "delta_sharpe_relativo": float(dif_rel),
            "menor_del_5pct": bool(dif_rel < 0.05),
            "ratio_final_bh_sobre_ew": float(bh[-1] / ew[-1]),
        }
        pd.DataFrame({"ew_diario": ew, "bh_puro": bh, "bh_fijo": bhfix},
                     index=closes.index).to_csv(
            f"fase0_n7/a5_curvas_{sello}.csv", index_label="date")
    json.dump(out, open("fase0_n7/a5_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/a5_salida.json y fase0_n7/a5_curvas_*.csv")


if __name__ == "__main__":
    main()
