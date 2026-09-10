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
- **Recursos**: registra el nombre lógico y su ruta en `src/core/config.py`
  (`RECURSOS`, `MUSICA`, `SONIDOS`, `EXPLOSIONES`); nunca escribas rutas de assets
  a mano en el código.
- **Temporizadores y pausa**: cualquier lógica con cuenta atrás debe basarse en
  `dt` (frame-independiente) o desplazar su marca de tiempo en
  `Juego.reanudar_juego()`. Si no, la pausa no la congela.
- **Movimiento**: usa `MovimientoSubpixel._desplazar(vx, vy, dt)` para mover un
  `rect`; las velocidades se expresan en px/frame-a-60fps.

## Añadir un enemigo o un ítem

El patrón completo está en [CLAUDE.md](CLAUDE.md). En resumen:

- **Enemigo**: una clase en `src/entities/enemies.py` que herede de `EnemigoBase`.
  Sobrescribe `FACTOR_NIVEL` si escala distinto, e implementa
  `disparo_enemigo(ahora, rm, nombre_bala)` si dispara. Regístralo en
  `WaveManager._get_ruta` y colócalo en la fase correspondiente de
  `WaveManager._obtener_config_enemigo`. Añade su sprite a `config.RECURSOS`.
- **Ítem**: añade el efecto a `Item.EFECTOS` (`src/entities/items.py`), el tipo a
  `EnemigoBase.CANDIDATOS_LOOT` y su condición de utilidad a
  `EnemigoBase._loot_util`. Añade su sprite a `config.RECURSOS`.

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

En la versión compilada, `config.ini` y las puntuaciones se guardan en
`%APPDATA%\GalacticGuardian` (no junto al `.exe`).

## Publicar una versión

El proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/): `MAJOR`
para cambios incompatibles, `MINOR` para funcionalidad nueva compatible, `PATCH`
para correcciones.

1. Sube `version` en `pyproject.toml` **y** `__version__` en `src/core/version.py`
   (un test comprueba que coinciden).
2. En [`CHANGELOG.md`](CHANGELOG.md), mueve las entradas de *Unreleased* a una
   nueva sección `## [X.Y.Z] - AAAA-MM-DD` y actualiza los enlaces de comparación
   del pie.
3. Etiqueta y sube:

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. Crea la *Release* en GitHub desde el tag, con las notas del CHANGELOG.

> Adjuntar el `.zip` del ejecutable a la Release todavía es manual (compílalo como
> arriba y súbelo). El workflow que lo hace al etiquetar está en el [ROADMAP](ROADMAP.md).
