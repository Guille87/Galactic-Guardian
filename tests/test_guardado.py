"""Guardado de partida: `Guardado` (punto de control), su uso desde `Juego` y el diálogo del menú."""
import json

import pygame
import pytest

from src.core import settings
from src.core.engine import Juego
from src.core.guardado import Guardado
from src.entities.enemies import Jefe
from src.ui.menu import MenuManager

DT60 = 1.0 / 60.0
P = settings.MONEDAS_PUNTOS


@pytest.fixture
def guardado(tmp_path):
    return Guardado(settings.MODO_CAMPANA, ruta=str(tmp_path / "partida.json"))


# --- El módulo --------------------------------------------------------------------

def test_sin_archivo_no_hay_guardado(guardado):
    assert not guardado.existe and guardado.nivel is None and guardado.puntuacion == 0


def test_guardar_un_punto_de_control_y_volver_a_leerlo(tmp_path):
    ruta = str(tmp_path / "p.json")
    Guardado(settings.MODO_CAMPANA, ruta=ruta).guardar_punto(3, 1234)
    otro = Guardado(settings.MODO_CAMPANA, ruta=ruta)
    assert otro.existe and (otro.nivel, otro.puntuacion) == (3, 1234)
    assert json.loads(open(ruta, encoding="utf-8").read()) == {
        "version": 1, "modo": settings.MODO_CAMPANA, "nivel": 3, "puntuacion": 1234}


def test_el_guardado_nunca_retrocede(guardado):
    guardado.guardar_punto(4, 5000)
    assert guardado.guardar_punto(2, 100) is False              # rejugar un nivel ya superado
    assert (guardado.nivel, guardado.puntuacion) == (4, 5000)
    assert guardado.guardar_punto(5, 6000) is True
    assert guardado.nivel == 5


def test_un_nivel_igual_actualiza_la_puntuacion(guardado):
    guardado.guardar_punto(3, 100)
    guardado.guardar_punto(3, 900)
    assert guardado.puntuacion == 900


def test_borrar_elimina_el_archivo_y_deja_de_existir(tmp_path):
    ruta = tmp_path / "p.json"
    g = Guardado(settings.MODO_CAMPANA, ruta=str(ruta))
    g.guardar_punto(2, 10)
    assert ruta.exists()
    g.borrar()
    assert not g.existe and not ruta.exists()
    g.borrar()                                                  # borrar sin archivo no falla


def test_borrar_permite_empezar_de_nuevo_desde_un_nivel_bajo(guardado):
    guardado.guardar_punto(4, 5000)
    guardado.borrar()
    assert guardado.guardar_punto(2, 100) is True and guardado.nivel == 2


def test_sin_persistir_no_se_toca_el_disco(tmp_path):
    ruta = tmp_path / "p.json"
    g = Guardado(ruta=str(ruta), persistir=False)
    g.guardar_punto(3, 10)
    g.borrar()
    assert g.nivel is None and not ruta.exists()


def test_la_escritura_es_atomica_y_no_deja_temporales(tmp_path):
    g = Guardado(ruta=str(tmp_path / "p.json"))
    g.guardar_punto(2, 10)
    assert not (tmp_path / "p.json.tmp").exists()


@pytest.mark.parametrize("contenido", [
    "esto no es json {{{",
    "[1, 2, 3]",
    '{"nivel": "tres", "puntuacion": 5}',
    '{"nivel": true, "puntuacion": 5}',
    '{"nivel": 0, "puntuacion": 5}',
    '{"nivel": 99, "puntuacion": 5}',                            # más niveles de los que tiene la campaña
    '{"nivel": 2, "puntuacion": -5}',
    '{"nivel": 2, "puntuacion": 1.5}',
    '{"nivel": 2, "puntuacion": 5, "modo": "sin_fin"}',          # de otro modo
    '{"puntuacion": 5}',
])
def test_un_archivo_roto_o_raro_se_ignora_y_se_aparta(tmp_path, contenido):
    ruta = tmp_path / "p.json"
    ruta.write_text(contenido)
    g = Guardado(settings.MODO_CAMPANA, ruta=str(ruta))
    assert not g.existe
    assert (tmp_path / "p.json.corrupto").exists()


def test_la_campana_y_el_sin_fin_tienen_cada_uno_su_archivo_y_topes(tmp_path):
    camp = Guardado(settings.MODO_CAMPANA, ruta=str(tmp_path / "c.json"))
    fin = Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))
    camp.guardar_punto(4, 1)
    fin.guardar_punto(37, 2)                                     # las oleadas no tienen techo
    assert Guardado(settings.MODO_CAMPANA, ruta=str(tmp_path / "c.json")).nivel == 4
    assert Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json")).nivel == 37
    assert Guardado(settings.MODO_CAMPANA).ruta != Guardado(settings.MODO_SIN_FIN).ruta


def test_un_nivel_por_encima_del_maximo_de_la_campana_se_recorta(guardado):
    guardado.guardar_punto(settings.NIVEL_MAX + 3, 0)
    assert guardado.nivel == settings.NIVEL_MAX


