"""B-c / B-b (N6, Fase 0) — Dos cosas que el brief no mira:

(1) La V del expediente se mide sobre 2024-10 -> 2026-10, que esta DENTRO de
    T3 (2023-01 -> fin). Medir Fase B en T3 reduce la heterogeneidad de
    ventana entre V y T, en vez de aumentarla. Es un argumento A FAVOR del
    holdout que el brief no hace, y cuenta para B-b.
(2) ¿Cuantas curvas de panel hay en el repo? B-c pregunta si existe familia
    de intentos sobre el objeto evaluado. N4 (B-07, hallazgo 10) dijo que no
    es N=1. Aqui se enumera lo enumerable.

Uso (desde fix-fase2/):
  STAMP_CONGELADO=20261009 python3 fase0_n6/b_ventana_homogenea.py
"""
import glob
import json
import math
import os
import statistics
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
PPY = 365
G = 0.5772156649
ND = statistics.NormalDist()
V12 = 0.0007021947704551833
V15 = 0.0015503661545655356


def psr(s, n, s0, sk, ku):
    return ND.cdf((s - s0) * math.sqrt(n - 1) /
                  math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2))


def sr0(n, v):
    if n <= 1:
        return 0.0
    return math.sqrt(v) * ((1 - G) * ND.inv_cdf(1 - 1 / n) +
                           G * ND.inv_cdf(1 - 1 / (n * math.e)))


def liston(n, v, te, sk, ku, conf=0.95):
    s0 = sr0(n, v)
    if psr(s0, te, s0, sk, ku) >= conf:
        return s0 * math.sqrt(PPY)
    lo, hi = s0, s0 + 2.0
    for _ in range(200):
        m = (lo + hi) / 2
        if psr(m, te, s0, sk, ku) >= conf:
            hi = m
        else:
            lo = m
    return hi * math.sqrt(PPY)


def ar1(r):
    r = np.asarray(r, dtype=float); r = r[~np.isnan(r)]
    rho = min(max(np.corrcoef(r[:-1], r[1:])[0, 1], -0.95), 0.95)
    return len(r) * (1 - rho) / (1 + rho)


