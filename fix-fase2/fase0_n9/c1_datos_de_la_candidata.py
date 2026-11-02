"""N9 Paso C, candidata C-1: comprueba si la serie historica que necesita su prueba
de muerte se baja sin clave desde el VPS, incluidos contratos ya vencidos.
Uso desde fix-fase2/: /opt/trading-bot/venv/bin/python fase0_n9/c1_datos_de_la_candidata.py
"""
import json
import urllib.error
import urllib.request

OUT = "fase0_n9/salida_c1_datos_de_la_candidata.json"
UA = "n9-fase0/1.0 (publico, sin credenciales)"
K = "https://fapi.binance.com/fapi/v1/klines?symbol={}&interval=1d&limit=5"
CANDIDATOS = ["BTCUSDT_261225", "BTCUSDT_270326", "BTCUSDT_260327",
              "BTCUSDT_260626", "BTCUSDT_260925", "BTCUSDT_251226",
              "ETHUSDT_260925", "BTCUSDT"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    res = {"credenciales_enviadas": [], "endpoint": K, "pruebas": {}}
    print("=== C-1 — se baja sin clave la serie de contratos con vencimiento? ===")
    print(f"{'symbol':<18} {'http':>5} {'filas':>6}  primera/ultima vela o error")
    for s in CANDIDATOS:
        http, body = get(K.format(s))
        try:
            d = json.loads(body)
        except Exception:
            d = None
        if isinstance(d, list):
            n = len(d)
            det = ("vacio" if n == 0 else
                   f"t0={d[0][0]} cierre0={d[0][4]} tN={d[-1][0]} cierreN={d[-1][4]}")
        else:
            n = 0
            det = body[:120]
        print(f"{s:<18} {http:>5} {n:>6}  {det}")
        res["pruebas"][s] = {"http": http, "filas": n, "detalle": det}

    vencidos = [s for s in CANDIDATOS if s.count("_")
                and res["pruebas"][s]["filas"] > 0]
    print(f"\ncontratos con guion que devuelven velas: {vencidos}")
    print("si entre ellos hay alguno YA VENCIDO, la prueba de muerte de C-1 es")
    print("ejecutable sin clave; si solo responden los vivos, hay que cambiar de fuente")
    res["veredicto"] = {"con_velas": vencidos}
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
