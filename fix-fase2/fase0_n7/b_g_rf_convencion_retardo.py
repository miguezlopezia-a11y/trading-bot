"""N7 · B-g — ANADIDO tras la critica del Maker/Verifier.
Corre DESDE fix-fase2/.  Salida: b_g_salida.json

Cuatro cosas que la v1 del registro afirmo mal o a medias:

(1) hallazgo 6, ALTA: "rf se cancela exactamente". Es cierto SOLO para
    Sharpe(d). Para la DIFERENCIA de Sharpes -- que es la otra cantidad que la
    §4.1 tabula, y que el propio B-d declara distinta -- NO se cancela.
(2) hallazgo 7, ALTA: el "4,85 %, por debajo del 5 %" de A-5 depende de una
    convencion no declarada (si la cesta previa cobra el retorno del dia de
    entrada antes de aplanarse). Se miden las dos lecturas.
(3) hallazgo 13, MEDIA: el coste del retardo duplicado se reporto solo para (a)
    (+0.0056) y se omitio el de (c), que es mayor.
(4) hallazgo 15, MEDIA: el test de permutaciones NO mide seleccion de dias. Se
    descompone en media y varianza para ver que mide de verdad.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLO = "20261007"


def sh(x):
    v = np.asarray(x, float); v = v[~np.isnan(v)]
    s = float(np.std(v, ddof=1))
    return float(np.mean(v) / s * math.sqrt(pr.PPY)) if s > 0 else 0.0


def mdd(x):
    eq = (1 + pd.Series(np.asarray(x, float)).fillna(0)).cumprod()
    return float(((eq - eq.cummax()) / eq.cummax()).min() * 100)


def cal(x):
    eq = (1 + pd.Series(np.asarray(x, float)).fillna(0)).cumprod()
    d = ((eq - eq.cummax()) / eq.cummax()).min(); a = len(eq) / pr.PPY
    return float((eq.iloc[-1] - 1) / abs(d) / a) if d != 0 and a > 0 else 0.0


def main():
    datos = pr.cargar_congelados(pr.ACTIVOS, stamp=SELLO, verbose=False)
    closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
    res = pr.simulate(datos)
    e = res["exposure"].values
    r_est = res["equity"].pct_change().fillna(0.0).values
    r_ben = res["benchmark"].pct_change().fillna(0.0).values
    a = e * r_ben
    d = r_est - a
    out = {}

    print("=== B-g.1 (hallazgo 6) ¿se cancela rf? Las dos cantidades ===")
    base_dif, base_d = sh(r_est) - sh(a), sh(d)
    print(f"  base rf=0: dif de Sharpes = {base_dif:+.6f}   Sharpe(d) = {base_d:+.6f}")
    out["rf"] = {"base_dif_sharpes": base_dif, "base_sharpe_d": base_d, "cotas": {}}
    for rf in (0.02, 0.05):
        c = (1 - e) * (rf / pr.PPY)          # rf sobre el efectivo NO invertido
        e2, a2 = r_est + c, a + c
        d2 = e2 - a2
        dif2 = sh(e2) - sh(a2)
        print(f"  rf={rf*100:.0f} %/ano (cota declarada, no dato):")
        print(f"    Sharpe(d)         {base_d:+.6f} -> {sh(d2):+.6f}"
              f"   max|d2-d| = {np.abs(d2-d).max():.3e}  -> SE CANCELA")
        print(f"    dif de Sharpes    {base_dif:+.6f} -> {dif2:+.6f}"
              f"   mueve {dif2-base_dif:+.6f}  -> NO SE CANCELA")
        print(f"    Calmar del bench (a)  {cal(a):.3f} -> {cal(a2):.3f}")
        print(f"    maxDD  del bench (a)  {mdd(a):.2f} % -> {mdd(a2):.2f} %")
        out["rf"]["cotas"][f"{rf}"] = {
            "sharpe_d": sh(d2), "max_abs_dif_d": float(np.abs(d2 - d).max()),
            "dif_sharpes": dif2, "movimiento_dif_sharpes": dif2 - base_dif,
            "calmar_a": cal(a2), "mdd_a": mdd(a2),
            "pct_del_0_063": 100 * abs(dif2 - base_dif) / abs(base_dif)}
        print(f"    el movimiento es el {100*abs(dif2-base_dif)/abs(base_dif):.1f} %"
              f" del -0.0629 que el registro llama 'la cifra que decide'")
    print("  => el hilo 2 de la §4.2 NO esta vacio. Esta vacio para Sharpe(d) y")
    print("     NO para la diferencia de Sharpes ni para el Calmar. La v1 uso la")
    print("     invariancia de una para declarar vacio un hilo que mueve la otra.")
    print("     Y la cota es barata: no hace falta FRED para declarar un 2 %.")

    print("\n=== B-g.2 (hallazgo 7) A-5: las dos convenciones del dia de entrada ===")
    R = closes.pct_change().values
    T, n = R.shape
    cum = np.cumsum((~np.isnan(R)).astype(np.int64), axis=0)
    elig = cum >= (pr.LOOKBACK + 1)
    ew = [1.0]
    for t in range(T):
        i = np.where(elig[t])[0]
        rb = float(np.nanmean(R[t][i])) if len(i) else 0.0
        ew.append(ew[-1] * (1 + (0.0 if np.isnan(rb) else rb)))
    ew = np.asarray(ew[1:])
    r_ew = np.concatenate([[0.0], ew[1:] / ew[:-1] - 1])
    s_ew = sh(r_ew)
    out["a5_convenciones"] = {"sharpe_ew": s_ew, "lecturas": {}}
    for modo in ("crecer_primero", "repartir_primero"):
        val = np.zeros(n); bh = np.zeros(T)
        for t in range(T):
            i = np.where(elig[t])[0]
            entra = (t == 0 or (elig[t] != elig[t - 1]).any()) and len(i)
            if modo == "crecer_primero":
                val = val * (1 + np.nan_to_num(R[t], nan=0.0))
                if entra:
                    tot = val.sum() or 1.0
                    val = np.zeros(n); val[i] = tot / len(i)
            else:
                if entra:
                    tot = val.sum() or 1.0
                    val = np.zeros(n); val[i] = tot / len(i)
                val = val * (1 + np.nan_to_num(R[t], nan=0.0))
            bh[t] = val.sum() or (bh[t - 1] if t else 1.0)
        bh = bh / bh[0]
        r_bh = np.concatenate([[0.0], bh[1:] / bh[:-1] - 1])
        rel = abs(sh(r_bh) - s_ew) / abs(s_ew)
        print(f"  [{modo:<17}] retorno={100*(bh[-1]-1):>10.2f} %  "
              f"Sharpe={sh(r_bh):.4f}  delta={sh(r_bh)-s_ew:+.4f}  "
              f"rel={100*rel:.2f} %  {'<5 %' if rel < 0.05 else '>=5 % !!'}"
              f"  ratio={bh[-1]/ew[-1]:.4f}")
        out["a5_convenciones"]["lecturas"][modo] = {
            "retorno_pct": float(100 * (bh[-1] - 1)), "sharpe": sh(r_bh),
            "delta": sh(r_bh) - s_ew, "rel_pct": float(100 * rel),
            "por_debajo_del_5pct": bool(rel < 0.05),
            "ratio_sobre_ew": float(bh[-1] / ew[-1])}
    ls = out["a5_convenciones"]["lecturas"]
    cruza = (ls["crecer_primero"]["por_debajo_del_5pct"]
             != ls["repartir_primero"]["por_debajo_del_5pct"])
    out["a5_convenciones"]["el_umbral_del_5pct_discrimina"] = not cruza
    print(f"  las dos lecturas CRUZAN el umbral del 5 %: {cruza}")
    print("  => el umbral del brief NO discrimina y por tanto NO decide. Hay que")
    print("     dar las dos cifras y declarar la convencion.")
    print("  NOTA sobre la critica: el segundo agente dio 6,81 % para")
    print("  'repartir_primero'. Mi implementacion da"
          f" {ls['repartir_primero']['rel_pct']:.2f} %. No reproduzco su cifra;")
    print("  su HALLAZGO (el veredicto cruza el umbral) si se sostiene.")

    print("\n=== B-g.3 (hallazgo 13) el retardo duplicado en (c), no solo en (a) ===")
    m_ok = e > 1e-12
    m_br = np.concatenate([[False], e[:-1] > 1e-12])
    a_br = np.concatenate([[0.0], e[:-1]]) * r_ben
    da, da_br = sh(r_est) - sh(a), sh(r_est) - sh(a_br)
    dc = sh(r_est[m_ok]) - sh(r_ben[m_ok])
    dc_br = sh(r_est[m_br]) - sh(r_ben[m_br])
    print(f"  (a)  alineado      diferencial={da:+.6f}")
    print(f"  (a') del brief     diferencial={da_br:+.6f}"
          f"   el retardo mueve {da_br-da:+.6f}")
    print(f"  (c)  alineado      n={int(m_ok.sum())}  diferencial={dc:+.6f}")
    print(f"  (c') del brief     n={int(m_br.sum())}  diferencial={dc_br:+.6f}"
          f"   el retardo mueve {dc_br-dc:+.6f}")
    print(f"  el retardo pesa {abs(dc_br-dc)/abs(da_br-da):.1f}x mas en (c) que en (a)")
    print(f"  tamano de mascara: {int(m_ok.sum())} en las dos (NO cambia);"
          f" difieren en MEMBRESIA en {int((m_ok!=m_br).sum())} dias")
    print("  => decir 'el error es pequeno' con el numero de (a) y no con el de")
    print("     (c) era quedarse con la mitad favorable.")
    out["retardo"] = {"dif_a": da, "dif_a_brief": da_br, "mueve_a": da_br - da,
                      "dif_c": dc, "dif_c_brief": dc_br, "mueve_c": dc_br - dc,
                      "veces_mayor_en_c": float(abs(dc_br - dc) / abs(da_br - da)),
                      "mascara_mismo_tamano": bool(m_ok.sum() == m_br.sum()),
                      "dias_que_difieren_en_membresia": int((m_ok != m_br).sum())}

    print("\n=== B-g.4 (hallazgo 15) ¿que mide el test de permutaciones? ===")
    rng = np.random.default_rng(43)
    vals = np.array([sh(rng.permutation(e) * r_ben) for _ in range(2000)])
    s_real = sh(a)
    pct = float((vals < s_real).mean() * 100)
    z = float((s_real - vals.mean()) / vals.std(ddof=1))
    print(f"  Sharpe (a) camino REAL   {s_real:.4f}   percentil {pct:.2f} %  z {z:+.3f}")
    print("  descomposicion en media y varianza:")
    print(f"    media(e*r_b)      = {np.mean(a):.6e}")
    print(f"    E[e]*E[r_b]       = {np.mean(e)*np.mean(r_ben):.6e}"
          f"   (lo que daria la independencia)")
    print(f"    corr(e, r_b)      = {np.corrcoef(e, r_ben)[0,1]:+.6f}")
    print(f"    corr(e, |r_b|)    = {np.corrcoef(e, np.abs(r_ben))[0,1]:+.6f}")
    print(f"    sd(e*r_b) real    = {np.std(a, ddof=1):.6f}")
    sds = np.array([np.std(rng.permutation(e) * r_ben, ddof=1) for _ in range(500)])
    print(f"    sd permutada media= {sds.mean():.6f}"
          f"   -> la real es {100*(np.std(a,ddof=1)/sds.mean()-1):+.1f} %")
    print("  => el camino real NO elige dias favorables: su media es incluso algo")
    print("     PEOR que la de la independencia y corr(e, r_b) es ~0. Toda la")
    print("     ganancia de Sharpe viene de que la sd BAJA, o sea de la reduccion")
    print("     de varianza del vol-targeting, que es LITERALMENTE lo que el brief")
    print("     escribio ('le entrega al benchmark el timing de volatilidad').")
    print("     Luego la etiqueta de la v1 ('la objecion del brief apunta al")
    print("     reves') era falsa: el MECANISMO del brief es el correcto; lo que")
    print("     esta mal es su DIRECCION ('(a) favorece a Fase B'), que no.")
    out["permutaciones"] = {
        "sharpe_real": s_real, "percentil": pct, "z": z,
        "media_real": float(np.mean(a)),
        "media_independencia": float(np.mean(e) * np.mean(r_ben)),
        "corr_e_rb": float(np.corrcoef(e, r_ben)[0, 1]),
        "corr_e_abs_rb": float(np.corrcoef(e, np.abs(r_ben))[0, 1]),
        "sd_real": float(np.std(a, ddof=1)), "sd_permutada_media": float(sds.mean()),
        "lectura": "no selecciona dias; el efecto entero es reduccion de varianza"}

    json.dump(out, open("fase0_n7/b_g_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/b_g_salida.json")


if __name__ == "__main__":
    main()
