"""N9 A-4/A-5 cerrado + insumo de B-c: extrae las comisiones VIP 0 de Bybit y los
minimos de orden de los cuerpos congelados, y calcula el retorno sobre capital y
los euros al ano con los regimenes de funding medidos en A-2.
ORDEN DE MAGNITUD DE UN SOLO SIMBOLO. No es la 4.2, que no se ejecuta.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a7_cuenta_minima.py
"""
import hashlib
import json
import re
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a7_cuenta_minima.json"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
BYBIT_FEES = "fase0_n9/fuentes_a4/bybit_help_fee.raw"
BYBIT_INSTR = "fase0_n9/fuentes_a4/bybit_api_instruments_linear.raw"
A2 = "fase0_n9/salida_a2_fecha_y_conteo_exacto.json"
ECB = ("https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV"
       "?lastNObservations=1&format=csvdata")
MARGENES = [0.05, 0.10, 0.20, 0.50]
CAPITALES = [1000, 10000, 100000]


def destag(html):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?is)</t[dh]>", " | ", t)
    t = re.sub(r"(?is)</tr>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    return re.sub(r"[ \t]{2,}", " ", t)


def main():
    res = {"credenciales_enviadas": [],
           "aviso": "orden de magnitud, un solo simbolo (BTCUSDT). No es la 4.2."}

    print("=== A-4 cerrado — Bybit VIP 0, extraido del cuerpo congelado ===")
    bruto = open(BYBIT_FEES, "rb").read()
    print(f"fuente  = {BYBIT_FEES}")
    print(f"sha256 del fichero = {hashlib.sha256(bruto).hexdigest()}")
    plano = destag(bruto.decode("utf-8", "replace"))
    m = re.search(r"VIP 0 \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \| ([\d.]+)% \|", plano)
    if not m:
        raise SystemExit("no se encontro la fila VIP 0: A-4 NO verificable en fuente")
    spot_taker, spot_maker, perp_taker, perp_maker = (float(x) / 100 for x in m.groups())
    print(f"fila literal: {m.group(0)}")
    print(f"spot  VIP0  taker={spot_taker:.6f}  maker={spot_maker:.6f}")
    print(f"perp  VIP0  taker={perp_taker:.6f}  maker={perp_maker:.6f}")
    print(f"la pata spot cuesta lo mismo maker o taker: {spot_maker == spot_taker}")
    res["a4_bybit_vip0"] = {"fuente": BYBIT_FEES, "fila": m.group(0),
                            "spot_taker": spot_taker, "spot_maker": spot_maker,
                            "perp_taker": perp_taker, "perp_maker": perp_maker,
                            "spot_maker_igual_taker": spot_maker == spot_taker}

    ida_taker = spot_taker + perp_taker
    ida_maker = spot_maker + perp_maker
    rt_taker, rt_maker = 2 * ida_taker, 2 * ida_maker
    print(f"\nida+vuelta taker/taker = {100 * rt_taker:.3f} % del nocional")
    print(f"ida+vuelta mejor caso   = {100 * rt_maker:.3f} % del nocional "
          f"(maker en perp; el spot no mejora)")
    res["a4_ida_y_vuelta"] = {"rt_taker_pct": 100 * rt_taker, "rt_maker_pct": 100 * rt_maker}

    print("\n=== A-5 cerrado — minimos de orden de la pata corta (Bybit BTCUSDT) ===")
    instr = json.load(open(BYBIT_INSTR))
    it = instr["result"]["list"][0]
    print(f"symbol={it['symbol']} launchTime={it['launchTime']}")
    print(f"lotSizeFilter = {json.dumps(it['lotSizeFilter'])}")
    print(f"leverageFilter = {json.dumps(it['leverageFilter'])}")
    res["a5_minimos_bybit"] = {"symbol": it["symbol"],
                               "lotSizeFilter": it["lotSizeFilter"],
                               "leverageFilter": it["leverageFilter"]}

    print("\n=== referencia sin riesgo: tipo de la facilidad de depositos del BCE ===")
    dfr = None
    try:
        req = urllib.request.Request(ECB, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            csv = r.read().decode()
        print(f"url  = {ECB}")
        print(f"http={r.status}")
        print(csv[:600])
        filas = [x for x in csv.strip().split("\n") if x]
        cab = filas[0].split(",")
        val = filas[-1].split(",")
        d = dict(zip(cab, val))
        dfr = float(d["OBS_VALUE"]) / 100
        print(f"DFR leido = {d.get('TIME_PERIOD')} -> {100 * dfr:.3f} % anual")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}  -> DFR queda [no verificado]")
    res["referencia_bce"] = {"url": ECB, "dfr_anual": dfr,
                             "estado": "verificado" if dfr is not None else "no verificado"}

    print("\n=== insumo de B-c — retorno sobre capital con los regimenes medidos en A-2 ===")
    a2 = json.load(open(A2))
    tarifa = a2["a2_3_tarifa_bruta"]
    regimenes = {"media 7,15 anos": tarifa["bruto_anual_pct_media"],
                 "mediana 7,15 anos": tarifa["bruto_anual_pct_mediana"]}
    for a, v in tarifa["por_ano"].items():
        regimenes[f"ano {a}"] = v["bruto_anual_pct"]

    print(f"{'regimen':<20} {'bruto %':>8} {'neto rt-maker %':>16} "
          + " ".join(f"m={m:<5}" for m in MARGENES))
    tabla = {}
    for nombre, bruto_pct in regimenes.items():
        neto = bruto_pct - 100 * rt_maker
        fila = {"bruto_anual_pct": bruto_pct, "neto_nocional_pct": neto,
                "sobre_capital_pct": {}}
        celdas = []
        for mg in MARGENES:
            roc = neto / (1 + mg)
            fila["sobre_capital_pct"][str(mg)] = roc
            celdas.append(f"{roc:>7.2f}")
        tabla[nombre] = fila
        print(f"{nombre:<20} {bruto_pct:>8.3f} {neto:>16.3f} " + " ".join(celdas))
    res["bc_retorno_sobre_capital"] = {"margenes": MARGENES, "tabla": tabla,
                                       "coste_rt_pct": 100 * rt_maker}

    print("\n=== euros al ano, margen m=0.10, neto de comisiones (orden de magnitud) ===")
    print(f"{'capital':>10} " + " ".join(f"{k:>18}" for k in
                                         ("media 7,15 anos", "ano 2026")))
    euros = {}
    for cap in CAPITALES:
        fila = {}
        celdas = []
        for k in ("media 7,15 anos", "ano 2026"):
            roc = tabla[k]["sobre_capital_pct"]["0.1"] / 100
            fila[k] = cap * roc
            celdas.append(f"{cap * roc:>18.0f}")
        euros[str(cap)] = fila
        print(f"{cap:>10} " + " ".join(celdas))
    if dfr is not None:
        print(f"\ncomparacion: el DFR del BCE paga {100 * dfr:.3f} % -> "
              f"{CAPITALES[0] * dfr:.0f} / {CAPITALES[1] * dfr:.0f} / "
              f"{CAPITALES[2] * dfr:.0f} EUR al ano, sin riesgo de contraparte cripto")
    res["bc_euros_ano"] = {"margen": 0.10, "por_capital": euros,
                           "dfr_anual": dfr,
                           "dfr_euros": None if dfr is None else
                                        {str(c): c * dfr for c in CAPITALES}}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
