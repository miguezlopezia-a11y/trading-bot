python3 -I - <<'PY'
import datetime as dt, json, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
DIAS = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"]
for sym in ["EURUSD=X", "JPY=X"]:
    req = urllib.request.Request(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=0&period2={int(time.time())}&interval=1d",
        headers=UA)
    d = json.load(urllib.request.urlopen(req, timeout=60))["chart"]["result"][0]
    ts = d["timestamp"]
    print(f"  {sym}: velas={len(ts)}")
    for rango, etiqueta in [((2004, 2006), "2004-2005"), ((2024, 2026), "2024-2025")]:
        cuenta = [0] * 7
        for t in ts:
            f = dt.datetime.fromtimestamp(t, tz=dt.timezone.utc).date()
            if rango[0] <= f.year < rango[1]:
                cuenta[f.weekday()] += 1
        linea = "  ".join(f"{DIAS[i]}={cuenta[i]}" for i in range(7))
        print(f"    {etiqueta}  {linea}")
    time.sleep(3)
PY
