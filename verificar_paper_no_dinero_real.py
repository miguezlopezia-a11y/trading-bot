"""Verificacion estructural: el paper runner NO tiene capacidad de orden real.

No basta un flag PAPER=True: se inspecciona el PATH DE EJECUCION por AST
(paper_runner + todo lo que importa desde src/) buscando:
  1. imports de clientes de exchange (ccxt, binance, kraken, alpaca, ...).
  2. llamadas/cadenas tipicas de orden real (create_order, place_order,
     market_buy/sell, submit_order, ...).
  3. variables de entorno de API de exchange presentes en el entorno del test.

Uso: /opt/trading-bot/venv/bin/python verificar_paper_no_dinero_real.py
     (desde la raiz del repo/copia)
"""
import ast
import os
import sys

EXCHANGE_MODULES = {"ccxt", "binance", "python_binance", "kraken", "alpaca",
                    "alpaca_trade_api", "coinbase", "kucoin", "bybit", "okx"}
ORDER_PATTERNS = ["create_order", "place_order", "submit_order", "market_buy",
                  "market_sell", "limit_buy", "limit_sell", "create_test_order",
                  "order_market", "private_post_order"]
ENV_FORBIDDEN_PREFIXES = ("BINANCE", "KRAKEN", "COINBASE", "ALPACA", "BYBIT",
                          "OKX", "KUCOIN", "BITGET")


def imports_of(path, seen):
    """Devuelve todos los modulos importados transitivamente desde path."""
    tree = ast.parse(open(path).read(), path)
    base = os.path.dirname(path)
    mods = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for n in names:
            if n in EXCHANGE_MODULES:
                mods.add(n)
            cand = os.path.join(base, n + ".py")
            if os.path.exists(cand) and cand not in seen:
                seen.add(cand)
                mods |= imports_of(cand, seen)
    return mods


def main():
    ok = True
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    src = os.path.join(root, "src")
    runner = os.path.join(src, "paper_runner.py")
    assert os.path.exists(runner), f"no existe {runner}"

    # 1. imports de exchange en todo el arbol de imports
    seen = {runner}
    bad = imports_of(runner, seen)
    if bad:
        print(f"  FALLO: clientes de exchange importados: {sorted(bad)}")
        ok = False
    else:
        print(f"  OK imports: ningun cliente de exchange en el path "
              f"({len(seen)} modulos inspeccionados: "
              f"{sorted(os.path.basename(p) for p in seen)})")

    # 2. cadenas de orden real en los fuentes del path
    hits = []
    for p in seen:
        txt = open(p).read()
        for pat in ORDER_PATTERNS:
            if pat in txt:
                hits.append(f"{os.path.basename(p)}: '{pat}'")
    if hits:
        print(f"  FALLO: patrones de orden real encontrados: {hits}")
        ok = False
    else:
        print(f"  OK patrones: ninguno de {ORDER_PATTERNS} en el path")

    # 3. variables de entorno de exchange
    env_hits = [k for k in os.environ if k.startswith(ENV_FORBIDDEN_PREFIXES)
                and ("KEY" in k or "SECRET" in k)]
    if env_hits:
        print(f"  FALLO: variables de entorno de exchange presentes: {env_hits}")
        ok = False
    else:
        print("  OK entorno: sin variables de API de exchange")

    if ok:
        print("\nVERIFICACION OK: paper runner sin capacidad de dinero real (estructural).")
        return 0
    print("\nVERIFICACION FALLO: el runner podria ejecutar ordenes reales. PARAR.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
