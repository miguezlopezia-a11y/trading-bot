"""B-b (N6, Fase 0) — Busqueda ACTIVA de una correccion pendiente que vaya en
la direccion CONTRARIA a las dos que esta tarea aplica (recuento de N y
holdout, que bajan el veredicto de Fase B).

El brief lo ordena: "Buscarla activamente: un brief que solo encuentra pruebas
en un sentido esta mal construido."

Candidata principal, que N4 dejo medida a medias (su B-06): E[max_N] de
Bailey-LdP es el maximo esperado de N extracciones INDEPENDIENTES de N(0,V).
Los trials del expediente no son independientes: seis son el mismo parametro
barrido sobre la misma serie. Si se corrige el N por correlacion, el N efectivo
baja, el SR0 baja y el liston BAJA. Esa es la correccion contraria.

TRES estimadores, aplicados a la matriz de correlacion de los retornos diarios
de los trials. CORRECCION (hallazgos 7 y 8 del segundo agente): solo los dos
primeros son de la literatura de tests multiples; el tercero NO lo es, y es el
unico que da "Fase B pasa".
  - Cheverud-Nyholt:  N_eff = 1 + (N-1)*(1 - Var(lambda)/N)
  - Li-Ji (2005):     N_eff = sum_i [ I(lambda_i >= 1) + (lambda_i - floor(lambda_i)) ]
      La primera version de este script implemento f(x)=1 si x>=1, que TIRA la
      parte fraccionaria de todo autovalor >= 1. Mal: para lambda=5.2698 vale
      1.2698, no 1. Corregido. El error subestimaba N_eff y por tanto BAJABA el
      liston, o sea favorecia la tesis de esta objecion.
  - Kish (1965), efecto de diseno: N_eff = N / (1 + (N-1)*rho_medio)
      NO es un estimador de numero efectivo de TESTS: es el tamano muestral
      efectivo del muestreo por conglomerados, y no tiene interpretacion como
      "numero de pruebas independientes" en un estadistico de maximo. Se deja
      porque es la unica fila que da la vuelta al veredicto, y precisamente por
      eso hay que decir que su procedencia NO cubre esa conclusion.
Se dan los tres y el rango, sin elegir: elegir es de Pablo.

Uso (desde fix-fase2/):
  STAMP_CONGELADO=20261009 python3 fase0_n6/b_correccion_contraria.py
"""
import json
import math
import statistics
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES        # noqa: E402
from backtester import run_backtest      # noqa: E402

PPY = 365
GAMMA_E = 0.5772156649
ND = statistics.NormalDist()
CSV = "data/btc_usd_5y_1d.csv"
TRAIN_FRAC, WARMUP, SIZE_FRACTION = 0.6, 200, 0.05

V11 = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
       "sma_timing_50", "sma_timing_100", "sma_timing_304",
       "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
EXTRA3 = ["mean_reversion", "breakout", "trend_following"]


def psr_m(s, n, s0, sk, ku):
    num = (s - s0) * math.sqrt(n - 1)
    den = math.sqrt(1 - sk * s + (ku - 1) / 4 * s ** 2)
    return ND.cdf(num / den)


def sr0_m(n, v):
    if n <= 1:
        return 0.0
    z1, z2 = ND.inv_cdf(1 - 1.0 / n), ND.inv_cdf(1 - 1.0 / (n * math.e))
    return math.sqrt(v) * ((1 - GAMMA_E) * z1 + GAMMA_E * z2)


def liston_m(n, v, n_eff, sk, ku, conf=0.95):
    s0 = sr0_m(n, v)
    if psr_m(s0, n_eff, s0, sk, ku) >= conf:
        return s0
    lo, hi = s0, s0 + 2.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if psr_m(mid, n_eff, s0, sk, ku) >= conf:
            hi = mid
        else:
            lo = mid
    return hi


