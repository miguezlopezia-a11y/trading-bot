"""N9 A-5: margen inicial y de mantenimiento de la pata corta del perpetuo, y
si el spot comprado sirve de colateral. Fuentes publicas del exchange, sin clave.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a5_margen.py
"""
import hashlib
import json
import os
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a5_margen.json"
CRUDO = "fase0_n9/fuentes_a5"
TOPE_FICHERO = 2000000
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")

FUENTES = [
    ("okx_position_tiers_cross",
     "https://www.okx.com/api/v5/public/position-tiers?instType=SWAP&tdMode=cross"
     "&instFamily=BTC-USDT"),
    ("okx_position_tiers_isolated",
     "https://www.okx.com/api/v5/public/position-tiers?instType=SWAP&tdMode=isolated"
     "&instFamily=BTC-USDT"),
    ("bybit_risk_limit_linear",
     "https://api.bybit.com/v5/market/risk-limit?category=linear&symbol=BTCUSDT"),
    ("binance_bapi_brackets",
     "https://www.binance.com/bapi/futures/v1/friendly/future/common/brackets"),
    ("binance_web_leverage_margin",
     "https://www.binance.com/en/futures/trading-rules/perpetual/leverage-margin"),
    ("okx_instruments_swap_btc_usdt",
     "https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP"),
    ("binance_exchangeinfo_btcusdt_filtros",
     "https://fapi.binance.com/fapi/v1/exchangeInfo?symbol=BTCUSDT"),
    ("okx_discount_rate_colateral",
     "https://www.okx.com/api/v5/public/discount-rate-interest-free-quota?ccy=BTC"),
]


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, f"{type(e).__name__}: {e}".encode()


def main():
    os.makedirs(CRUDO, exist_ok=True)
    res = {"credenciales_enviadas": [], "fuentes": {}}
    for nombre, url in FUENTES:
        http, body = get(url)
        sha = hashlib.sha256(body).hexdigest()
        guardado = body[:TOPE_FICHERO]
        sha_fichero = hashlib.sha256(guardado).hexdigest()
        truncado = len(guardado) < len(body)
        ruta = f"{CRUDO}/{nombre}.raw"
        with open(ruta, "wb") as f:
            f.write(guardado)
        texto = body.decode("utf-8", "replace")
        print(f"\n=== {nombre} ===")
        print(f"url    = {url}")
        print(f"http={http} bytes={len(body)} sha256_cuerpo={sha[:16]}... "
              f"sha256_fichero={sha_fichero[:16]}... truncado={truncado} -> {ruta}")
        extracto = None
        if texto.lstrip().startswith("{") or texto.lstrip().startswith("["):
            print(texto[:2500])
            extracto = texto[:4000]
        else:
            print(f"(no-JSON) primeros 300 car.: {texto[:300]!r}")
        res["fuentes"][nombre] = {"url": url, "http": http, "bytes": len(body),
                                  "sha256_cuerpo": sha, "sha256_fichero": sha_fichero,
                                  "truncado": truncado, "raw": ruta, "extracto": extracto}

    f_okx = res["fuentes"]["okx_position_tiers_cross"]
    if f_okx["http"] == 200:
        d = json.loads(f_okx["extracto"] if False else open(
            f"{CRUDO}/okx_position_tiers_cross.raw").read())
        if d.get("code") == "0":
            print("\n--- OKX BTC-USDT-SWAP, tramos de riesgo (cross) ---")
            print(f"{'tier':>4} {'maxSz':>14} {'imr':>8} {'mmr':>8} {'maxLever':>9}")
            tramos = []
            for t in d["data"]:
                print(f"{t['tier']:>4} {t['maxSz']:>14} {t['imr']:>8} {t['mmr']:>8} "
                      f"{t['maxLever']:>9}")
                tramos.append({k: t[k] for k in
                               ("tier", "minSz", "maxSz", "imr", "mmr", "maxLever")})
            res["okx_tramos_cross"] = tramos
            t1 = d["data"][0]
            imr = float(t1["imr"])
            print(f"\ntramo 1: imr={imr} -> apalancamiento maximo efectivo = {1 / imr:.1f}x ; "
                  f"mmr={t1['mmr']}")
            res["okx_tramo1"] = {"imr": imr, "mmr": float(t1["mmr"]),
                                 "apalancamiento_max": 1 / imr}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
