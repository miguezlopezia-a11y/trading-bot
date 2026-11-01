"""A-3 (N6, Fase 0) — ¿Son reproducibles los tramos T1/T2/T3 publicados?

El brief lo pone como NO-GO: "Si A-3 no reproduce los tres tramos -> PARAR.
Sin eso, 4.2 no se sostiene." (4.2 = el paso que mediria Fase B en el holdout
pre-registrado T3.)

Publicado en docs/fase_b_reevaluacion_resultado.md y en
results/portfolio_walkforward_temporal.json:
  T1 Sharpe 1.33 t 2.34 DSR 0.824 IC [+0.57, +38.51]
  T2 Sharpe 1.22 t 2.49 DSR 0.772 IC [+1.13, +30.71]
  T3 Sharpe 0.57 t 1.10 DSR 0.301 IC [-5.86, +20.30]

Metodo: se corta la curva de equity congelada (results/portfolio_equity.csv)
por los tres tramos PRE-REGISTRADOS y se recalcula todo con metrica
REESCRITA A MANO (PSR/E[max_N]/AR(1)/block bootstrap desde
statistics.NormalDist y numpy). No se importa rigor_estadistico.py ni
portfolio_walkforward_temporal.py. No se re-simula el portfolio: la equity
congelada ES el objeto evaluado, y re-simularla seria reejecutar, no
reverificar.

Uso (desde fix-fase2/):  python3 -I fase0_n6/a3_tramos_t1_t2_t3.py
"""
import json
import math
import statistics

import numpy as np
import pandas as pd

PPY = 365
GAMMA_E = 0.5772156649
ND = statistics.NormalDist()

TRAMOS = [("T1_2015-2018", "2015-09-01", "2018-12-31"),
          ("T2_2019-2022", "2019-01-01", "2022-12-31"),
          ("T3_2023-fin", "2023-01-01", "2262-12-31")]
N_TRIALS = 12
VAR_TRIALS = 0.0007021947704551833
BLOCK = 21
B_BOOT = 10000
SEED = 42

PUBLICADO = {
    "T1_2015-2018": {"sharpe_anual": 1.328, "t_stat": 2.34, "dsr": 0.8244,
                     "ic": [0.57, 38.51], "n_obs_eff": 1136, "pnl_pct": 81.72},
    "T2_2019-2022": {"sharpe_anual": 1.219, "t_stat": 2.49, "dsr": 0.7719,
                     "ic": [1.13, 30.71], "n_obs_eff": 1524, "pnl_pct": 82.42},
    "T3_2023-fin": {"sharpe_anual": 0.572, "t_stat": 1.10, "dsr": 0.3008,
                    "ic": [-5.86, 20.30], "n_obs_eff": 1356, "pnl_pct": 25.95},
}


def psr_m(sharpe_per, n_obs, sr_star, skew, kurt):
    num = (sharpe_per - sr_star) * math.sqrt(n_obs - 1)
    den = math.sqrt(1 - skew * sharpe_per + (kurt - 1) / 4 * sharpe_per ** 2)
    return ND.cdf(num / den)


def sr0_m(n_trials, var_trials):
    if n_trials <= 1:
        return 0.0
    z1 = ND.inv_cdf(1 - 1.0 / n_trials)
    z2 = ND.inv_cdf(1 - 1.0 / (n_trials * math.e))
    return math.sqrt(var_trials) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def ar1_eff_m(r):
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0:
        return float(len(r))
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho = min(max(rho, -0.95), 0.95)
    return len(r) * (1 - rho) / (1 + rho)


def block_boot_ci(s, block, n_boot, func, seed):
    s = np.asarray(s, dtype=float)
    s = s[~np.isnan(s)]
    n = len(s)
    if n < block:
        return None, None, func(s)
    rng = np.random.default_rng(seed)
    nblocks = int(math.ceil(n / block))
    stats = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n, nblocks)
        idx = np.concatenate([(st + np.arange(block)) % n for st in starts])[:n]
        stats[b] = func(s[idx])
    return (float(np.percentile(stats, 2.5)),
            float(np.percentile(stats, 97.5)), float(func(s)))


