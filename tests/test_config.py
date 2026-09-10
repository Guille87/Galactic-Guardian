"""src/core/config.py — persistencia de volúmenes."""
from src.core import config


def test_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, ruta=ruta)
    assert config.cargar_configuracion(ruta=ruta) == (0.3, 0.7)


def test_archivo_inexistente_devuelve_defecto(tmp_path):
    assert config.cargar_configuracion(ruta=str(tmp_path / "no_existe.ini")) == (0.5, 0.5)


def test_ini_corrupto_devuelve_defecto(tmp_path):
    ruta = tmp_path / "roto.ini"
    ruta.write_text("esto no es un ini valido [[[")
    assert config.cargar_configuracion(ruta=str(ruta)) == (0.5, 0.5)


def test_valor_no_numerico_devuelve_defecto(tmp_path):
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[VOLUMEN]\nmusica = alto\nefectos = 0.4\n")
    assert config.cargar_configuracion(ruta=str(ruta)) == (0.5, 0.5)


def test_diccionarios_de_recursos_coherentes():
    # Claves únicas entre sí y valores con extensión razonable
    assert set(config.MUSICA).isdisjoint(config.SONIDOS)
    assert all(v.endswith(".ogg") for v in config.MUSICA.values())
    assert all(v.endswith((".wav", ".ogg")) for v in config.SONIDOS.values())
    assert len(config.EXPLOSIONES) == 11
