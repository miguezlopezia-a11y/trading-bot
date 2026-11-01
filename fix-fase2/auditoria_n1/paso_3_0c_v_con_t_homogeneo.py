"""Paso 3.0c — recalcular V con T homogeneo y recalcular el DSR de Fase B.
   (objecion B1 de la nemesis de N2, rama nube/s2-literatura)

N2 observo que SR0 = sqrt(V)*E[max_N] usa una V estimada sobre 11 trials de
Fase A con n_obs_eff entre 598 y 2188, y la aplica a un estadistico medido con
T_eff 4336. Midio que la dispersion observada (sd 0.0265 diaria) cae dentro
del ruido muestral de Sharpes con habilidad cero a esos tamaños (0.021-0.041),
y que reescalando el ruido al T_eff del deflactado el liston caeria a 0.842
anual, por debajo del 1.008 observado.

Lo que hace este script, en el orden que importa:

  A) Diagnostico de la mezcla de escalas: descomponer la varianza observada
     en dispersion verdadera + ruido de estimacion, SIN asumir que los 11
     trials son independientes (comparten la misma serie de precios de BTC,
     asi que sus errores estan correlacionados — N2 no lo tuvo en cuenta).
  B) Replicar el bucle del portfolio con la REGLA DESACOPLADA, y validar la
     replica reproduciendo Fase B exacto. Si no reproduce, el resto no vale.
  C) Reestimar las 11 reglas de Fase A sobre el MISMO panel (10 activos, 12
     años, misma maquinaria Carver + cov EWMA + mismos costes). T homogeneo.
  D) Recalcular V con esos 12 trials y recalcular el DSR de Fase B.

N SIGUE SIENDO 12. Son las 11 reglas ya contadas, medidas otra vez, mas la
regla de portfolio. No se gasta ningun trial nuevo.

NO se cambia ninguna metrica ni umbral del expediente: se reporta el DSR con
la V vieja y con la nueva, y Pablo decide. [no verificado] La lectura de que
Bailey-LdP exija trials de longitud homogenea para que V sea comparable no se
ha podido comprobar contra el texto del paper desde esta sesion (sin acceso a
SSRN 2460551); se mantiene la etiqueta que N2 le puso.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_0c_v_con_t_homogeneo.py
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
os.chdir(FIX2)
from portfolio_runner import (load_or_download, simulate, metrics,  # noqa: E402
                              carver_weights, portfolio_vol_anual,
                              LAMBDA, SIGMA_TARGET, W_MAX, GROSS_MAX,
                              VOL_TOPE_MULT, COMMISSION, SLIPPAGE, LOOKBACK,
                              PPY)
from rigor_estadistico import dsr, psr, expected_max_sharpe, ar1_effective_n  # noqa: E402
from strategies import STRATEGIES  # noqa: E402
from indicators import sma as sma_ind  # noqa: E402

SELLO = "20261007"
N_TRIALS = 12
V_VIEJA = 0.0007021947704551833
CONF = 0.95
VARIANTES_A = ["ma_cross", "sma_timing_5", "sma_timing_10", "sma_timing_20",
               "sma_timing_50", "sma_timing_100", "sma_timing_304",
               "tsmom_7", "tsmom_365", "connors_rsi2", "rsi_hidden_divergence"]


# --------------------------------------------------------------- utilidades
def prepase(rets):
    """s2_path y cov_path EWMA, identico a portfolio_runner.simulate."""
    R = rets.values
    nf, n = R.shape
    s2_path = np.full((nf, n), np.nan)
    cov_path = np.full((nf, n, n), np.nan)
    s2 = np.full(n, np.nan)
    cov_acc = np.full((n, n), np.nan)
    have_var = np.zeros(n, dtype=bool)
    have_cov = np.zeros((n, n), dtype=bool)
    for t in range(nf):
        r = R[t]
        for i in range(n):
            if np.isnan(r[i]):
                continue
            if not have_var[i]:
                s2[i] = r[i] * r[i]
                have_var[i] = True
            else:
                s2[i] = LAMBDA * s2[i] + (1 - LAMBDA) * r[i] * r[i]
        for i in range(n):
            if np.isnan(r[i]):
                continue
            for j in range(n):
                if np.isnan(r[j]):
                    continue
                if not have_cov[i, j]:
                    cov_acc[i, j] = r[i] * r[j]
                    have_cov[i, j] = True
                else:
                    cov_acc[i, j] = LAMBDA * cov_acc[i, j] + \
                        (1 - LAMBDA) * r[i] * r[j]
        s2_path[t] = s2
        cov_path[t] = cov_acc
    return s2_path, cov_path


def simular_con_regla(datos, dentro):
    """Replica del bucle de portfolio_runner.simulate con la señal DESACOPLADA.

    `dentro(tk, t, closes, rets)` devuelve True si el activo tk debe estar
    dentro el dia t, decidiendo SOLO con datos < t. Todo lo demas (sizing
    Carver, veto w_max, cov EWMA completa, veto de vol, costes sobre turnover,
    elegibilidad por historia) es identico al original."""
    closes = pd.DataFrame({k: v["close"] for k, v in datos.items()}).sort_index()
    rets = closes.pct_change()
    fechas = closes.index
    tickers = list(datos.keys())
    n = len(tickers)
    s2_path, cov_path = prepase(rets)

    equity = 1.0
    eq_curve, exposure, rp_hist, coste_hist = [], [], [], []
    w_prev = np.zeros(n)
    for t in range(len(fechas)):
        w_target = np.zeros(n)
        sigmas = np.full(n, np.nan)
        if t > 0:
            for i, tk in enumerate(tickers):
                s = rets[tk].iloc[:t]
                if s.notna().sum() < LOOKBACK + 1:
                    continue
                if not dentro(tk, t, closes, rets):
                    continue
                sig = np.sqrt(s2_path[t - 1, i])
                if not np.isnan(sig) and sig > 0:
                    sigmas[i] = sig * np.sqrt(PPY)
            w_target, _ = carver_weights(sigmas)
        cov = cov_path[t - 1] if t > 1 else np.full((n, n), np.nan)
        vol_p = portfolio_vol_anual(w_target, cov)
        if vol_p > VOL_TOPE_MULT * SIGMA_TARGET:
            w_target = w_target * ((VOL_TOPE_MULT * SIGMA_TARGET) / vol_p)
        r_dia = rets.iloc[t].values
        r_p = float(np.nansum(w_prev * r_dia))
        turnover = float(np.nansum(np.abs(w_prev - w_target)))
        equity *= (1 + r_p - turnover * (COMMISSION + SLIPPAGE))
        eq_curve.append(equity)
        exposure.append(float(np.nansum(w_prev)))
        rp_hist.append(r_p)
        coste_hist.append(turnover * (COMMISSION + SLIPPAGE))
        w_prev = w_target
    return pd.Series(eq_curve, index=fechas)


def regla_fase_b(tk, t, closes, rets):
    """La regla que corrio Fase B: filtro de ESTADO mom>0 (portfolio_runner
    .py:215-219). Ojo: NO es strategies.tsmom_365, que entra solo en el cruce
    de signo — N2 lo documento en su A6."""
    if t - 1 - LOOKBACK < 0:
        return False
    mom = closes[tk].iloc[t - 1] / closes[tk].iloc[t - 1 - LOOKBACK] - 1
    return bool(mom > 0)


def hacer_regla_fase_a(nombre, datos):
    """Precalcula la señal de una regla de Fase A por activo y la convierte en
    un filtro de ESTADO comparable al de Fase B (que es de estado).

    Sale por los tres mecanismos que usa el backtester real, no solo por la
    columna exit_long: (a) exit_long, (b) señal contraria entry_short, y
    (c) el trailing sobre la media, `close <= sma(trailing_ma_period)`
    (backtester.py:96-105). Sin (c), las cinco variantes sma_timing_* —que NO
    tienen columna exit_long y salen solo por el trailing— se quedarian dentro
    para siempre desde su primera entrada y colapsarian todas al mismo numero.

    La señal del dia t-1 decide el dia t (sin look-ahead), igual que Fase B."""
    fn = STRATEGIES[nombre]
    estado = {}
    for tk, d in datos.items():
        df = d.dropna()
        try:
            sig = fn(df)
        except Exception:
            estado[tk] = pd.Series(False, index=df.index)
            continue
        ent = sig["entry_long"].fillna(False).astype(bool).values
        sal = (sig["exit_long"].fillna(False).astype(bool).values
               if "exit_long" in sig.columns
               else np.zeros(len(df), dtype=bool))
        corto = (sig["entry_short"].fillna(False).astype(bool).values
                 if "entry_short" in sig.columns
                 else np.zeros(len(df), dtype=bool))
        # trailing sobre la media: mismo mecanismo que backtester.py:96-105
        trail = np.zeros(len(df), dtype=bool)
        if "trailing_ma_period" in sig.columns:
            per = sig["trailing_ma_period"].dropna()
            if len(per):
                p = int(per.iloc[0])
                if p > 0:
                    ma = sma_ind(df["close"], p).values
                    cl = df["close"].values
                    trail = ~np.isnan(ma) & (cl <= ma)
        dentro, cur = np.zeros(len(df), dtype=bool), False
        for i in range(len(df)):
            if cur and (sal[i] or corto[i] or trail[i]):
                cur = False
            elif not cur and ent[i]:
                cur = True
            dentro[i] = cur
        estado[tk] = pd.Series(dentro, index=df.index)

    def regla(tk, t, closes, rets):
        fecha = closes.index[t - 1]
        s = estado.get(tk)
        if s is None or fecha not in s.index:
            return False
        return bool(s.loc[fecha])
    return regla


def sharpe_diario(eq):
    r = eq.pct_change().dropna().values
    return float(r.mean() / r.std()) if len(r) > 1 and r.std() > 0 else 0.0


print("=" * 74)
print("PASO 3.0c — V con T homogeneo y DSR de Fase B recalculado")
print("=" * 74)
print("Origen: objecion B1 de la nemesis de N2 (rama nube/s2-literatura).")
print("N SIGUE EN 12: las 11 reglas ya contadas, medidas otra vez.")
print()

datos = load_or_download(stamp=SELLO, verbose=False)
res_b = simulate(datos)
eq_b = res_b["equity"]
r_b = eq_b.pct_change().dropna()
s_per_b = r_b.mean() / r_b.std()
t_eff_b = int(ar1_effective_n(r_b.values))
skew_b, kurt_b = float(r_b.skew()), float(r_b.kurt() + 3)
print(f"Fase B: Sharpe anual {s_per_b*math.sqrt(PPY):.3f}  T_eff {t_eff_b}  "
      f"skew {skew_b:.3f}  curtosis {kurt_b:.3f}")
print()

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — diagnostico: ¿V mide habilidad o ruido de estimacion?")
print("-" * 74)
rig = json.load(open(os.path.join(FIX2, "results", "rigor_estadistico.json")))
sh_a = np.array([v["sharpe_per"] for v in rig["variantes"].values()])
nobs_a = np.array([v["n_obs_eff"] for v in rig["variantes"].values()])
var_obs = float(np.var(np.append(sh_a, s_per_b), ddof=1))
print(f"  11 Sharpe diarios de Fase A: sd {sh_a.std(ddof=1):.5f}")
print(f"  n_obs_eff de Fase A: min {nobs_a.min()} max {nobs_a.max()} "
      f"media {nobs_a.mean():.0f}")
print(f"  V observada (los 12 trials)  {var_obs:.10f}")
print(f"  V cableada en el codigo      {V_VIEJA:.10f}")
print()
# ruido de estimacion de un Sharpe: var(SR_hat) ~ (1 + SR^2/2)/T
ruido_i = (1 + sh_a ** 2 / 2) / nobs_a
print(f"  Ruido de estimacion por trial, var(SR_hat) ~ (1+SR²/2)/T_eff:")
print(f"    medio {ruido_i.mean():.10f}   (sd {math.sqrt(ruido_i.mean()):.5f})")
print(f"    rango {ruido_i.min():.10f} - {ruido_i.max():.10f}")
print()
print("  N2 señalo que la dispersion observada cae dentro del ruido muestral.")
print("  Comprobado y MATIZADO: la dispersion observada es incluso MENOR que")
print("  el ruido medio de estimacion:")
print(f"    var observada {var_obs:.8f}  vs  ruido medio {ruido_i.mean():.8f}")
print(f"    ratio {var_obs/ruido_i.mean():.3f}")
print()
disp_verdadera = var_obs - ruido_i.mean()
print(f"  Descomposicion naive (var_obs = var_verdadera + ruido):")
print(f"    var_verdadera estimada = {disp_verdadera:.10f}")
if disp_verdadera < 0:
    print("    -> NEGATIVA. Bajo el modelo de errores INDEPENDIENTES, la")
    print("       dispersion verdadera entre reglas se estima en CERO: toda")
    print("       la dispersion observada (y menos) es error de estimacion.")
    print()
    print("  Pero ese modelo no se sostiene, y es el matiz que N2 no incluyo:")
    print("  las 11 reglas corren sobre LA MISMA serie de precios de BTC, en")
    print("  el MISMO tramo OOS. Sus errores de estimacion estan fuertemente")
    print("  correlacionados, asi que la varianza entre ellas NO es la suma de")
    print("  ruidos independientes y puede ser mucho menor. De ahi el ratio")
    print(f"  {var_obs/ruido_i.mean():.3f} < 1.")
    print()
    print("  Conclusion del diagnostico: la V actual NO es interpretable como")
    print("  dispersion de habilidad, pero tampoco como ruido independiente")
    print("  reescalable. El reescalado V·843/4336 que propone N2 es UN modelo")
    print("  posible, no el correcto. La via limpia es medir los 12 trials con")
    print("  el MISMO T, que es lo que hacen las partes B-D.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — validacion de la replica del bucle (sin esto nada vale)")
print("-" * 74)
eq_rep = simular_con_regla(datos, regla_fase_b)
m_orig = metrics(eq_b, res_b["benchmark"])
dif_max = float(np.max(np.abs(eq_rep.values - eq_b.values)))
s_rep = sharpe_diario(eq_rep)
print(f"  Fase B original   Sharpe {s_per_b*math.sqrt(PPY):.6f}  "
      f"retorno {m_orig['retorno_pct']}%  equity final {eq_b.iloc[-1]:.6f}")
print(f"  Replica 3.0c      Sharpe {s_rep*math.sqrt(PPY):.6f}  "
      f"retorno {(eq_rep.iloc[-1]/eq_rep.iloc[0]-1)*100:.2f}%  "
      f"equity final {eq_rep.iloc[-1]:.6f}")
print(f"  maxima diferencia punto a punto en la equity: {dif_max:.3e}")
valida = dif_max < 1e-9
print(f"  -> replica {'VALIDA' if valida else 'NO VALIDA'}")
if not valida:
    print()
    print("  La replica no reproduce Fase B. No se puede usar para medir los")
    print("  otros 11 trials: cualquier V que saliese de aqui mezclaria el")
    print("  efecto de la regla con el de la replica. PARA AQUI.")
    sys.exit(1)
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — las 11 reglas de Fase A sobre el panel de Fase B")
print("-" * 74)
print("  Misma maquinaria: Carver, cov EWMA completa, vetos, costes, mismas")
print("  fechas. Unica diferencia entre trials: la regla de entrada/salida.")
print()
print(f"  {'trial':<24} {'Sharpe diario':>14} {'Sharpe anual':>13} "
      f"{'T_eff':>7} {'exp. media':>11}")
print(f"  {'-'*24} {'-'*14} {'-'*13} {'-'*7} {'-'*11}")
trials = {}
for nombre in VARIANTES_A:
    eq = simular_con_regla(datos, hacer_regla_fase_a(nombre, datos))
    r = eq.pct_change().dropna()
    s = sharpe_diario(eq)
    te = int(ar1_effective_n(r.values))
    trials[nombre] = {"sharpe_per": s, "sharpe_anual": s * math.sqrt(PPY),
                      "t_eff": te, "equity_final": float(eq.iloc[-1])}
    print(f"  {nombre:<24} {s:>14.6f} {s*math.sqrt(PPY):>13.3f} {te:>7} "
          f"{'':>11}")
trials["portfolio_fase_b"] = {"sharpe_per": s_per_b,
                              "sharpe_anual": s_per_b * math.sqrt(PPY),
                              "t_eff": t_eff_b,
                              "equity_final": float(eq_b.iloc[-1])}
print(f"  {'portfolio_fase_b':<24} {s_per_b:>14.6f} "
      f"{s_per_b*math.sqrt(PPY):>13.3f} {t_eff_b:>7}")
print()
# control: dos trials con el MISMO Sharpe exacto delatan un colapso de la
# conversion a estado, no un resultado
vals = [round(v["sharpe_per"], 12) for v in trials.values()]
dups = len(vals) - len(set(vals))
print(f"  control anti-colapso: {dups} par(es) de trials con Sharpe identico "
      f"-> {'OK' if dups == 0 else 'SOSPECHOSO'}")
if dups:
    print("  AVISO: trials identicos significan que la conversion a estado los")
    print("  colapso. La V que salga de aqui NO es fiable.")
print()
t_effs = np.array([v["t_eff"] for v in trials.values()])
print(f"  T_eff de los 12 trials: min {t_effs.min()} max {t_effs.max()} "
      f"ratio {t_effs.max()/t_effs.min():.2f}")
print(f"  (antes: min {nobs_a.min()} max {max(nobs_a.max(), t_eff_b)} "
      f"ratio {max(nobs_a.max(), t_eff_b)/nobs_a.min():.2f})")
print()

# ------------------------------------------------------------------ PARTE D
print("-" * 74)
print("PARTE D — V nueva y DSR de Fase B recalculado")
print("-" * 74)
sh_nuevos = np.array([v["sharpe_per"] for v in trials.values()])
v_nueva = float(np.var(sh_nuevos, ddof=1))
print(f"  V vieja (T heterogeneo, 598-4336)  {V_VIEJA:.10f}")
print(f"  V nueva (T homogeneo)              {v_nueva:.10f}")
print(f"  ratio                              {v_nueva/V_VIEJA:.4f}")
print()


def liston(var_trials):
    sr0, _ = expected_max_sharpe(N_TRIALS, var_trials)
    if psr(sr0, t_eff_b, sr0, skew_b, kurt_b) >= CONF:
        return sr0 * math.sqrt(PPY), sr0
    lo, hi = sr0, sr0 + 2.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if psr(mid, t_eff_b, sr0, skew_b, kurt_b) >= CONF:
            hi = mid
        else:
            lo = mid
    return hi * math.sqrt(PPY), sr0


d_viejo, sr0_viejo = dsr(s_per_b, t_eff_b, N_TRIALS, V_VIEJA, skew_b, kurt_b)
d_nuevo, sr0_nuevo = dsr(s_per_b, t_eff_b, N_TRIALS, v_nueva, skew_b, kurt_b)
l_viejo, _ = liston(V_VIEJA)
l_nuevo, _ = liston(v_nueva)
s_obs = s_per_b * math.sqrt(PPY)
print(f"  {'':<26} {'V vieja':>14} {'V nueva':>14}")
print(f"  {'-'*26} {'-'*14} {'-'*14}")
print(f"  {'SR0 diario':<26} {sr0_viejo:>14.5f} {sr0_nuevo:>14.5f}")
print(f"  {'liston Sharpe DSR>=0.95':<26} {l_viejo:>14.3f} {l_nuevo:>14.3f}")
print(f"  {'Sharpe observado':<26} {s_obs:>14.3f} {s_obs:>14.3f}")
print(f"  {'brecha':<26} {l_viejo-s_obs:>+14.3f} {l_nuevo-s_obs:>+14.3f}")
print(f"  {'DSR de Fase B':<26} {d_viejo:>14.4f} {d_nuevo:>14.4f}")
print(f"  {'¿DSR >= 0.95?':<26} {('SI' if d_viejo>=CONF else 'no'):>14} "
      f"{('SI' if d_nuevo>=CONF else 'no'):>14}")
print()
print(f"  Referencia de N2: estimaba que el liston podria caer a 0.842.")
print(f"  Medido aqui con T homogeneo: {l_nuevo:.3f}.")
print()
print("-" * 74)
print("PARTE E — el sesgo que corta en contra, medido")
print("-" * 74)
sh_viejos_an = np.append(sh_a, s_per_b) * math.sqrt(PPY)
sh_nuevos_an = sh_nuevos * math.sqrt(PPY)
print("  ¿Por que cae V tanto? Porque los 12 trials nuevos pasan TODOS por la")
print("  misma maquinaria: vol-targeting al 10% anual, w_max 0.20, tope de")
print("  gross y veto de vol de portfolio. Esa maquinaria comprime cualquier")
print("  regla hacia un mismo perfil de riesgo.")
print()
print(f"  {'familia de trials':<34} {'min':>8} {'max':>8} {'sd':>9} {'rango':>8}")
print(f"  {'-'*34} {'-'*8} {'-'*8} {'-'*9} {'-'*8}")
print(f"  {'Fase A single-asset + Fase B':<34} {sh_viejos_an.min():>8.3f} "
      f"{sh_viejos_an.max():>8.3f} {sh_viejos_an.std(ddof=1):>9.3f} "
      f"{sh_viejos_an.max()-sh_viejos_an.min():>8.3f}")
print(f"  {'11 reglas sobre el panel + Fase B':<34} {sh_nuevos_an.min():>8.3f} "
      f"{sh_nuevos_an.max():>8.3f} {sh_nuevos_an.std(ddof=1):>9.3f} "
      f"{sh_nuevos_an.max()-sh_nuevos_an.min():>8.3f}")
print(f"  {'negativos en la familia':<34} "
      f"{int((sh_viejos_an < 0).sum()):>8} {int((sh_nuevos_an < 0).sum()):>8}")
print()
print("  Los 12 trials nuevos estan todos entre "
      f"{sh_nuevos_an.min():.2f} y {sh_nuevos_an.max():.2f} y ninguno es")
print("  negativo; los viejos iban de "
      f"{sh_viejos_an.min():.2f} a {sh_viejos_an.max():.2f} con "
      f"{int((sh_viejos_an < 0).sum())} negativos.")
print("  Es decir: parte de la caida de V no es 'quitar ruido de muestras")
print("  cortas', es que el vol-targeting iguala las reglas.")
print()
print("  Y hay una objecion de fondo, que es mas grave que la direccion:")
print("  en Bailey-LdP, V es la dispersion entre los intentos QUE DE VERDAD SE")
print("  PROBARON. La busqueda real de este expediente fue: 11 reglas sobre")
print("  BTC solo (Fase A) y despues una regla de portfolio (Fase B). Medir")
print("  esas 11 reglas sobre el panel de 12 años describe una familia de")
print("  intentos que NUNCA se busco. Es mas homogenea en T — y eso arregla lo")
print("  que N2 denuncia— pero deja de ser el conjunto de intentos realizado.")
print()
print(f"  {'construccion de V':<40} {'V':>13} {'liston':>9} {'DSR':>8}")
print(f"  {'-'*40} {'-'*13} {'-'*9} {'-'*8}")
print(f"  {'la del expediente (T heterogeneo)':<40} {V_VIEJA:>13.8f} "
      f"{l_viejo:>9.3f} {d_viejo:>8.4f}")
print(f"  {'T homogeneo sobre el panel (3.0c)':<40} {v_nueva:>13.8f} "
      f"{l_nuevo:>9.3f} {d_nuevo:>8.4f}")
for etiqueta, vv in (("reescalado de N2 (V·843/4336)", V_VIEJA * 843 / 4336),):
    dd, _ = dsr(s_per_b, t_eff_b, N_TRIALS, vv, skew_b, kurt_b)
    ll, _ = liston(vv)
    print(f"  {etiqueta:<40} {vv:>13.8f} {ll:>9.3f} {dd:>8.4f}")
print()
print("  EL HALLAZGO, por encima de la direccion: el liston se mueve entre")
print(f"  {min(l_nuevo, l_viejo):.3f} y {max(l_nuevo, l_viejo):.3f} segun como se")
print("  construya V, y el Sharpe observado (1.008) cae EN MEDIO. La cifra")
print("  1.312 — y por tanto la brecha +0.304 de la que cuelga el expediente")
print("  entero, los tres briefs y la premisa 'solo quedan dos salidas' — NO")
print("  ES ROBUSTA a una eleccion metodologica defendible. Eso vale")
print("  independientemente de cual de las dos construcciones se prefiera.")
print()
print("=" * 74)
print("VEREDICTO 3.0c")
if d_nuevo >= CONF:
    print("  CON V MEDIDA A T HOMOGENEO, FASE B PASA DSR >= 0.95 CON N=12.")
    print(f"  El liston cae de {l_viejo:.3f} a {l_nuevo:.3f}, por debajo del")
    print(f"  {s_obs:.3f} observado: bajo ESTA construccion de V no hay brecha.")
    print("  La objecion B1 de N2 queda CONFIRMADA en direccion y en signo")
    print(f"  (estimaba ~0.842; medido {l_nuevo:.3f}).")
    print()
    print("  PERO esto NO es 'Fase B pasa'. Es: el liston depende de una")
    print("  eleccion metodologica que nadie habia hecho explicita, y las dos")
    print("  construcciones defendibles caen a lados opuestos del observado.")
    print("  La parte E mide dos razones para NO quedarse con el 0.823 sin mas:")
    print("  el vol-targeting comprime los 12 trials, y la familia nueva no es")
    print("  la que de verdad se busco. Lo que queda establecido es que la")
    print("  brecha +0.304 NO ES ROBUSTA, no que sea cero.")
else:
    print("  CON V MEDIDA A T HOMOGENEO, FASE B SIGUE SIN ALCANZAR DSR 0.95.")
    print(f"  El liston pasa de {l_viejo:.3f} a {l_nuevo:.3f} y el observado es")
    print(f"  {s_obs:.3f}: la brecha pasa de {l_viejo-s_obs:+.3f} a "
          f"{l_nuevo-s_obs:+.3f}.")
    if v_nueva > V_VIEJA:
        print("  La objecion B1 de N2 apuntaba a un defecto REAL de escala, pero")
        print("  la direccion del efecto es la CONTRARIA a la que estimaba:")
        print("  medir las 11 reglas sobre doce años AUMENTA su dispersion")
        print("  verdadera, que es el riesgo que N2 declaro explicitamente.")
    else:
        print("  B1 acierta en el signo pero no lo bastante para cruzar el umbral.")
print()
print("  NO se cambia ningun veredicto del expediente: eso lo decide Pablo.")
print("  Limites declarados:")
print("    - La replica del bucle reproduce Fase B a "
      f"{dif_max:.1e}, pero las 11 reglas de")
print("      Fase A se convirtieron a filtro de ESTADO (dentro desde")
print("      entry_long hasta exit/señal contraria) para ser comparables con")
print("      la regla de Fase B, que es de estado. Las reglas originales son")
print("      de evento y pasan por el backtester de una posicion. No es la")
print("      misma medicion que Fase A publico, y no pretende serlo.")
print("    - [no verificado] Que Bailey-LdP exija T homogeneo entre trials no")
print("      se pudo comprobar contra SSRN 2460551 desde esta sesion.")
with open(os.path.join(AQUI, "salida_3_0c_v_homogenea.json"), "w") as f:
    json.dump({"sello": SELLO, "n_trials": N_TRIALS,
               "v_vieja": V_VIEJA, "v_nueva": v_nueva,
               "replica_dif_max": dif_max,
               "var_observada_vieja": var_obs,
               "ruido_medio_estimacion": float(ruido_i.mean()),
               "dispersion_verdadera_naive": float(disp_verdadera),
               "sr0_viejo": sr0_viejo, "sr0_nuevo": sr0_nuevo,
               "liston_viejo": l_viejo, "liston_nuevo": l_nuevo,
               "sharpe_observado": s_obs,
               "dsr_viejo": d_viejo, "dsr_nuevo": d_nuevo,
               "pasa_095_con_v_nueva": bool(d_nuevo >= CONF),
               "trials": trials}, f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_0c_v_homogenea.json')}")
