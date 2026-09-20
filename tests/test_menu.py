"""src/ui/menu.py — pantalla de opciones (lo testeable sin el bucle bloqueante)."""
import pygame
import pygame_gui
import pytest

from src.core import i18n, settings
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


def _ir_a_pestana(menu, nombre):
    """Cambia de pestaña de Opciones con un clic real sobre su botón."""
    if menu._pestana == nombre:
        return
    boton = next(b for b, n in menu._botones_pestana.items() if n == nombre)
    _click(menu, boton, frames=2)
    assert menu._pestana == nombre


def _boton_control(menu, accion):
    _ir_a_pestana(menu, "controles")
    return menu._botones_controles[accion]


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


def test_aviso_de_que_las_flechas_y_esc_son_fijas(menu):
    """El jugador no debe tener que reasignar las flechas para poder usarlas."""
    menu._inicializar_interfaz_opciones()
    textos = " ".join(
        e.text for e in menu.ui_manager.get_root_container().elements
        if isinstance(e, pygame_gui.elements.UILabel)
    )
    assert "flechas" in textos.lower() and "esc" in textos.lower()


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
    _ir_a_pestana(menu, "audio")
    _mover_slider(menu, menu.slider_efectos, 0.27)
    _click(menu, menu.slider_efectos.right_button)
    assert menu.vol_efectos == pytest.approx(0.3)   # 0.27 -> 0.3, no 0.37


def test_flecha_desde_valor_libre_sin_salto_visible(menu):
    """El slider no debe pasar por 0.35 (±0.1 de pygame_gui) antes de cuadrar."""
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    _mover_slider(menu, menu.slider_musica, 0.25)
    menu.vol_musica = 0.25

    btn = menu.slider_musica.right_button
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(tipo, button=1, pos=btn.rect.center))
    picos = []
    for _ in range(6):
        menu._menu_opciones(1 / 60)
        picos.append(menu.slider_musica.get_current_value())

    assert max(picos) <= 0.3 + 1e-6       # nunca 0.35
    assert menu.vol_musica == pytest.approx(0.3)


def test_mantener_pulsada_la_flecha_no_dispara_el_volumen(menu):
    """pygame_gui, al mantener la flecha, arrancaba un scroll rápido; el volumen
    se "disparaba" y luego bajaba al escalón."""
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    menu._fijar_volumen("musica", 0.2)
    btn = menu.slider_musica.right_button

    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=btn.rect.center))
    picos = []
    for i in range(25):                       # ~0.4 s manteniendo pulsado
        menu._menu_opciones(1 / 60)
        picos.append(menu.slider_musica.get_current_value())
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=btn.rect.center))
    for _ in range(5):
        menu._menu_opciones(1 / 60)

    assert max(picos) <= 0.2 + 1e-6           # nunca se pasa de donde estaba
    assert menu.vol_musica == pytest.approx(0.3)   # al soltar, un solo paso


def test_flecha_del_slider_de_musica_actualiza_volumen(menu):
    """Antes las flechas del slider de música no hacían nada."""
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    _mover_slider(menu, menu.slider_musica, 0.5)
    _click(menu, menu.slider_musica.left_button)
    assert menu.vol_musica == pytest.approx(0.4)


def test_volumen_fuera_de_rango_no_bloquea_los_sliders(menu):
    """Un volumen ligeramente negativo dejaba el slider sin responder."""
    menu.vol_musica = -2.7755575615628914e-17
    menu.vol_efectos = -2.7755575615628914e-17
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    for _ in range(3):
        _click(menu, menu.slider_musica.right_button)
        _click(menu, menu.slider_efectos.right_button)
    assert menu.vol_musica == pytest.approx(0.3)
    assert menu.vol_efectos == pytest.approx(0.3)


def _pulsar_tecla_en_opciones(menu, tecla):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))
    menu._menu_opciones(0.016)


def test_clic_en_boton_de_control_empieza_a_escuchar(menu):
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    assert menu._reasignando_accion == "disparar"


def test_reasignar_disparar_actualiza_el_mapa_y_el_texto(menu):
    from src.core import controles
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    assert menu.controles["disparar"] == pygame.K_j
    assert controles.nombre_tecla(pygame.K_j) in _boton_control(menu, "disparar").text
    assert menu._reasignando_accion is None


def test_escape_cancela_la_reasignacion_sin_cambiar_nada(menu):
    menu._abrir_opciones()
    valor_previo = menu.controles["disparar"]
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_ESCAPE)
    assert menu.controles["disparar"] == valor_previo
    assert menu._reasignando_accion is None


def test_conflicto_entre_acciones_no_reasigna_y_avisa(menu):
    menu._abrir_opciones()
    valor_previo = menu.controles["disparar"]
    tecla_de_pausa = menu.controles["pausa"]
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, tecla_de_pausa)   # ya la usa "pausa"
    assert menu.controles["disparar"] == valor_previo   # no cambia
    assert menu._aviso_conflicto is not None


