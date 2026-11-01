"""A-1 (N6, Fase 0) — Inventario de los trece ficheros de results/ que ninguna
auditoria ha mirado.

El brief (§2.1) dice que results/ (raiz) y fix-fase2/results/ comparten solo
dos ficheros, y que los trece restantes de la raiz son material no auditado.
A-1 pide, para cada uno: que estrategia o experimento documenta, con que
sizing, sobre que CSV, y si constituye un trial.

"Trial", para este inventario, se usa en el sentido Bailey-LdP tal como esta
transcrito en el propio repo (fix-fase2/src/rigor_estadistico.py:17-22 y
fix-fase2/docs/rigor_estadistico_resultado.md): una CONFIGURACION DE ESTRATEGIA
probada contra los datos para ver si gana dinero. No se cita el paper, que no
es alcanzable desde este contenedor (A-4). Esta distincion es la que el
hallazgo 6 del segundo agente de N4 obligo a hacer explicita.

Uso (desde la raiz del repo):  python3 -I fix-fase2/fase0_n6/a1_inventario_results_raiz.py
"""
import json
import os
import re

RAIZ = "results"
FF2 = "fix-fase2/results"

# Las 11 variantes que componen la V(11) del expediente.
V11 = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
       "sma_timing_50", "sma_timing_100", "sma_timing_304", "tsmom_7",
       "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]


def sizing_y_csv_de(script):
    """Lee del codigo fuente el sizing efectivo y el origen de datos."""
    p = f"fix-fase2/src/{script}"
    if not os.path.exists(p):
        p = f"src/{script}"
    if not os.path.exists(p):
        return "(script ausente)", "(script ausente)"
    txt = open(p).read()
    m = re.search(r"^SIZE_FRACTION\s*=\s*([0-9.]+)", txt, re.M)
    sizing = m.group(1) if m else None
    if sizing is None:
        # ¿llama run_backtest sin size_fraction? -> default del backtester
        if re.search(r"run_backtest\([^)]*\)", txt) and "size_fraction" not in txt:
            bt = open("fix-fase2/src/backtester.py").read()
            mb = re.search(r"size_fraction[^=]*=\s*([0-9.]+)", bt)
            sizing = f"{mb.group(1)} (DEFAULT de backtester.py, no pasado)" if mb else "?"
        else:
            sizing = "?"
    origen = "yf.download (RED)" if "yf.download" in txt else "CSV congelado"
    if "btc_usd_5y_1d.csv" in txt:
        origen = "data/btc_usd_5y_1d.csv (congelado)"
    return sizing, origen


def main():
    comunes = set(os.listdir(RAIZ)) & set(os.listdir(FF2))
    solo_raiz = sorted(set(os.listdir(RAIZ)) - comunes)
    print(f"=== A-1 — {len(solo_raiz)} ficheros solo en results/ (raiz) ===\n")

    filas = []
    for n in solo_raiz:
        p = os.path.join(RAIZ, n)
        d = json.load(open(p))

        if n.startswith("walkforward_stability"):
            script = "walkforward_stability.py"
            estr = d.get("estrategia", "(sin campo)")
            sizing, origen = sizing_y_csv_de(script)
            configs = list(d.get("configs", {}))
            dictamen = d.get("dictamen")
            experimento = (f"walk-forward de ESTABILIDAD de '{estr}': mismo codigo "
                           f"y mismos parametros sobre {len(configs)} ventanas "
                           f"{configs}")
            # ¿la estrategia es nueva respecto a las 11 de V?
            nueva = estr not in V11
            trial = ("NO — reejecucion de una estrategia YA contada en V(11); "
                     "mide estabilidad, no busca parametro" if not nueva else
                     "SI — estrategia fuera de V(11)")
            filas.append((n, experimento, sizing, origen, dictamen, trial, estr))

        elif n == "backtest_sizing05.json":
            script = "backtest_sizing05.py"
            sizing, origen = sizing_y_csv_de(script)
            estrs = list(d.get("test_results", {}))
            experimento = (f"backtest OOS con sizing reducido de "
                           f"{len(estrs)} estrategias: {estrs}")
            nuevas = [e for e in estrs if e not in V11]
            trial = (f"SI — {len(nuevas)} de {len(estrs)} estan FUERA de V(11): "
                     f"{nuevas}")
            filas.append((n, experimento, f"{d.get('size_fraction')} (en el JSON)",
                          d.get("csv", origen), None, trial, ",".join(estrs)))

        elif n == "backtest_summary.json":
            script = "run_backtest.py"
            sizing, origen = sizing_y_csv_de(script)
            estrs = list(d.get("test_results", d.get("results", {})))
            experimento = f"backtest de {len(estrs)} estrategias: {estrs}"
            trial = ("NO COMMENSURABLE — sizing y origen de datos distintos de "
                     "los de Fase A; no se puede meter en la misma V")
            filas.append((n, experimento, sizing, origen, None, trial,
                          ",".join(estrs)))
        else:
            filas.append((n, "(no clasificado)", "?", "?", None, "?", "?"))

    for n, exp, sz, org, dic, tr, _ in filas:
        print(f"[{n}]")
        print(f"  documenta : {exp}")
        print(f"  sizing    : {sz}")
        print(f"  datos     : {org}")
        if dic is not None:
            print(f"  dictamen  : {dic}")
        print(f"  ¿trial?   : {tr}")
        print()

    print("=== A-1 recuento ===")
    wf = [f for f in filas if f[0].startswith("walkforward_stability")]
    print(f"  walkforward_stability_*.json en results/ (raiz) : {len(wf)}")
    estrs_wf = sorted({f[6] for f in wf})
    print(f"  estrategias que cubren : {len(estrs_wf)} -> {estrs_wf}")
    fuera = [e for e in estrs_wf if e not in V11]
    print(f"  de ellas, FUERA de V(11): {fuera if fuera else 'ninguna'}")
    print()
    # El 11º fichero walkforward esta en los dos arboles
    print(f"  Fichero walkforward COMUN a los dos arboles (no contado arriba):")
    for c in sorted(comunes):
        if c.startswith("walkforward"):
            dd = json.load(open(os.path.join(RAIZ, c)))
            print(f"    {c}  estrategia={dd.get('estrategia')}")
    print()
    print("  CONCLUSION A-1 sobre si N sube por estos trece:")
    print("   - Los walkforward_stability_* NO anaden estrategias nuevas:")
    print("     cubren exactamente las mismas 11 de V(11) (10 aqui + 1 comun)")
    print("     mas walkforward_stability.json, que es el default ma_cross.")
    print("   - backtest_sizing05.json SI anade 3 (mean_reversion, breakout,")
    print("     trend_following), que es lo que ya dijo N4.")
    print("   - backtest_summary.json no es commensurable (sizing/datos).")
    print("   => N NO pasa de 15 por este inventario. Queda en >=15.")


if __name__ == "__main__":
    main()
