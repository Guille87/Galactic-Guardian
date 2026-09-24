"""Monedas en el resumen de fin de nivel, resumen al abandonar la partida y economía (1 moneda / N puntos)."""
import pygame
import pytest

from src.core import settings
from src.core.engine import Juego
from src.core.guardado import Guardado
from src.ui.menu import MenuManager

DT60 = 1.0 / 60.0
P = settings.MONEDAS_PUNTOS


def _comprar(prog, *ids):
    prog.ingresar(1_000_000)
    for id_ in ids:
        assert prog.comprar(id_) == "ok", id_
    prog.monedas = 0


def _juego(rm, audio, scoreboard, prog, **kw):
    return Juego(pygame.display.get_surface(), audio, scoreboard, rm, progresion=prog, **kw)


def _lineas(juego, monkeypatch):
    """Textos que dibuja el juego con `_dibujar_estadisticas` (las líneas de un resumen)."""
    lineas = []
    monkeypatch.setattr(juego.render_manager, "_dibujar_estadisticas",
                        lambda l, y, color=(255, 255, 255): lineas.extend(l))
    juego.dibujar()
    return lineas


def _terminar_nivel(j):
    j.transicion_activa = True
    j._finalizar_transicion_fin_de_nivel()


# --- La economía -----------------------------------------------------------------------------

def test_una_moneda_cada_25_puntos():
    assert settings.MONEDAS_PUNTOS == 25


def test_un_nivel_1_perfecto_sin_mejoras_da_unas_120_monedas():
    """~3100 puntos: la cuenta del autor (3100 / 25 = 124)."""
    assert 3100 // settings.MONEDAS_PUNTOS == 124


# --- Monedas del nivel ---------------------------------------------------------------------------

