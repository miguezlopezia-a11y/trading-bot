"""Verificacion sintetica paquete 1 (walk-forward temporal), ANTES de datos.

Casos:
  1. Dictamen con ICs de respuesta conocida: 2 positivos + 1 ruido -> SUPERADO;
     3 ruido (ICs cruzan 0) -> NO SUPERADO; 1 positivo + 1 claramente negativo
     -> NO SUPERADO (el tramo negativo mata aunque haya 2 positivos).
  2. Tramos de series reales sinteticas: 2 tramos con drift positivo y 1 de
     ruido puro (seed fija) -> el pipeline bateria_tramo + dictamen clasifica
     SUPERADO; 3 tramos de ruido -> NO SUPERADO.

Sin LLM, sin red, determinista.

Uso: /opt/trading-bot/venv/bin/python verificar_portfolio_walkforward_sintetico.py
"""
import sys

import numpy as np

sys.path.insert(0, "src")
from portfolio_walkforward_temporal import bateria_tramo, dictamen_tramos  # noqa: E402


def caso_dictamen_puro():
    ok = True
    r = dictamen_tramos({"a": {"ic95_retorno_anual_pct": [1.0, 5.0]},
                         "b": {"ic95_retorno_anual_pct": [0.5, 8.0]},
                         "c": {"ic95_retorno_anual_pct": [-3.0, 4.0]}})
    if not r["superado"]:
        print("  FALLO 1a: 2 positivos + 1 ruido deberia SUPERAR"); ok = False
    r2 = dictamen_tramos({"a": {"ic95_retorno_anual_pct": [-2.0, 3.0]},
                          "b": {"ic95_retorno_anual_pct": [-1.0, 2.0]},
                          "c": {"ic95_retorno_anual_pct": [-4.0, 5.0]}})
    if r2["superado"]:
        print("  FALLO 1b: 3 ruido no deberia superar"); ok = False
    r3 = dictamen_tramos({"a": {"ic95_retorno_anual_pct": [1.0, 5.0]},
                          "b": {"ic95_retorno_anual_pct": [0.5, 8.0]},
                          "c": {"ic95_retorno_anual_pct": [-8.0, -1.0]}})
    if r3["superado"]:
        print("  FALLO 1c: 1 claramente negativo mata el dictamen"); ok = False
    print(f"  1. dictamen puro: 2pos+ruido->{'SUPERADO' if r['superado'] else 'NO'}; "
          f"ruido->{'NO' if not r2['superado'] else 'SUPERADO'}; "
          f"con negativo->{'NO' if not r3['superado'] else 'SUPERADO'} -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def caso_series():
    rng = np.random.default_rng(42)
    T = 1500
    edge = 0.0012  # drift diario -> SR anual ~2.3 con sigma 1%: margen amplio
    def tramo(drift):
        return drift + rng.normal(0, 0.01, T)
    import pandas as pd
    def run(tramos):
        res = {}
        for i, s in enumerate(tramos):
            r = bateria_tramo(pd.Series(s), seed=42 + i)
            res[f"t{i}"] = {"ic95_retorno_anual_pct": r["ic95_retorno_anual_pct"]}
        return dictamen_tramos(res)
    d_edge = run([tramo(edge), tramo(edge), tramo(0.0)])
    d_ruido = run([tramo(0.0), tramo(0.0), tramo(0.0)])
    ok = d_edge["superado"] and not d_ruido["superado"]
    print(f"  2. series sinteticas: edge2+ruido1 -> "
          f"{'SUPERADO' if d_edge['superado'] else 'NO'}; ruido3 -> "
          f"{'SUPERADO' if d_ruido['superado'] else 'NO'} -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def main():
    ok = caso_dictamen_puro() and caso_series()
    if ok:
        print("\nVERIFICACION WF-TEMPORAL SINTETICA OK.")
        return 0
    print("\nVERIFICACION WF-TEMPORAL SINTETICA FALLO: no correr datos reales.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