# --- Desde la partida -----------------------------------------------------------------

def _juego(rm, audio, scoreboard, progresion, guardado, modo=settings.MODO_CAMPANA, continuar=False):
    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=modo, progresion=progresion,
                 guardado=guardado, continuar=continuar)


def _terminar_nivel(j):
    j.transicion_activa = True
    j._finalizar_transicion_fin_de_nivel()


def test_terminar_un_nivel_guarda_el_siguiente_con_la_puntuacion(rm, audio, scoreboard, progresion, guardado):
    j = _juego(rm, audio, scoreboard, progresion, guardado)
    j.nivel, j.puntuacion = 2, 800
    _terminar_nivel(j)
    assert (guardado.nivel, guardado.puntuacion) == (3, 800)


def test_el_guardado_ya_cuenta_aunque_se_cierre_en_la_pantalla_de_resumen(rm, audio, scoreboard, progresion, guardado):
    j = _juego(rm, audio, scoreboard, progresion, guardado)
    j.nivel, j.puntuacion = 1, 300
    _terminar_nivel(j)
    assert j.estado_nivel_completado                             # aún sin pulsar "Continuar"
    assert Guardado(ruta=guardado.ruta).nivel == 2               # y ya está en disco


def test_completar_la_campana_borra_el_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(settings.NIVEL_MAX, 5000)
    j = _juego(rm, audio, scoreboard, progresion, guardado)
    j.nivel = settings.NIVEL_MAX
    _terminar_nivel(j)
    assert not guardado.existe


def test_el_game_over_conserva_el_ultimo_nivel_superado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    j.jugador.vidas = 0
    j.actualizar(DT60)                                           # -> Game Over
    assert guardado.existe and (guardado.nivel, guardado.puntuacion) == (4, 3000)


def test_reintentar_o_salir_al_menu_no_tocan_el_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    j.reiniciar_juego()
    j.volver_al_menu()
    j.salir_del_juego()
    assert (guardado.nivel, guardado.puntuacion) == (4, 3000)


def test_rejugar_un_nivel_del_selector_no_hace_retroceder_el_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    j.reiniciar_juego(nivel_forzado=1)
    j.puntuacion = 50
    _terminar_nivel(j)                                           # supera el nivel 1: guardaría el 2
    assert (guardado.nivel, guardado.puntuacion) == (4, 3000)


def test_continuar_arranca_en_el_nivel_y_con_la_puntuacion_guardados(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 2500)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    assert (j.nivel, j.puntuacion) == (4, 2500)
    assert j._definicion() is not None and (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == \
        j._definicion().intervalo_spawn


def test_continuar_da_vidas_y_salud_de_partida_nueva_y_combo_a_cero(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 2500)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    assert j.jugador.vidas == 3 and j.jugador.salud == j.jugador.salud_maxima and j.combo.racha == 0


def test_sin_continuar_se_empieza_de_cero_aunque_haya_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 2500)
    j = _juego(rm, audio, scoreboard, progresion, guardado)
    assert (j.nivel, j.puntuacion) == (1, 0) and guardado.existe


def test_continuar_sin_guardado_es_una_partida_normal(rm, audio, scoreboard, progresion, guardado):
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    assert (j.nivel, j.puntuacion) == (1, 0)


def test_continuar_no_vuelve_a_cobrar_las_monedas_de_la_puntuacion_guardada(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(3, 10 * P)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    antes = progresion.monedas
    j._cobrar_monedas()
    assert progresion.monedas == antes                           # esos puntos ya se cobraron en su día
    j.puntuacion += 2 * P
    j._cobrar_monedas()
    assert progresion.monedas == antes + 2


def test_jugar_desde_el_guardado_y_superar_el_nivel_avanza_el_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(2, 1000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True)
    j.puntuacion += 500
    _terminar_nivel(j)
    assert (guardado.nivel, guardado.puntuacion) == (3, 1500)


def test_sin_guardado_asociado_el_juego_funciona_como_siempre(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion, None)
    _terminar_nivel(j)
    j.jugador.vidas = 0
    j.actualizar(DT60)


# --- Sin fin -----------------------------------------------------------------------------

def test_cada_oleada_nueva_guarda_su_punto_de_control(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))
    j = _juego(rm, audio, scoreboard, progresion, g, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 700
    j._avanzar_oleada()
    assert (g.nivel, g.puntuacion) == (2, 700)
    j.puntuacion = 1900
    j._avanzar_oleada()
    assert (g.nivel, g.puntuacion) == (3, 1900)


def test_derrotar_a_un_jefe_del_sin_fin_tambien_guarda(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))
    j = _juego(rm, audio, scoreboard, progresion, g, modo=settings.MODO_SIN_FIN)
    j.nivel = 5
    j.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 5, j.jugador)
    j.al_eliminar_enemigo(jefe)
    assert g.nivel == 6


def test_continuar_el_sin_fin_arranca_en_esa_oleada(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))
    g.guardar_punto(12, 4000)
    j = _juego(rm, audio, scoreboard, progresion, g, modo=settings.MODO_SIN_FIN, continuar=True)
    assert (j.nivel, j.puntuacion) == (12, 4000) and j.inicio_juego == 0
    for _ in range(120):
        j.actualizar(DT60)
        j.dibujar()


