"""1.3 — Paper runner: simulacion pura de ma_cross con mark-to-market diario.

- NINGUNA orden real, NINGUN cliente de exchange, NINGUNA credencial de
  exchange: la simulacion es run_backtest() del backtester (fills reales,
  invariantes H1/S1/H2 ya auditadas). Este modulo solo orquesta.
- Modo: segun dictamen de walk-forward (results/walkforward_stability.json).
  Dictamen real 2026-10-06: FRAGIL -> todas las decisiones se registran como
  "observacion" (nunca "aprobada"). Nada se ejecuta de todas formas.
- Journal: Supabase (bunker-staging) si hay credenciales en
  /root/trading-bot-env (SUPABASE_URL + SUPABASE_ANON_KEY, chmod 600, fuera
  del repo); si no hay tabla accesible o falla la conexion, fallback SQLite
  local data/paper_journal.db (decision documentada por bloqueo, no por gusto).
- Datos: mismo origen que el backtest (yfinance BTC-USD 5y 1d auto_adjust);
  cada descarga se guarda como CSV con sha256 en data/ (reproducibilidad A7).
- Ejecucion: UNA pasada sobre los datos disponibles hasta hoy (no daemon).
  Propuesta de activacion diaria (cron/systemd) documentada en
  docs/paper_runner_operacion.md — NO ACTIVADA.

Uso: /opt/trading-bot/venv/bin/python src/paper_runner.py
"""
import hashlib
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, "src")
from strategies import STRATEGIES  # noqa: E402
from backtester import run_backtest  # noqa: E402

try:  # Etapa B: deliberacion en modo sombra (opcional, nunca bloquea)
    import deliberation
    from risk_veto import evaluar_veto
except ImportError:  # modulo ausente -> runner funciona igual, sin deliberar
    deliberation = None
    evaluar_veto = None

TICKER = "BTC-USD"
INTERVAL = "1d"
YEARS = 5
WARMUP = 200
ACTIVA = "ma_cross"
ENV_FILE = "/root/trading-bot-env"
DATA_DIR = "data"
DOCS_DIR = "docs"
MOTIVO_OBSERVACION = "walkforward_dictamen_fragil_2026-10-06"


# ---------------------------------------------------------------- datos

def load_data() -> pd.DataFrame:
    """Descarga con yfinance (mismo origen que run_backtest) y guarda snapshot
    CSV + sha256 + meta para reproducibilidad (mismo protocolo que A7)."""
    import yfinance as yf
    df = yf.download(TICKER, period=f"{YEARS}y", interval=INTERVAL,
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()

    os.makedirs(DATA_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = os.path.join(DATA_DIR, f"paper_{TICKER.lower().replace('-', '_')}_{stamp}.csv")
    df.to_csv(csv_path, index_label="date")
    digest = hashlib.sha256(open(csv_path, "rb").read()).hexdigest()
    with open(csv_path + ".sha256", "w") as f:
        f.write(f"{digest}  {os.path.basename(csv_path)}\n")
    with open(csv_path + ".meta.json", "w") as f:
        json.dump({"fecha_descarga": datetime.now(timezone.utc).isoformat(),
                   "ticker": TICKER, "period": f"{YEARS}y", "interval": INTERVAL,
                   "auto_adjust": True, "sha256": digest, "n_velas": len(df),
                   "primera_fecha": str(df.index[0].date()),
                   "ultima_fecha": str(df.index[-1].date())}, f, indent=2)
    return df


# ---------------------------------------------------------------- simulacion

def simulate(df: pd.DataFrame, strategy_name: str = ACTIVA) -> dict:
    """Simula la estrategia activa sobre df con el backtester real (fills,
    SL/TP/gap, MTM diario H1). Devuelve equity, trades y decisiones de journal.
    """
    fn = STRATEGIES[strategy_name]
    full_signals = fn(df)
    res = run_backtest(df, full_signals)
    decisions = []
    for t in res["trades"]:
        decisions.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "estrategia": strategy_name,
            "evento": "trade",
            "senal": t.side,
            "decision": "observacion",
            "motivo": MOTIVO_OBSERVACION,
            "detalle": json.dumps({"entry_date": str(t.entry_date.date()),
                                   "entry_price": t.entry_price,
                                   "exit_date": str(t.exit_date.date()),
                                   "exit_price": t.exit_price,
                                   "reason": t.reason,
                                   "pnl": round(t.pnl, 6)}),
            "equity_mtm": None,
            "fecha_dato": str(t.exit_date.date()),
        })
    return {"equity": res["equity"], "trades": res["trades"],
            "decisions": decisions, "signals": full_signals}


