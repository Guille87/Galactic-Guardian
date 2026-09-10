# PyInstaller — build en modo carpeta (onedir) para Windows.
#
#   pyinstaller GalacticGuardian.spec
#
# Genera dist/GalacticGuardian/ con GalacticGuardian.exe + _internal/. Se
# distribuye comprimida en zip. Ver CONTRIBUTING.md ("Compilar un ejecutable").

from PyInstaller.utils.hooks import collect_data_files

# Assets del juego + datos que pygame_gui carga en tiempo de ejecución (tema,
# fuentes por defecto): sin esto el menú de opciones peta al abrirse.
datas = [("data/assets", "data/assets")]
datas += collect_data_files("pygame_gui")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "_pytest", "coverage"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GalacticGuardian",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                       # sin ventana de consola
    disable_windowed_traceback=False,
    icon="data/assets/imagenes/favicon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GalacticGuardian",
)
