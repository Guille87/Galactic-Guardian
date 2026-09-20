"""Salud y daño en números reales (la nave 50 de salud y 10 de daño; balas enemigas de 10, jefe de 20).

El daño que llega a la nave en cada nivel es el de `settings` multiplicado por
`escalado.danio_x(nivel)`: esa parte se prueba en `test_escalado.py`.
"""
import math

import pytest

from src.core import mejoras, settings
from src.entities.bullet import Bala
from src.entities.enemies import EnemigoBase, EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from src.entities.player import Jugador

# --- Constantes --------------------------------------------------------------

def test_los_danios_en_numeros_reales():
    assert (settings.DANIO_CONTACTO, settings.DANIO_EMBESTIDA) == (10, 10)
    assert (settings.DANIO_BALA_TIPO2, settings.DANIO_BALA_TIPO3) == (10, 10)
    assert (settings.DANIO_JEFE_NORMAL, settings.DANIO_JEFE_RAPIDA) == (20, 10)


def test_la_nave_y_su_bala_en_numeros_reales():
    c = Jugador.CONFIG
    assert (c["salud_max"], c["danio_base"], c["danio_max"]) == (50, 10, 30)


def test_las_mejoras_de_salud_y_dano_estan_en_numeros_reales():
    assert mejoras.POR_ID["ataque_1"].efecto == {"danio_extra": 5}
    assert mejoras.POR_ID["defensa_1"].efecto == {"salud_extra": 15}


# --- Daño que hace y aguanta cada cosa ---------------------------------------

@pytest.fixture
def imgs(rm):
    return (rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR),
            rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE))


def _crear(clase, imgs, nivel, jugador):
    img, img_jefe = imgs
    if clase is EnemigoTipo1:
        return EnemigoTipo1(img, 0, 0, 600, nivel)
    if clase is Jefe:
        return Jefe(img_jefe, 0, 0, 600, 800, nivel, jugador)
    return clase(img, 0, 0, 600, nivel, jugador)


def test_los_impactos_que_aguanta_la_nave_base():
    """50 de salud: 5 golpes de 10, 3 disparos pesados del jefe, 5 golpes de choque."""
    salud = Jugador.CONFIG["salud_max"]
    assert math.ceil(salud / settings.DANIO_BALA_TIPO2) == 5
    assert math.ceil(salud / settings.DANIO_JEFE_NORMAL) == 3
    assert math.ceil(salud / settings.DANIO_CONTACTO) == 5


def test_los_disparos_enemigos_llevan_su_dano_a_plena_dificultad(rm, jugador, imgs):
    """En el último nivel el multiplicador de daño es 1: la bala hace lo que dice `settings`."""
    img, _ = imgs
    for clase, esperado in ((EnemigoTipo2, settings.DANIO_BALA_TIPO2), (EnemigoTipo3, settings.DANIO_BALA_TIPO3)):
        e = clase(img, 300, 100, 600, settings.NIVEL_MAX, jugador)
        bala = e.disparo_enemigo(10_000, rm, "bala_enemigo")
        assert bala.danio == esperado == 10


def test_los_disparos_del_jefe_llevan_su_dano_a_plena_dificultad(rm, jugador, imgs):
    jefe = _crear(Jefe, imgs, settings.NIVEL_MAX, jugador)
    assert jefe.disparo_jefe(10_000, rm, "bala_enemigo2").danio == 20
    assert jefe.disparo_rapido(10_000, rm, "bala_enemigo").danio == 10


def test_la_bala_de_la_nave_hace_el_dano_de_la_nave(rm, jugador):
    balas = jugador.disparar(10_000, rm.get_image_rotated("bala_jugador1", Bala.TAMANO, Bala.ANGULO))
    assert [b.danio for b in balas] == [10]


# --- En la partida -----------------------------------------------------------

