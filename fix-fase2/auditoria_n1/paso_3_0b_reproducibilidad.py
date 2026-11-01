"""Paso 3.0b — ¿es este código el que generó los resultados publicados?

CONDICION DE PARADA de la auditoria N1 (OK de Pablo, §8; objecion B-10).
Si las cifras reejecutadas no reproducen results/rigor_estadistico.json, la
auditoria para aqui: auditar un harness que no es el que genero el expediente
no dice nada sobre el expediente.

Que hace, en este orden:
  1. Reejecuta src/rigor_estadistico.py DOS veces en un directorio aislado
     (no toca fix-fase2/results/). Compara pasada 1 vs pasada 2: aisla el
     no-determinismo propio del harness en ESTE entorno (objecion B-13).
  2. Compara la pasada 1 contra el JSON publicado, campo a campo, y clasifica
     cada diferencia en: identico / no_determinismo / deriva_o_defecto.
  3. Veredicto REPRODUCE / NO REPRODUCE y codigo de salida (0 / 1).

No descarga nada: rigor_estadistico.py lee data/btc_usd_5y_1d.csv del disco.
Determinista: el harness fija SEED=42 y usa np.random.default_rng.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_0b_reproducibilidad.py
"""
import json
import os
import shutil
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
PUBLICADO = os.path.join(FIX2, "results", "rigor_estadistico.json")
# tolerancia de impresion: el harness redondea a 3-4 decimales al serializar
TOL = 1e-9


def preparar(sandbox):
    """Directorio de trabajo aislado: src y data por symlink (solo lectura
    efectiva), results propio. Asi ninguna reejecucion toca la evidencia."""
    if os.path.exists(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(os.path.join(sandbox, "results"))
    for sub in ("src", "data"):
        os.symlink(os.path.join(FIX2, sub), os.path.join(sandbox, sub))


def ejecutar(sandbox, etiqueta):
    t0 = time.time()
    p = subprocess.run([sys.executable, "src/rigor_estadistico.py"],
                       cwd=sandbox, capture_output=True, text=True,
                       timeout=1200)
    dur = time.time() - t0
    print(f"--- pasada {etiqueta}: rc={p.returncode}  {dur:.1f}s")
    for linea in p.stdout.strip().splitlines():
        print("    " + linea)
    if p.returncode != 0:
        print("    STDERR:")
        for linea in p.stderr.strip().splitlines()[-15:]:
            print("    " + linea)
        raise SystemExit(f"la pasada {etiqueta} fallo (rc={p.returncode})")
    destino = os.path.join(sandbox, "results", "rigor_estadistico.json")
    with open(destino) as f:
        return json.load(f)


def aplanar(d, prefijo=""):
    """{'variantes.ma_cross.dsr': 0.49, ...} — listas por indice."""
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(aplanar(v, f"{prefijo}.{k}" if prefijo else str(k)))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(aplanar(v, f"{prefijo}[{i}]"))
    else:
        out[prefijo] = d
    return out


def comparar(a, b, nombre_a, nombre_b):
    """Devuelve (iguales, lista de diferencias, n_campos)."""
    fa, fb = aplanar(a), aplanar(b)
    claves = sorted(set(fa) | set(fb))
    difs = []
    for k in claves:
        if k not in fa:
            difs.append((k, f"ausente en {nombre_a}", fb[k]))
            continue
        if k not in fb:
            difs.append((k, fa[k], f"ausente en {nombre_b}"))
            continue
        va, vb = fa[k], fb[k]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) \
                and not isinstance(va, bool) and not isinstance(vb, bool):
            if abs(float(va) - float(vb)) > TOL:
                difs.append((k, va, vb))
        elif va != vb:
            difs.append((k, va, vb))
    return len(difs) == 0, difs, len(claves)


def informe_difs(difs, nombre_a, nombre_b, limite=40):
    print(f"    {len(difs)} campo(s) distintos:")
    for k, va, vb in difs[:limite]:
        print(f"      {k}\n        {nombre_a}: {va}\n        {nombre_b}: {vb}")
    if len(difs) > limite:
        print(f"      … y {len(difs) - limite} mas")


def main():
    print("=" * 74)
    print("PASO 3.0b — reproducibilidad de Fase A (condicion de parada)")
    print("=" * 74)
    print(f"python {sys.version.split()[0]}")
    import numpy, pandas
    print(f"numpy {numpy.__version__}  pandas {pandas.__version__}")
    print(f"publicado: {PUBLICADO}")
    if not os.path.exists(PUBLICADO):
        raise SystemExit("NO LO SE: el JSON publicado no existe")
    with open(PUBLICADO) as f:
        pub = json.load(f)
    print()

    sandbox = os.path.join(FIX2, "auditoria_n1", "_sandbox_3_0b")
    preparar(sandbox)
    r1 = ejecutar(sandbox, "1")
    print()
    preparar(sandbox)
    r2 = ejecutar(sandbox, "2")
    print()

    print("-" * 74)
    print("1) DETERMINISMO EN ESTE ENTORNO  (pasada 1 vs pasada 2)")
    det_ok, det_difs, n = comparar(r1, r2, "pasada1", "pasada2")
    if det_ok:
        print(f"    IDENTICAS en los {n} campos comparados -> el harness es "
              "determinista aqui.")
    else:
        informe_difs(det_difs, "pasada1", "pasada2")
        print("    -> hay no-determinismo PROPIO: cualquier diferencia contra "
              "el publicado no se puede atribuir al codigo.")
    print()

    print("-" * 74)
    print("2) CODIGO vs RESULTADOS PUBLICADOS  (pasada 1 vs JSON del repo)")
    rep_ok, rep_difs, n2 = comparar(r1, pub, "reejecutado", "publicado")
    if rep_ok:
        print(f"    IDENTICOS en los {n2} campos comparados.")
    else:
        informe_difs(rep_difs, "reejecutado", "publicado")
    print()

    print("=" * 74)
    if rep_ok and det_ok:
        print("VEREDICTO: REPRODUCE")
        print("El codigo de este repo genera exactamente el JSON publicado de")
        print("Fase A, y lo hace de forma determinista. El vinculo")
        print("codigo<->resultados queda establecido para Fase A. La auditoria")
        print("puede continuar con 3.1.")
        print("Limite declarado: esto NO establece el vinculo para Fase B ni")
        print("para TimesFM, cuyos resultados no se regeneran con este script.")
        shutil.rmtree(sandbox, ignore_errors=True)
        return 0
    print("VEREDICTO: NO REPRODUCE")
    if not det_ok:
        print("Causa candidata: no-determinismo propio en este entorno.")
    print("CONDICION DE PARADA ACTIVADA (OK de Pablo, §8): la auditoria para")
    print("aqui. No se ejecuta 3.1 ni los pasos siguientes.")
    print(f"Sandbox conservado para inspeccion: {sandbox}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
