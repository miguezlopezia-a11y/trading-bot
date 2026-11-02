"""N7 · B-d, B-e, B-f — tres objeciones propias, medidas.
Corre DESDE fix-fase2/.  Salida: b_def_salida.json

B-d  El Sharpe del diferencial NO es la diferencia de Sharpes, y la §4.3
     mezcla las dos lecturas.
B-e  Los dias con exposure = 0: en la construccion (a) el diferencial es
     negativo POR CONSTRUCCION esos dias, y no es una comparacion.
B-f  PPY = 365 para cripto, y el recuento de construcciones de metrica.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import portfolio_runner as pr  # noqa: E402

SELLO = "20261007"


def sharpe(x):
    v = np.asarray(x, dtype=float); v = v[~np.isnan(v)]
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(pr.PPY)) if len(v) > 1 and sd > 0 else 0.0


def main():
    datos = pr.cargar_congelados(pr.ACTIVOS, stamp=SELLO, verbose=False)
    res = pr.simulate(datos)
    e = res["exposure"].values
    r_est = res["equity"].pct_change().fillna(0.0).values
    r_ben = res["benchmark"].pct_change().fillna(0.0).values
    coste = res["costes"].values
    rp = res["rp"].values
    a = e * r_ben                      # (a) alineada
    d = r_est - a                      # el diferencial de la §4.3
    out = {}

    print("=== B-d el Sharpe del diferencial no es la diferencia de Sharpes ===")
    s_e, s_a, s_d = sharpe(r_est), sharpe(a), sharpe(d)
    rho = float(np.corrcoef(r_est, a)[0, 1])
    print(f"  Sharpe(estrategia)            = {s_e:.6f}")
    print(f"  Sharpe((a) bench igualado)    = {s_a:.6f}")
    print(f"  Sharpe(estrategia) - Sharpe(a)= {s_e - s_a:+.6f}   <- la lectura de B-a")
    print(f"  Sharpe(d), d = r_est - r_a    = {s_d:+.6f}   <- la lectura de la §4.3")
    print(f"  LAS DOS CIFRAS NO SON LA MISMA. Difieren en {s_d-(s_e-s_a):+.6f}")
    print(f"  correlacion entre las dos series: rho = {rho:.6f}")
    print(f"  sd diaria: estrategia {np.std(r_est,ddof=1):.6f}  "
          f"(a) {np.std(a,ddof=1):.6f}  diferencial {np.std(d,ddof=1):.6f}")
    print(f"  el diferencial tiene {np.std(d,ddof=1)/np.std(r_est,ddof=1):.3f}x la sd")
    print("  de la estrategia: al compartir los mismos retornos subyacentes, la")
    print("  resta cancela el factor comun y lo que queda es casi todo senal de")
    print("  ponderacion. Eso hace el Sharpe(d) MAS informativo, no menos --")
    print("  pero es OTRA cantidad, con otro signo posible y otro umbral.")
    print(f"  media anualizada de d: {365*np.mean(d)*100:+.4f} %/ano")
    print(f"  signo: Sharpe(d) {'>' if s_d>0 else '<'} 0  y  "
          f"Sharpe(est)-Sharpe(a) {'>' if s_e-s_a>0 else '<'} 0"
          f"  -> {'COINCIDEN' if (s_d>0)==(s_e-s_a>0) else 'SE CONTRADICEN EN SIGNO'}")
    out["B-d"] = {"sharpe_est": s_e, "sharpe_a": s_a,
                  "dif_de_sharpes": s_e - s_a, "sharpe_del_diferencial": s_d,
                  "rho": rho, "sd_est": float(np.std(r_est, ddof=1)),
                  "sd_a": float(np.std(a, ddof=1)),
                  "sd_d": float(np.std(d, ddof=1)),
                  "media_anual_d_pct": float(365 * np.mean(d) * 100),
                  "mismo_signo": bool((s_d > 0) == (s_e - s_a > 0))}

    print("\n=== B-e los dias con exposure = 0 ===")
    z = e <= 1e-12
    nz = ~z
    print(f"  dias con exposure=0 : {int(z.sum())} de {len(e)}"
          f"  ({100*z.mean():.2f} %)")
    print(f"  en esos dias:  r_bench_igualado = exposure*r_bench = 0 SIEMPRE")
    print(f"                 r_estrategia     = r_p - coste = 0 - coste")
    print(f"  suma de costes en dias de exposure=0 : {coste[z].sum():.6f}"
          f"  ({100*coste[z].sum():.4f} % de capital acumulado, sin componer)")
    print(f"  dias de exposure=0 con coste > 0     : {int((coste[z]>1e-15).sum())}")
    print(f"  r_p en dias de exposure=0: max|r_p| = {np.abs(rp[z]).max():.3e}"
          f"  (debe ser 0)")
    print(f"  diferencial medio en dias exposure=0 : {d[z].mean():+.8e}")
    print(f"  diferencial medio en dias exposure>0 : {d[nz].mean():+.8e}")
    print(f"  d<0 por construccion en {int((d[z]<0).sum())} de {int(z.sum())}"
          f" dias de exposure=0")
    s_d_nz = sharpe(d[nz])
    print(f"  Sharpe(d) con TODOS los dias        : {s_d:+.6f}")
    print(f"  Sharpe(d) SOLO dias con exposure>0  : {s_d_nz:+.6f}")
    print(f"  los 915 ceros mueven el Sharpe(d) en {s_d - s_d_nz:+.6f}")
    print("  LECTURA, con la cifra medida y no la que yo esperaba: en el")
    print("  20.8 % de los dias la construccion (a) no compara nada -- las dos")
    print("  series estan fuera del mercado. Pero el diferencial NO es negativo")
    print(f"  'garantizado': solo {int((coste[z]>1e-15).sum())} de {int(z.sum())}"
          f" de esos dias llevan coste, y en los otros")
    print(f"  {int(z.sum())-int((coste[z]>1e-15).sum())} d(t) es EXACTAMENTE 0."
          " Y el efecto neto de los ceros va A FAVOR")
    print(f"  de Fase B: suben el Sharpe(d) en {s_d - s_d_nz:+.6f}, porque"
          " diluyen una media")
    print("  negativa con ceros. Mi objecion apuntaba al signo contrario del")
    print("  que tiene: queda en MEDIA y con la direccion corregida.")
    print("  Lo que si sobrevive: la §4.3 define d(t) sobre 4403 dias sin decir")
    print("  que en 898 de ellos d(t)=0 por construccion, y un IC de bootstrap")
    print("  sobre una serie con el 20 % de ceros exactos no tiene la misma")
    print("  lectura que uno sobre 4403 comparaciones efectivas. n efectivo de")
    print(f"  comparacion = {int(nz.sum())}, no {len(e)}.")
    out["B-e"] = {"dias_cero": int(z.sum()), "pct_cero": float(100 * z.mean()),
                  "coste_en_dias_cero": float(coste[z].sum()),
                  "dias_cero_con_coste": int((coste[z] > 1e-15).sum()),
                  "max_abs_rp_en_ceros": float(np.abs(rp[z]).max()),
                  "d_medio_ceros": float(d[z].mean()),
                  "d_medio_no_ceros": float(d[nz].mean()),
                  "dias_cero_con_d_negativo": int((d[z] < 0).sum()),
                  "sharpe_d_todos": s_d, "sharpe_d_sin_ceros": s_d_nz,
                  "efecto_de_los_ceros": s_d - s_d_nz,
                  "n_efectivo_de_comparacion": int(nz.sum()),
                  "direccion": "los ceros FAVORECEN a Fase B (+0.033 de Sharpe(d))",
                  "severidad": "MEDIA (bajada de ALTA: mi objecion tenia el signo al reves)"}

    print("\n=== B-f.1 PPY = 365 para cripto: ¿correcto? ===")
    idx = res["exposure"].index
    dias_cal = (idx[-1] - idx[0]).days + 1
    print(f"  rango {idx[0].date()} -> {idx[-1].date()} = {dias_cal} dias naturales")
    print(f"  filas en la serie                      = {len(idx)}")
    print(f"  huecos de calendario                   = {dias_cal - len(idx)}")
    print(f"  dias por ano implicitos                = {len(idx)/((idx[-1]-idx[0]).days/365.25):.2f}")
    print("  cripto cotiza los 365 dias: PPY=365 es correcto. Y ADEMAS es")
    print("  IRRELEVANTE para el veredicto: sqrt(365) escala por igual las dos")
    print("  series, luego no cambia el signo de ningun diferencial.")
    print("  -> objecion RETIRADA: era mia, no del expediente.")
    out["B-f1_PPY"] = {"dias_calendario": int(dias_cal), "filas": int(len(idx)),
                       "huecos": int(dias_cal - len(idx)),
                       "veredicto": "RETIRADA: PPY=365 correcto e irrelevante al signo"}

    print("\n=== B-f.2 el contador de construcciones de metrica ===")
    print("  N6 (su B-d) establecio que existe un contador no llevado de")
    print("  'construcciones de metrica probadas' y que iba por 5.")
    nuevas = ["(a) escalado dia a dia alineado",
              "(a') escalado con el retardo del brief",
              "(b) escalado por constante (no-op en Sharpe)",
              "(c) binario alineado", "(c') binario con el retardo del brief",
              "EW con coste real de rebalanceo", "B&H puro",
              "B&H universo fijo del primer dia", "B&H de BTC solo",
              "panel de 15 igualado"]
    print(f"  esta Fase 0 ha medido {len(nuevas)} construcciones de benchmark:")
    for n in nuevas:
        print(f"    - {n}")
    print("  La §4.2 del brief multiplica cada fila de la §4.1 por 2^4 hilos:")
    print("    2 paneles x 3 construcciones x 2 costes x 2 rf x 2 rebalanceo")
    print("    x 2 regla de entrada = 96 filas.")
    print("  El brief dice 'no es un menu del que elegir: es una tabla con")
    print("  todas las filas'. Una tabla de 96 filas de la que Pablo elige SI")
    print("  es un menu: es exactamente la maquina de metric-shopping que")
    print("  N6 · B-d nombro. Que las filas esten todas no lo arregla.")
    out["B-f2_contador"] = {"construcciones_medidas_aqui": nuevas,
                             "filas_que_pide_la_seccion_4_2": 96,
                             "contador_N6": 5}

    json.dump(out, open("fase0_n7/b_def_salida.json", "w"), indent=2)
    print("\n-> fase0_n7/b_def_salida.json")


if __name__ == "__main__":
    main()
