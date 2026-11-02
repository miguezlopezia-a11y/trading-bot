"""N9 Paso B (B-a, B-d) y Paso C (C-1), con lo medible sin bajar historico.
B-a: funding contra liquidez en el corte transversal, anualizando con el intervalo
real de cada simbolo y con mediana y media recortada, no solo media.
B-d: composicion y edad del universo, y los topes de funding.
C-1: base anualizada de los futuros con vencimiento real, hoy, contra el DFR del BCE.
Cuatro cross-sections de un instante. Sin descarga de historico: no es la 4.1.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/b1_transversal_y_basis.py
"""
import datetime as dt
import json
import urllib.error
import urllib.request

import numpy as np

OUT = "fase0_n9/salida_b1_transversal_y_basis.json"
UA = "n9-fase0/1.0 (publico, sin credenciales)"
URLS = {
    "premium": "https://fapi.binance.com/fapi/v1/premiumIndex",
    "ticker": "https://fapi.binance.com/fapi/v1/ticker/24hr",
    "exinfo": "https://fapi.binance.com/fapi/v1/exchangeInfo",
    "fundinfo": "https://fapi.binance.com/fapi/v1/fundingInfo",
}
DFR_PCT = 2.500
COSTE_RT_PCT = 0.240
HORIZONTE_DIAS = 400


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, json.loads(r.read().decode())


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def recortada(x, pct=10):
    if len(x) < 5:
        return float(np.mean(x))
    lo, hi = np.percentile(x, [pct, 100 - pct])
    s = x[(x >= lo) & (x <= hi)]
    return float(np.mean(s)) if len(s) else float(np.mean(x))


