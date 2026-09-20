"""Pantalla "Mejoras" del menú (src/ui/menu.py) y las monedas en las pantallas finales."""
import pygame
import pytest

from src.core import i18n, settings
from src.core.engine import Juego
from src.ui.menu import MenuManager


@pytest.fixture
def menu(rm, audio, scoreboard, progresion):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion)


def _clic_principal(menu, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    menu._menu_principal()


def _clic(menu, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    menu._menu_mejoras()


def _clic_nodo(menu, id_):
    _clic(menu, menu._rects_mejoras[id_].center)


# --- Acceso desde el menú principal ------------------------------------------

def test_el_boton_mejoras_abre_la_pantalla(menu):
    _clic_principal(menu, menu.btn_mejoras.rect.center)
    assert menu.estado == "MEJORAS"


def test_los_seis_botones_del_menu_caben_en_orden_y_sin_solaparse(menu):
    botones = [menu.btn_jugar, menu.btn_sin_fin, menu.btn_mejoras, menu.btn_opciones, menu.btn_puntos, menu.btn_salir]
    for arriba, abajo in zip(botones, botones[1:]):
        assert arriba.rect.bottom < abajo.rect.top
    assert botones[-1].rect.bottom < menu.btn_actualizar.rect.top            # el aviso sigue debajo


def test_el_bloque_de_seis_botones_sigue_centrado(menu):
    from src.ui import menu as modulo

    alto_titulo = menu.font_titulo.size("Galactic Guardian")[1]
    arriba = modulo._MENU_TITULO_Y - alto_titulo / 2
    abajo = menu.btn_salir.rect.bottom
    assert abs((arriba + abajo) / 2 - settings.ALTO / 2) <= 20


# --- Geometría ---------------------------------------------------------------

def test_los_nodos_caben_en_pantalla_sin_solaparse(menu):
    rects = list(menu._rects_mejoras.values())
    assert len(rects) == 12
    pantalla = pygame.Rect(0, 0, settings.ANCHO, settings.ALTO)
    assert all(pantalla.contains(r) for r in rects)
    for i, a in enumerate(rects):
        assert not any(a.colliderect(b) for b in rects[i + 1:])
    for boton in (menu.btn_restablecer_mejoras.rect, menu.btn_volver_mejoras.rect):
        assert pantalla.contains(boton) and not any(boton.colliderect(r) for r in rects)


# --- Comprar y restablecer ---------------------------------------------------

def test_pulsar_un_nodo_lo_compra_y_descuenta(menu, progresion):
    progresion.ingresar(150)
    _clic_nodo(menu, "ataque_1")
    assert progresion.compradas == {"ataque_1"} and progresion.monedas == 50


def test_sin_saldo_avisa_y_no_compra(menu, progresion):
    progresion.ingresar(50)
    _clic_nodo(menu, "ataque_1")
    assert not progresion.compradas and progresion.monedas == 50
    assert menu._aviso_mejoras[0] == "No tienes monedas suficientes"


def test_un_nodo_bloqueado_avisa_y_no_compra(menu, progresion):
    progresion.ingresar(10_000)
    _clic_nodo(menu, "ataque_3")
    assert not progresion.compradas and progresion.monedas == 10_000
    assert menu._aviso_mejoras[0] == "Compra antes la mejora anterior"


def test_pulsar_una_comprada_no_hace_nada(menu, progresion):
    progresion.ingresar(500)
    _clic_nodo(menu, "ataque_1")
    saldo = progresion.monedas
    _clic_nodo(menu, "ataque_1")
    assert progresion.monedas == saldo and menu._aviso_mejoras is None


def test_restablecer_devuelve_las_monedas_y_avisa(menu, progresion):
    progresion.ingresar(500)
    _clic_nodo(menu, "ataque_1")
    _clic_nodo(menu, "defensa_1")
    _clic(menu, menu.btn_restablecer_mejoras.rect.center)
    assert progresion.monedas == 500 and not progresion.compradas
    assert menu._aviso_mejoras[0] == "Compras deshechas: +200 monedas"


def test_restablecer_sin_compras_avisa_que_no_hay_nada(menu):
    _clic(menu, menu.btn_restablecer_mejoras.rect.center)
    assert menu._aviso_mejoras[0] == "No hay nada que restablecer"


# --- Salir y avisos ----------------------------------------------------------

def test_volver_y_escape_vuelven_al_menu(menu):
    menu._abrir_mejoras()
    _clic(menu, menu.btn_volver_mejoras.rect.center)
    assert menu.estado == "PRINCIPAL"

    menu._abrir_mejoras()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    menu._menu_mejoras()
    assert menu.estado == "PRINCIPAL"


def test_cerrar_la_ventana_en_mejoras_sale_del_juego(menu):
    menu._abrir_mejoras()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    menu._menu_mejoras()
    assert menu.ejecutando is False and menu.resultado == "SALIR"


def test_el_aviso_caduca(menu):
    menu._aviso_mejoras = ("hola", pygame.time.get_ticks() - 1)             # ya caducado
    menu._menu_mejoras()
    assert menu._aviso_mejoras is None


def test_el_aviso_se_muestra_mientras_no_caduca(menu):
    menu._avisar_mejoras("hola")
    menu._menu_mejoras()
    assert menu._aviso_mejoras is not None


def test_abrir_la_pantalla_borra_el_aviso_anterior(menu):
    menu._avisar_mejoras("viejo")
    menu._abrir_mejoras()
    assert menu._aviso_mejoras is None


# --- Dibujado e idioma -------------------------------------------------------

@pytest.mark.parametrize("codigo", i18n.IDIOMAS)
def test_la_pantalla_se_dibuja_en_todos_los_estados_e_idiomas(menu, progresion, codigo):
    i18n.establecer_idioma(codigo)
    menu._crear_botones()
    progresion.ingresar(700)
    menu._abrir_mejoras()
    menu._menu_mejoras()                                      # casi todo bloqueado
    for id_ in ("ataque_1", "ataque_2", "defensa_1"):
        _clic_nodo(menu, id_)                                 # comprados, disponibles y sin saldo mezclados
    menu._menu_mejoras()


def test_los_botones_de_mejoras_siguen_el_idioma(menu):
    assert menu.btn_restablecer_mejoras.texto == "Restablecer" and menu.btn_mejoras.texto == "Mejoras"
    i18n.establecer_idioma("en")
    menu._crear_botones()
    assert menu.btn_restablecer_mejoras.texto == "Reset" and menu.btn_mejoras.texto == "Upgrades"


def test_sin_progresion_el_menu_usa_una_en_memoria(rm, audio, scoreboard):
    """La pausa crea un `MenuManager` sin progresión: no debe fallar ni tocar el disco."""
    sin = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    assert sin.progresion.persistir is False
    sin._abrir_mejoras()
    sin._menu_mejoras()


def test_menu_y_partida_comparten_la_misma_cuenta(menu, audio, scoreboard, rm, progresion):
    juego = Juego(pygame.display.get_surface(), audio, scoreboard, rm, progresion=progresion)
    juego.puntuacion = 700
    juego.volver_al_menu()
    assert menu.progresion.monedas == 7


# --- Monedas en las pantallas finales ---------------------------------------

def test_game_over_y_victoria_incluyen_las_monedas(juego, monkeypatch):
    lineas = []
    monkeypatch.setattr(juego.render_manager, "_dibujar_estadisticas",
                        lambda l, y, color=(255, 255, 255): lineas.append(list(l)))
    juego.puntuacion = 900
    juego._cobrar_monedas()
    juego.estado_game_over = True
    juego.dibujar()
    assert any("Monedas: +9 (total 9)" in l for l in lineas)

    lineas.clear()
    juego.estado_game_over = False
    juego.estado_victoria_final = True
    juego.dibujar()
    assert any("Monedas: +9 (total 9)" in l for l in lineas)


def test_sin_progresion_las_pantallas_finales_no_hablan_de_monedas(rm, audio, scoreboard, monkeypatch):
    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm)
    lineas = []
    monkeypatch.setattr(j.render_manager, "_dibujar_estadisticas",
                        lambda l, y, color=(255, 255, 255): lineas.append(list(l)))
    j.estado_game_over = True
    j.dibujar()
    assert lineas and not any("Monedas" in x for l in lineas for x in l)
