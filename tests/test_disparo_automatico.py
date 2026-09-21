"""Disparo automático (Opciones > Controles) y la disposición de los controles como un mando."""
import pygame
import pytest

from src.core import config, controles, preferencias
from src.ui.menu import MenuManager

DT60 = 1.0 / 60.0


def _balas(juego):
    return len(juego.entity_manager.balas)


def _frames(juego, n=30):
    """Frames del bucle de la partida (eventos + actualizar), sin nada pulsado."""
    pygame.event.clear()
    for _ in range(n):
        juego.input_handler.manejar_eventos()
        if not juego.pausado:
            juego.actualizar(DT60)


# --- El comportamiento en la partida --------------------------------------------------

def test_por_defecto_la_nave_no_dispara_sola(juego):
    juego.tiempo_proximo_enemigo = float("inf")
    _frames(juego)
    assert _balas(juego) == 0


def test_con_el_disparo_automatico_la_nave_dispara_sin_pulsar_nada(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.tiempo_proximo_enemigo = float("inf")
    _frames(juego, 40)
    assert _balas(juego) >= 2                                   # 4 disparos/s durante ~0,7 s


def test_el_ritmo_del_disparo_automatico_es_el_de_la_nave(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.tiempo_proximo_enemigo = float("inf")
    disparos = 0
    for _ in range(120):                                        # 2 segundos
        antes = juego.jugador.ultimo_disparo
        juego.input_handler.manejar_eventos()
        juego.actualizar(DT60)
        disparos += juego.jugador.ultimo_disparo != antes
    assert disparos == pytest.approx(2 * juego.jugador.disparos_s, abs=1)


def test_no_dispara_en_pausa(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.pausado = True
    juego.input_handler.manejar_eventos()
    assert _balas(juego) == 0


def test_no_dispara_durante_la_transicion_de_fin_de_nivel(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.transicion_activa = True
    juego.input_handler.manejar_eventos()
    assert _balas(juego) == 0


def test_no_dispara_en_el_game_over(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.jugador.vidas = 0
    juego.actualizar(DT60)                                       # Game Over: la partida se congela
    antes = _balas(juego)
    for _ in range(30):
        juego.input_handler.manejar_eventos()
    assert _balas(juego) == antes


def test_apagarlo_a_mitad_de_partida_deja_de_disparar(juego):
    preferencias.establecer_disparo_automatico(True)
    juego.tiempo_proximo_enemigo = float("inf")
    _frames(juego, 20)
    preferencias.establecer_disparo_automatico(False)
    juego.entity_manager.balas.empty()
    _frames(juego, 20)
    assert _balas(juego) == 0


def test_pulsar_disparar_a_mano_sigue_funcionando_con_el_automatico_apagado(juego):
    juego.tiempo_juego = 1000                                    # ya pasó la espera del primer disparo
    juego.disparando = True
    juego.input_handler.manejar_eventos()
    assert _balas(juego) >= 1


# --- Configuración -------------------------------------------------------------------

def test_el_disparo_automatico_se_guarda_y_se_carga(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, disparo_automatico=True, ruta=ruta)
    assert config.cargar_disparo_automatico(ruta=ruta) is True
    config.guardar_configuracion(0.3, 0.7, disparo_automatico=False, ruta=ruta)
    assert config.cargar_disparo_automatico(ruta=ruta) is False


def test_por_defecto_esta_apagado(tmp_path):
    assert config.cargar_disparo_automatico(ruta=str(tmp_path / "no_existe.ini")) is False
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[PANTALLA]\ntemblor = no\n")
    assert config.cargar_disparo_automatico(ruta=str(ruta)) is False
    ruta.write_text("[JUEGO]\ndisparo_automatico = quiza\n")
    assert config.cargar_disparo_automatico(ruta=str(ruta)) is False
    ruta.write_text("esto no es un ini valido [[[")
    assert config.cargar_disparo_automatico(ruta=str(ruta)) is False


def test_convive_con_las_demas_secciones(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, controles.POR_DEFECTO, "es", temblor=False, cifras_dano=False,
                                 disparo_automatico=True, ruta=ruta)
    assert config.cargar_temblor(ruta=ruta) is False and config.cargar_cifras_dano(ruta=ruta) is False
    assert config.cargar_disparo_automatico(ruta=ruta) is True
    assert config.cargar_configuracion(ruta=ruta) == (0.3, 0.7)


# --- Opciones ----------------------------------------------------------------------------

@pytest.fixture
def menu(rm, audio, scoreboard):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)


def _pulsar(menu, boton):
    centro = boton.rect.center
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(tipo, button=1, pos=centro))
    for _ in range(5):
        menu._menu_opciones(0.016)


def test_el_interruptor_esta_en_controles_y_apagado_por_defecto(menu):
    menu._abrir_opciones()
    assert menu._pestana == "controles"
    assert menu.btn_disparo_auto in menu._elementos_pestana["controles"]
    assert menu.btn_disparo_auto.text == "Disparo automático: No" and not menu.btn_disparo_auto.is_selected


def test_pulsarlo_lo_enciende_y_apaga_al_instante(menu):
    menu._abrir_opciones()
    _pulsar(menu, menu.btn_disparo_auto)
    assert preferencias.disparo_automatico() is True
    assert menu.btn_disparo_auto.text == "Disparo automático: Sí" and menu.btn_disparo_auto.is_selected
    _pulsar(menu, menu.btn_disparo_auto)
    assert preferencias.disparo_automatico() is False


def test_volver_descarta_el_cambio(menu):
    menu._abrir_opciones()
    _pulsar(menu, menu.btn_disparo_auto)
    _pulsar(menu, menu.btn_volver)
    assert preferencias.disparo_automatico() is False


def test_guardar_lo_confirma_en_la_sesion_y_en_disco(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _pulsar(menu, menu.btn_disparo_auto)
    _pulsar(menu, menu.btn_guardar)
    assert preferencias.disparo_automatico() is True
    assert config.cargar_disparo_automatico(ruta=ruta) is True


def test_guardar_sin_tocarlo_conserva_lo_que_habia(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    preferencias.establecer_disparo_automatico(True)
    menu._abrir_opciones()
    _pulsar(menu, menu.btn_guardar)
    assert config.cargar_disparo_automatico(ruta=ruta) is True


def test_otro_menu_ve_el_estado_real(menu, rm, audio, scoreboard):
    pausa = MenuManager(menu.pantalla, rm, audio, scoreboard)
    pausa._abrir_opciones()
    preferencias.establecer_disparo_automatico(True)             # cambiado desde otra parte
    menu._abrir_opciones()
    assert menu.btn_disparo_auto.is_selected


# --- Los controles dispuestos como un mando ----------------------------------------------------

@pytest.fixture
def botones(menu):
    menu._abrir_opciones()
    return {accion: menu._botones_controles[accion].rect for accion in controles.ACCIONES}


def test_arriba_y_abajo_van_solos_y_centrados(botones):
    for accion in ("arriba", "abajo"):
        assert botones[accion].centerx == 300


def test_izquierda_y_derecha_comparten_fila_a_los_lados(botones):
    izq, der = botones["izquierda"], botones["derecha"]
    assert izq.y == der.y and izq.centerx < 300 < der.centerx
    assert izq.centerx + der.centerx == 600                       # simétricos respecto al centro


def test_el_orden_de_arriba_abajo_es_arriba_medio_abajo_y_luego_disparar_y_pausa(botones):
    assert botones["arriba"].y < botones["izquierda"].y < botones["abajo"].y < botones["disparar"].y
    assert botones["disparar"].y == botones["pausa"].y


def test_las_filas_no_se_solapan_ni_se_salen_de_la_pantalla(botones, menu):
    rects = list(botones.values()) + [menu.btn_disparo_auto.rect, menu.btn_restaurar_controles.rect]
    for i, a in enumerate(rects):
        assert 0 <= a.left and a.right <= 600 and a.bottom < menu.btn_guardar.rect.top
        assert not any(a.colliderect(b) for b in rects[i + 1:])


def test_las_cuatro_direcciones_forman_una_cruz(botones):
    cruz = [botones[a] for a in ("arriba", "izquierda", "derecha", "abajo")]
    assert cruz[0].bottom <= cruz[1].top and cruz[1].bottom <= cruz[3].top     # arriba / medio / abajo


def test_el_aviso_de_tecla_repetida_no_pisa_ningun_boton(botones, menu):
    from src.ui import menu as modulo
    y_aviso = 458
    assert all(not (r.top <= y_aviso <= r.bottom) for r in list(botones.values()) + [menu.btn_disparo_auto.rect])


def test_cada_boton_de_control_sigue_reasignando_su_accion(menu):
    menu._abrir_opciones()
    for accion in controles.ACCIONES:
        assert menu._acciones_por_boton[menu._botones_controles[accion]] == accion
