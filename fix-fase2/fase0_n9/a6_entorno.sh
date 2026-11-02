#!/usr/bin/env bash
# N9 A-1 (bloque 2.5): el entorno del VPS.
# Uso desde fix-fase2/: bash fase0_n9/a6_entorno.sh
set -u
cd "$(dirname "$0")/.."
OUT="fase0_n9/salida_a6_entorno.txt"
{
echo "=== 2.5 — entorno del VPS ==="
echo "cwd    = $(pwd)"
echo "host   = $(hostname)"
echo "fecha  = $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "--- git / curl / jq / python3 ---"
git --version
command -v curl
command -v jq
command -v python3 && python3 --version
echo
echo "--- interprete con numpy y pandas ---"
/opt/trading-bot/venv/bin/python -c "import sys,numpy,pandas;print('python',sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__)"
echo
echo "--- /root/trading-bot-fix-fase2/.git ---"
if [ -e /root/trading-bot-fix-fase2/.git ]; then echo "EXISTE (el brief dice que no)"; else echo "no existe -> sin git, CONFIRMADO"; fi
echo
echo "--- df -h / ---"
df -h /
echo
echo "--- el clon de trabajo ---"
cd /root/trading-bot-n9
echo "rama   = $(git rev-parse --abbrev-ref HEAD)"
echo "base   = $(git merge-base HEAD origin/fase-b-recuperada)"
echo "HEAD   = $(git rev-parse --short HEAD)"
echo "limpio = $([ -z "$(git status --porcelain --untracked-files=no)" ] && echo SI || echo NO)"
echo
echo "--- produccion viva en /opt/trading-bot (solo lectura) ---"
ls -d /opt/trading-bot >/dev/null 2>&1 && echo "/opt/trading-bot presente" || echo "/opt/trading-bot ausente"
pgrep -af 'trading-bot|paper' | head -5 || echo "(sin procesos coincidentes)"
} > "/root/trading-bot-n9/fix-fase2/${OUT}" 2>&1
cat "/root/trading-bot-n9/fix-fase2/${OUT}"
echo
echo "-> fix-fase2/${OUT}"
