"""Mejoras permanentes (src/core/mejoras.py) y su guardado (src/core/progresion.py)."""
import json

import pytest

from src.core import i18n, mejoras, progresion
from src.core.mejoras import Bonus, MEJORAS, POR_ID, RAMAS, calcular_bonus, de_la_rama
from src.core.progresion import Progresion


@pytest.fixture
def prog(tmp_path):
    return Progresion(ruta=str(tmp_path / "progresion.json"))


# --- La tabla de mejoras -----------------------------------------------------

def test_hay_tres_ramas_de_cuatro_mejoras():
    assert RAMAS == ("ataque", "defensa", "utilidad")
    assert all(len(de_la_rama(r)) == 4 for r in RAMAS)
    assert len(MEJORAS) == 12 and len(POR_ID) == 12          # ids únicos


def test_cada_rama_es_una_cadena_ordenada_y_los_costes_suben():
    for rama in RAMAS:
        cadena = de_la_rama(rama)
        assert cadena[0].requiere is None
        assert [m.requiere for m in cadena[1:]] == [m.id for m in cadena[:-1]]
        costes = [m.coste for m in cadena]
        assert costes == sorted(costes) and costes[0] > 0


def test_los_efectos_usan_campos_del_bonus_y_valores_validos():
    campos = set(Bonus.__dataclass_fields__)
    for m in MEJORAS:
        assert m.efecto and set(m.efecto) <= campos, m.id


@pytest.mark.parametrize("codigo", i18n.IDIOMAS)
def test_cada_mejora_y_rama_tiene_texto_en_cada_idioma(codigo):
    i18n.establecer_idioma(codigo)
    for m in MEJORAS:
        for clave in (f"mejoras.{m.id}.nombre", f"mejoras.{m.id}.desc"):
            assert i18n.t(clave) != clave, (codigo, clave)
    for rama in RAMAS:
        assert i18n.t(f"mejoras.rama_{rama}") != f"mejoras.rama_{rama}"


# --- Bonus -------------------------------------------------------------------

def test_sin_mejoras_el_bonus_es_neutro():
    assert calcular_bonus([]) == Bonus()
    b = Bonus()
    assert (b.salud_extra, b.vidas_extra, b.danio_extra, b.cadencia_menos_ms) == (0, 0, 0, 0)
    assert (b.disparo_inicial, b.monedas_pct, b.combo_factor) == ("simple", 0.0, 1.0)


def test_los_efectos_numericos_se_suman():
    b = calcular_bonus(["defensa_1", "defensa_3", "ataque_2", "ataque_3"])
    assert b.salud_extra == 2 and b.cadencia_menos_ms == 100


def test_efectos_especiales():
    b = calcular_bonus(["ataque_4", "utilidad_2", "utilidad_3", "utilidad_4", "defensa_4", "defensa_2", "utilidad_1"])
    assert b.disparo_inicial == "doble"
    assert b.monedas_pct == pytest.approx(0.5)                   # Botín I (+25 %) y Botín II (+25 %)
    assert b.combo_factor == pytest.approx(0.8)
    assert b.invulnerable_extra_ms == 2000 and b.vidas_extra == 1 and b.velocidad_extra == pytest.approx(0.5)


def test_ids_desconocidos_se_ignoran():
    assert calcular_bonus(["no_existe", "ataque_1"]).danio_extra == 1


# --- Compra ------------------------------------------------------------------

def test_arranca_sin_monedas_ni_mejoras(prog):
    assert prog.monedas == 0 and prog.compradas == set() and prog.bonus() == Bonus()


def test_ingresar_suma_e_ignora_lo_no_positivo(prog):
    prog.ingresar(50)
    prog.ingresar(0)
    prog.ingresar(-10)
    assert prog.monedas == 50


def test_comprar_descuenta_el_coste_y_aplica_el_bonus(prog):
    prog.ingresar(150)
    assert prog.comprar("ataque_1") == progresion.OK
    assert prog.monedas == 150 - POR_ID["ataque_1"].coste
    assert prog.estado("ataque_1") == progresion.COMPRADA
    assert prog.bonus().danio_extra == 1


def test_no_se_compra_sin_saldo_suficiente(prog):
    prog.ingresar(POR_ID["ataque_1"].coste - 1)
    assert prog.comprar("ataque_1") == progresion.SIN_SALDO
    assert prog.monedas == POR_ID["ataque_1"].coste - 1 and not prog.compradas


def test_no_se_compra_una_mejora_bloqueada_aunque_sobren_monedas(prog):
    prog.ingresar(10_000)
    assert prog.estado("ataque_2") == progresion.BLOQUEADA
    assert prog.comprar("ataque_2") == progresion.BLOQUEADA
    assert prog.monedas == 10_000


def test_comprar_desbloquea_la_siguiente_de_la_rama_y_solo_esa(prog):
    prog.ingresar(10_000)
    prog.comprar("ataque_1")
    assert prog.estado("ataque_2") == progresion.DISPONIBLE
    assert prog.estado("ataque_3") == progresion.BLOQUEADA
    assert prog.estado("defensa_1") == progresion.DISPONIBLE         # otra rama: su primera es libre
    assert prog.estado("defensa_2") == progresion.BLOQUEADA


