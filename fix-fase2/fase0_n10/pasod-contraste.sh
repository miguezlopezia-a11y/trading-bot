printf '=== 1. la llamada EXACTA de Kimi, con su UA, ahora ===\n'
python3 -I - <<'PY'
import json, urllib.request, urllib.error
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=max&interval=1d"
req = urllib.request.Request(url, headers={"User-Agent": UA})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
        ts = d["chart"]["result"][0]["timestamp"]
        print("http=200  velas=", len(ts))
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.reason)
PY

printf '=== 2. la vara de medir: URTH close vs adjclose, ahora ===\n'
python3 -I - <<'PY'
import json, time, urllib.request
req = urllib.request.Request(
    f"https://query1.finance.yahoo.com/v8/finance/chart/URTH?period1=0&period2={int(time.time())}&interval=1d",
    headers={"User-Agent": "Mozilla/5.0"})
d = json.load(urllib.request.urlopen(req, timeout=40))["chart"]["result"][0]
ind = d["indicators"]
cl = [x for x in ind["quote"][0]["close"] if x]
aj = [x for x in ind["adjclose"][0]["adjclose"] if x]
anos = (d["timestamp"][-1] - d["timestamp"][0]) / 86400 / 365.25
print(f"  anos={anos:.2f}")
print(f"  close    {((cl[-1]/cl[0])**(1/anos)-1)*100:.3f} %")
print(f"  adjclose {((aj[-1]/aj[0])**(1/anos)-1)*100:.3f} %")
PY

printf '=== 3. de donde sale el 9,43 que usa su Paso C ===\n'
cd /home/pablo/trading-bot-gh/.worktrees/n10
grep -n -E '9,43|9\.43|11,97|11\.97|9,92' fix-fase2/tareas/tarea-vps-N10-eleccion-de-mercado-y-de-instrumento.md | head
