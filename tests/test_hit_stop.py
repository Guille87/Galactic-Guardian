"""Hit-stop (src/visual/hit_stop.py) y la opción que apaga los efectos de pantalla."""
import pygame
import pytest

from src.core import preferencias, settings
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe
from src.visual.hit_stop import HitStop

DT60 = 1.0 / 60.0


# --- Modelo ------------------------------------------------------------------

def test_en_reposo_no_esta_activo():
    assert HitStop().activo is False


def test_agregar_lo_activa_y_se_gasta_con_dt_real():
    h = HitStop()
    h.agregar(100)
    assert h.activo
    h.actualizar(0.04)
    assert h.restante_ms == pytest.approx(60)
    h.actualizar(1.0)
    assert h.restante_ms == 0 and h.activo is False


def test_dos_golpes_no_se_suman_se_queda_el_mayor():
    h = HitStop()
    h.agregar(150)
    h.agregar(250)
    h.agregar(100)
    assert h.restante_ms == 250


def test_reiniciar_lo_apaga():
    h = HitStop()
    h.agregar(200)
    h.reiniciar()
    assert h.activo is False


# --- Disparadores ------------------------------------------------------------

def test_perder_una_vida_congela_el_juego(juego):
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.effect_manager.hit_stop.restante_ms == settings.HIT_STOP_MUERTE_MS
    assert juego.effect_manager.congelado


def test_derrotar_al_jefe_congela_mas_que_perder_una_vida(juego, rm):
    juego.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert juego.effect_manager.hit_stop.restante_ms == settings.HIT_STOP_JEFE_MS
    assert settings.HIT_STOP_JEFE_MS > settings.HIT_STOP_MUERTE_MS


def test_un_impacto_normal_no_congela(juego):
    juego.jugador.salud = juego.jugador.salud_maxima
    juego.manejar_impacto_jugador()
    assert juego.effect_manager.congelado is False


def test_destruir_un_enemigo_normal_no_congela(juego, rm):
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)
    juego.al_eliminar_enemigo(enemigo)
    assert juego.effect_manager.congelado is False


# --- Efecto sobre la partida -------------------------------------------------

def _con_enemigo(juego, rm):
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)
    juego.entity_manager.agregar_enemigo(enemigo)
    return enemigo


def test_mientras_dura_la_simulacion_esta_parada(juego, rm):
    enemigo = _con_enemigo(juego, rm)
    juego.effect_manager.agregar_hit_stop(100)
    y0, reloj0 = enemigo.rect.y, juego.tiempo_juego
    juego.actualizar(DT60)
    juego.actualizar(DT60)
    assert enemigo.rect.y == y0                     # no se ha movido
    assert juego.tiempo_juego == reloj0             # el reloj de juego está congelado


def test_el_temblor_sigue_vivo_y_decae_durante_el_congelado(juego):
    juego.effect_manager.agregar_temblor(0.8)
    juego.effect_manager.agregar_hit_stop(100)
    juego.actualizar(DT60)
    assert juego.effect_manager.temblor.trauma < 0.8


def test_al_acabar_el_congelado_todo_vuelve_a_moverse(juego, rm):
    enemigo = _con_enemigo(juego, rm)
    juego.effect_manager.agregar_hit_stop(50)
    for _ in range(10):                             # 10 frames a 60 FPS = 166 ms > 50 ms
        juego.actualizar(DT60)
    assert juego.effect_manager.congelado is False
    y0, reloj0 = enemigo.rect.y, juego.tiempo_juego
    juego.actualizar(DT60)
    assert enemigo.rect.y > y0 and juego.tiempo_juego > reloj0


def test_no_se_dispara_mientras_esta_congelado(juego):
    juego.disparando = True
    juego.jugador.ultimo_disparo = -99999
    juego.effect_manager.agregar_hit_stop(200)
    pygame.event.clear()
    juego.input_handler.manejar_eventos()
    assert len(juego.entity_manager.balas) == 0

    juego.effect_manager.hit_stop.reiniciar()
    juego.input_handler.manejar_eventos()
    assert len(juego.entity_manager.balas) > 0


