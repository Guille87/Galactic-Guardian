import configparser

CONFIG_FILE = 'config.ini'


def guardar_configuracion(volumen_musica, volumen_efectos):
    config = configparser.ConfigParser()
    config['VOLUMEN'] = {
        'musica': str(volumen_musica),
        'efectos': str(volumen_efectos)
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


def cargar_configuracion():
    config = configparser.ConfigParser()

    try:
        config.read(CONFIG_FILE)

        volumen_musica = float(config.get('VOLUMEN', 'musica', fallback=0.5))
        volumen_efectos = float(config.get('VOLUMEN', 'efectos', fallback=0.5))
    except (configparser.Error, ValueError):
        volumen_musica = 0.5
        volumen_efectos = 0.5

    return volumen_musica, volumen_efectos
