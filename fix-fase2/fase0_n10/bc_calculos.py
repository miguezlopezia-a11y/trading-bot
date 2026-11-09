#!/usr/bin/env python3
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out = {}


def impuesto_ahorro(ganancia):
    restante = max(0.0, ganancia)
    impuesto = 0.0
    anterior = 0.0
    for techo, tipo in [(6000, 0.19), (50000, 0.21), (200000, 0.23), (300000, 0.27)]:
        tramo = min(restante, techo - anterior)
        if tramo > 0:
            impuesto += tramo * tipo
            restante -= tramo
        anterior = techo
    return impuesto + restante * 0.28


print("=== B-1: contraste múltiple ===")
n_lags = 4 + 3 + 3
n_estimaciones = 18 * n_lags * 2
n_por_mitad = 18 * n_lags
print(f"18 mercados x (4 ACF + 3 VR + 3 |r|) x 2 mitades = {n_estimaciones} estimaciones")
print(f"por mitad = {n_por_mitad}; alfa Bonferroni global 0.05/{n_estimaciones} = {0.05/n_estimaciones:.10f}")
print(f"alfa Bonferroni por mitad 0.05/{n_por_mitad} = {0.05/n_por_mitad:.10f}")
out["b1"] = {"estimaciones": n_estimaciones, "por_mitad": n_por_mitad, "alfa_global": 0.05/n_estimaciones}

print("\n=== B-2: autocorrelación diaria mínima, modelo AR(1) gaussiano ideal ===")
c = 0.0005
for sigma in [0.01, 0.02]:
    rho = c / (sigma * math.sqrt(2 / math.pi))
    print(f"coste_ida_vuelta={c:.4f} vol_diaria={sigma:.2f} -> rho_min={rho:.6f} ({100*rho:.3f} %)")
    out.setdefault("b2", []).append({"coste": c, "sigma": sigma, "rho_min": rho})
print("Fórmula: E[r_t sign(r_(t-1))] = rho*sigma*sqrt(2/pi); se exige que supere el coste.")

print("\n=== B-3: dependencia de Yahoo y ETFs con historia limitada ===")
etfs = ["EEM", "IEF", "TLT", "DBC", "VNQ", "URTH"]
print(f"series_yahoo=18/18; ETFs={len(etfs)}/18 ({','.join(etfs)}); porcentaje_ETFs={100*len(etfs)/18:.3f} %")
out["b3"] = {"series_yahoo": 18, "etfs": etfs}

print("\n=== B-4: impuesto anual frente a diferido, 100.000 €, bruto 7 %, 20 años ===")
for tipo in [0.19, 0.28]:
    anual = (1 + 0.07 * (1 - tipo)) ** 20
    diferido = 1 + (1 - tipo) * ((1.07) ** 20 - 1)
    diferencia = 100000 * (diferido - anual)
    print(f"IRPF={100*tipo:.0f} %: final_anual={100000*anual:.2f} € final_diferido={100000*diferido:.2f} € diferencia={diferencia:.2f} €")
    out.setdefault("b4", []).append({"tipo": tipo, "final_anual": 100000*anual, "final_diferido": 100000*diferido, "diferencia": diferencia})

print("\n=== B-6: capital para que 2.400 €/año de sistema no superen el exceso ===")
for exceso in [0.01, 0.03, 0.056133]:
    capital = 2400 / exceso
    print(f"coste=2400 €/año exceso_neto={100*exceso:.4f} % -> capital_min={capital:.2f} €")
    out.setdefault("b6", []).append({"exceso": exceso, "capital_min": capital})
print("El 2.400 € es el ejemplo del brief, no un presupuesto medido de este sistema.")

print("\n=== Paso C: escenarios condicionados, no retornos esperados verificados ===")
dfr = 0.025
for nombre, bruto in [("C-1_mundo", 0.0943), ("C-2_tendencia", 0.049)]:
    filas = []
    for capital in [1000, 10000, 100000]:
        ganancia = capital * bruto
        neta = ganancia - impuesto_ahorro(ganancia)
        deposito = capital * dfr
        deposito_neto = deposito - impuesto_ahorro(deposito)
        mundo = capital * 0.0943
        mundo_neto = mundo - impuesto_ahorro(mundo)
        fila = {
            "capital": capital,
            "candidata_neta": neta,
            "vs_dfr": neta - deposito_neto,
            "vs_mundo": neta - mundo_neto,
        }
        filas.append(fila)
        print(f"{nombre} capital={capital} neta={neta:.2f} € vs_DFR={neta-deposito_neto:+.2f} € vs_mundo={neta-mundo_neto:+.2f} €")
    out[nombre] = {"bruto_supuesto": bruto, "filas": filas}
print("Insumos del brief, NO verificados hoy: mundo bruto 9,43 %; tendencia profesional bruta 4,9 %; DFR 2,5 %.")
print("IRPF calculado como realización anual, tramos 19 %/21 %; no incluye comisiones ni coste del sistema.")
print("N_vigente=16 -> N_candidata=17")
print("Coste de descarte estimado: C-1=1 hora; C-2=4 horas; ninguna se ejecuta con Yahoo en NO-GO.")

path = ROOT / "fix-fase2/fase0_n10/salida_bc_calculos.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print(f"\nsalida={path.relative_to(ROOT)}")
