"""Temblor de pantalla: modelo (src/visual/screen_shake.py), disparadores y dibujado."""
import pygame
import pytest

from src.core import preferencias, settings
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe
from src.visual.screen_shake import Temblor

DT60 = 1.0 / 60.0


# --- Modelo ------------------------------------------------------------------

def test_en_reposo_no_desplaza():
    t = Temblor()
    assert t.activo is False
    assert t.desplazamiento() == (0, 0)


def test_el_trauma_se_acumula_y_tiene_tope_en_1():
    t = Temblor()
    t.agregar(0.6)
    t.agregar(0.6)
    assert t.trauma == 1.0


def test_el_trauma_decae_con_el_tiempo_de_juego_hasta_0():
    t = Temblor()
    t.agregar(0.5)
    t.actualizar(0.1)
    assert t.trauma == pytest.approx(0.5 - settings.TEMBLOR_DECAIMIENTO * 0.1)
    t.actualizar(10)
    assert t.trauma == 0 and t.activo is False


def test_el_desplazamiento_esta_acotado_por_el_trauma_al_cuadrado():
    t = Temblor()
    t.agregar(0.5)
    tope = settings.TEMBLOR_MAX_PX * 0.5 ** 2
    desplazamientos = [t.desplazamiento() for _ in range(300)]
    assert all(abs(dx) <= round(tope) + 1 and abs(dy) <= round(tope) + 1 for dx, dy in desplazamientos)
    assert any(d != (0, 0) for d in desplazamientos)          # de verdad se mueve


def test_mas_trauma_mueve_mas():
    def amplitud_maxima(trauma):
        t = Temblor()
        t.agregar(trauma)
        return max(max(abs(dx), abs(dy)) for dx, dy in (t.desplazamiento() for _ in range(300)))

    assert amplitud_maxima(1.0) > amplitud_maxima(0.5) > amplitud_maxima(0.2)


def test_reiniciar_lo_apaga():
    t = Temblor()
    t.agregar(1.0)
    t.reiniciar()
    assert t.activo is False and t.desplazamiento() == (0, 0)


# --- Disparadores ------------------------------------------------------------

def test_recibir_un_impacto_hace_temblar(juego):
    juego.jugador.salud = juego.jugador.salud_maxima
    juego.manejar_impacto_jugador()
    assert juego.effect_manager.temblor.trauma == pytest.approx(settings.TEMBLOR_GOLPE)


def test_un_impacto_estando_invulnerable_no_hace_temblar(juego):
    juego.jugador.invulnerable = True
    juego.manejar_impacto_jugador()
    assert juego.effect_manager.temblor.trauma == 0


def test_perder_una_vida_tiembla_mas_que_un_impacto(juego):
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.effect_manager.temblor.trauma == pytest.approx(settings.TEMBLOR_MUERTE)
    assert settings.TEMBLOR_MUERTE > settings.TEMBLOR_GOLPE


def test_derrotar_al_jefe_hace_temblar(juego, rm):
    juego.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert juego.effect_manager.temblor.trauma == pytest.approx(settings.TEMBLOR_JEFE)


def test_destruir_un_enemigo_normal_no_hace_temblar(juego, rm):
    enemigo = EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, 1)
    juego.al_eliminar_enemigo(enemigo)
    assert juego.effect_manager.temblor.trauma == 0


# --- Reloj de juego ----------------------------------------------------------

def test_el_temblor_decae_al_actualizar_y_se_congela_en_pausa(juego):
    juego.effect_manager.agregar_temblor(0.8)
    juego.actualizar(DT60)
    tras_un_frame = juego.effect_manager.temblor.trauma
    assert tras_un_frame < 0.8

    juego.pausar_juego()
    for _ in range(30):            # `Juego.ejecutar` no llama a `actualizar` en pausa
        juego.dibujar()
    assert juego.effect_manager.temblor.trauma == tras_un_frame


def test_el_temblor_tambien_decae_durante_la_transicion_de_nivel(juego):
    juego.effect_manager.agregar_temblor(1.0)
    juego.transicion_activa = True
    juego.transicion_fase = "espera"
    juego.actualizar(DT60)
    assert juego.effect_manager.temblor.trauma < 1.0


def test_reiniciar_la_partida_borra_el_temblor(juego):
    juego.effect_manager.agregar_temblor(1.0)
    juego.reiniciar_juego()
    assert juego.effect_manager.temblor.activo is False


# --- Dibujado ----------------------------------------------------------------

def _pintar_fondo_reconocible(juego, monkeypatch):
    """Hace que el fondo sea una rejilla de columnas de colores distintos, para
    poder ver cuánto se ha desplazado el mundo."""
    def dibujar(pantalla):
        for x in range(pantalla.get_width()):
            pantalla.fill((x % 250, 40, 40), (x, 0, 1, pantalla.get_height()))
    monkeypatch.setattr(juego.background, "draw", dibujar)


