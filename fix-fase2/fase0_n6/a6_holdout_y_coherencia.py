"""§2.3 + §2.6 (N6, Fase 0) — Que el Sharpe de Fase B no tiene holdout, y si la
comparacion que el paso 4.2 propone es siquiera coherente.

§2.3 del brief: portfolio_runner.py no tiene split; la equity va de 2014-09-17
a 2026-10-07; los once Sharpes de V cubren 730 dias.

Lo segundo NO es ejecutar el paso 4.2. El paso 4.2 pide medir el Sharpe de
Fase B en T3 y compararlo "contra el liston de 6.3 y contra t>3", y entregar
salida_6_4_holdout.json. Aqui no se entrega nada de eso: se comprueba si la
comparacion esta bien definida, que es trabajo de Fase 0 (Paso B) y es lo que
decide si 4.2 sobra. Ningun JSON de Alcance se escribe.

Uso (desde fix-fase2/):
  STAMP_CONGELADO=20261009 python3 fase0_n6/a6_holdout_y_coherencia.py
"""
import json
import math
import os
import statistics
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
PPY = 365
GAMMA_E = 0.5772156649
ND = statistics.NormalDist()
V12 = 0.0007021947704551833
V15 = 0.0015503661545655356   # medida en A-5


def psr_m(s, n, s0, sk, ku):
    num = (s - s0) * math.sqrt(n - 1)
    den = math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2)
    return ND.cdf(num / den)


def sr0_m(n, v):
    if n <= 1:
        return 0.0
    z1, z2 = ND.inv_cdf(1 - 1.0 / n), ND.inv_cdf(1 - 1.0 / (n * math.e))
    return math.sqrt(v) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def liston_m(n, v, n_eff, sk, ku, conf=0.95):
    s0 = sr0_m(n, v)
    if psr_m(s0, n_eff, s0, sk, ku) >= conf:
        return s0, s0
    lo, hi = s0, s0 + 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if psr_m(mid, n_eff, s0, sk, ku) >= conf:
            hi = mid
        else:
            lo = mid
    return hi, s0


def ar1_eff_m(r):
    r = np.asarray(r, dtype=float); r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0:
        return float(len(r))
    rho = min(max(np.corrcoef(r[:-1], r[1:])[0, 1], -0.95), 0.95)
    return len(r) * (1 - rho) / (1 + rho)