def test_restaurar_valores_por_defecto(menu):
    from src.core import controles
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    assert menu.controles["disparar"] == pygame.K_j

    _ir_a_pestana(menu, "controles")
    _click(menu, menu.btn_restaurar_controles)
    assert menu.controles == controles.POR_DEFECTO


def test_guardar_persiste_el_mapa_de_controles(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    _click(menu, menu.btn_guardar)

    from src.core import config
    assert config.cargar_controles(ruta=ruta)["disparar"] == pygame.K_j


def _boton_idioma(menu, codigo):
    _ir_a_pestana(menu, "idioma")
    return next(b for b, c in menu._botones_idioma.items() if c == codigo)


def test_hay_un_boton_por_idioma_y_el_actual_esta_marcado(menu):
    menu._abrir_opciones()
    assert set(menu._botones_idioma.values()) == set(i18n.IDIOMAS)
    assert _boton_idioma(menu, "es").is_selected
    assert not _boton_idioma(menu, "en").is_selected


def test_cambiar_de_idioma_es_inmediato_y_rehace_los_botones_del_menu(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    assert i18n.idioma_actual() == "en"
    assert menu.btn_jugar.texto == "Campaign"
    assert menu.btn_salir.texto == "Quit"
    assert menu.btn_actualizar.texto == "Update"


def test_cambiar_de_idioma_rehace_la_ui_de_opciones(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    textos = {e.text for e in menu.ui_manager.get_root_container().elements
              if isinstance(e, pygame_gui.elements.UILabel)}
    assert {"Music", "Effects"} <= textos
    assert {"Audio", "Language", "Controls", "Display"} == {b.text for b in menu._botones_pestana}
    assert menu.btn_guardar.text == "Save"
    assert "Fire" in _boton_control(menu, "disparar").text
    assert _boton_idioma(menu, "en").is_selected and not _boton_idioma(menu, "es").is_selected


def test_cambiar_de_idioma_conserva_los_volumenes_y_las_teclas(menu):
    menu._abrir_opciones()
    _mover_slider(menu, menu.slider_musica, 0.7)
    menu.controles["disparar"] = pygame.K_j
    _click(menu, _boton_idioma(menu, "en"))
    assert menu.vol_musica == pytest.approx(0.7)
    assert menu.slider_musica.get_current_value() == pytest.approx(0.7)
    assert menu.controles["disparar"] == pygame.K_j


def test_volver_a_pulsar_el_idioma_actual_no_hace_nada(menu):
    menu._abrir_opciones()
    ui = menu.ui_manager
    _click(menu, _boton_idioma(menu, "es"))
    assert menu.ui_manager is ui and i18n.idioma_actual() == "es"


def test_guardar_persiste_el_idioma(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    _click(menu, menu.btn_guardar)

    from src.core import config
    assert config.cargar_idioma(ruta=ruta) == "en"


def test_menu_persistente_rehace_sus_botones_si_el_idioma_cambio_fuera(menu):
    """Cambio de idioma desde la pausa de una partida (otro MenuManager)."""
    assert menu.btn_jugar.texto == "Campaña"
    i18n.establecer_idioma("en")
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)   # una sola pasada del bucle
    menu.ejecutar()
    assert menu.btn_jugar.texto == "Campaign"


def test_opciones_del_menu_persistente_siguen_el_idioma_cambiado_fuera(menu):
    """Opciones -> English; en una partida (otro MenuManager) -> Español; al volver
    al menú, sus Opciones deben estar en español y con Español marcado (no con la
    UI vieja en inglés, donde pulsar Español no hacía nada)."""
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))               # Opciones -> English
    menu.estado = "PRINCIPAL"

    i18n.establecer_idioma("es")                            # cambiado desde la pausa
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)
    menu.ejecutar()                                         # vuelve al menú principal

    menu._abrir_opciones()                                  # y abre Opciones
    textos = {e.text for e in menu.ui_manager.get_root_container().elements
              if isinstance(e, pygame_gui.elements.UILabel)}
    assert {"Música", "Efectos"} <= textos
    assert {"Audio", "Idioma", "Controles", "Pantalla"} == {b.text for b in menu._botones_pestana}
    assert _boton_idioma(menu, "es").is_selected and not _boton_idioma(menu, "en").is_selected

    _click(menu, _boton_idioma(menu, "en"))                 # ahora sí responde a ambos
    assert i18n.idioma_actual() == "en"
    _click(menu, _boton_idioma(menu, "es"))
    assert i18n.idioma_actual() == "es"
    assert _boton_idioma(menu, "es").is_selected


def _volver_al_menu_principal(menu):
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)   # una sola pasada del bucle
    menu.ejecutar()