# ---------------------------------------------------------------- journal

class Journal:
    """Journal de decisiones. Supabase (REST, anon key) si es accesible;
    SQLite local como fallback. Misma interfaz en ambos."""

    def __init__(self):
        self.backend = None
        url = key = None
        if os.path.exists(ENV_FILE):
            for line in open(ENV_FILE):
                if line.startswith("SUPABASE_URL="):
                    url = line.strip().split("=", 1)[1]
                elif line.startswith("SUPABASE_ANON_KEY="):
                    key = line.strip().split("=", 1)[1]
        if url and key:
            try:
                self._sb_insert(url, key, {"evento": "journal_init_probe",
                                           "estrategia": "probe",
                                           "decision": "probe_ok"})
                self.backend = ("supabase", url, key)
                return
            except Exception:
                pass  # fallback sqlite, se reporta en el dashboard
        os.makedirs(DATA_DIR, exist_ok=True)
        self.db = sqlite3.connect(os.path.join(DATA_DIR, "paper_journal.db"))
        self.db.execute("""CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, estrategia TEXT, evento TEXT, senal TEXT,
            decision TEXT, motivo TEXT, detalle TEXT,
            equity_mtm REAL, fecha_dato TEXT,
            UNIQUE(evento, fecha_dato, detalle))""")
        self.db.commit()
        self.backend = ("sqlite",)

    def _sb_insert(self, url, key, row):
        import hashlib
        detalle = row.get("detalle") or ""
        dedupe = hashlib.sha256(
            f'{row.get("evento")}|{row.get("fecha_dato")}|{detalle}'.encode()
        ).hexdigest()
        body = {k: v for k, v in {
            "ts": row.get("timestamp"), "estrategia": row.get("estrategia"),
            "evento": row.get("evento"), "senal": row.get("senal"),
            "decision": row.get("decision"), "motivo": row.get("motivo"),
            "detalle": detalle, "equity_mtm": row.get("equity_mtm"),
            "fecha_dato": row.get("fecha_dato"),
            "fuente": row.get("fuente", "paper_runner_v1"),
            "dedupe_key": dedupe}.items() if v is not None}
        req = urllib.request.Request(
            url.rstrip("/") + "/rest/v1/journal?on_conflict=dedupe_key",
            data=json.dumps(body).encode(),
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "resolution=ignore-duplicates"},
            method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()

    def insert(self, row):
        if self.backend[0] == "supabase":
            try:
                self._sb_insert(self.backend[1], self.backend[2], row)
                return
            except Exception:
                pass
        import hashlib
        detalle = row.get("detalle") or ""
        dedupe = hashlib.sha256(
            f'{row.get("evento")}|{row.get("fecha_dato")}|{detalle}'.encode()
        ).hexdigest()
        self.db.execute(
            "INSERT OR IGNORE INTO journal (ts,estrategia,evento,senal,decision,"
            "motivo,detalle,equity_mtm,fecha_dato) VALUES (?,?,?,?,?,?,?,?,?)",
            (row["timestamp"], row["estrategia"], row["evento"], row["senal"],
             row["decision"], row["motivo"], row["detalle"], row["equity_mtm"],
             row["fecha_dato"]))
        self.db.commit()

    def close(self):
        if self.backend[0] == "sqlite":
            self.db.close()


