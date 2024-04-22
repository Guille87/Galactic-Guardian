import pygame
import os

from galactic_guardian.juego.menu import crear_pantalla, mostrar_menu
from galactic_guardian.resources.resource_manager import ResourceManager


# Instancia global de ResourceManager
resource_manager = ResourceManager()


def main():
    # Inicializar Pygame
    pygame.init()

    # Crear la pantalla
    pantalla = crear_pantalla()

    # Obtener la ruta al directorio actual del script
    dir_actual = os.path.dirname(os.path.abspath(__file__))

    # Cargar el icono como una superficie
    icono = pygame.image.load(os.path.join(dir_actual, 'imagenes', 'favicon.ico'))

    # Establecer el icono de la ventana
    pygame.display.set_icon(icono)

    # Cargar las imagenes de fondo
    resource_manager.load_image("imagen_fondo1", os.path.join(dir_actual, 'imagenes', 'fondo1.png'))
    resource_manager.load_image("imagen_fondo2", os.path.join(dir_actual, 'imagenes', 'fondo2.png'))

    # Cargar imágenes de balas
    resource_manager.load_image("bala_enemigo", os.path.join(dir_actual, 'imagenes', 'balas', 'bala_enemigo.png'))
    resource_manager.load_image("bala_enemigo2", os.path.join(dir_actual, 'imagenes', 'balas', 'bala_enemigo2.png'))
    resource_manager.load_image("bala_jugador1", os.path.join(dir_actual, 'imagenes', 'balas', 'bala_jugador1.png'))
    resource_manager.load_image("bala_jugador2", os.path.join(dir_actual, 'imagenes', 'balas', 'bala_jugador2.png'))

    # Cargar imagen del jugador
    resource_manager.load_image("jugador", os.path.join(dir_actual, 'imagenes', 'jugador.png'))

    # Cargar imágenes de enemigos
    resource_manager.load_image("enemigo1", os.path.join(dir_actual, 'imagenes', 'enemigos', 'enemigo1.png'))
    resource_manager.load_image("enemigo2", os.path.join(dir_actual, 'imagenes', 'enemigos', 'enemigo2.png'))
    resource_manager.load_image("enemigo3", os.path.join(dir_actual, 'imagenes', 'enemigos', 'enemigo3.png'))
    resource_manager.load_image("jefe1", os.path.join(dir_actual, 'imagenes', 'enemigos', 'jefe1.png'))

    # Cargar imágenes de explosiones
    for i in range(1, 12):
        resource_manager.load_image(f"explosion_{i}", os.path.join(dir_actual, 'imagenes', 'explosion', f'Explosion1_{i}.png'))

    # Cargar imágenes de objetos
    resource_manager.load_image("curacion", os.path.join(dir_actual, 'imagenes', 'objetos', 'curacion.png'))
    resource_manager.load_image("potenciador_cadencia", os.path.join(dir_actual, 'imagenes', 'objetos', 'potenciador_cadencia.png'))
    resource_manager.load_image("potenciador_danio", os.path.join(dir_actual, 'imagenes', 'objetos', 'potenciador_danio.png'))
    resource_manager.load_image("potenciador_velocidad", os.path.join(dir_actual, 'imagenes', 'objetos', 'potenciador_velocidad.png'))

    # Cargar sonidos de música
    resource_manager.load_sound("deathmatch_theme", os.path.join(dir_actual, 'musica', 'DeathMatch Boss Theme.ogg'))
    resource_manager.load_sound("defeated_tune", os.path.join(dir_actual, 'musica', 'Defeated (Game Over Tune).ogg'))
    resource_manager.load_sound("skyfire_theme", os.path.join(dir_actual, 'musica', 'SkyFire.ogg'))
    resource_manager.load_sound("victory_tune", os.path.join(dir_actual, 'musica', 'Victory Tune.ogg'))

    # Cargar sonidos de efectos
    resource_manager.load_sound("laser_gun", os.path.join(dir_actual, 'sonidos', 'laser-gun.wav'))
    resource_manager.load_sound("hit", os.path.join(dir_actual, 'sonidos', 'hit.wav'))
    resource_manager.load_sound("item_take", os.path.join(dir_actual, 'sonidos', 'item-take.wav'))

    # Mostrar el menú
    mostrar_menu(pantalla)


if __name__ == "__main__":
    main()
