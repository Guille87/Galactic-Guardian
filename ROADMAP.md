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

## En curso

- Ajuste fino del balance (`src/core/settings.py`) a partir del playtest: dificultad,
  hitboxes, `JUGADOR_SUAVIZADO`.

## Próximo (corto plazo)

- **`v0.1.1`** + release en GitHub (Fase 5).
- Adelgazar el "objeto-Dios" `Juego`: que los managers reciban solo lo que usan
  (pendiente de la auditoría, item 14).

## Backlog / ideas

- **Empaquetado y distribución** — build con PyInstaller; publicación (itch.io u otro).
- **Game Design Document** formal.
- Más tipos de enemigo y patrones de disparo; jefes con fases.
- Menú de opciones ampliado: reasignar teclas, modo ventana/pantalla completa, resolución.
- Música de victoria (`Victory Tune.ogg` está en el repo pero sin usar).
- Persistencia de progreso entre sesiones.
- Efectos de sonido para explosiones / recogida de mejoras con más variedad.