def test_las_monedas_del_nivel_salen_de_la_puntuacion(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 12 * P + P // 2
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 12


def test_el_resumen_del_nivel_muestra_monedas_ganadas_y_total(rm, audio, scoreboard, progresion, monkeypatch):
    progresion.monedas = 100
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 10 * P
    _terminar_nivel(j)
    assert "Monedas: +10 (total 110)" in _lineas(j, monkeypatch)


def test_con_botin_las_monedas_del_nivel_suman_el_porcentaje_y_se_avisa(rm, audio, scoreboard, progresion, monkeypatch):
    _comprar(progresion, "utilidad_1", "utilidad_2")                      # Botín I: +25 %
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 20 * P
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 25                                        # 20 * 1,25
    lineas = _lineas(j, monkeypatch)
    assert "Monedas: +25 (total 25)" in lineas and "Botín: +25 % de monedas" in lineas


def test_sin_botin_no_hay_linea_de_botin(rm, audio, scoreboard, progresion, monkeypatch):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 5 * P
    _terminar_nivel(j)
    assert not any("Botín" in l for l in _lineas(j, monkeypatch))


def test_el_botin_se_suma_con_todas_las_mejoras_de_monedas(rm, audio, scoreboard, progresion, monkeypatch):
    ids = [m.id for m in __import__("src.core.mejoras", fromlist=["MEJORAS"]).MEJORAS if m.rama == "utilidad"]
    _comprar(progresion, *ids)
    j = _juego(rm, audio, scoreboard, progresion)
    assert j.bonus.monedas_pct == pytest.approx(1.25)
    j.puntuacion = 40 * P
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 90                                        # 40 * 2,25
    assert "Botín: +125 % de monedas" in _lineas(j, monkeypatch)


def test_cada_nivel_cuenta_solo_sus_monedas(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 10 * P
    j.jefe_derrotado = True
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 10
    j.estado_nivel_completado = False
    j.reiniciar_juego()                                                      # avanza al nivel 2 (la puntuación sigue)
    j.puntuacion += 7 * P
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 7 and progresion.monedas == 17


def test_reiniciar_desde_cero_reinicia_la_cuenta_del_nivel(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 10 * P
    _terminar_nivel(j)
    j.reiniciar_juego(nivel_forzado=1)
    assert j.monedas_del_nivel == 0 and j.monedas_inicio_nivel == j.monedas_cobradas == 0


def test_continuar_una_campana_guardada_cuenta_desde_lo_ya_cobrado(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(ruta=str(tmp_path / "g.json"))
    g.guardar_punto(3, 10 * P)
    j = _juego(rm, audio, scoreboard, progresion, guardado=g, continuar=True)
    assert j.monedas_del_nivel == 0
    j.puntuacion += 5 * P
    _terminar_nivel(j)
    assert j.monedas_del_nivel == 5


def test_sin_progresion_el_resumen_del_nivel_no_habla_de_monedas(rm, audio, scoreboard, monkeypatch):
    j = _juego(rm, audio, scoreboard, None)
    j.puntuacion = 500
    _terminar_nivel(j)
    assert not any("Monedas" in l for l in _lineas(j, monkeypatch))


def test_los_botones_del_resumen_de_nivel_no_se_pisan_con_las_lineas(rm, audio, scoreboard, progresion):
    _comprar(progresion, "utilidad_1", "utilidad_2")
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 20 * P
    _terminar_nivel(j)
    j.dibujar()
    ultima_linea_y = 280 + 40 * 4                                            # 5 líneas: puntos, bajas, tiempo, monedas, botín
    assert j.boton_continuar.rect.top > ultima_linea_y + 10
    assert j.boton_continuar.rect.bottom < j.boton_elegir_nivel.rect.top < j.boton_elegir_nivel.rect.bottom < 800


# --- Abandonar la partida desde la pausa ----------------------------------------------------------

def _pausar_y_salir(j, decision="MENU"):
    """Pausa, pulsa Salir y contesta la confirmación (que es un bucle bloqueante)."""
    j.input_handler.mostrar_confirmacion_salida = lambda: decision
    j.pausar_juego()
    j.dibujar()                                                              # crea los botones de la pausa
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=j.boton_salir.rect.center))
    return j.input_handler.manejar_eventos()


def test_salir_por_su_cuenta_muestra_un_resumen_en_vez_de_ir_directo_al_menu(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    assert _pausar_y_salir(j) is True                                        # el bucle sigue: hay pantalla
    assert j.estado_resumen_salida and j.pausado and j.ejecutando


def test_el_resumen_asegura_las_monedas(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 9 * P + 3
    _pausar_y_salir(j)
    assert progresion.monedas == 9


def test_el_resumen_muestra_nivel_puntos_bajas_tiempo_y_monedas(rm, audio, scoreboard, progresion, monkeypatch):
    j = _juego(rm, audio, scoreboard, progresion)
    j.nivel, j.puntuacion, j.enemigos_eliminados_nivel, j.tiempo_juego = 3, 8 * P, 41, 65_000
    _pausar_y_salir(j)
    lineas = _lineas(j, monkeypatch)
    assert lineas == ["Nivel: 3", f"Puntuación: {8 * P}", "Enemigos destruidos: 41", "Tiempo: 65.0 s",
                      "Monedas: +8 (total 8)"]


def test_el_resumen_del_sin_fin_habla_de_oleada_y_avisa_del_botin(rm, audio, scoreboard, progresion, monkeypatch):
    _comprar(progresion, "utilidad_1", "utilidad_2")
    j = _juego(rm, audio, scoreboard, progresion, modo=settings.MODO_SIN_FIN)
    j.nivel, j.puntuacion = 6, 20 * P
    _pausar_y_salir(j)
    lineas = _lineas(j, monkeypatch)
    assert lineas[0] == "Oleada: 6" and "Monedas: +25 (total 25)" in lineas and "Botín: +25 % de monedas" in lineas


def test_el_boton_menu_del_resumen_vuelve_al_menu(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    _pausar_y_salir(j)
    j.dibujar()                                                              # crea el botón
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=j.boton_menu_resumen.rect.center))
    assert j.input_handler.manejar_eventos() is False
    assert j.resultado == "MENU" and j.ejecutando is False


def test_el_resumen_ignora_el_teclado_y_los_clics_fuera_del_boton(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    _pausar_y_salir(j)
    j.dibujar()
    pygame.event.clear()
    for tecla in (pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE, pygame.K_F1):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5)))
    assert j.input_handler.manejar_eventos() is True
    assert j.estado_resumen_salida and j.pausado and not j.disparando


def test_cerrar_la_ventana_desde_el_resumen_sale_y_ya_estaba_cobrado(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 3 * P
    _pausar_y_salir(j)
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert j.input_handler.manejar_eventos() is False
    assert j.resultado == "SALIR" and progresion.monedas == 3


def test_decir_que_no_en_la_confirmacion_sigue_en_la_pausa(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    _pausar_y_salir(j, decision="CONTINUAR")
    assert not j.estado_resumen_salida and j.pausado


def test_salir_de_la_aplicacion_desde_la_confirmacion_no_muestra_resumen(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    j.puntuacion = 2 * P
    assert _pausar_y_salir(j, decision="SALIR") is False
    assert j.resultado == "SALIR" and not j.estado_resumen_salida and progresion.monedas == 2


def test_el_resumen_se_dibuja_con_y_sin_progresion(rm, audio, scoreboard):
    j = _juego(rm, audio, scoreboard, None)
    _pausar_y_salir(j)
    j.dibujar()
    assert j.boton_menu_resumen is not None


def test_reiniciar_quita_el_resumen(rm, audio, scoreboard, progresion):
    j = _juego(rm, audio, scoreboard, progresion)
    _pausar_y_salir(j)
    j.reiniciar_juego()
    assert not j.estado_resumen_salida and not j.pausado


def test_los_textos_del_resumen_estan_traducidos():
    from src.core import i18n
    i18n.establecer_idioma("en")
    assert i18n.t("resumen.titulo") == "SUMMARY"
    assert i18n.t("resumen.botin", pct=25) == "Loot bonus: +25% coins"
    assert i18n.t("nivel_completado.monedas", n=3, total=9) == "Coins: +3 (total 9)"


# --- Perder y volver a Campaña: el progreso de los niveles completados sigue ahí ----------------------

def test_perder_y_volver_a_campana_ofrece_continuar_donde_se_quedo(rm, audio, scoreboard, progresion, tmp_path):
    """El flujo completo con un mismo guardado compartido, como en `main.py`."""
    g = Guardado(ruta=str(tmp_path / "g.json"))
    j = _juego(rm, audio, scoreboard, progresion, guardado=g)
    j.puntuacion = 500
    j.jefe_derrotado = True
    _terminar_nivel(j)                                                       # nivel 1 completado
    j.estado_nivel_completado = False
    j.reiniciar_juego()                                                      # "Continuar": avanza al nivel 2
    j.puntuacion += 700
    j.jefe_derrotado = True
    _terminar_nivel(j)                                                       # nivel 2 completado
    j.estado_nivel_completado = False
    j.reiniciar_juego()                                                      # empieza el nivel 3...
    j.jugador.vidas = 0
    j.actualizar(DT60)                                                       # ...y se pierde: Game Over
    j.volver_al_menu()

    menu = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion, g)
    preguntas = []
    menu._dialogo_partida_guardada = lambda guardado: preguntas.append((guardado.nivel, guardado.puntuacion)) or "CONTINUAR"
    menu.ejecutando, menu.resultado = True, None
    menu._empezar(settings.MODO_CAMPANA)
    assert preguntas == [(3, 1200)] and menu.resultado == "CONTINUAR"

    nueva = _juego(rm, audio, scoreboard, progresion, guardado=g, continuar=True)
    assert (nueva.nivel, nueva.puntuacion) == (3, 1200)


def test_perder_en_el_primer_nivel_no_deja_guardado(rm, audio, scoreboard, progresion, tmp_path):
    g = Guardado(ruta=str(tmp_path / "g.json"))
    j = _juego(rm, audio, scoreboard, progresion, guardado=g)
    j.jugador.vidas = 0
    j.actualizar(DT60)
    assert not g.existe                                                      # aún no había nada completado
