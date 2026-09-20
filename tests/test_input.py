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


def test_clic_reanudar_en_pausa_continua_la_partida(juego):
    juego.pausar_juego()
    juego.dibujar()   # crea boton_reanudar/boton_opciones/boton_salir
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=juego.boton_reanudar.rect.center)
    _procesar(juego)
    assert juego.pausado is False


def test_teclas_y_disparo_ignorados_durante_la_transicion_de_nivel(juego):
    """Durante la transición `pausado` sigue en False (el fondo y la nave se
    siguen actualizando solos), pero el jugador no debe poder hacer nada."""
    juego.transicion_activa = True

    _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    _procesar(juego)
    assert juego.pausado is False   # Esc no pausa durante la transición

    _evento(pygame.KEYDOWN, key=pygame.K_SPACE)
    _procesar(juego)
    assert juego.disparando is False

    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=(300, 400))
    _procesar(juego)
    assert juego.disparando is False


def test_teclas_ignoradas_en_game_over(juego):
    """Esc/P en Game Over no deben reanudar el juego (descuadraría los timers)."""
    juego.estado_game_over = True
    juego.pausado = True                 # como lo deja juego_terminado()
    ini0 = juego.inicio_juego
    for tecla in (pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE):
        _evento(pygame.KEYDOWN, key=tecla)
        _procesar(juego)
    assert juego.inicio_juego == ini0
    assert juego.pausado is True


def test_entrada_de_nombre_tras_victoria_final(juego):
    juego.pidiendo_nombre = True
    juego.pidiendo_nombre_para = "victoria"
    juego.nombre_entrada = "AN"
    juego.puntuacion = 999
    _evento(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")
    _procesar(juego)
    assert juego.pidiendo_nombre is False
    assert juego.estado_victoria_final is True
    assert juego.estado_game_over is False


def test_teclas_ignoradas_en_pantallas_de_campana(juego):
    for atributo in ("estado_nivel_completado", "mostrando_seleccion_nivel", "estado_victoria_final"):
        setattr(juego, atributo, True)
        juego.pausado = True
        _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        _procesar(juego)
        assert juego.pausado is True   # Esc no reanuda ni descuadra nada
        setattr(juego, atributo, False)


def test_clic_continuar_en_nivel_completado_avanza_de_nivel(juego):
    juego.nivel = 1
    juego.jefe_derrotado = True
    juego.estado_nivel_completado = True
    juego.pausado = True
    juego.dibujar()   # crea boton_continuar / boton_elegir_nivel
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=juego.boton_continuar.rect.center)
    _procesar(juego)
    assert juego.nivel == 2
    assert juego.estado_nivel_completado is False


def test_clic_elegir_nivel_abre_el_selector(juego):
    juego.nivel = 2
    juego.estado_nivel_completado = True
    juego.pausado = True
    juego.dibujar()
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=juego.boton_elegir_nivel.rect.center)
    _procesar(juego)
    assert juego.mostrando_seleccion_nivel is True
    assert juego.estado_nivel_completado is False


def test_clic_en_selector_de_nivel_salta_a_ese_nivel(juego):
    juego.nivel = 3
    juego.jugador.danio = 20           # mejora que un nivel "a rejugar" debe perder
    juego.mostrando_seleccion_nivel = True
    juego.pausado = True
    juego.dibujar()   # crea los botones de los niveles 1..4 (superados + el siguiente)
    _, boton_nivel_2 = juego.botones_seleccion_nivel[1]
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=boton_nivel_2.rect.center)
    _procesar(juego)
    assert juego.nivel == 2
    assert juego.mostrando_seleccion_nivel is False
    assert juego.jugador.danio == juego.jugador.CONFIG["danio_base"]    # nivel a rejugar: nave desde cero


def test_clic_en_el_siguiente_nivel_del_selector_conserva_las_mejoras(juego):
    """El botón "(siguiente)" es el mismo camino que Continuar: no resetea la
    nave ni la puntuación, a diferencia de rejugar un nivel ya superado."""
    juego.nivel = 3
    juego.jefe_derrotado = True        # lo deja así al_eliminar_enemigo
    juego.jugador.danio = 20
    juego.puntuacion = 500
    juego.mostrando_seleccion_nivel = True
    juego.pausado = True
    juego.dibujar()
    nivel_siguiente, boton_siguiente = juego.botones_seleccion_nivel[-1]
    assert nivel_siguiente == 4

    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=boton_siguiente.rect.center)
    _procesar(juego)

    assert juego.nivel == 4
    assert juego.jugador.danio == 20   # se conserva, como con "Continuar"
    assert juego.puntuacion == 500


def test_clic_jugar_de_nuevo_en_victoria_final_reinicia_desde_nivel_1(juego):
    juego.nivel = 5
    juego.estado_victoria_final = True
    juego.pausado = True
    juego.dibujar()
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=juego.boton_reintentar_final.rect.center)
    _procesar(juego)
    assert juego.nivel == 1
    assert juego.estado_victoria_final is False


def test_clic_menu_en_victoria_final_vuelve_al_menu(juego):
    juego.nivel = 5
    juego.estado_victoria_final = True
    juego.pausado = True
    juego.dibujar()
    _evento(pygame.MOUSEBUTTONDOWN, button=1, pos=juego.boton_menu_final.rect.center)
    resultado = _procesar(juego)
    assert resultado is False
    assert juego.resultado == "MENU"


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
    assert ("AN", 500, juego.nivel) in juego.clasificacion.obtener_puntuaciones_top()


def test_disparo_y_pausa_usan_la_tecla_reasignada(juego):
    """Tras reasignar "disparar" a J y "pausa" a O, esas teclas hacen lo suyo."""
    juego.input_handler.mapa_teclas["disparar"] = pygame.K_j
    juego.input_handler.mapa_teclas["pausa"] = pygame.K_o

    _evento(pygame.KEYDOWN, key=pygame.K_j)
    _procesar(juego)
    assert juego.disparando is True

    _evento(pygame.KEYDOWN, key=pygame.K_o)
    _procesar(juego)
    assert juego.pausado is True


def test_espacio_ya_no_dispara_si_se_reasigno_disparar(juego):
    juego.input_handler.mapa_teclas["disparar"] = pygame.K_j
    _evento(pygame.KEYDOWN, key=pygame.K_SPACE)
    _procesar(juego)
    assert juego.disparando is False


def test_escape_pausa_siempre_aunque_se_reasigne_pausa(juego):
    """Esc es fija: sigue pausando aunque "pausa" apunte a otra tecla."""
    juego.input_handler.mapa_teclas["pausa"] = pygame.K_o
    _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    _procesar(juego)
    assert juego.pausado is True
