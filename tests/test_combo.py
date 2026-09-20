"""Combo de puntuación: lógica (src/core/combo.py), reglas de la partida y HUD."""
import pygame
import pytest

from src.core import i18n, settings
from src.core.combo import Combo
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe

ORO = (255, 215, 0)


def _combo(racha):
    c = Combo()
    c.racha = racha
    return c


# --- Lógica pura -------------------------------------------------------------

def test_arranca_en_x1():
    c = Combo()
    assert c.racha == 0 and c.multiplicador == 1 and c.es_maximo is False


@pytest.mark.parametrize("racha, esperado", [
    (0, 1), (9, 1), (10, 2), (24, 2), (25, 3), (49, 3), (50, 4), (89, 4), (90, 5), (10_000, 5),
])
def test_los_umbrales_son_exactos_y_hay_tope(racha, esperado):
    assert _combo(racha).multiplicador == esperado


def test_el_tope_es_uno_mas_los_umbrales():
    assert _combo(10_000).multiplicador == 1 + len(settings.COMBO_UMBRALES)
    assert _combo(10_000).es_maximo and not _combo(89).es_maximo


def test_los_umbrales_estan_ordenados_y_son_positivos():
    u = settings.COMBO_UMBRALES
    assert list(u) == sorted(set(u)) and u[0] > 0


def test_el_progreso_va_de_0_a_1_en_cada_escalon():
    assert _combo(0).progreso() == 0
    assert _combo(5).progreso() == pytest.approx(0.5)         # a mitad de x1 -> x2
    assert _combo(10).progreso() == 0                          # acaba de llegar a x2
    assert _combo(17).progreso() == pytest.approx(7 / 15)      # x2 -> x3 (10..25)
    assert _combo(89).progreso() == pytest.approx(39 / 40)     # a punto de x5
    assert _combo(90).progreso() == 1.0 and _combo(500).progreso() == 1.0


def test_sumar_baja_y_romper():
    c = Combo()
    for _ in range(12):
        c.sumar_baja()
    assert c.racha == 12 and c.multiplicador == 2
    c.romper()
    assert c.racha == 0 and c.multiplicador == 1


# --- Reglas de la partida ----------------------------------------------------

def _enemigo(rm, nivel=1):
    return EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, nivel)


def test_cada_baja_suma_a_la_racha(juego, rm):
    juego.al_eliminar_enemigo(_enemigo(rm))
    juego.al_eliminar_enemigo(_enemigo(rm))
    assert juego.combo.racha == 2


def test_la_puntuacion_se_multiplica_por_el_combo(juego, rm):
    juego.combo.racha = 30                                     # x3 (25..49)
    enemigo = _enemigo(rm)
    juego.al_eliminar_enemigo(enemigo)
    assert juego.puntuacion == enemigo.valor_puntuacion * juego.nivel * 3


def test_la_baja_que_sube_de_escalon_ya_puntua_con_el_nuevo(juego, rm):
    juego.combo.racha = settings.COMBO_UMBRALES[0] - 1          # una baja para x2
    enemigo = _enemigo(rm)
    juego.al_eliminar_enemigo(enemigo)
    assert juego.combo.multiplicador == 2
    assert juego.puntuacion == enemigo.valor_puntuacion * juego.nivel * 2


def test_el_jefe_cuenta_y_puntua_con_el_combo(juego, rm):
    juego.combo.racha = 50                                     # x4
    juego.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, 1, juego.jugador)
    juego.al_eliminar_enemigo(jefe)
    assert juego.puntuacion == jefe.valor_puntuacion * juego.nivel * 4
    assert juego.combo.racha == 51


def test_un_impacto_que_llega_a_la_nave_rompe_el_combo(juego):
    juego.combo.racha = 60
    juego.jugador.salud = juego.jugador.salud_maxima
    juego.manejar_impacto_jugador()
    assert juego.combo.racha == 0


def test_un_impacto_estando_invulnerable_no_rompe_el_combo(juego):
    juego.combo.racha = 60
    juego.jugador.invulnerable = True
    juego.manejar_impacto_jugador()
    assert juego.combo.racha == 60


def test_perder_una_vida_rompe_el_combo(juego):
    juego.combo.racha = 60
    juego.jugador.salud = 0
    juego.manejar_impacto_jugador()
    assert juego.combo.racha == 0


