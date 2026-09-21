"""Guardado de la campaña: `Guardado` (punto de control), su uso desde `Juego` y los diálogos del menú."""
import json

import pygame
import pytest

from src.core import settings
from src.core.engine import Juego
from src.core.guardado import Guardado
from src.ui.menu import MenuManager

DT60 = 1.0 / 60.0
P = settings.MONEDAS_PUNTOS


@pytest.fixture
def guardado(tmp_path):
    return Guardado(ruta=str(tmp_path / "partida.json"))


# --- El módulo --------------------------------------------------------------------

def test_sin_archivo_no_hay_guardado(guardado):
    assert not guardado.existe and guardado.nivel is None and guardado.puntuacion == 0


def test_guardar_un_punto_de_control_y_volver_a_leerlo(tmp_path):
    ruta = str(tmp_path / "p.json")
    Guardado(ruta=ruta).guardar_punto(3, 1234)
    otro = Guardado(ruta=ruta)
    assert otro.existe and (otro.nivel, otro.puntuacion) == (3, 1234)
    assert json.loads(open(ruta, encoding="utf-8").read()) == {"version": 1, "nivel": 3, "puntuacion": 1234}


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
    g = Guardado(ruta=str(ruta))
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
    '{"puntuacion": 5}',
])
def test_un_archivo_roto_o_raro_se_ignora_y_se_aparta(tmp_path, contenido):
    ruta = tmp_path / "p.json"
    ruta.write_text(contenido)
    g = Guardado(ruta=str(ruta))
    assert not g.existe
    assert (tmp_path / "p.json.corrupto").exists()


def test_un_archivo_de_una_version_anterior_con_campos_de_mas_se_lee(tmp_path):
    """Los guardados de las pruebas (con `"modo"`) siguen siendo válidos."""
    ruta = tmp_path / "p.json"
    ruta.write_text('{"version": 1, "modo": "campana", "nivel": 3, "puntuacion": 700}')
    g = Guardado(ruta=str(ruta))
    assert (g.nivel, g.puntuacion) == (3, 700)


def test_un_nivel_por_encima_del_maximo_de_la_campana_se_recorta(guardado):
    guardado.guardar_punto(settings.NIVEL_MAX + 3, 0)
    assert guardado.nivel == settings.NIVEL_MAX


def test_la_ruta_por_defecto_es_la_de_la_campana():
    assert Guardado(persistir=False).ruta.endswith("partida_campana.json")


# --- Desde la partida -----------------------------------------------------------------

