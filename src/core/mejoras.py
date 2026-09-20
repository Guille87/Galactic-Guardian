"""Mejoras permanentes de la nave (solo datos) y el `Bonus` que suman.

Se compran con monedas en la pantalla "Mejoras" del menú (ver `progresion.py`).
Forman tres ramas; dentro de una rama cada mejora se desbloquea al comprar la
anterior (`requiere`). Añadir o retocar una es editar `MEJORAS`: las ramas pueden
tener los nodos que hagan falta (la pantalla se desplaza). Sus textos están en el
catálogo (`mejoras.<id>.nombre` y `mejoras.<id>.desc`) y los de las ramas en
`mejoras.rama_<rama>`.

Un `efecto` es un diccionario campo del `Bonus` -> valor. Los bonus suben el
valor **de arranque** de la nave, nunca los topes de `Jugador.CONFIG` (velocidad 6,
8 disparos por segundo, 3 balas, 30 de daño). Los costes y los valores salen del
modelo de `tools/balance.py`: si cambias uno, vuelve a correrlo.
"""

from dataclasses import dataclass, field, fields

RAMAS = ("ataque", "defensa", "utilidad")


@dataclass(frozen=True)
class Bonus:
    """Suma de los efectos de las mejoras compradas (todo a cero = sin mejoras)."""
    salud_extra: int = 0                # salud máxima inicial (en puntos de salud reales)
    vidas_extra: int = 0                # vidas iniciales
    danio_extra: int = 0                # daño inicial (por bala, en puntos reales)
    disparos_extra: float = 0.0         # disparos por segundo de más
    balas_extra: int = 0                # balas por disparo de más (2 = doble, 3 = triple)
    velocidad_extra: float = 0.0        # velocidad inicial
    regen_s: float = 0.0                # salud que se recupera por segundo tras unos segundos sin daño
    invulnerable_extra_ms: int = 0      # escudo de reaparición más largo
    monedas_pct: float = 0.0            # +% de monedas (0.25 = +25 %)
    combo_factor: float = 1.0           # multiplica los umbrales del combo (<1 = más fácil)


@dataclass(frozen=True)
class Mejora:
    id: str
    rama: str
    coste: int
    efecto: dict = field(default_factory=dict)
    requiere: str = None                # id de la mejora anterior de su rama
    icono: str = None                   # nombre de imagen (`config.RECURSOS`) para su nodo, o ninguno


MEJORAS = (
    # --- Ataque: daño, cadencia y balas
    Mejora("ataque_1", "ataque", 60, {"danio_extra": 5}, icono="potenciador_danio"),
    Mejora("ataque_2", "ataque", 100, {"disparos_extra": 1.0}, requiere="ataque_1", icono="potenciador_cadencia"),
    Mejora("ataque_3", "ataque", 600, {"balas_extra": 1}, requiere="ataque_2", icono="potenciador_danio"),       # doble
    Mejora("ataque_4", "ataque", 750, {"danio_extra": 5}, requiere="ataque_3", icono="potenciador_danio"),
    Mejora("ataque_5", "ataque", 1100, {"disparos_extra": 1.0}, requiere="ataque_4", icono="potenciador_cadencia"),
    Mejora("ataque_6", "ataque", 1700, {"balas_extra": 1}, requiere="ataque_5", icono="potenciador_danio"),     # triple
    Mejora("ataque_7", "ataque", 2000, {"danio_extra": 5}, requiere="ataque_6", icono="potenciador_danio"),
    Mejora("ataque_8", "ataque", 2300, {"disparos_extra": 1.0}, requiere="ataque_7", icono="potenciador_cadencia"),
    Mejora("ataque_9", "ataque", 2700, {"danio_extra": 5}, requiere="ataque_8", icono="potenciador_danio"),
    Mejora("ataque_10", "ataque", 3100, {"disparos_extra": 1.0}, requiere="ataque_9", icono="potenciador_cadencia"),
    # --- Defensa: salud, vidas, regeneración y escudo
    Mejora("defensa_1", "defensa", 60, {"salud_extra": 15}, icono="curacion"),
    Mejora("defensa_2", "defensa", 150, {"salud_extra": 15}, requiere="defensa_1", icono="curacion"),
    Mejora("defensa_3", "defensa", 600, {"vidas_extra": 1}, requiere="defensa_2", icono="curacion"),
    Mejora("defensa_4", "defensa", 850, {"regen_s": 0.5}, requiere="defensa_3", icono="curacion"),
    Mejora("defensa_5", "defensa", 1100, {"salud_extra": 20}, requiere="defensa_4", icono="curacion"),
    Mejora("defensa_6", "defensa", 1250, {"invulnerable_extra_ms": 2000}, requiere="defensa_5"),
    Mejora("defensa_7", "defensa", 1500, {"salud_extra": 25}, requiere="defensa_6", icono="curacion"),
    Mejora("defensa_8", "defensa", 1800, {"regen_s": 0.5}, requiere="defensa_7", icono="curacion"),
    Mejora("defensa_9", "defensa", 2200, {"vidas_extra": 1}, requiere="defensa_8", icono="curacion"),
    Mejora("defensa_10", "defensa", 2600, {"salud_extra": 25}, requiere="defensa_9", icono="curacion"),
    # --- Utilidad: velocidad, monedas y combo
    Mejora("utilidad_1", "utilidad", 60, {"velocidad_extra": 0.25}, icono="potenciador_velocidad"),
    Mejora("utilidad_2", "utilidad", 120, {"monedas_pct": 0.25}, requiere="utilidad_1"),
    Mejora("utilidad_3", "utilidad", 500, {"velocidad_extra": 0.25}, requiere="utilidad_2", icono="potenciador_velocidad"),
    Mejora("utilidad_4", "utilidad", 750, {"combo_factor": 0.8}, requiere="utilidad_3"),
    Mejora("utilidad_5", "utilidad", 1000, {"monedas_pct": 0.25}, requiere="utilidad_4"),
    Mejora("utilidad_6", "utilidad", 1200, {"velocidad_extra": 0.25}, requiere="utilidad_5", icono="potenciador_velocidad"),
    Mejora("utilidad_7", "utilidad", 1600, {"monedas_pct": 0.25}, requiere="utilidad_6"),
    Mejora("utilidad_8", "utilidad", 2000, {"velocidad_extra": 0.25}, requiere="utilidad_7", icono="potenciador_velocidad"),
    Mejora("utilidad_9", "utilidad", 2500, {"combo_factor": 0.8}, requiere="utilidad_8"),
    Mejora("utilidad_10", "utilidad", 3000, {"monedas_pct": 0.5}, requiere="utilidad_9"),
)

POR_ID = {m.id: m for m in MEJORAS}


def de_la_rama(rama):
    """Las mejoras de una rama, en el orden en que se desbloquean."""
    return [m for m in MEJORAS if m.rama == rama]


def calcular_bonus(ids):
    """`Bonus` que suman las mejoras `ids` (ids desconocidos se ignoran)."""
    valores = {f.name: f.default for f in fields(Bonus)}
    for id_ in ids:
        mejora = POR_ID.get(id_)
        if mejora is None:
            continue
        for campo, valor in mejora.efecto.items():
            if campo == "combo_factor":                      # se multiplican
                valores[campo] *= valor
            else:                                            # el resto se suma
                valores[campo] += valor
    return Bonus(**valores)
