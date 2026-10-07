"""Migracion del journal SQLite -> Supabase, SIN PERDIDA, con dedupe.

Lee todos los registros de data/paper_journal.db y los inserta en
public.journal (dedupe por dedupe_key = sha256(evento|fecha_dato|detalle),
mismo criterio que el runner). Verifica al final que el numero de claves
dedupe distintas migradas == numero de filas origen (idempotente: re-ejecutar
no duplica gracias al UNIQUE + ignore-duplicates).

Requisito: el esquema docs/supabase_esquema.sql debe estar aplicado en el
proyecto (verificar_journal_idempotente.py lo comprueba primero).

Uso: /opt/trading-bot/venv/bin/python migrar_journal_supabase.py
"""
import hashlib
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request

ENV_FILE = "/root/trading-bot-env"
DB = "data/paper_journal.db"


def creds():
    env = {}
    for line in open(ENV_FILE):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env[k] = v
    return env["SUPABASE_URL"].rstrip("/"), env["SUPABASE_ANON_KEY"]


def sb_insert(url, key, row):
    body = {k: v for k, v in row.items() if v is not None}
    req = urllib.request.Request(
        url + "/rest/v1/journal", data=json.dumps(body).encode(),
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "Prefer": "resolution=ignore-duplicates"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def sb_count(url, key):
    req = urllib.request.Request(
        url + "/rest/v1/journal?select=dedupe_key",
        headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return len(json.loads(r.read()))


def main():
    url, key = creds()
    # precheck: la tabla existe?
    req = urllib.request.Request(url + "/rest/v1/journal?select=id&limit=1",
                                 headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
    except urllib.error.HTTPError as e:
        print(f"BLOQUEO: public.journal no existe en Supabase ({e.code}).")
        print("Aplica docs/supabase_esquema.sql en el SQL Editor del dashboard.")
        return 1

    db = sqlite3.connect(DB)
    rows = db.execute("SELECT ts,estrategia,evento,senal,decision,motivo,"
                      "detalle,equity_mtm,fecha_dato FROM journal").fetchall()
    orig_keys = set()
    migrados = 0
    for ts, estrategia, evento, senal, decision, motivo, detalle, equity, fecha in rows:
        detalle = detalle or ""
        dedupe = hashlib.sha256(f"{evento}|{fecha}|{detalle}".encode()).hexdigest()
        orig_keys.add(dedupe)
        try:
            sb_insert(url, key, {
                "ts": ts, "estrategia": estrategia, "evento": evento,
                "senal": senal, "decision": decision, "motivo": motivo,
                "detalle": detalle if detalle else None, "equity_mtm": equity,
                "fecha_dato": fecha, "fuente": "paper_runner_v1",
                "dedupe_key": dedupe})
            migrados += 1
        except Exception as e:
            print(f"  error migrando {dedupe[:12]}: {type(e).__name__}: {e}")
    db.close()

    total = sb_count(url, key)
    print(f"filas origen (SQLite): {len(rows)} | claves dedupe distintas: {len(orig_keys)}")
    print(f"intentos de insert: {migrados} | filas destino (Supabase): {total}")
    if total == len(orig_keys):
        print("MIGRACION OK: conteo destino == claves origen (sin duplicados, sin perdida).")
        return 0
    print(f"DISCREPANCIA: destino {total} != origen {len(orig_keys)}. NO declarar migrado.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
