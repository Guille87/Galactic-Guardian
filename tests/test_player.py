"""src/entities/player.py — Jugador (stats, disparo, movimiento)."""
from collections import defaultdict

import pygame
import pytest

from src.entities.bullet import Bala

DT60 = 1.0 / 60.0


@pytest.fixture
def imagen_bala(rm):
    return rm.get_image_rotated("bala_jugador1", Bala.TAMANO, Bala.ANGULO)


def _teclas(*pulsadas):
    t = defaultdict(bool)
    for k in pulsadas:
        t[k] = True
    return t


# --- Salud / vidas ---

def test_recibir_danio(jugador):
    jugador.recibir_danio(20)
    assert jugador.salud == jugador.salud_maxima - 20


def test_recibir_danio_no_baja_de_cero(jugador):
    jugador.recibir_danio(999)
    assert jugador.salud == 0


def test_invulnerable_ignora_danio(jugador):
    jugador.invulnerable = True
    assert jugador.recibir_danio(30) is False
    assert jugador.salud == jugador.salud_maxima


def test_curar_no_pasa_del_maximo(jugador):
    jugador.salud = 1
    jugador.curar(999)
    assert jugador.salud == jugador.salud_maxima


def test_reducir_vidas_no_baja_de_cero(jugador):
    jugador.reducir_vidas(999)
    assert jugador.vidas == 0


# --- Disparo ---

def test_disparar_respeta_la_cadencia(jugador, imagen_bala):
    assert len(jugador.disparar(1000, imagen_bala)) == 1
    assert jugador.disparar(1000 + jugador.cadencia_disparo - 1, imagen_bala) == []
    assert len(jugador.disparar(1000 + jugador.cadencia_disparo + 1, imagen_bala)) == 1


@pytest.mark.parametrize("balas", [1, 2, 3])
def test_numero_de_balas_por_disparo(jugador, imagen_bala, balas):
    jugador.balas_por_disparo = balas
    jugador.ultimo_disparo = -99999
    assert len(jugador.disparar(0, imagen_bala)) == balas


def test_las_balas_multiples_salen_separadas_y_centradas(jugador, imagen_bala):
    for balas in (2, 3):
        jugador.balas_por_disparo = balas
        jugador.ultimo_disparo = -99999
        xs = sorted(b.rect.centerx for b in jugador.disparar(0, imagen_bala))
        assert len(set(xs)) == balas and sum(xs) / balas == pytest.approx(jugador.rect.centerx)


def test_a_60_fps_los_disparos_por_segundo_son_los_del_dato(jugador, imagen_bala):
    """4 disparos/s = uno cada 15 fotogramas: sin que la suma de tiempos en coma
    flotante retrase cada disparo un fotograma (que serían 3,75 disparos/s)."""
    for disparos_s in (4.0, 5.0, 6.0):
        jugador.disparos_s = disparos_s
        jugador.ultimo_disparo = 0
        tiempo, disparos = 0.0, 0
        for _ in range(60 * 10):                                  # 10 segundos de juego
            tiempo += 1000 / 60
            disparos += len(jugador.disparar(tiempo, imagen_bala))
        assert disparos == pytest.approx(disparos_s * 10, abs=1), disparos_s


def test_los_disparos_por_segundo_se_convierten_a_milisegundos(jugador):
    jugador.disparos_s = 4.0
    assert jugador.cadencia_disparo == 250
    jugador.disparos_s = 8.0
    assert jugador.cadencia_disparo == 125


def test_la_nave_base_es_la_acordada(jugador):
    assert (jugador.velocidad, jugador.disparos_s, jugador.balas_por_disparo, jugador.danio,
            jugador.salud_maxima, jugador.vidas) == (5, 4.0, 1, 10, 50, 3)


def test_los_topes_de_la_nave(jugador):
    c = jugador.CONFIG
    assert (c["vel_max"], c["disparos_max"], c["balas_max"], c["danio_max"]) == (6, 8.0, 3, 30)