def series_fase_a():
    df = pd.read_csv(CSV, index_col=0, parse_dates=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
    split = int(len(df) * TRAIN_FRAC)
    a = max(0, split - WARMUP)
    out = {}
    for n in V11 + EXTRA3:
        sig = STRATEGIES[n](df.iloc[a:]).iloc[split - a:]
        res = run_backtest(df.iloc[split:], sig, size_fraction=SIZE_FRACTION)
        out[n] = res["equity"].pct_change().dropna()
    return out


def n_eff_estimadores(C):
    """Tres estimadores de numero efectivo de tests sobre la matriz C."""
    N = C.shape[0]
    lam = np.linalg.eigvalsh(C)
    lam = np.clip(lam, 0, None)
    # Cheverud-Nyholt
    cn = 1 + (N - 1) * (1 - np.var(lam, ddof=1) / N)
    # Li-Ji
    # Li & Ji (2005): f(x) = I(x>=1) + (x - floor(x)). Las dos piezas se SUMAN.
    lj = float(sum((1.0 if x >= 1 else 0.0) + (x - math.floor(x)) for x in lam))
    # La implementacion erronea de la primera version, para poder comparar:
    lj_malo = float(sum(1.0 if abs(x) >= 1 else abs(x) - math.floor(abs(x))
                        for x in lam))
    # media de correlacion (Kish-like)
    off = C[~np.eye(N, dtype=bool)]
    rho = float(off.mean())
    kish = N / (1 + (N - 1) * rho) if (1 + (N - 1) * rho) > 0 else float("nan")
    return {"N": N, "rho_medio": rho, "cheverud_nyholt": float(cn),
            "li_ji": lj, "li_ji_impl_erronea_v1": lj_malo, "kish": float(kish),
            "autovalores": [round(float(x), 4) for x in sorted(lam)[::-1]]}


def main():
    print("=== B-b.1 matriz de correlacion de los trials (retornos diarios OOS) ===")
    ser = series_fase_a()
    M11 = pd.DataFrame({n: ser[n] for n in V11}).dropna()
    M14 = pd.DataFrame({n: ser[n] for n in V11 + EXTRA3}).dropna()
    print(f"  ventana comun: {len(M11)} dias, "
          f"{M11.index[0].date()} -> {M11.index[-1].date()}")
    C11 = M11.corr().values
    C14 = M14.corr().values

    sma = [n for n in V11 if n.startswith("sma_timing")]
    Csma = M11[sma].corr().values
    off = Csma[~np.eye(len(sma), dtype=bool)]
    print(f"\n  Correlacion entre las SEIS sma_timing (el barrido de un solo")
    print(f"  parametro): media {off.mean():.4f}  min {off.min():.4f}  "
          f"max {off.max():.4f}")
    print("  (N4 B-06 afirmo media 0.641 / min 0.368 / max 0.861)")
    print()
    print("  Matriz completa de las 11, correlacion media fuera de la diagonal:")
    off11 = C11[~np.eye(11, dtype=bool)]
    print(f"    media {off11.mean():.4f}  min {off11.min():.4f}  "
          f"max {off11.max():.4f}")
    print()

    print("=== B-b.2 numero EFECTIVO de trials ===")
    for etq, C in (("las 11 de V(11)", C11), ("las 11 + las 3 = 14", C14)):
        e = n_eff_estimadores(C)
        print(f"  [{etq}]  N nominal = {e['N']}")
        print(f"    rho medio          : {e['rho_medio']:.4f}")
        print(f"    Cheverud-Nyholt    : {e['cheverud_nyholt']:.2f}")
        print(f"    Li-Ji (2005)       : {e['li_ji']:.2f}"
              f"   [impl. erronea v1: {e['li_ji_impl_erronea_v1']:.2f}]")
        print(f"    Kish N/(1+(N-1)rho): {e['kish']:.2f}"
              f"   <- NO es estimador de tests multiples")
        print(f"    autovalores        : {e['autovalores'][:5]} ...")
    print()

    # Parametros del objeto evaluado (muestra completa, equity congelada)
    eq = pd.read_csv("results/portfolio_equity.csv", index_col=0,
                     parse_dates=True).iloc[:, 0]
    per = eq.pct_change().dropna().values
    r = np.asarray(per)
    rho = min(max(np.corrcoef(r[:-1], r[1:])[0, 1], -0.95), 0.95)
    t_eff = int(len(r) * (1 - rho) / (1 + rho))
    sk = float(pd.Series(per).skew()); ku = float(pd.Series(per).kurt() + 3)
    V12 = 0.0007021947704551833
    V15 = 0.0015503661545655356
    obs = per.mean() / per.std() * math.sqrt(PPY)

    print("=== B-b.3 el liston con N efectivo, frente al N nominal ===")
    e11 = n_eff_estimadores(C11)
    e14 = n_eff_estimadores(C14)
    casos = [
        ("expediente, N nominal", 12, V12),
        ("N efectivo CN (11 corr.) + portfolio", e11["cheverud_nyholt"] + 1, V12),
        ("N efectivo Li-Ji (11 corr.) + portfolio", e11["li_ji"] + 1, V12),
        ("N efectivo rho-medio (11) + portfolio", e11["kish"] + 1, V12),
        ("N=15 nominal (recuento de esta tarea)", 15, V15),
        ("N efectivo CN (14 corr.) + portfolio", e14["cheverud_nyholt"] + 1, V15),
        ("N efectivo Li-Ji (14 corr.) + portfolio", e14["li_ji"] + 1, V15),
        ("N efectivo rho-medio (14) + portfolio", e14["kish"] + 1, V15),
    ]
    print(f"  objeto evaluado: T_eff={t_eff} skew={sk:.3f} kurt={ku:.3f} "
          f"Sharpe_obs={obs:.4f}")
    print(f"  {'construccion':<42} {'N':>6} {'V':>12} {'liston':>8} {'¿pasa?':>7}")
    filas = []
    for etq, N, V in casos:
        l = liston_m(N, V, t_eff, sk, ku) * math.sqrt(PPY)
        filas.append({"construccion": etq, "N": round(float(N), 2), "V": V,
                      "liston_anual": round(l, 4), "pasa": bool(obs >= l)})
        print(f"  {etq:<42} {N:>6.2f} {V:>12.8f} {l:>8.4f} {str(obs>=l):>7}")
    print()
    print("  DIRECCION: corregir N por correlacion entre trials BAJA el liston.")
    print("  Es la correccion contraria que el brief pide buscar, y existe.")
    print("  Magnitud frente a las dos que la tarea aplica:")
    base = [f for f in filas if f["construccion"].startswith("expediente")][0]["liston_anual"]
    for f in filas[1:4]:
        print(f"    {f['construccion']:<42} {f['liston_anual']-base:+.4f}")
    print(f"    recuento N=15 (en contra)                  "
          f"{[x for x in filas if x['N']==15][0]['liston_anual']-base:+.4f}")
    print()
    print("  LIMITE DECLARADO, y es grande. Corregido tras los hallazgos 7,")
    print("  8 y 13 del segundo agente:")
    print("   - Cheverud-Nyholt y Li-Ji vienen de la literatura de tests")
    print("     multiples correlacionados (SNPs). Kish NO: es efecto de diseno")
    print("     de muestreo por conglomerados, y es LA UNICA FILA que da la")
    print("     vuelta al veredicto. La procedencia alegada no cubre la")
    print("     conclusion que sostiene esta objecion.")
    print("   - EL REPO NO TRANSCRIBE ninguna nocion de N efectivo por")
    print("     correlacion (rigor_estadistico.py:17-22 y")
    print("     docs/rigor_estadistico_resultado.md). Lo que diga el paper")
    print("     sobre esto es NO VERIFICABLE: SSRN no es alcanzable (A-4). La")
    print("     v1 de este script afirmaba 'Bailey-LdP no define un N efectivo")
    print("     por correlacion', que es una afirmacion POSITIVA sobre un texto")
    print("     que no se puede leer. Retirada.")
    print("   - Aplicar estos estimadores al E[max_N] es una ANALOGIA, no un")
    print("     resultado citable. Cota de direccion, no liston alternativo.")
    print()
    print("  Y el +1 por el portfolio: A-5.7 sostiene que el trial nº12 es la")
    print("  misma regla que el nº9. Si es duplicado, bajo una correccion por")
    print("  correlacion no aporta +1 sino 0. Las dos cosas no caben juntas")
    print("  (hallazgo 8 del segundo agente). Las dos lecturas, para Kish:")
    for nn, et in ((e11["kish"] + 1, "+1 (el portfolio cuenta)"),
                   (max(e11["kish"], 1.0001), "+0 (duplicado, no cuenta)")):
        ll = liston_m(nn, V12, t_eff, sk, ku) * math.sqrt(PPY)
        print(f"    N={nn:>5.2f} liston={ll:.4f} pasa={obs >= ll}   {et}")

    with open("fase0_n6/b_salida_correlacion.json", "w") as f:
        json.dump({"corr_sma_timing": {"media": float(off.mean()),
                                       "min": float(off.min()),
                                       "max": float(off.max())},
                   "corr_11_media": float(off11.mean()),
                   "n_eff_11": e11, "n_eff_14": e14,
                   "objeto": {"T_eff": t_eff, "skew": sk, "kurt_raw": ku,
                              "sharpe_obs_anual": obs},
                   "listones": filas}, f, indent=2)
    print("\n-> fase0_n6/b_salida_correlacion.json")


if __name__ == "__main__":
    main()
