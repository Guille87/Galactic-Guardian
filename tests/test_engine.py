"""src/core/engine.py — Juego (estado de partida, pausa, transiciones)."""
import pytest

from src.core import settings
from src.entities.enemies import EnemigoTipo1

DT60 = 1.0 / 60.0


def test_construccion(juego, audio):
    assert juego.nivel == 1
    assert juego.pausado is False
    assert audio.pista_actual == "rain_of_lasers"
    assert juego.resultado == "MENU"


def test_el_reloj_de_juego_solo_avanza_al_actualizar(juego):
    t0 = juego.tiempo_juego
    for _ in range(10):
        juego.actualizar(DT60)
    assert juego.tiempo_juego == pytest.approx(t0 + 10 * DT60 * 1000)


def test_la_pausa_congela_el_reloj_de_juego(juego):
    for _ in range(20):
        juego.actualizar(DT60)          # ~333 ms de juego
    t = juego.tiempo_juego
    juego.pausar_juego()
    # mientras esté pausado el bucle no llama a actualizar; el reloj no se toca
    juego.reanudar_juego()
    assert juego.tiempo_juego == t


def test_la_cadencia_de_disparo_no_avanza_en_pausa(juego):
    juego.jugador.ultimo_disparo = -99999
    juego.disparar()                    # dispara, fija ultimo_disparo = tiempo_juego
    n = len(juego.entity_manager.balas)
    juego.pausar_juego()
    for _ in range(60):
        juego.disparar()               # tiempo_juego congelado -> no pasa la cadencia
    assert len(juego.entity_manager.balas) == n


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
    juego.jugador.mejorar_danio()
    juego.jugador.vidas = 1
    juego.jefe_derrotado = False
    juego.reiniciar_juego()
    assert juego.puntuacion == 0
    # El jugador se restablece in situ: misma instancia, estado inicial (item 14).
    assert juego.jugador is jugador_viejo
    assert juego.jugador.vidas == juego.jugador.CONFIG["vidas_init"]
    assert juego.jugador.danio == 1


def test_reiniciar_desde_cero_limpia_enemigos_golpeados(juego, rm):
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", (48, 48)), 0, 0, 600, 1)
    golpeados = juego.enemigos_golpeados
    juego.enemigos_golpeados[enemigo] = 123.0
    juego.jefe_derrotado = False
    juego.reiniciar_juego()
    assert juego.enemigos_golpeados is golpeados   # misma instancia, vaciada
    assert len(juego.enemigos_golpeados) == 0


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
