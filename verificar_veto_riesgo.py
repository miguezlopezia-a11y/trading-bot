"""Verificacion — veto de riesgo: los 3 casos se vetan SIEMPRE, con y sin LLM.

  1. sizing > limite  -> veto
  2. DD proyectado > umbral -> veto
  3. estrategia descartada (las 3 no-ma_cross) -> veto SIEMPRE
Y el caso sano (ma_cross dentro de limites) NO se veta. evaluar_veto es
determinista y no toca ningun proveedor LLM (no hace falta uno).

Uso: /opt/trading-bot/venv/bin/python verificar_veto_riesgo.py
"""
import sys

sys.path.insert(0, "src")
from risk_veto import evaluar_veto, SIZE_MAX, DD_MAX_PCT, ESTRATEGIAS_DESCARTADAS  # noqa: E402

CASOS_VETADOS = [
    ("sizing > limite", {"estrategia": "ma_cross", "sizing": SIZE_MAX + 0.01,
                         "dd_proyectado_pct": -2.0}, "sizing_sobre_limite"),
    ("DD > umbral", {"estrategia": "ma_cross", "sizing": 0.01,
                     "dd_proyectado_pct": DD_MAX_PCT - 1.0}, "dd_sobre_umbral"),
    ("estrategia descartada", {"estrategia": "trend_following", "sizing": 0.01,
                               "dd_proyectado_pct": -1.0}, "estrategia_descartada"),
]


def main():
    ok = True
    # con LLM disponible en el entorno y sin el (el veto no depende de ello)
    for con_llm in (True, False):
        if not con_llm:
            import os
            saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        for nombre, cand, esperado in CASOS_VETADOS:
            v = evaluar_veto(cand)
            if not v["vetado"]:
                print(f"  FALLO [{nombre} con_llm={con_llm}]: no veto"); ok = False; continue
            if not any(m.startswith(esperado) for m in v["motivos"]):
                print(f"  FALLO [{nombre} con_llm={con_llm}]: motivos {v['motivos']}"); ok = False; continue
            print(f"  OK [{nombre}] con_llm={con_llm}: vetado, motivo '{esperado}'")
        if not con_llm and saved is not None:
            import os
            os.environ["ANTHROPIC_API_KEY"] = saved

    # las 3 estrategias descartadas siempre vetan
    for estr in sorted(ESTRATEGIAS_DESCARTADAS):
        v = evaluar_veto({"estrategia": estr, "sizing": 0.001, "dd_proyectado_pct": -0.5})
        if not v["vetado"]:
            print(f"  FALLO: {estr} no vetada"); ok = False
        else:
            print(f"  OK estrategia descartada '{estr}': vetada siempre")

    # sano: ma_cross dentro de limites -> NO veto
    v = evaluar_veto({"estrategia": "ma_cross", "sizing": 0.01, "dd_proyectado_pct": -2.0})
    if v["vetado"]:
        print(f"  FALLO: caso sano vetado {v['motivos']}"); ok = False
    else:
        print("  OK caso sano (ma_cross, sizing 1%, DD -2%): no vetado")

    if ok:
        print("\nVERIFICACION OK: veto de riesgo correcto en los 3 casos, con y sin LLM.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
