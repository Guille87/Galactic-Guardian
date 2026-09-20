"""src/entities/enemies.py — enemigos y jefe."""
import pygame
import pytest

from src.core import escalado, settings
from src.entities.bullet_enemy import BalaEnemigo
from src.entities.enemies import EnemigoBase, EnemigoTipo1, EnemigoTipo2, Jefe

DT60 = 1.0 / 60.0


@pytest.fixture
def img_enemigo(rm):
    return rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)


@pytest.fixture
def img_jefe(rm):
    return rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)


# --- Escalado de salud (tablas por nivel: ver `test_escalado.py`) ---

@pytest.mark.parametrize("nivel", [1, 2, 3, 4, 5])
def test_salud_enemigo_sigue_la_tabla(img_enemigo, nivel):
    e = EnemigoTipo1(img_enemigo, 100, 100, 600, nivel)
    assert e.salud_maxima == e.salud == round(EnemigoTipo1.SALUD_BASE * escalado.VIDA_X[nivel - 1])
    assert e.salud_maxima < 16 * EnemigoTipo1.SALUD_BASE       # nunca exponencial


def test_salud_jefe_crece_pero_no_se_dispara(img_jefe, jugador):
    saludes = [Jefe(img_jefe, 0, 0, 600, 800, n, jugador).salud_maxima for n in (1, 2, 3, 4, 5)]
    assert saludes == list(escalado.VIDA_JEFE)
    assert saludes == sorted(saludes)          # crece
    assert saludes[-1] < 8 * saludes[0]        # y no explota


def test_take_damage(img_enemigo):
    e = EnemigoTipo1(img_enemigo, 0, 0, 600, 3)
    s = e.salud
    e.take_damage(7)
    assert e.salud == s - 7


# --- Rebote en los bordes ---

def test_rebota_en_borde_izquierdo_con_velocidad_minima(img_enemigo):
    e = EnemigoTipo1(img_enemigo, 5, 100, 600, 1)
    e.velocidad_x = -0.05          # giro casi vertical
    e.rect.left = -3              # ya fuera
    e._rebotar_en_bordes()
    assert e.rect.left == 0
    assert e.velocidad_x >= settings.REBOTE_MIN_VX


def test_rebota_en_borde_derecho(img_enemigo):
    e = EnemigoTipo1(img_enemigo, 590, 100, 600, 1)
    e.rect.right = 605
    e._rebotar_en_bordes()
    assert e.rect.right == 600
    assert e.velocidad_x <= -settings.REBOTE_MIN_VX


def test_no_se_queda_pegado_con_dt_variable(img_enemigo):
    import random
    random.seed(1)
    e = EnemigoTipo1(img_enemigo, 5, 100, 600, 1)
    e.velocidad_x, e.velocidad_y = -0.05, 0.0
    xs = []
    for _ in range(200):
        e.movimiento_enemigo(random.choice([DT60] * 7 + [0.05, 1 / 30]))
        xs.append(e.rect.x)
    assert max(xs) > 40           # se despega de la pared


# --- Disparo enemigo ---

def test_tipo2_dispara_hacia_el_jugador(rm, jugador):
    img = rm.get_image_scaled("enemigo2", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo2(img, 300, 100, 600, 1, jugador)
    jugador.rect.center = (300, 700)          # justo debajo
    e.tiempo_ultimo_ataque = -99999
    bala = e.disparo_enemigo(0, rm, "bala_enemigo")
    assert isinstance(bala, BalaEnemigo)
    assert bala.dir_y > 0.9                   # apunta hacia abajo (al jugador)


def test_tipo2_respeta_su_cadencia(rm, jugador):
    img = rm.get_image_scaled("enemigo2", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo2(img, 300, 100, 600, 1, jugador)
    e.tiempo_ultimo_ataque = 0
    assert e.disparo_enemigo(e.cadencia - 1, rm, "bala_enemigo") is None
    assert e.disparo_enemigo(e.cadencia + 1, rm, "bala_enemigo") is not None


def test_bala_enemiga_sale_del_punto_de_aparicion(rm, jugador):
    """El vector director se calcula desde donde aparece la bala, no desde el centro."""
    img = rm.get_image_scaled("enemigo2", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo2(img, 40, 60, 600, 1, jugador)
    jugador.rect.center = (560, 720)
    e.tiempo_ultimo_ataque = -99999
    bala = e.disparo_enemigo(0, rm, "bala_enemigo")
    objetivo = pygame.Vector2(jugador.rect.center)
    dmin = min(
        pygame.Vector2(_avanzar(bala, i)).distance_to(objetivo) for i in range(300)
    )
    assert dmin < 12


def _avanzar(bala, _):
    bala.update(DT60)
    return bala.rect.center
