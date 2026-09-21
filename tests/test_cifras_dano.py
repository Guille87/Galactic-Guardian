"""Cifras flotantes de daño: sprite, combinación de impactos, interruptor y colisiones."""
import pygame
import pytest

from src.core import config, preferencias, settings
from src.entities.bullet import Bala
from src.entities.enemies import EnemigoBase, EnemigoTipo1
from src.ui.menu import MenuManager
from src.visual.floating_text import CifraFlotante

DT60 = 1.0 / 60.0


def _cifras(juego):
    return [e for e in juego.entity_manager.efectos if isinstance(e, CifraFlotante)]


# --- El sprite ------------------------------------------------------------------

def test_una_cifra_sube_y_muere_a_su_hora():
    c = CifraFlotante((100, 200), 10, (255, 255, 255))
    y0 = c.rect.centery
    c.update(0.1)
    assert c.rect.centery < y0
    grupo = pygame.sprite.Group(c)
    c.update(settings.CIFRA_DURACION_MS / 1000)
    assert not grupo                                    # se quitó sola


def test_una_cifra_se_desvanece_en_la_segunda_mitad():
    c = CifraFlotante((100, 200), 10, (255, 255, 255))
    c.update(settings.CIFRA_DURACION_MS / 2000 - 0.001)
    assert c.image.get_alpha() in (None, 255)           # aún opaca
    c.update(0.05 + 0.001)
    assert c.image.get_alpha() < 255


def test_sumar_cambia_el_valor_y_el_dibujo():
    c = CifraFlotante((100, 200), 10, (255, 255, 255))
    ancho = c.image.get_width()
    c.sumar(90)
    assert c.valor == 100 and c.image.get_width() > ancho     # "100" ocupa más que "10"


def test_la_cifra_dibuja_algo_visible():
    c = CifraFlotante((50, 50), 30, (255, 230, 120))
    assert c.image.get_bounding_rect().width > 5


# --- Efectos ---------------------------------------------------------------------

def _enemigo(rm, nivel=1):
    return EnemigoTipo1(rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR), 300, 100, 600, nivel)


def test_crear_una_cifra_la_mete_en_los_efectos(juego, rm):
    juego.effect_manager.crear_cifra_dano(_enemigo(rm), (300, 100), 10)
    (c,) = _cifras(juego)
    assert c.valor == 10


def test_impactos_seguidos_al_mismo_objetivo_suman_en_una_sola_cifra(juego, rm):
    e = _enemigo(rm)
    for _ in range(3):                                   # un disparo triple
        juego.effect_manager.crear_cifra_dano(e, (300, 100), 10)
    (c,) = _cifras(juego)
    assert c.valor == 30


def test_pasado_el_margen_sale_una_cifra_nueva(juego, rm):
    e = _enemigo(rm)
    juego.effect_manager.crear_cifra_dano(e, (300, 100), 10)
    juego.entity_manager.efectos.update(settings.CIFRA_COMBINAR_MS / 1000 + 0.05)
    juego.effect_manager.crear_cifra_dano(e, (300, 100), 10)
    assert len(_cifras(juego)) == 2


def test_objetivos_distintos_tienen_cifras_distintas(juego, rm):
    juego.effect_manager.crear_cifra_dano(_enemigo(rm), (100, 100), 10)
    juego.effect_manager.crear_cifra_dano(_enemigo(rm), (400, 100), 10)
    assert len(_cifras(juego)) == 2


def test_con_el_interruptor_apagado_no_salen_cifras(juego, rm):
    preferencias.establecer_cifras_dano(False)
    juego.effect_manager.crear_cifra_dano(_enemigo(rm), (300, 100), 10)
    assert not _cifras(juego)


def test_hay_un_tope_de_cifras_a_la_vez(juego, rm):
    for _ in range(settings.CIFRAS_MAX + 20):
        juego.effect_manager.crear_cifra_dano(_enemigo(rm), (300, 100), 10)
    assert len(_cifras(juego)) == settings.CIFRAS_MAX