def test_el_golpe_final_congela_antes_del_game_over(juego):
    juego.jugador.vidas = 1
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.jugador.vidas == 0
    juego.actualizar(DT60)                          # congelado: aún no hay Game Over
    assert juego.pausado is False and juego.estado_game_over is False
    for _ in range(30):
        juego.actualizar(DT60)
    assert juego.estado_game_over or juego.pidiendo_nombre


def test_reiniciar_la_partida_borra_el_congelado(juego):
    juego.effect_manager.agregar_hit_stop(500)
    juego.reiniciar_juego()
    assert juego.effect_manager.congelado is False


def test_la_pausa_conserva_el_congelado_pendiente(juego):
    juego.effect_manager.agregar_hit_stop(200)
    juego.pausar_juego()
    for _ in range(30):                             # en pausa `ejecutar` no llama a `actualizar`
        juego.dibujar()
    assert juego.effect_manager.hit_stop.restante_ms == 200


# --- La opción "Efectos de pantalla" ----------------------------------------

def test_con_los_efectos_apagados_no_hay_temblor_ni_hit_stop(juego):
    preferencias.establecer_efectos_pantalla(False)
    juego.effect_manager.agregar_temblor(1.0)
    juego.effect_manager.agregar_hit_stop(500)
    assert juego.effect_manager.temblor.trauma == 0
    assert juego.effect_manager.hit_stop.activo is False
    assert juego.effect_manager.congelado is False


def test_apagar_los_efectos_a_mitad_de_un_congelado_lo_corta(juego, rm):
    enemigo = _con_enemigo(juego, rm)
    juego.effect_manager.agregar_hit_stop(500)
    preferencias.establecer_efectos_pantalla(False)
    y0 = enemigo.rect.y
    juego.actualizar(DT60)
    assert enemigo.rect.y > y0                      # la partida sigue


def test_apagar_los_efectos_a_mitad_de_un_temblor_lo_corta(juego):
    juego.effect_manager.agregar_temblor(1.0)
    preferencias.establecer_efectos_pantalla(False)
    assert juego.effect_manager.desplazamiento_temblor() == (0, 0)


def test_con_los_efectos_apagados_los_disparadores_no_hacen_nada(juego, rm):
    preferencias.establecer_efectos_pantalla(False)
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert juego.effect_manager.temblor.trauma == 0 and juego.effect_manager.congelado is False


def test_los_efectos_apagados_no_desplazan_el_dibujado(juego, monkeypatch):
    def fondo(pantalla):
        for x in range(pantalla.get_width()):
            pantalla.fill((x % 250, 40, 40), (x, 0, 1, pantalla.get_height()))
    monkeypatch.setattr(juego.background, "draw", fondo)
    monkeypatch.setattr(juego.effect_manager.temblor, "desplazamiento", lambda: (7, 0))
    juego.effect_manager.temblor.trauma = 1.0

    preferencias.establecer_efectos_pantalla(False)
    juego.dibujar()
    assert juego.pantalla.get_at((300, 700))[:3] == (300 % 250, 40, 40)      # sin desplazar

    preferencias.establecer_efectos_pantalla(True)
    juego.dibujar()
    assert juego.pantalla.get_at((300, 700))[:3] == (293 % 250, 40, 40)      # con desplazamiento


def test_los_elementos_de_la_pestana_pantalla_se_ocultan_en_las_demas(rm, audio, scoreboard):
    from src.ui.menu import MenuManager

    menu = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    menu._abrir_opciones()
    menu._mostrar_pestana("controles")
    assert not menu.btn_efectos_pantalla.visible
    menu._mostrar_pestana("pantalla")
    assert menu.btn_efectos_pantalla.visible


def test_muchos_frames_con_hit_stop_sin_crash(juego):
    juego.jugador.vidas = 999
    for i in range(300):
        if i % 50 == 0:
            juego.effect_manager.agregar_hit_stop(settings.HIT_STOP_JEFE_MS)
            juego.effect_manager.agregar_temblor(0.9)
        juego.actualizar(DT60)
        juego.dibujar()
