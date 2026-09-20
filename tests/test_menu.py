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
    _mover_slider(menu, menu.slider_efectos, 0.27)
    _click(menu, menu.slider_efectos.right_button)
    assert menu.vol_efectos == pytest.approx(0.3)   # 0.27 -> 0.3, no 0.37


def test_flecha_desde_valor_libre_sin_salto_visible(menu):
    """El slider no debe pasar por 0.35 (±0.1 de pygame_gui) antes de cuadrar."""
    menu._abrir_opciones()
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


def _pulsar_tecla_en_opciones(menu, tecla):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))
    menu._menu_opciones(0.016)


def test_clic_en_boton_de_control_empieza_a_escuchar(menu):
    menu._abrir_opciones()
    _click(menu, menu._botones_controles["disparar"])
    assert menu._reasignando_accion == "disparar"


def test_reasignar_disparar_actualiza_el_mapa_y_el_texto(menu):
    from src.core import controles
    menu._abrir_opciones()
    _click(menu, menu._botones_controles["disparar"])
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    assert menu.controles["disparar"] == pygame.K_j
    assert controles.nombre_tecla(pygame.K_j) in menu._botones_controles["disparar"].text
    assert menu._reasignando_accion is None


def test_escape_cancela_la_reasignacion_sin_cambiar_nada(menu):
    menu._abrir_opciones()
    valor_previo = menu.controles["disparar"]
    _click(menu, menu._botones_controles["disparar"])
    _pulsar_tecla_en_opciones(menu, pygame.K_ESCAPE)
    assert menu.controles["disparar"] == valor_previo
    assert menu._reasignando_accion is None


def test_conflicto_entre_acciones_no_reasigna_y_avisa(menu):
    menu._abrir_opciones()
    valor_previo = menu.controles["disparar"]
    tecla_de_pausa = menu.controles["pausa"]
    _click(menu, menu._botones_controles["disparar"])
    _pulsar_tecla_en_opciones(menu, tecla_de_pausa)   # ya la usa "pausa"
    assert menu.controles["disparar"] == valor_previo   # no cambia
    assert menu._aviso_conflicto is not None


def test_restaurar_valores_por_defecto(menu):
    from src.core import controles
    menu._abrir_opciones()
    _click(menu, menu._botones_controles["disparar"])
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    assert menu.controles["disparar"] == pygame.K_j

    _click(menu, menu.btn_restaurar_controles)
    assert menu.controles == controles.POR_DEFECTO


def test_guardar_persiste_el_mapa_de_controles(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _click(menu, menu._botones_controles["disparar"])
    _pulsar_tecla_en_opciones(menu, pygame.K_j)
    _click(menu, menu.btn_guardar)

    from src.core import config
    assert config.cargar_controles(ruta=ruta)["disparar"] == pygame.K_j


def _boton_idioma(menu, codigo):
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
    assert menu.btn_jugar.texto == "Play"
    assert menu.btn_salir.texto == "Quit"
    assert menu.btn_actualizar.texto == "Update"


def test_cambiar_de_idioma_rehace_la_ui_de_opciones(menu):
    menu._abrir_opciones()
    _click(menu, _boton_idioma(menu, "en"))
    textos = {e.text for e in menu.ui_manager.get_root_container().elements
              if isinstance(e, pygame_gui.elements.UILabel)}
    assert {"Music", "Effects", "Language", "Controls"} <= textos
    assert menu.btn_guardar.text == "Save"
    assert "Fire" in menu._botones_controles["disparar"].text
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
    assert menu.btn_jugar.texto == "Jugar"
    i18n.establecer_idioma("en")
    menu._menu_principal = lambda: setattr(menu, "ejecutando", False)   # una sola pasada del bucle
    menu.ejecutar()
    assert menu.btn_jugar.texto == "Play"


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
