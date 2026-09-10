"""src/ui/menu.py — pantalla de opciones (lo testeable sin el bucle bloqueante)."""
import pygame
import pygame_gui
import pytest

from src.core import settings
from src.ui.menu import MenuManager, _clamp_volumen, _paso_volumen


def _mover_slider(menu, slider, valor):
    """Simula un arrastre: fija el valor y emite el evento de pygame_gui."""
    slider.set_current_value(valor)
    pygame.event.post(pygame.event.Event(
        pygame_gui.UI_HORIZONTAL_SLIDER_MOVED, ui_element=slider, value=valor))
    menu._menu_opciones(0.016)


def _click(menu, boton, frames=5):
    """Clic real de ratón sobre un elemento y varios frames de bucle.

    Un `UI_BUTTON_PRESSED` sintético no basta: el slider solo se mueve si
    detecta que su propia flecha recibió un clic de ratón de verdad."""
    centro = boton.rect.center
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(tipo, button=1, pos=centro))
    for _ in range(frames):
        menu._menu_opciones(0.016)


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


@pytest.mark.parametrize("entrada,esperado", [
    (0.5, 0.5),
    (0.273843, 0.27),                    # arrastre libre: solo se redondea a 2 dec.
    (2.7755575615628914e-17, 0.0),       # residuo de coma flotante -> 0
    (-1e-17, 0.0),                        # negativo minúsculo -> 0 (no fuera de rango)
    (1.5, 1.0),
    ("no es un número", 0.5),
])
def test_clamp_volumen(entrada, esperado):
    assert _clamp_volumen(entrada) == esperado


@pytest.mark.parametrize("valor,sube,esperado", [
    (0.27, True, 0.3), (0.27, False, 0.2),
    (0.2, True, 0.3), (0.2, False, 0.1),     # en la rejilla: salta al siguiente
    (0.0, False, 0.0), (1.0, True, 1.0),     # no se sale de [0, 1]
])
def test_paso_volumen(valor, sube, esperado):
    assert _paso_volumen(valor, sube) == pytest.approx(esperado)


def test_arrastre_permite_valores_libres(menu):
    menu._abrir_opciones()
    _mover_slider(menu, menu.slider_musica, 0.27)
    assert menu.vol_musica == pytest.approx(0.27)   # NO se cuadra a 0.3


def test_flecha_cuadra_un_valor_libre(menu):
    menu._abrir_opciones()
    _mover_slider(menu, menu.slider_efectos, 0.27)
    _click(menu, menu.slider_efectos.right_button)
    assert menu.vol_efectos == pytest.approx(0.3)   # 0.27 -> 0.3, no 0.37


def test_flecha_del_slider_de_musica_actualiza_volumen(menu):
    """Antes las flechas del slider de música no hacían nada."""
    menu._abrir_opciones()
    _mover_slider(menu, menu.slider_musica, 0.5)
    _click(menu, menu.slider_musica.left_button)
    assert menu.vol_musica == pytest.approx(0.4)


def test_volumen_fuera_de_rango_no_bloquea_los_sliders(menu):
    """Un volumen ligeramente negativo dejaba el slider sin responder."""
    menu.vol_musica = -2.7755575615628914e-17
    menu.vol_efectos = -2.7755575615628914e-17
    menu._abrir_opciones()
    for _ in range(3):
        _click(menu, menu.slider_musica.right_button)
        _click(menu, menu.slider_efectos.right_button)
    assert menu.vol_musica == pytest.approx(0.3)
    assert menu.vol_efectos == pytest.approx(0.3)


def test_ui_de_opciones_se_reutiliza(menu):
    menu._abrir_opciones()
    primero = menu.ui_manager
    menu.estado = "PRINCIPAL"
    menu._abrir_opciones()
    assert menu.ui_manager is primero


def test_ejecutar_reinicia_su_estado(menu):
    menu.estado = "OPCIONES"
    menu.ejecutando = False
    menu.resultado = "SALIR"
    # simulamos una sola pasada del bucle
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)
    menu.ejecutar()
    assert menu.estado == "PRINCIPAL"