def test_el_game_over_del_sin_fin_tambien_conserva_la_oleada(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))
    j = _juego(rm, audio, scoreboard, progresion, g, modo=settings.MODO_SIN_FIN)
    j._avanzar_oleada()
    j.jugador.vidas = 0
    j.actualizar(DT60)
    assert g.nivel == 2


# --- El menú ----------------------------------------------------------------------------------

@pytest.fixture
def menu(rm, audio, scoreboard, tmp_path):
    guardados = {settings.MODO_CAMPANA: Guardado(settings.MODO_CAMPANA, ruta=str(tmp_path / "c.json")),
                 settings.MODO_SIN_FIN: Guardado(settings.MODO_SIN_FIN, ruta=str(tmp_path / "s.json"))}
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, None, guardados)


def _elegir(menu, eleccion, modo=settings.MODO_CAMPANA, monkeypatch=None):
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda m, g: eleccion)
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(modo)


def test_sin_guardado_se_empieza_directamente_sin_preguntar(menu, monkeypatch):
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda *a: pytest.fail("no debe preguntar"))
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_CAMPANA)
    assert menu.resultado == "JUGAR" and menu.ejecutando is False
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_SIN_FIN)
    assert menu.resultado == "JUGAR_SIN_FIN"


def test_sin_guardados_en_el_menu_de_la_pausa_no_se_pregunta(rm, audio, scoreboard):
    m = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    m.ejecutando, m.resultado = True, None
    m._empezar(settings.MODO_CAMPANA)
    assert m.resultado == "JUGAR"


@pytest.mark.parametrize("modo, continuar, nueva", [
    (settings.MODO_CAMPANA, "CONTINUAR", "JUGAR"),
    (settings.MODO_SIN_FIN, "CONTINUAR_SIN_FIN", "JUGAR_SIN_FIN"),
])
def test_con_guardado_se_pregunta_y_se_respeta_la_eleccion(menu, monkeypatch, modo, continuar, nueva):
    menu.guardados[modo].guardar_punto(2, 100)
    _elegir(menu, "CONTINUAR", modo, monkeypatch)
    assert menu.resultado == continuar and menu.ejecutando is False
    _elegir(menu, "NUEVA", modo, monkeypatch)
    assert menu.resultado == nueva


def test_volver_del_dialogo_deja_el_menu_como_estaba(menu, monkeypatch):
    menu.guardados[settings.MODO_CAMPANA].guardar_punto(2, 100)
    _elegir(menu, None, settings.MODO_CAMPANA, monkeypatch)
    assert menu.ejecutando is True and menu.resultado is None


def test_cerrar_la_ventana_en_el_dialogo_sale_del_juego(menu, monkeypatch):
    menu.guardados[settings.MODO_CAMPANA].guardar_punto(2, 100)
    _elegir(menu, "SALIR", settings.MODO_CAMPANA, monkeypatch)
    assert menu.resultado == "SALIR"


def test_el_boton_de_campana_del_menu_pregunta_si_hay_guardado(menu, monkeypatch):
    menu.guardados[settings.MODO_CAMPANA].guardar_punto(3, 100)
    preguntas = []
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda m, g: preguntas.append((m, g.nivel)) or "CONTINUAR")
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_jugar.rect.center))
    menu.ejecutando, menu.resultado = True, None
    menu._menu_principal()
    assert preguntas == [(settings.MODO_CAMPANA, 3)] and menu.resultado == "CONTINUAR"


# --- El diálogo en sí (clics reales) --------------------------------------------------------

def _dialogo(menu, evento, modo=settings.MODO_CAMPANA):
    pygame.event.clear()
    pygame.event.post(evento)
    return menu._dialogo_partida_guardada(modo, menu.guardados[modo])


def _clic(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def test_dialogo_continuar_nueva_y_volver_con_clics(menu):
    menu.guardados[settings.MODO_CAMPANA].guardar_punto(3, 999)
    assert _dialogo(menu, _clic((300, 300))) == "CONTINUAR"
    assert _dialogo(menu, _clic((300, 365))) == "NUEVA"
    assert _dialogo(menu, _clic((300, 430))) is None


def test_dialogo_escape_vuelve_y_cerrar_la_ventana_sale(menu):
    menu.guardados[settings.MODO_CAMPANA].guardar_punto(3, 999)
    assert _dialogo(menu, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)) is None
    assert _dialogo(menu, pygame.event.Event(pygame.QUIT)) == "SALIR"


def test_los_textos_del_dialogo_dicen_nivel_y_oleada(menu):
    from src.core import i18n
    assert i18n.t("menu.continuar_campana", n=4) == "Continuar (Nivel 4)"
    assert i18n.t("menu.continuar_sin_fin", n=12) == "Continuar (Oleada 12)"
    i18n.establecer_idioma("en")
    assert i18n.t("menu.continuar_sin_fin", n=12) == "Continue (Wave 12)"