def test_menu_persistente_ve_el_volumen_cambiado_desde_la_pausa(menu, rm, audio, scoreboard):
    """El menú de la pausa es otro MenuManager: sus cambios de volumen suenan al
    instante, y el menú principal debe partir de ellos (no de lo que leyó al
    crearse) para no pisarlos con "Guardar"."""
    pausa = MenuManager(menu.pantalla, rm, audio, scoreboard)
    pausa._abrir_opciones()
    pausa._fijar_volumen("musica", 0.9)
    pausa._fijar_volumen("efectos", 0.7)

    _volver_al_menu_principal(menu)
    menu._abrir_opciones()
    assert menu.slider_musica.get_current_value() == pytest.approx(0.9)
    assert menu.slider_efectos.get_current_value() == pytest.approx(0.7)


def test_menu_nuevo_parte_del_volumen_que_suena_no_del_del_disco(menu, rm, audio, scoreboard):
    """Reabrir Opciones desde la pausa tras un cambio sin guardar."""
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.85)
    otro = MenuManager(menu.pantalla, rm, audio, scoreboard)
    assert otro.vol_musica == pytest.approx(0.85)


def test_menu_persistente_ve_las_teclas_guardadas_desde_la_pausa(menu, rm, audio, scoreboard,
                                                                monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    pausa = MenuManager(menu.pantalla, rm, audio, scoreboard)
    pausa._abrir_opciones()
    _click(pausa, _boton_control(pausa, "disparar"))
    _pulsar_tecla_en_opciones(pausa, pygame.K_j)
    _click(pausa, pausa.btn_guardar)                       # guardadas en config.ini

    assert menu.controles["disparar"] == pygame.K_SPACE     # el persistente aún no lo sabe
    _volver_al_menu_principal(menu)
    assert menu.controles["disparar"] == pygame.K_j
    menu._abrir_opciones()
    assert "J" in _boton_control(menu, "disparar").text


def test_guardar_en_el_menu_persistente_no_pisa_lo_cambiado_en_la_pausa(menu, rm, audio, scoreboard,
                                                                       monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    pausa = MenuManager(menu.pantalla, rm, audio, scoreboard)
    pausa._abrir_opciones()
    pausa._fijar_volumen("musica", 0.9)
    _click(pausa, pausa.btn_guardar)

    _volver_al_menu_principal(menu)
    menu._abrir_opciones()
    _click(menu, menu.btn_guardar)                          # guardar sin tocar nada
    from src.core import config
    assert config.cargar_configuracion(ruta=ruta)[0] == pytest.approx(0.9)


# --- Volver descarta los cambios; Guardar los confirma ---

def test_volver_descarta_el_volumen_probado(menu, audio):
    musica0, efectos0 = audio.vol_musica, audio.vol_efectos
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)
    menu._fijar_volumen("efectos", 0.7)
    assert audio.vol_musica == pytest.approx(0.9)          # vista previa: suena al instante

    _click(menu, menu.btn_volver)

    assert audio.vol_musica == pytest.approx(musica0) and audio.vol_efectos == pytest.approx(efectos0)
    assert menu.vol_musica == pytest.approx(musica0) and menu.vol_efectos == pytest.approx(efectos0)
    assert menu.estado == "PRINCIPAL"
    menu._abrir_opciones()                                  # y Opciones lo enseña como antes
    assert menu.slider_musica.get_current_value() == pytest.approx(musica0)


def test_guardar_confirma_el_volumen_en_la_sesion_y_en_disco(menu, audio, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)
    _click(menu, menu.btn_guardar)

    assert audio.vol_musica == pytest.approx(0.9)          # sigue así en la sesión
    from src.core import config
    assert config.cargar_configuracion(ruta=ruta)[0] == pytest.approx(0.9)
    menu._abrir_opciones()
    assert menu.slider_musica.get_current_value() == pytest.approx(0.9)


def test_volver_descarta_el_idioma(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    assert i18n.idioma_actual() == "en"

    _click(menu, menu.btn_volver)

    assert i18n.idioma_actual() == "es"
    assert menu.btn_jugar.texto == "Campaña"                  # los botones del menú vuelven a español
    menu._abrir_opciones()
    assert "Idioma" in {b.text for b in menu._botones_pestana}
    assert _boton_idioma(menu, "es").is_selected


def test_guardar_confirma_el_idioma_en_la_sesion(menu, monkeypatch, tmp_path):
    monkeypatch.setattr("src.core.config.CONFIG_FILE", str(tmp_path / "cfg.ini"))
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    _click(menu, menu.btn_guardar)
    assert i18n.idioma_actual() == "en" and menu.btn_jugar.texto == "Campaign"


def test_rehacer_la_ui_al_cambiar_de_idioma_no_pierde_lo_que_habia_al_entrar(menu):
    """La UI se reconstruye al cambiar de idioma (vía `_abrir_opciones` interno);
    eso no debe tomar una instantánea nueva: Volver tiene que volver al ORIGINAL."""
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))               # varios frames: rehace la UI
    menu._fijar_volumen("musica", 0.9)
    _click(menu, menu.btn_volver)
    assert i18n.idioma_actual() == "es"


