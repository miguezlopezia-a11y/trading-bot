"""1.1 — Deliberacion 6 Sombreros del Analista (MODO SOMBRA).

Dado un candidato de senal (estrategia, activo, direccion, contexto), produce
una deliberacion estructurada: 6 llamadas LLM independientes (hechos,
emociones/premortem, riesgo, beneficios, creatividad, proceso/gestion), cada
una con system prompt propio. Veredicto global si/no/size ajustado con
justificacion por sombrero. Salida JSON determinista con schema validado:
si el LLM devuelve basura -> reintento con reparacion; si persiste -> veto por
defecto (veredicto "no", motivo veto_por_defecto_parse, SIEMPRE parseable).

MODO SOMBRA: este modulo NUNCA ejecuta ni bloquea nada. El veto final lo tiene
Risk (src/risk_veto.py). La deliberacion solo se registra en el journal junto a
la decision del paper runner.

Proveedores: interfaz Provider; KimiProvider (usa MAIA_KIMI_KEY, proxy Kimi
compatible con Anthropic Messages API — PREFERIDO, cubre el proyecto sin saldo
Anthropic desde agosto 2026); AnthropicProvider (usa ANTHROPIC_API_KEY, fallback
si algun dia hay saldo); FakeProvider determinista para tests. Sin ninguna key ->
deliberar() no se invoca; el runner registra deliberacion "no_disponible" (ver
paper_runner.py).
"""
import hashlib
import json
import os
from datetime import datetime, timezone

# Carga MAIA_KIMI_KEY desde /root/maia/.env si no esta ya en el entorno
# (mismo patron que bunker-2026/bot.py: setdefault, nunca sobreescribe).
for _env_path in ("/root/maia/.env",):
    try:
        with open(_env_path, encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip().removeprefix("export").strip(), _v.strip())
    except (FileNotFoundError, PermissionError):
        pass

SOMBREROS = {
    "hechos": ("Eres el Sombrero Blanco (hechos). Analiza SOLO hechos verificables "
               "del candidato: datos de la senal, contexto de mercado proporcionado, "
               "cifras del backtest. Prohibido especular."),
    "premortem": ("Eres el Sombrero Rojo emocional con enfoque premortem: imagina que "
                  "la operacion salio mal y describe las emociones/razones por las que "
                  "te empujaron a entrar. Senala sesgos (FOMO, anclaje, rencor)."),
    "riesgo": ("Eres el Sombrero Negro (riesgo catastrofista). Enumera todo lo que "
               "puede salir mal: slippage, gaps, regimen de mercado, cola de la "
               "distribucion. Cuantifica en terminos del contexto dado."),
    "beneficios": ("Eres el Sombrero Amarillo (beneficios). Argumentos a favor REALES "
                   "(no optimismo vacio): que hay de cierto en la senal, edge conocido, "
                   "con texto del backtest."),
    "creatividad": ("Eres el Sombrero Verde (creatividad): alternativas no obvias, "
                    "variaciones de la senal, formas de reducir coste/riesgo que el "
                    "enfoque mecanico no ve."),
    "proceso": ("Eres el Sombrero Azul (control de proceso): evalua la senal contra el "
                "PROCESO (candidata debil en modo observacion, walk-forward fragil, "
                "reglas de riesgo). Veredicto de gestion, no de mercado."),
}

CANDIDATO_SCHEMA = ("Responde SOLO con JSON valido y nada mas, con exactamente estas "
                    "claves: {\"veredicto\": \"si\"|\"no\"|\"ajustar\", "
                    "\"size_ajuste\": <numero entre 0 y 1 o null>, "
                    "\"justificacion\": <string corto>}. "
                    "veredicto \"ajustar\" exige size_ajuste numerico.")

VERDICTOS_VALIDOS = {"si", "no", "ajustar"}


def prompt_sha256(sombrero: str) -> str:
    return hashlib.sha256((SOMBREROS[sombrero][0] + CANDIDATO_SCHEMA)
                          .encode()).hexdigest()[:16]


# ------------------------------------------------------------------ providers

