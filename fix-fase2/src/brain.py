"""Segundo cerebro: store append-only JSONL con semilla + recuperación por tags.
Cada registro: {ts, type, market, regime, tags, content, source}
types: lesson | backtest_result | deliberation | trade | audit_finding
"""
import hashlib
import json
import time
from pathlib import Path

BRAIN_DIR = Path(__file__).parent.parent / "data" / "brain"


def _hash(type_: str, market: str, content: str) -> str:
    return hashlib.sha256(f"{type_}|{market}|{content}".encode()).hexdigest()[:16]


class Brain:
    def __init__(self, path: Path | None = None):
        BRAIN_DIR.mkdir(parents=True, exist_ok=True)
        self.path = path or BRAIN_DIR / "knowledge.jsonl"
        if not self.path.exists():
            self.path.touch()
        self._hashes = set()
        for line in open(self.path):
            line = line.strip()
            if line:
                r = json.loads(line)
                self._hashes.add(_hash(r["type"], r["market"], r["content"]))

    def add(self, type_: str, content: str, market: str = "", regime: str = "",
            tags: list | None = None, source: str = "") -> dict | None:
        """Añade registro. Devuelve None si es duplicado exacto (type+market+content ya existe)."""
        h = _hash(type_, market, content)
        if h in self._hashes:
            return None
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "type": type_, "market": market, "regime": regime,
               "tags": tags or [], "content": content, "source": source}
        with open(self.path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._hashes.add(h)
        return rec

    def query(self, market: str = "", regime: str = "", type_: str = "",
              tag: str = "", limit: int = 20) -> list[dict]:
        out = []
        for line in open(self.path):
            r = json.loads(line)
            if market and r["market"] not in ("", market):
                continue
            if regime and r["regime"] not in ("", regime):
                continue
            if type_ and r["type"] != type_:
                continue
            if tag and tag not in r["tags"]:
                continue
            out.append(r)
        return out[-limit:]

    def seed(self):
        """Semilla previa: lecciones del PDF + resultados línea base. Idempotente por tag 'seeded'."""
        if self.query(tag="seeded"):
            return False
        lessons = [
            ("Nunca operar sin Stop Loss. Una operación sin SL puede liquidar la cuenta entera.", ["risk", "stop_loss"]),
            ("Overfitting: si la estrategia solo funciona en el periodo ajustado, es ruido. Validar siempre en datos no vistos.", ["overfitting", "validation"]),
            ("Una estrategia NO funciona en cualquier activo. Los parámetros son específicos por mercado.", ["overfitting", "market_specific"]),
            ("Saber cuándo SALIR es más importante que cuándo entrar. Trailing stop con MA 20 como salida de referencia.", ["exits", "trailing"]),
            ("Soltar rápido lo que no funciona. Aferrarse a una estrategia perdedora cuesta más que admitir el error.", ["psychology", "sunk_cost"]),
            ("El backtesting es el detector de mentiras: si un gurú no muestra backtest auditado, su estrategia no funciona.", ["backtest", "scam_filter"]),
            ("Las 4 familias: reversión a la media, cruce de medias, breakout, seguimiento de tendencia. El régimen decide cuál.", ["strategy", "regime"]),
        ]
        for content, tags in lessons:
            self.add("lesson", content, tags=tags + ["seeded"], source="guia-trader-algoritmico.pdf")
        self.add("backtest_result",
                 "Línea base pre-auditoría BTC-USD daily: ma_cross OOS +24.4% Sharpe 1.63 (12/16 WF folds); "
                 "mean_reversion y breakout pierden; trend_following colapsa en OOS (+61% IS → -20% OOS, caso de overfitting). "
                 "NO FIABLE hasta resolver S1 (look-ahead) y S3 (comisión).",
                 market="BTC-USD", regime="trending", tags=["seeded", "baseline", "pre_audit"],
                 source="results/backtest_summary.json")
        return True
