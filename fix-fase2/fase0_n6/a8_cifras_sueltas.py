"""A-8 (N6, Fase 0) — Las cifras que la v1 del registro pegó dentro de cercas de
código SIN script detrás.

El hallazgo 5 del segundo agente las identificó una a una: las dos z contra
bases alternativas (§2.2), los T mínimos (§2.5), las glosas de directorios de
A-2, y el "208.7 años" (§2.5). En un registro cuyo reproche de apertura es que
un documento que reprocha a otro no citar su fuente no puede llegar sin
scripts detrás, pegar prosa dentro de una cerca de código es la misma falta.

Este script las calcula todas. Dos de ellas salían mal y la corrección va
marcada.

Uso (desde fix-fase2/):  python3 -I fase0_n6/a8_cifras_sueltas.py
"""
import json
import math
import os
import statistics

import numpy as np

ND = statistics.NormalDist()
G = 0.5772156649
PPY = 365
V12 = 0.0007021947704551833
SK, KU, TE = 1.036877, 31.998897, 4336
OBS = 1.008383
SHARPE_DIARIO_PORT = 0.05278115954782411

V11N = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
        "sma_timing_50", "sma_timing_100", "sma_timing_304",
        "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]


def psr(s, n, s0, sk, ku):
    return ND.cdf((s - s0) * math.sqrt(n - 1) /
                  math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2))


def sr0(n, v):
    if n <= 1:
        return 0.0
    return math.sqrt(v) * ((1 - G) * ND.inv_cdf(1 - 1 / n) +
                           G * ND.inv_cdf(1 - 1 / (n * math.e)))


def liston(n, v, te, sk=SK, ku=KU, conf=0.95):
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


def t_min_dsr(N, V):
    """T_eff minimo para que el liston baje del Sharpe observado. Biseccion,
    no rejilla de 10 como hacia la v1."""
    if sr0(N, V) * math.sqrt(PPY) >= OBS:
        return None            # ningun T basta: SR0 ya supera al observado
    lo, hi = 10.0, 5_000_000.0
    for _ in range(300):
        m = (lo + hi) / 2
        if liston(N, V, m) > OBS:
            lo = m
        else:
            hi = m
    return hi