def _juego(rm, audio, scoreboard, progresion, guardado, modo=settings.MODO_CAMPANA, **kw):
    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=modo, progresion=progresion,
                 guardado=guardado, **kw)


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
    assert (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == j._definicion().intervalo_spawn


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


# --- Elegir un nivel anterior --------------------------------------------------------------

def test_se_puede_empezar_en_un_nivel_anterior_al_guardado_sin_puntos(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True, nivel_inicial=2)
    assert (j.nivel, j.puntuacion) == (2, 0)
    assert j.monedas_cobradas == 0
    assert (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == j._definicion().intervalo_spawn


def test_elegir_el_nivel_guardado_es_lo_mismo_que_continuar(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True, nivel_inicial=4)
    assert (j.nivel, j.puntuacion) == (4, 3000)


@pytest.mark.parametrize("nivel", [0, -1, 9])
def test_un_nivel_inicial_invalido_se_ignora(rm, audio, scoreboard, progresion, guardado, nivel):
    guardado.guardar_punto(3, 700)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True, nivel_inicial=nivel)
    assert (j.nivel, j.puntuacion) == (3, 700)


def test_rejugar_un_nivel_anterior_y_superarlo_no_hace_retroceder_el_guardado(rm, audio, scoreboard, progresion, guardado):
    guardado.guardar_punto(4, 3000)
    j = _juego(rm, audio, scoreboard, progresion, guardado, continuar=True, nivel_inicial=2)
    j.puntuacion = 400
    _terminar_nivel(j)
    assert (guardado.nivel, guardado.puntuacion) == (4, 3000)


# --- El sin fin no se guarda ---------------------------------------------------------------

def test_el_sin_fin_no_escribe_ningun_guardado(rm, audio, scoreboard, progresion, guardado):
    j = _juego(rm, audio, scoreboard, progresion, None, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 700
    j._avanzar_oleada()
    j.jugador.vidas = 0
    j.actualizar(DT60)
    assert not guardado.existe


def test_cada_oleada_del_sin_fin_asegura_las_monedas_ganadas(rm, audio, scoreboard, progresion):
    """Si el juego se cierra de golpe, como mucho se pierde la oleada en curso."""
    j = _juego(rm, audio, scoreboard, progresion, None, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 5 * P
    assert progresion.monedas == 0
    j._avanzar_oleada()
    assert progresion.monedas == 5 and j.monedas_cobradas == 5
    j.puntuacion += 3 * P
    j._avanzar_oleada()
    assert progresion.monedas == 8


@pytest.mark.parametrize("como", ["volver_al_menu", "salir_del_juego"])
def test_abandonar_el_sin_fin_convierte_la_puntuacion_en_monedas(rm, audio, scoreboard, progresion, como):
    j = _juego(rm, audio, scoreboard, progresion, None, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 7 * P + 3
    getattr(j, como)()
    assert progresion.monedas == 7


def test_cerrar_la_ventana_en_pleno_sin_fin_tambien_cobra(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion, None, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 4 * P
    j.input_handler.manejar_eventos = lambda: False             # como si llegara un QUIT
    j.ejecutar()
    assert progresion.monedas == 4


# --- El menú ----------------------------------------------------------------------------------

@pytest.fixture
def menu(rm, audio, scoreboard, tmp_path):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, None,
                       Guardado(ruta=str(tmp_path / "c.json")))


def _empezar(menu, monkeypatch, eleccion=None, nivel=None, modo=settings.MODO_CAMPANA):
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda g: eleccion)
    monkeypatch.setattr(menu, "_dialogo_elegir_nivel", lambda g: nivel)
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(modo)


def test_sin_guardado_se_empieza_directamente_sin_preguntar(menu, monkeypatch):
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda *a: pytest.fail("no debe preguntar"))
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_CAMPANA)
    assert menu.resultado == "JUGAR" and menu.ejecutando is False


def test_el_sin_fin_nunca_pregunta_aunque_haya_campana_guardada(menu, monkeypatch):
    menu.guardado.guardar_punto(3, 100)
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda *a: pytest.fail("no debe preguntar"))
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_SIN_FIN)
    assert menu.resultado == "JUGAR_SIN_FIN" and menu.nivel_elegido is None


def test_sin_guardado_en_el_menu_de_la_pausa_no_se_pregunta(rm, audio, scoreboard):
    m = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    m.ejecutando, m.resultado = True, None
    m._empezar(settings.MODO_CAMPANA)
    assert m.resultado == "JUGAR"


def test_con_guardado_continuar_y_nueva_partida(menu, monkeypatch):
    menu.guardado.guardar_punto(2, 100)
    _empezar(menu, monkeypatch, "CONTINUAR")
    assert menu.resultado == "CONTINUAR" and menu.ejecutando is False and menu.nivel_elegido is None
    _empezar(menu, monkeypatch, "NUEVA")
    assert menu.resultado == "JUGAR"


def test_elegir_nivel_arranca_ese_nivel(menu, monkeypatch):
    menu.guardado.guardar_punto(4, 900)
    _empezar(menu, monkeypatch, "ELEGIR", nivel=2)
    assert menu.resultado == "CONTINUAR" and menu.nivel_elegido == 2


def test_volver_de_la_lista_de_niveles_vuelve_al_primer_dialogo(menu, monkeypatch):
    menu.guardado.guardar_punto(4, 900)
    respuestas = iter(["ELEGIR", "CONTINUAR"])
    preguntas = []
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda g: preguntas.append(1) or next(respuestas))
    monkeypatch.setattr(menu, "_dialogo_elegir_nivel", lambda g: None)          # Volver
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_CAMPANA)
    assert len(preguntas) == 2 and menu.resultado == "CONTINUAR" and menu.nivel_elegido is None


def test_cerrar_la_ventana_en_la_lista_de_niveles_sale_del_juego(menu, monkeypatch):
    menu.guardado.guardar_punto(4, 900)
    _empezar(menu, monkeypatch, "ELEGIR", nivel="SALIR")
    assert menu.resultado == "SALIR"