def main():
    res = {"credenciales_enviadas": [],
           "instante_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "urls": URLS}
    datos = {}
    for k, u in URLS.items():
        http, d = get(u)
        datos[k] = d
        print(f"{k:<10} http={http} len={len(d) if isinstance(d, list) else 'obj'}  {u}")

    simbolos_ex = {s["symbol"]: s for s in datos["exinfo"]["symbols"]}
    prem = {p["symbol"]: p for p in datos["premium"]}
    tick = {t["symbol"]: t for t in datos["ticker"]}
    fi = {x["symbol"]: x for x in datos["fundinfo"]}

    print("\n=== 2.3 corregido — que son exactamente los 945 de premiumIndex ===")
    print(f"premiumIndex devuelve                  = {len(datos['premium'])} instrumentos")
    tipos = {}
    for s in prem:
        t = simbolos_ex.get(s, {}).get("contractType", "(no esta en exchangeInfo)")
        tipos[t] = tipos.get(t, 0) + 1
    print(f"por contractType de exchangeInfo       = {tipos}")
    perp = {s: v for s, v in simbolos_ex.items()
            if v["contractType"] == "PERPETUAL" and v["status"] == "TRADING"}
    print(f"PERPETUAL con status TRADING           = {len(perp)}")
    print(f"ticker/24hr devuelve                   = {len(datos['ticker'])}")
    res["c2_3_corregido"] = {"premium_index": len(datos["premium"]),
                             "por_contract_type": tipos,
                             "perpetual_trading": len(perp),
                             "ticker_24hr": len(datos["ticker"])}

    intervalo = {s: int(fi.get(s, {}).get("fundingIntervalHours") or 8) for s in prem}
    print("\n=== B-a — funding contra liquidez, corte transversal de un instante ===")
    print("anualizacion por simbolo: tasa x (24/intervalo_h) x 365, no x3x365")
    cand = [s for s in prem if s in tick and s in perp
            and float(tick[s]["quoteVolume"]) > 0]
    f_an = np.array([100 * float(prem[s]["lastFundingRate"])
                     * (24 / intervalo[s]) * 365 for s in cand])
    vol = np.array([float(tick[s]["quoteVolume"]) for s in cand])
    print(f"perpetuos TRADING con funding y volumen = {len(cand)}")
    print(f"pearson(funding anual, log10 volumen)   = "
          f"{float(np.corrcoef(f_an, np.log10(vol))[0, 1]):+.4f}")
    print(f"spearman(funding anual, volumen)        = {spearman(f_an, vol):+.4f}")
    orden = np.argsort(-vol)
    print(f"\n{'bloque':<10} {'media %':>10} {'mediana %':>10} {'recort10 %':>11} "
          f"| {'resto media':>11} {'resto mediana':>14} {'resto recort10':>15}")
    bloques = {}
    for n in (10, 20, 50, 100):
        top, resto = orden[:n], orden[n:]
        a, b = f_an[top], f_an[resto]
        print(f"top-{n:<6} {a.mean():>10.3f} {np.median(a):>10.3f} {recortada(a):>11.3f} "
              f"| {b.mean():>11.3f} {np.median(b):>14.3f} {recortada(b):>15.3f}")
        bloques[f"top{n}"] = {
            "n": n, "top_media_pct": float(a.mean()), "top_mediana_pct": float(np.median(a)),
            "top_recortada10_pct": recortada(a), "resto_media_pct": float(b.mean()),
            "resto_mediana_pct": float(np.median(b)), "resto_recortada10_pct": recortada(b),
            "dif_mediana_pp": float(np.median(a) - np.median(b)),
            "simbolos_top": [cand[i] for i in top[:20]]}
    print("\ndiferencia top-resto en MEDIANA (pp anuales), que es la robusta:")
    for k, v in bloques.items():
        print(f"  {k:<8} {v['dif_mediana_pp']:+.3f} pp")
    peor = int(np.argmin(f_an))
    mejor = int(np.argmax(f_an))
    print(f"\nextremos que descolocan la media: {cand[peor]} {f_an[peor]:+.1f} %/ano "
          f"(intervalo {intervalo[cand[peor]]} h) ; {cand[mejor]} {f_an[mejor]:+.1f} %/ano "
          f"(intervalo {intervalo[cand[mejor]]} h)")
    res["b_a"] = {"n_simbolos": len(cand),
                  "pearson_funding_logvol": float(np.corrcoef(f_an, np.log10(vol))[0, 1]),
                  "spearman_funding_vol": spearman(f_an, vol), "bloques": bloques,
                  "extremo_min": {"symbol": cand[peor], "anual_pct": float(f_an[peor])},
                  "extremo_max": {"symbol": cand[mejor], "anual_pct": float(f_an[mejor])},
                  "aviso": "un solo corte transversal; no es una estimacion temporal"}

    print("\n=== B-d — edad del universo de perpetuos vivos ===")
    edades, nombres = {}, {}
    for corte in ("2020-01-01", "2021-01-01", "2022-01-01", "2023-01-01",
                  "2024-01-01", "2025-01-01", "2026-01-01"):
        ms = int(dt.datetime.fromisoformat(corte + "T00:00:00+00:00").timestamp() * 1000)
        viejos = sorted(s for s, v in perp.items() if v["onboardDate"] < ms)
        edades[corte] = len(viejos)
        nombres[corte] = viejos[:25]
        print(f"  vivos hoy que ya existian antes de {corte}: {len(viejos):>4} de "
              f"{len(perp)} ({100 * len(viejos) / len(perp):>5.1f} %)")
    print(f"\n  los 3 anteriores a 2020-01-01: {nombres['2020-01-01']}")
    print(f"  los anteriores a 2021-01-01 (primeros 25): {nombres['2021-01-01']}")
    print("\n  CONSECUENCIA PARA LA CRIBA DE LA 4.1: el criterio que el brief sugiere")
    print("  ('los 20 de mayor volumen con historia completa desde 2019-09-10') tiene")
    print(f"  un universo elegible de {edades['2020-01-01']} simbolos, no de 20.")
    res["b_d"] = {"n_perpetuos_trading": len(perp), "vivos_antes_de": edades,
                  "nombres": nombres,
                  "limitacion": "exchangeInfo solo lista los vivos; el sesgo de "
                                "supervivencia no es acotable con esta fuente"}

    print("\n=== B-b — los topes de funding estan puestos por regla, no por el mercado ===")
    intervalos_c, topes_c = {}, {}
    for s, x in fi.items():
        intervalos_c[x.get("fundingIntervalHours")] = intervalos_c.get(
            x.get("fundingIntervalHours"), 0) + 1
        topes_c[x.get("adjustedFundingRateCap")] = topes_c.get(
            x.get("adjustedFundingRateCap"), 0) + 1
    print(f"entradas en fundingInfo = {len(fi)}")
    print(f"intervalos (h -> n)     = {dict(sorted(intervalos_c.items(), key=lambda t: -t[1]))}")
    print(f"topes (tope -> n), top6 = {dict(sorted(topes_c.items(), key=lambda t: -t[1])[:6])}")
    print(f"BTCUSDT                 = {json.dumps(fi.get('BTCUSDT'))}")
    print("el minimo y el maximo de 8 h observados en A-2 fueron -0.003 y +0.003:")
    print("coinciden con el tope de regla, asi que la cola de la TARIFA esta acotada")
    res["topes"] = {"n_en_fundinginfo": len(fi), "intervalos_horas": intervalos_c,
                    "topes": topes_c, "btcusdt": fi.get("BTCUSDT")}

    print("\n=== C-1 — base anualizada de los futuros con vencimiento REAL, hoy ===")
    ahora = dt.datetime.now(dt.timezone.utc)
    filas, descartados = [], {}
    for sym, s in simbolos_ex.items():
        ct = s["contractType"]
        if ct == "PERPETUAL" or s["status"] != "TRADING" or sym not in prem:
            continue
        venc = dt.datetime.fromtimestamp(s["deliveryDate"] / 1000, dt.timezone.utc)
        dias = (venc - ahora).total_seconds() / 86400
        if dias <= 1 or dias > HORIZONTE_DIAS:
            descartados[ct] = descartados.get(ct, 0) + 1
            continue
        mark = float(prem[sym]["markPrice"] or 0)
        idx = float(prem[sym]["indexPrice"] or 0)
        if not mark or not idx:
            continue
        base = mark / idx - 1
        filas.append({"symbol": sym, "pair": s["pair"], "contractType": ct,
                      "vencimiento": venc.date().isoformat(), "dias": round(dias, 2),
                      "markPrice": mark, "indexPrice": idx, "base_pct": 100 * base,
                      "base_anualizada_pct": 100 * base * 365 / dias})
    filas.sort(key=lambda r: -r["base_anualizada_pct"])
    print(f"descartados por vencimiento > {HORIZONTE_DIAS} dias (perpetuos de acciones")
    print(f"tokenizadas con deliveryDate en 2100): {descartados}")
    print(f"contratos con vencimiento real: {len(filas)}")
    print("el coste no es una ida y vuelta al ano: hay que renovar cada vencimiento,")
    print(f"asi que son 365/dias rolls al ano a {COSTE_RT_PCT} pp cada uno")
    print(f"\n{'symbol':<20} {'venc':>11} {'dias':>7} {'mark':>12} {'index':>12} "
          f"{'base %':>8} {'anual %':>9} {'rolls/ano':>10} {'coste/ano':>10} "
          f"{'neto %':>8} {'vs DFR':>8}")
    for r in filas:
        rolls = 365 / r["dias"]
        coste = COSTE_RT_PCT * rolls
        neto = r["base_anualizada_pct"] - coste
        r.update({"rolls_ano": rolls, "coste_anual_pct": coste, "neto_pct": neto,
                  "vs_dfr_pp": neto - DFR_PCT})
        print(f"{r['symbol']:<20} {r['vencimiento']:>11} {r['dias']:>7.2f} "
              f"{r['markPrice']:>12.2f} {r['indexPrice']:>12.2f} "
              f"{r['base_pct']:>8.3f} {r['base_anualizada_pct']:>9.3f} "
              f"{rolls:>10.2f} {coste:>10.3f} {neto:>8.3f} {r['vs_dfr_pp']:>+8.3f}")
    res["c_1_basis"] = {"dfr_anual_pct": DFR_PCT, "coste_rt_pct": COSTE_RT_PCT,
                        "horizonte_dias": HORIZONTE_DIAS,
                        "descartados_por_vencimiento_ficticio": descartados,
                        "contratos": filas}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