def test_no_se_compra_dos_veces_ni_algo_que_no_existe(prog):
    prog.ingresar(1000)
    prog.comprar("ataque_1")
    saldo = prog.monedas
    assert prog.comprar("ataque_1") == progresion.YA_COMPRADA
    assert prog.comprar("no_existe") == progresion.DESCONOCIDA
    assert prog.monedas == saldo


# --- Restablecer -------------------------------------------------------------

def test_restablecer_devuelve_todo_lo_gastado_y_quita_los_bonus(prog):
    prog.ingresar(1000)
    prog.comprar("ataque_1")
    prog.comprar("ataque_2")
    prog.comprar("defensa_1")
    gastado = sum(POR_ID[i].coste for i in ("ataque_1", "ataque_2", "defensa_1"))
    assert prog.monedas == 1000 - gastado

    assert prog.restablecer() == gastado
    assert prog.monedas == 1000 and prog.compradas == set() and prog.bonus() == Bonus()


def test_restablecer_sin_compras_no_cambia_nada(prog):
    prog.ingresar(30)
    assert prog.restablecer() == 0 and prog.monedas == 30


# --- Guardado ----------------------------------------------------------------

def test_todo_se_guarda_y_se_recupera(tmp_path):
    ruta = str(tmp_path / "p.json")
    a = Progresion(ruta=ruta)
    a.ingresar(500)
    a.comprar("utilidad_1")
    a.comprar("utilidad_2")

    b = Progresion(ruta=ruta)                                       # otra "sesión"
    assert b.monedas == a.monedas and b.compradas == {"utilidad_1", "utilidad_2"}


def test_cada_cambio_se_escribe_al_momento(tmp_path):
    ruta = tmp_path / "p.json"
    p = Progresion(ruta=str(ruta))
    p.ingresar(10)
    assert json.loads(ruta.read_text())["monedas"] == 10
    p.restablecer()
    assert json.loads(ruta.read_text()) == {"version": 1, "monedas": 10, "mejoras": []}


def test_no_deja_archivos_temporales(tmp_path):
    p = Progresion(ruta=str(tmp_path / "p.json"))
    p.ingresar(10)
    assert [f.name for f in tmp_path.iterdir()] == ["p.json"]


def test_sin_persistir_no_toca_el_disco(tmp_path):
    ruta = tmp_path / "no_debe_existir.json"
    p = Progresion(ruta=str(ruta), persistir=False)
    p.ingresar(100)
    p.comprar("ataque_1")
    assert not ruta.exists() and p.monedas == 100 - POR_ID["ataque_1"].coste


def test_crea_la_carpeta_de_guardado_si_no_existe(tmp_path):
    ruta = tmp_path / "data" / "saves" / "p.json"
    Progresion(ruta=str(ruta)).ingresar(5)
    assert ruta.exists()


# --- Carga tolerante ---------------------------------------------------------

@pytest.mark.parametrize("contenido", [
    "esto no es json {{{", "[1, 2, 3]", '{"monedas": "muchas"}', '{"monedas": 5, "mejoras": "ataque_1"}',
    '{"monedas": true}', "",
])
def test_un_archivo_ilegible_se_aparta_y_se_empieza_de_cero(tmp_path, contenido):
    ruta = tmp_path / "p.json"
    ruta.write_text(contenido)
    p = Progresion(ruta=str(ruta))
    assert p.monedas == 0 and p.compradas == set()
    assert (tmp_path / "p.json.corrupto").read_text() == contenido       # no se pierde lo que había


def test_los_datos_sueltos_invalidos_se_ignoran(tmp_path):
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps({"monedas": -50, "mejoras": ["ataque_1", "no_existe", 7, None]}))
    p = Progresion(ruta=str(ruta))
    assert p.monedas == 0 and p.compradas == {"ataque_1"}


def test_una_mejora_sin_su_requisito_se_descarta_y_se_devuelve_su_coste(tmp_path):
    """Archivo editado a mano: `ataque_3` sin `ataque_2` no es alcanzable."""
    ruta = tmp_path / "p.json"
    ruta.write_text(json.dumps({"monedas": 10, "mejoras": ["ataque_1", "ataque_3", "ataque_4"]}))
    p = Progresion(ruta=str(ruta))
    assert p.compradas == {"ataque_1"}
    assert p.monedas == 10 + POR_ID["ataque_3"].coste + POR_ID["ataque_4"].coste


def test_sin_archivo_empieza_vacia(tmp_path):
    assert Progresion(ruta=str(tmp_path / "no_existe.json")).monedas == 0


def test_la_ruta_por_defecto_es_la_carpeta_de_datos_de_usuario(monkeypatch, tmp_path):
    monkeypatch.setattr("src.core.paths.dir_datos_usuario", lambda: str(tmp_path))
    p = Progresion()
    assert p.ruta == str(tmp_path / "data" / "saves" / "progresion.json")
