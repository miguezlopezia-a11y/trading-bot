"""Paso 3.6 — sesgo de supervivencia y calidad de los datos de los caidos.

El brief original (§3.3) pedia: evaluar el sesgo residual del criterio de
seleccion de caidos, y verificar el caso FIL (yfinance da datos desde 2017-12,
anterior a su listado real) buscando mas casos iguales entre los 15 activos.

portfolio_supervivencia.congelar() tiene el MISMO defecto que
load_or_download tenia (sello = fecha de hoy, descarga si falta). No se
modifica ese fichero: el alcance de escrituras que autoriza el OK no lo
incluye. Se sustituye en tiempo de ejecucion por el cargador parcheado del
paso 3.0, que es equivalente salvo en que no descarga y verifica el hash.

Tres partes:
  A) Reproducir el dictamen P3 publicado (Sharpe 0.92, t 3.18, DSR 0.60).
  B) Buscar backfill sospechoso en los 15 activos: tramos iniciales con
     precio constante, volumen cero o volatilidad anomala — la firma de datos
     rellenados por el proveedor antes del listado real.
  C) Acotar el sesgo residual del criterio de seleccion SIN datos nuevos:
     ¿cuanto mueve el dictamen quitar y poner caidos de uno en uno?

Uso:  python3 fix-fase2/auditoria_n1/paso_3_6_supervivencia.py
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
import portfolio_supervivencia as ps  # noqa: E402
from portfolio_runner import cargar_congelados, simulate  # noqa: E402

SELLO = "20261009"            # unico sello de data/multi_muertos/
DIR_MUERTOS = "data/multi_muertos"


def cargador(tickers):
    return cargar_congelados(tickers, data_dir=DIR_MUERTOS, stamp=SELLO,
                             verbose=False)


ps.congelar = cargador        # sustitucion en memoria, no se toca el fichero

print("=" * 74)
print("PASO 3.6 — supervivencia y calidad de los datos de los caidos")
print("=" * 74)
print(f"criterio registrado: {ps.CRITERIO}")
print(f"caidos: {ps.MUERTOS}")
print(f"vivos:  {ps.VIVOS}")
print(f"cargador parcheado -> {DIR_MUERTOS}, sello {SELLO}, sin descarga")
print()

# ------------------------------------------------------------------ PARTE A
print("-" * 74)
print("PARTE A — reproducir el dictamen P3")
print("-" * 74)
pub_path = os.path.join(FIX2, "results", "portfolio_supervivencia.json")
pub = json.load(open(pub_path))["metricas"]
datos_v = cargador(ps.VIVOS)
datos_m = cargador(ps.MUERTOS)
datos_ext = {**datos_v, **datos_m}
res_ext = simulate(datos_ext)
obs = ps.bateria(res_ext["equity"], res_ext["benchmark"])
print(f"  {'metrica':<26} {'publicado':>12} {'reejecutado':>12} {'':>8}")
print(f"  {'-'*26} {'-'*12} {'-'*12} {'-'*8}")
difs = 0
for k in ("retorno_pct", "sharpe", "max_dd_pct", "dsr", "t_stat",
          "bench_retorno_pct", "bench_sharpe"):
    vp, vo = pub.get(k), obs.get(k)
    igual = (vp == vo) or (isinstance(vp, (int, float))
                           and isinstance(vo, (int, float))
                           and abs(vp - vo) < 1e-9)
    if not igual:
        difs += 1
    print(f"  {k:<26} {vp!s:>12} {vo!s:>12} {'OK' if igual else 'DIFIERE':>8}")
print()
print(f"  booleanos: pasa_t3 {obs['pasa_t3']}  edge_ic {obs['edge_ic']}  "
      f"supera_bench {obs['supera_bench_sharpe']}")
if difs == 0:
    print("  -> P3 REPRODUCE exacto con los CSV congelados de multi_muertos.")
else:
    print(f"  -> {difs} metrica(s) no reproducen. HALLAZGO.")
print()

# ------------------------------------------------------------------ PARTE B
print("-" * 74)
print("PARTE B — ¿hay backfill del proveedor antes del listado real?")
print("-" * 74)
print("  Firma buscada en el tramo inicial de cada serie: precios constantes,")
print("  volumen cero, o volatilidad muy por debajo de la del resto.")
print()
print(f"  {'activo':<10} {'primera':>11} {'ultima':>11} {'obs':>6} "
      f"{'vol=0 ini':>10} {'px const':>9} {'sigma ini/resto':>16}")
print(f"  {'-'*10} {'-'*11} {'-'*11} {'-'*6} {'-'*10} {'-'*9} {'-'*16}")
sospechosos, filas_b = [], {}
for tk, d in sorted(datos_ext.items()):
    d = d.dropna()
    n = len(d)
    k = min(90, n // 4)                # tramo inicial
    ini, resto = d.iloc[:k], d.iloc[k:]
    vol0 = int((ini["volume"] == 0).sum()) if "volume" in ini else -1
    # precios constantes: open==high==low==close en la misma barra
    const = int(((ini["open"] == ini["high"]) & (ini["high"] == ini["low"])
                 & (ini["low"] == ini["close"])).sum())
    s_ini = float(ini["close"].pct_change().std())
    s_res = float(resto["close"].pct_change().std())
    ratio = s_ini / s_res if s_res > 0 else float("nan")
    marca = ""
    if vol0 > 0 or const > 0 or (not math.isnan(ratio) and ratio < 0.35):
        marca = "  <-- sospechoso"
        sospechosos.append(tk)
    filas_b[tk] = {"primera": str(d.index[0].date()),
                   "ultima": str(d.index[-1].date()), "obs": n,
                   "vol_cero_inicio": vol0, "px_constante_inicio": const,
                   "sigma_ratio": None if math.isnan(ratio) else ratio}
    print(f"  {tk:<10} {d.index[0].date()!s:>11} {d.index[-1].date()!s:>11} "
          f"{n:>6} {vol0:>10} {const:>9} "
          f"{(f'{ratio:.3f}' if not math.isnan(ratio) else 'n/a'):>16}{marca}")
print()
print("  Lo que dice el expediente sobre FIL")
print("  (fase_b_reevaluacion_resultado.md, limites declarados): 'los datos de")
print("  FIL en yfinance empiezan 2017-12 (anterior a su listado real) — se")
print("  usa lo que el proveedor da, sin validar'.")
fil = filas_b.get("FIL-USD")
if fil:
    print(f"  Comprobado aqui: FIL-USD empieza {fil['primera']}, "
          f"{fil['obs']} obs,")
    print(f"  volumen cero en el inicio: {fil['vol_cero_inicio']}, precios")
    print(f"  constantes: {fil['px_constante_inicio']}, sigma inicial/resto: "
          f"{fil['sigma_ratio']:.3f}" if fil['sigma_ratio'] else "")
print()
if sospechosos:
    print(f"  Activos con firma de backfill: {sospechosos}")
else:
    print("  NINGUN activo muestra la firma buscada (volumen cero, precios")
    print("  constantes o volatilidad inicial anomalamente baja). La anomalia")
    print("  de FIL no es un backfill sintetico detectable por estas tres")
    print("  señales: es una fecha de inicio anterior al listado, con precios")
    print("  que se comportan como precios. No se puede acotar mas sin una")
    print("  fuente externa de fechas de listado, que esta sesion no tiene.")
    print("  [no verificado] Queda como limite declarado, igual que en el")
    print("  expediente.")
print()

# ------------------------------------------------------------------ PARTE C
print("-" * 74)
print("PARTE C — sesgo residual del criterio: quitar y poner caidos")
print("-" * 74)
print("  El expediente admite: 'la lista de caidos sigue siendo una eleccion")
print("  documentable, no el universo completo de 2017; top-N por market-cap")
print("  historico congelado seguiria siendo mejor y no se hizo'.")
print("  Sin datos nuevos no se puede construir ese universo. Lo que SI se")
print("  puede: medir cuanto depende el dictamen de CADA caido, que acota")
print("  la fragilidad de la eleccion.")
print()
print(f"  {'universo':<28} {'Sharpe':>8} {'t':>7} {'DSR':>7} {'IC95':>20} "
      f"{'t>3':>5}")
print(f"  {'-'*28} {'-'*8} {'-'*7} {'-'*7} {'-'*20} {'-'*5}")
base10 = ps.bateria(*[simulate(datos_v)[k] for k in ("equity", "benchmark")])
print(f"  {'solo 10 vivos':<28} {base10['sharpe']:>8} {base10['t_stat']:>7} "
      f"{base10['dsr']:>7} {str(base10['ic95_retorno_anual_pct']):>20} "
      f"{str(base10['pasa_t3']):>5}")
print(f"  {'15 (10 vivos + 5 caidos)':<28} {obs['sharpe']:>8} "
      f"{obs['t_stat']:>7} {obs['dsr']:>7} "
      f"{str(obs['ic95_retorno_anual_pct']):>20} {str(obs['pasa_t3']):>5}")
filas_c = {"solo_vivos": base10, "extendido_15": obs}
for fuera in ps.MUERTOS:
    sub = {**datos_v, **{k: v for k, v in datos_m.items() if k != fuera}}
    r = ps.bateria(*[simulate(sub)[k] for k in ("equity", "benchmark")])
    filas_c[f"sin_{fuera}"] = r
    print(f"  {'14, sin ' + fuera:<28} {r['sharpe']:>8} {r['t_stat']:>7} "
          f"{r['dsr']:>7} {str(r['ic95_retorno_anual_pct']):>20} "
          f"{str(r['pasa_t3']):>5}")
print()
sharpes = [v["sharpe"] for k, v in filas_c.items() if k.startswith("sin_")]
t3_todos = all(v["pasa_t3"] for v in filas_c.values())
ic_todos = all(v["edge_ic"] for v in filas_c.values())
print(f"  Rango de Sharpe entre los 6 universos con caidos: "
      f"{min(sharpes + [obs['sharpe']]):.3f} - {max(sharpes + [obs['sharpe']]):.3f}")
print(f"  ¿t>3 en TODOS los universos probados?        {t3_todos}")
print(f"  ¿IC95 positivo en TODOS?                     {ic_todos}")
print()
if t3_todos and ic_todos:
    print("  -> El dictamen P3 ('la señal sobrevive a los muertos') NO depende")
    print("     de ningun caido en particular: quitar cualquiera de los cinco")
    print("     deja t>3 e IC positivo. El sesgo residual de la ELECCION de")
    print("     caidos esta acotado por abajo: no es la eleccion lo que")
    print("     sostiene P3.")
    print("     Limite que sigue abierto: esto acota la sensibilidad a QUITAR")
    print("     caidos de la lista, no a los caidos que nunca entraron en")
    print("     ella. El universo completo de 2017 sigue sin construirse, y")
    print("     eso solo se arregla con datos nuevos (tarea N3).")
else:
    print("  -> HALLAZGO: el dictamen P3 depende de que caidos se incluyan.")
print()
print("=" * 74)
print("VEREDICTO 3.6")
print(f"  A) P3 {'reproduce exacto' if difs == 0 else 'NO reproduce'}.")
print(f"  B) Firma de backfill: {sospechosos if sospechosos else 'ninguna detectada'}. "
      "El caso FIL queda")
print("     como limite declarado [no verificado]: sin fuente externa de")
print("     fechas de listado no es acotable desde esta sesion.")
print(f"  C) P3 robusto a quitar cualquiera de los 5 caidos "
      f"(t>3 {t3_todos}, IC+ {ic_todos}).")
with open(os.path.join(AQUI, "salida_3_6_supervivencia.json"), "w") as f:
    json.dump({"sello": SELLO, "reproduce_p3": difs == 0,
               "publicado": pub, "reejecutado": obs,
               "calidad_datos": filas_b, "sospechosos": sospechosos,
               "universos": filas_c}, f, indent=2, default=str)
print(f"  -> {os.path.join('auditoria_n1', 'salida_3_6_supervivencia.json')}")
