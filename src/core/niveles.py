"""Definición de los niveles de la campaña (solo datos).

Cada nivel es una `DefinicionNivel`: fases con su reparto de enemigos, cuándo
llega el jefe, cada cuánto aparece un enemigo y qué música suena. Añadir o
retocar un nivel es editar `NIVELES`; `WaveManager` y `Juego` solo leen de aquí.

`NIVELES` debe tener exactamente `settings.NIVEL_MAX` entradas (lo comprueba un
test). El nivel N es `NIVELES[N - 1]`.
"""

from dataclasses import dataclass

from src.entities.enemies import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe

T1, T2, T3 = EnemigoTipo1, EnemigoTipo2, EnemigoTipo3


@dataclass(frozen=True)
class Fase:
    """Tramo del nivel que empieza `desde_ms` después de arrancarlo.

    `enemigos` es el conjunto entre el que se elige al azar (uniforme): para
    dar más peso a un tipo basta con repetirlo, p. ej. `(T1, T1, T2)`.
    """
    desde_ms: int
    enemigos: tuple


@dataclass(frozen=True)
class DefinicionNivel:
    fases: tuple                # `Fase`s ordenadas por `desde_ms`; la primera empieza en 0
    tiempo_jefe_ms: int         # a partir de aquí ya no salen enemigos normales
    espera_jefe_ms: int         # margen tras cambiar la música hasta que aparece el jefe
    intervalo_spawn: tuple      # (mín, máx) ms entre apariciones de enemigos
    jefe: type = Jefe
    musica: str = "rain_of_lasers"
    musica_jefe: str = "deathmatch_theme"


NIVELES = (
    # Nivel 1
    DefinicionNivel(
        fases=(Fase(0, (T1,)), Fase(20000, (T1, T2)), Fase(38000, (T1, T2, T3))),
        tiempo_jefe_ms=52000, espera_jefe_ms=5000, intervalo_spawn=(900, 1100),
    ),
    # Nivel 2
    DefinicionNivel(
        fases=(Fase(0, (T1,)), Fase(17600, (T1, T2)), Fase(33440, (T1, T2, T3))),
        tiempo_jefe_ms=45760, espera_jefe_ms=5000, intervalo_spawn=(800, 1000),
    ),
    # Nivel 3
    DefinicionNivel(
        fases=(Fase(0, (T1,)), Fase(15200, (T1, T2)), Fase(28880, (T1, T2, T3))),
        tiempo_jefe_ms=39520, espera_jefe_ms=5000, intervalo_spawn=(600, 800),
    ),
    # Nivel 4
    DefinicionNivel(
        fases=(Fase(0, (T1,)), Fase(12800, (T1, T2)), Fase(24320, (T1, T2, T3))),
        tiempo_jefe_ms=33280, espera_jefe_ms=5000, intervalo_spawn=(500, 700),
    ),
    # Nivel 5
    DefinicionNivel(
        fases=(Fase(0, (T1,)), Fase(12000, (T1, T2)), Fase(22800, (T1, T2, T3))),
        tiempo_jefe_ms=31200, espera_jefe_ms=5000, intervalo_spawn=(400, 600),
    ),
)


def definicion_nivel(nivel):
    """Definición del nivel `nivel` (1..N). Por encima del último se repite el último."""
    return NIVELES[min(max(nivel, 1), len(NIVELES)) - 1]
