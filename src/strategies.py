"""Los 4 arquetipos del PDF + sus salidas.
Cada estrategia devuelve un DataFrame con columnas:
  - entry_long / entry_short: señal de entrada (bool)
  - stop_loss / take_profit: niveles de precio para la salida fija (float o NaN)
  - trailing_ma_period: si usa trailing stop con media móvil (int o None)

Regla de gestión de salidas (del PDF):
  - SL/TP fijos en % si la estrategia los define
  - Trailing stop con MA opcional (override del TP cuando está activo)
"""
import numpy as np
import pandas as pd

from indicators import sma, ema, rsi, macd, bollinger, adx, atr


def _crossover(fast: pd.Series, slow: pd.Series) -> pd.Series:
    return (fast > slow) & (fast.shift(1) <= slow.shift(1))


def _crossunder(fast: pd.Series, slow: pd.Series) -> pd.Series:
    return (fast < slow) & (fast.shift(1) >= slow.shift(1))


# ---------------------------------------------------------------- 1/4 Reversión a la media
def mean_reversion(df: pd.DataFrame, bb_period: int = 20, num_std: float = 2.0,
                   rsi_period: int = 14, rsi_max: float = 35.0,
                   stop_pct: float = 0.02, tp_pct: float = 0.03) -> pd.DataFrame:
    """Bandas de Bollinger + filtro RSI: compra en sobreventa extrema (rebote a la media)."""
    out = pd.DataFrame(index=df.index)
    bb = bollinger(df["close"], bb_period, num_std)
    r = rsi(df["close"], rsi_period)
    out["entry_long"] = (df["close"] < bb["bb_lower"]) & (r < rsi_max)
    out["entry_short"] = (df["close"] > bb["bb_upper"]) & (r > 100 - rsi_max)
    out["stop_loss"] = np.where(out["entry_long"], df["close"] * (1 - stop_pct),
                        np.where(out["entry_short"], df["close"] * (1 + stop_pct), np.nan))
    out["take_profit"] = np.where(out["entry_long"], df["close"] * (1 + tp_pct),
                          np.where(out["entry_short"], df["close"] * (1 - tp_pct), np.nan))
    out["trailing_ma_period"] = None
    out["regime"] = "ranging"
    return out


# ---------------------------------------------------------------- 2/4 Cruce de medias
def ma_cross(df: pd.DataFrame, fast: int = 20, slow: int = 50,
             stop_pct: float = 0.02, tp_pct: float = 0.04) -> pd.DataFrame:
    """EMA rápida cruza lenta → entra en dirección de la tendencia."""
    out = pd.DataFrame(index=df.index)
    f, s = ema(df["close"], fast), ema(df["close"], slow)
    out["entry_long"] = _crossover(f, s)
    out["entry_short"] = _crossunder(f, s)
    out["stop_loss"] = np.where(out["entry_long"] | out["entry_short"],
                                df["close"] * (1 - stop_pct), np.nan)
    out["take_profit"] = np.where(out["entry_long"] | out["entry_short"],
                                  df["close"] * (1 + tp_pct), np.nan)
    out["trailing_ma_period"] = None
    out["regime"] = "trending"
    return out


# ---------------------------------------------------------------- 3/4 Breakout
def breakout(df: pd.DataFrame, lookback: int = 20,
             stop_pct: float = 0.015, tp_pct: float = 0.045) -> pd.DataFrame:
    """Ruptura de máximo/mínimo de N períodos + filtro ADX (solo rompe con tendencia)."""
    out = pd.DataFrame(index=df.index)
    highest = df["high"].rolling(lookback).max().shift(1)
    lowest = df["low"].rolling(lookback).min().shift(1)
    adx_val = adx(df["high"], df["low"], df["close"], 14)
    trending = adx_val > 25
    out["entry_long"] = (df["close"] > highest) & trending
    out["entry_short"] = (df["close"] < lowest) & trending
    out["stop_loss"] = np.where(out["entry_long"], df["close"] * (1 - stop_pct),
                        np.where(out["entry_short"], df["close"] * (1 + stop_pct), np.nan))
    out["take_profit"] = np.where(out["entry_long"], df["close"] * (1 + tp_pct),
                          np.where(out["entry_short"], df["close"] * (1 - tp_pct), np.nan))
    out["trailing_ma_period"] = None
    out["regime"] = "trending"
    return out


# ---------------------------------------------------------------- 4/4 Seguimiento de tendencia
def trend_following(df: pd.DataFrame, fast: int = 10, slow: int = 30,
                    adx_period: int = 14, adx_min: float = 20,
                    trailing_ma: int = 20) -> pd.DataFrame:
    """Momentum con MACD + ADX como régimen. Salida: trailing stop con MA (la joya del PDF).
    Sin TP fijo — deja correr las ganancias hasta que el precio toque la MA."""
    out = pd.DataFrame(index=df.index)
    m = macd(df["close"])
    adx_val = adx(df["high"], df["low"], df["close"], adx_period)
    ema_fast, ema_slow = ema(df["close"], fast), ema(df["close"], slow)
    trending = adx_val > adx_min

    out["entry_long"] = _crossover(m["macd"], m["signal"]) & trending & (ema_fast > ema_slow)
    out["entry_short"] = _crossunder(m["macd"], m["signal"]) & trending & (ema_fast < ema_slow)

    atr_val = atr(df["high"], df["low"], df["close"], 14)
    # SL a 2 ATR de distancia (volatilidad real, no % fijo)
    out["stop_loss"] = np.where(out["entry_long"], df["close"] - 2 * atr_val,
                        np.where(out["entry_short"], df["close"] + 2 * atr_val, np.nan))
    out["take_profit"] = np.nan  # sin TP fijo: trailing MA decide
    out["trailing_ma_period"] = trailing_ma
    out["regime"] = "trending"
    return out


STRATEGIES = {
    "mean_reversion": mean_reversion,
    "ma_cross": ma_cross,
    "breakout": breakout,
    "trend_following": trend_following,
}
