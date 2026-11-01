"""Paso 3.7 — los 4 verificadores que descargaban en vivo, ahora sin red.
   (objecion B-12)

Hallazgo A-05: 4 de los 23 verificar_*.py descargan de yfinance en tiempo de
ejecucion en vez de usar los CSV congelados. Un verificador cuyo insumo cambia
cada dia no congela nada: puede pasar hoy y fallar mañana sin que el codigo
cambie. Y ninguno de los cuatro comprueba que la descarga trajo filas: fallan
con IndexError sobre un DataFrame vacio en lugar de con un error claro.

Los cuatro:
  verificar_a5_indicadores.py      yf.download("BTC-USD", period="2y")
  verificar_a8_adversarial.py      yf.download("BTC-USD", period="5y")
  verificar_invariante_h1.py       run_backtest.load_data() -> yf.download 5y
  verificar_opus_fase2.py          run_backtest.load_data() -> yf.download 5y

NOTA DE ALCANCE: el OK de Pablo autoriza este paso pero su lista de escrituras
permitidas no incluye esos cuatro ficheros ni run_backtest.py. Asi que aqui NO
se editan. Este script redirige el origen de datos EN MEMORIA (sustituye
yfinance.download por un servidor del CSV congelado) y ejecuta los cuatro.
Eso demuestra dos cosas: que su LOGICA pasa, y que la suite es ejecutable sin
red en cuanto se haga permanente el cambio. Hacerlo permanente requiere editar
esos ficheros, que queda propuesto en el informe, no hecho.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_7_verificadores_sin_red.py
"""
import io
import os
import runpy
import sys
import traceback

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
CSV = os.path.join(FIX2, "data", "btc_usd_5y_1d.csv")
OBJETIVO = ["verificar_a5_indicadores.py", "verificar_a8_adversarial.py",
            "verificar_invariante_h1.py", "verificar_opus_fase2.py"]

_BASE = pd.read_csv(CSV, index_col=0, parse_dates=True)
_BASE = _BASE.rename(columns=str.lower)[["open", "high", "low", "close",
                                         "volume"]].dropna()


def descarga_congelada(ticker, period=None, interval=None, **kw):
    """Sustituto de yfinance.download: sirve el CSV congelado y NUNCA toca la
    red. Recorta por `period` y falla en duro si el recorte sale vacio — que
    es lo que los cuatro verificadores no comprueban."""
    if str(ticker).upper() not in ("BTC-USD", "['BTC-USD']"):
        raise RuntimeError(
            f"descarga prohibida: solo hay CSV congelado de BTC-USD, se pidio "
            f"{ticker!r}")
    df = _BASE.copy()
    if period and str(period).endswith("y"):
        años = int(str(period)[:-1])
        corte = df.index[-1] - pd.DateOffset(years=años)
        df = df[df.index > corte]
    if len(df) == 0:
        raise RuntimeError(
            f"el recorte period={period!r} deja 0 filas sobre el CSV "
            f"congelado ({_BASE.index[0].date()} -> {_BASE.index[-1].date()})")
    return df


print("=" * 74)
print("PASO 3.7 — los 4 verificadores de red, ejecutados sin red")
print("=" * 74)
print(f"origen congelado: data/btc_usd_5y_1d.csv")
print(f"  {len(_BASE)} velas, {_BASE.index[0].date()} -> {_BASE.index[-1].date()}")
print("yfinance.download sustituido en memoria. Los ficheros NO se modifican.")
print()

os.chdir(FIX2)
sys.path.insert(0, os.path.join(FIX2, "src"))
import yfinance as yf  # noqa: E402
yf.download = descarga_congelada
# run_backtest importa yf en su propio namespace: hay que parchearlo tambien
import run_backtest as rb  # noqa: E402
rb.yf = type("_shim", (), {"download": staticmethod(descarga_congelada)})

print(f"  control: load_data() de run_backtest devuelve "
      f"{len(rb.load_data())} velas sin tocar la red")
print()

resultados = {}
for fichero in OBJETIVO:
    ruta = os.path.join(FIX2, fichero)
    print("-" * 74)
    print(f"{fichero}")
    print("-" * 74)
    buf_out, buf_err = io.StringIO(), io.StringIO()
    so, se = sys.stdout, sys.stderr
    rc, exc = 0, None
    try:
        sys.stdout, sys.stderr = buf_out, buf_err
        runpy.run_path(ruta, run_name="__main__")
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException:
        rc, exc = 1, traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = so, se
    salida = buf_out.getvalue().strip()
    for linea in salida.splitlines()[-18:]:
        print("    " + linea)
    if exc:
        for linea in exc.strip().splitlines()[-8:]:
            print("    " + linea)
    estado = "PASS" if rc == 0 and not exc else "FAIL"
    resultados[fichero] = estado
    print(f"    >>> {estado} (rc={rc})")
    print()

print("=" * 74)
print("RESUMEN 3.7")
for f, e in resultados.items():
    print(f"  [{e}] {f}")
n_pass = sum(1 for e in resultados.values() if e == "PASS")
print()
print(f"  {n_pass}/{len(OBJETIVO)} pasan con el CSV congelado y sin red.")
print()
print("  Consecuencia para el hallazgo A-05: los 7 fallos de la suite que se")
print("  registraron en la Fase 0 eran de ENTORNO, no de logica. Con el origen")
print("  de datos congelado, estos 4 se recuperan. Los 3 restantes necesitan")
print("  torch/timesfm (verificar_timesfm_t1/t2) o un fichero de credenciales")
print("  en /root (verificar_journal_idempotente), y quedan fuera de alcance.")
print()
print("  Para hacerlo PERMANENTE hay que editar los 4 ficheros (y load_data de")
print("  run_backtest.py) para que lean el CSV congelado y asserten que trajo")
print("  filas. Esos ficheros no estan en el alcance de escrituras que")
print("  autoriza el §8, asi que queda PROPUESTO en el informe, no hecho.")
sys.exit(0 if n_pass == len(OBJETIVO) else 1)
