"""src/core/niveles.py — coherencia de la tabla de niveles."""
import pytest

from src.core import config, settings
from src.core.niveles import NIVELES, definicion_nivel
from src.entities.enemies import EnemigoBase, Jefe


def test_hay_un_nivel_por_cada_nivel_de_la_campana():
    assert len(NIVELES) == settings.NIVEL_MAX


@pytest.mark.parametrize("n", range(1, len(NIVELES) + 1))
def test_definicion_coherente(n):
    d = definicion_nivel(n)
    desdes = [f.desde_ms for f in d.fases]
    assert desdes[0] == 0
    assert desdes == sorted(set(desdes))                 # ordenadas y sin repetir
    assert d.tiempo_jefe_ms > desdes[-1]                 # el jefe llega tras la última fase
    assert d.espera_jefe_ms >= 0
    minimo, maximo = d.intervalo_spawn
    assert 0 < minimo <= maximo
    assert issubclass(d.jefe, Jefe)
    for f in d.fases:
        assert f.enemigos and all(issubclass(e, EnemigoBase) for e in f.enemigos)


@pytest.mark.parametrize("n", range(1, len(NIVELES) + 1))
def test_recursos_y_musica_existen(n):
    d = definicion_nivel(n)
    assert d.musica in config.MUSICA and d.musica_jefe in config.MUSICA
    clases = {e for f in d.fases for e in f.enemigos} | {d.jefe}
    assert all(c.RECURSO in config.RECURSOS for c in clases)


def test_los_niveles_altos_son_mas_exigentes():
    primero, ultimo = NIVELES[0], NIVELES[-1]
    assert ultimo.tiempo_jefe_ms < primero.tiempo_jefe_ms
    assert ultimo.intervalo_spawn[0] <= primero.intervalo_spawn[0]


def test_nivel_fuera_de_rango_repite_los_extremos():
    assert definicion_nivel(0) is NIVELES[0]
    assert definicion_nivel(len(NIVELES) + 10) is NIVELES[-1]
