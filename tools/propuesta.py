"""Propuesta de reequilibrio de la campaña (datos de diseño, evaluables con `tools/balance.py`).

    python tools/propuesta.py                  # informe de la propuesta (perfil medio)
    python tools/propuesta.py --perfil todos   # con los tres perfiles

Todo lo que el reequilibrio va a cambiar, como **datos**: la nave base, el árbol
ampliado, las tablas de vida y de daño por nivel, la densidad de enemigos y la
economía. Se evalúa con el mismo modelo que el juego actual (`MODELO_PROPUESTO` frente
a `MODELO_ACTUAL`), así que se puede tocar un número y ver al momento qué pasa con la
dificultad y con cuántas partidas lleva completar la campaña.

Cuando se implemente en el juego, estos datos pasan a `niveles.py`, `mejoras.py`,
`Jugador.CONFIG` y `settings.py`, y este archivo desaparece.
"""
import os
import sys
from dataclasses import dataclass, field, replace

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src.core import niveles  # noqa: E402
from src.entities.enemies import Jefe  # noqa: E402
from tools import balance  # noqa: E402
from tools.balance import Modelo, Nave, PERFILES  # noqa: E402

# ----------------------------------------------------------------------------- nave base
BASE = dict(
    salud=50, vidas=3, danio=10, balas=1,
    disparos_s=4.0,              # antes 2,9 (350 ms); el tope pasa de 6,7 a 8 disparos/s
    velocidad=5.0,               # antes 4; el tope se queda en 6
    invulnerable_ms=3000,
)
TOPES = dict(velocidad=6.0, disparos_s=8.0, balas=3, danio=30)


# ----------------------------------------------------------------------------- árbol
@dataclass(frozen=True)
class Nodo:
    id: str
    rama: str
    coste: int
    efecto: dict = field(default_factory=dict)      # campo de `Nave` -> lo que suma
    requiere: str = None


ARBOL = (
    # Ataque: daño, cadencia y balas
    Nodo("ataque_1", "ataque", 60, {"danio": 5}),
    Nodo("ataque_2", "ataque", 100, {"disparos_s": 1.0}, "ataque_1"),
    Nodo("ataque_3", "ataque", 600, {"balas": 1}, "ataque_2"),                  # disparo doble
    Nodo("ataque_4", "ataque", 750, {"danio": 5}, "ataque_3"),
    Nodo("ataque_5", "ataque", 1100, {"disparos_s": 1.0}, "ataque_4"),
    Nodo("ataque_6", "ataque", 1700, {"balas": 1}, "ataque_5"),                 # disparo triple
    # Defensa: salud, vidas, regeneración y escudo
    Nodo("defensa_1", "defensa", 60, {"salud": 15}),
    Nodo("defensa_2", "defensa", 150, {"salud": 15}, "defensa_1"),
    Nodo("defensa_3", "defensa", 600, {"vidas": 1}, "defensa_2"),
    Nodo("defensa_4", "defensa", 850, {"regen_s": 0.5}, "defensa_3"),
    Nodo("defensa_5", "defensa", 1100, {"salud": 20}, "defensa_4"),
    Nodo("defensa_6", "defensa", 1250, {"invulnerable_ms": 2000}, "defensa_5"),
    # Utilidad: velocidad, monedas y combo
    Nodo("utilidad_1", "utilidad", 60, {"velocidad": 0.5}),
    Nodo("utilidad_2", "utilidad", 120, {"monedas_pct": 0.25}, "utilidad_1"),
    Nodo("utilidad_3", "utilidad", 500, {"velocidad": 0.5}, "utilidad_2"),
    Nodo("utilidad_4", "utilidad", 750, {}, "utilidad_3"),                      # combo más fácil (no se modela)
    Nodo("utilidad_5", "utilidad", 1000, {"monedas_pct": 0.25}, "utilidad_4"),
)


def nave_propuesta(ids, arbol=ARBOL):
    """La nave que sale de comprar `ids` con la base y los topes de la propuesta."""
    v = dict(BASE, monedas_pct=0.0, regen_s=0.0)
    por_id = {n.id: n for n in arbol}
    for id_ in ids:
        for campo, valor in por_id[id_].efecto.items():
            v[campo] += valor
    for campo, tope in TOPES.items():
        v[campo] = min(v[campo], tope)
    return Nave(**v)


# ----------------------------------------------------------------------------- niveles
# Por nivel (1..5): multiplicador de vida de los enemigos normales y del jefe, multiplicador del
# daño que hacen y (min, máx) de ms entre apariciones. Sustituyen a las fórmulas por nivel.
VIDA_X = (1.0, 1.4, 2.0, 2.8, 3.8)
VIDA_JEFE = (700, 1300, 2100, 3100, 4400)
DANIO_X = (0.6, 0.7, 0.8, 0.9, 1.0)
INTERVALOS = ((900, 1100), (800, 1000), (700, 900), (600, 800), (500, 700))
MONEDAS_PUNTOS = 70


def _definicion(nivel):
    base = niveles.definicion_nivel(nivel)
    return replace(base, intervalo_spawn=INTERVALOS[min(max(nivel, 1), len(INTERVALOS)) - 1])


def _vida(clase, nivel):
    i = min(max(nivel, 1), len(VIDA_X)) - 1
    if clase is Jefe:
        return VIDA_JEFE[i]
    return max(1, round(clase.SALUD_BASE * VIDA_X[i]))


def _danio_x(nivel):
    return DANIO_X[min(max(nivel, 1), len(DANIO_X)) - 1]


def construir():
    return Modelo(nombre="propuesta", definicion=_definicion, vida=_vida, danio_x=_danio_x, arbol=ARBOL,
                  nave=nave_propuesta, monedas_puntos=MONEDAS_PUNTOS)


MODELO_PROPUESTO = construir()


def main(argv=None):
    """Mismo informe que `tools/balance.py`, pero sobre la propuesta."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import argparse
    ap = argparse.ArgumentParser(description="Informe de la propuesta de reequilibrio.")
    ap.add_argument("--perfil", default="medio", choices=[*PERFILES, "todos"])
    ap.add_argument("--builds", default="0,25,50,75,100")
    ap.add_argument("--niveles", action="store_true")
    ap.add_argument("--objetivo", type=int, default=20)
    args = ap.parse_args(argv)

    perfiles = list(PERFILES.values()) if args.perfil == "todos" else [PERFILES[args.perfil]]
    fracciones = [float(x) / 100 for x in args.builds.split(",")]
    todos = list(PERFILES.values())
    m = MODELO_PROPUESTO

    balance.informe_supuestos(perfiles)
    balance.informe_arbol(m)
    for p in perfiles:
        balance.informe_builds(p, fracciones, m, args.niveles)
    balance.informe_matriz(todos, fracciones, m)
    balance.informe_poder_necesario(perfiles[0] if args.perfil != "todos" else PERFILES["medio"], m, fracciones)
    balance.informe_progresion(todos, m, args.objetivo)


if __name__ == "__main__":
    main()