def _chocar(juego, enemigo):
    """Por el camino real: colisión cuerpo a cuerpo -> `CollisionManager` -> reglas."""
    enemigo.rect.center = juego.jugador.rect.center
    juego.entity_manager.agregar_enemigo(enemigo)
    juego.collision_manager.actualizar(juego.tiempo_juego + settings.CONTACTO_COOLDOWN_MS + 1)


def test_el_contacto_con_un_enemigo_tambien_lo_rompe(juego, rm):
    juego.combo.racha = 60
    enemigo = _enemigo(rm)
    enemigo.salud = 10 * settings.DANIO_EMBESTIDA              # sobrevive al choque
    _chocar(juego, enemigo)
    assert juego.combo.racha == 0


def test_un_choque_que_destruye_al_enemigo_rompe_el_combo_y_la_baja_abre_el_siguiente(juego, rm):
    """El daño rompe la racha y el enemigo destruido por el choque cuenta ya
    como la primera baja de la nueva (con multiplicador x1)."""
    juego.combo.racha = 60
    _chocar(juego, _enemigo(rm))                               # salud = DANIO_EMBESTIDA: muere en el choque
    assert juego.combo.racha == 1 and juego.combo.multiplicador == 1


def test_avanzar_de_nivel_conserva_el_combo(juego):
    juego.combo.racha = 40
    juego.jefe_derrotado = True
    juego.reiniciar_juego()
    assert juego.nivel == 2 and juego.combo.racha == 40


def test_reintentar_y_elegir_nivel_reinician_el_combo(juego):
    juego.combo.racha = 40
    juego.reiniciar_juego()                                    # Reintentar / Jugar de nuevo
    assert juego.combo.racha == 0

    juego.combo.racha = 40
    juego.reiniciar_juego(nivel_forzado=1)                     # nivel del selector
    assert juego.combo.racha == 0


def test_en_el_sin_fin_el_combo_sigue_tras_el_jefe_y_se_reinicia_al_reintentar(rm, audio, scoreboard):
    from src.core import sin_fin
    from src.core.engine import Juego

    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=settings.MODO_SIN_FIN)
    j.nivel = sin_fin.JEFE_CADA
    j.combo.racha = 30
    j.jefe = jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 200, 200, 600, 800, j.nivel, j.jugador)
    j.al_eliminar_enemigo(jefe)
    assert j.nivel == sin_fin.JEFE_CADA + 1 and j.combo.racha == 31
    j.reiniciar_juego()
    assert j.combo.racha == 0


# --- HUD ---------------------------------------------------------------------

def _hay_oro(juego, region):
    zona = juego.pantalla.subsurface(region)
    return any(zona.get_at((x, y))[:3] == ORO
               for x in range(zona.get_width()) for y in range(zona.get_height()))


REGION_CAMPANA = pygame.Rect(440, 68, 160, 40)


def test_en_x1_no_se_dibuja_el_combo(juego):
    juego.dibujar()
    assert not _hay_oro(juego, REGION_CAMPANA)


def test_con_combo_se_dibuja_bajo_la_puntuacion(juego):
    juego.combo.racha = 30
    juego.dibujar()
    assert _hay_oro(juego, REGION_CAMPANA)


def test_en_pausa_el_combo_se_atenua(juego):
    juego.combo.racha = 30
    juego.dibujar()
    juego.pausar_juego()
    juego.pantalla.fill((0, 0, 0))
    juego.ui_manager._dibujar_hud_basico(juego.pantalla)
    assert not _hay_oro(juego, REGION_CAMPANA)


def test_en_el_sin_fin_el_combo_va_bajo_la_oleada(rm, audio, scoreboard):
    from src.core.engine import Juego

    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm, modo=settings.MODO_SIN_FIN)
    j.combo.racha = 30
    j.dibujar()
    assert _hay_oro(j, pygame.Rect(440, 90, 160, 40))
    assert not _hay_oro(j, pygame.Rect(440, 68, 160, 20))       # la fila de la oleada queda libre


@pytest.mark.parametrize("codigo", i18n.IDIOMAS)
def test_el_hud_del_combo_se_dibuja_en_cada_idioma(juego, codigo):
    i18n.establecer_idioma(codigo)
    juego.combo.racha = 95                                      # tope: barra llena
    juego.dibujar()
    assert i18n.t("hud.combo", n=5) == "COMBO x5"
