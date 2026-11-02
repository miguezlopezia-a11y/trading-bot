"""N9 A-4: comisiones maker/taker vigentes de perpetuo y de spot, nivel sin
volumen (VIP 0), leidas de fuente del exchange. Guarda cada cuerpo con su sha256.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a4_comisiones.py
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a4_comisiones.json"
CRUDO = "fase0_n9/fuentes_a4"
TOPE_FICHERO = 2000000
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")

FUENTES = [
    ("binance_api_futuros_exchangeinfo",
     "https://fapi.binance.com/fapi/v1/exchangeInfo"),
    ("binance_bapi_fee_futuros",
     "https://www.binance.com/bapi/futures/v1/friendly/future/common/brackets"),
    ("binance_web_fee_futuros",
     "https://www.binance.com/en/fee/futureFee"),
    ("binance_web_fee_spot",
     "https://www.binance.com/en/fee/trading"),
    ("bybit_api_instruments_linear",
     "https://api.bybit.com/v5/market/instruments-info?category=linear&symbol=BTCUSDT"),
    ("bybit_help_fee",
     "https://www.bybit.com/en/help-center/article/Trading-Fee-Structure"),
    ("okx_api_instruments_swap",
     "https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP"),
    ("okx_web_fees",
     "https://www.okx.com/fees"),
    ("okx_priapi_fee_tier",
     "https://www.okx.com/priapi/v5/public/fee-rate-tier?t=0"),
    ("okx_docs_trading_fee",
     "https://www.okx.com/help/okx-trading-fees"),
]

RE_FEE = re.compile(
    r"(?is)(maker|taker)[^0-9%{}\[\]]{0,80}(-?\d{1,2}[.,]\d{1,5}\s?%|0\.000\d{1,3})")


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
        hallados = [(m.group(1).lower(), m.group(2)) for m in RE_FEE.finditer(texto)]
        vistos, unicos = set(), []
        for h in hallados:
            if h not in vistos:
                vistos.add(h)
                unicos.append(h)
        print(f"\n=== {nombre} ===")
        print(f"url    = {url}")
        print(f"http={http} bytes={len(body)} sha256_cuerpo={sha[:16]}... "
              f"sha256_fichero={sha_fichero[:16]}... truncado={truncado} -> {ruta}")
        print(f"pares (maker|taker, cifra) encontrados: {len(unicos)}")
        for k, v in unicos[:25]:
            print(f"    {k:<6} {v}")
        if not unicos:
            print(f"    cuerpo (primeros 300 car.): {texto[:300]!r}")
        res["fuentes"][nombre] = {"url": url, "http": http, "bytes": len(body),
                                  "sha256_cuerpo": sha, "sha256_fichero": sha_fichero,
                                  "truncado": truncado, "raw": ruta,
                                  "pares_maker_taker": unicos[:60]}
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
