"""Test unitario de DSR y block bootstrap sobre casos de respuesta conocida.

Se ejecuta ANTES de los datos reales. Casos:
  1. VALIDACION CRUZADA del paper: ejemplo impreso de Bailey & López de Prado
     (2014): sharpe diario 0.15811388, T=1250, N=100, V=0.002, skew -3,
     kurt 10 -> SR0 0.1132, DSR 0.9004 (reproducido por el paquete
     deflated_sharpe, daru.finance/projects/deflated-sharpe).
  2. Ruido puro: 200 corpus de N=100 series sin skill (seed fija); el mejor
     Sharpe seleccionado debe ser rechazado por DSR en la gran mayoria
     (>90% segun la literatura; con seed fija, assert >85% para no hacer el
     test fragil).
  3. Edge inyectado: serie con drift fuerte (SR diario 0.15, T=1250, N=1) ->
     PSR vs 0 y DSR(N=1) altos (>0.95).
  4. Block bootstrap: ruido puro -> IC95 del retorno medio cruza el 0;
     edge inyectado -> IC no cruza el 0 (seed fija).

Uso: /opt/trading-bot/venv/bin/python verificar_rigor_sintetico.py
"""
import sys

import numpy as np

sys.path.insert(0, "src")
from rigor_estadistico import (dsr, psr, expected_max_sharpe,  # noqa: E402
                               block_bootstrap_ci, PPY)


def caso_paper():
    dsr_val, sr0 = dsr(sharpe_per=0.15811388, n_obs=1250, n_trials=100,
                       var_trials=0.002, skew=-3.0, kurt=10.0)
    ok = abs(sr0 - 0.1132) < 5e-4 and abs(dsr_val - 0.9004) < 5e-3
    print(f"  1. ejemplo paper: SR0={sr0:.6f} (esperado 0.1132) "
          f"DSR={dsr_val:.6f} (esperado 0.9004) -> {'OK' if ok else 'FALLO'}")
    return ok


def ruido_puro():
    rng = np.random.default_rng(7)
    rechazados = 0
    corpus = 200
    for _ in range(corpus):
        rets = rng.normal(0, 1, (100, 1250))
        sharpes = rets.mean(axis=1) / rets.std(axis=1)
        best = int(np.argmax(sharpes))
        s = rets[best]
        v = float(sharpes.var(ddof=1))
        d, _ = dsr(sharpes[best], 1250, 100, v,
                   float(np.mean(((s - s.mean()) / s.std()) ** 3)),
                   float(np.mean(((s - s.mean()) / s.std()) ** 4)))
        if d < 0.95:
            rechazados += 1
    frac = rechazados / corpus
    ok = frac > 0.85
    print(f"  2. ruido puro (N=100, 200 corpus): DSR rechazo al mejor en "
          f"{rechazados}/{corpus} ({frac:.0%}) -> {'OK' if ok else 'FALLO'}")
    return ok


def edge_inyectado():
    rng = np.random.default_rng(11)
    s = 0.15 + rng.normal(0, 1, 1250)  # drift diario 0.15 sigma = SR 0.15
    per = s
    z = (per - per.mean()) / per.std()
    p = psr(per.mean() / per.std(), 1250, 0.0, float(z.mean() ** 3 * 0 + np.mean(z ** 3)),
            float(np.mean(z ** 4)))
    d, _ = dsr(per.mean() / per.std(), 1250, 1, 1e-6, float(np.mean(z ** 3)),
               float(np.mean(z ** 4)))
    ok = p > 0.95 and d > 0.95
    print(f"  3. edge inyectado (SR diario 0.15, T=1250): PSR(0)={p:.4f} "
          f"DSR(N=1)={d:.4f} -> {'OK' if ok else 'FALLO'}")
    return ok


def bootstrap():
    # Para UNA serie de ruido, "el IC cruza 0" no es determinista (~5% de
    # falsos positivos) — el test correcto es frecuentista con seed fija.
    rng = np.random.default_rng(3)
    falsos_pos = 0
    series = 100
    for _ in range(series):
        ruido = rng.normal(0, 1, 1000)
        lo, hi, _ = block_bootstrap_ci(ruido, 21, 2000, lambda x: x.mean(), 5)
        if not (lo < 0 < hi):
            falsos_pos += 1
    frac_fp = falsos_pos / series
    cruza = frac_fp <= 0.15  # esperado ~5%; tolerancia para no hacerlo fragil
    edge = 0.05 + rng.normal(0, 1, 1000)
    lo2, hi2, pt2 = block_bootstrap_ci(edge, 21, 5000, lambda x: x.mean(), 6)
    no_cruza = lo2 > 0
    ok = cruza and no_cruza
    print(f"  4. block bootstrap: ruido puro x{series}: IC sin cruzar 0 en "
          f"{falsos_pos} ({frac_fp:.0%}, esperado ~5%) -> {'OK' if cruza else 'FALLO'}; "
          f"edge IC95 [{lo2:+.4f},{hi2:+.4f}] punto {pt2:+.4f} no cruza -> "
          f"{'OK' if no_cruza else 'FALLO'}")
    return ok


def main():
    resultados = [caso_paper(), ruido_puro(), edge_inyectado(), bootstrap()]
    if all(resultados):
        print("\nVERIFICACION SINTETICA OK: DSR y bootstrap responden como se "
              "espera en casos de respuesta conocida.")
        return 0
    print("\nVERIFICACION SINTETICA FALLO: no correr datos reales.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