# ---------------------------------------------------------------- dashboard

def render_dashboard(sim, df, strategy_name, journal_backend, out_path):
    eq = sim["equity"]
    bh = df["close"] / df["close"].iloc[0]
    last = eq.iloc[-1]
    rows = []
    for t in reversed(sim["trades"][-15:]):
        rows.append(f"<tr><td>{t.entry_date.date()}</td><td>{t.side}</td>"
                    f"<td>{t.entry_price:.2f}</td><td>{t.exit_date.date() if t.exit_date else '-'}</td>"
                    f"<td>{t.exit_price if t.exit_price else '-'}".replace("None", "-") + "</td>"
                    f"<td>{t.reason}</td><td>{t.pnl:+.6f}</td></tr>")
    # estado actual
    pos = "flat"
    if sim["trades"] and sim["trades"][-1].exit_date is None:
        pos = f"abierta ({sim['trades'][-1].side} desde {sim['trades'][-1].entry_date.date()})"
    # serie para el grafico: muestreo de ~200 puntos
    step = max(1, len(eq) // 200)
    xs = list(range(0, len(eq), step))
    eqs = (eq / eq.iloc[0]).iloc[::step].tolist()
    bhs = bh.iloc[::step].tolist()
    poly = " ".join(f"{i * 4},{100 - v * 40:.2f}" for i, v in enumerate(eqs))
    poly_bh = " ".join(f"{i * 4},{100 - v * 40:.2f}" for i, v in enumerate(bhs))
    w = max(len(xs) * 4, 100)
    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Paper dashboard — {strategy_name}</title></head><body>
<h1>Paper trading (simulacion, SIN dinero real)</h1>
<p><b>Estrategia:</b> {strategy_name} · <b>Modo:</b> OBSERVACION (walk-forward dictamen: FRAGIL) ·
<b>Journal:</b> {journal_backend}</p>
<h2>Estado actual</h2>
<ul><li>Ultima fecha de datos: {df.index[-1].date()}</li>
<li>Posicion: {pos}</li>
<li>Equity simulada: {last:.6f} (retorno {(last / eq.iloc[0] - 1) * 100:.2f}%)</li>
<li>Buy&amp;hold mismo periodo: {bh.iloc[-1]:.4f} ({(bh.iloc[-1] - 1) * 100:.2f}%)</li>
<li>Trades: {len(sim['trades'])}</li></ul>
<h2>Equity simulada vs buy&amp;hold</h2>
<svg width="{w}" height="200" style="border:1px solid #999;background:#fafafa">
<polyline points="{poly}" fill="none" stroke="#06c" stroke-width="1.5"/>
<polyline points="{poly_bh}" fill="none" stroke="#c60" stroke-width="1" stroke-dasharray="4 3"/>
</svg>
<p><span style="color:#06c">— equity paper</span> · <span style="color:#c60">-- buy&amp;hold</span></p>
<h2>Ultimos trades (decision registrada: observacion)</h2>
<table border="1" cellpadding="4"><tr><th>Entrada</th><th>Lado</th><th>Precio ent.</th>
<th>Salida</th><th>Precio sal.</th><th>Motivo</th><th>PnL</th></tr>{''.join(rows)}</table>
<p>Generado {datetime.now(timezone.utc).isoformat()} — paper_runner.py, simulacion pura.</p>
</body></html>"""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page)


# ---------------------------------------------------------------- main

def deliberar_sombra(trades, equity):
    """Etapa B: deliberacion 6 Sombreros MODO SOMBRA + veto de riesgo.
    NUNCA modifica trades ni decisiones: solo produce registros para el
    journal. Sin proveedor LLM -> deliberacion "no_disponible" (runner igual)."""
    registros = []
    now = datetime.now(timezone.utc).isoformat()
    provider = None
    if deliberation is not None and deliberation.provider_disponible():
        try:
            # Orden: Kimi primero (cubre el proyecto sin saldo Anthropic desde
            # agosto 2026), Anthropic como fallback si algun dia hay saldo.
            if os.environ.get("MAIA_KIMI_KEY"):
                provider = deliberation.KimiProvider()
            elif os.environ.get("ANTHROPIC_API_KEY"):
                provider = deliberation.AnthropicProvider()
        except Exception as e:
            print(f"proveedor LLM no inicializable: {e}")
    for t in trades:
        eq_entry = float(equity.loc[:t.entry_date].iloc[-1])
        sizing = (t.entry_price * t.size) / eq_entry if eq_entry else 0.0
        direction = 1 if t.side == "long" else -1
        dd_proj = (t.stop - t.entry_price) / t.entry_price * 100 * direction \
            if t.stop else None
        fecha = str(t.exit_date.date()) if t.exit_date is not None \
            else str(t.entry_date.date())
        candidato = {"estrategia": ACTIVA, "activo": TICKER, "direccion": t.side,
                     "sizing": round(sizing, 6), "dd_proyectado_pct": dd_proj,
                     "contexto": {"entry_price": t.entry_price, "stop": t.stop,
                                  "target": t.target, "equity_entry": round(eq_entry, 6),
                                  "motivo_salida": t.reason,
                                  "dictamen": "walkforward_fragil_modo_observacion"}}
        base = {"timestamp": now, "estrategia": ACTIVA,
                "senal": t.side, "fecha_dato": fecha}
        if evaluar_veto is not None:
            veto = evaluar_veto(candidato)
            registros.append({**base, "evento": "risk_veto",
                              "decision": "vetada" if veto["vetado"] else "no_vetada",
                              "motivo": ",".join(veto["motivos"]) or "dentro_de_limites",
                              "detalle": json.dumps(veto, ensure_ascii=False),
                              "equity_mtm": None})
        if provider is not None:
            try:
                d = deliberation.deliberar(candidato, provider)
                assert deliberation.valida_deliberacion(d)
                registros.append({**base, "evento": "deliberacion",
                                  "decision": d["veredicto"],
                                  "motivo": d["motivo"],
                                  "detalle": json.dumps(d, ensure_ascii=False),
                                  "equity_mtm": None})
            except Exception as e:
                registros.append({**base, "evento": "deliberacion",
                                  "decision": "no_disponible",
                                  "motivo": f"error_provider:{type(e).__name__}",
                                  "detalle": "{}", "equity_mtm": None})
        else:
            registros.append({**base, "evento": "deliberacion",
                              "decision": "no_disponible",
                              "motivo": "sin_proveedor_llm",
                              "detalle": "{}", "equity_mtm": None})
    return registros


def main():
    df = load_data()
    sim = simulate(df, ACTIVA)
    eq = sim["equity"]
    print(f"Datos: {len(df)} velas ({df.index[0].date()} -> {df.index[-1].date()})")
    print(f"Simulacion {ACTIVA}: {len(sim['trades'])} trades, "
          f"equity final {eq.iloc[-1]:.6f} (retorno {(eq.iloc[-1] / eq.iloc[0] - 1) * 100:.2f}%)")
    print(f"Buy&hold: {(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.2f}%")

    shadow = deliberar_sombra(sim["trades"], eq)
    n_delib = sum(1 for r in shadow if r["evento"] == "deliberacion")
    n_veto = sum(1 for r in shadow if r["evento"] == "risk_veto")
    print(f"Modo sombra: {n_delib} deliberaciones, {n_veto} vetos de riesgo "
          f"(registrados, NUNCA bloquean)")

    journal = Journal()
    for d in sim["decisions"] + shadow:
        journal.insert(d)
    backend = journal.backend[0]
    print(f"Journal backend: {backend}")
    journal.close()

    out = os.path.join(DOCS_DIR, "paper_dashboard.html")
    render_dashboard(sim, df, ACTIVA, backend, out)
    print(f"-> {out} generado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
