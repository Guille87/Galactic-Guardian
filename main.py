import sys
import os

import pygame

from src.ui.menu import MenuManager
from src.core.engine import Juego
from src.core.audio import AudioManager
from src.core.resources import ResourceManager
from src.core import i18n, preferencias, settings
from src.core.config import (RECURSOS, MUSICA, SONIDOS, EXPLOSIONES, DIR_ASSETS, cargar_configuracion,
                             cargar_efectos_pantalla, cargar_idioma)
from src.core.version import __version__
from src.ui.scoreboard import SistemaClasificacion

RANKING_SIN_FIN = "puntuaciones_sin_fin.json"


def cargar_activos_del_juego(rm):
    """Carga imágenes y efectos en memoria; la música solo registra su ruta."""
    # Cargar Imágenes
    for nombre, ruta in {** RECURSOS, ** EXPLOSIONES}.items():
        rm.load_image(nombre, os.path.join(DIR_ASSETS, ruta))

    # Cargar Efectos de sonido
    for nombre, ruta in SONIDOS.items():
        rm.load_sound(nombre, os.path.join(DIR_ASSETS, ruta))

    # Registrar pistas de música (streaming, no se cargan en RAM)
    for nombre, ruta in MUSICA.items():
        rm.load_music(nombre, os.path.join(DIR_ASSETS, ruta))


def _smoke(frames=120):
    """Arranque headless para verificar un build (`main.py --smoke`).

    Carga todos los recursos, hace unos frames de menú y de partida y sale con
    código 0 si nada ha fallado. Lo usa el workflow de compilación para saber que
    el ejecutable empaquetado encuentra sus assets y sus datos de `pygame_gui`.
    """
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        pygame.mixer.set_num_channels(16)
    except pygame.error:
        pass

    pantalla = pygame.display.set_mode((settings.ANCHO, settings.ALTO))
    resource_manager = ResourceManager()
    cargar_activos_del_juego(resource_manager)
    audio_manager = AudioManager(resource_manager, 0.2, 0.2)
    sistema_clasificacion = SistemaClasificacion()

    menu = MenuManager(pantalla, resource_manager, audio_manager, sistema_clasificacion,
                       SistemaClasificacion(nombre_archivo=RANKING_SIN_FIN))
    menu._menu_principal()
    menu._abrir_opciones()
    for _ in range(5):
        menu._menu_opciones(1 / settings.FPS)

    for modo in (settings.MODO_CAMPANA, settings.MODO_SIN_FIN):
        juego = Juego(pantalla, audio_manager, sistema_clasificacion, resource_manager, modo=modo)
        juego.jugador.vidas = 999  # que no acabe la partida durante el humo
        for _ in range(frames):
            juego.actualizar(1 / settings.FPS)
            juego.dibujar()

    pygame.quit()
    print(f"smoke OK ({frames} frames, v{__version__})")


def main():
    if "--smoke" in sys.argv:
        _smoke()
        return

    # Buffer de audio pequeño ANTES de pygame.init() para reducir la latencia
    pygame.mixer.pre_init(44100, -16, 2, 512)

    # Inicializar Pygame
    pygame.init()
    pygame.mixer.set_num_channels(16)

    # Crear la pantalla
    pantalla = pygame.display.set_mode((settings.ANCHO, settings.ALTO))

    # Establecer el icono de la ventana
    icono_path = os.path.join(DIR_ASSETS, 'imagenes/favicon.ico')
    if os.path.exists(icono_path):
        pygame.display.set_icon(pygame.image.load(icono_path))

    # Gestión de recursos
    resource_manager = ResourceManager()
    cargar_activos_del_juego(resource_manager)

    # Cargar configuración de usuario (Volúmenes guardados) e idioma: el guardado o,
    # la primera vez, el del sistema.
    vol_musica, vol_efectos = cargar_configuracion()
    i18n.establecer_idioma(cargar_idioma() or i18n.detectar_idioma_sistema())
    preferencias.establecer_efectos_pantalla(cargar_efectos_pantalla())

    # Un único AudioManager compartido entre el menú y la partida
    audio_manager = AudioManager(resource_manager, vol_musica, vol_efectos)

    # Un ranking por modo de juego (cada uno en su archivo)
    sistema_clasificacion = SistemaClasificacion()
    clasificacion_sin_fin = SistemaClasificacion(nombre_archivo=RANKING_SIN_FIN)

    # El menú es persistente; se reutiliza cada vez que se vuelve a él
    menu = MenuManager(pantalla, resource_manager, audio_manager, sistema_clasificacion,
                       clasificacion_sin_fin)

    # --- Máquina de estados de alto nivel ---
    # Cada pantalla (menú / juego) devuelve el siguiente estado en lugar de
    # instanciar la otra o llamar a sys.exit() por su cuenta.
    estado = "MENU"
    while estado != "SALIR":
        if estado == "MENU":
            estado = menu.ejecutar()  # -> "JUGAR", "JUGAR_SIN_FIN" o "SALIR"
        elif estado in ("JUGAR", "JUGAR_SIN_FIN"):
            if estado == "JUGAR_SIN_FIN":
                juego = Juego(pantalla, audio_manager, clasificacion_sin_fin, resource_manager,
                              modo=settings.MODO_SIN_FIN)
            else:
                juego = Juego(pantalla, audio_manager, sistema_clasificacion, resource_manager)
            estado = juego.ejecutar()  # -> "MENU" o "SALIR"
        else:
            estado = "SALIR"

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
