# Roadmap

Documento vivo: qué está hecho, qué se está haciendo y qué vendrá después. No es un
compromiso de fechas; el orden se reajusta por impacto. El detalle de cada versión
está en [`CHANGELOG.md`](CHANGELOG.md).

## Hecho

- **Auditoría integral** (Fases 1–4) — estabilidad, rendimiento, arquitectura y
  jugabilidad. Detalle en [`AUDITORIA.md`](AUDITORIA.md).
- **Repositorio** — licencia MIT, `requirements` saneados, `pyproject.toml`,
  `.gitattributes`, `.gitignore` acotado, `CONTRIBUTING.md`.
- **Tests** — suite `pytest` headless (~83 % de cobertura).
- **Integración continua** — GitHub Actions (Python 3.11–3.13) + badge de cobertura;
  `main` protegido.
- **Documentación** — README, este roadmap, `CHANGELOG.md`.
- **`v0.1.0`** publicada.
- **Fase 5 — bugs conocidos** — arreglados todos (menú de opciones, Game Over +
  teclado, reloj de juego que se pausa de verdad, tirón al cambiar de música,
  código muerto). Ver `CHANGELOG.md` → `[0.1.1]`.
- **Item 14 de la auditoría — adelgazar el objeto-Dios `Juego`** — los managers
  mecánicos (`Wave`, `Entity`, `Effect`, `Collision`) reciben dependencias
  explícitas y ya no tocan `Juego`; `CollisionManager` habla por un contrato
  `reglas`. La capa Vista/Controlador (`Input`, `Render`, `UI`) mantiene `Juego`
  a propósito.

## En curso

- Ajuste fino del balance (`src/core/settings.py`) a partir del playtest: dificultad,
  hitboxes, `JUGADOR_SUAVIZADO`.

## Próximo (corto plazo)

- Playtest del refactor del item 14 y del siguiente lote de cambios; publicar la
  versión que lo agrupe.

## Backlog / ideas

- **Actualización automática** — al abrir el menú, comprobar si hay una versión
  publicada más reciente que la instalada. Si la hay, mostrar un aviso con un botón
  **Actualizar**: al pulsarlo, el juego se actualiza solo (descarga y aplica el
  parche, se reinicia si hace falta) sin que el usuario tenga que salir a ninguna
  web ni descargar nada a mano. Comprobación en segundo plano y silenciosa si no
  hay red (sin conexión se puede seguir jugando con la versión actual). Depende del
  **empaquetado y distribución** (define el formato del artefacto a actualizar).
- **Empaquetado y distribución** — build con PyInstaller; publicación (itch.io u otro).
- **Game Design Document** formal.
- Más tipos de enemigo y patrones de disparo; jefes con fases.
- Menú de opciones ampliado: reasignar teclas, modo ventana/pantalla completa, resolución.
- Música de victoria (`Victory Tune.ogg` está en el repo pero sin usar).
- Persistencia de progreso entre sesiones.
- Efectos de sonido para explosiones / recogida de mejoras con más variedad.
