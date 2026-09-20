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


# --- Hojas de sprites ---------------------------------------------------------

import pytest


@pytest.fixture
def hoja_de_prueba(rm, tmp_path):
    """Hoja sintética de 3 columnas x 2 filas con celdas de 10x8, cada una de un color."""
    colores = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]
    hoja = pygame.Surface((30, 16), pygame.SRCALPHA)
    for n, color in enumerate(colores):
        hoja.fill((*color, 255), ((n % 3) * 10, (n // 3) * 8, 10, 8))
    ruta = tmp_path / "hoja.png"
    pygame.image.save(hoja, str(ruta))
    yield ruta, colores
    for nombre in [n for n in rm.spritesheets if n.startswith("_prueba")]:
        del rm.spritesheets[nombre]
    for clave in [k for k in rm.scaled_resources if k.startswith("_prueba")]:
        del rm.scaled_resources[clave]


def test_la_hoja_se_corta_en_orden_izquierda_derecha_y_arriba_abajo(rm, hoja_de_prueba):
    ruta, colores = hoja_de_prueba
    rm.load_spritesheet("_prueba", str(ruta), columnas=3, filas=2)
    frames = rm.get_frames("_prueba")
    assert len(frames) == 6
    assert all(f.get_size() == (10, 8) for f in frames)
    assert [tuple(f.get_at((5, 4)))[:3] for f in frames] == colores


def test_cantidad_ignora_las_celdas_vacias_del_final(rm, hoja_de_prueba):
    ruta, colores = hoja_de_prueba
    rm.load_spritesheet("_prueba_cant", str(ruta), columnas=3, filas=2, cantidad=4)
    assert [tuple(f.get_at((5, 4)))[:3] for f in rm.get_frames("_prueba_cant")] == colores[:4]


def test_una_hoja_que_no_se_divide_en_celdas_iguales_da_error(rm, hoja_de_prueba):
    ruta, _ = hoja_de_prueba                                       # 30x16
    with pytest.raises(ValueError):
        rm.load_spritesheet("_prueba_mal", str(ruta), columnas=4, filas=2)      # 30 no se divide en 4
    with pytest.raises(ValueError):
        rm.load_spritesheet("_prueba_mal", str(ruta), columnas=0, filas=2)
    assert "_prueba_mal" not in rm.spritesheets


def test_pedir_mas_fotogramas_de_los_que_caben_da_error(rm, hoja_de_prueba):
    ruta, _ = hoja_de_prueba
    for cantidad in (0, 7):
        with pytest.raises(ValueError):
            rm.load_spritesheet("_prueba_mal", str(ruta), columnas=3, filas=2, cantidad=cantidad)


def test_get_frames_devuelve_una_lista_nueva_cada_vez(rm, hoja_de_prueba):
    ruta, _ = hoja_de_prueba
    rm.load_spritesheet("_prueba_lista", str(ruta), columnas=3, filas=2)
    lista = rm.get_frames("_prueba_lista")
    lista.clear()                                                   # tocar la lista no toca la hoja
    assert len(rm.get_frames("_prueba_lista")) == 6


def test_get_frames_escalados_se_cachean(rm, hoja_de_prueba):
    ruta, colores = hoja_de_prueba
    rm.load_spritesheet("_prueba_esc", str(ruta), columnas=3, filas=2)
    a = rm.get_frames("_prueba_esc", (20, 16))
    b = rm.get_frames("_prueba_esc", (20, 16))
    assert all(f.get_size() == (20, 16) for f in a)
    assert all(x is y for x, y in zip(a, b))                        # mismos objetos: vienen de caché
    assert [tuple(f.get_at((10, 8)))[:3] for f in a] == colores     # el escalado conserva el contenido


def test_hoja_desconocida_devuelve_lista_vacia(rm):
    assert rm.get_frames("no_existe") == []
    assert rm.get_frames("no_existe", (10, 10)) == []


def test_la_hoja_de_la_explosion_tiene_11_fotogramas_distintos(rm):
    frames = rm.get_frames("explosion")
    assert len(frames) == 11 and all(f.get_size() == (128, 128) for f in frames)
    assert len({pygame.image.tobytes(f, "RGBA") for f in frames}) == 11      # ninguno repetido ni vacío
