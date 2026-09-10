# Roadmap

Documento vivo: qué está hecho, qué se está haciendo y qué vendrá después. No es un
compromiso de fechas; el orden se reajusta por impacto. El detalle de cada versión
está en [`CHANGELOG.md`](CHANGELOG.md).

## Hecho

- **Auditoría integral** (Fases 1–4) — estabilidad, rendimiento, arquitectura y
  jugabilidad. Detalle en [`AUDITORIA.md`](AUDITORIA.md).
- **Repositorio** — licencia MIT, `requirements` saneados, `pyproject.toml`,
  `.gitattributes`, `.gitignore` acotado.
- **Tests** — suite `pytest` headless (~77 % de cobertura).
- **Integración continua** — GitHub Actions (Python 3.11–3.13) + badge de cobertura.
- **Documentación** — README, este roadmap, `CHANGELOG.md`.

## En curso

- Ajuste fino del balance (`src/core/settings.py`) a partir del playtest: dificultad,
  hitboxes, `JUGADOR_SUAVIZADO`.

## Próximo (corto plazo)

- `CONTRIBUTING.md` (guía de contribución + proceso de publicación de versiones).
- Primer tag **`v0.1.0`** + release en GitHub.
- **Fase 5 — bugs conocidos** (ver abajo).
- Adelgazar el "objeto-Dios" `Juego`: que los managers reciban solo lo que usan
  (pendiente de la auditoría, item 14).

## Bugs conocidos (Fase 5)

Todos pre-existentes a la auditoría, no bloqueantes:

- **Opciones — flechas del slider:** las flechas ◄ ► del volumen de música y de
  efectos saltan al máximo/mínimo de golpe; deberían subir/bajar en pasos (p. ej. 0.10).
- **Opciones — sin etiquetas:** no hay texto que indique cuál es el slider de música
  y cuál el de efectos.
- **Game Over + `Esc`:** pulsar `Esc` en la pantalla de Game Over reanuda la partida
  con los temporizadores descuadrados (el estado de "congelado" reutiliza la pausa
  sin fijar su marca de tiempo).
- **Reloj de juego:** todo el tiempo se mide con `pygame.time.get_ticks()` + ajustes
  manuales en cada pausa. El arreglo de fondo es un reloj de juego propio que se
  pausa de verdad y elimina esta clase de bugs (metralleta al pausar, saltos de fase,
  invulnerabilidad...). Es un refactor transversal.
- Limpieza de código muerto (`hud._dibujar_atributo`, `hud._dibujar_texto`,
  `input._manejar_clic_soltado`).

## Backlog / ideas

- **Empaquetado y distribución** — build con PyInstaller; publicación (itch.io u otro).
- **Game Design Document** formal.
- Más tipos de enemigo y patrones de disparo; jefes con fases.
- Menú de opciones ampliado: reasignar teclas, modo ventana/pantalla completa, resolución.
- Música de victoria (`Victory Tune.ogg` está en el repo pero sin usar).
- Persistencia de progreso entre sesiones.
- Efectos de sonido para explosiones / recogida de mejoras con más variedad.
