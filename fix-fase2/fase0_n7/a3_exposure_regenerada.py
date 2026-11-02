"""N7 · A-3 — Regenerar exposure(t) e intentar reproducir
exposicion_media = 0.1559827260735808 "al bit".  Corre DESDE fix-fase2/.

IMPORTANTE (limite de escritura del brief): el brief pide "ejecutar
portfolio_runner.py", pero su main() SOBREESCRIBE
results/portfolio_equity.csv, results/portfolio_benchmark.csv y
results/portfolio_runner.json, que el brief prohibe tocar. Aqui se IMPORTA
cargar_congelados() + simulate() y NO se llama a main(): ni un byte de
results/ se toca. La contradiccion queda registrada como hallazgo.

Se corre con los DOS sellos congelados que hay en data/multi (20261007 y
20261009) porque portfolio_bateria.json declara dias=4404, que es el 20261007.

Cache para A-4, A-5 y el Paso B: fase0_n7/a3_cache_<sello>.csv
Salida: a3_salida.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

OBJETIVO = 0.1559827260735808
SELLOS = ["20261007", "20261009"]


def correr(sello):
    assert not pr.PERMITIR_DESCARGA, "PERMITIR_DESCARGA activo: abortado"
    datos = pr.cargar_congelados(pr.ACTIVOS, data_dir=pr.DATA_DIR,
                                 stamp=sello, verbose=True)
    res = pr.simulate(datos)
    return res


def main():
    out = {"objetivo_exposicion_media": OBJETIVO, "sellos": {}}
    print("=== A-3.0 el brief manda EJECUTAR portfolio_runner.py ===")
    print("  su main() escribe en results/ (lineas 370-371, 372):")
    for i, l in enumerate(open("src/portfolio_runner.py", encoding="utf-8"), 1):
        if i in (370, 371, 372):
            print(f"   {i}: {l.rstrip()}")
    print("  -> prohibido por los limites de escritura. Se IMPORTA simulate().")

    for sello in SELLOS:
        print(f"\n=== A-3.1 re-simulacion con STAMP_CONGELADO={sello} ===")
        res = correr(sello)
        expo = res["exposure"]
        eq = res["equity"]
        be = res["benchmark"]
        media = float(expo.mean())
        dif = media - OBJETIVO
        print(f"  dias                 : {res['n_dias']}  "
              f"{expo.index[0].date()} -> {expo.index[-1].date()}")
        print(f"  exposicion_media     : {media!r}")
        print(f"  objetivo publicado   : {OBJETIVO!r}")
        print(f"  diferencia           : {dif:.3e}")
        print(f"  identica al bit      : {media == OBJETIVO}")
        print(f"  exposure min/max     : {float(expo.min()):.6f} / "
              f"{float(expo.max()):.6f}")
        print(f"  dias con exposure==0 : {int((expo == 0).sum())}"
              f"  ({100*float((expo==0).mean()):.2f}%)")
        print(f"  equity final         : {float(eq.iloc[-1])!r}")
        print(f"  bench final          : {float(be.iloc[-1])!r}")
        out["sellos"][sello] = {
            "dias": int(res["n_dias"]),
            "ini": str(expo.index[0].date()), "fin": str(expo.index[-1].date()),
            "exposicion_media": media,
            "diferencia_vs_objetivo": dif,
            "identica_al_bit": bool(media == OBJETIVO),
            "expo_min": float(expo.min()), "expo_max": float(expo.max()),
            "dias_expo_cero": int((expo == 0).sum()),
            "equity_final": float(eq.iloc[-1]),
            "bench_final": float(be.iloc[-1]),
        }
        # cache para los scripts siguientes
        cache = pd.DataFrame({"exposure": expo, "equity": eq,
                              "benchmark": be, "rp": res["rp"],
                              "coste": res["costes"]})
        cache.to_csv(f"fase0_n7/a3_cache_{sello}.csv", index_label="date")
        print(f"  -> fase0_n7/a3_cache_{sello}.csv")

    print("\n=== A-3.2 contraste con la equity congelada de results/ ===")
    eq_rep = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                         parse_dates=True).iloc[:, 0]
    for sello in SELLOS:
        c = pd.read_csv(f"fase0_n7/a3_cache_{sello}.csv", index_col=0,
                        parse_dates=True)
        com = eq_rep.index.intersection(c.index)
        d = float(np.abs(eq_rep.loc[com].values - c.loc[com, "equity"].values).max())
        print(f"  sello {sello}: {len(com)} fechas comunes, "
              f"max|dif equity| = {d:.3e}")
        out["sellos"][sello]["fechas_comunes_con_results"] = int(len(com))
        out["sellos"][sello]["max_dif_equity_vs_results"] = d

    print("\n=== A-3.3 veredicto del NO-GO ===")
    exacto = [s for s in SELLOS if out["sellos"][s]["identica_al_bit"]]
    out["sellos_que_reproducen_al_bit"] = exacto
    if exacto:
        print(f"  reproduce AL BIT con el sello: {exacto}")
        out["veredicto_nogo"] = f"NO-GO NO SE DISPARA (sello {exacto[0]})"
    else:
        print("  NINGUN sello reproduce exposicion_media al bit")
        out["veredicto_nogo"] = "NO-GO SE DISPARA"
    print(f"  -> {out['veredicto_nogo']}")
    print("  OJO: el brief manda el sello 20261009 explicitamente en A-3.")
    out["sello_que_manda_el_brief"] = "20261009"
    out["reproduce_con_el_sello_del_brief"] = \
        out["sellos"]["20261009"]["identica_al_bit"]

    json.dump(out, open("fase0_n7/a3_salida.json", "w"), indent=2)
    print("-> fase0_n7/a3_salida.json")


if __name__ == "__main__":
    main()
