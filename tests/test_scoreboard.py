"""src/ui/scoreboard.py — tabla de puntuaciones."""
import json

from src.ui.scoreboard import SistemaClasificacion


def test_arranca_vacio(scoreboard):
    assert scoreboard.puntuaciones == {}
    assert scoreboard.obtener_puntuaciones_top() == []


def test_agregar_puntuacion_nueva(scoreboard):
    scoreboard.agregar_puntuacion("Ana", 100)
    assert scoreboard.puntuaciones["Ana"] == 100


def test_solo_guarda_si_mejora(scoreboard):
    scoreboard.agregar_puntuacion("Ana", 100)
    scoreboard.agregar_puntuacion("Ana", 50)   # peor: se ignora
    assert scoreboard.puntuaciones["Ana"] == 100
    scoreboard.agregar_puntuacion("Ana", 200)  # mejor: actualiza
    assert scoreboard.puntuaciones["Ana"] == 200


def test_top_ordenado_y_limitado(scoreboard):
    for nombre, pts in [("A", 10), ("B", 90), ("C", 50), ("D", 70)]:
        scoreboard.agregar_puntuacion(nombre, pts)
    top = scoreboard.obtener_puntuaciones_top(n=2)
    assert top == [("B", 90), ("D", 70)]


def test_persistencia(tmp_path):
    ruta = str(tmp_path / "pts.json")
    s1 = SistemaClasificacion(ruta_archivo=ruta)
    s1.agregar_puntuacion("Ana", 123)

    s2 = SistemaClasificacion(ruta_archivo=ruta)
    assert s2.puntuaciones == {"Ana": 123}


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
    assert json.loads(ruta.read_text())["Ana"] == 1
