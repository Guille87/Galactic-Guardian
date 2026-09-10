"""src/managers/waves.py — director de oleadas."""
import pytest

from src.core import settings
from src.entities.enemies import EnemigoTipo1, Jefe
from src.managers.waves import WaveManager


@pytest.fixture
def wave(rm, audio):
    return WaveManager(rm, audio, settings.ANCHO, settings.ALTO)


def _config(wave, tiempo_nivel, nivel, tiempo_juego=None):
    """`_obtener_config_enemigo(tiempo_nivel, tiempo_juego, nivel)`."""
    return wave._obtener_config_enemigo(tiempo_nivel, tiempo_juego if tiempo_juego is not None else tiempo_nivel, nivel)


def test_escala_nivel(wave):
    assert wave._escala_nivel(1) == 1.0
    assert wave._escala_nivel(2) < 1.0
    assert wave._escala_nivel(3) < wave._escala_nivel(2)
    assert wave._escala_nivel(50) == settings.TIEMPO_ESCALA_SUELO


def test_fase_1_solo_tipo1(wave):
    tipo, _, es_jefe = _config(wave, 0, nivel=1)
    assert tipo is EnemigoTipo1
    assert es_jefe is False


def test_fase_2_incluye_tipo2(wave):
    tipos = {_config(wave, settings.TIEMPO_FASE_2 + 100, 1)[0] for _ in range(40)}
    assert len(tipos) >= 2       # ya no es solo Tipo1


def test_fase_jefe_espera_y_aparece(wave):
    """El jefe aparece tras TIEMPO_ESPERA_JEFE medido con el reloj de juego."""
    umbral = settings.TIEMPO_JEFE * wave._escala_nivel(1)
    t0 = 100_000

    # 1ª llamada: arranca la espera, aún no aparece
    assert _config(wave, umbral + 100, 1, tiempo_juego=t0)[2] is False
    # pasada la espera (reloj de juego avanzado)
    tipo, _, es_jefe = _config(wave, umbral + 100, 1, tiempo_juego=t0 + wave.tiempo_espera_jefe + 1)
    assert es_jefe is True and tipo is Jefe


def test_pausa_congela_la_espera_del_jefe(wave):
    """Si el reloj de juego no avanza (pausa), la espera del jefe no progresa."""
    umbral = settings.TIEMPO_JEFE * wave._escala_nivel(1)
    _config(wave, umbral + 100, 1, tiempo_juego=100_000)          # arranca la espera
    # mismas llamadas con el mismo tiempo_juego (como en pausa): nunca aparece
    for _ in range(5):
        assert _config(wave, umbral + 100, 1, tiempo_juego=100_000)[2] is False


def test_jefe_aparece_antes_en_niveles_altos(wave):
    assert (settings.TIEMPO_JEFE * wave._escala_nivel(3)
            < settings.TIEMPO_JEFE * wave._escala_nivel(1))


def test_spawn_enemigo_devuelve_instancia(wave, jugador):
    e = wave.spawn_enemigo(0, 0, jugador, nivel=1)
    assert isinstance(e, EnemigoTipo1)
    assert 0 <= e.rect.x <= settings.ANCHO