def test_volver_descarta_las_teclas_reasignadas(menu):
    antes = menu.controles["disparar"]
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    assert menu.controles["disparar"] == pygame.K_j

    _click(menu, menu.btn_volver)

    assert menu.controles["disparar"] == antes
    menu._abrir_opciones()
    assert "Espacio" in _boton_control(menu, "disparar").text


def test_guardar_confirma_las_teclas_en_la_sesion(menu, monkeypatch, tmp_path):
    monkeypatch.setattr("src.core.config.CONFIG_FILE", str(tmp_path / "cfg.ini"))
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    _click(menu, menu.btn_guardar)
    assert menu.controles["disparar"] == pygame.K_j


def test_cerrar_la_ventana_en_opciones_tambien_descarta(menu, audio):
    musica0 = audio.vol_musica
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    menu._menu_opciones(0.016)
    assert menu.resultado == "SALIR"
    assert audio.vol_musica == pytest.approx(musica0)


def test_cada_visita_a_opciones_toma_su_propia_instantanea(menu, audio, monkeypatch, tmp_path):
    """Lo guardado en una visita es el punto de partida de la siguiente."""
    monkeypatch.setattr("src.core.config.CONFIG_FILE", str(tmp_path / "cfg.ini"))
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)
    _click(menu, menu.btn_guardar)                         # 1ª visita: confirma 0.9

    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.3)
    _click(menu, menu.btn_volver)                          # 2ª visita: descarta -> vuelve a 0.9
    assert audio.vol_musica == pytest.approx(0.9)


# --- Pestañas de Opciones (Audio / Idioma / Controles) ---

def _visibles(menu, nombre):
    """True si todos los elementos de la pestaña están visibles; False si todos ocultos."""
    estados = {e.visible for e in menu._elementos_pestana[nombre]}
    assert len(estados) == 1, "una pestaña mezcla elementos visibles y ocultos"
    return estados.pop()


def test_hay_cuatro_pestanas_en_orden_y_se_entra_por_la_primera(menu):
    menu._abrir_opciones()
    assert list(menu._botones_pestana.values()) == ["controles", "idioma", "audio", "pantalla"]
    assert menu._pestana == "controles"
    assert _visibles(menu, "controles")
    assert not _visibles(menu, "idioma") and not _visibles(menu, "audio")
    assert next(b for b, n in menu._botones_pestana.items() if n == "controles").is_selected


def test_cambiar_de_pestana_muestra_solo_la_elegida(menu):
    menu._abrir_opciones()
    for nombre in ("idioma", "controles", "audio"):
        _ir_a_pestana(menu, nombre)
        for otra in ("audio", "idioma", "controles"):
            assert _visibles(menu, otra) == (otra == nombre)
        marcadas = [n for b, n in menu._botones_pestana.items() if b.is_selected]
        assert marcadas == [nombre]


def test_los_elementos_de_otra_pestana_no_reciben_clics(menu):
    """El botón de idioma "English" queda justo encima del slider de música, oculto:
    un clic ahí, con Audio abierta, debe caer en el slider y no cambiar el idioma."""
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    oculto = next(b for b, c in menu._botones_idioma.items() if c == "en")
    _click(menu, oculto)
    assert i18n.idioma_actual() == "es"


def test_guardar_y_volver_estan_siempre_visibles(menu):
    menu._abrir_opciones()
    for nombre in ("idioma", "controles", "audio"):
        _ir_a_pestana(menu, nombre)
        assert menu.btn_guardar.visible and menu.btn_volver.visible


def test_al_rehacer_la_ui_por_el_idioma_se_conserva_la_pestana(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))                # estamos en Idioma y se rehace la UI
    assert menu._pestana == "idioma"
    assert _visibles(menu, "idioma") and not _visibles(menu, "audio")


def test_cada_entrada_a_opciones_empieza_por_la_primera_pestana(menu):
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    _click(menu, menu.btn_volver)
    menu._abrir_opciones()
    assert menu._pestana == "controles" and _visibles(menu, "controles")
    assert not _visibles(menu, "audio")


def test_cambiar_de_pestana_cancela_una_reasignacion_a_medias(menu):
    menu._abrir_opciones()
    _click(menu, _boton_control(menu, "disparar"))
    assert menu._reasignando_accion == "disparar"
    _ir_a_pestana(menu, "audio")
    assert menu._reasignando_accion is None
    assert "Pulsa" not in menu._botones_controles["disparar"].text


