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


def test_feedback_efectos_arrastre_respeta_anti_spam(menu):
    menu._inicializar_interfaz_opciones()
    menu._feedback_sonoro_efectos()
    t = menu.tiempo_final_reproduccion
    menu._feedback_sonoro_efectos()          # inmediato: no relanza
    assert menu.tiempo_final_reproduccion == t


def test_feedback_efectos_flecha_reinicia_siempre(menu):
    import time
    menu._inicializar_interfaz_opciones()
    menu._feedback_sonoro_efectos()
    t = menu.tiempo_final_reproduccion
    time.sleep(0.01)
    menu._feedback_sonoro_efectos(reiniciar=True)   # relanza aunque el anterior no acabó
    assert menu.tiempo_final_reproduccion > t


def test_flecha_del_slider_de_efectos_actualiza_volumen(menu):
    menu._inicializar_interfaz_opciones()
    menu.slider_efectos.set_current_value(0.3)
    pygame.event.post(pygame.event.Event(
        pygame_gui.UI_BUTTON_PRESSED, ui_element=menu.slider_efectos.right_button))
    menu.estado, menu.opciones_cargadas = "OPCIONES", True
    menu._menu_opciones(0.016)
    assert menu.vol_efectos == 0.3


def test_ejecutar_reinicia_su_estado(menu):
    menu.estado = "OPCIONES"
    menu.ejecutando = False
    menu.resultado = "SALIR"
    # simulamos una sola pasada del bucle
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)
    menu.ejecutar()
    assert menu.estado == "PRINCIPAL"
