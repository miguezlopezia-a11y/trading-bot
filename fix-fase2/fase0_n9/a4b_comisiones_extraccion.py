"""N9 A-4 (segunda pasada): extraccion estructurada de las comisiones desde los
cuerpos congelados de A-4, mas sondeo de fuentes adicionales para la pata perp.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a4b_comisiones_extraccion.py
"""
import hashlib
import json
import os
import re
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a4b_comisiones_extraccion.json"
CRUDO = "fase0_n9/fuentes_a4b"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")

EXTRA = [
    ("okx_help_trading_fees", "https://www.okx.com/help/trading-fees"),
    ("okx_help_fee_schedule", "https://www.okx.com/help/fees-okx-trading-fees"),
    ("okx_priapi_trade_fee", "https://www.okx.com/priapi/v5/public/trade-fee?t=0"),
    ("bybit_web_fee_schedule", "https://www.bybit.com/en/fee-schedule/"),
    ("binance_bapi_vip_fee",
     "https://www.binance.com/bapi/accounts/v1/public/account/vip/fee/rate"),
    ("binance_bapi_trade_fee",
     "https://www.binance.com/bapi/composite/v1/public/future/common/trade-fee"),
    ("binance_fapi_commission_publico",
     "https://fapi.binance.com/fapi/v1/commissionRate?symbol=BTCUSDT"),
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


def okx_regular_user(texto):
    filas = []
    for m in re.finditer(r'\{[^{}]*"levelName":"Regular user"[^{}]*\}', texto):
        try:
            o = json.loads(m.group(0))
        except Exception:
            continue
        filas.append({k: o.get(k) for k in
                      ("levelName", "level", "tradeType", "assetType",
                       "makerFee", "takerFee", "standardMakerFee", "standardTakerFee")})
    tabs = []
    for m in re.finditer(r'\{"feeClazz":\d+,"instType":\d+[^{}]*"tabName":"[^"]*"\}', texto):
        try:
            tabs.append(json.loads(m.group(0)))
        except Exception:
            pass
    return filas, tabs


def destag(html):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?is)</t[dh]>", " | ", t)
    t = re.sub(r"(?is)</tr>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    t = t.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#39;", "'")
    t = re.sub(r"[ \t]{2,}", " ", t)
    return re.sub(r"\n{2,}", "\n", t)


def main():
    os.makedirs(CRUDO, exist_ok=True)
    res = {"credenciales_enviadas": [], "okx_fees_pagina": {}, "bybit_help": {},
           "sondeo_extra": {}}

    ruta_okx = "fase0_n9/fuentes_a4/okx_web_fees.raw"
    texto = open(ruta_okx, encoding="utf-8", errors="replace").read()
    filas, tabs = okx_regular_user(texto)
    print("=== A-4b.1 — OKX /fees, filas 'Regular user' extraidas del cuerpo congelado ===")
    print(f"fuente = {ruta_okx}  sha256 = "
          f"{hashlib.sha256(open(ruta_okx,'rb').read()).hexdigest()[:16]}...")
    print(f"pestanas declaradas en el cuerpo: {tabs}")
    print(f"filas 'Regular user' halladas: {len(filas)}")
    for f in filas:
        print(f"  tradeType={f['tradeType']} assetType={f['assetType']} "
              f"maker={f['makerFee']} taker={f['takerFee']} "
              f"(std {f['standardMakerFee']}/{f['standardTakerFee']})")
    res["okx_fees_pagina"] = {"fuente": ruta_okx, "tabs": tabs, "regular_user": filas}

    ruta_by = "fase0_n9/fuentes_a4/bybit_help_fee.raw"
    html = open(ruta_by, encoding="utf-8", errors="replace").read()
    plano = destag(html)
    idx = [m.start() for m in re.finditer(r"(?i)taker fee rate", plano)]
    print("\n=== A-4b.2 — Bybit help-center, tablas destagueadas del cuerpo congelado ===")
    print(f"fuente = {ruta_by}  sha256 = "
          f"{hashlib.sha256(open(ruta_by,'rb').read()).hexdigest()[:16]}...")
    print(f"apariciones de 'Taker Fee Rate': {len(idx)}")
    trozos = []
    for i, p in enumerate(idx[:4]):
        t = plano[max(0, p - 500):p + 1400]
        trozos.append(t)
        print(f"\n--- bloque {i + 1} ---")
        print(t)
    res["bybit_help"] = {"fuente": ruta_by, "apariciones": len(idx), "bloques": trozos}

    print("\n=== A-4b.3 — sondeo de fuentes adicionales ===")
    for nombre, url in EXTRA:
        http, body = get(url)
        sha = hashlib.sha256(body).hexdigest()
        with open(f"{CRUDO}/{nombre}.raw", "wb") as f:
            f.write(body[:400000])
        t = body.decode("utf-8", "replace")
        print(f"\n--- {nombre} ---")
        print(f"url  = {url}")
        print(f"http={http} bytes={len(body)} sha256={sha[:16]}...")
        print(f"primeros 240 car.: {t[:240]!r}")
        res["sondeo_extra"][nombre] = {"url": url, "http": http, "bytes": len(body),
                                       "sha256": sha, "cabeza": t[:400]}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
