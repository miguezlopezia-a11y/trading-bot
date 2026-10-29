import sys
sys.path.insert(0, "src")

from deliberation import deliberar, valida_deliberacion, provider_disponible, OpenRouterProvider

assert provider_disponible(), "provider_disponible() False"

candidato = {
    "estrategia": "ma_cross", "activo": "BTC-USD", "direccion": "long",
    "sizing": 0.012, "dd_proyectado_pct": -3.2,
    "contexto": {"entry_price": 61000.0, "stop": 59050.0, "target": 64200.0,
                 "equity_entry": 10000.0, "motivo_salida": "take_profit",
                 "dictamen": "walkforward_fragil_modo_observacion"},
}

provider = OpenRouterProvider()
d = deliberar(candidato, provider)

print("veredicto_global:", d["veredicto"], "| size_final:", d["size_final"],
      "| motivo:", d["motivo"])
for nombre, s in d["sombreros"].items():
    print(f"  {nombre}: veredicto={s['veredicto']} size_ajuste={s['size_ajuste']} "
          f"reparado={s['reparado']} justificacion={s['justificacion'][:90]!r}")

assert valida_deliberacion(d), "salida no pasa valida_deliberacion()"
n_prov_err = sum(1 for s in d["sombreros"].values()
                  if "proveedor_indisponible" in s["justificacion"])
print(f"\nsombreros con proveedor_indisponible: {n_prov_err}/6")
print("SMOKE_OPENROUTER_REAL_OK" if n_prov_err == 0 else "SMOKE_OPENROUTER_REAL_FALLO_PROVEEDOR")
