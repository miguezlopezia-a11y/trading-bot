#!/usr/bin/env bash
# N9 A-3: busca trabajo de funding ya hecho en las ramas y en el VPS.
# Uso desde fix-fase2/: bash fase0_n9/a3_trabajo_previo_funding.sh
set -u
cd "$(dirname "$0")/.."
RAIZ="$(cd .. && pwd)"
OUT="fase0_n9/salida_a3_trabajo_previo_funding.txt"

{
echo "=== A-3 — trabajo de funding ya hecho? ==="
echo "cwd     = $(pwd)"
echo "raiz    = ${RAIZ}"
echo "fecha   = $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

echo "--- A-3.1  git grep -il funding en las ramas remotas ---"
cd "${RAIZ}"
for b in main fase-b-recuperada feat/estrategias-candidatas \
         nube/n4-procedencia-v-t-n nube/n5-reconocimiento-datos \
         nube/n6-holdout-y-recuento nube/n7-benchmark-exposicion \
         nube/s1-auditoria-harness nube/s2-literatura nube/s3-datos; do
  archivos="$(git grep -il funding "origin/${b}" -- 2>/dev/null | sed "s|^origin/${b}:||")"
  n=0
  [ -n "${archivos}" ] && n="$(printf '%s\n' "${archivos}" | wc -l)"
  echo "origin/${b} : ${n} archivos con 'funding'"
  if [ "${n}" -gt 0 ]; then
    printf '%s\n' "${archivos}" | sed 's/^/      /'
  fi
done

echo
echo "--- A-3.2  codigo o datos de funding (no solo la palabra) en las ramas ---"
for b in main fase-b-recuperada feat/estrategias-candidatas \
         nube/n4-procedencia-v-t-n nube/n5-reconocimiento-datos \
         nube/n6-holdout-y-recuento nube/n7-benchmark-exposicion \
         nube/s1-auditoria-harness nube/s2-literatura nube/s3-datos; do
  rutas="$(git ls-tree -r --name-only "origin/${b}" 2>/dev/null \
           | grep -iE 'funding|carry|basis|perp' || true)"
  n=0
  [ -n "${rutas}" ] && n="$(printf '%s\n' "${rutas}" | wc -l)"
  echo "origin/${b} : ${n} rutas cuyo NOMBRE contiene funding/carry/basis/perp"
  if [ "${n}" -gt 0 ]; then
    printf '%s\n' "${rutas}" | sed 's/^/      /'
  fi
done

echo
echo "--- A-3.3  grep -rl -i funding en /opt/trading-bot (produccion, solo lectura) ---"
grep -rl -i funding /opt/trading-bot 2>/dev/null | head -40
echo "coincidencias: $(grep -rl -i funding /opt/trading-bot 2>/dev/null | wc -l)"

echo
echo "--- A-3.4  grep -rl -i funding en /root/trading-bot-fix-fase2 (solo lectura) ---"
grep -rl -i funding /root/trading-bot-fix-fase2 2>/dev/null | head -40
echo "coincidencias: $(grep -rl -i funding /root/trading-bot-fix-fase2 2>/dev/null | wc -l)"

echo
echo "--- A-3.5  datos de funding ya descargados en el VPS ---"
ls -la /root/trading-bot-n9/fix-fase2/data/ 2>/dev/null | head -20
echo "data/funding/ existe? $([ -d /root/trading-bot-n9/fix-fase2/data/funding ] && echo SI || echo NO)"
find /root /opt -maxdepth 6 -iname '*funding*' 2>/dev/null | grep -v '/root/trading-bot-n9/fix-fase2/fase0_n9' | head -20
echo "ficheros con 'funding' en el nombre bajo /root y /opt (excluyendo fase0_n9): $(find /root /opt -maxdepth 6 -iname '*funding*' 2>/dev/null | grep -vc '/root/trading-bot-n9/fix-fase2/fase0_n9')"

echo
echo "--- A-3.6  donde vive sharpe_min_dsr (lo citan N5 y el brief) ---"
git grep -n 'def sharpe_min_dsr' origin/fase-b-recuperada -- 2>/dev/null || echo "no esta en fase-b-recuperada"
git grep -ln 'sharpe_min_dsr' origin/fase-b-recuperada -- 2>/dev/null | head -20
} > "${RAIZ}/fix-fase2/${OUT}" 2>&1

cat "${RAIZ}/fix-fase2/${OUT}"
echo
echo "-> fix-fase2/${OUT}"
