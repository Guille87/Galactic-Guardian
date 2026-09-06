import sys
import os

import pygame

from src.ui.menu import MenuManager
from src.core.engine import Juego
from src.core.audio import AudioManager
from src.core.resources import ResourceManager
from src.core.config import RECURSOS, SONIDOS, EXPLOSIONES, DIR_ASSETS, cargar_configuracion
from src.ui.scoreboard import SistemaClasificacion


def cargar_activos_del_juego(rm):
    """Carga todas las imágenes y sonidos en el ResourceManager."""
    # Cargar Imágenes
    for nombre, ruta in {** RECURSOS, ** EXPLOSIONES}.items():
        rm.load_image(nombre, os.path.join(DIR_ASSETS, ruta))

    # Cargar Sonidos
    for nombre, ruta in SONIDOS.items():
        rm.load_sound(nombre, os.path.join(DIR_ASSETS, ruta))


def main():
    # Inicializar Pygame
    pygame.init()

    # Crear la pantalla
    pantalla = pygame.display.set_mode((600, 800))

    # Establecer el icono de la ventana
    icono_path = os.path.join(DIR_ASSETS, 'imagenes/favicon.ico')
    if os.path.exists(icono_path):
        pygame.display.set_icon(pygame.image.load(icono_path))

    # Gestión de recursos
    resource_manager = ResourceManager()
    cargar_activos_del_juego(resource_manager)

    # Cargar configuración de usuario (Volúmenes guardados)
    vol_musica, vol_efectos = cargar_configuracion()

    # Un único AudioManager compartido entre el menú y la partida
    audio_manager = AudioManager(resource_manager, vol_musica, vol_efectos)

    sistema_clasificacion = SistemaClasificacion()

    # El menú es persistente; se reutiliza cada vez que se vuelve a él
    menu = MenuManager(pantalla, resource_manager, audio_manager, sistema_clasificacion)

    # --- Máquina de estados de alto nivel ---
    # Cada pantalla (menú / juego) devuelve el siguiente estado en lugar de
    # instanciar la otra o llamar a sys.exit() por su cuenta.
    estado = "MENU"
    while estado != "SALIR":
        if estado == "MENU":
            estado = menu.ejecutar()  # -> "JUGAR" o "SALIR"
        elif estado == "JUGAR":
            juego = Juego(pantalla, audio_manager, sistema_clasificacion, resource_manager)
            estado = juego.ejecutar()  # -> "MENU" o "SALIR"
        else:
            estado = "SALIR"

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
