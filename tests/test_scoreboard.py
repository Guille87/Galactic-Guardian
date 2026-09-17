"""src/ui/scoreboard.py — tabla de puntuaciones."""
import json

from src.ui.scoreboard import SistemaClasificacion


def test_arranca_vacio(scoreboard):
    assert scoreboard.puntuaciones == {}
    assert scoreboard.obtener_puntuaciones_top() == []


def test_agregar_puntuacion_nueva(scoreboard):
    scoreboard.agregar_puntuacion("Ana", 100, nivel=3)
    assert scoreboard.puntuaciones["Ana"] == {"puntos": 100, "nivel": 3}


def test_nivel_es_opcional(scoreboard):
    scoreboard.agregar_puntuacion("Ana", 100)
    assert scoreboard.puntuaciones["Ana"] == {"puntos": 100, "nivel": None}


def test_solo_guarda_si_mejora(scoreboard):
    scoreboard.agregar_puntuacion("Ana", 100, nivel=2)
    scoreboard.agregar_puntuacion("Ana", 50, nivel=5)    # peor puntuación: se ignora entera
    assert scoreboard.puntuaciones["Ana"] == {"puntos": 100, "nivel": 2}
    scoreboard.agregar_puntuacion("Ana", 200, nivel=4)   # mejor: actualiza puntos y nivel
    assert scoreboard.puntuaciones["Ana"] == {"puntos": 200, "nivel": 4}


def test_top_ordenado_y_limitado(scoreboard):
    for nombre, pts in [("A", 10), ("B", 90), ("C", 50), ("D", 70)]:
        scoreboard.agregar_puntuacion(nombre, pts, nivel=1)
    top = scoreboard.obtener_puntuaciones_top(n=2)
    assert top == [("B", 90, 1), ("D", 70, 1)]


def test_persistencia(tmp_path):
    ruta = str(tmp_path / "pts.json")
    s1 = SistemaClasificacion(ruta_archivo=ruta)
    s1.agregar_puntuacion("Ana", 123, nivel=2)

    s2 = SistemaClasificacion(ruta_archivo=ruta)
    assert s2.puntuaciones == {"Ana": {"puntos": 123, "nivel": 2}}


def test_json_corrupto_no_crashea(tmp_path):
    ruta = tmp_path / "pts.json"
    ruta.write_text("{ esto no es json")
    s = SistemaClasificacion(ruta_archivo=str(ruta))
    assert s.puntuaciones == {}


def test_crea_directorio_de_guardado(tmp_path):
    ruta = tmp_path / "sub" / "carpeta" / "pts.json"
    s = SistemaClasificacion(ruta_archivo=str(ruta))
    s.agregar_puntuacion("Ana", 1)
    assert ruta.exists()
    assert json.loads(ruta.read_text())["Ana"]["puntos"] == 1


def test_formato_antiguo_sigue_funcionando(tmp_path):
    """Archivos de antes de la campaña guardaban un int suelto por nombre."""
    ruta = tmp_path / "pts.json"
    ruta.write_text(json.dumps({"Viejo": 500}))
    s = SistemaClasificacion(ruta_archivo=str(ruta))

    assert s.obtener_puntuaciones_top() == [("Viejo", 500, None)]

    s.agregar_puntuacion("Viejo", 600, nivel=4)   # mejora -> pasa a formato nuevo
    assert s.puntuaciones["Viejo"] == {"puntos": 600, "nivel": 4}