def test_los_cambios_de_varias_pestanas_se_descartan_juntos_con_volver(menu, audio):
    musica0, tecla0 = audio.vol_musica, menu.controles["disparar"]
    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)                     # Audio
    _click(menu, _boton_idioma(menu, "en"))                # Idioma
    _click(menu, _boton_control(menu, "disparar"))         # Controles
    _pulsar_tecla_en_opciones(menu, pygame.K_j)

    _click(menu, menu.btn_volver)

    assert audio.vol_musica == pytest.approx(musica0)
    assert i18n.idioma_actual() == "es"
    assert menu.controles["disparar"] == tecla0


def test_aviso_de_conflicto_solo_se_dibuja_en_la_pestana_de_controles(menu):
    """No debe asomar un aviso de teclas encima del slider de audio."""
    import time
    menu._abrir_opciones()
    _ir_a_pestana(menu, "audio")
    menu._aviso_conflicto = "aviso de prueba"
    menu._aviso_conflicto_hasta = time.time() + 99
    menu._menu_opciones(0.016)          # en Audio: no debe romper ni dibujarse
    _ir_a_pestana(menu, "controles")
    menu._menu_opciones(0.016)


def test_restaurar_deja_aire_respecto_a_las_teclas(menu):
    """El botón "Restaurar" es distinto de las asignaciones: que no quede pegado."""
    menu._abrir_opciones()
    ultima_fila = max(b.rect.bottom for b in menu._botones_controles.values())
    assert menu.btn_restaurar_controles.rect.top - ultima_fila >= 30


def test_ui_de_opciones_se_reutiliza(menu):
    menu._abrir_opciones()
    primero = menu.ui_manager
    menu.estado = "PRINCIPAL"
    menu._abrir_opciones()
    assert menu.ui_manager is primero


def _clic_actualizar(menu):
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_actualizar.rect.center))
    menu._menu_principal()


def test_actualizar_sin_instalador_abre_el_navegador(menu, monkeypatch):
    """En desarrollo (no frozen) el botón siempre abre la web."""
    menu.actualizaciones.resultado = {
        "version": "9.9.9", "url": "http://descarga", "instalador_url": "http://x/setup.exe", "instalador_sha256": "a" * 64,
    }
    abierto = []
    monkeypatch.setattr("src.ui.menu.webbrowser.open", lambda u: abierto.append(u))
    monkeypatch.setattr("src.core.updates.puede_autoactualizar", lambda: False)

    _clic_actualizar(menu)
    assert abierto == ["http://descarga"]


def test_botones_bloqueados_mientras_se_descarga_la_actualizacion(menu, monkeypatch):
    """No se puede interrumpir la descarga jugando, abriendo opciones, etc."""
    menu.actualizaciones.resultado = {
        "version": "9.9.9", "url": "http://d", "instalador_url": "http://x/setup.exe", "instalador_sha256": "a" * 64,
    }

    class _DescargaFalsa:
        def __init__(self): self.progreso = 0.5; self.terminada = False; self.error = False
    menu._descarga = _DescargaFalsa()
    assert menu._descargando_actualizacion() is True

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_jugar.rect.center))
    menu._menu_principal()
    assert menu.ejecutando is True and menu.resultado is None   # "Jugar" no hizo nada

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_puntos.rect.center))
    menu._menu_principal()
    assert menu.estado == "PRINCIPAL"   # "Puntuaciones" tampoco


def test_actualizar_instalado_descarga_y_al_terminar_lanza_y_sale(menu, monkeypatch):
    menu.actualizaciones.resultado = {
        "version": "9.9.9", "url": "http://d", "instalador_url": "http://x/setup.exe", "instalador_sha256": "a" * 64,
    }
    monkeypatch.setattr("src.core.updates.puede_autoactualizar", lambda: True)

    class _DescargaFalsa:
        def __init__(self, url, sha256): self.progreso = 0.5; self.terminada = False; self.error = False; self.ruta = None
        def empezar(self): pass
    monkeypatch.setattr("src.core.updates.DescargaActualizacion", _DescargaFalsa)

    lanzado = []
    monkeypatch.setattr("src.core.updates.lanzar_instalador", lambda r: lanzado.append(r))

    _clic_actualizar(menu)
    assert isinstance(menu._descarga, _DescargaFalsa)      # descargando
    menu._menu_principal()                                  # sigue a 50%, no lanza
    assert not lanzado

    menu._descarga.terminada = True
    menu._descarga.ruta = "C:/tmp/setup.exe"
    menu._menu_principal()
    assert lanzado == ["C:/tmp/setup.exe"]
    assert menu.ejecutando is False and menu.resultado == "SALIR"


def test_actualizar_instalado_sin_hash_no_descarga_y_abre_la_web(menu, monkeypatch):
    """Sin SHA-256 no se puede verificar el instalador: no se instala solo."""
    menu.actualizaciones.resultado = {
        "version": "9.9.9", "url": "http://d", "instalador_url": "http://x/setup.exe",
        "instalador_sha256": None,
    }
    monkeypatch.setattr("src.core.updates.puede_autoactualizar", lambda: True)
    creadas = []
    monkeypatch.setattr("src.core.updates.DescargaActualizacion",
                        lambda *a: creadas.append(a))
    abierto = []
    monkeypatch.setattr("src.ui.menu.webbrowser.open", lambda u: abierto.append(u))

    _clic_actualizar(menu)
    assert creadas == [] and abierto == ["http://d"]


