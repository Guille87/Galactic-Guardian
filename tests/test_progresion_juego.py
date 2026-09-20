"""La progresión dentro de la partida: bonus de la nave, botín, combo, escudo y cobro de monedas."""
import json

import pygame
import pytest

from src.core import mejoras, settings
from src.core.combo import Combo
from src.core.engine import Juego
from src.core.mejoras import Bonus
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe
from src.entities.player import Jugador

DT60 = 1.0 / 60.0


def _comprar(prog, *ids):
    prog.ingresar(100_000)
    for id_ in ids:
        assert prog.comprar(id_) == "ok", id_


def _juego(rm, audio, scoreboard, prog, modo=settings.MODO_CAMPANA):
    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=modo, progresion=prog)


def _enemigo(rm):
    return EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)


# --- La nave arranca con los bonus -------------------------------------------

def test_sin_mejoras_la_nave_arranca_como_siempre(juego):
    j = juego.jugador
    assert (j.vidas, j.salud_maxima, j.velocidad, j.danio, j.cadencia_disparo, j.tipo_disparo) == (3, 50, 4, 10, 350, "simple")


def test_las_mejoras_suben_los_valores_de_arranque(rm, audio, scoreboard, progresion):
    _comprar(progresion, "ataque_1", "ataque_2", "ataque_3", "ataque_4",
             "defensa_1", "defensa_2", "defensa_3", "utilidad_1")
    j = _juego(rm, audio, scoreboard, progresion).jugador
    assert j.vidas == 4
    assert j.salud_maxima == 70 and j.salud == 70
    assert j.danio == 20 and j.cadencia_disparo == 250 and j.tipo_disparo == "doble"
    assert j.velocidad == pytest.approx(4.5)


def test_los_bonus_nunca_pasan_de_los_topes_de_la_nave(rm):
    grande = Bonus(velocidad_extra=99, danio_extra=99, cadencia_menos_ms=99_999)
    j = Jugador(rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]), 600, 800, grande)
    assert j.velocidad == Jugador.CONFIG["vel_max"]
    assert j.danio == Jugador.CONFIG["danio_max"]
    assert j.cadencia_disparo == Jugador.CONFIG["cadencia_max"]


def test_los_bonus_se_mantienen_al_reiniciar_la_partida_y_al_elegir_nivel(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "ataque_1")
    juego = _juego(rm, audio, scoreboard, progresion)
    for reinicio in (lambda: juego.reiniciar_juego(), lambda: juego.reiniciar_juego(nivel_forzado=2)):
        juego.jugador.salud_maxima = 50
        juego.jugador.vidas = 1
        juego.jugador.danio = 10
        reinicio()
        assert (juego.jugador.vidas, juego.jugador.salud_maxima, juego.jugador.danio) == (4, 60, 20)


def test_el_bonus_de_salud_se_ve_en_la_barra_bajo_la_nave(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "defensa_3")
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.dibujar()                                  # no debe fallar con 70 de salud
    assert juego.jugador.salud_maxima == 70


def test_la_progresion_es_opcional(rm, audio, scoreboard):
    j = _juego(rm, audio, scoreboard, None)
    j.puntuacion = 5000
    j.volver_al_menu()                               # sin progresión no hay nada que cobrar ni que falle
    assert j.jugador.vidas == 3 and j.bonus == Bonus()


# --- Efectos concretos -------------------------------------------------------

def test_el_escudo_de_reaparicion_dura_mas_con_la_mejora(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "defensa_3", "defensa_4")
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.tiempo_juego = 10_000
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.jugador.tiempo_invulnerable == 10_000 + settings.JUGADOR_INVULNERABLE_MS + 2000


def test_el_escudo_normal_no_cambia_sin_la_mejora(juego):
    juego.tiempo_juego = 10_000
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.jugador.tiempo_invulnerable == 10_000 + settings.JUGADOR_INVULNERABLE_MS


def test_el_combo_sube_mas_facil_con_la_mejora_de_maestria(rm, audio, scoreboard, progresion):
    _comprar(progresion, "utilidad_1", "utilidad_2", "utilidad_3", "utilidad_4")
    juego = _juego(rm, audio, scoreboard, progresion)
    assert juego.combo.umbrales == tuple(round(u * 0.8) for u in settings.COMBO_UMBRALES)
    assert juego.combo.umbrales[0] < settings.COMBO_UMBRALES[0]


def test_combo_con_factor(monkeypatch):
    assert Combo().umbrales == settings.COMBO_UMBRALES
    assert Combo(0.5).umbrales == tuple(max(1, round(u * 0.5)) for u in settings.COMBO_UMBRALES)
    c = Combo(0.5)
    c.racha = c.umbrales[0]
    assert c.multiplicador == 2
    assert Combo(0.0001).umbrales == (1, 1, 1, 1)               # nunca 0: no hay combo gratis


# --- Cobro de monedas --------------------------------------------------------

def test_las_monedas_son_la_puntuacion_entre_100(juego, progresion):
    juego.puntuacion = 1234
    juego._cobrar_monedas()
    assert progresion.monedas == 12 and juego.monedas_cobradas == 12


