"""src/core/resources.py — ResourceManager (singleton + cachés)."""
import pygame

from src.core.resources import ResourceManager


def test_es_singleton(rm):
    assert ResourceManager() is rm


def test_get_image_devuelve_surface(rm):
    img = rm.get_image("jugador")
    assert isinstance(img, pygame.Surface)


def test_get_image_scaled_cachea_por_tamano(rm):
    a = rm.get_image_scaled("enemigo1", (48, 48))
    b = rm.get_image_scaled("enemigo1", (48, 48))
    assert a is b                                   # mismo objeto: viene de caché
    c = rm.get_image_scaled("enemigo1", (32, 32))
    assert c is not a
    assert c.get_size() == (32, 32)


def test_get_image_rotated_cachea_por_angulo(rm):
    a = rm.get_image_rotated("bala_enemigo", (24, 24), 90)
    b = rm.get_image_rotated("bala_enemigo", (24, 24), 90)
    assert a is b
    c = rm.get_image_rotated("bala_enemigo", (24, 24), 45)
    assert c is not a


def test_recurso_desconocido_devuelve_none(rm):
    assert rm.get_image_scaled("no_existe", (10, 10)) is None
    assert rm.get_image("no_existe") is None


def test_musica_cargada_como_bytes(rm):
    datos = rm.get_music_data("rain_of_lasers")
    assert isinstance(datos, bytes) and len(datos) > 1000
    assert datos[:4] == b"OggS"                 # cabecera OGG
    # la música NO se carga como Sound (se decodifica al vuelo)
    assert rm.get_sound("rain_of_lasers") is None


def test_get_sound_para_efectos(rm):
    assert rm.get_sound("laser_gun") is not None
