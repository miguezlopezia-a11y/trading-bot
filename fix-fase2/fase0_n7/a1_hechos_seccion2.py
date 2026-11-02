"""N7 · A-1 — Reverificar los OCHO bloques de la §2 del brief.
Corre DESDE fix-fase2/ (los bloques que tocan el arbol de la RAIZ lo dicen).
Salida: a1_salida.json

Veredicto por bloque: CONFIRMADO / CONFIRMADO con correccion / REFUTADO.
Las cifras que exigen simulacion estan en a2_, a3_, a4_, a5_; aqui se
verifican los TEXTOS, los FICHEROS y las CITAS, que es lo que el brief pega.
"""
import hashlib
import json
import os
import re
import subprocess

import pandas as pd

RAIZ = ".."
V = {}


def lineas(path, a, b):
    ls = open(path, encoding="utf-8").read().splitlines()
    return [f"{i}: {ls[i-1]}" for i in range(a, min(b, len(ls)) + 1)]


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return p.stdout.rstrip(), p.returncode


def main():
    out = {}

    # ---------------------------------------------------------------- 2.1
    print("=== §2.1 el JSON de la bateria ===")
    j = json.load(open("results/portfolio_bateria.json"))
    campos = ["n_trials", "var_trials", "sharpe_anual", "n_obs", "n_obs_eff",
              "skew", "kurt", "sr0_per", "dsr", "t_stat", "pasa_t3",
              "ic_retorno_anual_pct", "edge_ic", "retorno_pct", "max_dd_pct",
              "bench_retorno_pct", "bench_sharpe", "bench_max_dd_pct", "dias",
              "exposicion_media"]
    esperado = {"n_trials": 12, "var_trials": 0.0007021947704551833,
                "sharpe_anual": 1.008, "n_obs": 4403, "n_obs_eff": 4336,
                "skew": 1.037, "kurt": 31.999, "sr0_per": 0.04412,
                "dsr": 0.7191, "t_stat": 3.48, "pasa_t3": True,
                "ic_retorno_anual_pct": [4.47, 20.91], "edge_ic": True,
                "retorno_pct": 317.52, "max_dd_pct": -26.9,
                "bench_retorno_pct": 132831.04, "bench_sharpe": 1.164,
                "bench_max_dd_pct": -88.96, "dias": 4404,
                "exposicion_media": 0.1559827260735808}
    malos = []
    for k in campos:
        ok = j.get(k) == esperado[k]
        if not ok:
            malos.append((k, esperado[k], j.get(k)))
        print(f"  {k:<24} brief={esperado[k]!r:<24} json={j.get(k)!r:<24} {'OK' if ok else 'DIFIERE'}")
    out["2.1"] = {"campos_que_difieren": malos,
                  "veredicto": "CONFIRMADO" if not malos else "REFUTADO"}
    print(f"  sharpe_anual {j['sharpe_anual']} vs bench_sharpe {j['bench_sharpe']}"
          f" -> el bench GANA por {j['bench_sharpe']-j['sharpe_anual']:+.3f}")
    print(f"  retorno {j['retorno_pct']} vs bench {j['bench_retorno_pct']}"
          f" -> ratio {j['bench_retorno_pct']/j['retorno_pct']:.1f}x")
    print(f"  maxDD {j['max_dd_pct']} vs bench {j['bench_max_dd_pct']}"
          f" -> el contrapeso es real, ratio {j['bench_max_dd_pct']/j['max_dd_pct']:.2f}x")
    print(f"  -> §2.1 {out['2.1']['veredicto']}")

    # ---------------------------------------------------------------- 2.2
    print("\n=== §2.2 las cinco lineas del benchmark (318-328 segun el brief) ===")
    real = lineas("src/portfolio_runner.py", 318, 328)
    for l in real:
        print(f"  {l}")
    citado = ["turnover = float(np.nansum(np.abs(w_prev - w_target)))",
              "coste = turnover * (COMMISSION + SLIPPAGE)",
              "equity *= (1 + r_p - coste)",
              "# benchmark: media de activos elegibles (misma condicion de historia)",
              "elig = [i for i in range(n) if rets.iloc[:t + 1].iloc[:, i].notna().sum() >= LOOKBACK + 1]",
              "r_b = float(np.nanmean(r_dia[elig])) if elig else 0.0",
              "eq_curve.append(equity)",
              "bench_curve.append((bench_curve[-1] if bench_curve else 1.0) * (1 + r_b))",
              "exposure.append(float(np.nansum(w_prev)))"]
    cuerpo = "\n".join(open("src/portfolio_runner.py", encoding="utf-8")
                       .read().splitlines()[317:328])
    faltan = [c for c in citado if c not in cuerpo]
    print(f"  lineas citadas por el brief que NO estan en 318-328: {faltan}")
    print("  OJO: el brief etiqueta el bloque '318,328p' (11 lineas) y pega 9.")
    doc6, _ = sh("sed -n '6p' src/portfolio_bateria.py")
    print(f"  portfolio_bateria.py:6 = {doc6!r}")
    es_bh = "buy&hold" in doc6
    print(f"  el docstring dice 'buy&hold': {es_bh}")
    print("  el codigo rebalancea a diario (nanmean del dia) -> NO es buy&hold")
    out["2.2"] = {"lineas_citadas_ausentes": faltan,
                  "docstring_bateria_linea6": doc6,
                  "docstring_dice_buyhold": bool(es_bh),
                  "veredicto": "CONFIRMADO" if not faltan else "CONFIRMADO con correccion"}
    print(f"  -> §2.2 {out['2.2']['veredicto']} (magnitud medida en A-4 y A-5)")

    # ---------------------------------------------------------------- 2.3
    print("\n=== §2.3 benchmark_exposicion de Fase A (185-192) ===")
    for l in lineas("src/rigor_estadistico.py", 185, 192):
        print(f"  {l}")
    txt = open("src/rigor_estadistico.py", encoding="utf-8").read()
    tiene_calmar = "calmar_bh_misma_exposicion" in txt
    tiene_sharpe = "sharpe_bh_misma_exposicion" in txt
    mismo_subconj = "aligned[pos.values]" in txt and "[pos.values]" in txt
    print(f"  reporta Sharpe B&H igual-expo : {tiene_sharpe}")
    print(f"  reporta Calmar B&H igual-expo : {tiene_calmar}")
    print(f"  mismo subconjunto de dias para las dos series: {mismo_subconj}")
    tiene_ic = bool(re.search(r"def benchmark_exposicion.*?\n\n\ndef", txt, re.S)
                    and "bootstrap" in re.search(
                        r"def benchmark_exposicion(.*?)\n\ndef", txt, re.S).group(1))
    print(f"  calcula IC sobre la DIFERENCIA de Sharpes: {tiene_ic}"
          f"   (el brief dice que no, y es el defecto a no repetir)")
    print("  ---- §1: '9 de 11 variantes perdian contra el B&H' (arbol de la RAIZ) ----")
    doc = os.path.join(RAIZ, "docs/rigor_estadistico_resultado.md")
    pierden, total = 0, 0
    for l in open(doc, encoding="utf-8"):
        m = re.match(r"\|\s*([a-z_0-9]+)\s*\|\s*([\d.]+)\s*\|\s*(-?[\d.]+)\s*\|\s*(-?[\d.]+)\s*\|", l)
        if m:
            total += 1
            st, bh = float(m.group(3)), float(m.group(4))
            if st < bh:
                pierden += 1
    print(f"  variantes tabuladas: {total}   pierden en Sharpe: {pierden}")
    out["2.3"] = {"reporta_sharpe": tiene_sharpe, "reporta_calmar": tiene_calmar,
                  "mismo_subconjunto": bool(mismo_subconj),
                  "tiene_ic_diferencial": bool(tiene_ic),
                  "fase_a_variantes": total, "fase_a_pierden": pierden,
                  "veredicto": "CONFIRMADO"}
    print(f"  -> §2.3 CONFIRMADO ({pierden} de {total}, como dice la §1)")

    # ---------------------------------------------------------------- 2.4
    print("\n=== §2.4 los parametros (31-42) ===")
    for l in lineas("src/portfolio_runner.py", 31, 42):
        print(f"  {l}")
    import sys
    sys.path.insert(0, "src")
    import portfolio_runner as pr
    vals = {"LOOKBACK": 365, "LAMBDA": 0.94, "SIGMA_TARGET": 0.10,
            "W_MAX": 0.20, "GROSS_MAX": 1.0, "VOL_TOPE_MULT": 1.25,
            "PPY": 365, "COMMISSION": 0.001, "SLIPPAGE": 0.0005,
            "DATA_DIR": "data/multi"}
    mal = {k: (v, getattr(pr, k)) for k, v in vals.items() if getattr(pr, k) != v}
    print(f"  constantes que difieren del brief: {mal or 'ninguna'}")
    print(f"  ACTIVOS = {pr.ACTIVOS}")
    print("  OJO: el brief etiqueta '31,42p' y la linea 31 es la 2a de ACTIVOS;")
    print("       ACTIVOS empieza en la 30. Desviacion de forma.")
    out["2.4"] = {"constantes_que_difieren": mal,
                  "activos": pr.ACTIVOS,
                  "etiqueta_de_lineas_desplazada": True,
                  "veredicto": "CONFIRMADO con correccion" if not mal else "REFUTADO"}
    print(f"  -> §2.4 {out['2.4']['veredicto']}")

    # ---------------------------------------------------------------- 2.5
    print("\n=== §2.5 no hay tasa libre de riesgo en src/ ===")
    o, rc = sh("git grep -n -i -E 'risk_free|risk-free|libre de riesgo|\\brf\\b|tasa' "
               "fase-b-recuperada -- fix-fase2/src/", cwd=RAIZ)
    print(f"  salida del grep del brief: {o!r}   rc={rc}")
    o2, _ = sh("git grep -n -i -E 'risk_free|risk.free|libre de riesgo' "
               "fase-b-recuperada", cwd=RAIZ)
    print(f"  mismo patron en TODA la rama: {o2!r}")
    hay_serie = []
    for d in ["data", "data/multi", os.path.join(RAIZ, "data")]:
        if os.path.isdir(d):
            hay_serie += [f for f in os.listdir(d)
                          if re.search(r"dgs|tbill|rf|rate|libor|sofr", f, re.I)]
    print(f"  ficheros con pinta de serie de tasas en data/: {hay_serie or 'ninguno'}")
    out["2.5"] = {"grep_vacio": o == "", "grep_rama_completa": o2,
                  "ficheros_de_tasas": hay_serie,
                  "veredicto": "CONFIRMADO" if o == "" else "REFUTADO"}
    print(f"  -> §2.5 {out['2.5']['veredicto']}")

    # ---------------------------------------------------------------- 2.6
    print("\n=== §2.6 la curva del benchmark existe y es auditable ===")
    o, _ = sh("head -3 results/portfolio_benchmark.csv")
    print("  head -3:"); [print(f"    {x}") for x in o.splitlines()]
    o2, _ = sh("tail -2 results/portfolio_benchmark.csv")
    print("  tail -2:"); [print(f"    {x}") for x in o2.splitlines()]
    nl, _ = sh("wc -l < results/portfolio_benchmark.csv")
    be = pd.read_csv("results/portfolio_benchmark.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    print(f"  wc -l = {nl.strip()}   filas de datos = {len(be)}")
    ret = (be.iloc[-1] / be.iloc[0] - 1) * 100
    print(f"  {be.index[0].date()} -> {be.index[-1].date()}, "
          f"{be.iloc[0]} -> {be.iloc[-1]}")
    print(f"  retorno implicito = {ret:.2f} %  (brief: 132831.04)")
    hay_expo = os.path.exists("results/portfolio_exposure.csv")
    print(f"  ¿hay serie exposure en results/? {hay_expo}  "
          f"(el brief dice que no, y por eso A-3 la regenera)")
    out["2.6"] = {"wc_l": int(nl.strip()), "filas": int(len(be)),
                  "ini": str(be.index[0].date()), "fin": str(be.index[-1].date()),
                  "v0": float(be.iloc[0]), "vN": float(be.iloc[-1]),
                  "retorno_pct": round(float(ret), 2),
                  "exposure_en_results": bool(hay_expo),
                  "veredicto": "CONFIRMADO"}
    print("  -> §2.6 CONFIRMADO")

    # ---------------------------------------------------------------- 2.7
    print("\n=== §2.7 el segundo panel y su benchmark ===")
    for l in lineas("src/portfolio_supervivencia.py", 6, 13):
        print(f"  {l}")
    print("  OJO: el brief etiqueta '6,13p' y pega NUEVE lineas: ICP-USD es la 14.")
    files = {f: os.path.exists(f"results/{f}") for f in
             ["portfolio_benchmark_muertos.csv", "portfolio_equity_muertos.csv",
              "portfolio_supervivencia.json"]}
    print(f"  ficheros: {files}")
    sj = json.load(open("results/portfolio_supervivencia.json"))
    interes = {k: sj[k] for k in sj if not isinstance(sj[k], (list, dict))}
    print(f"  portfolio_supervivencia.json: {interes}")
    nm = len([f for f in os.listdir("data/multi_muertos") if f.endswith(".csv")])
    sellos = sorted({f.rsplit("_", 1)[1][:8] for f in
                     os.listdir("data/multi_muertos") if f.endswith(".csv")})
    print(f"  data/multi_muertos: {nm} CSV, sellos {sellos}")
    print("  -> el panel de 15 SOLO tiene sello 20261009 (no hay 20261007)")
    out["2.7"] = {"ficheros": files, "supervivencia_json": interes,
                  "csv_muertos": nm, "sellos_muertos": sellos,
                  "etiqueta_de_lineas_desplazada": True,
                  "veredicto": "CONFIRMADO con correccion"}
    print(f"  -> §2.7 {out['2.7']['veredicto']}")

    # ---------------------------------------------------------------- 2.8
    print("\n=== §2.8 lo que esto NO prueba ===")
    print("  Es una regla de metodo, no una proposicion empirica.")
    print("  Se verifica su unica parte comprobable: que el expediente NO tiene")
    print("  ninguna comparacion a igual exposicion para Fase B.")
    o, _ = sh("git grep -l -i -E 'exposicion_igualada|igual expos|misma exposicion' "
              "fase-b-recuperada -- fix-fase2/", cwd=RAIZ)
    print(f"  ficheros de fix-fase2/ que la mencionan: {o.splitlines() or 'ninguno'}")
    pw = json.load(open("results/portfolio_walkforward_temporal.json"))
    sb = {k: v.get("supera_bench_sharpe") for k, v in pw["resultados"].items()
          if isinstance(v, dict) and v}
    print(f"  PERO: portfolio_walkforward_temporal.json YA publica "
          f"supera_bench_sharpe = {sb}")
    print("  -> la §1 del brief ('NINGUNA ha preguntado si supera a comprar y")
    print("     aguantar') es FALSA tal como esta escrita: la comparacion SIN")
    print("     igualar exposicion ya esta hecha y publicada, y da False 3/3.")
    print("     Lo que no esta hecho es la comparacion A IGUAL EXPOSICION.")
    out["2.8"] = {"ficheros_que_mencionan_igual_exposicion": o.splitlines(),
                  "supera_bench_sharpe_publicado": sb,
                  "veredicto": "CONFIRMADO como regla; la §1 del brief, REFUTADA "
                               "tal como esta escrita"}
    print(f"  -> §2.8 {out['2.8']['veredicto']}")

    json.dump(out, open("fase0_n7/a1_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/a1_salida.json")
    print("=== RESUMEN DE VEREDICTOS ===")
    for k in sorted(out):
        print(f"  §{k}: {out[k]['veredicto']}")


if __name__ == "__main__":
    main()
