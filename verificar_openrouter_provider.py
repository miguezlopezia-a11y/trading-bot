"""Verificacion OpenRouterProvider: mock de urllib, cero llamadas de red reales.

Uso: /opt/trading-bot/venv/bin/python verificar_openrouter_provider.py
"""
import io
import json
import os
import sys
import unittest.mock as mock

sys.path.insert(0, "src")


def main():
    ok = True

    for k in ("OPENROUTER_API_KEY", "MAIA_KIMI_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)

    import deliberation
    import importlib
    importlib.reload(deliberation)

    os.environ.pop("OPENROUTER_API_KEY", None)
    try:
        deliberation.OpenRouterProvider(api_key=None)
        print("  FALLO: sin key no lanzo AssertionError"); ok = False
    except AssertionError:
        print("  OK sin key: AssertionError como se espera")

    captured = []

    def fake_urlopen_ok_primero(req, timeout=30):
        captured.append({"url": req.full_url,
                         "headers": {k.lower(): v for k, v in req.headers.items()},
                         "body": json.loads(req.data)})
        resp = {"choices": [{"message": {"content": "hola desde openrouter"}}]}
        return io.BytesIO(json.dumps(resp).encode())

    class FakeCtx:
        def __init__(self, f): self.f = f
        def __enter__(self): return self.f
        def __exit__(self, *a): return False

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=30: FakeCtx(fake_urlopen_ok_primero(req, timeout))):
        p = deliberation.OpenRouterProvider(api_key="test-or-key-123")
        out = p.complete("system prompt x", '{"candidato": 1}')

    if out != "hola desde openrouter":
        print(f"  FALLO: texto devuelto {out!r}"); ok = False
    elif captured[0]["url"] != "https://openrouter.ai/api/v1/chat/completions":
        print(f"  FALLO: URL {captured[0]['url']!r}"); ok = False
    elif captured[0]["headers"].get("authorization") != "Bearer test-or-key-123":
        print(f"  FALLO: header Authorization {captured[0]['headers'].get('authorization')!r}"); ok = False
    elif captured[0]["body"]["messages"][0] != {"role": "system", "content": "system prompt x"}:
        print(f"  FALLO: mensaje system mal formado {captured[0]['body']['messages']}"); ok = False
    elif captured[0]["body"]["model"] != deliberation.OpenRouterProvider.MODELOS_FREE[0]:
        print(f"  FALLO: modelo por defecto {captured[0]['body']['model']!r}"); ok = False
    else:
        print("  OK request bien formado al primer modelo: URL, headers Bearer, body estilo OpenAI (system como mensaje)")

    # Si el primer modelo falla (429), prueba el segundo de la lista.
    calls = []

    def fake_urlopen_fallback(req, timeout=30):
        body = json.loads(req.data)
        calls.append(body["model"])
        if body["model"] == deliberation.OpenRouterProvider.MODELOS_FREE[0]:
            import urllib.error
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)
        resp = {"choices": [{"message": {"content": "segundo modelo respondio"}}]}
        return io.BytesIO(json.dumps(resp).encode())

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=30: FakeCtx(fake_urlopen_fallback(req, timeout))):
        p2 = deliberation.OpenRouterProvider(api_key="test-or-key-123")
        out2 = p2.complete("sp", "um")

    if out2 != "segundo modelo respondio" or len(calls) != 2:
        print(f"  FALLO fallback entre modelos: out={out2!r} calls={calls}"); ok = False
    else:
        print("  OK fallback: 1er modelo 429 -> prueba el 2o de la lista y responde")

    # Si TODOS los modelos fallan, se propaga el error (no basura, no silencio).
    def fake_urlopen_todos_fallan(req, timeout=30):
        import urllib.error
        raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=30: fake_urlopen_todos_fallan(req, timeout)):
        p3 = deliberation.OpenRouterProvider(api_key="test-or-key-123")
        try:
            p3.complete("sp", "um")
            print("  FALLO: deberia haber lanzado si todos los modelos fallan"); ok = False
        except Exception:
            print("  OK: si todos los modelos free fallan, se propaga el error (veto por defecto aguas arriba)")

    # Hallazgo real (smoke 2026-10-07): un modelo free puede devolver
    # content=null (refusal/vacio) sin error HTTP -- debe tratarse como
    # fallo de ese modelo, no crashear ni devolver None.
    def fake_urlopen_content_null(req, timeout=30):
        body = json.loads(req.data)
        if body["model"] == deliberation.OpenRouterProvider.MODELOS_FREE[0]:
            resp = {"choices": [{"message": {"content": None}}]}
        else:
            resp = {"choices": [{"message": {"content": "tercer intento ok"}}]}
        return io.BytesIO(json.dumps(resp).encode())

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=30: FakeCtx(fake_urlopen_content_null(req, timeout))):
        p4 = deliberation.OpenRouterProvider(api_key="test-or-key-123")
        out4 = p4.complete("sp", "um")
    if out4 != "tercer intento ok":
        print(f"  FALLO: content null no se trato como fallo de ese modelo: {out4!r}"); ok = False
    else:
        print("  OK: content null/vacio en un modelo se trata como fallo, prueba el siguiente")

    os.environ["OPENROUTER_API_KEY"] = "x"
    if not deliberation.provider_disponible():
        print("  FALLO: provider_disponible() False con solo OPENROUTER_API_KEY"); ok = False
    else:
        print("  OK provider_disponible() True con solo OPENROUTER_API_KEY")
    os.environ.pop("OPENROUTER_API_KEY", None)

    # Orden de preferencia en paper_runner: OpenRouter > Kimi > Anthropic.
    os.environ["OPENROUTER_API_KEY"] = "or-x"
    os.environ["MAIA_KIMI_KEY"] = "kimi-x"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic-x"
    import paper_runner
    importlib.reload(paper_runner)
    import pandas as pd
    equity = pd.Series([1.0], index=[pd.Timestamp("2026-01-01")])
    with mock.patch.object(deliberation, "OpenRouterProvider") as MockOR, \
         mock.patch.object(deliberation, "KimiProvider") as MockKimi, \
         mock.patch.object(deliberation, "AnthropicProvider") as MockAnthropic:
        paper_runner.deliberar_sombra([], equity)
        if MockOR.call_count != 1 or MockKimi.call_count != 0 or MockAnthropic.call_count != 0:
            print(f"  FALLO: con las 3 keys, llamadas OR={MockOR.call_count} "
                  f"Kimi={MockKimi.call_count} Anthropic={MockAnthropic.call_count} "
                  f"(se esperaba OR=1, Kimi=0, Anthropic=0)")
            ok = False
        else:
            print("  OK paper_runner prefiere OpenRouterProvider sobre Kimi y Anthropic "
                  "cuando las 3 keys estan presentes")
    os.environ.pop("OPENROUTER_API_KEY", None)
    os.environ.pop("MAIA_KIMI_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)

    if ok:
        print("\nVERIFICACION OK: OpenRouterProvider construido, con fallback entre "
              "modelos free, y preferido correctamente; sin ninguna llamada de red real.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
