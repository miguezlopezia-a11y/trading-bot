"""N7 · A-7 — Interprete, modulos y red.

Corre DESDE fix-fase2/.  Salida: a7_salida.json
No descarga nada: solo pide el codigo HTTP de cada destino con curl.
Y comprueba que modulos de src/ intentarian descargar al EJECUTARSE
(no al importarse): se reportan, no se parchean.
"""
import json
import os
import subprocess
import sys

DESTINOS = [
    ("Yahoo chart BTC-USD", "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"),
    ("Yahoo fc", "https://fc.yahoo.com"),
    ("Binance ping", "https://api.binance.com/api/v3/ping"),
    ("Coinbase", "https://api.exchange.coinbase.com/products/BTC-USD/stats"),
    ("Kraken", "https://api.kraken.com/0/public/Time"),
    ("Bitstamp", "https://www.bitstamp.net/api/v2/ticker/btcusd/"),
    ("OKX", "https://www.okx.com/api/v5/public/time"),
    ("Bybit", "https://api.bybit.com/v5/market/time"),
    ("Stooq", "https://stooq.com/q/d/l/?s=btcusd&i=d"),
    ("FRED DGS3MO", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO"),
    ("PyPI simple", "https://pypi.org/simple/"),
]
MERCADO = {d[0] for d in DESTINOS} - {"PyPI simple"}


def main():
    out = {"interprete": {}, "modulos": {}, "red": [], "descargarian": []}
    out["interprete"] = {"executable": sys.executable, "version": sys.version}
    print("=== A-7.1 interprete ===")
    print(f"  sys.executable : {sys.executable}")
    print(f"  version        : {sys.version}")

    print("=== A-7.2 modulos ===")
    for m in ["numpy", "pandas", "scipy", "statsmodels", "yfinance", "statistics"]:
        try:
            mod = __import__(m)
            v = getattr(mod, "__version__", "(stdlib)")
            out["modulos"][m] = v
            print(f"  {m:<14} OK   {v}")
        except Exception as e:
            out["modulos"][m] = f"NO: {type(e).__name__}"
            print(f"  {m:<14} NO   {type(e).__name__}")

    print("=== A-7.3 red: solo codigo HTTP, sin descargar cuerpo ===")
    alcanzables = 0
    merc_ok = 0
    for nombre, url in DESTINOS:
        try:
            p = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "8", url],
                capture_output=True, text=True, timeout=20)
            code = p.stdout.strip() or "000"
            err = p.stderr.strip()[:60]
        except Exception as e:
            code, err = "000", str(e)[:60]
        ok = code.startswith("2") or code.startswith("3")
        if ok:
            alcanzables += 1
            if nombre in MERCADO:
                merc_ok += 1
        out["red"].append({"destino": nombre, "http": code, "alcanzable": ok,
                           "err": err})
        print(f"  {nombre:<22} http={code}  {'ALCANZABLE' if ok else 'NO'}"
              f"{'  | ' + err if err and not ok else ''}")
    out["alcanzables_total"] = alcanzables
    out["fuentes_mercado_alcanzables"] = merc_ok
    out["fuentes_mercado_total"] = len(MERCADO)
    print(f"  fuentes de MERCADO alcanzables: {merc_ok} de {len(MERCADO)}")
    print(f"  destinos alcanzables en total : {alcanzables} de {len(DESTINOS)}")

    print("=== A-7.4 que descargaria si se EJECUTASE (grep, no ejecucion) ===")
    for root in ["src"]:
        for f in sorted(os.listdir(root)):
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            for i, line in enumerate(open(path, encoding="utf-8"), 1):
                if "yf.download" in line:
                    out["descargarian"].append(f"{path}:{i}")
                    print(f"  {path}:{i}")
    print("  (reportados, NO parcheados)")

    print("=== A-7.5 import de portfolio_runner: ¿descarga al importarse? ===")
    import importlib
    sys.path.insert(0, "src")
    pr = importlib.import_module("portfolio_runner")
    out["import_portfolio_runner_ok"] = True
    out["PERMITIR_DESCARGA"] = pr.PERMITIR_DESCARGA
    print(f"  import OK. PERMITIR_DESCARGA = {pr.PERMITIR_DESCARGA}")
    print("  -> importarlo no descarga: la descarga esta en load_or_download(),")
    print("     y exige PERMITIR_DESCARGA=1.")

    json.dump(out, open("fase0_n7/a7_salida.json", "w"), indent=2)
    print("-> fase0_n7/a7_salida.json")


if __name__ == "__main__":
    main()
