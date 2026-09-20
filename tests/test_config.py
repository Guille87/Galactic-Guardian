"""src/core/config.py — persistencia de volúmenes y controles."""
import pygame

from src.core import config, controles


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
    for hoja in config.HOJAS.values():
        assert hoja["ruta"].endswith(".png") and hoja["columnas"] >= 1 and hoja["filas"] >= 1
        assert 1 <= hoja.get("cantidad", hoja["columnas"] * hoja["filas"]) <= hoja["columnas"] * hoja["filas"]
    assert config.HOJAS["explosion"]["cantidad"] == 11


def test_controles_sin_config_devuelve_los_valores_por_defecto(tmp_path):
    ruta = str(tmp_path / "no_existe.ini")
    assert config.cargar_controles(ruta=ruta) == controles.POR_DEFECTO


def test_controles_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    mapa = dict(controles.POR_DEFECTO, disparar=pygame.K_j, pausa=pygame.K_ESCAPE)
    config.guardar_configuracion(0.3, 0.7, mapa_controles=mapa, ruta=ruta)
    assert config.cargar_controles(ruta=ruta) == mapa


def test_guardar_sin_mapa_de_controles_no_escribe_esa_seccion(tmp_path):
    """Guardar solo volumen (p.ej. desde la pausa antes de tocar Controles) no
    debe crear una sección [CONTROLES] vacía ni tocar los valores por defecto."""
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, ruta=ruta)
    assert config.cargar_controles(ruta=ruta) == controles.POR_DEFECTO


def test_controles_tecla_guardada_invalida_cae_a_esa_accion_por_defecto(tmp_path):
    """Un nombre de tecla corrupto en una acción no debe tirar las demás."""
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[CONTROLES]\ndisparar = esto-no-es-una-tecla\npausa = escape\n")
    mapa = config.cargar_controles(ruta=str(ruta))
    assert mapa["disparar"] == controles.POR_DEFECTO["disparar"]   # cae a la de defecto
    assert mapa["pausa"] == pygame.K_ESCAPE                         # esta sí es válida
    assert mapa["arriba"] == controles.POR_DEFECTO["arriba"]        # no estaba en el ini


def test_idioma_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, idioma="en", ruta=ruta)
    assert config.cargar_idioma(ruta=ruta) == "en"


def test_idioma_sin_config_es_none(tmp_path):
    """None = primer arranque: quien llama usa el idioma del sistema."""
    assert config.cargar_idioma(ruta=str(tmp_path / "no_existe.ini")) is None


def test_idioma_guardado_no_disponible_es_none(tmp_path):
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[IDIOMA]\ncodigo = klingon\n")
    assert config.cargar_idioma(ruta=str(ruta)) is None


def test_guardar_sin_idioma_no_escribe_esa_seccion(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, ruta=ruta)
    assert config.cargar_idioma(ruta=ruta) is None


def test_temblor_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, temblor=False, ruta=ruta)
    assert config.cargar_temblor(ruta=ruta) is False
    config.guardar_configuracion(0.3, 0.7, temblor=True, ruta=ruta)
    assert config.cargar_temblor(ruta=ruta) is True


def test_temblor_por_defecto_activados(tmp_path):
    """Sin config, sin la sección o con un valor raro: activados."""
    assert config.cargar_temblor(ruta=str(tmp_path / "no_existe.ini")) is True
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[PANTALLA]\nefectos = quiza\n")
    assert config.cargar_temblor(ruta=str(ruta)) is True
    ruta.write_text("esto no es un ini valido [[[")
    assert config.cargar_temblor(ruta=str(ruta)) is True


def test_guardar_sin_efectos_no_escribe_esa_seccion(tmp_path):
    ruta = tmp_path / "cfg.ini"
    config.guardar_configuracion(0.3, 0.7, ruta=str(ruta))
    assert "PANTALLA" not in ruta.read_text()
