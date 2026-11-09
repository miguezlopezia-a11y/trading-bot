#!/usr/bin/env python3
import csv
import io
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
YAHOO="https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=1d"
ECB="https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?lastNObservations=1&format=csvdata"
SG_BASE="https://wholesale.banking.societegenerale.com/fileadmin/indices_feeds/ti_screen/"


def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=45) as response:
        body=response.read(); status=response.status
    return {"url":url,"http":status,"bytes":len(body),"body":body}

pre=get(YAHOO)
json.loads(pre["body"])
print(f"PREVIO_YAHOO http={pre['http']} bytes={pre['bytes']} cuerpo_util=True")
if pre["http"]!=200: raise SystemExit("No se ejecuta la tanda")

ecb=get(ECB)
texto=ecb["body"].decode("utf-8-sig")
rows=list(csv.DictReader(io.StringIO(texto)))
row=rows[-1]
dfr={"fecha":row["TIME_PERIOD"],"valor_pct":float(row["OBS_VALUE"])}
serie=next(iter(row.values()))
print(f"BCE http={ecb['http']} bytes={ecb['bytes']} serie={serie} fecha={dfr['fecha']} DFR={dfr['valor_pct']:.3f} %")

maxdate=get(SG_BASE+"data/0.max_trade_date.txt")
fecha=maxdate["body"].decode().strip()
stats=get(SG_BASE+f"data/2stats/2.{fecha}.stats.csv")
stats_text=stats["body"].decode()
print(f"SG_MAX_DATE http={maxdate['http']} fecha={fecha}")
print(f"SG_STATS http={stats['http']} bytes={stats['bytes']}")
print(stats_text,end="")

salida={
    "fecha_utc":datetime.now(timezone.utc).isoformat(),"user_agent":UA,
    "previo_yahoo":{"http":pre["http"],"bytes":pre["bytes"]},
    "bce":{"url":ECB,"http":ecb["http"],"bytes":ecb["bytes"],**dfr},
    "sg_trend_indicator":{"pagina":SG_BASE+"index.html","fecha":fecha,
        "stats_url":stats["url"],"http":stats["http"],"csv":stats_text,
        "advertencia":"Es SG Trend Indicator, no el Sharpe del SG CTA Index desde 2000."},
    "sg_cta_0_56_verificado_en_fuente_primaria":False,
    "dato_publico_mas_cercano":{"valor":0.61,"desde":"2000-01","fecha_documento":"2022-05-26",
        "fuente":"CFM, A good time for trend following... but, then again, it's always been!, figura 2; fuente de datos Bloomberg",
        "url":"https://www.cfm.com/wp-content/uploads/2022/12/39-A-Good-Time-for-Trend-Following-FINAL.pdf",
        "tipo":"secundario, no SG oficial"},
}
out=ROOT/"fix-fase2/fase0_n10/salida_cierre_a6_dfr_sg.json"
out.write_text(json.dumps(salida,ensure_ascii=False,indent=2)+"\n")
print("SG_CTA_0.56=[no verificado]; dato público más cercano=0.61 desde enero de 2000 (CFM 2022, secundario).")
print(f"salida={out.relative_to(ROOT)}")
