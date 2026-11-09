python3 -I - <<'PY'
import time, urllib.error, urllib.request
URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=0&period2=1762387200&interval=1d"
UA_CORTO = "Mozilla/5.0"
UA_KIMI = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
UA_MIO = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
casos = [
    ("python  UA corto", {"User-Agent": UA_CORTO}),
    ("python  UA de Kimi", {"User-Agent": UA_KIMI}),
    ("python  UA mio", {"User-Agent": UA_MIO}),
    ("python  UA de Kimi + Accept", {"User-Agent": UA_KIMI, "Accept": "*/*",
                                     "Accept-Language": "en-US,en;q=0.9"}),
    ("python  sin User-Agent", {}),
]
for etiqueta, cab in casos:
    req = urllib.request.Request(URL, headers=cab)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  {etiqueta:30} http={r.status} bytes={len(r.read())}")
    except urllib.error.HTTPError as e:
        print(f"  {etiqueta:30} HTTP {e.code} {e.reason}")
    time.sleep(4)
PY

printf '=== y curl con el UA exacto de Kimi ===\n'
curl -s -o /dev/null -w '  curl    UA de Kimi                     http=%{http_code} bytes=%{size_download}\n' \
  --max-time 25 -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36' \
  "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=0&period2=1762387200&interval=1d"
