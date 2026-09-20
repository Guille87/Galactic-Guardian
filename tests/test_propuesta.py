"""tools/propuesta.py: la propuesta de reequilibrio cumple los criterios de diseño acordados.

Cada test es un objetivo (no un detalle de implementación): si al retocar un número
deja de cumplirse, hay que decidir si el objetivo cambia o el número se corrige.
"""
import pytest

from src.entities.enemies import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from tools import propuesta as P
from tools.balance import PERFILES, analizar_nivel, build_al, jugar, orden_de_compra, progresion

M = P.MODELO_PROPUESTO
CAMPANA = 5


def _nave(fraccion):
    return M.nave(build_al(orden_de_compra(M.arbol), fraccion)[0])


# --- La nave base -----------------------------------------------------------------------

def test_la_nave_base_es_la_acordada():
    n = _nave(0)
    assert (n.salud, n.vidas, n.danio, n.balas, n.disparos_s, n.velocidad) == (50, 3, 10, 1, 4.0, 5.0)


def test_la_velocidad_base_sube_a_5_y_su_tope_no_cambia():
    assert P.BASE["velocidad"] == 5.0 and P.TOPES["velocidad"] == 6.0


def test_la_cadencia_base_sube_y_el_tope_es_un_numero_limpio():
    assert P.BASE["disparos_s"] == 4.0 > 1000 / 350
    assert P.TOPES["disparos_s"] == 8.0                       # 125 ms; antes 6,7 (150 ms)


# --- El árbol -----------------------------------------------------------------------------

def test_el_arbol_son_tres_ramas_encadenadas_con_costes_crecientes():
    for rama in ("ataque", "defensa", "utilidad"):
        cadena = [n for n in P.ARBOL if n.rama == rama]
        assert len(cadena) >= 5 and cadena[0].requiere is None
        assert [n.requiere for n in cadena[1:]] == [n.id for n in cadena[:-1]]
        assert [n.coste for n in cadena] == sorted(n.coste for n in cadena)


def test_el_arbol_da_2_y_3_balas_mas_dano_y_regeneracion():
    efectos = {c for n in P.ARBOL for c in n.efecto}
    assert {"danio", "balas", "disparos_s", "regen_s", "salud", "vidas", "velocidad", "monedas_pct"} <= efectos
    assert _nave(1.0).balas == 3 and _nave(1.0).regen_s > 0


def test_ninguna_mejora_supera_los_topes():
    n = _nave(1.0)
    assert n.danio <= P.TOPES["danio"] and n.disparos_s <= P.TOPES["disparos_s"]
    assert n.balas <= P.TOPES["balas"] and n.velocidad <= P.TOPES["velocidad"]


def test_los_efectos_usan_campos_de_la_nave():
    from dataclasses import fields
    from tools.balance import Nave
    campos = {f.name for f in fields(Nave)}
    assert all(set(n.efecto) <= campos for n in P.ARBOL)


# --- Las tablas por nivel --------------------------------------------------------------------

def test_las_tablas_crecen_con_el_nivel():
    assert list(P.VIDA_X) == sorted(P.VIDA_X) and list(P.VIDA_JEFE) == sorted(P.VIDA_JEFE)
    assert list(P.DANIO_X) == sorted(P.DANIO_X)
    assert all(len(t) == CAMPANA for t in (P.VIDA_X, P.VIDA_JEFE, P.DANIO_X, P.INTERVALOS))


def test_la_densidad_de_enemigos_nunca_hace_imposible_un_nivel():
    """Con el intervalo antiguo del nivel 5 (200 ms) ni el DPS infinito bastaba."""
    medio = PERFILES["medio"]
    nave = _nave(1.0)
    for n in range(1, CAMPANA + 1):
        assert analizar_nivel(nave, n, medio, M).muertes(nave) < 2.0


def test_las_vidas_de_enemigos_son_enteros_positivos():
    for n in range(1, CAMPANA + 1):
        for clase in (EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe):
            assert isinstance(M.vida(clase, n), int) and M.vida(clase, n) > 0


# --- Los objetivos de dificultad y de progresión -------------------------------------------------

@pytest.mark.parametrize("perfil", PERFILES)
def test_ni_la_primera_partida_completa_la_campana(perfil):
    p = jugar(_nave(0), PERFILES[perfil], M)
    assert not p.victoria and p.nivel_alcanzado < 3


@pytest.mark.parametrize("perfil", PERFILES)
def test_el_nivel_1_se_supera_sin_mejoras(perfil):
    assert jugar(_nave(0), PERFILES[perfil], M).nivel_alcanzado >= 1.0


@pytest.mark.parametrize("perfil", PERFILES)
def test_con_el_arbol_entero_todos_los_perfiles_completan_la_campana(perfil):
    assert jugar(_nave(1.0), PERFILES[perfil], M).victoria


def test_el_nivel_5_exige_mejoras():
    """Sin ninguna, ni el jugador hábil llega al final."""
    assert not jugar(_nave(0), PERFILES["habil"], M).victoria


def test_el_perfil_medio_completa_la_campana_en_unas_20_partidas():
    n = progresion(PERFILES["medio"], M).partidas_hasta_victoria
    assert 16 <= n <= 24, n


def test_mejor_jugador_completa_antes():
    runs = {k: progresion(p, M).partidas_hasta_victoria for k, p in PERFILES.items()}
    assert 0 < runs["habil"] < runs["medio"] < runs["torpe"]


def test_la_primera_mejora_llega_en_las_primeras_partidas_y_no_hay_llanuras_largas():
    pr = progresion(PERFILES["medio"], M)
    partidas = sorted({n for n, _ in pr.compras})
    assert partidas[0] <= 2
    assert max(b - a for a, b in zip(partidas, partidas[1:])) <= 4


def test_una_partida_media_da_para_la_primera_mejora_pronto():
    monedas = jugar(_nave(0), PERFILES["medio"], M).monedas
    assert monedas >= min(n.coste for n in P.ARBOL) * 0.8


# --- El informe -----------------------------------------------------------------------------------

def test_el_informe_de_la_propuesta_se_imprime(capsys):
    P.main(["--perfil", "todos", "--builds", "0,100"])
    salida = capsys.readouterr().out
    for texto in ("NAVE BASE Y ÁRBOL (propuesta)", "PARTIDA ESPERADA", "PODER QUE EXIGE", "PROGRESIÓN",
                  "Calendario de compras"):
        assert texto in salida, texto
