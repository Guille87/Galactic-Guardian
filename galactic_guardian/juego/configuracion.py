import configparser


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
    config.read('config.ini')

    if 'VOLUMEN' in config and 'musica' in config['VOLUMEN']:
        volumen_musica = float(config['VOLUMEN']['musica'])
    else:
        volumen_musica = 0.5  # Valor predeterminado para la música

    if 'VOLUMEN' in config and 'efectos' in config['VOLUMEN']:
        volumen_efectos = float(config['VOLUMEN']['efectos'])
    else:
        volumen_efectos = 0.5  # Valor predeterminado para los efectos de sonido

    return volumen_musica, volumen_efectos
