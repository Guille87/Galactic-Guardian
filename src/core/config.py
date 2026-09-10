import configparser
import os

from src.core import paths

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
    "item_take": "sonidos/item-take.wav",
}

EXPLOSIONES = {f"explosion_{i}": f"imagenes/explosion/Explosion1_{i}.png" for i in range(1, 12)}

# --- LÓGICA DE PERSISTENCIA (OPCIONES DE USUARIO) ---

def guardar_configuracion(volumen_musica, volumen_efectos, ruta=None):
    config = configparser.ConfigParser()
    config['VOLUMEN'] = {
        'musica': str(volumen_musica),
        'efectos': str(volumen_efectos)
    }
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
