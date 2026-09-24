# Contribuir

Gracias por tu interés. El proyecto es pequeño; estas son las convenciones.

## Antes de empezar

- **Python 3.11 o superior** (el CI corre 3.11–3.13).
- `pip install -r requirements-dev.txt` instala lo de runtime + `pytest` y
  `pytest-cov`. No hace falta nada más.
- Funciona en Windows, Linux y macOS (pygame es multiplataforma).
- Los comandos del día a día están en el [README](README.md); la arquitectura, en
  [CLAUDE.md](CLAUDE.md); la auditoría de deuda técnica, en [AUDITORIA.md](AUDITORIA.md);
  lo que hay pendiente, en [ROADMAP.md](ROADMAP.md).

## Flujo de trabajo

1. Crea una rama desde `main`.
2. Un commit por unidad lógica de cambio.
3. Antes de abrir el PR: `pytest` tiene que pasar en verde. Si tocas lógica,
   añade o ajusta su test.
4. Abre un pull request contra `main`. El CI ejecuta la suite en Python 3.11–3.13
   (Ubuntu, pygame headless) y actualiza el badge de cobertura: tiene que quedar
   todo verde.
5. `main` está protegido: solo entra vía PR con el CI en verde.

## Convenciones

- **Código, comentarios y docstrings en español**, como el resto del proyecto.
- **Mensajes de commit**: prefijo `feat:`, `fix:`, `perf:`, `refactor:`, `balance:`,
  `test:`, `docs:`, `ci:`, `build:`, `style:` o `chore:`, y el resto en imperativo.
- **Números "mágicos" a `src/core/settings.py`** (ventana, FPS, balance, hitboxes,
  umbrales de oleada). Las constantes propias de una clase se quedan en la clase
  (`Jugador.CONFIG`, `EnemigoBase.TAMANO_ESTANDAR`, `Bala.TAMANO`...).
- **Textos visibles**: nunca escritos a mano en la pantalla; van al catálogo
  (`data/assets/idiomas/es.json`) y se piden con `t("espacio.clave", n=...)`
  (`src/core/i18n.py`). El español es el idioma de referencia.
- **Recursos**: registra el nombre lógico y su ruta en `src/core/config.py`
  (`RECURSOS`, `HOJAS`, `MUSICA`, `SONIDOS`); nunca escribas rutas de assets
  a mano en el código.
- **Temporizadores y pausa**: cualquier lógica con cuenta atrás debe basarse en
  `dt` (frame-independiente) o desplazar su marca de tiempo en
  `Juego.reanudar_juego()`. Si no, la pausa no la congela.
- **Movimiento**: usa `MovimientoSubpixel._desplazar(vx, vy, dt)` para mover un
  `rect`; las velocidades se expresan en px/frame-a-60fps.

## Añadir un idioma

1. Copia `data/assets/idiomas/es.json` a `<codigo>.json` (p. ej. `fr.json`) y
   traduce los valores; no cambies las claves ni los huecos `{n}`, `{version}`…
2. Añade el código a `IDIOMAS` y su nombre en ese idioma a `NOMBRES`
   (`src/core/i18n.py`). Aparece solo en el selector de Opciones.
3. `pytest`: comprueba que tiene las mismas claves y los mismos huecos que el
   español. Si el idioma usa un alfabeto que la fuente por defecto de pygame no
   cubre, habrá que cargar otra fuente.

## Añadir un enemigo o una mejora

El patrón completo está en [CLAUDE.md](CLAUDE.md). En resumen:

- **Enemigo**: una clase en `src/entities/enemies.py` que herede de `EnemigoBase`.
  Dale su `SALUD_BASE` (la vida en el nivel 1; `src/core/escalado.py` la
  multiplica por nivel) e implementa
  `disparo_enemigo(ahora, rm, nombre_bala)` si dispara (usa
  `self.danio_escalado(...)` para el daño de la bala). Ponle `RECURSO` (el
  nombre lógico de su sprite), añade ese sprite a `config.RECURSOS` y
  colócalo en las `Fase` de los niveles que quieras en `src/core/niveles.py`.
