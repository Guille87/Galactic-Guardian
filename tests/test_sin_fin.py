"""Modo sin fin: curva (src/core/sin_fin.py), partida (Juego) y sus rankings."""
import math

import pygame
import pytest

from src.core import config, settings, sin_fin
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe
from src.ui.scoreboard import SistemaClasificacion

DT60 = 1.0 / 60.0


# --- Curva -------------------------------------------------------------------

def test_solo_cada_n_oleadas_es_de_jefe():
    jefes = [n for n in range(1, 31) if sin_fin.es_oleada_de_jefe(n)]
    assert jefes == list(range(sin_fin.JEFE_CADA, 31, sin_fin.JEFE_CADA))


def test_el_intervalo_baja_hasta_el_suelo_y_ahi_se_queda():
    minimos = [sin_fin.intervalo_spawn(n)[0] for n in range(1, 40)]
    maximos = [sin_fin.intervalo_spawn(n)[1] for n in range(1, 40)]
    assert minimos == sorted(minimos, reverse=True) and maximos == sorted(maximos, reverse=True)
    assert sin_fin.intervalo_spawn(1) == sin_fin.INTERVALO_INICIAL
    assert sin_fin.intervalo_spawn(39) == sin_fin.INTERVALO_MIN
    assert sin_fin.intervalo_spawn(400) == sin_fin.INTERVALO_MIN


@pytest.mark.parametrize("oleada", range(1, 16))
def test_definicion_de_oleada_coherente(oleada):
    d = sin_fin.definicion_oleada(oleada)
    assert [f.desde_ms for f in d.fases] == [0]
    assert all(issubclass(e, EnemigoBase) for e in d.fases[0].enemigos)
    assert d.intervalo_spawn == sin_fin.intervalo_spawn(oleada)
    assert issubclass(d.jefe, Jefe)
    assert d.musica in config.MUSICA and d.musica_jefe in config.MUSICA
    if sin_fin.es_oleada_de_jefe(oleada):
        assert d.tiempo_jefe_ms == 0
    else:
        assert d.tiempo_jefe_ms == math.inf


def test_el_reparto_de_enemigos_se_diversifica_con_las_oleadas():
    assert sin_fin.enemigos(1) == (EnemigoTipo1,)
    assert len(set(sin_fin.enemigos(6))) == 3


def test_oleada_cero_o_negativa_se_trata_como_la_primera():
    assert sin_fin.definicion_oleada(0) is sin_fin.definicion_oleada(1)


# --- Partida -----------------------------------------------------------------

@pytest.fixture
def sin_fin_juego(rm, audio, scoreboard):
    from src.core.engine import Juego

    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=settings.MODO_SIN_FIN)


def _jefe_de(juego, rm):
    img = rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)
    return Jefe(img, 200, 200, 600, 800, juego.nivel, juego.jugador)


