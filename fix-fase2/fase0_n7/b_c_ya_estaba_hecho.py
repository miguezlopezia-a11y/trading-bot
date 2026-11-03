"""N7 · B-c (propia, CRITICA) — La comparacion que el brief dice que no existe
YA ESTA HECHA, MEDIDA, PUBLICADA Y AUDITADA. Un dia antes del brief.
Corre DESDE fix-fase2/.  Salida: b_c_salida.json
"""
import json
import os
import subprocess


def sh(cmd, cwd=None):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return p.stdout.rstrip()


def main():
    out = {}
    print("=== B-c.1 el fichero existe y hace exactamente esto ===")
    f = "auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py"
    print(f"  {f}  ({os.path.getsize(f)} bytes)")
    ls = open(f, encoding="utf-8").read().splitlines()
    for i in range(1, 30):
        print(f"  {i:>3}: {ls[i-1]}")
    out["script"] = f
    out["existe"] = os.path.exists(f)

    print("\n=== B-c.2 su salida publicada ===")
    j = json.load(open("auditoria_n1/salida_3_0d_exposicion.json"))
    for k, v in j.items():
        print(f"  {k:<32} {v}")
    out["salida_3_0d"] = j

    print("\n=== B-c.3 esta en los documentos de dictamen ===")
    for doc, pat in [("docs/estado-auditoria-n1.md", "H11"),
                     ("docs/auditoria_harness_n1.md", "3.0d")]:
        print(f"  --- {doc} (lineas con '{pat}') ---")
        o = sh(f"grep -n '{pat}' {doc} | head -4")
        for l in o.splitlines():
            print(f"   {l[:300]}")
    out["documentado_en"] = ["docs/estado-auditoria-n1.md (H11)",
                             "docs/auditoria_harness_n1.md (3.0d, 5-bis)"]

    print("\n=== B-c.4 fechas: el 3.0d es ANTERIOR al brief ===")
    o = sh("git log -1 --format='%h %ad %s' --date=iso -- "
           "fix-fase2/auditoria_n1/paso_3_0d_benchmark_exposicion_igualada.py",
           cwd="..")
    print(f"  commit del 3.0d        : {o}")
    print(f"  estado-auditoria-n1.md : "
          f"{sh('grep -n \"2026-11-01\" docs/estado-auditoria-n1.md | head -2')}")
    print("  brief de N7 declara    : 'sesion de escritorio, 2026-11-02 14:21'")
    out["commit_3_0d"] = o

    print("\n=== B-c.5 que de la §4 queda sin hacer, y que no ===")
    hecho = {
        "§4.1(a) escalado dia a dia": "HECHO en 3.0d PARTE C (sharpe_bh_igual_exposicion=1.07121)",
        "§4.1(b) escalado por constante k": "INNECESARIO: 3.0d ya demuestra la invariancia de escala (k=0.5/1/2)",
        "§4.1(c) binario tipo Fase A": "HECHO en 3.0d PARTE B (mascara_binaria: 1.13587 vs 1.15670)",
        "§4.2 hilo 1 costes del benchmark": "NO hecho (lo mide A-4 de esta Fase 0)",
        "§4.2 hilo 2 rf del efectivo": "VACIO en (a): las dos series tienen la MISMA exposicion, luego el mismo efectivo, luego rf se cancela exactamente en el diferencial",
        "§4.2 hilo 3 B&H puro vs EW diario": "NO hecho (lo mide A-5 de esta Fase 0)",
        "§4.2 hilo 4 regla de entrada": "NO hecho (lo mide A-4: el bench admite cada activo 1 dia antes, 10 celdas)",
        "§4.3 IC del diferencial por block bootstrap": "NO hecho. ES LA UNICA APORTACION GENUINA DE LA §4",
        "§4.4 por tramos": "PARCIAL: portfolio_walkforward_temporal.json ya publica supera_bench_sharpe=False en T1/T2/T3, SIN igualar exposicion",
        "test de seleccion por permutaciones": "HECHO en 3.0d PARTE D (percentil 73.55) y el brief NO LO CONTEMPLA",
    }
    for k, v in hecho.items():
        print(f"  {k}\n      -> {v}")
    out["estado_de_la_seccion_4"] = hecho

    print("\n=== B-c.6 defecto en el material EXISTENTE, para que conste ===")
    print("  3.0d imprime en su PARTE B: 'Matiz: con 99%+ de dias con")
    print("  exposicion>0 esta construccion apenas corrige nada'.")
    print(f"  Su propio JSON dice dias_exposicion_cero = {j['dias_exposicion_cero']}"
          f" de {j['dias']} = {100*j['dias_exposicion_cero']/j['dias']:.1f} % a cero,")
    print(f"  o sea {100-100*j['dias_exposicion_cero']/j['dias']:.1f} % con exposicion>0,"
          f" NO '99%+'. La conclusion ('apenas")
    print("  corrige nada') sigue siendo correcta, la cifra que la apoya no.")
    out["defecto_en_3_0d"] = {
        "afirma": "99%+ de dias con exposicion>0",
        "medido": f"{100-100*j['dias_exposicion_cero']/j['dias']:.2f} %",
        "dias_cero": j["dias_exposicion_cero"], "dias": j["dias"]}

    json.dump(out, open("fase0_n7/b_c_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/b_c_salida.json")


if __name__ == "__main__":
    main()
