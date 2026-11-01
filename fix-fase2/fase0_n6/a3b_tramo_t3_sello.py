"""A-3b (N6, Fase 0) — Por que T3 no reproduce desde la equity congelada, y
si reproduce con el sello de datos que el propio documento declara.

A-3 encontro que T1 y T2 reproducen campo a campo desde
results/portfolio_equity.csv, y que T3 NO: n_obs_eff 1354 vs 1356 publicado,
Sharpe 0.573 vs 0.572, DSR 0.3013 vs 0.3008, IC [-5.82,+20.35] vs
[-5.86,+20.30].

Hipotesis: la equity congelada en results/ es del run con sello 20261007
(acaba 2026-10-07), y el walk-forward temporal publicado se corrio con el
sello 20261009 (+2 velas), tal como dice docs/fase_b_reevaluacion_resultado.md:8.
T1 y T2 no se enteran porque acaban en 2018 y 2022; T3 es "2023-01-01 -> fin
datos" y si.

Se re-simula con STAMP_CONGELADO=20261009 importando portfolio_runner SIN
editarlo (el brief lo permite explicitamente: "se importa y se llama desde el
directorio de la tarea; no se edita"). No se descarga nada: PERMITIR_DESCARGA
se deja sin poner, asi que el loader parcheado por N1 falla en duro si falta
un CSV.

Uso (desde fix-fase2/):
  STAMP_CONGELADO=20261009 python3 fase0_n6/a3b_tramo_t3_sello.py
"""
import json
import math
import os
import statistics
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")

PPY = 365
GAMMA_E = 0.5772156649
ND = statistics.NormalDist()
N_TRIALS = 12
VAR_TRIALS = 0.0007021947704551833
BLOCK, B_BOOT, SEED = 21, 10000, 42


def psr_m(s, n, s0, sk, ku):
    num = (s - s0) * math.sqrt(n - 1)
    den = math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2)
    return ND.cdf(num / den)


def sr0_m(n, v):
    if n <= 1:
        return 0.0
    z1, z2 = ND.inv_cdf(1 - 1.0 / n), ND.inv_cdf(1 - 1.0 / (n * math.e))
    return math.sqrt(v) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def ar1_eff_m(r):
    r = np.asarray(r, dtype=float); r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0:
        return float(len(r))
    rho = min(max(np.corrcoef(r[:-1], r[1:])[0, 1], -0.95), 0.95)
    return len(r) * (1 - rho) / (1 + rho)


def block_boot_ci(s, block, n_boot, func, seed):
    s = np.asarray(s, dtype=float); s = s[~np.isnan(s)]
    n = len(s)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    st = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n, nb)
        idx = np.concatenate([(x + np.arange(block)) % n for x in starts])[:n]
        st[b] = func(s[idx])
    return float(np.percentile(st, 2.5)), float(np.percentile(st, 97.5))


def metricas_tramo(eq, ini, fin, seed):
    rets_all = eq.pct_change()
    mask = (eq.index >= ini) & (eq.index <= fin)
    per = rets_all[mask].dropna().values
    t_eff = int(ar1_eff_m(per))
    s_per = per.mean() / per.std()
    sk = float(pd.Series(per).skew()); ku = float(pd.Series(per).kurt() + 3)
    s0 = sr0_m(N_TRIALS, VAR_TRIALS)
    lo, hi = block_boot_ci(per, BLOCK, B_BOOT,
                           lambda x: x.mean() * PPY * 100, seed)
    eqt = eq[mask]
    return {"n_retornos": len(per), "n_obs_eff": t_eff,
            "sharpe_anual": round(s_per * math.sqrt(PPY), 3),
            "t_stat": round(float(s_per * math.sqrt(t_eff)), 2),
            "dsr": round(psr_m(s_per, t_eff, s0, sk, ku), 4),
            "ic95": [round(lo, 2), round(hi, 2)],
            "pnl_pct": round(float((eqt.iloc[-1] / eqt.iloc[0] - 1) * 100), 2)}


