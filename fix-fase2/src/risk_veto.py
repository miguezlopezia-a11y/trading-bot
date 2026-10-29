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
# Tolerancia numerica (decision de Pablo, 2026-10-07): el backtester calcula
# el sizing sobre cash y el veto lo mide sobre equity al cierre de la vela de
# entrada; el slippage + ese desajuste cash-vs-equity produce un exceso
# medido de ~7.5e-6 sobre el 5% nominal en operaciones que SI respetan la
# politica real. Epsilon = 1e-4 (13x ese ruido) absorbe el redondeo sin
# dejar pasar un sizing de verdad excesivo (p.ej. 0.06 sigue vetado).
SIZE_MAX_EPSILON = 1e-4
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
    if isinstance(sizing, (int, float)) and sizing > SIZE_MAX + SIZE_MAX_EPSILON:
        motivos.append(f"sizing_sobre_limite:{sizing}>{SIZE_MAX}+eps")
    if isinstance(dd, (int, float)) and dd < DD_MAX_PCT:
        motivos.append(f"dd_sobre_umbral:{dd}<{DD_MAX_PCT}")

    return {"vetado": bool(motivos), "motivos": motivos,
            "limites": {"size_max": SIZE_MAX, "size_max_epsilon": SIZE_MAX_EPSILON, "dd_max_pct": DD_MAX_PCT,
                        "estrategias_descartadas": sorted(ESTRATEGIAS_DESCARTADAS)}}
