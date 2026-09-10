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
    jugador.recibir_danio(2)
    assert jugador.salud == jugador.salud_maxima - 2


def test_recibir_danio_no_baja_de_cero(jugador):
    jugador.recibir_danio(999)
    assert jugador.salud == 0


def test_invulnerable_ignora_danio(jugador):
    jugador.invulnerable = True
    assert jugador.recibir_danio(3) is False
    assert jugador.salud == jugador.salud_maxima


def test_curar_no_pasa_del_maximo(jugador):
    jugador.salud = 1
    jugador.curar(999)
    assert jugador.salud == jugador.salud_maxima


def test_reducir_vidas_no_baja_de_cero(jugador):
    jugador.reducir_vidas(999)
    assert jugador.vidas == 0


# --- Mejoras ---

def test_mejorar_danio_sube_hasta_max_y_luego_evoluciona(jugador):
    while jugador.danio < jugador.danio_maximo:
        jugador.mejorar_danio()
    assert jugador.danio == jugador.danio_maximo
    assert jugador.tipo_disparo == "simple"
    jugador.mejorar_danio()
    assert jugador.tipo_disparo == "doble"
    jugador.mejorar_danio()
    assert jugador.tipo_disparo == "triple"


def test_mejorar_velocidad_topa_en_max(jugador):
    for _ in range(20):
        jugador.mejorar_velocidad(1)
    assert jugador.velocidad == jugador.velocidad_maxima


def test_mejorar_cadencia_topa_en_min(jugador):
    for _ in range(50):
        jugador.mejorar_cadencia(50)
    assert jugador.cadencia_disparo == jugador.cadencia_disparo_maxima


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


def test_actualizar_pausa_desplaza_cadencia(jugador):
    jugador.ultimo_disparo = 1000
    jugador.actualizar_pausa(5000)
    assert jugador.ultimo_disparo == 6000


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


# --- Lecturas para el HUD ---

def test_cadencia_visual(jugador):
    jugador.cadencia_disparo = 250
    assert jugador.obtener_cadencia_visual() == 4.0
