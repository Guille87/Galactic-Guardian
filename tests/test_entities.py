"""src/managers/entities.py — EntityManager (grupos de sprites)."""
from src.entities.enemies import EnemigoBase, EnemigoTipo1

DT60 = 1.0 / 60.0


def _enemigo(rm, x=300, y=100):
    img = rm.get_image_scaled("enemigo1", EnemigoBase.TAMANO_ESTANDAR)
    return EnemigoTipo1(img, x, y, 600, 1)


def test_grupos_arrancan_vacios(juego):
    em = juego.entity_manager
    assert all(len(g) == 0 for g in (em.balas, em.balas_enemigo, em.items, em.efectos))
    # `enemigos` puede tener spawns si el juego ya corrió; recién creado está vacío
    assert len(em.enemigos) == 0


def test_agregar_ignora_none(juego):
    em = juego.entity_manager
    em.agregar_enemigo(None)
    em.agregar_bala_jugador(None)
    assert len(em.enemigos) == 0 and len(em.balas) == 0


def test_agregar_enemigo(juego, rm):
    juego.entity_manager.agregar_enemigo(_enemigo(rm))
    assert len(juego.entity_manager.enemigos) == 1


def test_culling_fuera_de_pantalla(juego, rm):
    em = juego.entity_manager
    e = _enemigo(rm)
    em.agregar_enemigo(e)
    e.rect.y = -500                       # fuera por arriba
    em.actualizar(DT60)
    assert e not in em.enemigos


def test_culling_purga_enemigos_golpeados(juego, rm):
    em = juego.entity_manager
    e = _enemigo(rm)
    em.agregar_enemigo(e)
    juego.enemigos_golpeados[e] = 123
    e.rect.y = -500
    em.actualizar(DT60)
    assert e not in juego.enemigos_golpeados


def test_vaciar_todo(juego, rm):
    em = juego.entity_manager
    em.agregar_enemigo(_enemigo(rm))
    em.agregar_bala_enemigo(_enemigo(rm))   # sirve como sprite cualquiera
    em.vaciar_todo()
    assert len(em.enemigos) == 0 and len(em.balas_enemigo) == 0


def test_vaciar_todo_avance_nivel_conserva_balas_enemigas(juego, rm):
    em = juego.entity_manager
    em.agregar_enemigo(_enemigo(rm))
    em.agregar_bala_enemigo(_enemigo(rm))
    em.vaciar_todo(avance_nivel=True)
    assert len(em.enemigos) == 0            # los enemigos sí se limpian
    assert len(em.balas_enemigo) == 1       # las balas del jefe siguen volando
