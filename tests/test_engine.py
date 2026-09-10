"""src/core/engine.py — Juego (estado de partida, pausa, transiciones)."""
import pygame

from src.core import settings
from src.entities.enemies import EnemigoTipo1

DT60 = 1.0 / 60.0


def test_construccion(juego, audio):
    assert juego.nivel == 1
    assert juego.pausado is False
    assert audio.pista_actual == "rain_of_lasers"
    assert juego.resultado == "MENU"


def test_pausa_desplaza_los_temporizadores(juego, monkeypatch):
    reloj = {"t": 10_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: reloj["t"])
    juego.inicio_juego = reloj["t"]

    juego.pausar_juego()
    prox0, ini0 = juego.tiempo_proximo_enemigo, juego.inicio_juego
    reloj["t"] += 60_000                 # 60 s de pausa
    juego.reanudar_juego()

    assert juego.tiempo_proximo_enemigo == prox0 + 60_000
    assert juego.inicio_juego == ini0 + 60_000


def test_pausa_no_salta_a_la_fase_del_jefe(juego, monkeypatch):
    reloj = {"t": 5_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: reloj["t"])
    juego.inicio_juego = reloj["t"]

    reloj["t"] += 10_000                 # 10 s de juego
    juego.pausar_juego()
    reloj["t"] += 120_000                # 2 min de pausa
    juego.reanudar_juego()

    fase = pygame.time.get_ticks() - juego.inicio_juego
    assert fase < settings.TIEMPO_JEFE   # sigue lejos del jefe


def test_reiniciar_avance_de_nivel(juego, rm):
    juego.jefe_derrotado = True
    bala_ficticia = EnemigoTipo1(rm.get_image_scaled("enemigo1", (48, 48)), 0, 0, 600, 1)
    juego.entity_manager.agregar_bala_enemigo(bala_ficticia)
    juego.reiniciar_juego()
    assert juego.nivel == 2
    assert len(juego.entity_manager.balas_enemigo) == 1   # balas del jefe conservadas


def test_reiniciar_desde_cero(juego):
    juego.puntuacion = 500
    jugador_viejo = juego.jugador
    juego.jefe_derrotado = False
    juego.reiniciar_juego()
    assert juego.puntuacion == 0
    assert juego.jugador is not jugador_viejo


def test_disparar_añade_balas(juego):
    juego.jugador.ultimo_disparo = -99999
    juego.disparar()
    assert len(juego.entity_manager.balas) >= 1


def test_impacto_jugador_con_salud_pierde_vida_y_reaparece(juego):
    vidas0 = juego.jugador.vidas
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.jugador.vidas == vidas0 - 1
    assert juego.jugador.salud == juego.jugador.salud_maxima
    assert juego.jugador.invulnerable is True


def test_transiciones_de_estado(juego):
    juego.volver_al_menu()
    assert juego.resultado == "MENU" and juego.ejecutando is False

    juego.ejecutando = True
    juego.salir_del_juego()
    assert juego.resultado == "SALIR" and juego.ejecutando is False


def test_actualizar_muchos_frames_sin_crash(juego):
    juego.disparando = True
    for _ in range(400):
        juego.disparar()
        juego.actualizar(DT60)