def test_no_se_crean_cifras_de_dano_cero(juego):
    juego.effect_manager.crear_cifra_dano(juego.jugador, (300, 700), 0, de_la_nave=True)
    assert not _cifras(juego)


def test_las_cifras_se_congelan_en_pausa_y_siguen_al_reanudar(juego, rm):
    juego.effect_manager.crear_cifra_dano(_enemigo(rm), (300, 100), 10)
    (c,) = _cifras(juego)
    juego.pausado = True                                  # `ejecutar` no llama a `actualizar` en pausa
    y = c.rect.centery
    juego.dibujar()
    assert c.rect.centery == y
    juego.pausado = False
    juego.tiempo_proximo_enemigo = float("inf")
    juego.actualizar(DT60 * 6)
    assert c.rect.centery < y


# --- Con las colisiones ------------------------------------------------------------------

def _enemigo_en(juego, rm, x, y, vida=1000):
    e = _enemigo(rm, settings.NIVEL_MAX)
    e.salud = e.salud_maxima = vida
    e.rect.center = (x, y)
    e.velocidad_x = e.velocidad_y = 0
    juego.entity_manager.agregar_enemigo(e)
    return e


def _bala(rm, x, y, danio):
    return Bala(rm.get_image_rotated("bala_jugador1", Bala.TAMANO, Bala.ANGULO), x, y, danio)


def test_una_bala_que_da_a_un_enemigo_saca_su_dano(juego, rm):
    e = _enemigo_en(juego, rm, 300, 300)
    juego.entity_manager.balas.add(_bala(rm, 300, 300, 30))
    juego.collision_manager.actualizar(juego.tiempo_juego)
    (c,) = _cifras(juego)
    assert c.valor == 30 and e.salud == 970


def test_tres_balas_a_la_vez_dan_una_cifra_con_la_suma(juego, rm):
    _enemigo_en(juego, rm, 300, 300)
    for dx in (-15, 0, 15):
        juego.entity_manager.balas.add(_bala(rm, 300 + dx, 300, 10))
    juego.collision_manager.actualizar(juego.tiempo_juego)
    (c,) = _cifras(juego)
    assert c.valor == 30


def _bala_enemiga_sobre_la_nave(juego, rm):
    from src.entities.bullet_enemy import BalaEnemigo
    img = rm.get_image_rotated("bala_enemigo", BalaEnemigo.TAMANO, 0)
    juego.entity_manager.agregar_bala_enemigo(BalaEnemigo(img, *juego.jugador.rect.center, 0, 1, 10, 4))


def test_un_impacto_en_la_nave_saca_una_cifra_roja(juego, rm):
    juego.jugador.invulnerable = False
    _bala_enemiga_sobre_la_nave(juego, rm)
    juego.collision_manager.actualizar(juego.tiempo_juego)
    (c,) = _cifras(juego)
    assert c.valor == 10 and c.color == juego.effect_manager.COLOR_CIFRA_NAVE


def test_con_la_nave_invulnerable_no_sale_cifra(juego, rm):
    juego.jugador.invulnerable = True
    _bala_enemiga_sobre_la_nave(juego, rm)
    juego.collision_manager.actualizar(juego.tiempo_juego)
    assert not _cifras(juego)


def test_el_choque_con_un_enemigo_saca_la_cifra_de_la_nave(juego, rm):
    juego.jugador.invulnerable = False
    e = _enemigo_en(juego, rm, 0, 0)
    e.rect.center = juego.jugador.rect.center
    juego.collision_manager.actualizar(juego.tiempo_juego + settings.CONTACTO_COOLDOWN_MS + 1)
    (c,) = _cifras(juego)
    assert c.valor == e.danio_escalado(settings.DANIO_CONTACTO)


def test_una_partida_larga_con_todo_el_arbol_dibuja_sin_fallar(juego):
    juego.jugador.balas_por_disparo, juego.jugador.disparos_s, juego.jugador.danio = 3, 8.0, 30
    juego.jugador.vidas = 999
    juego.disparando = True
    for _ in range(600):
        juego.actualizar(DT60)
        juego.dibujar()
    assert len(_cifras(juego)) <= settings.CIFRAS_MAX


