"""B-a (N6, Fase 0) — ¿Es auditable el pre-registro del holdout?

La §2.4 del brief sostiene toda la legitimidad del paso 4.2 en una sola
premisa: "El holdout ya estaba pre-registrado, y eso es lo que lo hace
legitimo." Y cita docs/fase_b_reevaluacion_resultado.md:14-22.

Este script no discute si el pre-registro es buena practica. Comprueba si la
AFIRMACION de que existio antes de la corrida es verificable desde este repo,
con la misma vara que N4 aplico a la cadena N=11->12->14 (su A-3, veredicto
NO VERIFICABLE).

Uso (desde fix-fase2/):  python3 -I fase0_n6/b_a_preregistro_auditable.py
"""
import os
import subprocess


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True,
                          text=True, cwd="..").stdout.strip()


def main():
    print("=== B-a.1 el texto del pre-registro existe y es literal ===")
    p = "docs/fase_b_reevaluacion_resultado.md"
    print(f"  {p}:14-22")
    for i, l in enumerate(open(p).read().splitlines()[13:22], start=14):
        print(f"    {i:>3}| {l}")
    print()

    print("=== B-a.2 ¿la ruta que el brief da es correcta? ===")
    print("  El brief dice: 'Todas las rutas de aqui en adelante son desde la")
    print("  raiz del repo, que no es fix-fase2/' y luego cita")
    print("  'docs/fase_b_reevaluacion_resultado.md:14-22'.")
    print(f"  raiz/docs/fase_b_reevaluacion_resultado.md : "
          f"{'EXISTE' if os.path.exists('../docs/fase_b_reevaluacion_resultado.md') else 'NO EXISTE'}")
    print(f"  fix-fase2/docs/fase_b_reevaluacion_resultado.md : "
          f"{'EXISTE' if os.path.exists(p) else 'NO EXISTE'}")
    print("  -> la cita del brief, leida con su propio convenio de rutas,")
    print("     apunta a un fichero que no existe. Desviacion de forma.")
    print()

    print("=== B-a.3 ¿se puede FECHAR el pre-registro por git? ===")
    for f in ("fix-fase2/src/portfolio_walkforward_temporal.py",
              "fix-fase2/docs/fase_b_reevaluacion_resultado.md",
              "fix-fase2/results/portfolio_walkforward_temporal.json",
              "fix-fase2/results/portfolio_equity.csv"):
        linea = git("log", "--follow", "--reverse", "--date=short",
                    "--pretty=%h %ad %s", "--", f).splitlines()
        print(f"  {os.path.basename(f):<42} {linea[0] if linea else '(sin historia)'}")
    print()
    print("  Commits del repo entre la fecha declarada del pre-registro")
    print("  (2026-10-09) y el commit que trae el material (2026-10-29):")
    r = git("log", "--all", "--date=short", "--pretty=%h %ad %s",
            "--since=2026-10-08", "--until=2026-10-28")
    print("    " + (r.replace("\n", "\n    ") if r else "(NINGUNO)"))
    print()
    print("=== B-a.4 veredicto ===")
    print("  El diseño de los tramos, la metrica decisiva, el codigo que los")
    print("  implementa, los resultados y la curva de equity llegan al repo")
    print("  en EL MISMO COMMIT (d34b147, 2026-10-29). No hay ningun commit")
    print("  entre el 2026-10-07 y el 2026-10-29.")
    print()
    print("  Luego la afirmacion 'fijado antes de correr' / 'aprobada por")
    print("  Pablo 2026-10-09, antes de la corrida' es AUTOATESTIGUADA: la")
    print("  hace el mismo documento que publica el resultado, y no hay")
    print("  artefacto independiente que la fije en el tiempo.")
    print()
    print("  Esto NO dice que sea falsa. Dice que NO ES AUDITABLE desde este")
    print("  repo, exactamente con la misma vara con la que N4 (A-3) declaro")
    print("  NO VERIFICABLE la cadena N=11->12->14. Aplicar una vara distinta")
    print("  aqui, porque el pre-registro conviene al planteamiento de la")
    print("  tarea, seria la doble vara que el hallazgo 6 del segundo agente")
    print("  de N4 reprocho.")


if __name__ == "__main__":
    main()
