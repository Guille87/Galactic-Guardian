import pygame
import os

from galactic_guardian.juego.menu import crear_pantalla, mostrar_menu
from galactic_guardian.resources.resource_manager import ResourceManager

# Directorio de recursos
DIR_RECURSOS = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# Lista de recursos a cargar
RECURSOS = {
    "imagen_fondo1": "imagenes\\fondo1.png",
    "imagen_fondo2": "imagenes\\fondo2.png",
    "bala_enemigo": "imagenes\\balas\\bala_enemigo.png",
    "bala_enemigo2": "imagenes\\balas\\bala_enemigo2.png",
    "bala_jugador1": "imagenes\\balas\\bala_jugador1.png",
    "bala_jugador2": "imagenes\\balas\\bala_jugador2.png",
    "jugador": "imagenes\\jugador.png",
    "enemigo1": "imagenes\\enemigos\\enemigo1.png",
    "enemigo2": "imagenes\\enemigos\\enemigo2.png",
    "enemigo3": "imagenes\\enemigos\\enemigo3.png",
    "jefe1": "imagenes\\enemigos\\jefe1.png",
    "curacion": "imagenes\\objetos\\curacion.png",
    "potenciador_cadencia": "imagenes\\objetos\\potenciador_cadencia.png",
    "potenciador_danio": "imagenes\\objetos\\potenciador_danio.png",
    "potenciador_velocidad": "imagenes\\objetos\\potenciador_velocidad.png",
}

# Sonidos
SONIDOS = {
    "skyfire_theme": "musica\\SkyFire.ogg",
    "rain_of_lasers": "musica\\Rain of Lasers.ogg",
    "deathmatch_theme": "musica\\DeathMatch Boss Theme.ogg",
    "defeated_tune": "musica\\Defeated (Game Over Tune).ogg",
    "victory_tune": "musica\\Victory Tune.ogg",
    "laser_gun": "sonidos\\laser-gun.wav",
    "hit": "sonidos\\hit.wav",
    "item_take": "sonidos\\item-take.wav",
}

# Lista de explosiones
EXPLOSIONES = {
    f"explosion_{i}": f"imagenes\\explosion\\Explosion1_{i}.png" for i in range(1, 12)
}


def cargar_recursos(resource_manager, directorio, recursos):
    for nombre, ruta in recursos.items():
        resource_manager.load_image(nombre, os.path.join(directorio, ruta))


def cargar_sonidos(resource_manager, directorio, sonidos):
    for nombre, ruta in sonidos.items():
        resource_manager.load_sound(nombre, os.path.join(directorio, ruta))


def cargar_explosiones(resource_manager, directorio, explosiones):
    for nombre, ruta in explosiones.items():
        resource_manager.load_image(nombre, os.path.join(directorio, ruta))


def main():
    # Inicializar Pygame
    pygame.init()

    # Crear la pantalla
    pantalla = crear_pantalla()

    # Establecer el icono de la ventana
    icono = pygame.image.load(os.path.join(str(DIR_RECURSOS), 'imagenes\\favicon.ico'))
    pygame.display.set_icon(icono)

    # Cargar recursos
    resource_manager = ResourceManager()
    cargar_recursos(resource_manager, DIR_RECURSOS, RECURSOS)
    cargar_sonidos(resource_manager, DIR_RECURSOS, SONIDOS)
    cargar_explosiones(resource_manager, DIR_RECURSOS, EXPLOSIONES)

    # Mostrar el menú
    mostrar_menu(pantalla)


if __name__ == "__main__":
    main()
