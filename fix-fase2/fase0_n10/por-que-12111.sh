printf -- '--- ultimos cierres de URTH, con su variacion ---\n'
python3 -I - <<'PY'
import json, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
req = urllib.request.Request(
    f"https://query1.finance.yahoo.com/v8/finance/chart/URTH?period1=0&period2={int(time.time())}&interval=1d",
    headers=UA)
d = json.load(urllib.request.urlopen(req, timeout=60))["chart"]["result"][0]
ts, aj = d["timestamp"], d["indicators"]["adjclose"][0]["adjclose"]
for i in range(-6, 0):
    var = (aj[i] / aj[i-1] - 1) * 100
    print(f"  {time.strftime('%Y-%m-%d', time.gmtime(ts[i]))}  adjclose={aj[i]:.4f}  var={var:+.2f} %")
anos = (ts[-1] - ts[0]) / 86400 / 365.25
print(f"  CAGR con el ultimo cierre     = {((aj[-1]/aj[0])**(1/anos)-1)*100:.4f} %")
print(f"  CAGR con el penultimo cierre  = {((aj[-2]/aj[0])**(1/((ts[-2]-ts[0])/86400/365.25))-1)*100:.4f} %")
PY

printf -- '--- mis huecos del lunes (VPS) contra su clasificacion de hoy ---\n'
ssh -o BatchMode=yes -o ConnectTimeout=15 bunker "cat /root/.worktrees/trading-bot-n10/fix-fase2/fase0_n10/salida_a2_fuentes_y_universo.json" > /tmp/mio_lunes.json 2>/dev/null
python3 -I - <<'PY'
import json
try:
    mio = json.load(open("/tmp/mio_lunes.json"))
except Exception as e:
    print("  no pude traer mi JSON del lunes:", e)
    raise SystemExit
suyo = json.load(open("/home/pablo/trading-bot-gh/.worktrees/n10/fix-fase2/fase0_n10/salida_cierre_bc_recalculo.json"))
limpias = set(suyo.get("limpias", []))
excl = set(suyo.get("excluidas", []))
print(f"  {'ticker':12} {'mis huecos% (lunes)':>20} {'su veredicto hoy':>18}")
for f in mio.get("a3_universo", []):
    t = f.get("ticker", "?")
    h = f.get("huecos_pct")
    v = "limpia" if t in limpias else ("excluida" if t in excl else "?")
    print(f"  {t:12} {str(h):>20} {v:>18}")
PY
