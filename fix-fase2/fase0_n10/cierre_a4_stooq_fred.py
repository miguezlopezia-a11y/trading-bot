#!/usr/bin/env python3
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
URLS={
    "previo_yahoo":"https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=1d",
    "stooq_sp500":"https://stooq.com/q/d/l/?s=%5Espx&i=d",
    "fred_dgs10_csv":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",
    "fred_vix_csv":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS",
    "fred_dgs10_api_sin_clave":"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&file_type=json",
}


def get(nombre,url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            body=response.read(); status=response.status
    except urllib.error.HTTPError as e:
        body=e.read(); status=e.code
    except Exception as e:
        return {"nombre":nombre,"url":url,"http":0,"bytes":0,"error":repr(e),"cuerpo_util":False}
    texto=body.decode("utf-8",errors="replace")
    if nombre.startswith("stooq"):
        util=texto.startswith("Date,Open,High,Low,Close")
    elif nombre=="previo_yahoo":
        try: util=bool(json.loads(texto)["chart"]["result"])
        except Exception: util=False
    elif nombre.endswith("csv"):
        util=texto.startswith("observation_date,") or texto.startswith("DATE,")
    else:
        util=False
    return {"nombre":nombre,"url":url,"http":status,"bytes":len(body),
            "inicio_cuerpo":texto[:400],"cuerpo_util":util}

salida={"fecha_utc":datetime.now(timezone.utc).isoformat(),"user_agent":UA,"fuentes":[]}
for nombre,url in URLS.items():
    r=get(nombre,url); salida["fuentes"].append(r)
    print(f"{nombre} http={r['http']} bytes={r['bytes']} cuerpo_util={r['cuerpo_util']}")
    print(f"  inicio={r.get('inicio_cuerpo','')!r}")
    if "error" in r: print(f"  error={r['error']}")
    if nombre=="previo_yahoo" and (r["http"]!=200 or not r["cuerpo_util"]):
        raise SystemExit("Comprobación previa fallida; no se ejecuta el resto de la tanda")
out=ROOT/"fix-fase2/fase0_n10/salida_cierre_a4_stooq_fred.json"
out.write_text(json.dumps(salida,ensure_ascii=False,indent=2)+"\n")
print(f"salida={out.relative_to(ROOT)}")
