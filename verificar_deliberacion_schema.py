"""Verificacion 1.1 — deliberacion 6 Sombreros: schema + veto por defecto.

20 deliberaciones sinteticas con FakeProvider determinista, incluidos casos
malformados a proposito (JSON roto, texto plano, schema equivocado, veredicto
invalido). A asertar:
  - sanos: schema valida, veredicto coherente con los sombreros, parseable.
  - malformados: reparacion y, si persiste, veto por defecto parseable
    (veredicto "no", motivo veto_por_defecto_parse) — NUNCA una excepcion ni
    una salida sin schema.
  - la salida SIEMPRE pasa deliberation.valida_deliberacion().

Uso: /opt/trading-bot/venv/bin/python verificar_deliberacion_schema.py
"""
import json
import sys

sys.path.insert(0, "src")
from deliberation import (SOMBREROS, deliberar, valida_deliberacion,  # noqa: E402
                          FakeProvider, Provider)

SANO_SI = json.dumps({"veredicto": "si", "size_ajuste": None,
                      "justificacion": "todo en orden"})
SANO_NO = json.dumps({"veredicto": "no", "size_ajuste": None,
                      "justificacion": "senal en contra del regimen"})
SANO_AJUSTA = json.dumps({"veredicto": "ajustar", "size_ajuste": 0.5,
                          "justificacion": "media confianza"})

MALFORMADOS = [
    "no es json, es texto plano",
    '{"veredicto": "si"}',                                          # faltan claves
    '{"veredicto": "quizas", "size_ajuste": null, "justificacion": "x"}',  # veredicto invalido
    '{"veredicto": "ajustar", "size_ajuste": "medio", "justificacion": "x"}',  # tipo mal
    '{"veredicto": "ajustar", "size_ajuste": 1.5, "justificacion": "x"}',      # fuera de rango
    '{"veredicto": "si", "size_ajuste": 0.5, "justificacion": "x"}',           # size sin ajustar
    '[{"veredicto": "si"}]',                                        # array, no objeto
    '{"veredicto": "si", "size_ajuste": null, "justificacion": 42}',  # justif no string
]


def candidato(i):
    return {"estrategia": "ma_cross", "activo": "BTC-USD",
            "direccion": "long" if i % 2 == 0 else "short",
            "contexto": {"caso": i, "equity": 1.0 + i * 0.01}}


def main():
    ok = True

    # 8 casos sanos: 3x si, 3x no, 2x ajustar
    sanos = [(SANO_SI, "si", 1.0), (SANO_NO, "no", 0.0), (SANO_AJUSTA, "ajustar", 0.5)]
    n_ok = 0
    for i in range(8):
        resp, esperado, size_esp = sanos[i % 3]
        provider = FakeProvider(default=resp)
        d = deliberar(candidato(i), provider)
        if not valida_deliberacion(d):
            print(f"  FALLO sano {i}: schema invalido"); ok = False; continue
        if d["veredicto"] != esperado:
            print(f"  FALLO sano {i}: veredicto {d['veredicto']} != {esperado}"); ok = False
        if esperado != "ajustar" and abs(d["size_final"] - size_esp) > 1e-9:
            print(f"  FALLO sano {i}: size_final {d['size_final']}"); ok = False
        # prompts versionados: hash presente por sombrero
        if any("prompt_sha256" not in s for s in d["sombreros"].values()):
            print(f"  FALLO sano {i}: falta prompt_sha256"); ok = False
        json.dumps(d)
        n_ok += 1
    print(f"  OK sanos: {n_ok}/8 deliberaciones validas, veredicto y size coherentes")

    # 12 casos malformados: cada respuesta malformada se repite en los 6 sombreros
    n_mal = 0
    for j, malf in enumerate(MALFORMADOS):
        for persistente in (False, True):
            # no persistente: por sombrero, 1er intento malo + reparacion OK
            # (cola intercalada: el FakeProvider hace pop por llamada)
            # persistente: 1er y 2do intento malos por sombrero -> veto
            if persistente:
                respuestas = [malf] * 12
            else:
                respuestas = []
                for _ in range(6):
                    respuestas += [malf, SANO_SI]
            provider = FakeProvider(respuestas=respuestas)
            try:
                d = deliberar(candidato(100 + j), provider)
            except Exception as e:
                print(f"  FALLO malformado {j} (persistente={persistente}): "
                      f"excepcion {e}"); ok = False; continue
            if not valida_deliberacion(d):
                print(f"  FALLO malformado {j}: salida sin schema"); ok = False; continue
            json.dumps(d)
            if persistente:
                esperado = "no"
                if d["veredicto"] != esperado:
                    print(f"  FALLO malformado {j}: sin veto por defecto "
                          f"({d['veredicto']})"); ok = False; continue
                vetos = [s for s in d["sombreros"].values()
                         if "veto_por_defecto_parse" in s["justificacion"]]
                if len(vetos) != 6:
                    print(f"  FALLO malformado {j}: {len(vetos)}/6 sombreros con veto"); ok = False; continue
            else:
                if d["veredicto"] != "si":
                    print(f"  FALLO malformado {j}: reparacion OK pero veredicto "
                          f"{d['veredicto']}"); ok = False; continue
                if not all(s["reparado"] for s in d["sombreros"].values()):
                    print(f"  FALLO malformado {j}: reparacion no marcada"); ok = False; continue
            n_mal += 1
    n_comb = len(MALFORMADOS) * 2
    print(f"  OK malformados: {n_mal}/{n_comb} combinaciones (reparacion o veto por defecto, "
          f"nunca excepcion ni salida sin parsear)")

    # 2 casos de proveedor caido (excepcion de transporte, p.ej. HTTPError por
    # falta de credito): sin reintento, motivo proveedor_indisponible, nunca
    # confundido con "el LLM deliberó y vetó"
    class ProveedorCaido(Provider):
        def complete(self, system_prompt, user_message):
            raise ConnectionError("simulado: credit balance too low")

    d = deliberar(candidato(200), ProveedorCaido())
    if not valida_deliberacion(d) or d["motivo"] != "proveedor_indisponible":
        print(f"  FALLO proveedor caido: motivo {d['motivo']}"); ok = False
    elif not all("proveedor_indisponible" in s["justificacion"]
                 for s in d["sombreros"].values()):
        print("  FALLO proveedor caido: justificaciones incorrectas"); ok = False
    else:
        print("  OK proveedor caido: motivo proveedor_indisponible (no 'veto deliberado')")

    total = 8 + n_comb + 1
    if ok:
        print(f"\nVERIFICACION OK: {total} deliberaciones sinteticas — schema validado, "
              f"veto por defecto parseable, sin decision sin parsear.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