class Provider:
    """Interfaz: complete(system_prompt, user_message) -> texto crudo del LLM."""

    def complete(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError


class AnthropicProvider(Provider):
    def __init__(self, api_key=None, model=None, max_tokens=512):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        assert self.api_key, "ANTHROPIC_API_KEY no disponible"
        self.model = model or os.environ.get("DELIBERATION_MODEL",
                                             "claude-sonnet-4-5")
        self.max_tokens = max_tokens

    def complete(self, system_prompt: str, user_message: str) -> str:
        import urllib.request
        body = json.dumps({
            "model": self.model, "max_tokens": self.max_tokens,
            "system": system_prompt, "messages": [{"role": "user",
                                                   "content": user_message}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return "".join(b.get("text", "") for b in data.get("content", [])
                       if b.get("type") == "text")


class KimiProvider(Provider):
    """Proveedor preferido: proxy Kimi compatible con Anthropic Messages API
    (ver bunker-2026/bot.py:call_kimi). Mismo formato de body que Anthropic;
    headers propios (Bearer, no x-api-key). Cubre el proyecto sin saldo
    Anthropic, decision de agosto 2026."""

    def __init__(self, api_key=None, model=None, max_tokens=512):
        self.api_key = api_key or os.environ.get("MAIA_KIMI_KEY")
        assert self.api_key, "MAIA_KIMI_KEY no disponible"
        self.model = model or os.environ.get("DELIBERATION_MODEL_KIMI",
                                             "kimi-for-coding")
        self.max_tokens = max_tokens

    def complete(self, system_prompt: str, user_message: str) -> str:
        import urllib.request
        body = json.dumps({
            "model": self.model, "max_tokens": self.max_tokens,
            "system": system_prompt, "messages": [{"role": "user",
                                                   "content": user_message}],
        }).encode()
        req = urllib.request.Request(
            "https://api.kimi.com/coding/v1/messages", data=body,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        if not text.strip():
            # gotcha real de produccion (bot.py:559-562): Kimi a veces devuelve
            # solo bloques "thinking" sin bloque "text" -> usar ese contenido.
            text = "".join(b.get("thinking", "") for b in blocks
                          if b.get("type") == "thinking")
        return text


class FakeProvider(Provider):
    """Determinista para tests: responde segun una cola de respuestas
    prefijadas, o con un veredicto fijo."""

    def __init__(self, respuestas=None, default='{"veredicto": "si", '
                                               '"size_ajuste": null, '
                                               '"justificacion": "fake determinista"}'):
        self.respuestas = list(respuestas or [])
        self.default = default

    def complete(self, system_prompt: str, user_message: str) -> str:
        if self.respuestas:
            return self.respuestas.pop(0)
        return self.default


def provider_disponible() -> bool:
    return bool(os.environ.get("MAIA_KIMI_KEY") or os.environ.get("ANTHROPIC_API_KEY"))


# ------------------------------------------------------------------ parsing

def _extract_json(text: str) -> dict:
    """Extrae el primer objeto JSON de texto; valida campos y tipos."""
    start = text.find("{")
    if start < 0:
        raise ValueError("sin JSON en la respuesta")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    obj = json.loads(text[start:i + 1])
                    _valida_schema(obj)
                    return obj
    raise ValueError("JSON truncado")


def _valida_schema(obj):
    if not isinstance(obj, dict):
        raise ValueError("no es un objeto")
    if set(obj.keys()) != {"veredicto", "size_ajuste", "justificacion"}:
        raise ValueError(f"claves inesperadas: {sorted(obj.keys())}")
    if obj["veredicto"] not in VERDICTOS_VALIDOS:
        raise ValueError(f"veredicto invalido: {obj['veredicto']!r}")
    if obj["veredicto"] == "ajustar":
        if not isinstance(obj["size_ajuste"], (int, float)):
            raise ValueError("ajustar sin size_ajuste numerico")
        if not (0 <= obj["size_ajuste"] <= 1):
            raise ValueError("size_ajuste fuera de [0,1]")
    else:
        if obj["size_ajuste"] is not None:
            raise ValueError("size_ajuste debe ser null sin 'ajustar'")
    if not isinstance(obj["justificacion"], str) or not obj["justificacion"]:
        raise ValueError("justificacion vacia")


def _llama_sombrero(provider, sombrero, candidato):
    """Una llamada por sombrero. Distingue dos fallos distintos:
      - proveedor caido/sin credito (excepcion de complete): SIN reintento,
        marca {"_proveedor_error": tipo}.
      - respuesta no parseable (el LLM habla pero no cumple schema): reintento
        con reparacion (1 vez); si persiste, veto por defecto.
    Devuelve (respuesta_dict|None, info_error|None, reparado)."""
    sys_prompt = SOMBREROS[sombrero][0] + " " + CANDIDATO_SCHEMA
    user = json.dumps(candidato, ensure_ascii=False)
    try:
        raw = provider.complete(sys_prompt, user)
    except Exception as e:
        return None, f"proveedor_indisponible:{type(e).__name__}", False
    try:
        return _extract_json(raw), None, False
    except ValueError:
        pass
    try:
        repaired = provider.complete(
            sys_prompt,
            user + "\n\nTu respuesta anterior no fue JSON valido con el schema "
                   "pedido. Responde OTRA VEZ con SOLO el JSON.")
        return _extract_json(repaired), None, True
    except ValueError:
        return None, None, True
    except Exception as e:
        return None, f"proveedor_indisponible:{type(e).__name__}", True


# ------------------------------------------------------------------ API

def deliberar(candidato: dict, provider: Provider) -> dict:
    """Delibera los 6 sombreros y devuelve el veredicto global. NUNCA lanza:
    fallos de parseo -> veto por defecto en ese sombrero. Salida SIEMPRE
    conforme al schema de deliberacion (dict JSON-serializable)."""
    sombreros_out = {}
    size = 1.0
    n_prov_error = 0
    for nombre in SOMBREROS:
        resp, prov_err, reparado = _llama_sombrero(provider, nombre, candidato)
        if prov_err is not None:
            n_prov_error += 1
            sombreros_out[nombre] = {
                "veredicto": "no", "size_ajuste": None,
                "justificacion": prov_err, "reparado": reparado,
                "prompt_sha256": prompt_sha256(nombre)}
            continue
        if resp is None:
            sombreros_out[nombre] = {
                "veredicto": "no", "size_ajuste": None,
                "justificacion": "veto_por_defecto_parse (respuesta no parseable "
                                 "tras reparacion)",
                "reparado": reparado, "prompt_sha256": prompt_sha256(nombre)}
            continue
        sombreros_out[nombre] = {
            "veredicto": resp["veredicto"], "size_ajuste": resp["size_ajuste"],
            "justificacion": resp["justificacion"], "reparado": reparado,
            "prompt_sha256": prompt_sha256(nombre)}
        if resp["veredicto"] == "no":
            size = 0.0
        elif resp["veredicto"] == "ajustar" and size > 0:
            size = min(size, float(resp["size_ajuste"]))

    veredictos = [s["veredicto"] for s in sombreros_out.values()]
    if n_prov_error == len(SOMBREROS):
        veredicto_global, motivo = "no", "proveedor_indisponible"
    elif "no" in veredictos:
        veredicto_global, motivo = "no", "al_menos_un_sombrero_veto"
    elif "ajustar" in veredictos:
        veredicto_global, motivo = "ajustar", "size_ajustado_por_sombreros"
    else:
        veredicto_global, motivo = "si", "consenso_6_sombreros"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modo": "sombra",
        "candidato": {k: candidato.get(k) for k in
                      ("estrategia", "activo", "direccion")},
        "sombreros": sombreros_out,
        "veredicto": veredicto_global,
        "size_final": round(size, 4),
        "motivo": motivo,
    }


def valida_deliberacion(d) -> bool:
    """Schema de la salida de deliberar() — para tests y journal."""
    try:
        assert set(d.keys()) == {"timestamp", "modo", "candidato", "sombreros",
                                 "veredicto", "size_final", "motivo"}
        assert d["modo"] == "sombra"
        assert d["veredicto"] in VERDICTOS_VALIDOS
        assert isinstance(d["size_final"], (int, float))
        assert set(d["sombreros"].keys()) == set(SOMBREROS.keys())
        json.dumps(d)  # siempre serializable
        return True
    except (AssertionError, TypeError, ValueError):
        return False
