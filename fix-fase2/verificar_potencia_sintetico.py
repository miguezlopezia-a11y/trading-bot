"""Verificacion sintetica paquete 2 (potencia a priori), ANTES de datos.

Caso: con N=12, V, T_eff, skew y kurtosis del proyecto, generar curvas
diarias sinteticas con Sharpe anual conocido por encima y por debajo del
umbral calculado (con cola gaussiana, margen amplio) y comprobar que el DSR
(reutilizado de rigor_estadistico) clasifica: encima -> DSR>=0.95, debajo ->
DSR<0.95. Ademas: el umbral t>3 clasifica igual con t_observado.

Sin LLM, sin red, determinista (seed fija).

Uso: /opt/trading-bot/venv/bin/python verificar_potencia_sintetico.py
"""
import sys

import numpy as np

sys.path.insert(0, "src")
from rigor_estadistico import dsr, PPY  # noqa: E402
from potencia_fase_b import sharpe_min_dsr, sharpe_min_t, T_EFF, V_TRIALS


def curva_con_sharpe(sr_anual, n, seed):
    """Retornos diarios con sigma 1% y drift = SR_anual*sigma/sqrt(PPY)."""
    rng = np.random.default_rng(seed)
    sigma_d = 0.01
    drift = sr_anual * sigma_d / np.sqrt(PPY)
    return drift + rng.normal(0, sigma_d, n)


def main():
    s_min_per, sr0 = sharpe_min_dsr(12)
    s_min_anual = s_min_per * np.sqrt(PPY)
    # margen del 20% sobre el umbral para que la clasificacion sea robusta
    encima = s_min_anual * 1.2
    debajo = s_min_anual * 0.8

    def dsr_de(sr_anual, seed):
        r = curva_con_sharpe(sr_anual, T_EFF, seed)
        per = r
        z = (per - per.mean()) / per.std()
        return dsr(per.mean() / per.std(), T_EFF, 12, V_TRIALS,
                   float(np.mean(z ** 3)), float(np.mean(z ** 4)))[0]

    d_encima = dsr_de(encima, 42)
    d_debajo = dsr_de(debajo, 43)
    ok1 = d_encima >= 0.95 and d_debajo < 0.95

    r = curva_con_sharpe(encima, T_EFF, 42)
    t_obs = r.mean() / r.std() * np.sqrt(T_EFF)
    t_umbral = 3.0
    ok2 = t_obs > t_umbral

    print(f"umbral DSR(N=12) = Sharpe anual {s_min_anual:.3f}")
    print(f"curva en {encima:.3f} -> DSR {d_encima:.4f} (esperado >=0.95)")
    print(f"curva en {debajo:.3f} -> DSR {d_debajo:.4f} (esperado <0.95)")
    print(f"curva en {encima:.3f} -> t {t_obs:.2f} (esperado >3)")
    ok = ok1 and ok2
    print(f"\nVERIFICACION POTENCIA SINTETICA {'OK' if ok else 'FALLO'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
