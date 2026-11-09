#!/usr/bin/env python3
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as response:
        body = response.read()
        status = response.status
    data = json.loads(body)
    result = data.get("chart", {}).get("result")
    useful = bool(result and result[0].get("timestamp"))
    if not useful:
        raise RuntimeError(f"Respuesta sin velas: {body[:300]!r}")
    result = result[0]
    ts = result["timestamp"]
    return {
        "url": url,
        "http": status,
        "bytes": len(body),
        "cuerpo_util": useful,
        "n_velas": len(ts),
        "primera": datetime.fromtimestamp(ts[0], timezone.utc).date().isoformat(),
        "ultima": datetime.fromtimestamp(ts[-1], timezone.utc).date().isoformat(),
        "granularidad_meta": result.get("meta", {}).get("dataGranularity"),
        "error_chart": data.get("chart", {}).get("error"),
    }


print(f"User-Agent={UA}")
pre = get(f"{BASE}?range=1d&interval=1d")
print(f"PREVIO http={pre['http']} bytes={pre['bytes']} cuerpo_util={pre['cuerpo_util']}")
if pre["http"] != 200:
    raise SystemExit("No se ejecuta la tanda")
period2 = int(time.time())
consultas = [
    ("range_max_1d", f"{BASE}?range=max&interval=1d"),
    ("range_10y_1d", f"{BASE}?range=10y&interval=1d"),
    ("periodos_1d", f"{BASE}?period1=0&period2={period2}&interval=1d"),
]
salida = {
    "fecha_utc": datetime.now(timezone.utc).isoformat(),
    "user_agent": UA,
    "previo": pre,
    "period2_epoch": period2,
    "resultados": [],
}
for nombre, url in consultas:
    r = get(url)
    r["nombre"] = nombre
    salida["resultados"].append(r)
    print(f"{nombre} http={r['http']} bytes={r['bytes']} velas={r['n_velas']} {r['primera']} -> {r['ultima']} granularidad={r['granularidad_meta']}")
    time.sleep(0.5)
salida["no_go_fuente_disparado"] = any(r["http"] != 200 or not r["cuerpo_util"] for r in salida["resultados"])
out = ROOT / "fix-fase2/fase0_n10/salida_cierre_a2_granularidad.json"
out.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n")
print(f"period2={period2}")
print(f"NO-GO fuente: {'SE DISPARA' if salida['no_go_fuente_disparado'] else 'NO SE DISPARA'}")
print(f"salida={out.relative_to(ROOT)}")
