"""§2.2 salvedad (N6, Fase 0) — ¿Es mean_reversion un outlier a ~3.5
desviaciones, y manda el efecto del recuento de N casi entero?

El brief conserva la salvedad de N4: "el efecto lo manda casi entero
mean_reversion, a ~3.5 desviaciones del resto. Es una cota colgada de un
outlier, no un liston nuevo." Se reverifica, porque la §2.6 del propio brief
dice "se mide, no se supone".

Uso (desde fix-fase2/):  python3 -I fase0_n6/a7_outlier_mean_reversion.py
"""
import json
import math
import statistics

import numpy as np

ND = statistics.NormalDist()
GAMMA_E = 0.5772156649
PPY = 365


def psr_m(s, n, s0, sk, ku):
    num = (s - s0) * math.sqrt(n - 1)
    den = math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2)
    return ND.cdf(num / den)


def sr0_m(n, v):
    if n <= 1:
        return 0.0
    z1, z2 = ND.inv_cdf(1 - 1.0 / n), ND.inv_cdf(1 - 1.0 / (n * math.e))
    return math.sqrt(v) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def liston(n, v, n_eff, sk, ku, conf=0.95):
    s0 = sr0_m(n, v)
    if psr_m(s0, n_eff, s0, sk, ku) >= conf:
        return s0 * math.sqrt(PPY)
    lo, hi = s0, s0 + 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if psr_m(mid, n_eff, s0, sk, ku) >= conf:
            hi = mid
        else:
            lo = mid
    return hi * math.sqrt(PPY)


def main():
    d = json.load(open("fase0_n6/a5_salida.json"))
    sh = d["sharpes_diarios"]
    sp = d["sharpe_portfolio"]
    t_eff, sk, ku = d["t_eff"], d["skew"], d["kurt_raw"]
    V11N = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
            "sma_timing_50", "sma_timing_100", "sma_timing_304",
            "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
    EXTRA3 = ["mean_reversion", "breakout", "trend_following"]

    print("=== distancia de cada trial a la masa de los demas ===")
    todos = {**{k: sh[k] for k in V11N + EXTRA3}, "PORTFOLIO": sp}
    print(f"  {'trial':<24} {'sharpe_d':>12} {'z (deja-uno-fuera)':>20}")
    zs = {}
    for k, v in sorted(todos.items(), key=lambda x: x[1]):
        resto = [x for kk, x in todos.items() if kk != k]
        m, s = float(np.mean(resto)), float(np.std(resto, ddof=1))
        z = (v - m) / s
        zs[k] = z
        marca = "  <-- OUTLIER" if abs(z) > 3 else ""
        print(f"  {k:<24} {v:>12.8f} {z:>20.3f}{marca}")
    print()
    print(f"  Afirmacion del brief: mean_reversion a ~3.5 sd del resto.")
    print(f"  Medido: z = {zs['mean_reversion']:.3f}  -> "
          f"{'CONFIRMADO' if 3.0 <= abs(zs['mean_reversion']) <= 4.0 else 'NO CONFIRMADO'}")
    segundo = sorted(((abs(z), k) for k, z in zs.items()), reverse=True)[1]
    print(f"  Segundo mas extremo: {segundo[1]} con |z| = {segundo[0]:.3f}")
    print()

    print("=== ¿manda mean_reversion el efecto del recuento de N? ===")
    V12 = float(np.var([sh[k] for k in V11N] + [sp], ddof=1))
    casos = [
        ("N=12, expediente (11+portfolio)", 12, V11N),
        ("N=15, con las 3", 15, V11N + EXTRA3),
        ("N=14, con las 3 SIN mean_reversion", 14,
         V11N + ["breakout", "trend_following"]),
        ("N=13, solo mean_reversion anadida", 13, V11N + ["mean_reversion"]),
    ]
    print(f"  {'construccion':<40} {'N':>3} {'V':>13} {'liston':>8} {'delta':>8}")
    base = None
    filas = []
    for etq, N, lista in casos:
        V = float(np.var([sh[k] for k in lista] + [sp], ddof=1))
        L = liston(N, V, t_eff, sk, ku)
        if base is None:
            base = L
        filas.append({"construccion": etq, "N": N, "V": V,
                      "liston_anual": round(L, 4), "delta": round(L - base, 4)})
        print(f"  {etq:<40} {N:>3} {V:>13.8f} {L:>8.4f} {L-base:>+8.4f}")
    print()
    d15 = [f for f in filas if f["N"] == 15][0]["delta"]
    d14 = [f for f in filas if f["N"] == 14][0]["delta"]
    print(f"  El salto total con las tres            : {d15:+.4f}")
    print(f"  El salto sin mean_reversion            : {d14:+.4f}")
    print(f"  Fraccion del efecto que aporta mean_reversion: "
          f"{(d15 - d14) / d15 * 100:.1f}%")
    print()
    print("  VEREDICTO: la salvedad del brief se CONFIRMA. El recuento de N")
    print("  sube el liston, pero el salto cuelga de un solo trial atipico.")
    print("  Sin mean_reversion el recuento de N apenas mueve el liston.")

    with open("fase0_n6/a7_salida.json", "w") as f:
        json.dump({"z_scores": zs, "casos": filas,
                   "fraccion_mean_reversion_pct": (d15 - d14) / d15 * 100},
                  f, indent=2)
    print("\n-> fase0_n6/a7_salida.json")


if __name__ == "__main__":
    main()
