"""src/ui/menu.py — pantalla de opciones (lo testeable sin el bucle bloqueante)."""
import pygame
import pygame_gui
import pytest

from src.core import settings
from src.ui.menu import MenuManager


@pytest.fixture
def menu(rm, audio, scoreboard):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)


def test_sliders_con_incremento_pequeno(menu):
    menu._inicializar_interfaz_opciones()
    assert menu.slider_musica.increment == settings.VOLUMEN_PASO
    assert menu.slider_efectos.increment == settings.VOLUMEN_PASO


def test_etiquetas_de_los_sliders(menu):
    menu._inicializar_interfaz_opciones()
    textos = {
        e.text for e in menu.ui_manager.get_root_container().elements
        if isinstance(e, pygame_gui.elements.UILabel)
    }
    assert {"Música", "Efectos"} <= textos


def test_ejecutar_reinicia_su_estado(menu):
    menu.estado = "OPCIONES"
    menu.ejecutando = False
    menu.resultado = "SALIR"
    # simulamos una sola pasada del bucle
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)
    menu.ejecutar()
    assert menu.estado == "PRINCIPAL"
