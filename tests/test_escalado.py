"""src/core/escalado.py — vida y daño de los enemigos por nivel."""
import pytest

from src.core import escalado, settings
from src.entities.enemies import EnemigoBase, EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe

CLASES = (EnemigoTipo1, EnemigoTipo2, EnemigoTipo3)


# --- Las tablas ---------------------------------------------------------------

def test_hay_una_entrada_por_nivel_de_la_campana():
    assert len(escalado.VIDA_X) == len(escalado.VIDA_JEFE) == len(escalado.DANIO_X) == settings.NIVEL_MAX


def test_la_dificultad_solo_sube_con_el_nivel():
    for tabla in (escalado.VIDA_X, escalado.VIDA_JEFE, escalado.DANIO_X):
        assert list(tabla) == sorted(tabla) and len(set(tabla)) > 1


def test_el_primer_nivel_es_el_de_referencia_y_el_ultimo_hace_todo_el_dano():
    assert escalado.VIDA_X[0] == 1.0                        # `SALUD_BASE` es la vida en el nivel 1
    assert escalado.DANIO_X[0] < 1.0                        # el nivel 1 se completa sin mejoras
    assert escalado.DANIO_X[-1] == 1.0


def test_las_funciones_leen_la_tabla_de_cada_nivel():
    for n in range(1, settings.NIVEL_MAX + 1):
        assert escalado.vida_x(n) == escalado.VIDA_X[n - 1]
        assert escalado.vida_jefe(n) == escalado.VIDA_JEFE[n - 1]
        assert escalado.danio_x(n) == escalado.DANIO_X[n - 1]


def test_por_debajo_del_primer_nivel_cuenta_como_el_primero():
    assert escalado.vida_x(0) == escalado.vida_x(-3) == escalado.vida_x(1)
    assert escalado.vida_jefe(0) == escalado.vida_jefe(1)
    assert escalado.danio_x(0) == escalado.danio_x(1)


def test_mas_alla_del_ultimo_nivel_la_vida_sigue_subiendo_y_el_dano_se_queda():
    ultimo = settings.NIVEL_MAX
    paso_x = escalado.VIDA_X[-1] - escalado.VIDA_X[-2]
    paso_jefe = escalado.VIDA_JEFE[-1] - escalado.VIDA_JEFE[-2]
    for extra in (1, 2, 10):
        assert escalado.vida_x(ultimo + extra) == pytest.approx(escalado.VIDA_X[-1] + paso_x * extra)
        assert escalado.vida_jefe(ultimo + extra) == escalado.VIDA_JEFE[-1] + paso_jefe * extra
        assert escalado.danio_x(ultimo + extra) == escalado.DANIO_X[-1]


# --- Los enemigos las usan -----------------------------------------------------

@pytest.fixture
def imgs(rm):
    return (rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR),
            rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE))


def _crear(clase, imgs, nivel, jugador):
    img, img_jefe = imgs
    if clase is EnemigoTipo1:
        return EnemigoTipo1(img, 0, 0, 600, nivel)
    if clase is Jefe:
        return Jefe(img_jefe, 0, 0, 600, 800, nivel, jugador)
    return clase(img, 0, 0, 600, nivel, jugador)


@pytest.mark.parametrize("nivel", range(1, settings.NIVEL_MAX + 3))          # incluye dos "oleadas" del sin fin
@pytest.mark.parametrize("clase", CLASES)
def test_la_vida_de_cada_enemigo_es_su_base_por_el_multiplicador(imgs, jugador, clase, nivel):
    e = _crear(clase, imgs, nivel, jugador)
    assert e.salud_maxima == e.salud == clase.vida_en_nivel(nivel) == round(clase.SALUD_BASE * escalado.vida_x(nivel))


@pytest.mark.parametrize("nivel", range(1, settings.NIVEL_MAX + 3))
def test_la_vida_del_jefe_es_la_de_la_tabla(imgs, jugador, nivel):
    j = _crear(Jefe, imgs, nivel, jugador)
    assert j.salud_maxima == j.salud == escalado.vida_jefe(nivel)


def test_la_base_del_jefe_es_su_vida_en_el_primer_nivel():
    assert Jefe.SALUD_BASE == Jefe.vida_en_nivel(1) == escalado.VIDA_JEFE[0]


def test_el_dano_escalado_se_redondea_y_nunca_baja_de_uno(imgs, jugador):
    e = _crear(EnemigoTipo1, imgs, 1, jugador)                # x0,6
    assert e.danio_escalado(10) == 6 and e.danio_escalado(20) == 12 and e.danio_escalado(1) == 1
    assert e.danio_escalado(0) == 1


@pytest.mark.parametrize("nivel", range(1, settings.NIVEL_MAX + 1))
def test_las_balas_enemigas_llevan_el_dano_del_nivel(rm, imgs, jugador, nivel):
    x = escalado.danio_x(nivel)
    for clase, base in ((EnemigoTipo2, settings.DANIO_BALA_TIPO2), (EnemigoTipo3, settings.DANIO_BALA_TIPO3)):
        bala = _crear(clase, imgs, nivel, jugador).disparo_enemigo(10_000, rm, "bala_enemigo")
        assert bala.danio == round(base * x)
    jefe = _crear(Jefe, imgs, nivel, jugador)
    assert jefe.disparo_jefe(10_000, rm, "bala_enemigo2").danio == round(settings.DANIO_JEFE_NORMAL * x)
    assert jefe.disparo_rapido(10_000, rm, "bala_enemigo").danio == round(settings.DANIO_JEFE_RAPIDA * x)


def test_el_choque_de_un_enemigo_de_nivel_bajo_hace_menos_dano(juego, rm):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo1(img, 0, 0, 600, 1)
    e.salud = e.salud_maxima = 100
    e.rect.center = juego.jugador.rect.center
    juego.entity_manager.agregar_enemigo(e)
    antes = juego.jugador.salud
    juego.collision_manager.actualizar(juego.tiempo_juego + settings.CONTACTO_COOLDOWN_MS + 1)
    assert antes - juego.jugador.salud == e.danio_escalado(settings.DANIO_CONTACTO) == 6
    assert e.salud == 100 - settings.DANIO_EMBESTIDA           # la embestida al enemigo no escala
