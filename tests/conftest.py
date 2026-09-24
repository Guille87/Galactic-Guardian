"""Configuración común de la suite de tests.

pygame se ejecuta en modo headless (controladores SDL "dummy"): sin ventana ni
audio real, para poder correr en CI. Las variables de entorno se fijan aquí,
antes de que ningún test inicialice pygame.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Que la suite no consulte la API de GitHub al crear un MenuManager.
os.environ.setdefault("GG_SIN_COMPROBAR_ACTUALIZACIONES", "1")

import pygame  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _pygame_headless():
    """Inicializa pygame una vez para toda la sesión de tests."""
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        pygame.mixer.set_num_channels(16)
    except pygame.error:
        pass
    pygame.display.set_mode((600, 800))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _idioma_espanol():
    """Los tests comparan textos en español: cada test parte (y termina) en `es`."""
    from src.core import i18n

    i18n.establecer_idioma("es")
    yield
    i18n.establecer_idioma("es")


@pytest.fixture(autouse=True)
def _temblor_activado():
    """Las preferencias son estado de módulo: cada test parte (y termina) con el
    temblor de pantalla en su valor por defecto (activado)."""
    from src.core import preferencias

    preferencias.establecer_temblor(True)
    preferencias.establecer_cifras_dano(True)
    preferencias.establecer_disparo_automatico(False)
    preferencias.establecer_mostrar_fps(True)
    yield
    preferencias.establecer_temblor(True)
    preferencias.establecer_cifras_dano(True)
    preferencias.establecer_disparo_automatico(False)
    preferencias.establecer_mostrar_fps(True)


@pytest.fixture(scope="session")
def rm():
    """ResourceManager (singleton) con todos los recursos del juego cargados."""
    from main import cargar_activos_del_juego
    from src.core.resources import ResourceManager

    recursos = ResourceManager()
    cargar_activos_del_juego(recursos)
    return recursos


@pytest.fixture
def audio(rm):
    from src.core.audio import AudioManager

    return AudioManager(rm, 0.2, 0.2)


@pytest.fixture
def scoreboard(tmp_path):
    """SistemaClasificacion sobre un archivo temporal (no toca el real)."""
    from src.ui.scoreboard import SistemaClasificacion

    return SistemaClasificacion(ruta_archivo=str(tmp_path / "puntuaciones.json"))


@pytest.fixture
def progresion(tmp_path):
    """Progresión sobre un archivo temporal (no toca la real)."""
    from src.core.progresion import Progresion

    return Progresion(ruta=str(tmp_path / "progresion.json"))


@pytest.fixture
def hacer_juego(rm, audio, scoreboard, progresion):
    """Factory: devuelve una función que crea instancias frescas de `Juego`."""
    from src.core.engine import Juego

    pantalla = pygame.display.get_surface()

    def _crear():
        return Juego(pantalla, audio, scoreboard, rm, progresion=progresion)

    return _crear


@pytest.fixture
def juego(hacer_juego):
    return hacer_juego()


@pytest.fixture
def pantalla():
    return pygame.display.get_surface()


@pytest.fixture
def jugador(rm):
    """Jugador suelto (sin partida), para tests de entidades."""
    from src.entities.player import Jugador

    img = rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"])
    return Jugador(img, 600, 800)
