"""Curva de dificultad del modo sin fin (solo datos y funciones puras).

La partida se divide en **oleadas** numeradas desde 1. Cada una es una
`DefinicionNivel` (la misma estructura que un nivel de campaña, así que
`WaveManager` la lee igual) generada por `definicion_oleada(n)`:

- Una oleada normal dura `OLEADA_MS` y no tiene jefe; cuando se acaba el tiempo,
  `Juego` pasa a la siguiente.
- Cada `JEFE_CADA` oleadas toca una **de jefe**: el jefe sale nada más empezar
  (tras una breve espera con la música cambiada), no aparece ningún otro enemigo
  mientras dura, y la oleada acaba cuando cae.

No hay techo: el intervalo entre apariciones se estabiliza en `INTERVALO_MIN`,
pero la vida de los enemigos y de los jefes sigue creciendo con el número de
oleada (tablas de `escalado.py`, que siguen más allá del nivel 5) y la puntuación se multiplica por él.
"""

import math
from functools import lru_cache

from src.core.niveles import DefinicionNivel, Fase, T1, T2, T3

OLEADA_MS = 45000          # duración de una oleada normal
JEFE_CADA = 5              # una de cada N oleadas es de jefe
ESPERA_JEFE_MS = 3000      # margen entre el cambio de música y la aparición del jefe

INTERVALO_INICIAL = (900, 1100)   # (mín, máx) ms entre apariciones en la oleada 1 (como el nivel 1)
INTERVALO_PASO_MS = 100           # cuánto baja cada oleada, en cada extremo
INTERVALO_MIN = (500, 700)        # suelo: el ritmo del último nivel de la campaña


def es_oleada_de_jefe(oleada):
    return oleada % JEFE_CADA == 0


def intervalo_spawn(oleada):
    """(mín, máx) ms entre apariciones: baja `INTERVALO_PASO_MS` por oleada hasta el suelo."""
    bajada = INTERVALO_PASO_MS * (max(oleada, 1) - 1)
    return (max(INTERVALO_MIN[0], INTERVALO_INICIAL[0] - bajada),
            max(INTERVALO_MIN[1], INTERVALO_INICIAL[1] - bajada))


def enemigos(oleada):
    """Reparto de enemigos normales (uniforme; repetir una clase le da más peso)."""
    if oleada <= 1:
        return (T1,)
    if oleada == 2:
        return (T1, T1, T2)
    if oleada <= 4:
        return (T1, T2, T3)
    return (T1, T2, T2, T3, T3)


def definicion_oleada(oleada):
    """`DefinicionNivel` de la oleada `oleada` (1, 2, ...; menos de 1 cuenta como 1)."""
    return _definicion_oleada(max(oleada, 1))


@lru_cache(maxsize=None)
def _definicion_oleada(oleada):
    if es_oleada_de_jefe(oleada):
        # El jefe llega ya (tiempo 0 de la oleada): no salen enemigos normales.
        tiempo_jefe_ms = 0
    else:
        tiempo_jefe_ms = math.inf   # nunca: la oleada termina por tiempo, en `Juego`
    return DefinicionNivel(
        fases=(Fase(0, enemigos(oleada)),),
        tiempo_jefe_ms=tiempo_jefe_ms,
        espera_jefe_ms=ESPERA_JEFE_MS,
        intervalo_spawn=intervalo_spawn(oleada),
    )
