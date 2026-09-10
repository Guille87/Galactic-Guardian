"""src/core/input.py — InputHandler (traducción de eventos a acciones)."""
import pygame


def _evento(tipo, **kw):
    pygame.event.post(pygame.event.Event(tipo, **kw))


def _procesar(juego):
    return juego.input_handler.manejar_eventos()


def test_quit_cierra_la_app(juego):
    _evento(pygame.QUIT)
    assert _procesar(juego) is False
    assert juego.resultado == "SALIR"


def test_espacio_activa_y_desactiva_el_disparo(juego):
    _evento(pygame.KEYDOWN, key=pygame.K_SPACE)
    _procesar(juego)
    assert juego.disparando is True

    _evento(pygame.KEYUP, key=pygame.K_SPACE)
    _procesar(juego)
    assert juego.disparando is False


def test_escape_pausa_y_reanuda(juego):
    _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    _procesar(juego)
    assert juego.pausado is True

    _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    _procesar(juego)
    assert juego.pausado is False


def test_f1_activa_el_overlay_de_debug(juego):
    estado0 = juego.debug_hitboxes
    _evento(pygame.KEYDOWN, key=pygame.K_F1)
    _procesar(juego)
    assert juego.debug_hitboxes is not estado0


def test_no_dispara_mientras_esta_pausado(juego):
    juego.disparando = True
    juego.pausar_juego()
    juego.jugador.ultimo_disparo = -99999
    _procesar(juego)
    assert len(juego.entity_manager.balas) == 0


def test_entrada_de_nombre_en_game_over(juego):
    juego.pidiendo_nombre = True
    juego.nombre_entrada = ""
    juego.puntuacion = 500
    for letra in "ANA":
        _evento(pygame.KEYDOWN, key=ord(letra.lower()), unicode=letra)
        _procesar(juego)
    assert juego.nombre_entrada == "ANA"

    _evento(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode="")
    _procesar(juego)
    assert juego.nombre_entrada == "AN"

    _evento(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")
    _procesar(juego)
    assert juego.pidiendo_nombre is False
    assert juego.estado_game_over is True
    assert ("AN", 500) in juego.clasificacion.obtener_puntuaciones_top()
