"""Paso 3.0c — el mismo vinculo codigo<->resultados, para FASE B.

3.0b establecio el vinculo solo para Fase A (rigor_estadistico.json). Fase B
es el dictamen que sobrevive ("SEÑAL DEBIL"), asi que su vinculo importa mas.
Reejecutable solo desde el parche del paso 3.0 (antes, el loader no alcanzaba
los CSV congelados).

Reejecuta simulate() del portfolio con los dos sellos congelados disponibles
(20261007 y 20261009) y compara las metricas contra
results/portfolio_runner.json. No escribe nada en fix-fase2/results/.

Uso:  python3 fix-fase2/auditoria_n1/paso_3_0c_reproducibilidad_fase_b.py
"""
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
FIX2 = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(FIX2, "src"))
os.chdir(FIX2)                      # data/multi y results/ son relativos

from portfolio_runner import (load_or_download, simulate, metrics,  # noqa: E402
                              DatoCongeladoAusente)

PUBLICADO = os.path.join(FIX2, "results", "portfolio_runner.json")
SELLOS = ["20261007", "20261009"]
TOL = 1e-9


def main():
    print("=" * 74)
    print("PASO 3.0c — reproducibilidad de Fase B (portfolio 10 activos)")
    print("=" * 74)
    with open(PUBLICADO) as f:
        pub = json.load(f)
    m_pub = pub["metricas"]
    print("publicado (results/portfolio_runner.json):")
    for k, v in m_pub.items():
        print(f"    {k:<22} {v}")
    print(f"    {'n_vetos_wmax':<22} {pub['n_vetos_wmax']}")
    print(f"    {'n_vetos_vol':<22} {pub['n_vetos_vol']}")
    print(f"    {'exposicion_media':<22} {pub['exposicion_media']}")
    print()

    resultados = {}
    for sello in SELLOS:
        print("-" * 74)
        print(f"reejecucion con sello {sello}")
        try:
            t0 = time.time()
            datos = load_or_download(stamp=sello)
            res = simulate(datos)
            m = metrics(res["equity"], res["benchmark"])
            dur = time.time() - t0
        except DatoCongeladoAusente as e:
            print(f"    NO EJECUTABLE: {e}")
            continue
        obs = dict(m)
        obs["n_vetos_wmax"] = len(res["vetos_wmax"])
        obs["n_vetos_vol"] = len(res["vetos_vol"])
        obs["exposicion_media"] = float(res["exposure"].mean())
        obs["n_dias"] = res["n_dias"]
        resultados[sello] = obs
        print(f"    ({dur:.1f}s, {res['n_dias']} dias)")
        for k, v in obs.items():
            print(f"    {k:<22} {v}")
        print()

    print("=" * 74)
    print("COMPARACION campo a campo contra el publicado")
    esperado = dict(m_pub)
    esperado["n_vetos_wmax"] = pub["n_vetos_wmax"]
    esperado["n_vetos_vol"] = pub["n_vetos_vol"]
    esperado["exposicion_media"] = pub["exposicion_media"]
    coincide = None
    for sello, obs in resultados.items():
        difs = []
        for k, ve in esperado.items():
            vo = obs.get(k)
            if vo is None:
                difs.append((k, ve, "ausente"))
            elif abs(float(vo) - float(ve)) > TOL:
                difs.append((k, ve, vo))
        print(f"\n  sello {sello}: {'IDENTICO' if not difs else str(len(difs)) + ' diferencia(s)'}")
        for k, ve, vo in difs:
            print(f"    {k}\n      publicado:    {ve}\n      reejecutado:  {vo}")
        if not difs:
            coincide = sello
    print()
    print("=" * 74)
    if coincide:
        print(f"VEREDICTO: REPRODUCE con el sello {coincide}.")
        print("El vinculo codigo<->resultados queda establecido tambien para")
        print("Fase B. Las cifras del dictamen 'SEÑAL DEBIL' salen de este")
        print("codigo con estos datos congelados.")
        return 0
    print("VEREDICTO: NO REPRODUCE con ninguno de los sellos congelados.")
    print("Es un hallazgo: las cifras publicadas de Fase B no se regeneran")
    print("desde el codigo y los datos que hay en el repo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