def main():
    stamp = os.environ.get("STAMP_CONGELADO")
    print(f"=== A-3b: STAMP_CONGELADO = {stamp!r} ===")
    print(f"    PERMITIR_DESCARGA        = "
          f"{os.environ.get('PERMITIR_DESCARGA')!r}  (si no es '1', el loader")
    print(f"    parcheado por N1 falla EN DURO en vez de descargar)")
    print()

    from portfolio_runner import load_or_download, simulate  # noqa: E402
    datos = load_or_download()
    res = simulate(datos)
    eq = res["equity"]
    print(f"  equity re-simulada: {len(eq)} dias, "
          f"{eq.index[0].date()} -> {eq.index[-1].date()}")

    eq_congelada = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                               parse_dates=True).iloc[:, 0]
    print(f"  equity en results/: {len(eq_congelada)} dias, "
          f"{eq_congelada.index[0].date()} -> {eq_congelada.index[-1].date()}")
    comun = eq.index.intersection(eq_congelada.index)
    d = (eq.reindex(comun) - eq_congelada.reindex(comun)).abs().max()
    print(f"  max |diferencia| en las {len(comun)} fechas comunes: {d:.3e}")
    print()

    PUB = {"T1_2015-2018": {"sharpe_anual": 1.328, "t_stat": 2.34, "dsr": 0.8244,
                            "ic95": [0.57, 38.51], "n_obs_eff": 1136, "pnl_pct": 81.72},
           "T2_2019-2022": {"sharpe_anual": 1.219, "t_stat": 2.49, "dsr": 0.7719,
                            "ic95": [1.13, 30.71], "n_obs_eff": 1524, "pnl_pct": 82.42},
           "T3_2023-fin": {"sharpe_anual": 0.572, "t_stat": 1.10, "dsr": 0.3008,
                           "ic95": [-5.86, 20.30], "n_obs_eff": 1356, "pnl_pct": 25.95}}
    TR = [("T1_2015-2018", "2015-09-01", "2018-12-31"),
          ("T2_2019-2022", "2019-01-01", "2022-12-31"),
          ("T3_2023-fin", "2023-01-01", "2262-12-31")]

    out, todos = {}, True
    for i, (n, a, b) in enumerate(TR):
        m = metricas_tramo(eq, a, b, SEED + i)
        p = PUB[n]
        ok = all(
            (m[k] == p[k]) if k == "n_obs_eff"
            else (m[k] == p[k]) if k == "ic95"
            else abs(m[k] - p[k]) <= 1e-9
            for k in p)
        todos &= ok
        print(f"  [{n}] {'REPRODUCE' if ok else '*** NO REPRODUCE ***'}")
        for k in p:
            print(f"    {k:<14} mio={str(m[k]):<16} publicado={str(p[k]):<16}"
                  f" {'OK' if (m[k] == p[k] if k in ('n_obs_eff','ic95') else abs(m[k]-p[k])<=1e-9) else '*** DIFIERE ***'}")
        out[n] = {"mio": m, "publicado": p, "reproduce": bool(ok)}
        print()

    print("=== A-3b veredicto ===")
    if todos:
        print(f"  Con el sello {stamp} los TRES tramos reproducen campo a campo,")
        print("  IC del bootstrap incluidos. Hipotesis CONFIRMADA: la equity")
        print("  congelada en results/ es del run 20261007 y el walk-forward")
        print("  publicado es del 20261009.")
        print("  -> NO-GO de A-3 NO se dispara. Pero T3 solo es reproducible")
        print("     RE-SIMULANDO, no desde el fichero congelado del repo.")
    else:
        print("  Siguen sin reproducir -> NO-GO de A-3 DISPARADO.")

    with open(f"fase0_n6/a3b_salida_{stamp}.json", "w") as f:
        json.dump({"stamp": stamp, "n_dias_equity": len(eq),
                   "ultima_fecha": str(eq.index[-1].date()),
                   "tramos": out, "reproducen_todos": bool(todos)}, f, indent=2)
    print(f"\n-> fase0_n6/a3b_salida_{stamp}.json")


if __name__ == "__main__":
    main()