def test_arranca_en_la_oleada_1_con_su_cadencia(sin_fin_juego):
    j = sin_fin_juego
    assert j.modo == settings.MODO_SIN_FIN and j.nivel == 1
    assert (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == sin_fin.intervalo_spawn(1)


def test_la_campana_sigue_siendo_el_modo_por_defecto(juego):
    assert juego.modo == settings.MODO_CAMPANA


def test_la_oleada_avanza_por_tiempo_sin_tocar_lo_que_hay_en_pantalla(sin_fin_juego, rm):
    j = sin_fin_juego
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)
    j.entity_manager.agregar_enemigo(enemigo)
    j.tiempo_juego = sin_fin.OLEADA_MS + 1
    j.tiempo_proximo_enemigo = math.inf          # que este frame no genere nada más
    j._gestionar_generacion_enemigos()
    assert j.nivel == 2
    assert j.inicio_juego == j.tiempo_juego      # el reloj de la oleada vuelve a 0
    assert enemigo in j.entity_manager.enemigos
    assert (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == sin_fin.intervalo_spawn(2)


def test_no_avanza_antes_de_tiempo(sin_fin_juego):
    j = sin_fin_juego
    j.tiempo_juego = sin_fin.OLEADA_MS - 1
    j.tiempo_proximo_enemigo = math.inf
    j._gestionar_generacion_enemigos()
    assert j.nivel == 1


def test_la_oleada_de_jefe_no_acaba_por_tiempo(sin_fin_juego):
    j = sin_fin_juego
    j.nivel = sin_fin.JEFE_CADA
    j.tiempo_juego = sin_fin.OLEADA_MS * 10
    j.tiempo_proximo_enemigo = math.inf
    j._gestionar_generacion_enemigos()
    assert j.nivel == sin_fin.JEFE_CADA


def test_en_la_oleada_de_jefe_sale_el_jefe_y_no_otros_enemigos(sin_fin_juego, audio):
    j = sin_fin_juego
    j.nivel = sin_fin.JEFE_CADA
    j.inicio_juego = j.tiempo_juego = 100_000
    audio.reproducir_musica(j._definicion().musica)

    generados = []
    for paso in range(0, sin_fin.ESPERA_JEFE_MS + 3000, 200):
        j.tiempo_juego = 100_000 + paso
        j.tiempo_proximo_enemigo = 0
        j._gestionar_generacion_enemigos()
        generados = list(j.entity_manager.enemigos)
        if j.jefe:
            break
    assert isinstance(j.jefe, Jefe)
    assert generados == [j.jefe]                                   # nada más durante la espera ni con el jefe
    assert audio.pista_actual == j._definicion().musica_jefe


def test_matar_al_jefe_pasa_a_la_siguiente_oleada_sin_transicion(sin_fin_juego, rm, audio):
    j = sin_fin_juego
    j.nivel = sin_fin.JEFE_CADA
    j.tiempo_juego = 50_000
    jefe = j.jefe = _jefe_de(j, rm)
    audio.reproducir_musica(j._definicion().musica_jefe)
    j.wave_manager.jefe_generado = True
    puntos = j.puntuacion

    j.al_eliminar_enemigo(jefe)

    assert j.nivel == sin_fin.JEFE_CADA + 1
    assert j.puntuacion > puntos
    assert j.jefe is None
    assert j.wave_manager.jefe_generado is False                    # el siguiente jefe podrá salir
    assert (j.transicion_activa, j.pendiente_reinicio, j.jefe_derrotado) == (False, False, False)
    assert not (j.estado_nivel_completado or j.estado_victoria_final or j.mostrando_seleccion_nivel)
    assert audio.pista_actual == j._definicion().musica              # vuelve la música normal
    assert j.inicio_juego == j.tiempo_juego


def test_matar_al_jefe_se_lleva_sus_balas(sin_fin_juego, rm):
    from src.entities.bullet_enemy import BalaEnemigo

    j = sin_fin_juego
    j.nivel = sin_fin.JEFE_CADA
    imagen = rm.get_image_scaled("bala_enemigo", BalaEnemigo.TAMANO)
    j.entity_manager.balas_enemigo.add(BalaEnemigo(imagen, 100, 100, 0, 1, 1, 5))
    jefe = j.jefe = _jefe_de(j, rm)
    j.al_eliminar_enemigo(jefe)
    assert len(j.entity_manager.balas_enemigo) == 0


def test_los_puntos_se_multiplican_por_la_oleada(sin_fin_juego, rm):
    j = sin_fin_juego
    j.nivel = 4
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 4)
    j.al_eliminar_enemigo(enemigo)
    assert j.puntuacion == enemigo.valor_puntuacion * 4


def test_reintentar_vuelve_a_la_oleada_1_desde_cero(sin_fin_juego):
    j = sin_fin_juego
    j.nivel = 7
    j.puntuacion = 999
    j.reiniciar_juego()
    assert j.nivel == 1 and j.puntuacion == 0
    assert j.inicio_juego == 0 and j.tiempo_juego == 0
    assert (j.MIN_TIEMPO_GENERACION, j.MAX_TIEMPO_GENERACION) == sin_fin.intervalo_spawn(1)


def test_la_campana_reintenta_el_mismo_nivel(juego):
    """`reiniciar_juego` del sin fin no cambia lo de la campaña."""
    juego.nivel = 3
    juego.reiniciar_juego()
    assert juego.nivel == 3


def test_muchos_frames_sin_crash_y_con_hud_de_oleada(sin_fin_juego):
    j = sin_fin_juego
    j.jugador.vidas = 999
    for _ in range(600):
        j.actualizar(DT60)
        j.dibujar()


def test_dibuja_game_over_con_oleada_y_pausa(sin_fin_juego):
    j = sin_fin_juego
    j.nivel = 6
    j.estado_game_over = True
    j.dibujar()
    j.estado_game_over = False
    j.pausar_juego()
    j.dibujar()


def test_game_over_registra_la_oleada_en_el_ranking_del_modo(sin_fin_juego):
    j = sin_fin_juego
    j.nivel = 8
    j.puntuacion = 1234
    j._pedir_nombre_o_mostrar("game_over")
    assert j.pidiendo_nombre
    j.nombre_entrada = "Ana"
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
    j.input_handler.manejar_eventos()
    assert j.clasificacion.puntuaciones["Ana"] == {"puntos": 1234, "nivel": 8}
    assert j.estado_game_over


# --- Rankings separados ------------------------------------------------------

def test_cada_ranking_usa_su_propio_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr("src.core.paths.dir_datos_usuario", lambda: str(tmp_path))
    campana = SistemaClasificacion()
    endless = SistemaClasificacion(nombre_archivo="puntuaciones_sin_fin.json")
    campana.agregar_puntuacion("Ana", 100, nivel=2)
    endless.agregar_puntuacion("Beto", 900, nivel=7)

    assert campana.ruta_archivo != endless.ruta_archivo
    assert SistemaClasificacion().obtener_puntuaciones_top() == [("Ana", 100, 2)]
    assert SistemaClasificacion(nombre_archivo="puntuaciones_sin_fin.json").obtener_puntuaciones_top() == [("Beto", 900, 7)]