def test_actualizar_error_de_descarga_ofrece_la_web(menu, monkeypatch):
    menu.actualizaciones.resultado = {
        "version": "9.9.9", "url": "http://d", "instalador_url": "http://x/setup.exe", "instalador_sha256": "a" * 64,
    }
    monkeypatch.setattr("src.core.updates.puede_autoactualizar", lambda: True)

    class _DescargaFalsa:
        def __init__(self, url, sha256): self.progreso = 0.0; self.terminada = False; self.error = True; self.ruta = None
        def empezar(self): pass
    monkeypatch.setattr("src.core.updates.DescargaActualizacion", _DescargaFalsa)
    abierto = []
    monkeypatch.setattr("src.ui.menu.webbrowser.open", lambda u: abierto.append(u))

    _clic_actualizar(menu)      # arranca -> _dibujar detecta error -> _descarga_fallo
    assert menu._descarga is None and menu._descarga_fallo is True

    _clic_actualizar(menu)      # ahora el botón abre la web
    assert abierto == ["http://d"]


def test_sin_actualizacion_el_boton_no_hace_nada(menu, monkeypatch):
    menu.actualizaciones.resultado = False        # al día
    abierto = []
    monkeypatch.setattr("src.ui.menu.webbrowser.open", lambda u: abierto.append(u))

    pos = menu.btn_actualizar.rect.center
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    menu._menu_principal()

    assert abierto == []


def test_confirmar_salida_si_devuelve_true(menu):
    cx = menu.pantalla.get_rect().centerx
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(cx - 100, 345)))   # botón "Sí"
    assert menu._confirmar_salida() is True


def test_confirmar_salida_no_devuelve_false(menu):
    cx = menu.pantalla.get_rect().centerx
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=(cx + 110, 345)))   # botón "No"
    assert menu._confirmar_salida() is False


def test_confirmar_salida_quit_tambien_confirma(menu):
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert menu._confirmar_salida() is True


def test_boton_salir_confirmado_termina_el_menu(menu, monkeypatch):
    monkeypatch.setattr(menu, "_confirmar_salida", lambda: True)
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_salir.rect.center))
    menu._menu_principal()
    assert menu.ejecutando is False
    assert menu.resultado == "SALIR"


def test_boton_salir_cancelado_sigue_en_el_menu(menu, monkeypatch):
    monkeypatch.setattr(menu, "_confirmar_salida", lambda: False)
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_salir.rect.center))
    menu._menu_principal()
    assert menu.ejecutando is True
    assert menu.resultado is None


def test_boton_salir_bloqueado_durante_la_descarga(menu, monkeypatch):
    class _DescargaFalsa:
        def __init__(self): self.progreso = 0.1; self.terminada = False; self.error = False
    menu._descarga = _DescargaFalsa()
    llamado = []
    monkeypatch.setattr(menu, "_confirmar_salida", lambda: llamado.append(1) or True)
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_salir.rect.center))
    menu._menu_principal()
    assert llamado == []
    assert menu.ejecutando is True


def test_pantalla_de_puntuaciones_con_y_sin_nivel(menu):
    """Formato nuevo (con nivel) y antiguo (sin nivel) mezclados, sin crash."""
    menu.clasificacion.agregar_puntuacion("Ana", 300, nivel=3)
    menu.clasificacion.puntuaciones["Viejo"] = 150   # formato antiguo (int suelto)
    menu.estado = "PUNTUACIONES"
    menu._menu_puntuaciones()   # no debe lanzar excepción


def _fondo_oscurecido(menu):
    fondo = menu.rm.get_image("imagen_fondo1").copy()
    fondo.blit(menu._overlay_oscuro(), (0, 0))
    return fondo


def test_puntuaciones_oscurece_el_fondo_para_leer_mejor(menu):
    esperado = _fondo_oscurecido(menu)
    menu.estado = "PUNTUACIONES"
    menu._menu_puntuaciones()
    for pos in ((5, 795), (595, 795), (595, 5)):     # rincones sin texto
        assert menu.pantalla.get_at(pos)[:3] == esperado.get_at(pos)[:3]


def test_opciones_oscurece_el_fondo_para_leer_mejor(menu):
    esperado = _fondo_oscurecido(menu)
    menu._abrir_opciones()
    menu._menu_opciones(0.016)
    for pos in ((595, 5), (595, 795), (5, 795)):
        assert menu.pantalla.get_at(pos)[:3] == esperado.get_at(pos)[:3]


def test_pantalla_de_puntuaciones_vacia(menu):
    menu.estado = "PUNTUACIONES"
    menu._menu_puntuaciones()


