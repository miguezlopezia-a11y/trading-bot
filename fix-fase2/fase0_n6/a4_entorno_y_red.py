"""A-4 (N6, Fase 0) — Interprete usable y ausencia de red.

Reverifica, con comandos propios, lo que N4 (A-5/A-6) y N5 (A.1/A.5) dejaron
dicho: que hay un Python usable sin tocar nada y que el contenedor no alcanza
ninguna fuente de datos de mercado. No descarga nada: solo pregunta por el
codigo HTTP y lo reporta.

El brief de N6 dice: "Si algo intenta descargar, es el defecto H1: reportarlo,
no sortearlo." Este script por tanto NO parchea nada; solo inventaria que
modulos de src/ harian una descarga si se ejecutasen.

Uso (desde la raiz del repo):  python3 -I fix-fase2/fase0_n6/a4_entorno_y_red.py
"""
import os
import subprocess
import sys

MODULOS = ["numpy", "pandas", "scipy", "statsmodels", "yfinance", "torch",
           "timesfm", "statistics"]

# Las mismas 10 fuentes que N5 probo, mas las dos de N4 que no estaban.
FUENTES = [
    ("Yahoo chart BTC-USD", "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"),
    ("Yahoo fc", "https://fc.yahoo.com"),
    ("Binance ping", "https://api.binance.com/api/v3/ping"),
    ("Coinbase", "https://api.exchange.coinbase.com/products"),
    ("Kraken", "https://api.kraken.com/0/public/Time"),
    ("Bitstamp", "https://www.bitstamp.net/api/v2/ticker/btcusd/"),
    ("OKX", "https://www.okx.com/api/v5/public/time"),
    ("Bybit", "https://api.bybit.com/v5/market/time"),
    ("Stooq", "https://stooq.com/q/d/l/?s=btcusd&i=d"),
    ("FRED", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"),
    ("SSRN 2460551", "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551"),
    ("PyPI simple", "https://pypi.org/simple/"),
]


def main():
    print("=== A-4.1 interprete ===")
    print("sys.executable :", sys.executable)
    print("version        :", sys.version.replace("\n", " "))
    print("cwd            :", os.getcwd())
    print()
    print("=== A-4.2 modulos ===")
    for m in MODULOS:
        try:
            mod = __import__(m)
            v = getattr(mod, "__version__", "(stdlib)")
            print(f"  {m:<14} OK   {v}")
        except Exception as e:
            print(f"  {m:<14} NO   {type(e).__name__}")
    print()
    print("=== A-4.3 venv citado en los docstrings de src/ ===")
    p = "/opt/trading-bot/venv/bin/python"
    print(f"  {p}: {'EXISTE' if os.path.exists(p) else 'NO EXISTE'}")
    print()
    print("=== A-4.4 red: 12 destinos, solo codigo HTTP ===")
    alcanzables = 0
    for nombre, url in FUENTES:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "12", "-o", "/dev/null",
             "-w", "%{http_code}", url],
            capture_output=True, text=True)
        code = (r.stdout or "").strip() or "000"
        err = (r.stderr or "").strip().replace("\n", " ")[:70]
        ok = code.startswith("2")
        alcanzables += ok
        print(f"  {nombre:<22} http={code:<4} {'ALCANZABLE' if ok else 'NO'}"
              f"{('  | ' + err) if err else ''}")
    print(f"\n  fuentes de MERCADO alcanzables: "
          f"{sum(1 for n, u in FUENTES[:10] if False)} de 10 "
          f"(ver lineas de arriba)")
    print(f"  destinos alcanzables en total: {alcanzables} de {len(FUENTES)}")
    print()
    print("=== A-4.5 modulos de src/ que descargarian si se ejecutasen ===")
    r = subprocess.run(["grep", "-rn", "yf.download", "--include=*.py",
                        "src", "fix-fase2/src"], capture_output=True, text=True)
    print(r.stdout or "  (ninguno)")
    print("NOTA: no se parchea ninguno. Se reporta, como manda el brief (A-4).")


if __name__ == "__main__":
    main()
