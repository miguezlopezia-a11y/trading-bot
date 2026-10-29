"""Fase A — Rigor estadistico sobre las 11 variantes ya probadas.

Capa de analisis: NO rebacktestea variantes nuevas ni optimiza nada. Extrae
las series diarias del pipeline congelado (mismas senales de STRATEGIES, mismo
CSV btc_usd_5y_1d.csv sha256 1c393a00..., mismo split 60/40, sizing 0.05 =
politica Risk) para poder calcular lo que los JSON de folds no guardan:
retornos diarios, skew/kurtosis, mascara de exposicion y PnLs por trade.

Metricas por variante:
  - Sharpe bruto anualizado (PPY=365)
  - DSR (Bailey & López de Prado 2014, SSRN 2460551) corrigiendo por N=11
  - Block bootstrap (bloques de 21d, B=10000) sobre retornos diarios y sobre
    PnLs por trade: IC95 del retorno medio y del win rate
  - t-stat de los retornos diarios (umbral exigido: t>3, Harvey/Liu/Zhu 2016)
  - Benchmark de exposicion igualada: Sharpe/Calmar del B&H de BTC solo en
    los dias con posicion abierta (misma exposicion media que la estrategia)

Fuente de la formula: paper original (J. Portfolio Management 40(5):94-107,
SSRN 2460551) + validacion cruzada contra el ejemplo impreso del paper
(DSR 0.9004, SR0 0.1132: sharpe diario 0.15811388, T=1250, N=100, V=0.002,
skew -3, kurt 10) tal como lo reproduce el paquete deflated_sharpe
(daru.finance/projects/deflated-sharpe). Ver docs/rigor_estadistico_resultado.md.

Uso: /opt/trading-bot/venv/bin/python src/rigor_estadistico.py
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest, compute_metrics  # noqa: E402

CSV = "data/btc_usd_5y_1d.csv"
PPY = 365
TRAIN_FRAC = 0.6
WARMUP = 200
SIZE_FRACTION = 0.05
VARIANTES = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
             "sma_timing_50", "sma_timing_100", "sma_timing_304",
             "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]
N_TRIALS = len(VARIANTES)
BLOCK = 21
B_BOOT = 10000
SEED = 42


# ------------------------------------------------------------ DSR
# PSR(SR*) = Phi( (SR_hat - SR*) * sqrt(T-1) /
#                  sqrt(1 - g3*SR_hat + (g4-1)/4 * SR_hat^2) )
# E[max_N] = sqrt(V) * [ (1-g)*Phi^-1(1-1/N) + g*Phi^-1(1-1/(N*e)) ]
# DSR = PSR(SR0). Todo en terminos por periodo (diario). g = 0.5772156649.
GAMMA_E = 0.5772156649


def _phiinv(p):
    return _NormalDist().inv_cdf(p)


class _NormalDist:
    """Normal estandar: CDF y cuantil (statistics.NormalDist)."""
    def __init__(self):
        import statistics
        self._nd = statistics.NormalDist()

    def inv_cdf(self, p):
        return self._nd.inv_cdf(p)

    def cdf(self, z):
        return self._nd.cdf(z)


_ND = None


def nd():
    global _ND
    if _ND is None:
        _ND = _NormalDist()
    return _ND


def psr(sharpe_per, n_obs, sr_star, skew, kurt):
    """Probabilistic Sharpe Ratio: P(SR_verdadero > sr_star)."""
    num = (sharpe_per - sr_star) * math.sqrt(n_obs - 1)
    den = math.sqrt(1 - skew * sharpe_per + (kurt - 1) / 4 * sharpe_per ** 2)
    return nd().cdf(num / den)


def expected_max_sharpe(n_trials, var_trials):
    """SR0 = sqrt(V) * E[max de N normales estandar] (Bailey-LdP Ec. 2).
    N=1 -> sin seleccion: E[max] = 0, SR0 = 0."""
    if n_trials <= 1:
        return 0.0, 0.0
    z1 = nd().inv_cdf(1 - 1.0 / n_trials)
    z2 = nd().inv_cdf(1 - 1.0 / (n_trials * math.e))
    emax = (1 - GAMMA_E) * z1 + GAMMA_E * z2
    return math.sqrt(var_trials) * emax, emax


def dsr(sharpe_per, n_obs, n_trials, var_trials, skew, kurt):
    """Deflated Sharpe Ratio."""
    sr0, _ = expected_max_sharpe(n_trials, var_trials)
    return psr(sharpe_per, n_obs, sr0, skew, kurt), sr0


def ar1_effective_n(returns):
    """Tamano muestral efectivo corrigiendo autocorrelacion AR(1) de los
    retornos (los backtester con posiciones abiertas la inducen)."""
    r = np.asarray(returns)
    r = r[~np.isnan(r)]
    if len(r) < 3 or r.std() == 0:
        return len(r)
    rho = np.corrcoef(r[:-1], r[1:])[0, 1]
    rho = min(max(rho, -0.95), 0.95)
    n = len(r)
    return n * (1 - rho) / (1 + rho)


# ------------------------------------------------------------ bootstrap
def block_bootstrap_ci(series, block, n_boot, func, seed, pct=True):
    """IC95 de func sobre remuestreos por bloques (circular). Devuelve
    (lo, hi, punto) en las unidades de func."""
    s = np.asarray(series, dtype=float)
    s = s[~np.isnan(s)]
    n = len(s)
    if n < block:
        return None, None, func(s)
    rng = np.random.default_rng(seed)
    nblocks = int(math.ceil(n / block))
    stats = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n, nblocks)
        idx = np.concatenate([(st + np.arange(block)) % n for st in starts])[:n]
        stats[b] = func(s[idx])
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5)), float(func(s))


# ------------------------------------------------------------ pipeline
def load_data():
    df = pd.read_csv(CSV, index_col=0, parse_dates=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()


def extract(variantes, df):
    """Serie diaria OOS de cada variante desde el pipeline congelado."""
    split = int(len(df) * TRAIN_FRAC)
    out = {}
    for name in variantes:
        fn = STRATEGIES[name]
        a = max(0, split - WARMUP)
        sig_full = fn(df.iloc[a:])
        sliced = df.iloc[split:]
        sig = sig_full.iloc[split - a:]
        res = run_backtest(sliced, sig, size_fraction=SIZE_FRACTION)
        eq = res["equity"]
        rets = eq.pct_change().dropna()
        pos = eq.index.to_series().map(
            lambda d: any(t.entry_date <= d <= (t.exit_date or d) for t in res["trades"]))
        out[name] = {"rets": rets, "trades": res["trades"], "pos": pos,
                     "bh": sliced["close"].pct_change().dropna()}
    return out


def stats_variante(name, data):
    rets = data["rets"]
    per = rets.values
    t_raw = len(per)
    t_eff = int(ar1_effective_n(per))
    sharpe_per = per.mean() / per.std() if per.std() > 0 else 0.0
    sharpe_ann = sharpe_per * math.sqrt(PPY)
    skew = float(pd.Series(per).skew())
    kurt = float(pd.Series(per).kurt() + 3)  # pandas da exceso; raw = exceso+3
    # DSR con T efectivo (AR1) — documentado
    return {"sharpe_anual": round(sharpe_ann, 3), "sharpe_per": sharpe_per,
            "n_obs": t_raw, "n_obs_eff": t_eff, "skew": round(skew, 3),
            "kurt": round(kurt, 3)}


def benchmark_exposicion(data, rets):
    """B&H con la misma exposicion: retornos de BTC solo en dias con posicion."""
    pos = data["pos"]
    aligned = data["bh"].reindex(pos.index).fillna(0.0)
    bh_exp = aligned[pos.values]
    st_exp = rets.reindex(pos.index).fillna(0.0)[pos.values]
    def sharpe(x):
        x = np.asarray(x, dtype=float)
        return float(x.mean() / x.std() * math.sqrt(PPY)) if x.std() > 0 else 0.0
    def calmar(x):
        x = pd.Series(np.asarray(x, dtype=float))
        eq = (1 + x).cumprod()
        dd = (eq - eq.cummax()) / eq.cummax()
        total = eq.iloc[-1] - 1
        years = len(x) / PPY
        if dd.min() == 0 or years <= 0:
            return 0.0
        return float(total / abs(dd.min()) / years)
    return {
        "exposicion_pct": round(100 * float(pos.mean()), 1),
        "sharpe_estrategia_exp": round(sharpe(st_exp.values), 3),
        "sharpe_bh_misma_exposicion": round(sharpe(bh_exp.values), 3),
        "calmar_estrategia_exp": round(calmar(st_exp.values), 3),
        "calmar_bh_misma_exposicion": round(calmar(bh_exp.values), 3),
    }


def main():
    df = load_data()
    print(f"Pipeline congelado: {CSV}, {len(df)} velas, N variantes = {N_TRIALS}")
    data = extract(VARIANTES, df)

    base = {n: stats_variante(n, d) for n, d in data.items()}
    # V = varianza across-trial de los Sharpes por periodo de las 11 variantes
    sharpes_per = np.array([base[n]["sharpe_per"] for n in VARIANTES])
    var_trials = float(sharpes_per.var(ddof=1))
    print(f"V (varianza across-trial de Sharpe diario, {N_TRIALS} variantes) = "
          f"{var_trials:.6f}")

    out = {}
    for i, name in enumerate(VARIANTES):
        d = data[name]
        b = base[name]
        dsr_val, sr0 = dsr(b["sharpe_per"], b["n_obs_eff"], N_TRIALS, var_trials,
                           b["skew"], b["kurt"])
        # t-stat diario (media/std * sqrt(T_eff)); umbral exigido t>3
        per = d["rets"].values
        t_stat = float(per.mean() / per.std() * math.sqrt(b["n_obs_eff"])) \
            if per.std() > 0 else 0.0
        # bootstrap: retorno medio diario (anualizado) y win rate por trade
        lo_r, hi_r, pt_r = block_bootstrap_ci(
            per, BLOCK, B_BOOT, lambda x: x.mean() * PPY * 100, SEED + i)
        pnls = [t.pnl for t in d["trades"]]
        wins = [1.0 if p > 0 else 0.0 for p in pnls]
        lo_w, hi_w, pt_w = (None, None, None)
        if len(wins) >= 10:
            lo_w, hi_w, pt_w = block_bootstrap_ci(
                wins, max(3, len(wins) // 4), B_BOOT, lambda x: x.mean() * 100,
                SEED + 100 + i)
        bench = benchmark_exposicion(d, d["rets"])
        n_trades = len(d["trades"])
        out[name] = {**b, "dsr": round(dsr_val, 4), "sr0_per": round(sr0, 5),
                     "t_stat": round(t_stat, 2),
                     "ic_retorno_anual_pct": [round(lo_r, 2), round(hi_r, 2)],
                     "ic_win_rate_pct": None if lo_w is None else
                                        [round(lo_w, 1), round(hi_w, 1)],
                     "n_trades": n_trades,
                     "edge_ic_retorno": bool(hi_r > 0 and lo_r > 0),
                     "edge_ic_winrate": (None if lo_w is None else
                                         bool(hi_w > 50 and lo_w > 50)),
                     "pasa_t3": bool(t_stat > 3), **bench}
        print(f"{name:<22} Sharpe {b['sharpe_anual']:>6} DSR {dsr_val:>6.3f} "
              f"t {t_stat:>6.2f} IC_ret [{lo_r:>7.2f},{hi_r:>7.2f}] "
              f"IC_win {('n/a' if lo_w is None else f'[{lo_w:.0f},{hi_w:.0f}]'):>10} "
              f"exp {bench['exposicion_pct']:>5}%")

    with open("results/rigor_estadistico.json", "w") as f:
        json.dump({"n_trials": N_TRIALS, "var_trials": var_trials,
                   "block": BLOCK, "n_boot": B_BOOT, "seed": SEED,
                   "size_fraction": SIZE_FRACTION, "variantes": out}, f,
                  indent=2, default=str)
    print("-> results/rigor_estadistico.json guardado")


if __name__ == "__main__":
    main()
