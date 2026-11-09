python3 -I - <<'PY'
import json, time, urllib.error, urllib.request
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
ahora = int(time.time())
pruebas = [
    ("range=max&interval=1d", "range=max&interval=1d"),
    ("range=10y&interval=1d", "range=10y&interval=1d"),
    (f"period1=0&period2={ahora}&interval=1d", f"period1=0&period2={ahora}&interval=1d"),
]
for etiqueta, params in pruebas:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
            ts = d["chart"]["result"][0]["timestamp"]
            print(f"  {etiqueta:44} http=200  velas={len(ts):6}  "
                  f"{time.strftime('%Y-%m-%d', time.gmtime(ts[0]))} -> "
                  f"{time.strftime('%Y-%m-%d', time.gmtime(ts[-1]))}")
    except urllib.error.HTTPError as e:
        print(f"  {etiqueta:44} HTTP {e.code} {e.reason}")
    time.sleep(3)
PY
