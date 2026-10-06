"""PASO 3 (H1): equity marked-to-market dia a dia. cash = realizado,
unrealized = valor de la posicion abierta a close[i]. equity[i] = cash +
unrealized. Invariante: equity en cada vela de cierre de trade debe ser
identica a la version anterior (sin MTM) -- solo cambia el valor intermedio
entre entrada y salida."""
import numpy as np
import pandas as pd

from indicators import sma


class Trade:
    __slots__ = ("side", "entry_date", "entry_price", "size", "stop", "target",
                 "trailing_ma_period", "exit_date", "exit_price", "reason", "pnl")

    def __init__(self, side, entry_date, entry_price, size, stop, target, trailing_ma_period):
        self.side = side
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.size = size
        self.stop = stop
        self.target = target
        self.trailing_ma_period = trailing_ma_period
        self.exit_date = None
        self.exit_price = None
        self.reason = None
        self.pnl = None


def run_backtest(df: pd.DataFrame, signals: pd.DataFrame,
                 commission: float = 0.001, slippage: float = 0.0005,
                 size_fraction: float = 0.95) -> dict:
    """Backtest event-driven, 1 posicion, costes (comision + slippage por lado).

    Orden intravela real (A4, verificado por verificar_a4_a7_cierre.py):
    1. Si en la misma vela se tocan SL y TP (long: low[i] <= stop y high[i] >=
       target; short: high[i] >= stop y low[i] <= target), el codigo evalua el
       SL PRIMERO (pessimista): la salida es siempre por stop, nunca por TP.
    2. Si la vela abre con gap a traves del nivel (long: open_[i] <= stop;
       short: open_[i] >= stop; analogo para TP), el fill es al open real
       (reason "stop_loss_gap" / "take_profit_gap"), NO al nivel de SL/TP.
    3. La senal en la vela i crea un `pending` que se rellena en open[i+1] y,
       en la MISMA iteracion i+1, se evaluan las salidas con low[i+1]/high[i+1]:
       el SL/TP PUEDE dispararse en la propia vela de entrada.
    """
    open_ = df["open"].values
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    dates = df.index

    cash = 1.0
    equity_curve = []
    trades = []
    position = None
    pending = None

    entry_long = signals["entry_long"].values
    entry_short = signals["entry_short"].values
    sl_vals = signals["stop_loss"].values
    tp_vals = signals["take_profit"].values
    trail_periods = signals["trailing_ma_period"].values
    ma_cache = {}

    for i in range(len(df)):
        if pending is not None and position is None:
            side, sl, tp, trail = pending
            pending = None
            fill = open_[i] * (1 + slippage) if side == "long" else open_[i] * (1 - slippage)
            qty = (cash * size_fraction) / fill
            position = Trade(side, dates[i], fill, qty, sl, tp, trail)

        if position is not None:
            exit_price, reason = None, None
            if position.side == "long":
                if open_[i] <= position.stop:
                    exit_price, reason = open_[i], "stop_loss_gap"
                elif low[i] <= position.stop:
                    exit_price, reason = position.stop, "stop_loss"
                elif not np.isnan(position.target) and open_[i] >= position.target:
                    exit_price, reason = open_[i], "take_profit_gap"
                elif not np.isnan(position.target) and high[i] >= position.target:
                    exit_price, reason = position.target, "take_profit"
            else:
                if open_[i] >= position.stop:
                    exit_price, reason = open_[i], "stop_loss_gap"
                elif high[i] >= position.stop:
                    exit_price, reason = position.stop, "stop_loss"
                elif not np.isnan(position.target) and open_[i] <= position.target:
                    exit_price, reason = open_[i], "take_profit_gap"
                elif not np.isnan(position.target) and low[i] <= position.target:
                    exit_price, reason = position.target, "take_profit"

            if exit_price is None and position.trailing_ma_period:
                p = position.trailing_ma_period
                if p not in ma_cache:
                    ma_cache[p] = sma(df["close"], p).values
                ma_val = ma_cache[p][i]
                if not np.isnan(ma_val):
                    if position.side == "long" and close[i] <= ma_val:
                        exit_price, reason = close[i], "trailing_ma"
                    elif position.side == "short" and close[i] >= ma_val:
                        exit_price, reason = close[i], "trailing_ma"

            if exit_price is not None:
                exit_price *= (1 - slippage) if position.side == "long" else (1 + slippage)
                position.exit_date = dates[i]
                position.exit_price = exit_price
                position.reason = reason
                direction = 1 if position.side == "long" else -1
                gross = direction * (exit_price - position.entry_price) * position.size
                cost = (position.entry_price + exit_price) * position.size * commission
                position.pnl = gross - cost
                cash += position.pnl
                trades.append(position)
                position = None

        if position is None and pending is None and i < len(df) - 1:
            if entry_long[i]:
                pending = ("long", sl_vals[i], tp_vals[i],
                          trail_periods[i] if not pd.isna(trail_periods[i]) else None)
            elif entry_short[i]:
                pending = ("short", sl_vals[i], tp_vals[i],
                          trail_periods[i] if not pd.isna(trail_periods[i]) else None)

        if position is not None:
            direction = 1 if position.side == "long" else -1
            unrealized = direction * (close[i] - position.entry_price) * position.size
        else:
            unrealized = 0.0
        equity_curve.append(cash + unrealized)

    if position is not None:
        position.exit_date = dates[-1]
        position.exit_price = close[-1] * (1 - slippage if position.side == "long" else 1 + slippage)
        position.reason = "end_of_data"
        direction = 1 if position.side == "long" else -1
        gross = direction * (position.exit_price - position.entry_price) * position.size
        cost = (position.entry_price + position.exit_price) * position.size * commission
        position.pnl = gross - cost
        cash += position.pnl
        trades.append(position)
        equity_curve[-1] = cash

    eq = pd.Series(equity_curve, index=dates)
    return {"equity": eq, "trades": trades}


def compute_metrics(equity: pd.Series, trades: list, periods_per_year: int) -> dict:
    rets = equity.pct_change().dropna()
    n = len(trades)
    wins = [t for t in trades if t.pnl > 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl <= 0))
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max

    return {
        "total_return_pct": round((equity.iloc[-1] / equity.iloc[0] - 1) * 100, 2),
        "sharpe": round((rets.mean() / rets.std() * np.sqrt(periods_per_year)), 2) if rets.std() > 0 else 0.0,
        "max_drawdown_pct": round(drawdown.min() * 100, 2),
        "trades": n,
        "win_rate_pct": round(len(wins) / n * 100, 1) if n else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "final_equity": round(equity.iloc[-1], 4),
    }
