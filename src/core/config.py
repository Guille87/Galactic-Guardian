import configparser
import os

import pygame

from src.core import controles, i18n, paths

# --- RUTAS Y RECURSOS (CONSTANTES) ---
DIR_ASSETS = paths.recurso('data', 'assets')          # solo lectura (empaquetado)
CONFIG_FILE = os.path.join(paths.dir_datos_usuario(), 'config.ini')  # escribible

RECURSOS = {
    "imagen_fondo1": "imagenes/fondo1.png",
    "imagen_fondo2": "imagenes/fondo2.png",
    "bala_enemigo": "imagenes/balas/bala_enemigo.png",
    "bala_enemigo2": "imagenes/balas/bala_enemigo2.png",
    "bala_jugador1": "imagenes/balas/bala_jugador1.png",
    "bala_jugador2": "imagenes/balas/bala_jugador2.png",
    "jugador": "imagenes/jugador.png",
    "enemigo1": "imagenes/enemigos/enemigo1.png",
    "enemigo2": "imagenes/enemigos/enemigo2.png",
    "enemigo3": "imagenes/enemigos/enemigo3.png",
    "jefe1": "imagenes/enemigos/jefe1.png",
    "curacion": "imagenes/objetos/curacion.png",
    "potenciador_cadencia": "imagenes/objetos/potenciador_cadencia.png",
    "potenciador_danio": "imagenes/objetos/potenciador_danio.png",
    "potenciador_velocidad": "imagenes/objetos/potenciador_velocidad.png",
}

# Música de fondo: se reproduce en streaming vía pygame.mixer.music (una sola
# pista a la vez), NO se decodifica entera en memoria.
MUSICA = {
    "skyfire_theme": "musica/SkyFire.ogg",
    "rain_of_lasers": "musica/Rain of Lasers.ogg",
    "deathmatch_theme": "musica/DeathMatch Boss Theme.ogg",
    "defeated_tune": "musica/Defeated (Game Over Tune).ogg",
    "victory_tune": "musica/Victory Tune.ogg",
}

# Efectos cortos: se cargan en memoria como pygame.mixer.Sound.
SONIDOS = {
    "laser_gun": "sonidos/laser-gun.wav",
    "hit": "sonidos/hit.wav",
}

# Hojas de sprites (animaciones): una imagen con los fotogramas en una rejilla
# regular, sin márgenes, de izquierda a derecha y de arriba abajo. `cantidad`
# es cuántos son válidos si las últimas celdas están vacías. Ver
# `ResourceManager.load_spritesheet` / `get_frames`.
HOJAS = {
    "explosion": {"ruta": "imagenes/explosion/explosion.png", "columnas": 4, "filas": 3, "cantidad": 11},
}

# --- LÓGICA DE PERSISTENCIA (OPCIONES DE USUARIO) ---

