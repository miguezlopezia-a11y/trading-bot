#!/usr/bin/env python3
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
TICKERS = [
    "^GSPC", "^STOXX50E", "^IBEX", "EEM", "^TNX", "IEF", "TLT", "GC=F",
    "CL=F", "HG=F", "DBC", "EURUSD=X", "JPY=X", "^VIX", "BTC-EUR",
    "ETH-EUR", "VNQ", "URTH",
]
US_REFERENCE = {"EEM", "^TNX", "IEF", "TLT", "GC=F", "CL=F", "HG=F", "DBC", "^VIX", "VNQ", "URTH"}
EUROPE = {"^STOXX50E", "^IBEX"}
FX = {"EURUSD=X", "JPY=X"}
CRYPTO = {"BTC-EUR", "ETH-EUR"}


def easter(y):
    a=y%19; b=y//100; c=y%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7
    m=(a+11*h+22*l)//451; month=(h+l-7*m+114)//31; day=(h+l-7*m+114)%31+1
    return date(y,month,day)


def observed(y, month, day):
    d=date(y,month,day)
    if d.weekday()==5: return d-timedelta(days=1)
    if d.weekday()==6: return d+timedelta(days=1)
    return d


def nth_weekday(y, month, weekday, n):
    d=date(y,month,1)
    return d+timedelta(days=(weekday-d.weekday())%7+7*(n-1))


def last_weekday(y, month, weekday):
    d=date(y,month+1,1)-timedelta(days=1) if month<12 else date(y,12,31)
    return d-timedelta(days=(d.weekday()-weekday)%7)


def us_holidays(y):
    washington=nth_weekday(y,2,0,3) if y>=1971 else observed(y,2,22)
    h={observed(y,1,1), washington, easter(y)-timedelta(days=2),
       last_weekday(y,5,0), observed(y,7,4), nth_weekday(y,9,0,1),
       nth_weekday(y,11,3,4), observed(y,12,25)}
    if y>=1998: h.add(nth_weekday(y,1,0,3))
    if y>=2022: h.add(observed(y,6,19))
    return h


SPECIAL_US_CLOSURES = {
    date(1972,11,7), date(1972,12,28), date(1973,1,25), date(1976,11,2),
    date(1977,7,14), date(1980,11,4), date(1985,9,27),
    date(1994,4,27), date(2001,9,11), date(2001,9,12), date(2001,9,13),
    date(2001,9,14), date(2004,6,11), date(2007,1,2), date(2012,10,29),
    date(2012,10,30), date(2018,12,5), date(2025,1,9),
}


def europe_holidays(y, ibex):
    e=easter(y)
    h={date(y,1,1), e-timedelta(days=2), e+timedelta(days=1), date(y,5,1),
       date(y,12,24), date(y,12,25), date(y,12,26), date(y,12,31)}
    if not ibex:
        h.update({date(y,1,2), e+timedelta(days=39), e+timedelta(days=50), date(y,8,1)})
    return h


def get(ticker, period2, extra=""):
    url=("https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(ticker, safe="")
         +f"?period1=0&period2={period2}&interval=1d"+extra)
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=45) as response:
        body=response.read(); status=response.status
    data=json.loads(body); result=data.get("chart",{}).get("result")
    if not result or not result[0].get("timestamp"):
        raise RuntimeError(f"{ticker}: respuesta sin velas")
    r=result[0]; stamps=r["timestamp"]
    fechas=[datetime.fromtimestamp(t,timezone.utc).date() for t in stamps]
    closes=r.get("indicators",{}).get("quote",[{}])[0].get("close",[])
    nulos=[f.isoformat() for f,c in zip(fechas,closes) if c is None]
    return {"ticker":ticker,"url":url,"http":status,"bytes":len(body),"fechas":fechas,
            "moneda":r.get("meta",{}).get("currency"),"nulos":nulos,
            "granularidad":r.get("meta",{}).get("dataGranularity")}


def weekdays_between(first,last):
    d=first; out=[]
    while d<=last:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out


print(f"User-Agent={UA}")
period2=int(time.time())
pre=get("^GSPC",period2)
print(f"PREVIO ^GSPC http={pre['http']} bytes={pre['bytes']} velas={len(pre['fechas'])}")
if pre['http']!=200: raise SystemExit("No se ejecuta la tanda")
series={}
for ticker in TICKERS:
    r=get(ticker,period2); series[ticker]=r
    print(f"DESCARGA {ticker} http={r['http']} bytes={r['bytes']} velas={len(r['fechas'])}")
    time.sleep(0.35)

gspc_dates=set(series["^GSPC"]["fechas"])
resultado=[]
for ticker,r in series.items():
    fechas=r["fechas"]; conjunto=set(fechas); first,last=fechas[0],fechas[-1]
    duplicados=len(fechas)-len(conjunto)
    if ticker in CRYPTO:
        esperadas=[first+timedelta(days=i) for i in range((last-first).days+1)]
        metodo="diario_natural_cripto"
    elif ticker in US_REFERENCE:
        esperadas=sorted(d for d in gspc_dates if first<=d<=last)
        metodo="fechas_de_GSPC_como_calendario_de_mercado"
    elif ticker=="^GSPC":
        esperadas=[d for d in weekdays_between(first,last)
                   if d not in us_holidays(d.year) and d not in SPECIAL_US_CLOSURES]
        metodo="NYSE_laborables_menos_festivos_y_cierres_extraordinarios"
    elif ticker in EUROPE:
        esperadas=[d for d in weekdays_between(first,last) if d not in europe_holidays(d.year,ticker=="^IBEX")]
        metodo="laborables_menos_festivos_BME" if ticker=="^IBEX" else "laborables_menos_festivos_Xetra"
    elif ticker in FX:
        esperadas=[d for d in weekdays_between(first,last) if (d.month,d.day) not in {(1,1),(12,25)}]
        metodo="FX_laborables_menos_1_enero_y_25_diciembre"
    huecos=sorted(d for d in esperadas if d not in conjunto)
    fila={"ticker":ticker,"http":r["http"],"bytes":r["bytes"],"n_velas":len(fechas),
          "primera":first.isoformat(),"ultima":last.isoformat(),"moneda":r["moneda"],
          "granularidad":r["granularidad"],"duplicados":duplicados,"cierres_nulos":r["nulos"],
          "metodo_calendario":metodo,"n_huecos":len(huecos),
          "huecos":[d.isoformat() for d in huecos]}
    resultado.append(fila)
    print(f"RESULTADO {ticker} velas={len(fechas)} {first} -> {last} moneda={r['moneda']} huecos={len(huecos)} nulos={len(r['nulos'])} duplicados={duplicados}")
    if huecos: print("  PRIMERAS_FECHAS "+",".join(fila["huecos"][:20])+(" ..." if len(huecos)>20 else ""))

salida={"fecha_utc":datetime.now(timezone.utc).isoformat(),"period2_epoch":period2,
        "user_agent":UA,"previo_http":pre["http"],"series":resultado,
        "nota":"Calendarios reconstruidos; los activos US no-GSPC se comparan con las fechas efectivamente observadas de GSPC."}
out=ROOT/"fix-fase2/fase0_n10/salida_cierre_a3_series_y_huecos.json"
out.write_text(json.dumps(salida,ensure_ascii=False,indent=2)+"\n")
print(f"salida={out.relative_to(ROOT)}")
