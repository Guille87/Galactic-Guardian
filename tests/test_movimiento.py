"""src/entities/base/movimiento.py — desplazamiento sub-pixel independiente de FPS."""
import pygame

from src.core import settings
from src.entities.base.movimiento import MovimientoSubpixel

DT60 = 1.0 / 60.0
DT30 = 1.0 / 30.0


class _Movil(MovimientoSubpixel):
    def __init__(self):
        self.rect = pygame.Rect(300, 300, 10, 10)
        self._init_subpixel()


def test_distancia_total_proporcional_a_la_velocidad():
    m = _Movil()
    x0 = m.rect.x
    for _ in range(60):
        m._desplazar(3.0, 0.0, DT60)          # 3 px/frame-a-60fps durante 1 s
    assert abs((m.rect.x - x0) - 180) <= 1     # ~180 px


def test_independiente_de_fps():
    a, b = _Movil(), _Movil()
    for _ in range(10):
        a._desplazar(0.0, 3.0, DT60)
    for _ in range(5):
        b._desplazar(0.0, 3.0, DT30)           # mismo tiempo total
    assert abs((a.rect.y - 300) - (b.rect.y - 300)) <= 1


def test_movimiento_simetrico_izquierda_derecha():
    der, izq = _Movil(), _Movil()
    for _ in range(20):
        der._desplazar(4.5, 0.0, DT60)
    for _ in range(20):
        izq._desplazar(-4.5, 0.0, DT60)
    assert (der.rect.x - 300) == -(izq.rect.x - 300)


def test_velocidad_fraccionaria_no_se_pierde():
    m = _Movil()
    x0 = m.rect.x
    for _ in range(100):
        m._desplazar(0.5, 0.0, DT60)           # con truncado se quedaría en 0
    assert (m.rect.x - x0) >= 45


def test_registra_ultimo_desplazamiento():
    m = _Movil()
    m._desplazar(3.0, -2.0, DT60)
    assert isinstance(m._ultimo_desplazamiento, pygame.Vector2)
    assert m._ultimo_desplazamiento.length() > 0
    m._desplazar(0.0, 0.0, DT60)
    assert m._ultimo_desplazamiento.length() == 0


def test_factor_dt_usa_fps_de_settings():
    m = _Movil()
    m._desplazar(1.0, 0.0, 1.0 / settings.FPS)  # factor == 1.0
    assert m.rect.x - 300 == 1
