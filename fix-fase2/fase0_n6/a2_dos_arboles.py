"""A-2 (N6, Fase 0) — ¿Se contradicen los dos arboles de resultados?

El brief (§2.1) dice que results/ y fix-fase2/results/ comparten solo dos
ficheros. A-2 pide compararlos AL BYTE y decir cual manda. Si se contradicen,
el NO-GO del brief se dispara.

Se amplia a los dos arboles de src/ y de data/, porque el hallazgo 16 del
segundo agente de N4 fue precisamente que "byte a byte identicas" era falso
como estaba escrito: los ficheros comunes si son identicos, los CONJUNTOS no.

Uso (desde la raiz del repo):  python3 -I fix-fase2/fase0_n6/a2_dos_arboles.py
"""
import hashlib
import json
import os


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def comparar(dir_a, dir_b, etiqueta):
    a = set(os.listdir(dir_a)) if os.path.isdir(dir_a) else set()
    b = set(os.listdir(dir_b)) if os.path.isdir(dir_b) else set()
    comunes = sorted(a & b)
    print(f"--- {etiqueta} ---")
    print(f"  {dir_a:<22} {len(a)} ficheros")
    print(f"  {dir_b:<22} {len(b)} ficheros")
    print(f"  comunes: {len(comunes)} | solo en {dir_a}: {len(a - b)} | "
          f"solo en {dir_b}: {len(b - a)}")
    difieren = []
    for n in comunes:
        pa, pb = os.path.join(dir_a, n), os.path.join(dir_b, n)
        if os.path.isdir(pa) or os.path.isdir(pb):
            continue
        ha, hb = sha(pa), sha(pb)
        estado = "IDENTICO" if ha == hb else "DIFIEREN"
        if ha != hb:
            difieren.append(n)
        print(f"    {n:<48} {estado}  {ha[:16]}")
    if a - b:
        print(f"  solo en {dir_a}:")
        for n in sorted(a - b):
            print(f"    + {n}")
    if b - a:
        print(f"  solo en {dir_b}:")
        for n in sorted(b - a):
            print(f"    + {n}")
    print()
    return difieren


def main():
    print("=== A-2 — los dos arboles del repo ===\n")
    dif_res = comparar("results", "fix-fase2/results", "RESULTS")
    dif_src = comparar("src", "fix-fase2/src", "SRC")
    dif_data = comparar("data", "fix-fase2/data", "DATA")

    print("=== A-2 veredicto ===")
    todos = dif_res + dif_src + dif_data
    if todos:
        print(f"  CONTRADICCION: {len(todos)} fichero(s) con el mismo nombre y")
        print(f"  contenido distinto -> {todos}")
        print("  -> NO-GO del brief DISPARADO")
    else:
        print("  Ningun fichero con el mismo nombre difiere en contenido.")
        print("  Los arboles NO se contradicen: se SOLAPAN parcialmente.")
        print("  -> NO-GO del brief NO se dispara.")
    print()
    print("  Cual manda, para cada fichero no comun: el unico que existe.")
    print("  Para los comunes: da igual, son el mismo byte a byte.")

    # Comprobacion extra: el contenido del JSON comun, no solo el byte
    for n in ("rigor_estadistico.json",):
        pa, pb = f"results/{n}", f"fix-fase2/results/{n}"
        if os.path.exists(pa) and os.path.exists(pb):
            ja = json.load(open(pa))
            jb = json.load(open(pb))
            print(f"\n  json.load igualdad semantica de {n}: {ja == jb}")


if __name__ == "__main__":
    main()