def test_invulnerabilidad_expira_con_el_reloj_de_juego(jugador):
    jugador.invulnerable = True
    jugador.tiempo_invulnerable = 3000
    jugador.update(dt=1 / 60, tiempo_juego=2999)
    assert jugador.invulnerable is True          # aún no
    jugador.update(dt=1 / 60, tiempo_juego=3001)
    assert jugador.invulnerable is False


# --- Movimiento ---

def test_diagonal_normalizada(jugador):
    jugador.velocidad = 5
    jugador.rect.center = (300, 400)
    p0 = pygame.Vector2(jugador.rect.center)
    for _ in range(20):
        jugador.mover(_teclas(pygame.K_LEFT, pygame.K_UP), pygame.display.get_surface(), DT60)
    recorrido = (pygame.Vector2(jugador.rect.center) - p0).length() / 20
    assert 4.5 <= recorrido <= 5.5      # ~= velocidad, no velocidad * raíz(2)


def test_no_se_sale_de_la_pantalla(jugador):
    for _ in range(300):
        jugador.mover(_teclas(pygame.K_RIGHT, pygame.K_DOWN), pygame.display.get_surface(), DT60)
    assert jugador.rect.right <= 600
    assert jugador.rect.bottom <= 800


def test_mover_usa_las_flechas_aunque_se_reasigne_otra_tecla(jugador):
    """Las flechas son fijas: siguen funcionando pase lo que pase con el mapa."""
    mapa = {"arriba": pygame.K_i, "abajo": pygame.K_k,
            "izquierda": pygame.K_j, "derecha": pygame.K_l,
            "disparar": pygame.K_SPACE, "pausa": pygame.K_p}
    x0 = jugador.rect.centerx
    jugador.mover(_teclas(pygame.K_RIGHT), pygame.display.get_surface(), DT60, mapa)
    assert jugador.rect.centerx > x0


def test_mover_respeta_la_tecla_reasignada(jugador):
    """Si "derecha" se reasigna a L, pulsar L también mueve (no solo D)."""
    mapa = {"arriba": pygame.K_i, "abajo": pygame.K_k,
            "izquierda": pygame.K_j, "derecha": pygame.K_l,
            "disparar": pygame.K_SPACE, "pausa": pygame.K_p}
    x0 = jugador.rect.centerx
    jugador.mover(_teclas(pygame.K_l), pygame.display.get_surface(), DT60, mapa)
    assert jugador.rect.centerx > x0


def test_mover_ya_no_responde_a_la_tecla_por_defecto_si_se_reasigno(jugador):
    """Tras reasignar "derecha" a L, D deja de mover (solo la flecha sigue fija)."""
    mapa = {"arriba": pygame.K_i, "abajo": pygame.K_k,
            "izquierda": pygame.K_j, "derecha": pygame.K_l,
            "disparar": pygame.K_SPACE, "pausa": pygame.K_p}
    x0 = jugador.rect.centerx
    jugador.mover(_teclas(pygame.K_d), pygame.display.get_surface(), DT60, mapa)
    assert jugador.rect.centerx == x0


# --- Reinicio in situ ---

def test_reiniciar_restaura_estado(jugador):
    jugador.danio = 30
    jugador.velocidad = 6
    jugador.balas_por_disparo = 3
    jugador.disparos_s = 7.0
    jugador.regen_s = 2.0
    jugador.vidas = 1
    jugador.salud = 1
    jugador.invulnerable = True
    jugador.tiempo_invulnerable = 5000
    jugador.ultimo_disparo = 4321
    jugador.rect.topleft = (0, 0)
    jugador._resto.update(0.4, 0.3)

    jugador.reiniciar(600, 800)

    assert jugador.vidas == jugador.CONFIG["vidas_init"]
    assert jugador.salud == jugador.salud_maxima
    assert jugador.danio == jugador.CONFIG["danio_base"]
    assert jugador.velocidad == jugador.CONFIG["vel_base"]
    assert (jugador.balas_por_disparo, jugador.disparos_s, jugador.regen_s) == (1, 4.0, 0.0)
    assert jugador.invulnerable is False
    assert jugador.tiempo_invulnerable == 0
    assert jugador.ultimo_disparo == 0
    assert jugador.rect.centerx == 300 and jugador.rect.bottom == 790
    assert jugador._resto.length() == 0
    assert jugador._ultimo_desplazamiento.length() == 0


