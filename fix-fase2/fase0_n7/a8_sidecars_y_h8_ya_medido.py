"""N7 · A-8 — ANADIDO tras la critica del Maker/Verifier.
Corre DESDE fix-fase2/.  Salida: a8_salida.json

Dos cosas que la v1 del registro afirmo sin script detras:

(1) hallazgo 16, MEDIA: "los 35 sidecars .sha256 estan verificados, no
    asumidos". Era cierto pero no lo contaba ningun script, y se atribuia a
    A-7, que no toca hashes. Aqui se cuentan y se verifican.

(2) hallazgo 5, CRITICA: la asimetria `:t+1` contra `:t` del elegible del
    benchmark, que el registro presento como hallazgo propio de A-4 y declaro
    "NO hecho" en su tabla de supervivencia de la §4, YA ESTA MEDIDA Y
    DICTAMINADA como H8, en el MISMO directorio auditoria_n1/ del que el
    registro saco su hallazgo CRITICO, y en el MISMO documento de dictamen que
    grepea. Aqui se lee su salida publicada.
"""
import glob
import hashlib
import json
import os
import subprocess


def main():
    out = {}
    print("=== A-8.1 los sidecars .sha256, verificados con comando propio ===")
    tot, mal, det = 0, [], {}
    for d in ["data/multi", "data/multi_muertos"]:
        n_ok, n_mal = 0, 0
        for side in sorted(glob.glob(d + "/*.sha256")):
            csv = side[:-7]
            tot += 1
            calc = hashlib.sha256(open(csv, "rb").read()).hexdigest()
            esp = open(side).read().split()[0]
            if calc == esp:
                n_ok += 1
            else:
                n_mal += 1
                mal.append(csv)
        det[d] = {"sidecars": n_ok + n_mal, "cuadran": n_ok, "descuadran": n_mal}
        print(f"  {d:<22} sidecars={n_ok+n_mal:>3}  cuadran={n_ok:>3}  "
              f"descuadran={n_mal}")
    print(f"  TOTAL sidecars verificados: {tot}   descuadran: {len(mal)}")
    print(f"  ficheros que descuadran: {mal or 'ninguno'}")
    out["sidecars"] = {"total": tot, "descuadran": len(mal),
                       "ficheros_malos": mal, "por_directorio": det}

    print("\n=== A-8.2 H8: la asimetria del elegible YA estaba medida ===")
    f = "auditoria_n1/paso_3_5_simetria_benchmark.py"
    print(f"  fichero: {f}  (existe: {os.path.exists(f)})")
    ls = open(f, encoding="utf-8").read().splitlines()
    for i in range(8, 14):
        print(f"  {i:>3}: {ls[i-1]}")
    j = json.load(open("auditoria_n1/salida_3_5_simetria.json"))["parte_a"]
    campos = ("decisiones", "divergentes", "sharpe_benchmark_actual",
              "sharpe_benchmark_simetrico")
    print("  salida_3_5_simetria.json, parte_a:")
    for k in campos:
        print(f"    {k:<28} {j[k]}")
    delta = j["sharpe_benchmark_actual"] - j["sharpe_benchmark_simetrico"]
    print(f"    delta de Sharpe del benchmark  {delta:+.4f}"
          f"   ({j['divergentes']} de {j['decisiones']} decisiones,"
          f" {100*j['divergentes']/j['decisiones']:.3f} %)")
    out["h8_medido"] = {k: j[k] for k in campos}
    out["h8_medido"]["delta_sharpe"] = delta

    print("\n  --- y su dictamen publicado, en el fichero que el registro grepea ---")
    p = subprocess.run("sed -n '46p' docs/auditoria_harness_n1.md", shell=True,
                       capture_output=True, text=True)
    print(f"  docs/auditoria_harness_n1.md:46")
    print(f"   {p.stdout.strip()}")
    out["dictamen_h8"] = p.stdout.strip()

    print("\n=== A-8.3 que implica para el registro ===")
    print("  La v1 escribio en su tabla de supervivencia de la §4:")
    print('    "§4.2 hilo 4, regla de entrada | NO hecho, y la respuesta es *no*:')
    print('     A-4.1 encuentra la asimetria de :t+1 contra :t"')
    print("  Es FALSO: esta hecho, medido, cuantificado en Sharpe (+0.0041, que")
    print("  la v1 no daba) y dictaminado como H8 (BAJO). Mi A-4.1 reproduce sus")
    print("  10 celdas divergentes sin saberlo.")
    print("  Y es el mismo punto ciego que el registro le cobra al brief: yo abri")
    print("  paso_3_0d y no abri paso_3_5_simetria_benchmark.py, que esta en el")
    print("  mismo directorio y se llama literalmente 'simetria del benchmark'.")
    out["consecuencia"] = ("el hilo 4 de la §4.2 esta HECHO: H8, BAJO, "
                           "10 de 44030 decisiones, +0.0041 de Sharpe. "
                           "La fila 'NO hecho' del registro era falsa.")

    json.dump(out, open("fase0_n7/a8_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/a8_salida.json")


if __name__ == "__main__":
    main()
