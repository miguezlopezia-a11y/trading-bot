"""A-9 (N6, Fase 0) — El "Balance honesto" de B-b sumado de verdad, y la V que
hace falta para el liston 0.823 de H10.

Corrige dos cosas que el segundo agente encontro:
  - hallazgo 6 (MEDIA): el "Balance honesto" de B-b daba +0.49 como el efecto
    de las DOS correcciones de la tarea. +0.49 es solo el recuento. El holdout
    aporta otros ~+0.39 de liston, que el registro mide en otra seccion y no
    suma aqui. La unica tabla cuya funcion era ser ecuanime infracontaba su
    propio lado fuerte.
  - hallazgo 12 (BAJA): B-e6 describe la construccion de H10 como "homogeneiza
    SUBIENDO V al universo del objeto", pero el liston crece con V y H10 lo
    BAJA de 1.312 a 0.823. Para eso V tiene que BAJAR. Se calcula cuanto.

Uso (desde fix-fase2/):
  STAMP_CONGELADO=20261009 python3 fase0_n6/a9_balance_y_etiquetas.py
  (o sin sello: usa la equity congelada 20261007; imprime las dos)
"""
import json
import math
import statistics
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
ND = statistics.NormalDist()
G = 0.5772156649
PPY = 365
V12 = 0.0007021947704551833


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
    for _ in range(300):
        m = (lo + hi) / 2
        if psr(m, te, s0, sk, ku) >= conf:
            hi = m
        else:
            lo = m
    return hi * math.sqrt(PPY)


def params(per):
    r = np.asarray(per, dtype=float)
    rho = min(max(np.corrcoef(r[:-1], r[1:])[0, 1], -0.95), 0.95)
    return (int(len(r) * (1 - rho) / (1 + rho)),
            float(pd.Series(per).skew()), float(pd.Series(per).kurt() + 3),
            per.mean() / per.std() * math.sqrt(PPY))


def main():
    V15 = json.load(open("fase0_n6/a5_salida.json"))["V15"]
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    ra = eq.pct_change()
    full = ra.dropna().values
    t3 = ra[eq.index >= "2023-01-01"].dropna().values

    print("=== A-9.1 las DOS correcciones de la tarea, sumadas de verdad ===")
    print("  (equity congelada, sello 20261007)")
    print(f"  {'construccion':<34} {'T_eff':>6} {'liston':>8} {'delta':>8} "
          f"{'Sharpe':>8} {'pasa':>6}")
    base = None
    filas = []
    for etq, per, N, V in (("base: N=12, muestra completa", full, 12, V12),
                           ("solo recuento: N=15, completa", full, 15, V15),
                           ("solo holdout: N=12 en T3", t3, 12, V12),
                           ("LAS DOS: N=15 en T3", t3, 15, V15)):
        te, sk, ku, obs = params(per)
        L = liston(N, V, te, sk, ku)
        if base is None:
            base = L
        filas.append({"construccion": etq, "N": N, "T_eff": te,
                      "liston_anual": round(L, 4), "delta": round(L - base, 4),
                      "sharpe_obs_anual": round(obs, 4), "pasa": bool(obs >= L)})
        print(f"  {etq:<34} {te:>6} {L:>8.4f} {L - base:>+8.4f} "
              f"{obs:>8.4f} {str(obs >= L):>6}")
    print()
    print("  CORRECCION (hallazgo 6, MEDIA): el 'Balance honesto' de la v1 daba")
    print("  +0.49 como el efecto de las dos correcciones. Es solo el recuento.")
    print(f"  Las dos juntas suman {filas[-1]['delta']:+.4f} de liston, y encima")
    print(f"  el Sharpe cae {filas[0]['sharpe_obs_anual'] - filas[-1]['sharpe_obs_anual']:.4f}.")
    print("  El lado contrario se daba a valor completo (-0.04 a -0.35). La")
    print("  unica tabla del registro cuya funcion era ser ecuanime")
    print("  infracontaba su propio lado fuerte en ~0.39.")
    print()

    print("=== A-9.2 que V hace falta para el liston 0.823 de H10 ===")
    te, sk, ku, obs = params(full)
    lo, hi = 1e-8, V12
    for _ in range(300):
        m = (lo + hi) / 2
        if liston(12, m, te, sk, ku) < 0.823:
            lo = m
        else:
            hi = m
    print(f"  liston con V(12)={V12:.6e} : {liston(12, V12, te, sk, ku):.4f}")
    print(f"  V que da liston 0.823      : {hi:.4e}  "
          f"(cociente V/V12 = {hi / V12:.3f})")
    print()
    print("  CORRECCION (hallazgo 12, BAJA): B-e6 describia la construccion de")
    print("  H10 como 'homogeneiza SUBIENDO V al universo del objeto'. El")
    print("  liston crece con V, y H10 lo BAJA de 1.312 a 0.823, luego V tiene")
    print(f"  que BAJAR a {hi / V12:.3f}x la actual. 'Subiendo V al universo' se")
    print("  lee como 'aumentando V', que es el signo contrario — en la unica")
    print("  seccion del registro cuyo objeto es que las etiquetas invitan a")
    print("  equivocarse de signo. Redaccion correcta: 'V remedida sobre el")
    print("  panel, que la BAJA a ~0.18x porque el vol-targeting comprime la")
    print("  dispersion entre reglas' (N1, 3.0c: sd de 0.506 a 0.212).")

    with open("fase0_n6/a9_salida.json", "w") as f:
        json.dump({"filas": filas, "V_para_liston_0823": hi,
                   "cociente_V": hi / V12}, f, indent=2)
    print("\n-> fase0_n6/a9_salida.json")


if __name__ == "__main__":
    main()
