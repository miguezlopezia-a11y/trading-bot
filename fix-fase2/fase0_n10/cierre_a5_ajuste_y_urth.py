#!/usr/bin/env python3
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
TICKERS=["^GSPC","^STOXX50E","^IBEX","EEM","^TNX","IEF","TLT","GC=F","CL=F","HG=F","DBC","EURUSD=X","JPY=X","^VIX","BTC-EUR","ETH-EUR","VNQ","URTH"]
ETFS={"EEM","IEF","TLT","DBC","VNQ","URTH"}


def get(ticker,period2,events=False):
    url=("https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(ticker,safe="")
         +f"?period1=0&period2={period2}&interval=1d"+("&events=div%2Csplits" if events else ""))
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=45) as response:
        body=response.read(); status=response.status
    data=json.loads(body); result=data.get("chart",{}).get("result")
    if not result or not result[0].get("timestamp"): raise RuntimeError(f"{ticker}: sin velas")
    return {"url":url,"http":status,"bytes":len(body),"data":result[0]}


def cagr(first,last,first_date,last_date):
    years=(last_date-first_date).days/365.2425
    return years,(last/first)**(1/years)-1

print(f"User-Agent={UA}")
period2=int(time.time())
pre=get("^GSPC",period2)
print(f"PREVIO http={pre['http']} bytes={pre['bytes']} cuerpo_util=True")
if pre["http"]!=200: raise SystemExit("No se ejecuta la tanda")
filas=[]; detalle_urth=None
for ticker in TICKERS:
    r=get(ticker,period2,ticker in ETFS); d=r["data"]
    stamps=d["timestamp"]; fechas=[datetime.fromtimestamp(t,timezone.utc).date() for t in stamps]
    quote=d.get("indicators",{}).get("quote",[{}])[0]
    close=quote.get("close",[]); adjlist=d.get("indicators",{}).get("adjclose",[])
    adj=adjlist[0].get("adjclose",[]) if adjlist else []
    pares=[(c,a) for c,a in zip(close,adj) if c is not None and a is not None]
    diffs=sum(not math.isclose(c,a,rel_tol=1e-12,abs_tol=1e-12) for c,a in pares)
    eventos=d.get("events",{})
    dividends=eventos.get("dividends",{}); splits=eventos.get("splits",{})
    fila={"ticker":ticker,"http":r["http"],"bytes":r["bytes"],"n_velas":len(stamps),
          "adjclose_existe":bool(adjlist),"n_adjclose":len(adj),"n_pares_validos":len(pares),
          "n_diferencias_close_adjclose":diffs,"n_dividendos":len(dividends),"n_splits":len(splits),
          "url":r["url"]}
    if ticker=="URTH":
        validos=[(f,c,a) for f,c,a in zip(fechas,close,adj) if c is not None and a is not None]
        f0,c0,a0=validos[0]; f1,c1,a1=validos[-1]
        anos_close,ret_close=cagr(c0,c1,f0,f1); anos_adj,ret_adj=cagr(a0,a1,f0,f1)
        fila.update({"primera":f0.isoformat(),"ultima":f1.isoformat(),"close_inicial":c0,
                     "close_final":c1,"adjclose_inicial":a0,"adjclose_final":a1,
                     "anos_close":anos_close,"cagr_close":ret_close,"anos_adjclose":anos_adj,
                     "cagr_adjclose":ret_adj})
        detalle_urth=fila
    filas.append(fila)
    print(f"{ticker} http={r['http']} velas={len(stamps)} adjclose={bool(adjlist)} pares={len(pares)} diffs={diffs} dividendos={len(dividends)} splits={len(splits)}")
    time.sleep(0.25)

print("=== URTH, crecimiento anual compuesto sobre la historia disponible ===")
print(f"ventana={detalle_urth['primera']} -> {detalle_urth['ultima']} anos={detalle_urth['anos_adjclose']:.6f}")
print(f"close {detalle_urth['close_inicial']:.6f} -> {detalle_urth['close_final']:.6f}; CAGR={100*detalle_urth['cagr_close']:.6f} %")
print(f"adjclose {detalle_urth['adjclose_inicial']:.6f} -> {detalle_urth['adjclose_final']:.6f}; CAGR={100*detalle_urth['cagr_adjclose']:.6f} %")
print(f"diferencia_adjclose_menos_close={100*(detalle_urth['cagr_adjclose']-detalle_urth['cagr_close']):.6f} pp")
salida={"fecha_utc":datetime.now(timezone.utc).isoformat(),"period2_epoch":period2,
        "user_agent":UA,"previo_http":pre["http"],"series":filas,"urth":detalle_urth,
        "nota":"CAGR histórico de URTH en USD; no es retorno esperado ni conversión a euros."}
out=ROOT/"fix-fase2/fase0_n10/salida_cierre_a5_ajuste_y_urth.json"
out.write_text(json.dumps(salida,ensure_ascii=False,indent=2)+"\n")
print(f"salida={out.relative_to(ROOT)}")
