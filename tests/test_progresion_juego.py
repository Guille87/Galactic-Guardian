"""La progresión dentro de la partida: bonus de la nave, botín, combo, escudo y cobro de monedas.

`P` es lo que vale una moneda en puntos: los tests no dependen de ese ritmo."""
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
P = settings.MONEDAS_PUNTOS


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
    assert (j.vidas, j.salud_maxima, j.velocidad, j.danio, j.disparos_s, j.balas_por_disparo) == (3, 50, 5, 10, 4.0, 1)
    assert j.regen_s == 0


def test_las_mejoras_suben_los_valores_de_arranque(rm, audio, scoreboard, progresion):
    _comprar(progresion, "ataque_1", "ataque_2", "ataque_3", "ataque_4", "ataque_5", "ataque_6",
             "defensa_1", "defensa_2", "defensa_3", "defensa_4", "defensa_5",
             "utilidad_1", "utilidad_2", "utilidad_3")
    j = _juego(rm, audio, scoreboard, progresion).jugador
    assert j.vidas == 4
    assert j.salud_maxima == 100 and j.salud == 100
    assert j.danio == 20 and j.disparos_s == 6.0 and j.balas_por_disparo == 3
    assert j.velocidad == pytest.approx(6.0) and j.regen_s == pytest.approx(0.5)


def test_los_bonus_nunca_pasan_de_los_topes_de_la_nave(rm):
    grande = Bonus(velocidad_extra=99, danio_extra=99, disparos_extra=99, balas_extra=99)
    j = Jugador(rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]), 600, 800, grande)
    c = Jugador.CONFIG
    assert (j.velocidad, j.danio, j.disparos_s, j.balas_por_disparo) == (
        c["vel_max"], c["danio_max"], c["disparos_max"], c["balas_max"])


def test_los_bonus_se_mantienen_al_reiniciar_la_partida_y_al_elegir_nivel(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "ataque_1")
    juego = _juego(rm, audio, scoreboard, progresion)
    for reinicio in (lambda: juego.reiniciar_juego(), lambda: juego.reiniciar_juego(nivel_forzado=2)):
        juego.jugador.salud_maxima = 50
        juego.jugador.vidas = 1
        juego.jugador.danio = 10
        reinicio()
        assert (juego.jugador.vidas, juego.jugador.salud_maxima, juego.jugador.danio) == (3, 80, 15)


def test_el_bonus_de_salud_se_ve_en_la_barra_bajo_la_nave(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "defensa_3")
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.dibujar()                                  # no debe fallar con 80 de salud
    assert juego.jugador.salud_maxima == 80


def test_la_progresion_es_opcional(rm, audio, scoreboard):
    j = _juego(rm, audio, scoreboard, None)
    j.puntuacion = 5000
    j.volver_al_menu()                               # sin progresión no hay nada que cobrar ni que falle
    assert j.jugador.vidas == 3 and j.bonus == Bonus()


# --- Efectos concretos -------------------------------------------------------

def test_el_escudo_de_reaparicion_dura_mas_con_la_mejora(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "defensa_3", "defensa_4", "defensa_5", "defensa_6")
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


def test_recibir_un_golpe_reinicia_la_espera_de_la_regeneracion(juego):
    juego.jugador.invulnerable = False
    juego.tiempo_juego = 20_000
    juego.manejar_impacto_jugador()
    assert juego.jugador.ultimo_dano == 20_000


def test_un_impacto_con_la_nave_invulnerable_no_reinicia_la_regeneracion(juego):
    juego.jugador.invulnerable = True
    juego.tiempo_juego = 20_000
    juego.manejar_impacto_jugador()
    assert juego.jugador.ultimo_dano < 0


def test_la_regeneracion_funciona_dentro_de_la_partida(rm, audio, scoreboard, progresion):
    _comprar(progresion, "defensa_1", "defensa_2", "defensa_3", "defensa_4")
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.tiempo_proximo_enemigo = float("inf")               # sin enemigos que molesten
    juego.jugador.salud = 20
    for _ in range(60 * 10):
        juego.actualizar(DT60)
    assert juego.jugador.salud > 20 + 0.5 * 5                 # tras la espera, ~0,5 por segundo


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

def test_las_monedas_son_la_puntuacion_entre_el_ritmo_del_juego(juego, progresion):
    juego.puntuacion = 12 * P + P // 2
    juego._cobrar_monedas()
    assert progresion.monedas == 12 and juego.monedas_cobradas == 12


def test_cobrar_es_idempotente_y_solo_cobra_lo_nuevo(juego, progresion):
    juego.puntuacion = 2 * P + P // 2
    juego._cobrar_monedas()
    juego._cobrar_monedas()
    assert progresion.monedas == 2
    juego.puntuacion = 3 * P + P // 2
    juego._cobrar_monedas()
    assert progresion.monedas == 3                              # sin perder ni duplicar


