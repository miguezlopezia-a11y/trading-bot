"""A4/A7 — Cierre de deuda de auditoria Fase 1.

Test de regresion del orden intravela real de run_backtest (copia de trabajo
/root/trading-bot-fix-fase2/, NO produccion). Se espera que PASE: el codigo
ya implementa el comportamiento; este test lo ata.

Casos:
  1. Long, SL y TP tocados en la misma vela  -> sale por SL (pessimista).
  2. Short, SL y TP tocados en la misma vela -> sale por SL (pessimista).
  3. Long con gap a traves del SL (open < stop) -> fill al open, razon
     "stop_loss_gap".

Uso: /opt/trading-bot/venv/bin/python verificar_a4_a7_cierre.py
     (desde el directorio de la copia de trabajo)
"""
import sys
import pandas as pd

sys.path.insert(0, "src")
from backtester import run_backtest  # noqa: E402

SLIPPAGE = 0.0005


def make_frames(candles, side, stop, target):
    """candles: lista de tuplas (open, high, low, close). La vela 0 emite la senal."""
    df = pd.DataFrame(candles, columns=["open", "high", "low", "close"],
                      index=pd.date_range("2026-01-01", periods=len(candles), freq="D"))
    df["volume"] = 1.0
    n = len(candles)
    signals = pd.DataFrame({
        "entry_long": [side == "long"] + [False] * (n - 1),
        "entry_short": [side == "short"] + [False] * (n - 1),
        "stop_loss": [stop] * n,
        "take_profit": [target] * n,
        "trailing_ma_period": [None] * n,
    }, index=df.index)
    return df, signals


def check(name, trades, expected_reason, expected_fill):
    assert len(trades) == 1, f"{name}: se esperaba 1 trade, hay {len(trades)}"
    t = trades[0]
    assert t.reason == expected_reason, \
        f"{name}: razon {t.reason!r} != {expected_reason!r}"
    assert abs(t.exit_price - expected_fill) < 1e-9, \
        f"{name}: fill {t.exit_price} != {expected_fill} (esperado {expected_fill})"
    print(f"  OK {name}: razon={t.reason!r} fill={t.exit_price:.6f} "
          f"(esperado {expected_fill:.6f})")


def main():
    ok = True
    try:
        # Caso 1: long, SL=95 y TP=105 tocados en la misma vela de entrada.
        # Vela 1 (entrada): open=100, low=94 (<=SL), high=106 (>=TP).
        df, sig = make_frames([(100, 101, 99, 100), (100, 106, 94, 100)], "long", 95, 105)
        res = run_backtest(df, sig)
        check("long SL+TP misma vela -> SL", res["trades"], "stop_loss",
              95 * (1 - SLIPPAGE))

        # Caso 2: short, SL=105 y TP=95 tocados en la misma vela de entrada.
        # Vela 1 (entrada): open=100, high=106 (>=SL), low=94 (<=TP).
        df, sig = make_frames([(100, 101, 99, 100), (100, 106, 94, 100)], "short", 105, 95)
        res = run_backtest(df, sig)
        check("short SL+TP misma vela -> SL", res["trades"], "stop_loss",
              105 * (1 + SLIPPAGE))

        # Caso 3: long con gap a traves del SL. Vela 1 abre en 90 (< SL=95),
        # high=99 (< TP=105): sin ambiguedad, el gap manda -> fill al open.
        df, sig = make_frames([(100, 101, 99, 100), (90, 99, 89, 95)], "long", 95, 105)
        res = run_backtest(df, sig)
        check("long gap a traves del SL -> open", res["trades"], "stop_loss_gap",
              90 * (1 - SLIPPAGE))
    except AssertionError as e:
        print(f"  FALLO: {e}")
        ok = False

    if ok:
        print("\nA4 OK: los 3 casos sinteticos pasan (orden intravela documentado = real).")
        return 0
    print("\nA4 FALLO: el codigo no hace lo documentado. PARAR y reportar.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
