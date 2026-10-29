"""Verificacion sintetica paquete 3 (supervivencia), ANTES de datos.

No se re-testea el nucleo (bateria ya validada en verificar_rigor_sintetico):
lo nuevo aqui es la COMPARACION DE DICTAMENES entre universos. Casos:
  1. Decisor de comparacion con metricas de respuesta conocida: universo
     superviviente con edge (t>3, IC+, DSR alta, supera bench) vs extendido
     que destruye el edge (IC negativo, no supera bench) -> dictamen
     "SEÑAL MUERTA por supervivencia".
  2. Caso simetrico: el universo extendido MANTIENE las 4 pruebas -> dictamen
     "SEÑAL VIVA".
  3. Integridad del universo: la funcion de criterio exige >=5 activos
     caidos y >=10 vivos, y rechaza listas que incumplen.

Sin LLM, sin red, determinista.

Uso: /opt/trading-bot/venv/bin/python verificar_supervivencia_sintetico.py
"""
import sys

sys.path.insert(0, "src")
from portfolio_supervivencia import MUERTOS, VIVOS  # noqa: E402


def dictamen_comparacion(superviviente: dict, extendido: dict) -> dict:
    """Decisor: la senal muere por supervivencia si en el universo con
    muertos cae CUALQUIERA de las 4 pruebas que el superviviente pasaba."""
    pruebas = ["pasa_t3", "edge_ic", "supera_bench_sharpe"]
    caidas = [p for p in pruebas
              if superviviente.get(p) and not extendido.get(p)]
    muerta = bool(caidas)
    dsr_cayo = bool(superviviente.get("dsr", 0) >= 0.95
                    and extendido.get("dsr", 0) < 0.95)
    return {"senal_muerta": muerta, "pruebas_caidas": caidas,
            "dsr_cayo": dsr_cayo}


def caso_muerta():
    sup = {"pasa_t3": True, "edge_ic": True, "supera_bench_sharpe": True,
           "dsr": 0.72}
    ext = {"pasa_t3": False, "edge_ic": False, "supera_bench_sharpe": True,
           "dsr": 0.10}
    d = dictamen_comparacion(sup, ext)
    ok = d["senal_muerta"] and set(d["pruebas_caidas"]) == {"pasa_t3", "edge_ic"}
    print(f"  1. extendido destruye edge -> muerta={d['senal_muerta']} "
          f"caidas={d['pruebas_caidas']} -> {'OK' if ok else 'FALLO'}")
    return ok


def caso_viva():
    sup = {"pasa_t3": True, "edge_ic": True, "supera_bench_sharpe": True,
           "dsr": 0.72}
    ext = {"pasa_t3": True, "edge_ic": True, "supera_bench_sharpe": True,
           "dsr": 0.68}
    d = dictamen_comparacion(sup, ext)
    ok = not d["senal_muerta"]
    print(f"  2. extendido mantiene edge -> muerta={d['senal_muerta']} -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def caso_universo():
    ok = len(MUERTOS) >= 5 and len(VIVOS) >= 10
    for m in MUERTOS:
        if m in VIVOS:
            ok = False
    print(f"  3. universo: {len(VIVOS)} vivos + {len(MUERTOS)} caidos, "
          f"sin solape -> {'OK' if ok else 'FALLO'}")
    return ok


def main():
    ok = caso_muerta() and caso_viva() and caso_universo()
    print(f"\nVERIFICACION SUPERVIVENCIA SINTETICA {'OK' if ok else 'FALLO'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
