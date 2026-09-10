# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-09-10

Primera versión con versionado. Incluye el juego base más una auditoría integral
de estabilidad, rendimiento, arquitectura y jugabilidad (ver `AUDITORIA.md`), y la
puesta a punto del repositorio (licencia, tests, integración continua, documentación).

### Added

- `src/core/settings.py`: constantes globales del juego (ventana, FPS, balance,
  hitboxes, umbrales de oleada) en un único sitio.
- Movimiento independiente de los FPS (delta time) con acumulador sub-pixel
  (`MovimientoSubpixel`).
- Tecla **F1**: overlay de depuración que dibuja los círculos de colisión, con
  aviso en pantalla de cómo desactivarlo.
- HUD en modo desarrollo: valores numéricos de las estadísticas, velocidad real
  por frame y vida del jefe.
- Música de fondo en *streaming* (`pygame.mixer.music`) en vez de cargarse entera
  en memoria; caché de imágenes rotadas para los proyectiles.
- Grupos de `pygame.sprite` para todas las entidades; colisiones vectorizadas
  (`groupcollide` / `collide_circle`).
- `LICENSE` (MIT), suite de tests con `pytest` (~77 % de cobertura), integración
  continua en GitHub Actions (Python 3.11–3.13) con badge de cobertura,
  `CHANGELOG.md`, `ROADMAP.md`, `CONTRIBUTING.md`, `requirements-dev.txt`,
  `.gitattributes` y `dependabot.yml`.

### Changed

- Flujo de pantallas reescrito como una máquina de estados de alto nivel en
  `main.py`: menú y partida devuelven el siguiente estado en lugar de instanciarse
  entre sí.
- Un único `AudioManager` compartido entre el menú y la partida.
- Curva de dificultad: la salud enemiga pasa de exponencial (`×2` por nivel) a
  lineal.
- El jefe aparece antes en los niveles altos; escala de daño de las balas
  unificada y legible.
- Menú de opciones migrado a la API de eventos de `pygame_gui` 0.6.
- Tamaño de sprite de las balas y radios de colisión recalibrados.
- `requirements.txt` reescrito en UTF-8 (antes UTF-16, ilegible por `pip` en Linux);
  `.gitignore` con globs acotados.

### Fixed

- Volver al menú principal desde la partida cerraba el proceso.
- Bucles de diálogo (confirmar salida, opciones en pausa) consumían el 100 % de una
  CPU.
- Fuga de memoria: `enemigos_golpeados` retenía enemigos ya destruidos.
- `reiniciar_juego()` se ejecutaba en mitad del bucle de colisiones.
- La pausa no congelaba la progresión de la oleada: una pausa larga te llevaba
  directo a la pelea del jefe.
- El jefe y los enemigos con giro casi vertical se quedaban atascados en los
  bordes de la pantalla.
- Las balas enemigas salían desviadas (el vector se calculaba desde el centro del
  enemigo, no desde el punto de disparo).
- El fundido del destello de daño no se veía.
- El menú de opciones no respondía (API antigua de `pygame_gui`).

### Removed

- Contador `enemigos_activos` (solo se decrementaba, nunca se incrementaba).
- `Proyectil.comprobar_colision` y el grupo `juego.all_sprites` (sustituidos por
  los grupos tipados y `groupcollide`).
- `__init__.py` vacío en la raíz del repositorio.

[Unreleased]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Guille87/Galactic-Guardian/releases/tag/v0.1.0
