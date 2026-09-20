"""Mejoras permanentes de la nave (solo datos) y el `Bonus` que suman.

Se compran con monedas en la pantalla "Mejoras" del menú (ver `progresion.py`).
Forman tres ramas de cuatro mejoras cada una; dentro de una rama cada mejora se
desbloquea al comprar la anterior (`requiere`). Añadir o retocar una es editar
`MEJORAS`. Sus textos están en el catálogo (`mejoras.<id>.nombre` y
`mejoras.<id>.desc`) y los de las ramas en `mejoras.rama_<rama>`.

Un `efecto` es un diccionario campo del `Bonus` -> valor. Los bonus suben el
valor **de arranque** de la nave, no los topes: los ítems de la partida siguen
sirviendo. Los costes y valores son de primera pasada.
"""

from dataclasses import dataclass, field, fields

RAMAS = ("ataque", "defensa", "utilidad")

# Orden de los tipos de disparo iniciales: el mayor que dé alguna mejora gana.
_ORDEN_DISPARO = ("simple", "doble", "triple")


@dataclass(frozen=True)
class Bonus:
    """Suma de los efectos de las mejoras compradas (todo a cero = sin mejoras)."""
    salud_extra: int = 0                # salud máxima inicial (en puntos de salud reales)
    vidas_extra: int = 0                # vidas iniciales
    danio_extra: int = 0                # daño inicial (por bala, en puntos reales)
    cadencia_menos_ms: int = 0          # ms menos entre disparos
    velocidad_extra: float = 0.0        # velocidad inicial
    disparo_inicial: str = "simple"     # tipo de disparo con el que se empieza
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
    # --- Ataque
    Mejora("ataque_1", "ataque", 100, {"danio_extra": 10}, icono="potenciador_danio"),
    Mejora("ataque_2", "ataque", 200, {"cadencia_menos_ms": 50}, requiere="ataque_1", icono="potenciador_cadencia"),
    Mejora("ataque_3", "ataque", 300, {"cadencia_menos_ms": 50}, requiere="ataque_2", icono="potenciador_cadencia"),
    Mejora("ataque_4", "ataque", 400, {"disparo_inicial": "doble"}, requiere="ataque_3", icono="potenciador_danio"),
    # --- Defensa
    Mejora("defensa_1", "defensa", 100, {"salud_extra": 10}, icono="curacion"),
    Mejora("defensa_2", "defensa", 200, {"vidas_extra": 1}, requiere="defensa_1", icono="curacion"),
    Mejora("defensa_3", "defensa", 300, {"salud_extra": 10}, requiere="defensa_2", icono="curacion"),
    Mejora("defensa_4", "defensa", 400, {"invulnerable_extra_ms": 2000}, requiere="defensa_3"),
    # --- Utilidad
    Mejora("utilidad_1", "utilidad", 100, {"velocidad_extra": 0.5}, icono="potenciador_velocidad"),
    Mejora("utilidad_2", "utilidad", 200, {"monedas_pct": 0.25}, requiere="utilidad_1"),
    Mejora("utilidad_3", "utilidad", 300, {"monedas_pct": 0.25}, requiere="utilidad_2"),   # provisional: Botín II
    Mejora("utilidad_4", "utilidad", 400, {"combo_factor": 0.8}, requiere="utilidad_3"),
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
            elif campo == "disparo_inicial":                 # gana el mejor
                if _ORDEN_DISPARO.index(valor) > _ORDEN_DISPARO.index(valores[campo]):
                    valores[campo] = valor
            else:                                            # el resto se suma
                valores[campo] += valor
    return Bonus(**valores)
