"""Verificacion KimiProvider: mock de urllib, cero llamadas de red reales.

Uso: /opt/trading-bot/venv/bin/python verificar_kimi_provider.py
"""
import io
import json
import os
import sys
import unittest.mock as mock

sys.path.insert(0, "src")


def main():
    ok = True

    for k in ("MAIA_KIMI_KEY", "ANTHROPIC_API_KEY", "DELIBERATION_MODEL_KIMI"):
        os.environ.pop(k, None)

    import deliberation
    import importlib
    importlib.reload(deliberation)

    os.environ.pop("MAIA_KIMI_KEY", None)
    try:
        deliberation.KimiProvider(api_key=None)
        print("  FALLO: KimiProvider sin key no lanzo AssertionError"); ok = False
    except AssertionError:
        print("  OK sin key: AssertionError como se espera")

    captured = {}

    def fake_urlopen(req, timeout=60):
        captured["url"] = req.full_url
        captured["headers"] = {k.lower(): v for k, v in req.headers.items()}
        captured["body"] = json.loads(req.data)
        resp = {"content": [{"type": "text", "text": "hola desde kimi"}]}
        return io.BytesIO(json.dumps(resp).encode())

    class FakeCtx:
        def __init__(self, f): self.f = f
        def __enter__(self): return self.f
        def __exit__(self, *a): return False

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=60: FakeCtx(fake_urlopen(req, timeout))):
        kp = deliberation.KimiProvider(api_key="test-kimi-key-123")
        out = kp.complete("system prompt x", '{"candidato": 1}')

    if out != "hola desde kimi":
        print(f"  FALLO: texto devuelto {out!r}"); ok = False
    elif captured["url"] != "https://api.kimi.com/coding/v1/messages":
        print(f"  FALLO: URL {captured['url']!r}"); ok = False
    elif captured["headers"].get("authorization") != "Bearer test-kimi-key-123":
        print(f"  FALLO: header Authorization {captured['headers'].get('authorization')!r}"); ok = False
    elif "x-api-key" in captured["headers"]:
        print("  FALLO: no debe usar x-api-key (eso es Anthropic, no Kimi)"); ok = False
    elif captured["headers"].get("anthropic-version") != "2023-06-01":
        print("  FALLO: falta/incorrecto header anthropic-version"); ok = False
    elif captured["body"].get("model") != "kimi-for-coding":
        print(f"  FALLO: model por defecto {captured['body'].get('model')!r}"); ok = False
    elif captured["body"].get("system") != "system prompt x":
        print("  FALLO: system prompt no llego igual al body"); ok = False
    else:
        print("  OK request bien formado: URL, headers Bearer+anthropic-version, body tipo Anthropic")

    def fake_urlopen_thinking(req, timeout=60):
        resp = {"content": [{"type": "thinking", "thinking": "razonamiento sin bloque text"}]}
        return io.BytesIO(json.dumps(resp).encode())

    with mock.patch("urllib.request.urlopen",
                    side_effect=lambda req, timeout=60: FakeCtx(fake_urlopen_thinking(req, timeout))):
        kp = deliberation.KimiProvider(api_key="test-kimi-key-123")
        out2 = kp.complete("sp", "um")

    if out2 != "razonamiento sin bloque text":
        print(f"  FALLO fallback thinking: {out2!r}"); ok = False
    else:
        print("  OK fallback a bloque 'thinking' cuando no hay bloque 'text' (gotcha real de produccion)")

    os.environ["MAIA_KIMI_KEY"] = "x"
    os.environ.pop("ANTHROPIC_API_KEY", None)
    if not deliberation.provider_disponible():
        print("  FALLO: provider_disponible() False con solo MAIA_KIMI_KEY"); ok = False
    else:
        print("  OK provider_disponible() True con solo MAIA_KIMI_KEY")
    os.environ.pop("MAIA_KIMI_KEY", None)

    os.environ["MAIA_KIMI_KEY"] = "kimi-x"
    os.environ["ANTHROPIC_API_KEY"] = "anthropic-x"
    import paper_runner
    importlib.reload(paper_runner)
    import pandas as pd
    equity = pd.Series([1.0], index=[pd.Timestamp("2026-01-01")])
    with mock.patch.object(deliberation, "KimiProvider") as MockKimi, \
         mock.patch.object(deliberation, "AnthropicProvider") as MockAnthropic:
        paper_runner.deliberar_sombra([], equity)
        if MockKimi.call_count != 1 or MockAnthropic.call_count != 0:
            print(f"  FALLO: con ambas keys, llamadas Kimi={MockKimi.call_count} "
                  f"Anthropic={MockAnthropic.call_count} (se esperaba Kimi=1, Anthropic=0)")
            ok = False
        else:
            print("  OK paper_runner prefiere KimiProvider cuando MAIA_KIMI_KEY esta presente, "
                  "aunque ANTHROPIC_API_KEY tambien lo este")
    os.environ.pop("MAIA_KIMI_KEY", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)

    if ok:
        print("\nVERIFICACION OK: KimiProvider construido, formado y preferido correctamente; "
              "sin ninguna llamada de red real.")
        return 0
    print("\nVERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