def main():
    from portfolio_runner import load_or_download, simulate  # noqa
    eq = simulate(load_or_download())["equity"]
    rets = eq.pct_change()

    df = pd.read_csv("data/btc_usd_5y_1d.csv", index_col=0, parse_dates=True)
    oos = df.iloc[int(len(df) * 0.6):]
    v_ini, v_fin = oos.index[0], oos.index[-1]

    print("=== B-c.1 solape de ventana entre V y el objeto evaluado ===")
    print(f"  ventana de V (OOS Fase A) : {v_ini.date()} -> {v_fin.date()}  "
          f"({len(oos)} velas)")
    ventanas = {
        "muestra completa": (eq.index[0], eq.index[-1]),
        "T3 2023-fin": (pd.Timestamp("2023-01-01"), eq.index[-1]),
        "ventana de V exacta": (v_ini, v_fin),
    }
    for nombre, (a, b) in ventanas.items():
        m = (eq.index >= a) & (eq.index <= b)
        n = int(m.sum())
        sol = ((eq.index >= max(a, v_ini)) & (eq.index <= min(b, v_fin))).sum()
        print(f"  {nombre:<22} {a.date()} -> {b.date()}  T={n:>5}  "
              f"solape con V = {sol:>4} dias = {sol/n*100:>5.1f}%")
    print()
    print("  LECTURA: medir en T3 sube el solape del 16.6% al 53%. Esa parte")
    print("  de la heterogeneidad V/T que H10 senala MEJORA con el holdout.")
    print("  Es un argumento A FAVOR del holdout, y el brief no lo hace.")
    print()

    print("=== B-c.2 la construccion de ventana HOMOGENEA ===")
    print("  Si se exige que V y T describan la MISMA ventana, el objeto hay")
    print("  que medirlo solo en 2024-10 -> 2026-10:")
    print(f"  {'ventana':<24} {'T':>5} {'T_eff':>6} {'Sh_an':>8} {'t':>6} "
          f"{'lis_N12':>8} {'lis_N15':>8} {'lis_t3':>8}")
    filas = []
    for nombre, (a, b) in ventanas.items():
        per = rets[(eq.index >= a) & (eq.index <= b)].dropna().values
        te = int(ar1(per))
        sk = float(pd.Series(per).skew()); ku = float(pd.Series(per).kurt() + 3)
        s = per.mean() / per.std()
        obs = s * math.sqrt(PPY)
        l12 = liston(12, V12, te, sk, ku)
        l15 = liston(15, V15, te, sk, ku)
        lt = 3 / math.sqrt(te) * math.sqrt(PPY)
        filas.append({"ventana": nombre, "T": len(per), "T_eff": te,
                      "sharpe_anual": round(obs, 4),
                      "t": round(s * math.sqrt(te), 2),
                      "liston_n12": round(l12, 4), "liston_n15": round(l15, 4),
                      "liston_t3": round(lt, 4),
                      "pasa_n12": bool(obs >= l12), "pasa_n15": bool(obs >= l15),
                      "pasa_t3": bool(obs >= lt)})
        print(f"  {nombre:<24} {len(per):>5} {te:>6} {obs:>8.4f} "
              f"{s*math.sqrt(te):>6.2f} {l12:>8.4f} {l15:>8.4f} {lt:>8.4f}")
    print()
    print(f"  {'ventana':<24} {'pasa N=12':>10} {'pasa N=15':>10} {'pasa t>3':>9}")
    for f in filas:
        print(f"  {f['ventana']:<24} {str(f['pasa_n12']):>10} "
              f"{str(f['pasa_n15']):>10} {str(f['pasa_t3']):>9}")
    print()
    print("  LECTURA: en NINGUNA de las tres ventanas Fase B pasa el DSR. Pasa")
    print("  t>3 solo en la muestra completa. La ventana homogenea (la que")
    print("  H10 pediria por coherencia V/T) es la PEOR de las tres.")
    print()

    print("=== B-c.3 ¿cuantas curvas de panel hay? (familia del objeto) ===")
    for p in sorted(glob.glob("results/portfolio_*")):
        if p.endswith(".csv"):
            s = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0]
            print(f"  {os.path.basename(p):<34} {len(s)} dias "
                  f"{s.index[0].date()} -> {s.index[-1].date()}")
        else:
            print(f"  {os.path.basename(p):<34} (json)")
    sup = json.load(open("results/portfolio_supervivencia.json"))
    print()
    print(f"  portfolio_supervivencia.json: n_activos="
          f"{sup.get('n_activos')} sharpe={sup['metricas']['sharpe']} "
          f"dsr={sup['metricas']['dsr']}")
    print("  Hiperparametros del panel NO pre-registrados "
          "(portfolio_runner.py:32-37):")
    txt = open("src/portfolio_runner.py").read().splitlines()
    for i, l in enumerate(txt[:60], 1):
        if l.split("=")[0].strip() in ("LOOKBACK", "LAMBDA", "SIGMA_TARGET",
                                       "W_MAX", "GROSS_MAX", "VOL_TOPE_MULT"):
            print(f"    {i}: {l}")
    print()
    print("  Curvas de panel enumerables: 2 (10 activos y 15 activos).")
    print("  Luego la familia del objeto evaluado NO es N=1, pero tampoco es")
    print("  enumerable: 6 hiperparametros sin pre-registro y la eleccion del")
    print("  universo de 10 no dejan rastro de cuantas combinaciones se")
    print("  probaron. Con N=2 el liston es "
          f"{liston(2, V12, 4336, 1.036877, 31.998897):.4f} y Fase B pasa;")
    print("  con N=3, "
          f"{liston(3, V12, 4336, 1.036877, 31.998897):.4f} y no pasa.")
    print("  El veredicto cambia entre 2 y 3, y nadie puede decir cual es.")

    with open("fase0_n6/b_salida_ventanas.json", "w") as f:
        json.dump({"ventana_V": [str(v_ini.date()), str(v_fin.date())],
                   "filas": filas}, f, indent=2)
    print("\n-> fase0_n6/b_salida_ventanas.json")


if __name__ == "__main__":
    main()
