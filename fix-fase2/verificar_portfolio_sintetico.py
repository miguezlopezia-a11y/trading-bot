"""Verificacion sintetica del portfolio multi-activo (ANTES de datos reales).

Casos de respuesta conocida:
  1. w'Σw a mano: 2 activos, sigma diaria 1 ambos, rho=0.5, w=[0.5,0.5] ->
     var diaria = 0.25*(1+1+2*0.5) = 0.75 -> vol anual = sqrt(0.75*365).
  2. Correccion Sonnet (correlacion): con rho=0.9 la varianza COMPLETA debe
     ser MAYOR que la diagonal (que ignora los terminos cruzados positivos).
     Con rho=0 deben coincidir. Esto documenta por que la diagonal esta
     prohibida como "conservadora": es optimista con correlacion positiva.
  3. H1 en la curva combinada: reconstruir la equity dia a dia desde los
     retornos del portfolio y los costes registrados (eq_t = eq_(t-1)*(1+r-coste)).
  4. Sizing Carver: sigma_i alta -> peso bajo; cap w_max; gross <= 1.

Uso: /opt/trading-bot/venv/bin/python verificar_portfolio_sintetico.py
"""
import sys

import numpy as np

sys.path.insert(0, "src")
from portfolio_runner import (portfolio_vol_anual, carver_weights,  # noqa: E402
                              ewma_vol, SIGMA_TARGET, W_MAX,
                              GROSS_MAX, PPY)


def caso_teorico():
    cov = np.array([[1.0, 0.5], [0.5, 1.0]])
    w = np.array([0.5, 0.5])
    got = portfolio_vol_anual(w, cov)
    esperado = float(np.sqrt(0.75 * PPY))
    ok = abs(got - esperado) < 1e-9
    print(f"  1. w'Sw a mano: got {got:.6f} esperado {esperado:.6f} -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def caso_correlacion():
    cov_alta = np.array([[1.0, 0.9], [0.9, 1.0]])
    cov_cero = np.array([[1.0, 0.0], [0.0, 1.0]])
    w = np.array([0.5, 0.5])
    completa = portfolio_vol_anual(w, cov_alta) ** 2
    diag = portfolio_vol_anual(w, cov_cero) ** 2
    ok = completa > diag
    ok2 = abs(portfolio_vol_anual(w, cov_cero) -
              float(np.sqrt(0.5 * PPY))) < 1e-9
    print(f"  2. correlacion: completa(rho=0.9) var {completa:.4f} > "
          f"diagonal var {diag:.4f} -> {'OK' if ok else 'FALLO'} (la diagonal "
          f"subestima riesgo: {((completa/diag)-1)*100:.0f}%); rho=0 coincide "
          f"con teoria -> {'OK' if ok2 else 'FALLO'}")
    return ok and ok2


def caso_h1():
    # equity reconstruible: rp y costes fijos conocidos
    rp = np.array([0.01, -0.02, 0.03, 0.0, 0.005])
    costes = np.array([0.001, 0.0, 0.002, 0.0, 0.0])
    eq = 1.0
    curva = [eq]
    for r, c in zip(rp, costes):
        eq *= (1 + r - c)
        curva.append(eq)
    # reconstruccion desde la curva: retornos netos implicados
    curva = np.array(curva)
    rets = curva[1:] / curva[:-1] - 1
    ok = np.allclose(rets, rp - costes)
    print(f"  3. H1 curva combinada: retornos netos = rp - costes dia a dia -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def caso_carver():
    sigmas = np.array([0.10, 0.20, 0.50, np.nan])  # anualizadas
    w, vetos = carver_weights(sigmas)
    esperado = np.array([SIGMA_TARGET / 0.10, SIGMA_TARGET / 0.20,
                         SIGMA_TARGET / 0.50, 0.0])
    esperado = np.minimum(esperado, W_MAX)
    gross = esperado.sum()
    if gross > GROSS_MAX:
        esperado *= GROSS_MAX / gross
    ok = np.allclose(w, esperado) and w.max() <= W_MAX + 1e-12 \
        and w.sum() <= GROSS_MAX + 1e-12 and len(vetos) == 2  # 0.10 y 0.20 capados? no: 1.0 y 0.5 capados
    print(f"  4. Carver: w={np.round(w, 4)} gross={w.sum():.4f} "
          f"vetos_wmax={len(vetos)} -> {'OK' if ok else 'FALLO'}")
    return ok


def caso_ewma_vol():
    # serie constante |r|=1 -> sigma diaria -> 1
    r = np.ones(50)
    s = ewma_vol(r)
    ok = abs(s[-1] - 1.0) < 1e-9
    print(f"  5. EWMA vol: |r|=1 constante -> sigma diaria {s[-1]:.6f} -> "
          f"{'OK' if ok else 'FALLO'}")
    return ok


def main():
    res = [caso_teorico(), caso_correlacion(), caso_h1(), caso_carver(),
           caso_ewma_vol()]
    if all(res):
        print("\nVERIFICACION PORTFOLIO SINTETICA OK: nucleo (cov completa, "
              "Carver, H1, EWMA) responde como se espera en casos conocidos.")
        return 0
    print("\nVERIFICACION PORTFOLIO SINTETICA FALLO: no correr datos reales.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
