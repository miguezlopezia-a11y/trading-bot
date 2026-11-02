"""N9 B-d: comprueba si el historico de funding sobrevive al delistado, que es lo
que decide si el sesgo de supervivencia es acotable o no. Pocas peticiones, sin
descarga de historico.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/b2_supervivencia_acotable.py
"""
import datetime as dt
import json
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_b2_supervivencia_acotable.json"
UA = "n9-fase0/1.0 (publico, sin credenciales)"
EXINFO = "https://fapi.binance.com/fapi/v1/exchangeInfo"
FUNDINFO = "https://fapi.binance.com/fapi/v1/fundingInfo"
PREMIUM = "https://fapi.binance.com/fapi/v1/premiumIndex"
FR = "https://fapi.binance.com/fapi/v1/fundingRate?symbol={}&limit=3"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    res = {"credenciales_enviadas": []}
    _, ex = get(EXINFO)
    _, fun = get(FUNDINFO)
    _, pre = get(PREMIUM)
    ex = json.loads(ex)
    fun = json.loads(fun)
    pre = json.loads(pre)

    en_ex = {s["symbol"] for s in ex["symbols"]}
    estados = {}
    for s in ex["symbols"]:
        estados[s["status"]] = estados.get(s["status"], 0) + 1
    en_fun = {x["symbol"] for x in fun}
    en_pre = {p["symbol"] for p in pre}

    print("=== B-d.1 — quien aparece en que endpoint ===")
    print(f"exchangeInfo  = {len(en_ex)} simbolos ; estados = {estados}")
    print(f"fundingInfo   = {len(en_fun)}")
    print(f"premiumIndex  = {len(en_pre)}")
    solo_fun = sorted(en_fun - en_ex)
    solo_pre = sorted(en_pre - en_ex)
    print(f"en fundingInfo y NO en exchangeInfo  = {len(solo_fun)} -> {solo_fun[:20]}")
    print(f"en premiumIndex y NO en exchangeInfo = {len(solo_pre)} -> {solo_pre[:20]}")
    res["cobertura"] = {"exchange_info": len(en_ex), "estados": estados,
                        "funding_info": len(en_fun), "premium_index": len(en_pre),
                        "solo_funding_info": solo_fun, "solo_premium_index": solo_pre}

    print("\n=== B-d.2 — sobrevive el historico de funding al delistado? ===")
    pruebas = (solo_fun[:3] + solo_pre[:3]) or []
    for s in dict.fromkeys(pruebas):
        http, body = get(FR.format(s))
        try:
            d = json.loads(body)
            n = len(d) if isinstance(d, list) else 0
        except Exception:
            n = 0
        print(f"  {s:<22} http={http} filas={n}  {body[:200]}")
        res.setdefault("pruebas", {})[s] = {"http": http, "filas": n, "cuerpo": body[:400]}
    if not pruebas:
        print("  no hay simbolos fuera de exchangeInfo en estos endpoints: la prueba")
        print("  directa no se puede hacer con estas tres fuentes")

    print("\n=== B-d.3 — un simbolo que ya no cotiza pero esta en exchangeInfo ===")
    no_trading = sorted(s["symbol"] for s in ex["symbols"] if s["status"] != "TRADING")
    print(f"simbolos con status != TRADING: {len(no_trading)} -> {no_trading[:20]}")
    for s in no_trading[:3]:
        http, body = get(FR.format(s))
        try:
            d = json.loads(body)
            n = len(d) if isinstance(d, list) else 0
        except Exception:
            n = 0
        est = next(x["status"] for x in ex["symbols"] if x["symbol"] == s)
        print(f"  {s:<22} status={est:<18} http={http} filas={n}  {body[:160]}")
        res.setdefault("no_trading_probados", {})[s] = {
            "status": est, "http": http, "filas": n, "cuerpo": body[:400]}
    res["no_trading"] = {"n": len(no_trading), "primeros": no_trading[:40]}

    res["instante_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
