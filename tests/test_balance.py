"""tools/balance.py: el modelo lee los datos reales del juego y sus fórmulas son coherentes.

Además de comprobar las fórmulas, se **valida contra el juego de verdad**: el tiempo
que se tarda en matar al jefe y el ritmo de aparición de enemigos medidos en una
partida real coinciden con lo que predice el modelo.
"""
import math
from dataclasses import replace

import pytest

from src.core import mejoras, niveles, settings
from src.entities.enemies import EnemigoBase, EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from src.entities.player import Jugador
from tools import balance
from tools.balance import (MODELO_ACTUAL, PERFILES, Nave, analizar_nivel, build_al, dps_necesario, jugar,
                           nave_de, orden_de_compra, progresion, vida_enemigo)

DT60 = 1.0 / 60.0
MEDIO = PERFILES["medio"]


# --- Lee los datos reales del juego --------------------------------------------------

@pytest.mark.parametrize("nivel", range(1, 6))
@pytest.mark.parametrize("clase", [EnemigoTipo1, EnemigoTipo2, EnemigoTipo3])
def test_la_vida_del_modelo_es_la_del_juego(rm, jugador, clase, nivel):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    real = clase(img, 0, 0, 600, nivel) if clase is EnemigoTipo1 else clase(img, 0, 0, 600, nivel, jugador)
    assert vida_enemigo(clase, nivel) == real.salud_maxima


@pytest.mark.parametrize("nivel", range(1, 6))
def test_la_vida_del_jefe_del_modelo_es_la_del_juego(rm, jugador, nivel):
    real = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 0, 0, 600, 800, nivel, jugador)
    assert vida_enemigo(Jefe, nivel) == real.salud_maxima


def test_la_nave_base_del_modelo_es_la_del_juego(rm):
    n = nave_de([])
    j = Jugador(rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]), 600, 800)
    assert (n.salud, n.vidas, n.danio, n.velocidad) == (j.salud_maxima, j.vidas, j.danio, j.velocidad)
    assert n.disparos_s == pytest.approx(1000 / j.cadencia_disparo)
    assert n.balas == 1


def test_la_nave_con_todo_el_arbol_del_modelo_es_la_del_juego(rm):
    ids = [m.id for m in mejoras.MEJORAS]
    n = nave_de(ids)
    j = Jugador(rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]), 600, 800, mejoras.calcular_bonus(ids))
    assert (n.salud, n.vidas, n.danio, n.velocidad) == (j.salud_maxima, j.vidas, j.danio, j.velocidad)
    assert n.disparos_s == pytest.approx(j.disparos_s) and n.balas == j.balas_por_disparo
    assert n.regen_s == j.regen_s and n.salud == j.salud_maxima


def test_los_atributos_de_clase_de_los_enemigos_son_los_que_usan_las_instancias(rm, jugador):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    for clase in (EnemigoTipo2, EnemigoTipo3):
        e = clase(img, 0, 0, 600, 1, jugador)
        assert (e.cadencia, e.valor_puntuacion) == (clase.CADENCIA, clase.VALOR)
    jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 0, 0, 600, 800, 1, jugador)
    assert jefe.valor_puntuacion == Jefe.VALOR == 1000


def test_el_modelo_sigue_los_cambios_en_los_datos_del_juego(monkeypatch):
    nave = nave_de([])
    antes = analizar_nivel(nave, 1, MEDIO).danio
    monkeypatch.setattr(settings, "DANIO_BALA_TIPO2", settings.DANIO_BALA_TIPO2 * 3)
    monkeypatch.setattr(settings, "DANIO_JEFE_RAPIDA", settings.DANIO_JEFE_RAPIDA * 3)
    assert analizar_nivel(nave, 1, MEDIO).danio > antes


# --- Coherencia de las fórmulas -------------------------------------------------------

def test_mas_dps_mata_antes_al_jefe_y_da_menos_dano():
    base = nave_de([])
    fuerte = replace(base, danio=base.danio * 4)
    a, b = analizar_nivel(base, 1, MEDIO), analizar_nivel(fuerte, 1, MEDIO)
    assert b.ttk_jefe == pytest.approx(a.ttk_jefe / 4)
    assert b.danio_jefe < a.danio_jefe and b.danio < a.danio and b.afluencia_max < a.afluencia_max


def test_mas_salud_da_menos_muertes():
    base = nave_de([])
    resistente = replace(base, salud=base.salud * 2)
    assert analizar_nivel(resistente, 1, MEDIO).muertes(resistente) == pytest.approx(
        analizar_nivel(base, 1, MEDIO).muertes(base) / 2)


