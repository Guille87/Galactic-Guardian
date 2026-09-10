"""src/core/settings.py — sanidad de las constantes globales."""
from src.core import settings


def test_ventana_y_bucle():
    assert settings.ANCHO > 0 and settings.ALTO > 0
    assert settings.FPS > 0
    assert isinstance(settings.DEBUG, bool)


def test_generacion_de_enemigos():
    assert settings.GEN_MIN_INICIAL <= settings.GEN_MAX_INICIAL
    assert settings.GEN_MIN_SUELO > 0
    assert settings.GEN_DECREMENTO_NIVEL > 0


def test_fases_de_oleada_ordenadas():
    assert settings.TIEMPO_FASE_2 < settings.TIEMPO_FASE_3 < settings.TIEMPO_JEFE
    assert 0 < settings.TIEMPO_ESCALA_SUELO <= 1
    assert 0 < settings.TIEMPO_ESCALA_NIVEL < 1


def test_balance_de_danio_positivo():
    for nombre in ("DANIO_CONTACTO", "DANIO_BALA_TIPO2", "DANIO_BALA_TIPO3",
                   "DANIO_JEFE_NORMAL", "DANIO_JEFE_RAPIDA"):
        assert getattr(settings, nombre) >= 1


def test_dificultad_lineal_no_exponencial():
    # factores razonables (< 1 por nivel: la salud no se dispara)
    assert 0 < settings.DIFICULTAD_FACTOR_ENEMIGO < 1
    assert 0 < settings.DIFICULTAD_FACTOR_JEFE < 1


def test_radios_de_hitbox():
    for nombre in ("RADIO_JUGADOR", "RADIO_ENEMIGO", "RADIO_JEFE",
                   "RADIO_BALA_JUGADOR", "RADIO_BALA_ENEMIGO"):
        assert getattr(settings, nombre) > 0
    # el jugador tiene el hitbox más pequeño (estilo shmup)
    assert settings.RADIO_JUGADOR < settings.RADIO_ENEMIGO < settings.RADIO_JEFE


def test_movimiento_jugador():
    assert 0 < settings.JUGADOR_SUAVIZADO <= 1
    assert settings.REBOTE_MIN_VX > 0
