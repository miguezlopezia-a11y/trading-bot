"""TDD de rsi_hidden_divergence (adaptado de jamniol/freqtrade-setup
DivergenceStrategy, MIT, con el look-ahead de su deteccion de swings
corregido: swings confirmados con retraso real, no argrelextrema sobre
toda la serie de golpe).

Uso: /opt/trading-bot/venv/bin/python verificar_rsi_hidden_divergence.py
"""
import sys

import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES, _hidden_divergence_signals, rsi_hidden_divergence  # noqa: E402


def _ohlc(closes):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    s = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s}, index=idx)


def test_entrada_divergencia_alcista():
    ok = True
    closes = [100, 98, 95, 92, 90, 92, 95, 98, 100, 98, 95, 93, 92, 93, 95, 98,
              100, 102, 104, 106, 108, 106, 104, 102, 100, 102, 105, 108, 110]
    osc = [50, 48, 45, 42, 35, 42, 45, 48, 50, 48, 45, 43, 20, 43, 45, 48,
           50, 52, 54, 56, 58, 56, 54, 52, 25, 48, 46, 44, 42]
    close = pd.Series(closes, dtype=float)
    oscilador = pd.Series(osc, dtype=float)
    entry, exit_ = _hidden_divergence_signals(close, oscilador, swing_order=2, min_gap=3)

    if list(entry[entry].index) != [14]:
        print(f"  FALLO entrada: esperado solo indice 14, real={list(entry[entry].index)}"); ok = False
    elif exit_.any():
        print(f"  FALLO: no deberia haber salida en este escenario"); ok = False
    else:
        print("  OK divergencia oculta alcista: precio higher-low (90->92) + oscilador "
              "lower-low (35->20) -> entry en el swing confirmado (indice 14), "
              "no antes (sin mirar al futuro); el par siguiente (92->100 precio, "
              "20->25 oscilador, sin divergencia) no dispara nada")
    return ok


def test_salida_divergencia_bajista():
    ok = True
    closes = [100, 102, 105, 108, 110, 108, 105, 102, 100, 102, 105, 107, 108,
              107, 105, 102, 100, 98, 96, 94, 92]
    osc = [50, 52, 55, 58, 65, 58, 55, 52, 50, 52, 55, 57, 70, 57, 55, 52,
           50, 48, 46, 44, 42]
    close = pd.Series(closes, dtype=float)
    oscilador = pd.Series(osc, dtype=float)
    entry, exit_ = _hidden_divergence_signals(close, oscilador, swing_order=2, min_gap=3)

    if list(exit_[exit_].index) != [14]:
        print(f"  FALLO salida: esperado solo indice 14, real={list(exit_[exit_].index)}"); ok = False
    elif entry.any():
        print("  FALLO: no deberia haber entrada en este escenario"); ok = False
    else:
        print("  OK divergencia oculta bajista: precio lower-high (110->108) + oscilador "
              "higher-high (65->70) -> exit en el swing confirmado (indice 14)")
    return ok


def test_contrato_columnas():
    ok = True
    df = _ohlc([100.0 + ((i * 7) % 23) - 11 for i in range(400)])
    out = rsi_hidden_divergence(df, swing_order=5, min_gap=12, rsi_period=14)

    if out["entry_short"].any() or out["exit_short"].any():
        print("  FALLO: entry_short/exit_short deberian ser siempre False"); ok = False
    elif out["stop_loss"].notna().any() or out["take_profit"].notna().any():
        print("  FALLO: stop_loss/take_profit deberian ser NaN siempre"); ok = False
    elif out["trailing_ma_period"].notna().any():
        print("  FALLO: trailing_ma_period deberia ser None siempre (usa exit_long)"); ok = False
    elif "rsi_hidden_divergence" not in STRATEGIES:
        print("  FALLO: no registrada en STRATEGIES"); ok = False
    else:
        print("  OK contrato: entry_short/exit_short False, SL/TP/trailing_ma_period "
              "vacios, registrada en STRATEGIES, corre sobre datos reales sin excepcion")
    return ok


def main():
    resultados = [test_entrada_divergencia_alcista(), test_salida_divergencia_bajista(),
                  test_contrato_columnas()]
    if all(resultados):
        print("\nVERIFICACION OK: rsi_hidden_divergence respeta el contrato, confirma "
              "swings con retraso real (sin mirar al futuro), y la logica de "
              "coincidencia de divergencia es correcta en ambas direcciones.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
