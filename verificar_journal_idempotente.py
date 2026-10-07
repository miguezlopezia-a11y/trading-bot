"""Verificacion 1.2 — journal idempotente contra el backend REAL (Supabase).

Dos fases:
  1. La misma fila se inserta dos veces -> existe UNA sola vez en Supabase
     (dedupe por dedupe_key, re-ingesta sin duplicados).
  2. La fila de probe se borra al terminar (limpieza).

Si public.journal NO existe todavia en el proyecto (esquema no aplicado), el
test lo detecta y sale con SKIP explicito (exit 2): NO cuenta como PASS ni
como fallo — es un bloqueo real que requiere aplicar
docs/supabase_esquema.sql. Contra SQLite (fallback del runner) la idempotencia
ya quedo cubierta por el UNIQUE(evento, fecha_dato, detalle) en Etapa A.

Uso: /opt/trading-bot/venv/bin/python verificar_journal_idempotente.py
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

ENV_FILE = "/root/trading-bot-env"


def creds():
    env = {}
    for line in open(ENV_FILE):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env[k] = v
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_ANON_KEY"]


def req(url, key, path, method="GET", body=None):
    r = urllib.request.Request(url + path, data=body,
                               headers={"apikey": key, "Authorization": f"Bearer {key}",
                                        "Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(r, timeout=20) as resp:
        return resp.status, resp.read()


def main():
    url, key = creds()
    try:
        req(url, key, "/rest/v1/journal?select=id&limit=1")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("SKIP (exit 2): public.journal no existe en Supabase. "
                  "Aplica docs/supabase_esquema.sql en el dashboard y re-ejecuta.")
            return 2
        raise

    stamp = time.strftime("%Y%m%d%H%M%S")
    detalle = json.dumps({"probe": "verificar_journal_idempotente", "ts": stamp})
    dedupe = hashlib.sha256(f"probe|2026-10-07|{detalle}".encode()).hexdigest()
    row = {"ts": "2026-10-07T00:00:00Z", "estrategia": "ma_cross", "evento": "probe",
           "senal": "long", "decision": "no_vetada", "motivo": "test_idempotencia",
           "detalle": detalle, "fecha_dato": "2026-10-07",
           "fuente": "verificacion", "dedupe_key": dedupe}

    # doble insercion (misma dedupe_key)
    for _ in range(2):
        req(url, key, "/rest/v1/journal", "POST", json.dumps(row).encode())

    _, out = req(url, key, f"/rest/v1/journal?dedupe_key=eq.{dedupe}&select=id")
    n = len(json.loads(out))
    print(f"inserciones=2 | filas con dedupe_key={dedupe[:12]}: {n}")
    ok = n == 1
    # limpieza del probe
    req(url, key, f"/rest/v1/journal?dedupe_key=eq.{dedupe}", "DELETE")
    _, out2 = req(url, key, f"/rest/v1/journal?dedupe_key=eq.{dedupe}&select=id")
    n2 = len(json.loads(out2))
    print(f"limpieza probe: filas restantes {n2}")
    ok = ok and n2 == 0

    if ok:
        print("VERIFICACION OK: journal idempotente contra Supabase real "
              "(re-ingesta sin duplicados, dedupe por dedupe_key).")
        return 0
    print("VERIFICACION FALLO.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
