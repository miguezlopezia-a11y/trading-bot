"""N9 A-2: fecha exacta del primer funding de BTCUSDT y conteo EXACTO de
liquidaciones disponibles, enumerandolas. Da tambien la media historica, el
porcentaje de periodos negativos y la media por ano, que son el insumo de B-c.
NO es la descarga de la 4.1: un solo simbolo, nada congelado, data/funding/ intacto.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/a2_fecha_y_conteo_exacto.py
"""
import datetime as dt
import json
import statistics
import subprocess
import time
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_a2_fecha_y_conteo_exacto.json"
UA = "n9-fase0/1.0 (publico, sin credenciales)"
BASE = "https://fapi.binance.com/fapi/v1/fundingRate"
SIMBOLO = "BTCUSDT"
T0_BRIEF = 1568102400
INTERVALO_MS = 8 * 3600 * 1000
TOPE_PETICIONES = 60


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


def main():
    res = {"simbolo": SIMBOLO, "endpoint": BASE, "credenciales_enviadas": []}

    print("=== A-2.1 — fecha exacta de fundingTime 1568102400000 ===")
    cmd = ["date", "-u", "-d", f"@{T0_BRIEF}", "+%Y-%m-%d %H:%M:%S %Z"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(f"$ {' '.join(cmd)}")
    print(p.stdout.strip())
    iso = dt.datetime.fromtimestamp(T0_BRIEF, dt.timezone.utc).isoformat()
    print(f"python (UTC) = {iso}")
    print(f"brief dice 2019-09-10 -> coincide: {iso.startswith('2019-09-10')}")
    res["a2_1_fecha"] = {"comando": " ".join(cmd), "salida_date": p.stdout.strip(),
                         "iso_utc": iso, "brief": "2019-09-10",
                         "coincide": iso.startswith("2019-09-10")}

    print("\n=== A-2.2 — enumeracion completa de las liquidaciones de BTCUSDT ===")
    filas = []
    start = 1500000000000
    peticiones = 0
    while peticiones < TOPE_PETICIONES:
        url = f"{BASE}?symbol={SIMBOLO}&startTime={start}&limit=1000"
        http, d = get_json(url)
        peticiones += 1
        if not d:
            break
        filas.extend(d)
        ult = d[-1]["fundingTime"]
        print(f"  peticion {peticiones:>2}  http={http}  filas={len(d):>3}  "
              f"hasta {dt.datetime.fromtimestamp(ult / 1000, dt.timezone.utc).isoformat()}")
        if len(d) < 500:
            break
        start = ult + 1
        time.sleep(0.25)

    vistos = {}
    for f in filas:
        vistos[f["fundingTime"]] = f
    tiempos = sorted(vistos)
    n_exacto = len(tiempos)
    primero, ultimo = tiempos[0], tiempos[-1]
    dias = (ultimo - primero) / 86400000.0
    esperadas_si_8h = int((ultimo - primero) / INTERVALO_MS) + 1
    difs = [tiempos[i + 1] - tiempos[i] for i in range(len(tiempos) - 1)]
    irregulares = sorted({d for d in difs if d != INTERVALO_MS})

    print(f"\n  peticiones usadas       = {peticiones} (tope del script {TOPE_PETICIONES})")
    print(f"  filas crudas            = {len(filas)}  duplicadas = {len(filas) - n_exacto}")
    print(f"  CONTEO EXACTO           = {n_exacto}")
    print(f"  primera                 = "
          f"{dt.datetime.fromtimestamp(primero / 1000, dt.timezone.utc).isoformat()}")
    print(f"  ultima                  = "
          f"{dt.datetime.fromtimestamp(ultimo / 1000, dt.timezone.utc).isoformat()}")
    print(f"  dias cubiertos          = {dias:.2f}  ({dias / 365.25:.3f} anos)")
    print(f"  esperadas si todo 8h    = {esperadas_si_8h}  -> huecos = "
          f"{esperadas_si_8h - n_exacto}")
    print(f"  intervalos != 8h (ms)   = {irregulares[:20]}")
    print(f"  brief estima ~7.830 ; exacto = {n_exacto} ; diferencia = {n_exacto - 7830}")
    print(f"  T_eff de Fase B = 4336 ; ratio = {n_exacto / 4336:.3f}x")

    res["a2_2_conteo"] = {
        "peticiones": peticiones, "filas_crudas": len(filas), "conteo_exacto": n_exacto,
        "primera_ms": primero, "ultima_ms": ultimo,
        "primera_iso": dt.datetime.fromtimestamp(primero / 1000, dt.timezone.utc).isoformat(),
        "ultima_iso": dt.datetime.fromtimestamp(ultimo / 1000, dt.timezone.utc).isoformat(),
        "dias": round(dias, 2), "anos": round(dias / 365.25, 3),
        "esperadas_si_8h": esperadas_si_8h, "huecos": esperadas_si_8h - n_exacto,
        "intervalos_distintos_de_8h_ms": irregulares,
        "brief_estimaba": 7830, "diferencia_con_brief": n_exacto - 7830,
        "t_eff_fase_b": 4336, "ratio": round(n_exacto / 4336, 3)}

    print("\n=== A-2.3 — insumo de B-c: la tarifa medida (bruta, un solo simbolo) ===")
    tasas = [float(vistos[t]["fundingRate"]) for t in tiempos]
    media = statistics.fmean(tasas)
    mediana = statistics.median(tasas)
    neg = sum(1 for x in tasas if x < 0)
    print(f"  media por 8h            = {media:.8f}  -> x3x365 = {100 * media * 3 * 365:.3f} % anual")
    print(f"  mediana por 8h          = {mediana:.8f}  -> x3x365 = {100 * mediana * 3 * 365:.3f} % anual")
    print(f"  periodos negativos      = {neg} / {n_exacto} = {100 * neg / n_exacto:.2f} %")
    print(f"  minimo observado 8h     = {min(tasas):.8f}")
    print(f"  maximo observado 8h     = {max(tasas):.8f}")
    por_ano = {}
    for t in tiempos:
        a = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).year
        por_ano.setdefault(a, []).append(float(vistos[t]["fundingRate"]))
    print("\n  ano   n     media 8h      bruto anual %   % periodos negativos")
    anual = {}
    for a in sorted(por_ano):
        v = por_ano[a]
        m = statistics.fmean(v)
        pn = 100 * sum(1 for x in v if x < 0) / len(v)
        print(f"  {a}  {len(v):>4}  {m: .8f}   {100 * m * 3 * 365:>8.3f}        {pn:>6.2f}")
        anual[str(a)] = {"n": len(v), "media_8h": m, "bruto_anual_pct": 100 * m * 3 * 365,
                         "pct_negativos": pn}
    res["a2_3_tarifa_bruta"] = {
        "nota": "BRUTO, sin comisiones ni coste de margen. Un solo simbolo (BTCUSDT), "
                "pre-especificado en la 2.2 del brief: sin criba, no es la 4.2.",
        "media_8h": media, "mediana_8h": mediana,
        "bruto_anual_pct_media": 100 * media * 3 * 365,
        "bruto_anual_pct_mediana": 100 * mediana * 3 * 365,
        "n_negativos": neg, "pct_negativos": 100 * neg / n_exacto,
        "min_8h": min(tasas), "max_8h": max(tasas), "por_ano": anual}

    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