def test_cobrar_es_idempotente_y_solo_cobra_lo_nuevo(juego, progresion):
    juego.puntuacion = 250
    juego._cobrar_monedas()
    juego._cobrar_monedas()
    assert progresion.monedas == 2
    juego.puntuacion = 350
    juego._cobrar_monedas()
    assert progresion.monedas == 3                              # 350 // 100, sin perder ni duplicar


def test_por_debajo_de_100_puntos_no_hay_monedas(juego, progresion):
    juego.puntuacion = 99
    juego._cobrar_monedas()
    assert progresion.monedas == 0


def test_la_mejora_de_botin_suma_un_25_por_ciento(rm, audio, scoreboard, progresion):
    _comprar(progresion, "utilidad_1", "utilidad_2")
    progresion.monedas = 0
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.puntuacion = 2000
    juego._cobrar_monedas()
    assert progresion.monedas == 25                             # 20 * 1,25


def test_el_game_over_cobra_y_lo_muestra(juego, progresion):
    juego.puntuacion = 730
    juego.jugador.vidas = 0
    juego.actualizar(DT60)                                      # -> juego_terminado
    assert progresion.monedas == 7 and juego.monedas_cobradas == 7
    juego.estado_game_over = True
    juego.pidiendo_nombre = False
    juego.dibujar()


def test_la_victoria_final_cobra(juego, progresion):
    juego.nivel = settings.NIVEL_MAX
    juego.puntuacion = 4200
    juego.transicion_activa = True
    juego._finalizar_transicion_fin_de_nivel()
    assert progresion.monedas == 42


def test_terminar_un_nivel_intermedio_ya_cobra_un_punto_de_control(juego, progresion):
    juego.nivel = 1
    juego.puntuacion = 900
    juego.transicion_activa = True
    juego._finalizar_transicion_fin_de_nivel()
    assert progresion.monedas == 9


def test_salir_al_menu_o_cerrar_la_ventana_no_pierde_lo_ganado(hacer_juego, progresion):
    a = hacer_juego()
    a.puntuacion = 500
    a.volver_al_menu()
    assert progresion.monedas == 5
    b = hacer_juego()
    b.puntuacion = 300
    b.salir_del_juego()
    assert progresion.monedas == 8


def test_ejecutar_cobra_al_terminar_por_cualquier_camino(juego, progresion):
    juego.puntuacion = 600
    juego.input_handler.manejar_eventos = lambda: False        # sale del bucle en el primer ciclo
    juego.ejecutar()
    assert progresion.monedas == 6


def test_avanzar_de_nivel_conserva_lo_cobrado_y_sigue_acumulando_sin_duplicar(juego, progresion):
    juego.puntuacion = 300
    juego._cobrar_monedas()
    juego.jefe_derrotado = True
    juego.reiniciar_juego()                                     # avance: la puntuación continúa
    assert juego.puntuacion == 300 and progresion.monedas == 3
    juego.puntuacion = 450
    juego._cobrar_monedas()
    assert progresion.monedas == 4


@pytest.mark.parametrize("reinicio", [
    lambda j: j.reiniciar_juego(),                              # Reintentar / Jugar de nuevo
    lambda j: j.reiniciar_juego(nivel_forzado=1),               # nivel del selector
])
def test_reiniciar_cobra_lo_pendiente_y_empieza_de_cero(juego, progresion, reinicio):
    juego.puntuacion = 800
    reinicio(juego)                                             # cobra 8 antes de poner la puntuación a 0
    assert progresion.monedas == 8 and juego.puntuacion == 0 and juego.monedas_cobradas == 0
    juego.puntuacion = 150
    juego._cobrar_monedas()
    assert progresion.monedas == 9                              # la nueva partida cobra desde cero


def test_reintentar_tras_game_over_no_cobra_dos_veces(juego, progresion):
    juego.puntuacion = 500
    juego.jugador.vidas = 0
    juego.actualizar(DT60)
    assert progresion.monedas == 5
    juego.reiniciar_juego()
    assert progresion.monedas == 5


def test_en_el_sin_fin_tambien_se_cobra(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 3300
    j.volver_al_menu()
    assert progresion.monedas == 33


def test_lo_cobrado_queda_guardado_en_disco(juego, progresion):
    juego.puntuacion = 1000
    juego._cobrar_monedas()
    assert json.loads(open(progresion.ruta, encoding="utf-8").read())["monedas"] == 10


def test_un_ciclo_completo_ganar_gastar_y_notar_el_efecto(rm, audio, scoreboard, progresion):
    """Partida 1 sin mejoras -> monedas -> comprar -> partida 2 ya con el bonus."""
    a = _juego(rm, audio, scoreboard, progresion)
    a.puntuacion = 15_000
    a.volver_al_menu()
    assert progresion.monedas == 150
    assert progresion.comprar("defensa_1") == "ok"

    b = _juego(rm, audio, scoreboard, progresion)               # el menú crea un Juego nuevo
    assert b.jugador.salud_maxima == 60 and progresion.monedas == 50
