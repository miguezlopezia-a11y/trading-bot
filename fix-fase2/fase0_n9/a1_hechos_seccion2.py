"""N9 A-1: reverifica 2.1, 2.3, 2.4 y 2.6 del brief. Cero credenciales.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a1_hechos_seccion2.py
"""
import json
import time
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a1_hechos_seccion2.json"
UA = "n9-fase0/1.0 (publico, sin credenciales)"

ENDPOINTS = {
    "binance": "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=3",
    "bybit": "https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&limit=3",
    "okx": "https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USD-SWAP&limit=3",
}
PREMIUM_INDEX = "https://fapi.binance.com/fapi/v1/premiumIndex"
PAGINACION = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1000"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return {"http": r.status, "bytes": len(body), "ms": int(1000 * (time.time() - t0)),
                    "body": body.decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        body = e.read()
        return {"http": e.code, "bytes": len(body), "ms": int(1000 * (time.time() - t0)),
                "body": body.decode("utf-8", "replace")}
    except Exception as e:
        return {"http": None, "bytes": 0, "ms": int(1000 * (time.time() - t0)),
                "body": "", "error": f"{type(e).__name__}: {e}"}


def main():
    res = {"endpoints_2_1": {}, "headers_enviados": {"User-Agent": UA},
           "credenciales_enviadas": []}

    print("=== 2.1 — las tres APIs de funding, sin credenciales ===")
    for nombre, url in ENDPOINTS.items():
        r = get(url)
        res["endpoints_2_1"][nombre] = {"url": url, **r}
        print(f"\n--- {nombre.upper()} ---")
        print(f"url   = {url}")
        print(f"http={r['http']} bytes={r['bytes']} ms={r['ms']}")
        print(r["body"][:900])

    todos_200 = all(v["http"] == 200 for v in res["endpoints_2_1"].values())
    res["veredicto_2_1"] = "CONFIRMADO" if todos_200 else "REFUTADO"
    print(f"\n2.1 -> {res['veredicto_2_1']} (los tres http==200: {todos_200})")

    print("\n=== 2.3 — tamano del universo de perpetuos (premiumIndex) ===")
    r = get(PREMIUM_INDEX)
    n_perp = None
    simbolos = []
    if r["http"] == 200:
        d = json.loads(r["body"])
        n_perp = len(d)
        simbolos = sorted(x["symbol"] for x in d)
    print(f"url   = {PREMIUM_INDEX}")
    print(f"http={r['http']} bytes={r['bytes']} -> len = {n_perp}")
    print(f"brief dice 945 ; medido = {n_perp} ; diferencia = "
          f"{None if n_perp is None else n_perp - 945}")
    res["universo_2_3"] = {"url": PREMIUM_INDEX, "http": r["http"], "n_medido": n_perp,
                           "n_brief": 945,
                           "diferencia": None if n_perp is None else n_perp - 945,
                           "primeros_10": simbolos[:10], "ultimos_10": simbolos[-10:]}

    print("\n=== 2.4 — limite real de paginacion (se pide 1000) ===")
    r = get(PAGINACION)
    n_filas = None
    if r["http"] == 200:
        n_filas = len(json.loads(r["body"]))
    print(f"url   = {PAGINACION}")
    print(f"http={r['http']} bytes={r['bytes']} -> filas devueltas = {n_filas}")
    res["paginacion_2_4"] = {"url": PAGINACION, "http": r["http"], "pedido": 1000,
                             "devuelto": n_filas, "brief_dice": 500}

    print("\n=== 2.6 — regimen actual del funding (orden de magnitud, NO media historica) ===")
    tasas = {}
    b = res["endpoints_2_1"]["binance"]
    if b["http"] == 200:
        tasas["binance_btcusdt"] = [float(x["fundingRate"]) for x in json.loads(b["body"])]
    by = res["endpoints_2_1"]["bybit"]
    if by["http"] == 200:
        tasas["bybit_btcusdt"] = [float(x["fundingRate"])
                                  for x in json.loads(by["body"])["result"]["list"]]
    ok = res["endpoints_2_1"]["okx"]
    if ok["http"] == 200:
        tasas["okx_btc_usd_swap"] = [float(x["realizedRate"])
                                     for x in json.loads(ok["body"])["data"]]
    for k, v in tasas.items():
        print(f"{k:<22} {v}  -> anualizado x3x365: "
              f"{[round(100 * x * 3 * 365, 2) for x in v]} %")
    res["regimen_2_6"] = {"tasas_8h": tasas,
                          "nota": "regimen actual, no media historica; no es entrada de nada"}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