def test_ejecutar_reinicia_su_estado(menu):
    menu.estado = "OPCIONES"
    menu.ejecutando = False
    menu.resultado = "SALIR"
    # simulamos una sola pasada del bucle
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)
    menu.ejecutar()
    assert menu.estado == "PRINCIPAL"


# --- Modo sin fin: botón y ranking -------------------------------------------

@pytest.fixture
def menu_con_rankings(rm, audio, scoreboard, tmp_path):
    from src.ui.scoreboard import SistemaClasificacion

    sin_fin = SistemaClasificacion(ruta_archivo=str(tmp_path / "sin_fin.json"))
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, sin_fin)


def _clic_menu(menu, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def test_el_boton_sin_fin_lanza_ese_modo(menu):
    _clic_menu(menu, menu.btn_sin_fin.rect.center)
    menu._menu_principal()
    assert menu.ejecutando is False and menu.resultado == "JUGAR_SIN_FIN"


def test_el_boton_de_campana_sigue_lanzando_la_campana(menu):
    _clic_menu(menu, menu.btn_jugar.rect.center)
    menu._menu_principal()
    assert menu.ejecutando is False and menu.resultado == "JUGAR"


def test_los_botones_del_menu_caben_en_orden_y_sin_solaparse(menu):
    botones = [menu.btn_jugar, menu.btn_sin_fin, menu.btn_opciones, menu.btn_puntos, menu.btn_salir]
    for arriba, abajo in zip(botones, botones[1:]):
        assert arriba.rect.bottom < abajo.rect.top
    assert botones[-1].rect.bottom < settings.ALTO - 40


def _filas_dibujadas(menu, monkeypatch):
    """Ejecuta un frame de Puntuaciones y devuelve las filas de texto dibujadas."""
    filas = []
    monkeypatch.setattr(menu, "_dibujar_fila_puntuaciones", lambda textos, *a, **k: filas.append(tuple(textos)))
    menu._menu_puntuaciones()
    return filas


def test_puntuaciones_arranca_en_la_campana_y_la_pestana_cambia_de_ranking(menu_con_rankings, monkeypatch):
    menu = menu_con_rankings
    menu.clasificacion.agregar_puntuacion("Ana", 100, nivel=2)
    menu.clasificacion_sin_fin.agregar_puntuacion("Beto", 900, nivel=7)

    _clic_menu(menu, menu.btn_puntos.rect.center)
    menu._menu_principal()
    assert menu.estado == "PUNTUACIONES"

    filas = _filas_dibujadas(menu, monkeypatch)          # 1er frame: dibuja y fija los rects de las pestañas
    assert ("1", "Ana", "100", "2") in filas and filas[0][3] == "Nivel"

    _clic_menu(menu, menu._pestanas_puntuaciones[settings.MODO_SIN_FIN].center)
    filas = _filas_dibujadas(menu, monkeypatch)
    assert menu.estado == "PUNTUACIONES"                 # pulsar una pestaña no vuelve al menú
    assert ("1", "Beto", "900", "7") in filas and filas[0][3] == "Oleada"
    assert all("Ana" not in fila for fila in filas)      # los rankings no se mezclan


def test_puntuaciones_un_clic_fuera_de_las_pestanas_vuelve_al_menu(menu_con_rankings, monkeypatch):
    menu = menu_con_rankings
    menu.estado = "PUNTUACIONES"
    _filas_dibujadas(menu, monkeypatch)
    _clic_menu(menu, (300, 700))
    menu._menu_puntuaciones()
    assert menu.estado == "PRINCIPAL"


def test_puntuaciones_siempre_se_abre_en_la_campana(menu_con_rankings):
    menu = menu_con_rankings
    menu._modo_puntuaciones = settings.MODO_SIN_FIN
    _clic_menu(menu, menu.btn_puntos.rect.center)
    menu._menu_principal()
    assert menu._modo_puntuaciones == settings.MODO_CAMPANA


def test_puntuaciones_sin_ranking_de_sin_fin_no_rompe(menu, monkeypatch):
    """La pausa crea un `MenuManager` sin el ranking del sin fin: no debe fallar."""
    menu._modo_puntuaciones = settings.MODO_SIN_FIN
    menu.estado = "PUNTUACIONES"
    assert _filas_dibujadas(menu, monkeypatch) == []


def test_pestanas_de_puntuaciones_en_ingles(menu_con_rankings):
    i18n.establecer_idioma("en")
    menu = menu_con_rankings
    menu.estado = "PUNTUACIONES"
    menu._menu_puntuaciones()                            # no debe lanzar excepción


# --- Pestaña Pantalla: interruptor del temblor de pantalla --------------------

def _boton_temblor(menu):
    _ir_a_pestana(menu, "pantalla")
    return menu.btn_temblor


def test_pestana_pantalla_muestra_el_interruptor_activado_por_defecto(menu):
    menu._abrir_opciones()
    boton = _boton_temblor(menu)
    assert boton.text == "Temblor de pantalla: Sí" and boton.is_selected


def test_pulsar_el_interruptor_apaga_y_enciende_al_instante(menu):
    from src.core import preferencias

    menu._abrir_opciones()
    _click(menu, _boton_temblor(menu))
    assert preferencias.temblor_activado() is False
    assert menu.btn_temblor.text == "Temblor de pantalla: No" and not menu.btn_temblor.is_selected
    _click(menu, menu.btn_temblor)
    assert preferencias.temblor_activado() is True


def test_volver_descarta_el_cambio_del_temblor(menu):
    from src.core import preferencias

    menu._abrir_opciones()
    _click(menu, _boton_temblor(menu))
    assert preferencias.temblor_activado() is False
    _click(menu, menu.btn_volver)
    assert preferencias.temblor_activado() is True


def test_guardar_confirma_el_temblor_en_la_sesion_y_en_disco(menu, monkeypatch, tmp_path):
    from src.core import config, preferencias

    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _click(menu, _boton_temblor(menu))
    _click(menu, menu.btn_guardar)
    assert preferencias.temblor_activado() is False
    assert config.cargar_temblor(ruta=ruta) is False


def test_guardar_sin_tocar_el_temblor_conserva_lo_que_habia(menu, monkeypatch, tmp_path):
    """Guardar escribe el estado actual aunque no se haya tocado esa pestaña."""
    from src.core import config, preferencias

    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    preferencias.establecer_temblor(False)
    menu._abrir_opciones()
    _click(menu, menu.btn_guardar)
    assert config.cargar_temblor(ruta=ruta) is False


def test_el_interruptor_se_descarta_junto_al_resto_de_cambios(menu, audio):
    from src.core import preferencias

    menu._abrir_opciones()
    menu._fijar_volumen("musica", 0.9)
    _click(menu, _boton_temblor(menu))
    _click(menu, menu.btn_volver)
    assert audio.vol_musica != 0.9 and preferencias.temblor_activado() is True


def test_otro_menu_ve_el_cambio_del_temblor_hecho_desde_la_pausa(menu, rm, audio, scoreboard):
    """El menú persistente muestra el estado real, no el de cuando se creó."""
    from src.core import preferencias

    pausa = MenuManager(menu.pantalla, rm, audio, scoreboard)
    pausa._abrir_opciones()
    _click(pausa, _boton_temblor(pausa))
    _click(pausa, pausa.btn_guardar)                  # confirmado: el estado vivo es "No"
    assert preferencias.temblor_activado() is False

    menu._abrir_opciones()
    assert _boton_temblor(menu).text == "Temblor de pantalla: No"


def test_el_texto_del_interruptor_sigue_el_idioma(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    assert _boton_temblor(menu).text == "Screen shake: Yes"


def test_las_cuatro_pestanas_caben_en_pantalla_sin_solaparse(menu):
    menu._abrir_opciones()
    rects = sorted((b.relative_rect for b in menu._botones_pestana), key=lambda r: r.x)
    assert len(rects) == 4
    for izq, der in zip(rects, rects[1:]):
        assert izq.right < der.left
    assert rects[0].left >= 0 and rects[-1].right <= settings.ANCHO


# --- Composición del menú principal ------------------------------------------

def test_el_titulo_y_los_botones_forman_un_bloque_centrado_en_la_pantalla(menu):
    from src.ui import menu as modulo_menu

    alto_titulo = menu.font_titulo.size("Galactic Guardian")[1]
    arriba = modulo_menu._MENU_TITULO_Y - alto_titulo / 2
    abajo = menu.btn_salir.rect.bottom
    assert abs((arriba + abajo) / 2 - settings.ALTO / 2) <= 20      # centro del bloque ~ centro de la pantalla


def test_el_titulo_queda_por_encima_del_primer_boton_con_aire(menu):
    from src.ui import menu as modulo_menu

    alto_titulo = menu.font_titulo.size("Galactic Guardian")[1]
    assert modulo_menu._MENU_TITULO_Y + alto_titulo / 2 + 30 <= menu.btn_jugar.rect.top


def test_el_aviso_de_actualizacion_va_debajo_de_los_botones_sin_solaparse(menu):
    from src.ui import menu as modulo_menu

    assert menu.btn_actualizar.rect.top > menu.btn_salir.rect.bottom
    assert menu.btn_actualizar.rect.bottom < settings.ALTO
    assert modulo_menu._MENU_AVISO_Y > menu.btn_salir.rect.bottom            # el texto también


def test_menu_principal_con_aviso_de_actualizacion_se_dibuja(menu):
    menu.actualizaciones.resultado = {"version": "9.9.9", "url": "http://d", "instalador_url": None,
                                      "instalador_sha256": None}
    menu._menu_principal()          # no debe lanzar excepción
