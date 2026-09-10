"""Pruebas de integración: varios sistemas juntos, muchos frames, sin crash.

Port del harness headless que se usó durante la auditoría.
"""
import random

import pygame

from src.entities.enemies import EnemigoBase, EnemigoTipo1, EnemigoTipo2, Jefe

DT60 = 1.0 / 60.0


def _img_enemigo(rm):
    return rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)


def test_partida_completa_sin_crash(juego, rm):
    """Simula ~15 s de juego con disparo continuo y enemigos."""
    juego.disparando = True
    juego.entity_manager.agregar_enemigo(EnemigoTipo1(_img_enemigo(rm), 300, -40, 600, 1))
    for i in range(900):
        juego.disparar()
        juego.actualizar(DT60)
        juego.dibujar()
        if i % 300 == 150:                       # pausa/reanuda por el camino
            juego.pausar_juego()
            juego.reanudar_juego()


def test_derrota_del_jefe_sube_de_nivel(juego, rm):
    img = rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)
    jefe = Jefe(img, 200, 200, 600, 800, 1, juego.jugador)
    jefe.salud = 1
    juego.jefe = jefe
    juego.entity_manager.agregar_enemigo(jefe)

    juego.jugador.ultimo_disparo = -99999
    juego.disparar()
    bala = list(juego.entity_manager.balas)[0]
    bala.rect.center = jefe.rect.center
    bala.radius = 300

    juego.collision_manager.actualizar()
    nivel0 = juego.nivel
    juego.actualizar(DT60)                       # procesa pendiente_reinicio
    assert juego.nivel == nivel0 + 1


def test_jefe_no_se_atasca_con_dt_variable(juego, rm):
    img = rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)
    jefe = Jefe(img, 200, -150, 600, 800, 1, juego.jugador)
    random.seed(2)
    xs = []
    for _ in range(3000):
        jefe.update(random.choice([DT60] * 7 + [0.04, 0.05, 1 / 30]))
        xs.append(jefe.rect.x)
    assert min(xs[300:]) >= -1
    assert max(xs[300:]) + Jefe.TAMANO_JEFE[0] <= 601


def test_bala_enemiga_apunta_al_jugador_quieto(juego, rm):
    img = rm.get_image_scaled("enemigo2", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo2(img, 40, 60, 600, 1, juego.jugador)
    juego.jugador.rect.center = (550, 720)
    e.tiempo_ultimo_ataque = -99999
    bala = e.disparo_enemigo(0, rm, "bala_enemigo")

    objetivo = pygame.Vector2(juego.jugador.rect.center)
    dmin = float("inf")
    for _ in range(300):
        bala.update(DT60)
        dmin = min(dmin, pygame.Vector2(bala.rect.center).distance_to(objetivo))
    assert dmin < 12


def test_movimiento_igual_a_30_y_60_fps(juego, rm):
    a = EnemigoTipo1(_img_enemigo(rm), 300, 50, 600, 1)
    b = EnemigoTipo1(_img_enemigo(rm), 300, 50, 600, 1)
    a.velocidad_x = b.velocidad_x = 0.0
    a.velocidad_y = b.velocidad_y = 3.0
    for _ in range(10):
        a.movimiento_enemigo(DT60)
    for _ in range(5):
        b.movimiento_enemigo(1 / 30)
    assert abs(a.rect.y - b.rect.y) <= 1