def test_un_impacto_de_bala_enemiga_quita_su_dano(juego, rm, jugador):
    from src.entities.bullet_enemy import BalaEnemigo
    img = rm.get_image_rotated("bala_enemigo", BalaEnemigo.TAMANO, 0)
    bala = BalaEnemigo(img, *juego.jugador.rect.center, 0, 1, settings.DANIO_BALA_TIPO2, 4)
    juego.entity_manager.agregar_bala_enemigo(bala)
    antes = juego.jugador.salud
    juego.collision_manager.actualizar(juego.tiempo_juego)
    assert juego.jugador.salud == antes - settings.DANIO_BALA_TIPO2


def test_el_choque_quita_a_la_nave_lo_del_nivel_y_diez_al_enemigo(juego, rm):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo1(img, 0, 0, 600, settings.NIVEL_MAX)          # a plena dificultad
    e.salud = e.salud_maxima = 100
    e.rect.center = juego.jugador.rect.center
    juego.entity_manager.agregar_enemigo(e)
    juego.collision_manager.actualizar(juego.tiempo_juego + settings.CONTACTO_COOLDOWN_MS + 1)
    assert juego.jugador.salud == juego.jugador.salud_maxima - settings.DANIO_CONTACTO
    assert e.salud == 100 - settings.DANIO_EMBESTIDA


def test_el_disparo_pesado_del_jefe_mata_en_tres_impactos(juego):
    golpes = 0
    while juego.jugador.salud > 0:
        juego.jugador.recibir_danio(settings.DANIO_JEFE_NORMAL)
        golpes += 1
    assert golpes == 3


# --- Barra de salud bajo la nave ---------------------------------------------

VERDE, GRIS = (0, 255, 100), (60, 60, 60)


def _barra(juego, salud):
    pantalla = juego.pantalla
    pantalla.fill((0, 0, 0))
    juego.jugador.rect.bottom = 700       # la nave arranca pegada abajo: la barra saldría de la pantalla
    juego.jugador.salud = salud
    juego.ui_manager._dibujar_indicador_salud_nave(pantalla)
    j = juego.jugador
    ancho = max(24, round(j.salud_maxima * juego.ui_manager.PX_POR_PUNTO_DE_SALUD))
    x0, y = j.rect.centerx - ancho // 2, j.rect.bottom + 12 + 2
    return pantalla, x0, ancho, y


def test_la_barra_esta_llena_con_la_salud_completa(juego):
    pantalla, x0, ancho, y = _barra(juego, juego.jugador.salud_maxima)
    assert ancho == 48                                              # lo que ocupaban los cinco puntitos
    assert pantalla.get_at((x0 + 2, y))[:3] == VERDE and pantalla.get_at((x0 + ancho - 2, y))[:3] == VERDE


def test_la_barra_se_vacia_de_derecha_a_izquierda(juego):
    pantalla, x0, ancho, y = _barra(juego, juego.jugador.salud_maxima // 2)
    assert pantalla.get_at((x0 + 2, y))[:3] == VERDE
    assert pantalla.get_at((x0 + ancho - 2, y))[:3] == GRIS


def test_sin_salud_no_hay_verde(juego):
    pantalla, x0, ancho, y = _barra(juego, 0)
    assert all(pantalla.get_at((x0 + i, y))[:3] != VERDE for i in range(ancho))


def test_hay_una_marca_oscura_cada_diez_de_salud(juego):
    pantalla, x0, ancho, y = _barra(juego, juego.jugador.salud_maxima)
    marcas = [i for i in range(ancho) if pantalla.get_at((x0 + i, y))[:3] == (20, 20, 20)]
    assert len(marcas) == juego.jugador.salud_maxima // 10 - 1     # 4 marcas para 5 tramos de 10


def test_mas_salud_maxima_alarga_la_barra(juego):
    juego.jugador.salud_maxima = 70
    _, _, ancho, _ = _barra(juego, 70)
    assert ancho == round(70 * 0.96)


def test_la_barra_no_falla_con_la_salud_por_debajo_de_cero_o_por_encima(juego):
    _barra(juego, -5)
    _barra(juego, juego.jugador.salud_maxima + 20)
