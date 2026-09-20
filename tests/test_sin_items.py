"""Sin ítems en la partida: nada cae, la curación es por nivel/oleada y "Botín II" sustituye a "Suerte"."""
import importlib.util
import math

import pygame
import pytest

from src.core import config, mejoras, settings, sin_fin
from src.core.engine import Juego
from src.core.mejoras import calcular_bonus
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe
from src.entities.player import Jugador

DT60 = 1.0 / 60.0


def _enemigo(rm):
    return EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)


# --- No queda nada de los ítems ----------------------------------------------

def test_el_modulo_de_items_ya_no_existe():
    assert importlib.util.find_spec("src.entities.items") is None


def test_no_hay_grupo_de_items_ni_sonido_de_recogida(juego, audio):
    assert not hasattr(juego.entity_manager, "items")
    assert "item" not in audio.efectos and "item_take" not in config.SONIDOS


def test_los_enemigos_y_la_nave_ya_no_tienen_la_maquinaria_de_loot(juego, rm):
    for nombre in ("die", "generate_item", "_loot_util", "CANDIDATOS_LOOT"):
        assert not hasattr(EnemigoBase, nombre), nombre
    for nombre in ("mejorar_danio", "mejorar_velocidad", "mejorar_cadencia"):
        assert not hasattr(juego.jugador, nombre), nombre


def test_destruir_muchos_enemigos_no_suelta_nada(juego, rm):
    for _ in range(200):
        juego.al_eliminar_enemigo(_enemigo(rm))
    juego.actualizar(DT60)
    assert juego.puntuacion > 0
    assert not hasattr(juego.entity_manager, "items")
    assert len(juego.entity_manager.efectos) == 0                # ni explosiones sueltas por el camino


def test_el_jefe_tampoco_suelta_nada(juego, rm):
    juego.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert not hasattr(juego.entity_manager, "items")


def test_las_imagenes_de_los_items_siguen_cargadas_para_el_arbol(rm):
    """Los iconos se conservan: el árbol de mejoras puede reutilizarlos."""
    for nombre in ("curacion", "potenciador_danio", "potenciador_cadencia", "potenciador_velocidad"):
        assert rm.get_image(nombre) is not None


# --- Curación en el sin fin --------------------------------------------------

@pytest.fixture
def sin_fin_juego(rm, audio, scoreboard):
    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=settings.MODO_SIN_FIN)


def test_cada_oleada_nueva_cura_una_parte_de_la_salud(sin_fin_juego):
    j = sin_fin_juego
    j.jugador.salud = 1
    j.tiempo_juego = sin_fin.OLEADA_MS + 1
    j.tiempo_proximo_enemigo = math.inf
    j._gestionar_generacion_enemigos()
    assert j.nivel == 2
    esperado = 1 + math.ceil(settings.SIN_FIN_CURACION_OLEADA * j.jugador.salud_maxima)
    assert j.jugador.salud == esperado and j.jugador.salud < j.jugador.salud_maxima


def test_la_curacion_de_oleada_no_pasa_de_la_salud_maxima(sin_fin_juego):
    j = sin_fin_juego
    j.jugador.salud = j.jugador.salud_maxima
    j._avanzar_oleada()
    assert j.jugador.salud == j.jugador.salud_maxima


def test_derrotar_al_jefe_del_sin_fin_deja_la_salud_completa(sin_fin_juego, rm):
    j = sin_fin_juego
    j.nivel = sin_fin.JEFE_CADA
    j.jugador.salud = 1
    j.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, j.nivel, j.jugador)
    j.al_eliminar_enemigo(jefe)
    assert j.nivel == sin_fin.JEFE_CADA + 1
    assert j.jugador.salud == j.jugador.salud_maxima


def test_la_curacion_escala_con_la_salud_maxima(rm, audio, scoreboard, progresion):
    progresion.ingresar(10_000)
    for id_ in ("defensa_1", "defensa_2", "defensa_3"):
        progresion.comprar(id_)
    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=settings.MODO_SIN_FIN, progresion=progresion)
    maxima = j.jugador.salud_maxima
    assert maxima > Jugador.CONFIG["salud_max"]                   # con la mejora, más que la base
    j.jugador.salud = 1
    j._avanzar_oleada()
    assert j.jugador.salud == 1 + math.ceil(settings.SIN_FIN_CURACION_OLEADA * maxima)


def test_la_campana_sigue_curando_al_pasar_de_nivel(juego):
    juego.jugador.salud = 1
    juego.jefe_derrotado = True
    juego.reiniciar_juego()
    assert juego.jugador.salud == juego.jugador.salud_maxima


# --- "Botín II" sustituye a "Suerte" -----------------------------------------

def test_botin_ii_es_la_ultima_de_utilidad_y_no_queda_rastro_de_suerte():
    m = mejoras.POR_ID["utilidad_5"]
    assert m.efecto == {"monedas_pct": 0.25} and m.requiere == "utilidad_4"
    assert not hasattr(mejoras.Bonus(), "probabilidad_item")


def test_botin_i_y_ii_suman_un_50_por_ciento(rm, audio, scoreboard, progresion):
    progresion.ingresar(10_000)
    for id_ in ("utilidad_1", "utilidad_2", "utilidad_3", "utilidad_4", "utilidad_5"):
        assert progresion.comprar(id_) == "ok"
    progresion.monedas = 0
    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm, progresion=progresion)
    j.puntuacion = 20 * settings.MONEDAS_PUNTOS
    j._cobrar_monedas()
    assert progresion.monedas == 30                               # 20 * 1,5


def test_un_guardado_con_la_antigua_suerte_recupera_lo_que_costo(tmp_path):
    """Con el árbol nuevo, lo comprado en el antiguo se devuelve entero (no se pierde nada)."""
    import json
    from src.core.progresion import Progresion

    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps({"version": 1, "monedas": 5, "mejoras": ["utilidad_1", "utilidad_2", "utilidad_3"]}))
    p = Progresion(ruta=str(ruta))
    assert p.compradas == set() and p.monedas == 5 + 100 + 200 + 300
    assert calcular_bonus(p.compradas).monedas_pct == 0