- **Mejora del árbol**: una `Mejora` más en `mejoras.MEJORAS` (`src/core/mejoras.py`) con
  su rama, coste, `requiere` (la anterior de su rama) y su `efecto` (campos de `Bonus`), y
  sus textos `mejoras.<id>.nombre` y `mejoras.<id>.desc` en cada idioma (la descripción no
  debe pasar de 3 líneas: un test lo comprueba). Un efecto nuevo necesita además un campo
  en `Bonus` y que `Jugador` lo aplique. Después vuelve a correr `python tools/balance.py`
  y `pytest`: `tests/test_diseno_balance.py` guarda los objetivos de diseño.

Todo cambio de lógica viene con su test.

## Compilar un ejecutable

El juego se empaqueta con **PyInstaller** en modo carpeta (Windows):

```bash
pip install -r requirements-build.txt
pyinstaller GalacticGuardian.spec --noconfirm --clean
```

Genera `dist/GalacticGuardian/` (`GalacticGuardian.exe` + `_internal/`). Para
verificar el build sin abrir ventana:

```bash
dist/GalacticGuardian/GalacticGuardian.exe --smoke
```

Carga todos los recursos, hace unos frames de menú y de partida y sale con
código 0 si todo va bien. El `.spec` incluye `data/assets/` y los datos de
`pygame_gui`; si añades otra dependencia que cargue archivos en runtime, hay que
sumarla ahí (`collect_data_files`).

El instalador (`installer.iss`, Inno Setup 6) se genera a partir de `dist/`:

```bash
iscc /DVersion=0.1.4 installer.iss   # -> GalacticGuardian-setup.exe
```

En una Release, `build.yml` compila y sube el `.zip` y el `-setup.exe`.

En la versión compilada, `config.ini` y las puntuaciones se guardan en
`%APPDATA%\GalacticGuardian` (no junto al `.exe`).

## Herramienta de balance

`tools/balance.py` es un script de desarrollo (no forma parte del juego) que estima
la dificultad de la campaña y la economía a partir de los datos reales del juego:

```bash
python tools/balance.py                  # informe del juego tal como está
python tools/balance.py --perfil todos   # con los tres perfiles de jugador
python tools/balance.py --niveles        # detalle por fase de cada nivel
```

Es un modelo analítico, no una simulación: sirve como brújula para fijar la
curva de dificultad y el precio de las mejoras, y los números definitivos se
afinan jugando. Si cambias vida, daño, niveles o el árbol, vuelve a correrlo.

## Publicar una versión

El proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/): `MAJOR`
para cambios incompatibles, `MINOR` para funcionalidad nueva compatible, `PATCH`
para correcciones.

**No se publica una versión por cada PR.** Cada PR añade su entrada a *Unreleased*
del CHANGELOG y no toca la versión; una release se publica cuando hay un
conjunto de cambios con sentido, con varias entradas y un motivo para que alguien
quiera actualizar (una función grande terminada, o varias cosas que juntas
cambian cómo se juega). Las correcciones urgentes sí pueden salir solas, como
versión `PATCH`. Los cambios que ya están en `main` se prueban ejecutando desde
el código, sin esperar a una release.

1. Sube `version` en `pyproject.toml` **y** `__version__` en `src/core/version.py`
   (un test comprueba que coinciden).
2. En [`CHANGELOG.md`](CHANGELOG.md), mueve las entradas de *Unreleased* a una
   nueva sección `## [X.Y.Z] - AAAA-MM-DD` y actualiza los enlaces de comparación
   del pie.
3. Si hay algo que merezca contárselo al jugador (no cada PATCH), añade una entrada al
   **principio** de `HISTORIAL` en [`src/core/novedades.py`](src/core/novedades.py) (queda
   de la más reciente a la más antigua) y sus claves `novedades.*` en `es.json`/`en.json`,
   con un resumen en el tono del jugador (no el del CHANGELOG): la próxima vez que abra el
   menú tras actualizar verá esa pantalla una única vez, y siempre puede volver a verla
   (junto con las de versiones anteriores) pulsando el número de versión en el menú
   principal. Sin entrada nueva, esta versión no tiene nada que anunciar.
4. Etiqueta y sube:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. Crea la *Release* en GitHub desde el tag, con las notas del CHANGELOG. Al
   **publicarla**, el workflow `build.yml` compila el ejecutable de Windows y
   adjunta `GalacticGuardian-vX.Y.Z-windows.zip` a la Release (unos minutos).
   Para relanzarlo contra un tag ya publicado: *Actions → Build → Run workflow*.