def test_sin_temblor_el_mundo_se_dibuja_donde_siempre(juego, monkeypatch):
    _pintar_fondo_reconocible(juego, monkeypatch)
    juego.dibujar()
    assert juego.pantalla.get_at((300, 700))[:3] == (300 % 250, 40, 40)


def test_con_temblor_el_mundo_se_desplaza(juego, monkeypatch):
    _pintar_fondo_reconocible(juego, monkeypatch)
    monkeypatch.setattr(juego.effect_manager.temblor, "desplazamiento", lambda: (7, 0))
    juego.effect_manager.agregar_temblor(1.0)
    juego.dibujar()
    # El píxel que estaba en x = 293 se ve ahora en x = 300
    assert juego.pantalla.get_at((300, 700))[:3] == (293 % 250, 40, 40)


def test_el_temblor_no_mueve_el_hud(juego, monkeypatch):
    """La puntuación (arriba a la derecha) sale en el mismo sitio con y sin temblor."""
    juego.puntuacion = 123456
    juego.dibujar()
    sin_temblor = juego.pantalla.subsurface((440, 35, 150, 35)).copy()

    monkeypatch.setattr(juego.effect_manager.temblor, "desplazamiento", lambda: (9, 9))
    juego.effect_manager.agregar_temblor(1.0)
    juego.dibujar()
    con_temblor = juego.pantalla.subsurface((440, 35, 150, 35)).copy()

    # Mismo texto en el mismo sitio (el fondo detrás sí cambia, así que
    # comparamos solo los píxeles blancos del texto)
    def texto(s):
        return {(x, y) for x in range(s.get_width()) for y in range(s.get_height())
                if s.get_at((x, y))[:3] == (240, 240, 240)}
    assert texto(sin_temblor) and texto(sin_temblor) == texto(con_temblor)


def test_las_pantallas_de_overlay_no_tiemblan(juego, monkeypatch):
    llamadas = []
    monkeypatch.setattr(juego.effect_manager.temblor, "desplazamiento", lambda: llamadas.append(1) or (5, 5))
    juego.effect_manager.agregar_temblor(1.0)
    for estado in ("estado_game_over", "estado_nivel_completado", "estado_victoria_final"):
        setattr(juego, estado, True)
        juego.pausado = True
        juego.dibujar()
        setattr(juego, estado, False)
    assert llamadas == []


def test_muchos_frames_con_temblor_sin_crash(juego):
    juego.jugador.vidas = 999
    for i in range(300):
        if i % 60 == 0:
            juego.effect_manager.agregar_temblor(0.9)
        juego.actualizar(DT60)
        juego.dibujar()


# --- La opción de Opciones que lo apaga -------------------------------------

def test_con_el_temblor_apagado_no_se_acumula_trauma(juego):
    preferencias.establecer_temblor(False)
    juego.effect_manager.agregar_temblor(1.0)
    assert juego.effect_manager.temblor.trauma == 0


def test_apagar_el_temblor_a_mitad_de_uno_lo_corta(juego):
    juego.effect_manager.agregar_temblor(1.0)
    preferencias.establecer_temblor(False)
    assert juego.effect_manager.desplazamiento_temblor() == (0, 0)


def test_con_el_temblor_apagado_los_disparadores_no_hacen_nada(juego, rm):
    preferencias.establecer_temblor(False)
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert juego.effect_manager.temblor.trauma == 0


def test_con_el_temblor_apagado_no_se_desplaza_el_dibujado(juego, monkeypatch):
    _pintar_fondo_reconocible(juego, monkeypatch)
    monkeypatch.setattr(juego.effect_manager.temblor, "desplazamiento", lambda: (7, 0))
    juego.effect_manager.temblor.trauma = 1.0

    preferencias.establecer_temblor(False)
    juego.dibujar()
    assert juego.pantalla.get_at((300, 700))[:3] == (300 % 250, 40, 40)      # sin desplazar

    preferencias.establecer_temblor(True)
    juego.dibujar()
    assert juego.pantalla.get_at((300, 700))[:3] == (293 % 250, 40, 40)      # con desplazamiento


def test_los_elementos_de_la_pestana_pantalla_se_ocultan_en_las_demas(rm, audio, scoreboard):
    from src.ui.menu import MenuManager

    menu = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    menu._abrir_opciones()
    menu._mostrar_pestana("controles")
    assert not menu.btn_temblor.visible
    menu._mostrar_pestana("pantalla")
    assert menu.btn_temblor.visible