# --- Lecturas para el HUD ---

def test_cadencia_visual(jugador):
    jugador.disparos_s = 4.0
    assert jugador.obtener_cadencia_visual() == 4.0
    assert jugador.obtener_cadencia_max_visual() == 8.0


# --- Regeneración ------------------------------------------------------------------------

def _regenerar(jugador, segundos, desde_ms=10_000):
    t = desde_ms
    for _ in range(int(segundos * 60)):
        t += 1000 / 60
        jugador.update(dt=1 / 60, tiempo_juego=t)
    return t


def test_sin_la_mejora_no_se_regenera(jugador):
    jugador.salud = 10
    _regenerar(jugador, 30)
    assert jugador.salud == 10


def test_con_regeneracion_se_recupera_salud_tras_unos_segundos_sin_dano(jugador):
    jugador.regen_s = 0.5
    jugador.salud = 10
    jugador.marcar_golpe(10_000)
    _regenerar(jugador, 2.9)                                       # aún en la espera de 3 s
    assert jugador.salud == 10
    _regenerar(jugador, 10, desde_ms=10_000 + 3000)                # ya regenera: 0,5 por segundo
    assert jugador.salud == pytest.approx(15, abs=0.2)


def test_un_golpe_reinicia_la_espera_de_la_regeneracion(jugador):
    jugador.regen_s = 1.0
    jugador.salud = 10
    jugador.marcar_golpe(10_000)
    t = _regenerar(jugador, 5, desde_ms=10_000)
    salud = jugador.salud
    assert salud > 10
    jugador.marcar_golpe(t)                                        # otro golpe
    _regenerar(jugador, 2.9, desde_ms=t)
    assert jugador.salud == salud                                  # vuelve a esperar


def test_la_regeneracion_no_pasa_de_la_salud_maxima_ni_revive(jugador):
    jugador.regen_s = 50.0
    jugador.salud = jugador.salud_maxima - 1
    _regenerar(jugador, 5)
    assert jugador.salud == jugador.salud_maxima
    jugador.salud = 0
    _regenerar(jugador, 5)
    assert jugador.salud == 0                                      # con 0 ya se perdió la vida: no regenera


# --- De dónde salen las balas ------------------------------------------------------------------

def _origenes(jugador, imagen_bala, balas):
    jugador.balas_por_disparo = balas
    jugador.ultimo_disparo = -99999
    return [(b.rect.centerx - jugador.rect.centerx, b.rect.centery - jugador.rect.top)
            for b in jugador.disparar(0, imagen_bala)]


def test_con_una_bala_sale_del_morro(jugador, imagen_bala):
    assert _origenes(jugador, imagen_bala, 1) == [(0, 10)]


def test_con_dos_balas_salen_de_los_canones_de_las_alas_y_no_del_centro(jugador, imagen_bala):
    (xi, _), (xd, _) = _origenes(jugador, imagen_bala, 2)
    assert xi == -xd < 0 and abs(xi) >= 15                       # una a cada lado, bien separadas


def test_con_tres_balas_salen_los_canones_y_el_morro(jugador, imagen_bala):
    origenes = _origenes(jugador, imagen_bala, 3)
    assert sorted(x for x, _ in origenes) == [-20, 0, 20]
    assert set(_origenes(jugador, imagen_bala, 2)) <= set(origenes)   # los cañones son los mismos que con dos


def test_los_canones_de_las_alas_quedan_algo_mas_atras_que_el_morro(jugador, imagen_bala):
    lados = [dy for dx, dy in _origenes(jugador, imagen_bala, 3) if dx]
    centro = [dy for dx, dy in _origenes(jugador, imagen_bala, 3) if not dx]
    assert all(dy > centro[0] for dy in lados)


def test_los_canones_estan_dentro_de_la_nave(jugador, imagen_bala):
    ancho = jugador.rect.width
    assert all(abs(x) < ancho / 2 for x, _ in _origenes(jugador, imagen_bala, 3))
