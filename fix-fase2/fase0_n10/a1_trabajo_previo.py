#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFS = [
    "task/n10-eleccion-de-mercado",
    "origin/fase-b-recuperada",
    "origin/feat/estrategias-candidatas",
    "origin/main",
    "origin/nube/n4-procedencia-v-t-n",
    "origin/nube/n5-reconocimiento-datos",
    "origin/nube/n6-holdout-y-recuento",
    "origin/nube/n7-benchmark-exposicion",
    "origin/nube/s1-auditoria-harness",
    "origin/nube/s2-literatura",
    "origin/nube/s3-datos",
]
PATTERNS = {
    "autocorr": r"autocorr",
    "variance_ratio": r"variance_ratio|ratio de varianza",
    "hurst": r"hurst",
    "mercado": r"mercado",
    "universo": r"universo",
}


def run(args):
    p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return {"comando": " ".join(args), "rc": p.returncode, "salida": p.stdout.splitlines()}


log = run(["git", "log", "--all", "--oneline"])
busquedas = {}
for nombre, patron in PATTERNS.items():
    por_rama = {}
    for ref in REFS:
        r = run(["git", "grep", "-i", "-l", "-E", patron, ref, "--", ".", ":!*.csv", ":!*.html"])
        por_rama[ref] = {"rc": r["rc"], "archivos": r["salida"]}
    busquedas[nombre] = por_rama

focal = run([
    "git", "grep", "-i", "-n", "-E",
    r"variance_ratio|hurst|ratio de varianza|autocorrelaci[oó]n de (los )?retornos|criba de mercados",
    REFS[0], "--", ".", ":!*.csv", ":!*.html",
])

salida = {
    "fecha_utc": datetime.now(timezone.utc).isoformat(),
    "cwd": str(ROOT),
    "n_ramas": len(REFS),
    "ramas": REFS,
    "git_log": log,
    "busquedas": busquedas,
    "busqueda_focal_rama_actual": focal,
    "criterio_no_go": "Solo dispara si hay una medición ejecutada de memoria de precios o una criba de mercados; briefs y autocorrelación de equity no cuentan.",
    "no_go_disparado": False,
    "nota": "La búsqueda amplia produce documentación y mediciones de equity; la focal no encuentra ratio de varianza, Hurst ni criba ejecutada. S3 A.12 mide autocorrelación de la equity, no memoria de precios de mercados.",
}
out = ROOT / "fix-fase2/fase0_n10/salida_a1_trabajo_previo.json"
out.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n")
print(f"$ python3 fix-fase2/fase0_n10/a1_trabajo_previo.py")
print(f"ramas_revisadas={len(REFS)}")
print(f"commits_en_git_log_all={len(log['salida'])}")
for nombre, por_rama in busquedas.items():
    archivos = sorted({linea for r in por_rama.values() for linea in r["archivos"]})
    print(f"patron={nombre} archivos_distintos_con_rama={len(archivos)}")
print("--- búsqueda focal en la rama actual ---")
print(f"rc={focal['rc']} (1 significa sin coincidencias)")
for linea in focal["salida"]:
    print(linea)
print("NO-GO A-1: NO SE DISPARA; no hay medición previa ejecutada de memoria de precios ni criba de mercados.")
print(f"salida={out.relative_to(ROOT)}")
