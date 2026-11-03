"""N7 · A-6 — Copiar los cortes T1/T2/T3 DEL CODIGO, no asumirlos.
Corre DESDE fix-fase2/.  Salida: a6_salida.json
El brief no los transcribe a proposito. Aqui se leen de
src/portfolio_walkforward_temporal.py y se contrastan con el JSON publicado.
"""
import ast
import json
import re

import pandas as pd

SRC = "src/portfolio_walkforward_temporal.py"
PUB = "results/portfolio_walkforward_temporal.json"


def main():
    txt = open(SRC, encoding="utf-8").read()
    lineas = txt.splitlines()
    print("=== A-6.1 las lineas literales del codigo ===")
    ini = None
    for i, l in enumerate(lineas, 1):
        if l.startswith("TRAMOS"):
            ini = i
            break
    bloque = []
    for i in range(ini, min(ini + 6, len(lineas) + 1)):
        l = lineas[i - 1]
        bloque.append(f"{i}: {l}")
        print(f"  {i}: {l}")
        if l.rstrip().endswith("]"):
            break
    print("=== A-6.2 docstring del diseno (lineas 8-18) ===")
    for i in range(8, 19):
        print(f"  {i}: {lineas[i-1]}")

    m = re.search(r"TRAMOS\s*=\s*(\[[^\]]*\])", txt, re.S)
    tramos = ast.literal_eval(m.group(1))
    print("=== A-6.3 TRAMOS evaluado ===")
    for t in tramos:
        print(f"  {t}")

    print("=== A-6.4 contraste con el JSON publicado ===")
    pub = json.load(open(PUB))
    pub_def = [list(x) for x in pub.get("tramos_definicion", [])]
    print(f"  tramos_definicion publicado: {pub_def}")
    coincide = pub_def == [list(t) for t in tramos]
    print(f"  coincide con el codigo: {coincide}")

    print("=== A-6.5 dias reales de cada tramo sobre la equity congelada ===")
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    reales = {}
    for nom, a, b in tramos:
        mask = (eq.index >= a) & (eq.index <= b)
        s = eq[mask]
        r = s.pct_change().dropna()
        reales[nom] = {"ini_real": str(s.index[0].date()),
                       "fin_real": str(s.index[-1].date()),
                       "dias": int(len(s)), "retornos": int(len(r))}
        print(f"  {nom:<16} {s.index[0].date()} -> {s.index[-1].date()}"
              f"  dias={len(s):>5} retornos={len(r):>5}")
    print("  NOTA: T3 se cierra con '2262-12-31', no con la fecha real de fin.")
    print("        El corte efectivo lo pone el ultimo dia de datos del sello.")

    out = {"fuente": SRC, "lineas_tramos": bloque,
           "TRAMOS": [list(t) for t in tramos],
           "tramos_definicion_publicado": pub_def,
           "coincide_codigo_vs_json": bool(coincide),
           "tramos_sobre_equity_congelada": reales,
           "advertencia": "T3 termina en '2262-12-31' (centinela), no en fin real"}
    json.dump(out, open("fase0_n7/a6_salida.json", "w"), indent=2)
    print("-> fase0_n7/a6_salida.json")



# --- A-6.6 anadido tras encontrarlo: el walkforward YA compara contra el bench
def a6_6():
    import json as _j
    print("=== A-6.6 el walkforward publicado YA tiene campos de benchmark ===")
    # CORREGIDO tras la critica del Maker/Verifier (hallazgo 9, ALTA).
    # La v1 iteraba el NIVEL RAIZ del JSON, cuyas claves son
    # tramos_definicion / n_trials / var_trials / seed / resultados. Los dicts
    # por tramo estan ANIDADOS dentro de "resultados", asi que el filtro nunca
    # encontraba nada e imprimia "resultados: {}". El registro pego a mano las
    # cifras que habia sacado con una consulta aparte. Ahora las produce el script.
    pub = _j.load(open(PUB))
    for k, v in pub["resultados"].items():
        if not isinstance(v, dict) or not v:
            continue
        campos = {kk: v[kk] for kk in v
                  if "bench" in kk or kk in ("sharpe_anual", "exposicion_media")}
        print(f"  {k}: {campos}")
    print("  -> 'supera_bench_sharpe' existe en el codigo "
          "(portfolio_walkforward_temporal.py:100) y en el JSON.")


if __name__ == "__main__":
    main()
    a6_6()