def test_por_debajo_de_una_moneda_no_hay_monedas(juego, progresion):
    juego.puntuacion = P - 1
    juego._cobrar_monedas()
    assert progresion.monedas == 0


def test_la_mejora_de_botin_suma_un_25_por_ciento(rm, audio, scoreboard, progresion):
    _comprar(progresion, "utilidad_1", "utilidad_2")
    progresion.monedas = 0
    juego = _juego(rm, audio, scoreboard, progresion)
    juego.puntuacion = 20 * P
    juego._cobrar_monedas()
    assert progresion.monedas == 25                             # 20 * 1,25


def test_el_game_over_cobra_y_lo_muestra(juego, progresion):
    juego.puntuacion = 7 * P + 3
    juego.jugador.vidas = 0
    juego.actualizar(DT60)                                      # -> juego_terminado
    assert progresion.monedas == 7 and juego.monedas_cobradas == 7
    juego.estado_game_over = True
    juego.pidiendo_nombre = False
    juego.dibujar()


def test_la_victoria_final_cobra(juego, progresion):
    juego.nivel = settings.NIVEL_MAX
    juego.puntuacion = 42 * P
    juego.transicion_activa = True
    juego._finalizar_transicion_fin_de_nivel()
    assert progresion.monedas == 42


def test_terminar_un_nivel_intermedio_ya_cobra_un_punto_de_control(juego, progresion):
    juego.nivel = 1
    juego.puntuacion = 9 * P
    juego.transicion_activa = True
    juego._finalizar_transicion_fin_de_nivel()
    assert progresion.monedas == 9


def test_salir_al_menu_o_cerrar_la_ventana_no_pierde_lo_ganado(hacer_juego, progresion):
    a = hacer_juego()
    a.puntuacion = 5 * P
    a.volver_al_menu()
    assert progresion.monedas == 5
    b = hacer_juego()
    b.puntuacion = 3 * P
    b.salir_del_juego()
    assert progresion.monedas == 8


def test_ejecutar_cobra_al_terminar_por_cualquier_camino(juego, progresion):
    juego.puntuacion = 6 * P
    juego.input_handler.manejar_eventos = lambda: False        # sale del bucle en el primer ciclo
    juego.ejecutar()
    assert progresion.monedas == 6


def test_avanzar_de_nivel_conserva_lo_cobrado_y_sigue_acumulando_sin_duplicar(juego, progresion):
    juego.puntuacion = 3 * P
    juego._cobrar_monedas()
    juego.jefe_derrotado = True
    juego.reiniciar_juego()                                     # avance: la puntuación continúa
    assert juego.puntuacion == 3 * P and progresion.monedas == 3
    juego.puntuacion = 4 * P + P // 2
    juego._cobrar_monedas()
    assert progresion.monedas == 4


@pytest.mark.parametrize("reinicio", [
    lambda j: j.reiniciar_juego(),                              # Reintentar / Jugar de nuevo
    lambda j: j.reiniciar_juego(nivel_forzado=1),               # nivel del selector
])
def test_reiniciar_cobra_lo_pendiente_y_empieza_de_cero(juego, progresion, reinicio):
    juego.puntuacion = 8 * P
    reinicio(juego)                                             # cobra 8 antes de poner la puntuación a 0
    assert progresion.monedas == 8 and juego.puntuacion == 0 and juego.monedas_cobradas == 0
    juego.puntuacion = P + P // 2
    juego._cobrar_monedas()
    assert progresion.monedas == 9                              # la nueva partida cobra desde cero


def test_reintentar_tras_game_over_no_cobra_dos_veces(juego, progresion):
    juego.puntuacion = 5 * P
    juego.jugador.vidas = 0
    juego.actualizar(DT60)
    assert progresion.monedas == 5
    juego.reiniciar_juego()
    assert progresion.monedas == 5


def test_en_el_sin_fin_tambien_se_cobra(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion, modo=settings.MODO_SIN_FIN)
    j.puntuacion = 33 * P
    j.volver_al_menu()
    assert progresion.monedas == 33


def test_lo_cobrado_queda_guardado_en_disco(juego, progresion):
    juego.puntuacion = 10 * P
    juego._cobrar_monedas()
    assert json.loads(open(progresion.ruta, encoding="utf-8").read())["monedas"] == 10


def test_un_ciclo_completo_ganar_gastar_y_notar_el_efecto(rm, audio, scoreboard, progresion):
    """Partida 1 sin mejoras -> monedas -> comprar -> partida 2 ya con el bonus."""
    a = _juego(rm, audio, scoreboard, progresion)
    a.puntuacion = 150 * P
    a.volver_al_menu()
    assert progresion.monedas == 150
    assert progresion.comprar("defensa_1") == "ok"

    b = _juego(rm, audio, scoreboard, progresion)               # el menú crea un Juego nuevo
    assert b.jugador.salud_maxima == 65
    assert progresion.monedas == 150 - mejoras.POR_ID["defensa_1"].coste
