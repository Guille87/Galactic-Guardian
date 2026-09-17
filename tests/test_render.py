"""src/managers/render.py + src/ui/hud.py — que dibujar en cada estado no crashea."""
import pygame

from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe

DT60 = 1.0 / 60.0


def _poblar(juego, rm):
    em = juego.entity_manager
    em.agregar_enemigo(EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1))
    juego.jugador.ultimo_disparo = -99999
    juego.disparar()


def test_render_partida_activa(juego, rm):
    _poblar(juego, rm)
    juego.actualizar(DT60)
    juego.dibujar()


def test_render_en_pausa(juego, rm):
    _poblar(juego, rm)
    juego.actualizar(DT60)
    juego.dibujar()                     # un frame activo primero (para el snapshot)
    juego.pausar_juego()
    juego.dibujar()
    juego.dibujar()                     # segundo frame: reutiliza el snapshot


def test_render_game_over(juego):
    juego.estado_game_over = True
    juego.dibujar()


def test_render_pidiendo_nombre(juego):
    juego.pidiendo_nombre = True
    juego.nombre_entrada = "TEST"
    juego.dibujar()


def test_render_con_overlay_de_hitboxes(juego, rm):
    _poblar(juego, rm)
    juego.debug_hitboxes = True
    juego.actualizar(DT60)
    juego.dibujar()


def test_render_hud_con_jefe(juego, rm):
    img = rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)
    juego.jefe = Jefe(img, 200, 200, 600, 800, 2, juego.jugador)
    juego.ui_manager.dibujar_interfaz(pygame.display.get_surface())


def test_seleccion_nivel_incluye_el_siguiente_ademas_de_los_superados(juego):
    juego.nivel = 3
    juego.mostrando_seleccion_nivel = True
    juego.dibujar()
    niveles = [n for n, _ in juego.botones_seleccion_nivel]
    assert niveles == [1, 2, 3, 4]   # superados (1-3) + el siguiente (4)

    _, boton_siguiente = juego.botones_seleccion_nivel[-1]
    assert "siguiente" in boton_siguiente.texto.lower()


def test_seleccion_nivel_no_pasa_del_ultimo_nivel_de_la_campana(juego, monkeypatch):
    from src.core import settings
    monkeypatch.setattr(settings, "NIVEL_MAX", 3)
    juego.nivel = 3   # último nivel: no hay "siguiente" que ofrecer
    juego.mostrando_seleccion_nivel = True
    juego.dibujar()
    niveles = [n for n, _ in juego.botones_seleccion_nivel]
    assert niveles == [1, 2, 3]
