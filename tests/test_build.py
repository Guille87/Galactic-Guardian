"""Empaquetado: el arranque de humo (`main.py --smoke`) y el .spec."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def test_smoke_arranca_y_sale_con_codigo_0():
    """Lo que ejecuta el workflow de compilación para validar el ejecutable."""
    r = subprocess.run(
        [sys.executable, "main.py", "--smoke"],
        cwd=RAIZ, capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    assert "smoke OK" in r.stdout


def test_el_spec_esta_versionado_y_recoge_los_assets():
    spec = (RAIZ / "GalacticGuardian.spec").read_text(encoding="utf-8")
    assert '("data/assets", "data/assets")' in spec
    assert 'collect_data_files("pygame_gui")' in spec
