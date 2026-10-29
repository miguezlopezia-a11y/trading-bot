import sys
sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from indicators import sma, ema, rsi, macd, bollinger, stochastic, atr, adx
import yfinance as yf

df = yf.download("BTC-USD", period="2y", interval="1d", auto_adjust=True, progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
c, h, l = df["close"].values, df["high"].values, df["low"].values
n = len(df)


def ref_sma(x, p):
    out = np.full(n, np.nan)
    for i in range(p - 1, n):
        out[i] = np.mean(x[i - p + 1:i + 1])
    return out


def ref_ema(x, p):
    alpha = 2 / (p + 1)
    out = np.full(n, np.nan)
    out[0] = x[0]
    for i in range(1, n):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def ref_rsi(x, p=14):
    out = np.full(n, np.nan)
    gains = np.full(n, np.nan)
    losses = np.full(n, np.nan)
    avg_gain = avg_loss = None
    for i in range(1, n):
        delta = x[i] - x[i - 1]
        g = max(delta, 0.0)
        ls = max(-delta, 0.0)
        if avg_gain is None:
            avg_gain, avg_loss = g, ls
        else:
            avg_gain = (avg_gain * (p - 1) + g) / p
            avg_loss = (avg_loss * (p - 1) + ls) / p
        rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
        out[i] = 100 - 100 / (1 + rs)
    return out


def ref_true_range(h, l, c):
    tr = np.full(n, np.nan)
    tr[0] = h[0] - l[0]
    for i in range(1, n):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    return tr


def ref_atr(h, l, c, p=14):
    tr = ref_true_range(h, l, c)
    out = np.full(n, np.nan)
    out[0] = tr[0]
    for i in range(1, n):
        out[i] = (out[i - 1] * (p - 1) + tr[i]) / p
    return out


def ref_bollinger(x, p=20, k=2.0):
    mid = ref_sma(x, p)
    out_up = np.full(n, np.nan)
    out_lo = np.full(n, np.nan)
    for i in range(p - 1, n):
        std = np.std(x[i - p + 1:i + 1], ddof=0)
        out_up[i] = mid[i] + k * std
        out_lo[i] = mid[i] - k * std
    return mid, out_up, out_lo


def ref_macd(x, fast=12, slow=26, signal=9):
    f = ref_ema(x, fast)
    s = ref_ema(x, slow)
    line = f - s
    sig = ref_ema(line, signal)
    return line, sig


def ref_stoch(h, l, c, k=14, d=3):
    kline = np.full(n, np.nan)
    for i in range(k - 1, n):
        hh = np.max(h[i - k + 1:i + 1])
        ll = np.min(l[i - k + 1:i + 1])
        kline[i] = 100 * (c[i] - ll) / (hh - ll) if hh != ll else np.nan
    dline = np.full(n, np.nan)
    for i in range(k - 1 + d - 1, n):
        dline[i] = np.nanmean(kline[i - d + 1:i + 1])
    return kline, dline


def ref_adx(h, l, c, p=14):
    plus_dm = np.full(n, 0.0)
    minus_dm = np.full(n, 0.0)
    for i in range(1, n):
        up = h[i] - h[i - 1]
        down = l[i - 1] - l[i]
        plus_dm[i] = up if (up > down and up > 0) else 0.0
        minus_dm[i] = down if (down > up and down > 0) else 0.0
    tr = ref_true_range(h, l, c)
    atr_v = np.full(n, np.nan)
    atr_v[0] = tr[0]
    pdm_s = np.full(n, np.nan)
    mdm_s = np.full(n, np.nan)
    pdm_s[0] = plus_dm[0]
    mdm_s[0] = minus_dm[0]
    for i in range(1, n):
        atr_v[i] = (atr_v[i - 1] * (p - 1) + tr[i]) / p
        pdm_s[i] = (pdm_s[i - 1] * (p - 1) + plus_dm[i]) / p
        mdm_s[i] = (mdm_s[i - 1] * (p - 1) + minus_dm[i]) / p
    plus_di = 100 * pdm_s / atr_v
    minus_di = 100 * mdm_s / atr_v
    dx = np.full(n, np.nan)
    for i in range(n):
        denom = plus_di[i] + minus_di[i]
        dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / denom if denom != 0 else np.nan
    out = np.full(n, np.nan)
    out[0] = dx[0] if not np.isnan(dx[0]) else 0.0
    for i in range(1, n):
        prev = out[i - 1] if not np.isnan(out[i - 1]) else 0.0
        cur = dx[i] if not np.isnan(dx[i]) else 0.0
        out[i] = (prev * (p - 1) + cur) / p
    return out


def cmp(name, a, b, tail=200, tol=1e-4):
    a = np.asarray(a)[-tail:]
    b = np.asarray(b)[-tail:]
    mask = ~(np.isnan(a) | np.isnan(b))
    if mask.sum() == 0:
        print(f"{name}: SIN DATOS COMPARABLES")
        return
    diff = np.abs(a[mask] - b[mask])
    rel = diff / np.maximum(np.abs(b[mask]), 1e-9)
    print(f"{name}: max_abs_diff={diff.max():.6g}  max_rel_diff={rel.max():.6g}  "
          f"n_comparado={mask.sum()}  {'OK' if rel.max() < tol or diff.max() < 1e-6 else 'REVISAR'}")


cmp("SMA(20)", sma(df["close"], 20).values, ref_sma(c, 20))
cmp("EMA(20)", ema(df["close"], 20).values, ref_ema(c, 20), tol=1e-3)
cmp("RSI(14)", rsi(df["close"], 14).values, ref_rsi(c, 14), tol=1e-2)
cmp("ATR(14)", atr(df["high"], df["low"], df["close"], 14).values, ref_atr(h, l, c, 14), tol=1e-3)

bb = bollinger(df["close"], 20, 2.0)
mid, up, lo = ref_bollinger(c, 20, 2.0)
cmp("BB_mid(20)", bb["bb_mid"].values, mid)
cmp("BB_upper(20)", bb["bb_upper"].values, up)
cmp("BB_lower(20)", bb["bb_lower"].values, lo)

m = macd(df["close"])
line, sig = ref_macd(c)
cmp("MACD_line", m["macd"].values, line, tol=1e-3)
cmp("MACD_signal", m["signal"].values, sig, tol=1e-3)

st = stochastic(df["high"], df["low"], df["close"])
kk, dd = ref_stoch(h, l, c)
cmp("STOCH_k", st["stoch_k"].values, kk)
cmp("STOCH_d", st["stoch_d"].values, dd)

cmp("ADX(14)", adx(df["high"], df["low"], df["close"], 14).values, ref_adx(h, l, c, 14), tol=2e-2)
