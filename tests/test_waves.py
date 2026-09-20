"""src/managers/waves.py — director de oleadas (lee la definición del nivel)."""
import pytest

from src.core import settings
from src.core.niveles import definicion_nivel
from src.entities.enemies import EnemigoTipo1, EnemigoTipo2, Jefe
from src.managers.waves import WaveManager


@pytest.fixture
def wave(rm, audio):
    return WaveManager(rm, audio, settings.ANCHO, settings.ALTO)


def _config(wave, tiempo_nivel, nivel, tiempo_juego=None):
    """`_obtener_config_enemigo(tiempo_nivel, tiempo_juego, nivel)`."""
    return wave._obtener_config_enemigo(tiempo_nivel, tiempo_juego if tiempo_juego is not None else tiempo_nivel, nivel)


def test_fase_1_solo_tipo1(wave):
    tipo, recurso, es_jefe = _config(wave, 0, nivel=1)
    assert tipo is EnemigoTipo1
    assert recurso == "enemigo1"
    assert es_jefe is False


def test_fase_2_incluye_tipo2(wave):
    desde = definicion_nivel(1).fases[1].desde_ms
    tipos = {_config(wave, desde + 100, 1)[0] for _ in range(40)}
    assert tipos == {EnemigoTipo1, EnemigoTipo2}


def test_la_fase_cambia_justo_en_su_umbral(wave):
    desde = definicion_nivel(1).fases[1].desde_ms
    assert {_config(wave, desde - 1, 1)[0] for _ in range(40)} == {EnemigoTipo1}
    assert len({_config(wave, desde, 1)[0] for _ in range(40)}) == 2


def test_fase_jefe_espera_y_aparece(wave):
    """El jefe aparece tras `espera_jefe_ms` medido con el reloj de juego."""
    d = definicion_nivel(1)
    t0 = 100_000

    # 1ª llamada: arranca la espera, aún no aparece
    assert _config(wave, d.tiempo_jefe_ms + 100, 1, tiempo_juego=t0)[2] is False
    # pasada la espera (reloj de juego avanzado)
    tipo, recurso, es_jefe = _config(wave, d.tiempo_jefe_ms + 100, 1, tiempo_juego=t0 + d.espera_jefe_ms + 1)
    assert es_jefe is True and tipo is Jefe and recurso == "jefe1"


def test_fase_jefe_cambia_la_musica_del_nivel(wave, audio):
    d = definicion_nivel(1)
    audio.reproducir_musica(d.musica)
    _config(wave, d.tiempo_jefe_ms + 100, 1, tiempo_juego=100_000)
    assert audio.pista_actual == d.musica_jefe


def test_no_hay_mas_enemigos_una_vez_generado_el_jefe(wave):
    d = definicion_nivel(1)
    wave.jefe_generado = True
    assert _config(wave, d.tiempo_jefe_ms + 100, 1) == (None, None, False)


def test_pausa_congela_la_espera_del_jefe(wave):
    """Si el reloj de juego no avanza (pausa), la espera del jefe no progresa."""
    d = definicion_nivel(1)
    _config(wave, d.tiempo_jefe_ms + 100, 1, tiempo_juego=100_000)          # arranca la espera
    # mismas llamadas con el mismo tiempo_juego (como en pausa): nunca aparece
    for _ in range(5):
        assert _config(wave, d.tiempo_jefe_ms + 100, 1, tiempo_juego=100_000)[2] is False


def test_cada_nivel_usa_su_propia_definicion(wave):
    """El jefe del nivel 3 llega antes que el del 1: no comparten umbral."""
    d1, d3 = definicion_nivel(1), definicion_nivel(3)
    t = d3.tiempo_jefe_ms + 100
    assert t < d1.tiempo_jefe_ms
    assert _config(wave, t, 1)[2] is False                        # nivel 1: aún fase normal
    assert _config(wave, t, 3, tiempo_juego=100_000)[0] is None   # nivel 3: ya espera al jefe


def test_spawn_enemigo_devuelve_instancia(wave, jugador):
    e = wave.spawn_enemigo(0, 0, jugador, nivel=1)
    assert isinstance(e, EnemigoTipo1)
    assert 0 <= e.rect.x <= settings.ANCHO


def test_spawn_del_jefe_devuelve_un_jefe(wave, jugador):
    d = definicion_nivel(1)
    wave.spawn_enemigo(d.tiempo_jefe_ms + 100, 100_000, jugador, nivel=1)      # arranca la espera
    jefe = wave.spawn_enemigo(d.tiempo_jefe_ms + 100, 100_000 + d.espera_jefe_ms + 1, jugador, nivel=1)
    assert isinstance(jefe, Jefe)
