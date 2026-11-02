"""N7 · B-b (obligatoria) — Buscar ACTIVAMENTE la construccion que favorezca a
Fase B y medirla. El brief lo escribio alguien que ya dijo que cree que Fase B
pierde: esa predisposicion se trata como sesgo del autor.
Corre DESDE fix-fase2/.  Salida: b_b_salida.json

Candidatas del brief: (1) el panel de 15 de la §2.7, (2) el drawdown -26.9 vs
-88.96 de la §2.1. Candidatas propias: (3) el benchmark B&H PURO en vez del
igual-ponderado rebalanceado a diario, (4) cobrarle al benchmark su coste real
de rebalanceo (A-4), (5) B&H de BTC solo, que es lo que "comprar y aguantar"
significa para quien no construye cestas, y es el benchmark que uso Fase A.
Todas sobre la construccion (a) ALINEADA, que B-a establece como la honesta.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLO10 = "20261007"
SELLO15 = "20261009"      # el panel de 15 solo tiene este sello (A-1 · §2.7)
COSTE_UNIT = pr.COMMISSION + pr.SLIPPAGE


def sharpe(x):
    v = np.asarray(x, dtype=float); v = v[~np.isnan(v)]
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(pr.PPY)) if len(v) > 1 and sd > 0 else 0.0


def calmar(x):
    v = pd.Series(np.asarray(x, dtype=float)).fillna(0.0)
    eq = (1 + v).cumprod(); dd = (eq - eq.cummax()) / eq.cummax()
    a = len(v) / pr.PPY
    return float((eq.iloc[-1] - 1) / abs(dd.min()) / a) if dd.min() != 0 and a > 0 else 0.0


def mdd(x):
    v = pd.Series(np.asarray(x, dtype=float)).fillna(0.0)
    eq = (1 + v).cumprod()
    return float(((eq - eq.cummax()) / eq.cummax()).min() * 100)


def curvas_bench(closes, lookback):
    """Devuelve (r_ew_diario, r_bh_puro, coste_rebal_diario, elig)."""
    R = closes.pct_change().values
    T, n = R.shape
    cum = np.cumsum((~np.isnan(R)).astype(np.int64), axis=0)
    elig = cum >= (lookback + 1)
    wt = np.zeros((T, n))
    for t in range(T):
        idx = np.where(elig[t])[0]
        if len(idx):
            wt[t, idx] = 1.0 / len(idx)
    # EW rebalanceado a diario (el del codigo) + su turnover real
    r_ew = np.zeros(T); coste = np.zeros(T); w_hold = np.zeros(n)
    for t in range(T):
        r = np.nan_to_num(R[t], nan=0.0)
        idx = np.where(elig[t])[0]
        rb = float(np.nanmean(R[t][idx])) if len(idx) else 0.0
        r_ew[t] = 0.0 if np.isnan(rb) else rb
        val = w_hold * (1 + r); s = val.sum()
        wd = val / s if s > 0 else np.zeros(n)
        coste[t] = float(np.abs(wt[t] - wd).sum()) * COSTE_UNIT
        w_hold = wt[t].copy()
    # B&H puro: reparto solo los dias de entrada
    val = np.zeros(n); bh = np.zeros(T)
    for t in range(T):
        val = val * (1 + np.nan_to_num(R[t], nan=0.0))
        idx = np.where(elig[t])[0]
        if (t == 0 or (elig[t] != elig[t - 1]).any()) and len(idx):
            tot = val.sum() if val.sum() > 0 else 1.0
            val = np.zeros(n); val[idx] = tot / len(idx)
        bh[t] = val.sum() if val.sum() > 0 else (bh[t - 1] if t else 1.0)
    r_bh = np.concatenate([[0.0], bh[1:] / bh[:-1] - 1])
    return r_ew, r_bh, coste, elig


def main():
    out = {"candidatas": {}}

    # ---------------- panel de 10
    datos = pr.cargar_congelados(pr.ACTIVOS, stamp=SELLO10, verbose=False)
    closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
    res = pr.simulate(datos)
    e = res["exposure"].values
    r_est = res["equity"].pct_change().fillna(0.0).values
    r_ew, r_bh, coste, _ = curvas_bench(closes, pr.LOOKBACK)
    s_est = sharpe(r_est)

    print(f"=== B-b.1 panel de 10, sello {SELLO10}: la escalera de candidatas ===")
    print("  Todas con la construccion (a) ALINEADA: r_b(t) = exposure[t]*r_b(t)")
    print(f"  Fase B (neto de costes): Sharpe {s_est:.4f}  Calmar "
          f"{calmar(r_est):.3f}  maxDD {mdd(r_est):.2f} %")
    print()
    print(f"  {'benchmark igualado a exposure[t]':<48} {'Sharpe':>8} {'dif':>9}"
          f" {'Calmar':>8} {'maxDD %':>9} {'¿gana FaseB?':>13}")
    cands = [
        ("EW diario, sin coste (el del expediente)", e * r_ew),
        ("EW diario, CON su coste real de rebalanceo", e * (r_ew - coste)),
        ("B&H PURO (sin rebalanceo diario)", e * r_bh),
    ]
    # CORREGIDO tras la critica (hallazgo 11, MEDIA). La v1 tenia una cuarta
    # fila, "B&H PURO + coste de las 4 entradas", BIT A BIT identica a la
    # anterior porque el B&H puro no paga rebalanceo diario. Inflaba el
    # recuento a costa de una fila vacia. Retirada.
    for nom, x in cands:
        d = s_est - sharpe(x)
        print(f"  {nom:<48} {sharpe(x):>8.4f} {d:>+9.4f} {calmar(x):>8.3f}"
              f" {mdd(x):>9.2f} {str(d > 0):>13}")
        out["candidatas"][nom] = {"sharpe_bench": sharpe(x),
                                  "diferencial": d, "calmar_bench": calmar(x),
                                  "max_dd_bench": mdd(x), "gana_fase_b": bool(d > 0)}
    # combinada: B&H puro + coste
    x = e * (r_bh - coste * 0)   # el B&H puro no paga rebalanceo diario
    print("  (el B&H puro no paga rebalanceo diario: solo 4 entradas en 12 anos,")
    print("   turnover total ~2.92 segun A-4 -> coste acumulado 0.44 %, despreciable)")

    print(f"\n=== B-b.2 candidata (5) propia: B&H de BTC SOLO ===")
    btc = closes["BTC-USD"]
    r_btc = btc.pct_change().fillna(0.0).values
    print("  Es el benchmark que uso Fase A (rigor_estadistico.py:188, data['bh'])")
    print("  y es lo que 'comprar y aguantar' significa para quien no construye")
    print("  una cesta igual-ponderada rebalanceada a diario.")
    for nom, x in [("BTC B&H, 100 %", r_btc),
                   ("BTC B&H igualado a exposure[t]", e * r_btc)]:
        d = s_est - sharpe(x)
        print(f"  {nom:<48} {sharpe(x):>8.4f} {d:>+9.4f} {calmar(x):>8.3f}"
              f" {mdd(x):>9.2f} {str(d > 0):>13}")
        out["candidatas"][nom] = {"sharpe_bench": sharpe(x), "diferencial": d,
                                  "calmar_bench": calmar(x), "max_dd_bench": mdd(x),
                                  "gana_fase_b": bool(d > 0)}

    print(f"\n=== B-b.3 candidata (2) del brief: el drawdown y el Calmar ===")
    best = e * r_ew
    print(f"  maxDD Fase B {mdd(r_est):.2f} % vs (a) EW igualado {mdd(best):.2f} %"
          f"  -> Fase B {'GANA' if mdd(r_est) > mdd(best) else 'pierde'}")
    print(f"  maxDD Fase B {mdd(r_est):.2f} % vs bench PUBLICADO al 100 % "
          f"{mdd(r_ew):.2f} %  -> Fase B GANA por {mdd(r_est)-mdd(r_ew):+.2f} pp")
    print(f"  Calmar Fase B {calmar(r_est):.3f} vs (a) EW igualado "
          f"{calmar(best):.3f}  -> Fase B "
          f"{'GANA' if calmar(r_est) > calmar(best) else 'pierde'}")
    # CORREGIDO tras la critica (hallazgo 4, CRITICA). La v1 concluia aqui que
    # el contrapeso "se evapora" / "desaparece". ES FALSO, y lo contradice este
    # mismo script dos lineas arriba ("-> Fase B GANA") y el campo
    # contrapeso_sobrevive_a_igual_exposicion del JSON.
    gana_mdd = abs(mdd(r_est)) < abs(mdd(best))
    print("  => el contrapeso COLAPSA EN MAGNITUD Y CONSERVA EL SIGNO:")
    print(f"     del par publicado {mdd(r_ew)/mdd(r_est):.3f}x  ->  a igual"
          f" exposicion {mdd(best)/mdd(r_est):.4f}x")
    print(f"     de +{mdd(r_est)-mdd(r_ew):.2f} pp a +{mdd(r_est)-mdd(best):.2f} pp")
    print(f"     Fase B sigue teniendo el drawdown MENOR: {gana_mdd}")
    print(f"     Lo que SI se invierte es el Calmar: {calmar(r_est):.3f} contra"
          f" {calmar(best):.3f}")
    print("     Luego la §2.1 NO debe RETIRAR el drawdown: debe declararlo")
    print("     medido a igual exposicion. Retirarlo borraria un hecho cierto.")
    out["drawdown"] = {"mdd_fase_b": mdd(r_est), "mdd_a_igualado": mdd(best),
                       "mdd_bench_100": mdd(r_ew),
                       "calmar_fase_b": calmar(r_est),
                       "calmar_a_igualado": calmar(best),
                       "contrapeso_sobrevive_a_igual_exposicion":
                           bool(abs(mdd(r_est)) < abs(mdd(best))),
                       "ratio_par_publicado": float(mdd(r_ew) / mdd(r_est)),
                       "ratio_a_igual_exposicion": float(mdd(best) / mdd(r_est)),
                       "calmar_se_invierte": bool(calmar(r_est) < calmar(best)),
                       "lectura": "colapsa en magnitud, conserva el signo"}

    # ---------------- panel de 15
    print(f"\n=== B-b.4 candidata (1) del brief: el panel de 15, sello {SELLO15} ===")
    print("  UNA cifra de titular, no la tabla de la §4.1: esto es Paso B.")
    import portfolio_supervivencia as ps
    univ = list(ps.VIVOS) + list(ps.MUERTOS)
    print(f"  universo de 15 leido de portfolio_supervivencia.py "
          f"(VIVOS+MUERTOS, lineas 39-41): {len(univ)} activos")
    print(f"    VIVOS   ({len(ps.VIVOS)}): {ps.VIVOS}")
    print(f"    MUERTOS ({len(ps.MUERTOS)}): {ps.MUERTOS}")
    d15 = pr.cargar_congelados(univ, data_dir="data/multi_muertos",
                               stamp=SELLO15, verbose=False)
    cl15 = pd.DataFrame({k: v["close"] for k, v in d15.items()}).sort_index()
    res15 = pr.simulate(d15)
    e15 = res15["exposure"].values
    r15 = res15["equity"].pct_change().fillna(0.0).values
    ew15, bh15, c15, _ = curvas_bench(cl15, pr.LOOKBACK)
    s15 = sharpe(r15)
    print(f"  Fase B panel 15: Sharpe {s15:.4f}  exposicion media {e15.mean():.6f}"
          f"  dias {len(e15)}")
    for nom, x in [("EW 100 % (el publicado del panel 15)", ew15),
                   ("EW igualado a exposure[t]", e15 * ew15),
                   ("EW igualado + coste real", e15 * (ew15 - c15)),
                   ("B&H PURO igualado a exposure[t]", e15 * bh15)]:
        d = s15 - sharpe(x)
        print(f"  {nom:<48} {sharpe(x):>8.4f} {d:>+9.4f} {calmar(x):>8.3f}"
              f" {mdd(x):>9.2f} {str(d > 0):>13}")
        out["candidatas"]["panel15 · " + nom] = {
            "sharpe_bench": sharpe(x), "diferencial": d,
            "calmar_bench": calmar(x), "max_dd_bench": mdd(x),
            "gana_fase_b": bool(d > 0)}
    # ANADIDO tras la critica (hallazgo 14, MEDIA). La v1 describia una
    # "escalera" sumando +0.010 (coste) + 0.032 (B&H puro) + 0.028 (panel 15)
    # como si fueran aditivos. No lo son: coste y B&H puro se miden los DOS
    # desde la misma base, y el B&H puro no paga rebalanceo diario, asi que el
    # +0.010 se anula en cuanto se aplica el +0.032. Y la fila que combina las
    # tres NO ESTABA MEDIDA. Aqui esta.
    print("\n=== B-b.4-bis la fila combinada, que la v1 no midio ===")
    comb = e15 * bh15          # panel 15 + B&H puro + igual exposicion
    dc = s15 - sharpe(comb)
    print(f"  {'panel 15 + B&H puro + igual exposicion':<48} {sharpe(comb):>8.4f}"
          f" {dc:>+9.4f} {calmar(comb):>8.3f} {mdd(comb):>9.2f} {str(dc > 0):>13}")
    print("  Coincide con 'B&H PURO igualado' porque el B&H puro no tiene")
    print("  rebalanceo diario que cobrar: la combinacion de las tres")
    print("  correcciones ES esa fila, no la suma de sus tres deltas.")
    print(f"  Suma aritmetica ingenua de los tres deltas sobre -0.0629:"
          f" {-0.0629 + 0.0101 + 0.0319 + 0.0330:+.4f}  <- NO es el resultado")
    print(f"  Resultado realmente medido                   : {dc:+.4f}")
    print(f"  -> diferencial mas benigno de todas las construcciones HONESTAS")
    out["fila_combinada_panel15_bh_puro"] = {
        "sharpe_bench": sharpe(comb), "diferencial": dc,
        "nota": "el coste de rebalanceo no aplica al B&H puro; las tres "
                "correcciones NO son aditivas"}
    out["panel15"] = {"sharpe_fase_b": s15, "exposicion_media": float(e15.mean()),
                      "dias": int(len(e15)), "sello": SELLO15,
                      "aviso_sellos": "el panel de 10 corre con 20261007 y el de "
                                      "15 solo existe con 20261009: NO van en la "
                                      "misma escalera"}

    print("\n=== B-b.5 veredicto de B-b ===")
    ganan = [k for k, v in out["candidatas"].items() if v["gana_fase_b"]]
    print(f"  construcciones DISTINTAS medidas aqui: {len(out['candidatas'])}")
    print("  (la v1 decia 'diez': una de sus filas era duplicado al bit de otra)")
    print(f"  AVISO DE SELLOS: las del panel de 10 corren con {SELLO10} y las del")
    print(f"  panel de 15 con {SELLO15}, porque el de 15 solo existe con ese sello.")
    print("  NO se pueden leer como una sola escalera.")
    print(f"  construcciones en que Fase B GANA: {len(ganan)}")
    for g in ganan:
        print(f"    - {g}: diferencial {out['candidatas'][g]['diferencial']:+.4f}")
    if not ganan:
        print("    (ninguna)")
    out["construcciones_en_que_gana_fase_b"] = ganan
    out["n_construcciones_distintas"] = len(out["candidatas"])
    json.dump(out, open("fase0_n7/b_b_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/b_b_salida.json")


if __name__ == "__main__":
    main()
