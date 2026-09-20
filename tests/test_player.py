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


@pytest.mark.parametrize("tipo,n", [("simple", 1), ("doble", 2), ("triple", 3)])
def test_numero_de_balas_por_tipo(jugador, imagen_bala, tipo, n):
    jugador.tipo_disparo = tipo
    jugador.ultimo_disparo = -99999
    assert len(jugador.disparar(0, imagen_bala)) == n


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
    jugador.tipo_disparo = "triple"
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
    assert jugador.velocidad == 4
    assert jugador.tipo_disparo == "simple"
    assert jugador.invulnerable is False
    assert jugador.tiempo_invulnerable == 0
    assert jugador.ultimo_disparo == 0
    assert jugador.rect.centerx == 300 and jugador.rect.bottom == 790
    assert jugador._resto.length() == 0
    assert jugador._ultimo_desplazamiento.length() == 0


# --- Lecturas para el HUD ---

def test_cadencia_visual(jugador):
    jugador.cadencia_disparo = 250
    assert jugador.obtener_cadencia_visual() == 4.0
