"""TDD de las 3 estrategias candidatas de Opus (9 variantes via STRATEGIES).

Uso: /opt/trading-bot/venv/bin/python verificar_estrategias_candidatas.py
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES, sma_timing, tsmom, connors_rsi2  # noqa: E402
from indicators import sma, rsi  # noqa: E402


def _ohlc(closes):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    s = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s}, index=idx)


def test_sma_timing():
    ok = True
    closes = [10, 10, 10, 9, 8, 12, 13, 14, 6, 5]
    df = _ohlc(closes)
    out = sma_timing(df, period=3)

    if out["entry_short"].any():
        print("  FALLO sma_timing: entry_short deberia ser siempre False"); ok = False
    elif (out["stop_loss"].notna().any() or out["take_profit"].notna().any()):
        print("  FALLO sma_timing: stop_loss/take_profit deberian ser NaN siempre"); ok = False
    elif not (out["trailing_ma_period"] == 3).all():
        print("  FALLO sma_timing: trailing_ma_period debe ser el period pedido"); ok = False
    elif out["entry_long"].iloc[5] != True or out["entry_long"].sum() != 1:
        print(f"  FALLO sma_timing: entry_long esperado solo en indice 5, "
              f"real={out['entry_long'].tolist()}"); ok = False
    else:
        print("  OK sma_timing: entry_long solo en el cruce al alza, nunca entry_short, "
              "SL/TP NaN, trailing_ma_period=period")
    return ok


def test_tsmom():
    ok = True
    closes = [100] * 4 + [95, 90, 85, 110, 120, 80]
    df = _ohlc(closes)
    out = tsmom(df, period=3)

    if out["entry_short"].any() or out["exit_short"].any():
        print("  FALLO tsmom: entry_short/exit_short deberian ser siempre False"); ok = False
    elif out["entry_long"].iloc[7] != True or out["entry_long"].sum() != 1:
        print(f"  FALLO tsmom entry_long: real={out['entry_long'].tolist()}"); ok = False
    elif out["exit_long"].iloc[9] != True:
        print(f"  FALLO tsmom exit_long: real={out['exit_long'].tolist()}"); ok = False
    elif (out["stop_loss"].notna().any() or out["take_profit"].notna().any()
          or out["trailing_ma_period"].notna().any()):
        print("  FALLO tsmom: SL/TP/trailing_ma_period deben ser NaN/None"); ok = False
    else:
        print("  OK tsmom: entry_long solo en el cambio de signo, exit_long cuando "
              "el retorno vuelve a <=0, nunca cortos")
    return ok


def test_connors_rsi2():
    ok = True
    closes = [100 + i * 0.3 for i in range(200)]
    closes += [closes[-1] * 0.95, closes[-1] * 0.95 * 0.95]
    closes += [closes[-1] * 0.95 * 0.95 * 1.02,
               closes[-1] * 0.95 * 0.95 * 1.02 * 1.03,
               closes[-1] * 0.95 * 0.95 * 1.02 * 1.03 * 1.05]
    df = _ohlc(closes)
    out = connors_rsi2(df, sma_filter=200)

    r2 = rsi(df["close"], 2)
    filtro = sma(df["close"], 200)
    salida = sma(df["close"], 5)
    entry_esperado = ((r2 < 5) & (df["close"] > filtro)).fillna(False)
    exit_esperado = (df["close"] > salida).fillna(False)

    if out["entry_short"].any() or out["exit_short"].any():
        print("  FALLO connors_rsi2: entry_short/exit_short deberian ser siempre False"); ok = False
    elif entry_esperado.sum() == 0 or exit_esperado.sum() == 0:
        print("  FALLO escenario de prueba: no genera ninguna entrada/salida, ajustar datos"); ok = False
    elif not out["entry_long"].fillna(False).equals(entry_esperado):
        print(f"  FALLO connors_rsi2 entry_long: difiere de rsi(2)<5 & close>sma(filtro) "
              f"en {(out['entry_long'].fillna(False) != entry_esperado).sum()} filas"); ok = False
    elif not out["exit_long"].fillna(False).equals(exit_esperado):
        print(f"  FALLO connors_rsi2 exit_long: difiere de close>sma(5) "
              f"en {(out['exit_long'].fillna(False) != exit_esperado).sum()} filas"); ok = False
    elif (out["stop_loss"].notna().any() or out["take_profit"].notna().any()
          or out["trailing_ma_period"].notna().any()):
        print("  FALLO connors_rsi2: SL/TP/trailing_ma_period deben ser NaN/None"); ok = False
    else:
        print(f"  OK connors_rsi2: entry_long == rsi(2)<5 & close>sma(filtro) "
              f"({entry_esperado.sum()} filas), exit_long == close>sma(5) "
              f"({exit_esperado.sum()} filas), nunca cortos")
    return ok


def test_registro_9_variantes():
    ok = True
    esperadas = {"sma_timing_5", "sma_timing_10", "sma_timing_20", "sma_timing_50",
                 "sma_timing_100", "sma_timing_304", "tsmom_365", "tsmom_7",
                 "connors_rsi2"}
    faltan = esperadas - set(STRATEGIES.keys())
    if faltan:
        print(f"  FALLO registro: faltan en STRATEGIES: {sorted(faltan)}"); ok = False
        return ok

    df = _ohlc([100.0 + (i % 7) - 3 for i in range(320)])
    cols = {"entry_long", "entry_short", "stop_loss", "take_profit",
            "trailing_ma_period", "regime"}
    for nombre in sorted(esperadas):
        try:
            out = STRATEGIES[nombre](df)
        except Exception as e:
            print(f"  FALLO {nombre}: excepcion {e}"); ok = False; continue
        if not cols.issubset(out.columns):
            print(f"  FALLO {nombre}: faltan columnas {cols - set(out.columns)}"); ok = False
    if ok:
        print(f"  OK registro: las 9 variantes estan en STRATEGIES y devuelven "
              f"las columnas del contrato sobre datos reales")
    return ok


def main():
    resultados = [test_sma_timing(), test_tsmom(), test_connors_rsi2(),
                  test_registro_9_variantes()]
    if all(resultados):
        print("\nVERIFICACION OK: 3 funciones + 9 variantes registradas, "
              "contrato de columnas respetado.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
