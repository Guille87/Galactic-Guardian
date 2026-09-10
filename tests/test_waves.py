"""src/managers/waves.py — director de oleadas."""
import pytest

from src.core import settings
from src.entities.enemies import EnemigoTipo1, Jefe
from src.managers.waves import WaveManager


@pytest.fixture
def wave(rm, audio):
    return WaveManager(rm, audio, settings.ANCHO, settings.ALTO)


def test_escala_nivel(wave):
    assert wave._escala_nivel(1) == 1.0
    assert wave._escala_nivel(2) < 1.0
    assert wave._escala_nivel(3) < wave._escala_nivel(2)
    # nunca por debajo del suelo
    assert wave._escala_nivel(50) == settings.TIEMPO_ESCALA_SUELO


def test_fase_1_solo_tipo1(wave):
    tipo, _, es_jefe = wave._obtener_config_enemigo(0, nivel=1)
    assert tipo is EnemigoTipo1
    assert es_jefe is False


def test_fase_2_incluye_tipo2(wave):
    # justo pasado el umbral de fase 2 del nivel 1
    tipos = {wave._obtener_config_enemigo(settings.TIEMPO_FASE_2 + 100, 1)[0] for _ in range(40)}
    assert len(tipos) >= 2       # ya no es solo Tipo1


def test_fase_jefe(wave, jugador, monkeypatch):
    import pygame
    reloj = {"t": 100_000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: reloj["t"])
    umbral = settings.TIEMPO_JEFE * wave._escala_nivel(1)

    # 1ª llamada tras el umbral: arranca la espera de 5 s y aún no aparece
    assert wave._obtener_config_enemigo(umbral + 100, nivel=1)[2] is False
    # pasados los 5 s de espera, sale el jefe
    reloj["t"] += wave.tiempo_espera_jefe + 100
    tipo, _, es_jefe = wave._obtener_config_enemigo(umbral + 100, nivel=1)
    assert es_jefe is True
    assert tipo is Jefe


def test_jefe_aparece_antes_en_niveles_altos(wave):
    assert (settings.TIEMPO_JEFE * wave._escala_nivel(3)
            < settings.TIEMPO_JEFE * wave._escala_nivel(1))


def test_spawn_enemigo_devuelve_instancia(wave, jugador):
    e = wave.spawn_enemigo(0, jugador, nivel=1)
    assert isinstance(e, EnemigoTipo1)
    assert 0 <= e.rect.x <= settings.ANCHO