def main():
    d = json.load(open("fase0_n6/a5_salida.json"))
    sh, sp = d["sharpes_diarios"], d["sharpe_portfolio"]
    V15 = d["V15"]

    print("=== A-8.1 §2.2: la z de mean_reversion contra las tres bases ===")
    mr = sh["mean_reversion"]
    bases = [
        ("contra las 11 de V(11)", [sh[k] for k in V11N]),
        ("contra las 11 + portfolio (V12)", [sh[k] for k in V11N] + [sp]),
        ("contra 11+portfolio+breakout+trend",
         [sh[k] for k in V11N] + [sp, sh["breakout"], sh["trend_following"]]),
    ]
    zs = {}
    for etq, base in bases:
        m, s = float(np.mean(base)), float(np.std(base, ddof=1))
        zs[etq] = (mr - m) / s
        print(f"  {etq:<40} media={m:+.6f} sd={s:.6f} "
              f"z={(mr - m) / s:+.3f}")
    print("  Ninguna da ~3.5. El brief subestima la cifra.")
    print()

    print("=== A-8.2 §2.5: los T minimos, por biseccion (no por rejilla) ===")
    t3_exacto = (3.0 / SHARPE_DIARIO_PORT) ** 2
    print(f"  t>3 : T_eff = (3/{SHARPE_DIARIO_PORT:.11f})^2 = "
          f"{t3_exacto:.1f} dias = {t3_exacto / PPY:.2f} anos")
    print(f"        CORRECCION: la v1 pego 3240 dias / 8.88 anos. Era un")
    print(f"        artefacto de recorrer T de 10 en 10. El exacto es "
          f"{t3_exacto:.1f} / {t3_exacto / PPY:.2f}. (N5 decia 9.0)")
    for N, V, etq in ((1, V12, "N=1  con V(12)"),
                      (12, V12, "N=12 con V(12)"),
                      (15, V12, "N=15 con V(12)"),
                      (15, V15, "N=15 con V(15)  <-- la DEL RECUENTO")):
        t = t_min_dsr(N, V)
        s0a = sr0(N, V) * math.sqrt(PPY)
        if t is None:
            print(f"  {etq:<32} SR0_anual={s0a:.4f} > Sharpe obs {OBS:.4f}")
            print(f"  {'':<32} -> NINGUN T BASTA. El numerador de la PSR es")
            print(f"  {'':<32}    negativo: mas datos ALEJAN el DSR de 0.95.")
        else:
            print(f"  {etq:<32} SR0_anual={s0a:.4f}  T_eff={t:.1f} dias "
                  f"= {t / PPY:.2f} anos")
    print()
    print("  CORRECCION (hallazgo 2 del segundo agente, ALTA): la v1 pego")
    print("  '208.7 anos' como el T que el DSR exigiria con N=15. Esa cifra")
    print("  empareja N=15 con V(12), o sea con la V ANTERIOR al recuento que")
    print("  es el eje de la tarea. Con la pareja coherente (N=15, V(15)) la")
    print("  respuesta no es 208.7 anos: es que NO EXISTE T. Y es justo el")
    print("  emparejamiento (N,V) descolocado que el registro se felicitaba")
    print("  por no haber encontrado en el expediente.")
    print()

    print("=== A-8.3 A-2: las glosas de directorio, calculadas ===")
    for a, b in (("src", "fix-fase2/src"), ("data", "fix-fase2/data")):
        pa = os.path.join("..", a)
        comunes = sorted(set(os.listdir(pa)) & set(os.listdir(f"../{b}")))
        dirs = [c for c in comunes if os.path.isdir(os.path.join(pa, c))]
        print(f"  {a} / {b}: {len(comunes)} entradas comunes, de ellas "
              f"{len(dirs)} directorio(s): {dirs}")
    print(f"  contenido de ../data: "
          f"{[os.path.join(dp, f).replace('../', '') for dp, _, fs in os.walk('../data') for f in fs]}")
    print()

    print("=== A-8.4 §2.5 y B-c: la FRONTERA del veredicto, no la del test ===")
    lt = 3.0 / math.sqrt(TE) * math.sqrt(PPY)
    print(f"  liston t>3 = {lt:.4f}   Sharpe observado = {OBS:.6f}")
    print(f"  {'N':>6} {'liston_DSR':>11} {'manda':>6} {'Fase B pasa?':>13}")
    for N in (1, 2, 3, 4, 5, 12, 15):
        L = liston(N, V12, TE)
        print(f"  {N:>6} {L:>11.4f} {('t>3' if lt > L else 'DSR'):>6} "
              f"{str(OBS >= L):>13}")
    lo, hi = 1.0, 15.0
    for _ in range(100):
        m = (lo + hi) / 2
        if liston(m, V12, TE) < OBS:
            lo = m
        else:
            hi = m
    print(f"  frontera del VEREDICTO : N* = {lo:.4f}")
    print(f"  frontera de QUE TEST MANDA : entre N=2 y N=3")
    print("  Son dos fronteras distintas y la v1 del registro las confundio.")

    with open("fase0_n6/a8_salida.json", "w") as f:
        json.dump({"z_por_base": zs,
                   "t_min_t3_dias": t3_exacto,
                   "t_min_dsr": {f"N{N}_V{tag}": t_min_dsr(N, V)
                                 for N, V, tag in ((1, V12, "12"),
                                                   (12, V12, "12"),
                                                   (15, V12, "12"),
                                                   (15, V15, "15"))},
                   "frontera_veredicto_N": lo,
                   "sr0_anual_n15_v15": sr0(15, V15) * math.sqrt(PPY)},
                  f, indent=2)
    print("\n-> fase0_n6/a8_salida.json")


if __name__ == "__main__":
    main()
