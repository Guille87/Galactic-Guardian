"""src/core/controles.py — lógica pura del mapa de teclas reasignable."""
import pygame

from src.core import controles


def test_todas_las_acciones_tienen_etiqueta_y_valor_por_defecto():
    assert set(controles.ETIQUETAS) == set(controles.ACCIONES)
    assert set(controles.POR_DEFECTO) == set(controles.ACCIONES)


def test_por_defecto_coincide_con_lo_que_era_fijo_antes():
    assert controles.POR_DEFECTO["arriba"] == pygame.K_w
    assert controles.POR_DEFECTO["abajo"] == pygame.K_s
    assert controles.POR_DEFECTO["izquierda"] == pygame.K_a
    assert controles.POR_DEFECTO["derecha"] == pygame.K_d
    assert controles.POR_DEFECTO["disparar"] == pygame.K_SPACE
    assert controles.POR_DEFECTO["pausa"] == pygame.K_p


def test_nombre_tecla_espacio_legible():
    assert controles.nombre_tecla(pygame.K_SPACE) == "Espacio"


def test_nombre_tecla_letra():
    assert controles.nombre_tecla(pygame.K_w) == "W"