def test_volver_del_dialogo_deja_el_menu_como_estaba(menu, monkeypatch):
    menu.guardado.guardar_punto(2, 100)
    _empezar(menu, monkeypatch, None)
    assert menu.ejecutando is True and menu.resultado is None


def test_cerrar_la_ventana_en_el_dialogo_sale_del_juego(menu, monkeypatch):
    menu.guardado.guardar_punto(2, 100)
    _empezar(menu, monkeypatch, "SALIR")
    assert menu.resultado == "SALIR"


def test_el_boton_de_campana_del_menu_pregunta_si_hay_guardado(menu, monkeypatch):
    menu.guardado.guardar_punto(3, 100)
    preguntas = []
    monkeypatch.setattr(menu, "_dialogo_partida_guardada", lambda g: preguntas.append(g.nivel) or "CONTINUAR")
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.btn_jugar.rect.center))
    menu.ejecutando, menu.resultado = True, None
    menu._menu_principal()
    assert preguntas == [3] and menu.resultado == "CONTINUAR"


# --- Los diálogos en sí (clics reales) --------------------------------------------------------

def _dialogo(menu, funcion, evento):
    pygame.event.clear()
    pygame.event.post(evento)
    return funcion(menu.guardado)


def _clic(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)


def test_dialogo_continuar_elegir_nueva_y_volver_con_clics(menu):
    menu.guardado.guardar_punto(3, 999)
    d = menu._dialogo_partida_guardada
    assert _dialogo(menu, d, _clic((300, 280))) == "CONTINUAR"
    assert _dialogo(menu, d, _clic((300, 345))) == "ELEGIR"
    assert _dialogo(menu, d, _clic((300, 410))) == "NUEVA"
    assert _dialogo(menu, d, _clic((300, 475))) is None


def test_dialogo_escape_vuelve_y_cerrar_la_ventana_sale(menu):
    menu.guardado.guardar_punto(3, 999)
    d = menu._dialogo_partida_guardada
    assert _dialogo(menu, d, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)) is None
    assert _dialogo(menu, d, pygame.event.Event(pygame.QUIT)) == "SALIR"


def test_lista_de_niveles_del_1_al_guardado_con_clics(menu):
    menu.guardado.guardar_punto(4, 999)
    d = menu._dialogo_elegir_nivel
    rect_top = 130
    for n in (1, 2, 3, 4):
        assert _dialogo(menu, d, _clic((300, rect_top + 100 + (n - 1) * 60))) == n


def test_lista_de_niveles_volver_escape_y_cerrar(menu):
    menu.guardado.guardar_punto(3, 999)
    d = menu._dialogo_elegir_nivel
    volver = 130 + 100 + 3 * 60 + 15
    assert _dialogo(menu, d, _clic((300, volver))) is None
    assert _dialogo(menu, d, pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)) is None
    assert _dialogo(menu, d, pygame.event.Event(pygame.QUIT)) == "SALIR"


def test_la_lista_no_ofrece_niveles_por_encima_del_guardado(menu):
    menu.guardado.guardar_punto(2, 999)
    d = menu._dialogo_elegir_nivel
    # el tercer botón de la lista es "Volver", no un nivel 3
    assert _dialogo(menu, d, _clic((300, 130 + 100 + 2 * 60 + 15))) is None


def test_con_el_nivel_1_guardado_el_dialogo_no_ofrece_elegir_nivel(menu):
    menu.guardado.guardar_punto(1, 0)
    d = menu._dialogo_partida_guardada
    assert _dialogo(menu, d, _clic((300, 280))) == "CONTINUAR"
    assert _dialogo(menu, d, _clic((300, 345))) == "NUEVA"           # el segundo botón ya es "Nueva partida"


def test_los_textos_de_los_dialogos_estan_traducidos():
    from src.core import i18n
    assert i18n.t("menu.continuar_campana", n=4) == "Continuar (Nivel 4)"
    assert i18n.t("menu.nivel_guardado", n=4) == "Nivel 4 (guardado)"
    i18n.establecer_idioma("en")
    assert i18n.t("menu.elegir_nivel") == "Choose level"
    assert i18n.t("menu.nivel_guardado", n=4) == "Level 4 (saved)"
