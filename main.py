import pygame
import os

from juego.menu import crear_pantalla, mostrar_menu
from resources.resource_manager import ResourceManager
from juego.configuracion import RECURSOS, SONIDOS, EXPLOSIONES, DIR_BASE


def cargar_activos_del_juego(rm):
    """Carga todas las imágenes y sonidos en el ResourceManager."""
    # Cargar Imágenes
    for nombre, ruta in {** RECURSOS, ** EXPLOSIONES}.items():
        rm.load_image(nombre, os.path.join(DIR_BASE, ruta))

    # Cargar Sonidos
    for nombre, ruta in SONIDOS.items():
        rm.load_sound(nombre, os.path.join(DIR_BASE, ruta))


def main():
    # Inicializar Pygame
    pygame.init()

    # Crear la pantalla
    pantalla = crear_pantalla()

    # Establecer el icono de la ventana
    icono_path = os.path.join(DIR_BASE, 'imagenes/favicon.ico')
    if os.path.exists(icono_path):
        pygame.display.set_icon(pygame.image.load(icono_path))

    # Gestión de recursos
    resource_manager = ResourceManager()
    cargar_activos_del_juego(resource_manager)

    # Mostrar el menú
    mostrar_menu(pantalla)


if __name__ == "__main__":
    main()