def main():
    print("=== §2.3a el codigo no tiene split ===")
    for pat in ("TRAIN_FRAC", "train_test", "holdout", "split"):
        r = subprocess.run(["grep", "-n", pat, "src/portfolio_runner.py"],
                           capture_output=True, text=True)
        salida = r.stdout.strip() or "(0 coincidencias)"
        print(f"  grep '{pat}' src/portfolio_runner.py -> {salida}")
    print()
    print("  Comparar con el pipeline de Fase A, que SI tiene split:")
    r = subprocess.run(["grep", "-n", "TRAIN_FRAC", "src/rigor_estadistico.py"],
                       capture_output=True, text=True)
    print("  " + r.stdout.strip().replace("\n", "\n  "))
    print()
    print("  ¿Existe src/portfolio_runner.py en la RAIZ del repo?")
    print(f"    {'SI' if os.path.exists('../src/portfolio_runner.py') else 'NO'}"
          f"   (solo esta en fix-fase2/src/)")
    print()

    print("=== §2.3b las dos ventanas ===")
    eq07 = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                       parse_dates=True).iloc[:, 0]
    print(f"  objeto evaluado (equity congelada): {len(eq07)} dias, "
          f"{eq07.index[0].date()} -> {eq07.index[-1].date()}")
    df = pd.read_csv("data/btc_usd_5y_1d.csv", index_col=0, parse_dates=True)
    split = int(len(df) * 0.6)
    oos = df.iloc[split:]
    print(f"  las 11 series de V (OOS de Fase A) : {len(oos)} velas, "
          f"{oos.index[0].date()} -> {oos.index[-1].date()}")
    print(f"  solape temporal: la V cubre "
          f"{len(oos)/len(eq07)*100:.1f}% de la ventana del objeto evaluado")
    print()

    print("=== §2.6 ¿esta bien definida la comparacion del paso 4.2? ===")
    from portfolio_runner import load_or_download, simulate  # noqa: E402
    eq = simulate(load_or_download())["equity"]
    rets_all = eq.pct_change()

    def params(per):
        return (int(ar1_eff_m(per)), per.mean() / per.std(),
                float(pd.Series(per).skew()), float(pd.Series(per).kurt() + 3))

    escenarios = []
    # muestra completa
    per = rets_all.dropna().values
    escenarios.append(("muestra completa 2014-2026", per))
    # T3
    m3 = (eq.index >= "2023-01-01")
    escenarios.append(("T3 holdout 2023-fin", rets_all[m3].dropna().values))
    # T1+T2 (el "train" implicito)
    m12 = (eq.index >= "2015-09-01") & (eq.index <= "2022-12-31")
    escenarios.append(("T1+T2 2015-09-2022", rets_all[m12].dropna().values))

    print(f"  {'ventana':<28} {'T':>6} {'T_eff':>6} {'Sharpe_an':>10} "
          f"{'t':>6} {'skew':>7} {'kurt':>8}")
    datos = {}
    for nombre, per in escenarios:
        t_eff, s_per, sk, ku = params(per)
        datos[nombre] = (len(per), t_eff, s_per, sk, ku)
        print(f"  {nombre:<28} {len(per):>6} {t_eff:>6} "
              f"{s_per*math.sqrt(PPY):>10.4f} {s_per*math.sqrt(t_eff):>6.2f} "
              f"{sk:>7.3f} {ku:>8.3f}")
    print()
    print("  El liston NO es una constante: depende de T_eff, skew y kurt de")
    print("  la ventana que se evalua. Si se mide Fase B en T3, el liston que")
    print("  le corresponde es el de T3, no el 1.3118 de la muestra completa:")
    print()
    print(f"  {'ventana':<28} {'N':>3} {'V':>12} {'liston_DSR':>11} "
          f"{'liston_t3':>10} {'Sharpe_obs':>11} {'¿pasa DSR?':>11} {'¿pasa t?':>9}")
    filas = []
    for nombre, (T, t_eff, s_per, sk, ku) in datos.items():
        for N, V, etq in ((12, V12, "V(12)"), (15, V15, "V(15)")):
            lper, s0 = liston_m(N, V, t_eff, sk, ku)
            lan = lper * math.sqrt(PPY)
            lt = 3.0 / math.sqrt(t_eff) * math.sqrt(PPY)
            obs = s_per * math.sqrt(PPY)
            filas.append({"ventana": nombre, "N": N, "V": V, "T_eff": t_eff,
                          "liston_dsr_anual": round(lan, 4),
                          "liston_t3_anual": round(lt, 4),
                          "sharpe_obs_anual": round(obs, 4),
                          "pasa_dsr": bool(obs >= lan), "pasa_t": bool(obs >= lt)})
            print(f"  {nombre:<28} {N:>3} {V:>12.8f} {lan:>11.4f} "
                  f"{lt:>10.4f} {obs:>11.4f} {str(obs>=lan):>11} {str(obs>=lt):>9}")
    print()
    print("  LECTURA (diagnostico de Fase 0, NO el paso 4.2):")
    print("   CORRECCION: una version previa de este script imprimia aqui que")
    print("   'el liston DSR BAJA al acortar la ventana'. Es FALSO y lo")
    print("   contradice su propia tabla. En la PSR el numerador va con")
    print("   sqrt(T-1): para la misma confianza, MENOS T exige MAS Sharpe.")
    print("   - El liston DSR SUBE al acortar la ventana: 1.3117 (T_eff 4338)")
    print("     -> 1.7007 (T_eff 1356). Con V(15): 1.8022 -> 2.1944.")
    print("   - El liston t>3 SUBE tambien, y mas: 0.8702 -> 1.5565.")
    print("   - Y el Sharpe observado BAJA: 1.0082 -> 0.5721; el t, 3.48 -> 1.10.")
    print("   => Medir en el holdout mueve numerador y liston EN CONTRA de")
    print("      Fase B a la vez, por los dos tests. No hay compensacion.")
    print("      Fase B pasa t>3 en la muestra completa y NO lo pasa en T3.")
    print("      Eso agrava el problema de B-b: las correcciones de esta tarea")
    print("      van todas en el mismo sentido y hay que buscar la contraria")
    print("      en otro sitio (ver B-b).")

    with open("fase0_n6/a6_salida.json", "w") as f:
        json.dump({"ventanas": {k: {"T": v[0], "T_eff": v[1],
                                    "sharpe_diario": v[2], "skew": v[3],
                                    "kurt_raw": v[4]} for k, v in datos.items()},
                   "comparaciones": filas}, f, indent=2)
    print("\n-> fase0_n6/a6_salida.json")


if __name__ == "__main__":
    main()
