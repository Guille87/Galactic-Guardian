"""src/managers/collision.py — resolución de colisiones."""
from src.managers.collision import CollisionManager
from src.entities.bullet import Bala
from src.entities.enemies import EnemigoBase, EnemigoTipo1, Jefe


def _bala_jugador(rm, danio=1):
    img = rm.get_image_rotated("bala_jugador1", Bala.TAMANO, Bala.ANGULO)
    return Bala(img, 0, 0, danio)


def _enemigo(rm, salud=1, nivel=1):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    e = EnemigoTipo1(img, 300, 300, 600, nivel)
    e.salud = e.salud_maxima = salud
    return e


def test_bala_jugador_mata_enemigo(juego, rm):
    em = juego.entity_manager
    e = _enemigo(rm, salud=1)
    b = _bala_jugador(rm)
    em.agregar_enemigo(e)
    em.agregar_bala_jugador(b)
    b.rect.center = e.rect.center

    p0 = juego.puntuacion
    juego.collision_manager.actualizar(juego.tiempo_juego)

    assert e not in em.enemigos
    assert b not in em.balas
    assert juego.puntuacion > p0
    assert any(type(s).__name__ == "Explosion" for s in em.efectos)


def test_doble_bala_mismo_enemigo_no_puntua_doble(juego, rm):
    em = juego.entity_manager
    e = _enemigo(rm, salud=1)
    em.agregar_enemigo(e)
    for _ in range(3):
        b = _bala_jugador(rm)
        b.rect.center = e.rect.center
        em.agregar_bala_jugador(b)

    p0 = juego.puntuacion
    juego.collision_manager.actualizar(juego.tiempo_juego)

    explosiones = sum(1 for s in em.efectos if type(s).__name__ == "Explosion")
    assert explosiones == 1
    assert juego.puntuacion - p0 == e.valor_puntuacion * juego.nivel


def test_bala_enemiga_daña_al_jugador(juego, rm):
    em = juego.entity_manager
    from src.entities.enemies import EnemigoTipo2
    img = rm.get_image_scaled("enemigo2", EnemigoBase.TAMANO_ESTANDAR)
    disparador = EnemigoTipo2(img, 300, 100, 600, 1, juego.jugador)
    disparador.tiempo_ultimo_ataque = -99999
    bala = disparador.disparo_enemigo(0, rm, "bala_enemigo")
    bala.rect.center = juego.jugador.rect.center
    em.agregar_bala_enemigo(bala)

    salud0 = juego.jugador.salud
    juego.collision_manager.actualizar(juego.tiempo_juego)

    assert juego.jugador.salud < salud0
    assert bala not in em.balas_enemigo


def test_muerte_del_jefe_marca_pendiente_reinicio(juego, rm):
    em = juego.entity_manager
    img = rm.get_image_scaled("jefe1", Jefe.TAMANO_JEFE)
    jefe = Jefe(img, 200, 200, 600, 800, 1, juego.jugador)
    jefe.salud = 1
    juego.jefe = jefe
    em.agregar_enemigo(jefe)

    b = _bala_jugador(rm)
    b.rect.center = jefe.rect.center
    b.radius = 300
    em.agregar_bala_jugador(b)

    juego.collision_manager.actualizar(juego.tiempo_juego)
    assert juego.pendiente_reinicio is True


class _ReglasEspia:
    """Doble del contrato `reglas` que consume CollisionManager."""
    def __init__(self):
        self.enemigos_eliminados = []
        self.impactos_jugador = 0

    def al_eliminar_enemigo(self, enemigo):
        self.enemigos_eliminados.append(enemigo)

    def manejar_impacto_jugador(self):
        self.impactos_jugador += 1


def test_collision_manager_no_toca_juego_usa_el_contrato_reglas(juego, rm):
    """CollisionManager funciona con un `reglas` cualquiera, sin ver el Juego."""
    em = juego.entity_manager
    reglas = _ReglasEspia()
    cm = CollisionManager(em, juego.jugador, juego.effect_manager,
                          juego.audio_manager, juego.enemigos_golpeados, reglas)

    e = _enemigo(rm, salud=1)
    b = _bala_jugador(rm)
    b.rect.center = e.rect.center
    em.agregar_enemigo(e)
    em.agregar_bala_jugador(b)

    cm.actualizar(0)

    assert reglas.enemigos_eliminados == [e]   # la regla se delegó, no se aplicó aquí
    assert e not in em.enemigos                 # la parte mecánica sí


def test_recoger_item(juego, rm):
    from src.entities.items import Item
    em = juego.entity_manager
    img = rm.get_image_scaled("potenciador_velocidad", Item.TAMANO_ESTANDAR)
    item = Item("potenciador_velocidad", img, *juego.jugador.rect.center)
    em.items.add(item)

    vel0 = juego.jugador.velocidad
    juego.collision_manager.actualizar(juego.tiempo_juego)

    assert item not in em.items
    assert juego.jugador.velocidad > vel0