# --- Configuración ------------------------------------------------------------------------

def test_cifras_roundtrip(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, cifras_dano=False, ruta=ruta)
    assert config.cargar_cifras_dano(ruta=ruta) is False
    config.guardar_configuracion(0.3, 0.7, cifras_dano=True, ruta=ruta)
    assert config.cargar_cifras_dano(ruta=ruta) is True


def test_cifras_y_temblor_conviven_en_la_misma_seccion(tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    config.guardar_configuracion(0.3, 0.7, temblor=False, cifras_dano=True, ruta=ruta)
    assert config.cargar_temblor(ruta=ruta) is False and config.cargar_cifras_dano(ruta=ruta) is True
    config.guardar_configuracion(0.3, 0.7, temblor=True, cifras_dano=False, ruta=ruta)
    assert config.cargar_temblor(ruta=ruta) is True and config.cargar_cifras_dano(ruta=ruta) is False


def test_cifras_por_defecto_activadas(tmp_path):
    assert config.cargar_cifras_dano(ruta=str(tmp_path / "no_existe.ini")) is True
    ruta = tmp_path / "raro.ini"
    ruta.write_text("[PANTALLA]\ntemblor = no\n")             # sin la clave: activadas
    assert config.cargar_cifras_dano(ruta=str(ruta)) is True
    ruta.write_text("esto no es un ini valido [[[")
    assert config.cargar_cifras_dano(ruta=str(ruta)) is True


# --- Opciones -----------------------------------------------------------------------------------

@pytest.fixture
def menu(rm, audio, scoreboard):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)


def _pulsar(menu, boton):
    centro = boton.rect.center
    for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(tipo, button=1, pos=centro))
    for _ in range(5):
        menu._menu_opciones(0.016)


def _a_pantalla(menu):
    for boton, nombre in menu._botones_pestana.items():
        if nombre == "pantalla":
            _pulsar(menu, boton)
    return menu.btn_cifras


def test_la_pestana_pantalla_tiene_el_interruptor_de_cifras_activado(menu):
    menu._abrir_opciones()
    boton = _a_pantalla(menu)
    assert boton.text == "Cifras de daño: Sí" and boton.is_selected


def test_pulsarlo_apaga_y_enciende_al_instante(menu):
    menu._abrir_opciones()
    _pulsar(menu, _a_pantalla(menu))
    assert preferencias.cifras_dano_activadas() is False
    assert menu.btn_cifras.text == "Cifras de daño: No" and not menu.btn_cifras.is_selected
    _pulsar(menu, menu.btn_cifras)
    assert preferencias.cifras_dano_activadas() is True


def test_volver_descarta_el_cambio(menu):
    menu._abrir_opciones()
    _pulsar(menu, _a_pantalla(menu))
    _pulsar(menu, menu.btn_volver)
    assert preferencias.cifras_dano_activadas() is True


def test_guardar_lo_confirma_en_la_sesion_y_en_disco(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    menu._abrir_opciones()
    _pulsar(menu, _a_pantalla(menu))
    _pulsar(menu, menu.btn_guardar)
    assert preferencias.cifras_dano_activadas() is False
    assert config.cargar_cifras_dano(ruta=ruta) is False


def test_guardar_sin_tocarlo_conserva_lo_que_habia_y_no_pisa_el_temblor(menu, monkeypatch, tmp_path):
    ruta = str(tmp_path / "cfg.ini")
    monkeypatch.setattr("src.core.config.CONFIG_FILE", ruta)
    preferencias.establecer_cifras_dano(False)
    preferencias.establecer_temblor(False)
    menu._abrir_opciones()
    _pulsar(menu, menu.btn_guardar)
    assert config.cargar_cifras_dano(ruta=ruta) is False and config.cargar_temblor(ruta=ruta) is False
