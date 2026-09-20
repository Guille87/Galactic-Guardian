"""Escalado de la dificultad por nivel (solo datos y funciones puras).

Tres tablas, una entrada por nivel de la campaña (`settings.NIVEL_MAX`):

- `VIDA_X`: multiplicador de la vida de los enemigos normales (su `SALUD_BASE` es la del nivel 1).
- `VIDA_JEFE`: vida del jefe (número real, no multiplicador: cada jefe es una pelea distinta).
- `DANIO_X`: multiplicador del daño que hacen los enemigos (balas y embestida). Empieza por
  debajo de 1 para que el primer nivel se pueda completar con la nave sin mejoras.

Los valores salen del modelo de `tools/balance.py` (la campaña está pensada para completarse
en unas 20 partidas con la progresión); si cambias uno, vuelve a correrlo.

Más allá del último nivel (el modo sin fin numera las oleadas sin techo) la vida sigue subiendo
con el mismo paso que entre los dos últimos niveles y el daño se queda en el del último.
Esto vive aparte de `niveles.py` porque lo leen las entidades, que `niveles.py` importa.
"""

VIDA_X = (1.0, 1.4, 2.0, 2.8, 3.8)
VIDA_JEFE = (700, 1300, 2100, 3100, 4400)
DANIO_X = (0.6, 0.7, 0.8, 0.9, 1.0)


def _indice(nivel, tabla):
    return min(max(nivel, 1), len(tabla)) - 1


def _extra(nivel, tabla):
    """Niveles por encima del último de la tabla (0 dentro de la campaña)."""
    return max(nivel - len(tabla), 0)


def vida_x(nivel):
    """Multiplicador de vida de los enemigos normales en `nivel`."""
    paso = VIDA_X[-1] - VIDA_X[-2]
    return VIDA_X[_indice(nivel, VIDA_X)] + paso * _extra(nivel, VIDA_X)


def vida_jefe(nivel):
    """Vida del jefe en `nivel`."""
    paso = VIDA_JEFE[-1] - VIDA_JEFE[-2]
    return VIDA_JEFE[_indice(nivel, VIDA_JEFE)] + paso * _extra(nivel, VIDA_JEFE)


def danio_x(nivel):
    """Multiplicador del daño enemigo en `nivel`."""
    return DANIO_X[_indice(nivel, DANIO_X)]
