"""Paquete 2 — Potencia estadistica formal A PRIORI (lo que se debio hacer
antes de la Fase A: regla de proyecto a partir de ahora).

Pregunta: con T_eff=4336, skew=1.037, curtosis raw=31.999, N=12 trials y
V=0.0007022 (Sharpe diario across-trial), que Sharpe anual minimo exige
DSR >= 0.95? Y para t > 3? ¿Es plausible cerrar la brecha desde 1.008?

Metodo ANALITICO (sin backtests nuevos): invertir la PSR de Bailey-LdP
(reutilizada de rigor_estadistico.py — no reimplementada): el Sharpe minimo
es el menor SR con PSR(SR0) >= 0.95, resuelto por biseccion sobre la
correccion de Mertens. Para t>3: SR_min_per = 3/sqrt(T_eff) (t = SR*sqrt(T)).

Salida: results/potencia_fase_b.json con tabla N x {1,5,12,50,100}.

Uso: /opt/trading-bot/venv/bin/python src/potencia_fase_b.py
"""
import json
import sys

import numpy as np

sys.path.insert(0, "src")
from rigor_estadistico import psr, expected_max_sharpe, PPY  # noqa: E402

T_EFF = 4336
SKEW = 1.037
KURT = 31.999
V_TRIALS = 0.0007021947704551833
Z95 = 1.6448536269514722
N_TABLA = [1, 5, 12, 50, 100]
SHARPE_OBSERVADO = 1.008


def sharpe_min_dsr(n_trials, var_trials=V_TRIALS, n_eff=T_EFF,
                   skew=SKEW, kurt=KURT, conf=0.95):
    """Menor Sharpe PERIODO con PSR(SR0) >= conf. Biseccion en [sr0, sr0+1]."""
    sr0, _ = expected_max_sharpe(n_trials, var_trials)
    if psr(sr0, n_eff, sr0, skew, kurt) >= conf:
        return sr0, sr0
    lo, hi = sr0, sr0 + 2.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if psr(mid, n_eff, sr0, skew, kurt) >= conf:
            hi = mid
        else:
            lo = mid
    return hi, sr0


def sharpe_min_t(n_eff=T_EFF):
    """Sharpe periodo minimo para t>3: 3/sqrt(T_eff)."""
    return 3.0 / np.sqrt(n_eff)


def main():
    filas = []
    for n in N_TABLA:
        s_min_per, sr0 = sharpe_min_dsr(n)
        s_min_anual = s_min_per * np.sqrt(PPY)
        filas.append({"N": n, "sr0_per": round(sr0, 5),
                      "sharpe_min_dsr_anual": round(float(s_min_anual), 3)})
        print(f"N={n:>3}: SR0={sr0:.5f} (diario)  Sharpe min para DSR>=0.95: "
              f"{s_min_anual:.3f} (anual)")
    s_t_per = sharpe_min_t()
    print(f"\nSharpe min para t>3: {s_t_per * np.sqrt(PPY):.3f} (anual) "
          f"[t = SR*sqrt(T_eff), T_eff={T_EFF}]")
    brecha = filas[2]["sharpe_min_dsr_anual"] - SHARPE_OBSERVADO
    print(f"Sharpe observado Fase B: {SHARPE_OBSERVADO} | brecha vs umbral "
          f"N=12: {brecha:+.3f}")
    out = {"T_eff": T_EFF, "skew": SKEW, "kurt_raw": KURT,
           "var_trials": V_TRIALS, "confianza_dsr": 0.95,
           "umbral_t": 3, "sharpe_observado": SHARPE_OBSERVADO,
           "sharpe_min_t_anual": round(float(s_t_per * np.sqrt(PPY)), 3),
           "tabla": filas,
           "brecha_dsr_n12": round(float(brecha), 3)}
    with open("results/potencia_fase_b.json", "w") as f:
        json.dump(out, f, indent=2)
    print("-> results/potencia_fase_b.json guardado")


if __name__ == "__main__":
    main()
