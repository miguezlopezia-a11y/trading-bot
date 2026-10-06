"""Veto de riesgo (Risk): el UNICO modulo con potestad de veto.

Reglas duras (deterministas, sin LLM):
  1. sizing propuesto > SIZE_MAX (default 0.05 = 5% del equity) -> veto.
  2. drawdown proyectado > DD_MAX (default -10%) -> veto.
  3. estrategia en ESTRATEGIAS_DESCARTADAS (las 3 no-ma_cross, descartadas por
     los datos en Fase 1) -> veto SIEMPRE, con o sin LLM.

evaluar_veto() nunca lanza y nunca depende del proveedor LLM. En modo sombra
su resultado se registra junto a la deliberacion; el paper runner no ejecuta
nada de todas formas.
"""

SIZE_MAX = 0.05
DD_MAX_PCT = -10.0
ESTRATEGIAS_DESCARTADAS = {"mean_reversion", "breakout", "trend_following"}


def evaluar_veto(candidato: dict) -> dict:
    """candidato: {estrategia, sizing (fraccion equity), dd_proyectado_pct}.
    Devuelve {"vetado": bool, "motivos": [...]} — siempre parseable."""
    motivos = []
    estrategia = candidato.get("estrategia")
    sizing = candidato.get("sizing")
    dd = candidato.get("dd_proyectado_pct")

    if estrategia in ESTRATEGIAS_DESCARTADAS:
        motivos.append(f"estrategia_descartada:{estrategia}")
    if isinstance(sizing, (int, float)) and sizing > SIZE_MAX:
        motivos.append(f"sizing_sobre_limite:{sizing}>{SIZE_MAX}")
    if isinstance(dd, (int, float)) and dd < DD_MAX_PCT:
        motivos.append(f"dd_sobre_umbral:{dd}<{DD_MAX_PCT}")

    return {"vetado": bool(motivos), "motivos": motivos,
            "limites": {"size_max": SIZE_MAX, "dd_max_pct": DD_MAX_PCT,
                        "estrategias_descartadas": sorted(ESTRATEGIAS_DESCARTADAS)}}