def guardar_configuracion(volumen_musica, volumen_efectos, mapa_controles=None, idioma=None,
                          temblor=None, cifras_dano=None, disparo_automatico=None, mostrar_fps=None,
                          ruta=None):
    config = configparser.ConfigParser()
    config['VOLUMEN'] = {
        'musica': str(volumen_musica),
        'efectos': str(volumen_efectos)
    }
    if mapa_controles is not None:
        config['CONTROLES'] = {
            accion: pygame.key.name(codigo) for accion, codigo in mapa_controles.items()
        }
    if idioma is not None:
        config['IDIOMA'] = {'codigo': idioma}
    if temblor is not None or cifras_dano is not None or mostrar_fps is not None:
        config['PANTALLA'] = {}
        if temblor is not None:
            config['PANTALLA']['temblor'] = 'si' if temblor else 'no'
        if cifras_dano is not None:
            config['PANTALLA']['cifras_dano'] = 'si' if cifras_dano else 'no'
        if mostrar_fps is not None:
            config['PANTALLA']['mostrar_fps'] = 'si' if mostrar_fps else 'no'
    juego = {}
    if disparo_automatico is not None:
        juego['disparo_automatico'] = 'si' if disparo_automatico else 'no'
    # `version_vista` (pantalla de novedades) no es una opción de esta pantalla: se conserva
    # tal cual estuviera, para que Guardar no la borre (esta función reescribe el archivo entero).
    version_vista = cargar_version_vista(ruta)
    if version_vista is not None:
        juego['version_vista'] = version_vista
    if juego:
        config['JUEGO'] = juego
    with open(ruta or CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def cargar_configuracion(ruta=None):
    config = configparser.ConfigParser()

    try:
        config.read(ruta or CONFIG_FILE)

        volumen_musica = float(config.get('VOLUMEN', 'musica', fallback=0.5))
        volumen_efectos = float(config.get('VOLUMEN', 'efectos', fallback=0.5))
    except (configparser.Error, ValueError):
        volumen_musica, volumen_efectos = 0.5, 0.5

    return volumen_musica, volumen_efectos


def cargar_idioma(ruta=None):
    """Idioma guardado, o None si no hay (primer arranque) o no es uno de los
    disponibles: quien llama decide entonces con `i18n.detectar_idioma_sistema()`."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        codigo = config.get('IDIOMA', 'codigo', fallback=None)
    except configparser.Error:
        return None
    return codigo if codigo in i18n.IDIOMAS else None


def cargar_temblor(ruta=None):
    """True si el temblor de pantalla está activado: lo
    está por defecto (sin config, sin la sección o con un valor que no es "no")."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        valor = config.get('PANTALLA', 'temblor', fallback='si')
    except configparser.Error:
        return True
    return valor.strip().lower() != 'no'


def cargar_mostrar_fps(ruta=None):
    """True si se muestran los FPS en partida: lo está por defecto (sin config, sin la
    sección o con un valor que no es "no")."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        valor = config.get('PANTALLA', 'mostrar_fps', fallback='si')
    except configparser.Error:
        return True
    return valor.strip().lower() != 'no'


def cargar_disparo_automatico(ruta=None):
    """True si el disparo automático está activado: por defecto **no** lo está (sin config, sin
    la sección o con un valor que no es "si")."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        valor = config.get('JUEGO', 'disparo_automatico', fallback='no')
    except configparser.Error:
        return False
    return valor.strip().lower() == 'si'


def cargar_cifras_dano(ruta=None):
    """True si las cifras flotantes de daño están activadas: lo están por defecto
    (sin config, sin la sección o con un valor que no es "no")."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        valor = config.get('PANTALLA', 'cifras_dano', fallback='si')
    except configparser.Error:
        return True
    return valor.strip().lower() != 'no'


def cargar_version_vista(ruta=None):
    """Última versión para la que ya se mostró la pantalla de novedades, o `None` si no hay
    ninguna guardada (instalación nueva, o `config.ini` de antes de que existiera esta clave)."""
    config = configparser.ConfigParser()
    try:
        config.read(ruta or CONFIG_FILE)
        return config.get('JUEGO', 'version_vista', fallback=None)
    except configparser.Error:
        return None


def guardar_version_vista(version, ruta=None):
    """Marca `version` como ya vista (pantalla de novedades). A diferencia de
    `guardar_configuracion`, hace una lectura-modificación-escritura: no reescribe el resto
    del archivo, porque se llama fuera del flujo de Guardar de Opciones."""
    ruta = ruta or CONFIG_FILE
    config = configparser.ConfigParser()
    config.read(ruta)
    if not config.has_section('JUEGO'):
        config['JUEGO'] = {}
    config['JUEGO']['version_vista'] = version
    with open(ruta, 'w') as configfile:
        config.write(configfile)


def cargar_controles(ruta=None):
    """Mapa de teclas reasignable (una por acción). Cada acción cae a su
    valor por defecto por separado si falta o el nombre guardado no es
    válido, para que un campo corrupto no tire el resto del mapa."""
    config = configparser.ConfigParser()
    config.read(ruta or CONFIG_FILE)

    mapa = {}
    for accion in controles.ACCIONES:
        nombre = config.get('CONTROLES', accion, fallback=None)
        codigo = None
        if nombre:
            try:
                codigo = pygame.key.key_code(nombre)
            except ValueError:
                codigo = None
        mapa[accion] = codigo if codigo is not None else controles.POR_DEFECTO[accion]
    return mapa
