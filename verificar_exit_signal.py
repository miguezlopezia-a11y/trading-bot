"""Verificacion exit_long/exit_short en backtester.py (contrato ampliado,
2026-10-07, decision Pablo: desbloquea TSMOM y Connors RSI2 de las
candidatas de Opus). Columnas opcionales -- sin ellas, comportamiento
identico al de antes.

Uso: /opt/trading-bot/venv/bin/python verificar_exit_signal.py
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from backtester import run_backtest  # noqa: E402


def _df(n=10, price=100.0):
    idx = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame({"open": price, "high": price, "low": price,
                         "close": price}, index=idx)


def main():
    ok = True

    # 1) Compatibilidad: sin exit_long/exit_short, comportamiento igual que
    #    antes (solo SL/TP, sin salida -> llega a end_of_data).
    df = _df(5)
    sig = pd.DataFrame(index=df.index)
    sig["entry_long"] = [True, False, False, False, False]
    sig["entry_short"] = False
    sig["stop_loss"] = [90.0, np.nan, np.nan, np.nan, np.nan]
    sig["take_profit"] = [np.nan, np.nan, np.nan, np.nan, np.nan]
    sig["trailing_ma_period"] = None
    res = run_backtest(df, sig, size_fraction=0.05)
    if len(res["trades"]) != 1 or res["trades"][0].reason != "end_of_data":
        print(f"  FALLO compatibilidad: {[t.reason for t in res['trades']]}"); ok = False
    else:
        print("  OK sin exit_long/exit_short: comportamiento igual que antes (end_of_data)")

    # 2) exit_long se respeta cuando no hay SL/TP/trailing que disparen antes.
    df2 = _df(5)
    sig2 = pd.DataFrame(index=df2.index)
    sig2["entry_long"] = [True, False, False, False, False]
    sig2["entry_short"] = False
    sig2["stop_loss"] = np.nan
    sig2["take_profit"] = np.nan
    sig2["trailing_ma_period"] = None
    sig2["exit_long"] = [False, False, True, False, False]
    sig2["exit_short"] = False
    res2 = run_backtest(df2, sig2, size_fraction=0.05)
    if len(res2["trades"]) != 1 or res2["trades"][0].reason != "exit_signal":
        print(f"  FALLO exit_long: {[(t.reason, t.exit_date) for t in res2['trades']]}"); ok = False
    elif str(res2["trades"][0].exit_date.date()) != "2026-01-03":
        print(f"  FALLO exit_long fecha: {res2['trades'][0].exit_date}"); ok = False
    else:
        print("  OK exit_long dispara la salida en el dia señalado (sin SL/TP/trailing)")

    # 3) Prioridad: SL sigue ganando a exit_long si ambos se tocan la misma vela.
    df3 = pd.DataFrame({
        "open":  [100, 100, 100],
        "high":  [100, 100, 100],
        "low":   [100,  80, 100],
        "close": [100,  85, 100],
    }, index=pd.date_range("2026-01-01", periods=3, freq="D"))
    sig3 = pd.DataFrame(index=df3.index)
    sig3["entry_long"] = [True, False, False]
    sig3["entry_short"] = False
    sig3["stop_loss"] = [90.0, np.nan, np.nan]
    sig3["take_profit"] = np.nan
    sig3["trailing_ma_period"] = None
    sig3["exit_long"] = [False, True, False]  # misma vela que toca el SL
    sig3["exit_short"] = False
    res3 = run_backtest(df3, sig3, size_fraction=0.05)
    if len(res3["trades"]) != 1 or res3["trades"][0].reason != "stop_loss":
        print(f"  FALLO prioridad: {[t.reason for t in res3['trades']]}"); ok = False
    else:
        print("  OK prioridad: SL sigue ganando a exit_signal en la misma vela")

    # 4) exit_short simetrico para posiciones cortas.
    df4 = _df(5)
    sig4 = pd.DataFrame(index=df4.index)
    sig4["entry_long"] = False
    sig4["entry_short"] = [True, False, False, False, False]
    sig4["stop_loss"] = np.nan
    sig4["take_profit"] = np.nan
    sig4["trailing_ma_period"] = None
    sig4["exit_long"] = False
    sig4["exit_short"] = [False, False, False, True, False]
    res4 = run_backtest(df4, sig4, size_fraction=0.05)
    if len(res4["trades"]) != 1 or res4["trades"][0].reason != "exit_signal":
        print(f"  FALLO exit_short: {[t.reason for t in res4['trades']]}"); ok = False
    else:
        print("  OK exit_short simetrico para posiciones cortas")

    if ok:
        print("\nVERIFICACION OK: exit_long/exit_short funcionan, con la prioridad "
              "correcta (SL/TP > trailing_ma > exit_signal) y compatibilidad total "
              "con estrategias que no las usan.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