def main():
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    print(f"=== A-3.0 la curva congelada ===")
    print(f"  results/portfolio_equity.csv : {len(eq)} dias, "
          f"{eq.index[0].date()} -> {eq.index[-1].date()}")
    print(f"  retornos diarios             : {len(eq.pct_change().dropna())}")
    print(f"  NO hay split train/test en la curva: es la historia entera.")
    print()

    rets_all = eq.pct_change()
    out, ok_todos = {}, True
    print("=== A-3.1 los tres tramos pre-registrados, recalculados ===")
    for i, (nombre, ini, fin) in enumerate(TRAMOS):
        mask = (eq.index >= ini) & (eq.index <= fin)
        rets = rets_all[mask].dropna()
        per = rets.values
        t_eff = int(ar1_eff_m(per))
        s_per = per.mean() / per.std() if per.std() > 0 else 0.0
        skew = float(pd.Series(per).skew())
        kurt = float(pd.Series(per).kurt() + 3)
        s0 = sr0_m(N_TRIALS, VAR_TRIALS)
        dsr_v = psr_m(s_per, t_eff, s0, skew, kurt)
        t_stat = float(s_per * math.sqrt(t_eff))
        lo, hi, _ = block_boot_ci(per, BLOCK, B_BOOT,
                                  lambda x: x.mean() * PPY * 100, SEED + i)
        eq_t = eq[mask]
        pnl = float((eq_t.iloc[-1] / eq_t.iloc[0] - 1) * 100)
        sh_an = s_per * math.sqrt(PPY)

        p = PUBLICADO[nombre]
        comp = [
            ("sharpe_anual", round(sh_an, 3), p["sharpe_anual"], 1e-3),
            ("t_stat", round(t_stat, 2), p["t_stat"], 1e-2),
            ("dsr", round(dsr_v, 4), p["dsr"], 1e-4),
            ("n_obs_eff", t_eff, p["n_obs_eff"], 0),
            ("pnl_pct", round(pnl, 2), p["pnl_pct"], 1e-2),
            ("ic_lo", round(lo, 2), p["ic"][0], 1e-2),
            ("ic_hi", round(hi, 2), p["ic"][1], 1e-2),
        ]
        print(f"  [{nombre}]  {rets.index[0].date()} -> {rets.index[-1].date()}"
              f"  ({len(per)} retornos)")
        ok_tramo = True
        for campo, mio, pub, tol in comp:
            igual = abs(mio - pub) <= tol
            ok_tramo &= igual
            print(f"    {campo:<14} mio={mio:<10} publicado={pub:<10} "
                  f"{'OK' if igual else '*** DIFIERE ***'}")
        print(f"    skew={skew:.4f} kurt_raw={kurt:.4f} SR0={s0:.5f}")
        print(f"    -> {nombre}: {'REPRODUCE' if ok_tramo else 'NO REPRODUCE'}")
        print()
        ok_todos &= ok_tramo
        out[nombre] = {"sharpe_anual": round(sh_an, 3), "t_stat": round(t_stat, 2),
                       "dsr": round(dsr_v, 4), "n_obs_eff": t_eff,
                       "ic95": [round(lo, 2), round(hi, 2)],
                       "pnl_pct": round(pnl, 2), "n_retornos": len(per),
                       "skew": skew, "kurt_raw": kurt,
                       "desde": str(rets.index[0].date()),
                       "hasta": str(rets.index[-1].date()),
                       "reproduce": bool(ok_tramo)}

    print("=== A-3.2 veredicto del NO-GO ===")
    if ok_todos:
        print("  Los TRES tramos reproducen campo a campo, incluidos los IC")
        print("  del block bootstrap (seed 42/43/44, B=10000, bloque 21).")
        print("  -> NO-GO de A-3 NO se dispara.")
    else:
        print("  Algun tramo NO reproduce -> NO-GO de A-3 DISPARADO. PARAR.")

    print()
    print("=== A-3.3 lo que estos tramos NO son ===")
    print("  Los tres salen de UNA SOLA simulacion sobre la historia completa,")
    print("  cortada despues por fecha (portfolio_walkforward_temporal.py:")
    print("  'Una sola simulacion sobre datos completos ... la equity se corta")
    print("  por tramo'). No hay entrenamiento en T1+T2 y prueba en T3:")
    print("  los parametros estan congelados a mano, no ajustados en T1+T2.")
    print("  Luego T3 es un tramo FUERA DE MUESTRA EN EL TIEMPO respecto a la")
    print("  eleccion de la regla, pero NO un holdout en el sentido de")
    print("  'ajustado en train, medido en test'. La distincion importa para")
    print("  el paso 4.2 y es el nucleo de la objecion B-a.")

    with open("fase0_n6/a3_salida.json", "w") as f:
        json.dump({"tramos": out, "reproducen_todos": bool(ok_todos)}, f, indent=2)
    print("\n-> fase0_n6/a3_salida.json")


if __name__ == "__main__":
    main()
