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


def test_campana_tiene_al_menos_un_nivel():
    assert settings.NIVEL_MAX >= 1


def test_gen_intervalo_para_nivel_decrece_y_no_baja_del_suelo():
    minimo1, maximo1 = settings.gen_intervalo_para_nivel(1)
    assert (minimo1, maximo1) == (settings.GEN_MIN_INICIAL, settings.GEN_MAX_INICIAL)

    minimo2, maximo2 = settings.gen_intervalo_para_nivel(2)
    assert minimo2 < minimo1 and maximo2 < maximo1

    # en un nivel muy alto, nunca por debajo del suelo
    minimo_alto, maximo_alto = settings.gen_intervalo_para_nivel(50)
    assert minimo_alto == settings.GEN_MIN_SUELO
    assert maximo_alto == settings.GEN_MIN_SUELO

    # es una función pura: mismo resultado que el decremento manual iterado
    minimo_iterado, maximo_iterado = settings.GEN_MIN_INICIAL, settings.GEN_MAX_INICIAL
    for _ in range(1, 4):
        minimo_iterado = max(settings.GEN_MIN_SUELO, minimo_iterado - settings.GEN_DECREMENTO_NIVEL)
        maximo_iterado = max(settings.GEN_MIN_SUELO, maximo_iterado - settings.GEN_DECREMENTO_NIVEL)
    assert settings.gen_intervalo_para_nivel(4) == (minimo_iterado, maximo_iterado)


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