def test_los_niveles_altos_tienen_un_jefe_que_tarda_mas():
    nave = nave_de([])
    ttk = [analizar_nivel(nave, n, MEDIO).ttk_jefe for n in range(1, 6)]
    assert ttk == sorted(ttk) and ttk[-1] > ttk[0]


def test_un_jugador_peor_recibe_mas_dano():
    nave = nave_de([])
    d = {k: analizar_nivel(nave, 2, p).danio for k, p in PERFILES.items()}
    assert d["torpe"] > d["medio"] > d["habil"]


def test_el_multiplicador_de_dano_enemigo_por_nivel_escala_todo_el_dano():
    nave = nave_de([])
    doble = replace(MODELO_ACTUAL, danio_x=lambda n: 2.0)
    assert analizar_nivel(nave, 2, MEDIO, doble).danio == pytest.approx(analizar_nivel(nave, 2, MEDIO).danio * 2)


def test_una_propuesta_puede_cambiar_la_vida_de_los_enemigos():
    nave = nave_de([])
    mitad = replace(MODELO_ACTUAL, vida=lambda clase, n: vida_enemigo(clase, n) // 2)
    assert analizar_nivel(nave, 2, MEDIO, mitad).ttk_jefe == pytest.approx(analizar_nivel(nave, 2, MEDIO).ttk_jefe / 2)


def test_las_fases_cubren_exactamente_hasta_la_llegada_del_jefe():
    for n in range(1, 6):
        r = analizar_nivel(nave_de([]), n, MEDIO)
        assert sum(f.duracion_s for f in r.fases) == pytest.approx(niveles.definicion_nivel(n).tiempo_jefe_ms / 1000)


# --- Árbol y builds -------------------------------------------------------------------

def test_el_orden_de_compra_respeta_los_requisitos_y_lo_mas_barato():
    orden = orden_de_compra(MODELO_ACTUAL.arbol)
    assert len(orden) == len(mejoras.MEJORAS) and len({m.id for m in orden}) == len(orden)
    vistas = set()
    for i, m in enumerate(orden):
        assert m.requiere is None or m.requiere in vistas                 # su anterior ya estaba comprada
        disponibles = [x for x in orden[i:] if x.requiere is None or x.requiere in vistas]
        assert m.coste == min(x.coste for x in disponibles)               # y era lo más barato disponible
        vistas.add(m.id)


def test_las_builds_por_porcentaje_son_crecientes_y_no_pasan_del_presupuesto():
    orden = orden_de_compra(MODELO_ACTUAL.arbol)
    total = sum(m.coste for m in orden)
    previos = -1
    for fr in (0, 0.25, 0.5, 0.75, 1.0):
        ids, gastado = build_al(orden, fr)
        assert gastado <= fr * total + 1e-6 and len(ids) >= previos
        previos = len(ids)
    assert build_al(orden, 0)[0] == [] and len(build_al(orden, 1.0)[0]) == len(orden)


def test_dps_necesario_crece_con_el_nivel_y_cumple_su_objetivo():
    nave = nave_de([])
    requisitos = [dps_necesario(n, MEDIO, nave, muertes_max=3.0) for n in (1, 2)]
    assert requisitos[0] < requisitos[1]
    x = requisitos[0]
    fuerte = replace(nave, danio=x / (nave.balas * nave.disparos_s))
    assert analizar_nivel(fuerte, 1, MEDIO).muertes(fuerte) == pytest.approx(3.0, abs=0.05)


def test_dps_necesario_dice_imposible_cuando_ni_con_dps_infinito_se_aguanta():
    debil = Nave(salud=1, vidas=1, danio=10, balas=1, disparos_s=3.0, velocidad=4, invulnerable_ms=3000, monedas_pct=0)
    assert math.isinf(dps_necesario(5, MEDIO, debil))


# --- Partida y progresión esperadas ----------------------------------------------------

def test_una_nave_sobrada_completa_la_campana():
    p = jugar(Nave(salud=10_000, vidas=3, danio=10_000, balas=1, disparos_s=4, velocidad=5,
                   invulnerable_ms=3000, monedas_pct=0), MEDIO)
    assert p.victoria and p.nivel_alcanzado == settings.NIVEL_MAX and p.monedas > 0


def test_una_nave_debil_muere_en_el_primer_nivel():
    debil = Nave(salud=10, vidas=1, danio=1, balas=1, disparos_s=1, velocidad=4, invulnerable_ms=3000, monedas_pct=0)
    p = jugar(debil, MEDIO)
    assert not p.victoria and 0 <= p.nivel_alcanzado < 1


def test_las_monedas_de_una_partida_siguen_la_formula_del_juego():
    nave = replace(nave_de([]), monedas_pct=0.5)
    p = jugar(nave, PERFILES["habil"])
    assert p.monedas == int(p.puntos // settings.MONEDAS_PUNTOS * 1.5)


def test_la_progresion_con_un_modelo_facil_termina_en_pocas_partidas():
    facil = replace(MODELO_ACTUAL, danio_x=lambda n: 0.0, vida=lambda c, n: 10)
    pr = progresion(MEDIO, facil)
    assert pr.partidas_hasta_victoria == 1 and pr.curva[0][0] == 1


def test_la_progresion_avisa_si_no_llega():
    imposible = replace(MODELO_ACTUAL, vida=lambda c, n: 10 ** 9)
    pr = progresion(PERFILES["torpe"], imposible)
    assert pr.partidas_hasta_victoria == 0 and len(pr.curva) == balance.MAX_PARTIDAS


def test_la_progresion_compra_lo_mas_barato_primero_y_el_arbol_crece():
    pr = progresion(PERFILES["habil"])
    porcentajes = [p for _, p, _ in pr.curva]
    assert porcentajes == sorted(porcentajes) and porcentajes[0] == 0


# --- El informe -----------------------------------------------------------------------

def test_el_informe_se_imprime_completo(capsys):
    balance.main(["--perfil", "medio", "--builds", "0,100", "--niveles", "--objetivo", "20"])
    salida = capsys.readouterr().out
    for texto in ("SUPUESTOS", "NAVE BASE Y ÁRBOL", "BUILD 0%", "BUILD 100%", "fase desde",
                  "PARTIDA ESPERADA", "PODER QUE EXIGE", "PROGRESIÓN", "Curva del perfil"):
        assert texto in salida, texto


def test_el_informe_con_todos_los_perfiles(capsys):
    balance.main(["--perfil", "todos", "--builds", "0,50"])
    salida = capsys.readouterr().out
    assert all(p.nombre in salida for p in PERFILES.values())


# --- Validación contra el juego real --------------------------------------------------

def test_el_tiempo_de_matar_al_jefe_del_modelo_coincide_con_el_del_juego(juego, rm):
    """Jefe quieto sobre una nave quieta que dispara sin parar: el modelo (acierto 100 %)
    debe dar el mismo tiempo que la partida real, salvo la cuantización a fotogramas."""
    j = juego
    j.jugador.salud_maxima = j.jugador.salud = 10 ** 7
    j.tiempo_proximo_enemigo = math.inf          # sin enemigos normales que intercepten las balas
    jefe = Jefe(rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE), 0, 0, 600, 800, 1, j.jugador)
    jefe.velocidad_x = 0
    jefe.rect.centerx, jefe.rect.y = j.jugador.rect.centerx, 260          # ya en su sitio (no baja)
    j.jefe = jefe
    j.entity_manager.agregar_enemigo(jefe)

    fotogramas = 0
    while j.jefe is not None and fotogramas < 60 * 120:
        j.disparar()
        j.actualizar(DT60)
        fotogramas += 1
    assert j.jefe is None, "el jefe no llegó a morir"

    perfecto = replace(PERFILES["medio"], precision_jefe=1.0)
    esperado = analizar_nivel(nave_de([]), 1, perfecto).ttk_jefe
    assert fotogramas / 60 == pytest.approx(esperado, rel=0.12)           # cadencia por fotogramas (~4 %) + vuelo de la bala


def test_el_ritmo_de_aparicion_de_enemigos_del_modelo_coincide_con_el_del_juego(juego, monkeypatch):
    """Cuántos enemigos salen en la primera fase del nivel 1, contados en la partida real."""
    j = juego
    j.jugador.salud_maxima = j.jugador.salud = 10 ** 7
    aparecidos = []
    original = j.entity_manager.agregar_enemigo
    monkeypatch.setattr(j.entity_manager, "agregar_enemigo", lambda e: (aparecidos.append(e), original(e))[1])

    primera = niveles.definicion_nivel(1).fases[0]
    duracion = (niveles.definicion_nivel(1).fases[1].desde_ms - primera.desde_ms) / 1000
    for _ in range(int(duracion * 60)):
        j.actualizar(DT60)

    lo, hi = niveles.definicion_nivel(1).intervalo_spawn
    esperado = duracion * 1000 / ((lo + hi) / 2)
    assert len(aparecidos) == pytest.approx(esperado, rel=0.12)
    assert all(isinstance(e, EnemigoTipo1) for e in aparecidos)          # la fase 1 solo tiene tipo 1
