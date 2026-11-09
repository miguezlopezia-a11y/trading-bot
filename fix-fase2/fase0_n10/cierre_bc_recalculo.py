#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"fix-fase2/fase0_n10"
a3=json.loads((BASE/"salida_cierre_a3_series_y_huecos.json").read_text())
a5=json.loads((BASE/"salida_cierre_a5_ajuste_y_urth.json").read_text())
a6=json.loads((BASE/"salida_cierre_a6_dfr_sg.json").read_text())
mundo=a5["urth"]["cagr_adjclose"]
dfr=a6["bce"]["valor_pct"]/100


def impuesto(ganancia):
    restante=max(0.0,ganancia); total=0.0; anterior=0.0
    for techo,tipo in [(6000,0.19),(50000,0.21),(200000,0.23),(300000,0.27)]:
        tramo=min(restante,techo-anterior)
        if tramo>0: total+=tramo*tipo; restante-=tramo
        anterior=techo
    return total+restante*0.28


def neta(capital,tasa):
    bruta=capital*tasa
    return bruta-impuesto(bruta)

print("=== A-3: series utilizables sin huecos ni cierres nulos ===")
limpias=[]; excluidas=[]
for s in a3["series"]:
    if s["n_huecos"]==0 and not s["cierres_nulos"]:
        limpias.append(s["ticker"])
    else:
        excluidas.append(s["ticker"])
print(f"limpias={len(limpias)}/18: {','.join(limpias)}")
print(f"excluidas={len(excluidas)}/18: {','.join(excluidas)}")

print("=== Recalculo B-6 y Paso C ===")
print(f"fuente_URTH=salida_cierre_a5_ajuste_y_urth.json CAGR_adjclose={100*mundo:.6f} %")
print(f"fuente_DFR=salida_cierre_a6_dfr_sg.json fecha={a6['bce']['fecha']} DFR={100*dfr:.3f} %")
exceso_pequeno=(neta(1000,mundo)-neta(1000,dfr))/1000
print(f"B-6 exceso_neto_mundo_menos_DFR={100*exceso_pequeno:.6f} %; capital_min_con_coste_2400={2400/exceso_pequeno:.2f} €")

salida={"mundo_cagr":mundo,"dfr":dfr,"limpias":limpias,"excluidas":excluidas,
        "b6_exceso_neto":exceso_pequeno,"b6_capital_min":2400/exceso_pequeno,"candidatas":{}}
for nombre,tasa in [("C-1_mundo",mundo),("C-2_tendencia",0.049)]:
    filas=[]
    for capital in [1000,10000,100000]:
        valor=neta(capital,tasa); deposito=neta(capital,dfr); referencia=neta(capital,mundo)
        fila={"capital":capital,"neta":valor,"vs_dfr":valor-deposito,"vs_mundo":valor-referencia}
        filas.append(fila)
        print(f"{nombre} capital={capital} neta={valor:.2f} € vs_DFR={valor-deposito:+.2f} € vs_mundo={valor-referencia:+.2f} €")
    salida["candidatas"][nombre]={"tasa_bruta":tasa,"filas":filas}
print("C-1 usa CAGR histórico medido, no esperanza futura; C-2 conserva 4,9 % secundario [no verificado].")
print("IRPF como realización anual; sin comisiones ni coste de sistema.")
out=BASE/"salida_cierre_bc_recalculo.json"
out.write_text(json.dumps(salida,ensure_ascii=False,indent=2)+"\n")
print(f"salida={out.relative_to(ROOT)}")
