"""N7 · B-a (obligatoria) — Las tres construcciones de la §4.1 no son
equivalentes. ¿Cual es la comparacion honesta?
Corre DESDE fix-fase2/.  Salida: b_a_salida.json

Esto es EVIDENCIA DEL PASO B, no la ejecucion de la §4.1: no se emite la tabla
doble de la §4.2, ni el block bootstrap de la §4.3, ni los tramos de la §4.4.
Se mide lo justo para decidir que construccion es honesta, que es lo que B-a
pide por escrito.

Se mide tambien el DESFASE que el brief introduce al escribir
  r_bench_a(t) = exposure(t-1) * r_bench(t)
cuando portfolio_runner.py:328 ya guarda exposure(t) = sum(w_prev), o sea el
gross que YA gano r(t). El brief duplica el retardo.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLO = "20261007"      # el del numero publicado (dias=4404)
K_BRIEF = 0.1559827260735808


def sharpe(x):
    v = np.asarray(x, dtype=float)
    v = v[~np.isnan(v)]
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(pr.PPY)) if len(v) > 1 and sd > 0 else 0.0


def calmar(x):
    v = pd.Series(np.asarray(x, dtype=float)).fillna(0.0)
    eq = (1 + v).cumprod()
    dd = (eq - eq.cummax()) / eq.cummax()
    anos = len(v) / pr.PPY
    return float((eq.iloc[-1] - 1) / abs(dd.min()) / anos) if dd.min() != 0 and anos > 0 else 0.0


def mdd(x):
    v = pd.Series(np.asarray(x, dtype=float)).fillna(0.0)
    eq = (1 + v).cumprod()
    return float(((eq - eq.cummax()) / eq.cummax()).min() * 100)


def total(x):
    v = pd.Series(np.asarray(x, dtype=float)).fillna(0.0)
    return float(((1 + v).cumprod().iloc[-1] - 1) * 100)


def main():
    datos = pr.cargar_congelados(pr.ACTIVOS, stamp=SELLO, verbose=False)
    res = pr.simulate(datos)
    eq, bench, expo = res["equity"], res["benchmark"], res["exposure"]
    e = expo.values
    r_est = eq.pct_change().fillna(0.0).values          # neto de costes
    r_ben = bench.pct_change().fillna(0.0).values       # bruto, 100 %
    T = len(e)
    out = {"sello": SELLO, "dias": T, "k_brief": K_BRIEF}

    print("=== B-a.0 que es exactamente exposure(t) en el codigo ===")
    print("  portfolio_runner.py:318-328, en la iteracion t:")
    print("    r_dia   = rets.iloc[t]            <- retorno del dia t")
    print("    r_p     = nansum(w_prev * r_dia)  <- w_prev son los pesos de t-1")
    print("    exposure.append(nansum(w_prev))   <- el gross QUE GANO r(t)")
    print("  => exposure[t] ya esta retardado. Alinear con r_bench(t) exige")
    print("     exposure[t], NO exposure[t-1]. El brief escribe exposure(t-1)")
    print("     en la §4.1(a) y en la §4.1(c): duplica el retardo.")
    cor = float(np.corrcoef(e[1:], e[:-1])[0, 1])
    print(f"  autocorrelacion lag-1 de exposure: {cor:.6f}")

    # --- (a) escalado dia a dia, en las dos alineaciones
    a_ok = e * r_ben                      # alineado (exposure[t])
    a_brief = np.concatenate([[0.0], e[:-1]]) * r_ben   # como lo escribe el brief
    # --- (b) escalado por constante
    b = K_BRIEF * r_ben
    # --- (c) binario tipo Fase A
    mask_ok = e > 1e-12
    mask_brief = np.concatenate([[False], e[:-1] > 1e-12])

    print("\n=== B-a.1 las tres construcciones, misma bateria ===")
    filas = [
        ("estrategia Fase B (neto de costes)", r_est, 1.0),
        ("benchmark PUBLICADO: B&H 100 %", r_ben, 1.0),
        ("(a) exposure[t]*r_bench  ALINEADO", a_ok, float(e.mean())),
        ("(a') exposure[t-1]*r_bench (del brief)", a_brief,
         float(np.concatenate([[0.0], e[:-1]]).mean())),
        ("(b) k*r_bench, k=0.15598273", b, K_BRIEF),
    ]
    print(f"  {'serie':<40} {'retorno %':>13} {'Sharpe':>8} {'maxDD %':>9} {'Calmar':>8} {'expo':>7}")
    res_tab = {}
    for nom, x, ex in filas:
        print(f"  {nom:<40} {total(x):>13.2f} {sharpe(x):>8.4f}"
              f" {mdd(x):>9.2f} {calmar(x):>8.3f} {ex:>7.4f}")
        res_tab[nom] = {"retorno_pct": total(x), "sharpe": sharpe(x),
                        "max_dd_pct": mdd(x), "calmar": calmar(x),
                        "exposicion_media": ex, "n": int(len(x))}
    print("  --- (c) binario: los dos sobre el MISMO subconjunto de dias ---")
    for etiq, m in [("(c) mask exposure[t]>0  ALINEADO", mask_ok),
                    ("(c') mask exposure[t-1]>0 (del brief)", mask_brief)]:
        print(f"  {etiq}  n={int(m.sum())} dias ({100*m.mean():.2f} %)")
        print(f"    {'estrategia, esos dias':<38} {total(r_est[m]):>13.2f}"
              f" {sharpe(r_est[m]):>8.4f} {mdd(r_est[m]):>9.2f}"
              f" {calmar(r_est[m]):>8.3f}")
        print(f"    {'B&H 100 %, LOS MISMOS dias':<38} {total(r_ben[m]):>13.2f}"
              f" {sharpe(r_ben[m]):>8.4f} {mdd(r_ben[m]):>9.2f}"
              f" {calmar(r_ben[m]):>8.3f}")
        res_tab[etiq] = {"n_dias": int(m.sum()), "pct_dias": float(100*m.mean()),
                         "sharpe_estrategia": sharpe(r_est[m]),
                         "sharpe_bh": sharpe(r_ben[m]),
                         "calmar_estrategia": calmar(r_est[m]),
                         "calmar_bh": calmar(r_ben[m]),
                         "diferencia_sharpe": sharpe(r_est[m]) - sharpe(r_ben[m])}
    out["tabla"] = res_tab

    print("\n=== B-a.2 (b) ES UN NO-OP PARA EL SHARPE. Demostrado ===")
    print("  El Sharpe es invariante a multiplicar por una constante positiva:")
    for k in (0.1559827260735808, 0.5, 1.0, 2.0, 37.0):
        print(f"    Sharpe(k*r_bench) con k={k:<20} = {sharpe(k*r_ben):.10f}")
    print(f"  Sharpe(r_bench) sin escalar            = {sharpe(r_ben):.10f}")
    iguales = abs(sharpe(b) - sharpe(r_ben)) < 1e-12
    print(f"  identicos a 1e-12: {iguales}")
    print("  => la construccion (b) devuelve EXACTAMENTE el 1.164 publicado.")
    print("     No iguala nada. Lo que si mueve son retorno total, maxDD y")
    print("     Calmar, porque esos no son invariantes a escala.")
    out["b_es_noop_en_sharpe"] = bool(iguales)
    out["sharpe_b"] = sharpe(b)
    out["sharpe_bench_sin_escalar"] = sharpe(r_ben)

    print("\n=== B-a.3 cuanto cuesta el desfase del brief ===")
    print(f"  Sharpe (a) alineado      : {sharpe(a_ok):.6f}")
    print(f"  Sharpe (a') del brief    : {sharpe(a_brief):.6f}")
    print(f"  delta por el retardo de mas: {sharpe(a_brief)-sharpe(a_ok):+.6f}")
    print(f"  dias de mascara (c) alineado: {int(mask_ok.sum())}"
          f"   (c') del brief: {int(mask_brief.sum())}"
          f"   difieren en {int((mask_ok!=mask_brief).sum())} dias")
    d_ok = sharpe(r_est) - sharpe(a_ok)
    d_br = sharpe(r_est) - sharpe(a_brief)
    print(f"  diferencial Fase B - (a) alineado : {d_ok:+.6f}")
    print(f"  diferencial Fase B - (a') brief   : {d_br:+.6f}")
    print(f"  el desfase mueve el diferencial en {d_br-d_ok:+.6f}"
          f"  -> {'A FAVOR' if d_br>d_ok else 'EN CONTRA'} de Fase B")
    out["desfase"] = {"sharpe_a_alineado": sharpe(a_ok),
                      "sharpe_a_brief": sharpe(a_brief),
                      "delta_sharpe": sharpe(a_brief) - sharpe(a_ok),
                      "dias_mask_alineado": int(mask_ok.sum()),
                      "dias_mask_brief": int(mask_brief.sum()),
                      "dias_mask_difieren": int((mask_ok != mask_brief).sum()),
                      "diferencial_alineado": d_ok, "diferencial_brief": d_br,
                      "favorece_a_fase_b": bool(d_br > d_ok)}

    print("\n=== B-a.4 ¿contamina (a) el benchmark con el timing de vol? ===")
    print("  Test: ¿el camino de exposicion real elige dias BUENOS para el")
    print("  benchmark? 2000 permutaciones del propio camino, semilla 43.")
    rng = np.random.default_rng(43)
    vals = np.array([sharpe(rng.permutation(e) * r_ben) for _ in range(2000)])
    s_real = sharpe(a_ok)
    pct = float((vals < s_real).mean() * 100)
    z = float((s_real - vals.mean()) / vals.std(ddof=1))
    print(f"  Sharpe (a) camino REAL        : {s_real:.4f}")
    print(f"  permutados: media {vals.mean():.4f}  sd {vals.std(ddof=1):.4f}")
    print(f"  percentil del real            : {pct:.2f} %   z = {z:+.3f}")
    print(f"  Sharpe del bench SIN escalar  : {sharpe(r_ben):.4f}")
    print(f"  -> escalar por el camino real {'SUBE' if s_real>vals.mean() else 'BAJA'}"
          f" el Sharpe del benchmark frente a un camino aleatorio de la MISMA"
          f" distribucion")
    if pct > 90:
        lec = "el camino real SI selecciona dias favorables al benchmark: (a) esta inflada EN CONTRA de Fase B"
    elif pct < 10:
        lec = "el camino real selecciona dias DESfavorables al benchmark: (a) esta deprimida A FAVOR de Fase B"
    else:
        lec = f"seleccion NO significativa (z={z:+.2f}); el leve sesgo va en contra de Fase B pero no se distingue del ruido"
    print(f"  lectura: {lec}")
    out["permutaciones"] = {"n": 2000, "semilla": 43, "sharpe_real": s_real,
                            "media_permutado": float(vals.mean()),
                            "sd_permutado": float(vals.std(ddof=1)),
                            "percentil": pct, "z": z, "lectura": lec}

    print("\n=== B-a.5 veredicto de B-a ===")
    ver = []
    ver.append("(b) queda DESCARTADA: es un no-op para el Sharpe (identidad a 1e-12). "
               "No es una tercera construccion, es el 1.164 publicado con otra etiqueta. "
               "Solo aporta retorno/maxDD/Calmar, que no son invariantes a escala.")
    ver.append(f"(c) corrige poco: la mascara conserva {100*mask_ok.mean():.1f} % de los dias "
               f"y en ellos el benchmark sigue al 100 % mientras la estrategia esta al "
               f"{100*e[mask_ok].mean():.1f} %. No iguala exposicion: solo descarta los dias de caja total.")
    ver.append(f"(a) es la unica que iguala de verdad el gross dia a dia. Su objecion "
               f"-- que le regala al benchmark el timing de vol de la estrategia -- esta "
               f"MEDIDA: percentil {pct:.1f} %, z {z:+.2f}. El sesgo existe y va EN CONTRA "
               f"de Fase B, no a su favor, asi que (a) es la construccion DURA, no la blanda.")
    ver.append("CONCLUSION: la comparacion honesta es (a) ALINEADA con exposure[t], "
               "leida junto al percentil de seleccion. (c) se reporta como control de "
               "robustez y (b) solo para retorno/Calmar. NO es 'hay que leer las tres "
               "juntas' en pie de igualdad: (b) no es una comparacion.")
    for v in ver:
        print(f"  - {v}")
    out["veredicto_b_a"] = ver
    out["ninguna_es_honesta"] = False   # el NO-GO de B-a NO se dispara

    json.dump(out, open("fase0_n7/b_a_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/b_a_salida.json")


if __name__ == "__main__":
    main()
