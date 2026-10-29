"""Verificacion: la equity del paper runner marca a mercado con el close de
CADA vela (invariante H1 heredada del backtester), incluso sin trades cerrados
en ese tramo.

Caso sintetico: una senal long en la vela 0 con stop/target inalcanzables y
sin trailing. Entre la entrada (open[1]) y el final, la equity de cada vela
debe ser cash + qty*(close[i] - fill) — es decir, se mueve con el close diario
aunque no haya ningun trade cerrado en esas velas.

Uso: /opt/trading-bot/venv/bin/python verificar_mark_to_market_paper.py
     (desde la raiz del repo/copia)
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
import paper_runner  # noqa: E402


def main():
    n = 12
    # Tendencia suave con velas que nunca tocan stop=1 ni target=1e9.
    close = 100 + np.linspace(0, 3, n) + np.array([0, 1, -1, 0.5, 0, 1, -0.5, 0, 0.5, 0, -0.5, 0.5])
    df = pd.DataFrame({
        "open": close - 0.2, "high": close + 1.0, "low": close - 1.0,
        "close": close, "volume": 1.0,
    }, index=pd.date_range("2026-01-01", periods=n, freq="D"))

    def fake_signals(d):
        return pd.DataFrame({
            "entry_long": [True] + [False] * (len(d) - 1),
            "entry_short": [False] * len(d),
            "stop_loss": [1.0] * len(d),
            "take_profit": [1e9] * len(d),
            "trailing_ma_period": [None] * len(d),
        }, index=d.index)

    paper_runner.STRATEGIES["fake_mtm"] = fake_signals
    sim = paper_runner.simulate(df, "fake_mtm")
    eq = sim["equity"]

    assert len(eq) == n, f"equity tiene {len(eq)} puntos, se esperaban {n}"
    t = sim["trades"][0]
    assert t.reason == "end_of_data", f"la posicion no quedo abierta: {t.reason}"
    qty = t.size
    fill = t.entry_price
    cash_before = 1.0
    # equity[i] con posicion abierta = cash_realizado(1.0) + qty*(close[i]-fill).
    # La ultima vela no aplica: el backtester cierra por end_of_data y equity[-1]
    # pasa a ser cash realizado (incluye costes), no MTM naive — eso es correcto.
    max_err = 0.0
    for i in range(1, n - 1):
        expected = cash_before + qty * (df["close"].iloc[i] - fill)
        max_err = max(max_err, abs(eq.iloc[i] - expected))
    assert max_err < 1e-9, f"equity no marca a mercado: err max {max_err}"
    expected_last = cash_before + t.pnl
    assert abs(eq.iloc[-1] - expected_last) < 1e-9, \
        f"equity final != cash realizado tras cierre: {eq.iloc[-1]} vs {expected_last}"
    # ademas: la equity varia entre velas aunque no haya trade cerrado
    assert eq.iloc[1:].nunique() > 1, "equity plana entre entrada y cierre: sin MTM"
    print(f"  OK equity[{n} velas] = cash + qty*(close-fill) en cada vela "
          f"(err max {max_err:.2e}); posicion abierta hasta end_of_data, "
          f"sin trades intermedios -> MTM diario heredado de H1.")
    print("\nVERIFICACION OK: mark-to-market diario en paper runner.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
