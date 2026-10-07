"""Los 4 arquetipos del PDF + sus salidas.
Cada estrategia devuelve un DataFrame con columnas:
  - entry_long / entry_short: señal de entrada (bool)
  - stop_loss / take_profit: niveles de precio para la salida fija (float o NaN)
  - trailing_ma_period: si usa trailing stop con media móvil (int o None)

Regla de gestión de salidas (del PDF):
  - SL/TP fijos en % si la estrategia los define
  - Trailing stop con MA opcional (override del TP cuando está activo)
"""
from functools import partial

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


# ---------------------------------------------------------------- 5/7 SMA-timing (Faber 2007 + Detzel et al. 2021)
def sma_timing(df: pd.DataFrame, period: int = 100) -> pd.DataFrame:
    """Largo si close cruza por encima de sma(period); fuera si cae por debajo (trailing_ma_period)."""
    out = pd.DataFrame(index=df.index)
    ma = sma(df["close"], period)
    out["entry_long"] = (df["close"] > ma) & (df["close"].shift(1) <= ma.shift(1))
    out["entry_short"] = False
    out["stop_loss"] = np.nan
    out["take_profit"] = np.nan
    out["trailing_ma_period"] = period
    out["regime"] = "trending"
    return out


# ---------------------------------------------------------------- 6/7 TSMOM (Moskowitz/Ooi/Pedersen 2012 + Liu/Tsyvinski 2021)
def tsmom(df: pd.DataFrame, period: int = 365) -> pd.DataFrame:
    """Adaptacion spot (sin cortos): largo en el cambio de signo del retorno de N velas, fuera cuando vuelve a <=0."""
    out = pd.DataFrame(index=df.index)
    ret_n = df["close"].pct_change(period)
    out["entry_long"] = (ret_n > 0) & (ret_n.shift(1) <= 0)
    out["entry_short"] = False
    out["exit_long"] = ret_n <= 0
    out["exit_short"] = False
    out["stop_loss"] = np.nan
    out["take_profit"] = np.nan
    out["trailing_ma_period"] = None
    out["regime"] = "trending"
    return out


# ---------------------------------------------------------------- 7/7 Connors RSI(2) — prueba de falsacion
def connors_rsi2(df: pd.DataFrame, sma_filter: int = 290) -> pd.DataFrame:
    """Largo si rsi(2)<5 con close por encima del filtro de tendencia; fuera al recuperar sobre sma(5)."""
    out = pd.DataFrame(index=df.index)
    r2 = rsi(df["close"], 2)
    filtro = sma(df["close"], sma_filter)
    salida = sma(df["close"], 5)
    out["entry_long"] = (r2 < 5) & (df["close"] > filtro)
    out["entry_short"] = False
    out["exit_long"] = df["close"] > salida
    out["exit_short"] = False
    out["stop_loss"] = np.nan
    out["take_profit"] = np.nan
    out["trailing_ma_period"] = None
    out["regime"] = "ranging"
    return out


# ---------------------------------------------------------------- 8/8 RSI hidden divergence
# Adaptado de jamniol/freqtrade-setup (DivergenceStrategy, licencia MIT,
# github.com/jamniol/freqtrade-setup) -- idea real de practicante (divergencia
# oculta precio/RSI), NO el codigo tal cual: su deteccion de swings con
# argrelextrema sobre toda la serie corre riesgo de look-ahead (el propio
# ranking freqle.org marca "2 potential lookahead patterns" en esa entrada), y
# su ROI (62.4% inicial) es un valor de hyperopt sobre su propio dataset, no
# una regla transferible. Aqui: un solo oscilador (RSI, no 3 en confluencia,
# mas simple y auditable), swing confirmado con el retraso real que exige
# detectarlo (rolling centrado + shift(swing_order) -- no se usa la senal
# hasta que de verdad se podria haber confirmado en tiempo real).
def _swings_confirmados(series: pd.Series, order: int, min_gap: int, n: int):
    roll = series.rolling(2 * order + 1, center=True)
    extremo_min = roll.min()
    extremo_max = roll.max()
    es_min = (series == extremo_min) & extremo_min.notna()
    es_max = (series == extremo_max) & extremo_max.notna()

    def _filtrar(mask):
        posiciones = np.where(mask.values)[0]
        filtradas = []
        for p in posiciones:
            if not filtradas or p - filtradas[-1] >= min_gap:
                filtradas.append(p)
        return [(p, p + order) for p in filtradas if p + order < n]

    return _filtrar(es_min), _filtrar(es_max)


def _hidden_divergence_signals(close: pd.Series, oscilador: pd.Series,
                               swing_order: int, min_gap: int):
    """Logica pura, testeable sin pasar por rsi() real: entry/exit booleans
    (listas alineadas con close.index) para divergencia oculta alcista/bajista."""
    n = len(close)
    entry = pd.Series(False, index=close.index)
    exit_ = pd.Series(False, index=close.index)
    precio_lows, precio_highs = _swings_confirmados(close, swing_order, min_gap, n)
    osc_lows, osc_highs = _swings_confirmados(oscilador, swing_order, min_gap, n)

    for i in range(1, len(precio_lows)):
        p1, _ = precio_lows[i - 1]
        p2, conf2 = precio_lows[i]
        if close.iloc[p2] <= close.iloc[p1]:
            continue
        ventana = [oscilador.iloc[p] for p, _ in osc_lows if p1 <= p <= p2]
        if len(ventana) >= 2 and ventana[-1] < ventana[0]:
            entry.iloc[conf2] = True

    for i in range(1, len(precio_highs)):
        p1, _ = precio_highs[i - 1]
        p2, conf2 = precio_highs[i]
        if close.iloc[p2] >= close.iloc[p1]:
            continue
        ventana = [oscilador.iloc[p] for p, _ in osc_highs if p1 <= p <= p2]
        if len(ventana) >= 2 and ventana[-1] > ventana[0]:
            exit_.iloc[conf2] = True

    return entry, exit_


def rsi_hidden_divergence(df: pd.DataFrame, swing_order: int = 5, min_gap: int = 12,
                          rsi_period: int = 14) -> pd.DataFrame:
    """Divergencia oculta alcista (precio higher-low, RSI lower-low) -> largo.
    Divergencia oculta bajista (precio lower-high, RSI higher-high) -> sale.
    Swings confirmados con retraso real (sin mirar al futuro)."""
    out = pd.DataFrame(index=df.index)
    out["entry_short"] = False
    out["exit_short"] = False
    out["stop_loss"] = np.nan
    out["take_profit"] = np.nan
    out["trailing_ma_period"] = None
    out["regime"] = "ranging"

    close = df["close"]
    r = rsi(close, rsi_period)
    out["entry_long"], out["exit_long"] = _hidden_divergence_signals(
        close, r, swing_order, min_gap)
    return out


STRATEGIES = {
    "mean_reversion": mean_reversion,
    "ma_cross": ma_cross,
    "breakout": breakout,
    "trend_following": trend_following,
    "sma_timing_5": partial(sma_timing, period=5),
    "sma_timing_10": partial(sma_timing, period=10),
    "sma_timing_20": partial(sma_timing, period=20),
    "sma_timing_50": partial(sma_timing, period=50),
    "sma_timing_100": partial(sma_timing, period=100),
    "sma_timing_304": partial(sma_timing, period=304),
    "tsmom_365": partial(tsmom, period=365),
    "tsmom_7": partial(tsmom, period=7),
    "connors_rsi2": connors_rsi2,
    "rsi_hidden_divergence": rsi_hidden_divergence,
}
