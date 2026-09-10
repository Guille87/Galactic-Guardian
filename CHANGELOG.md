# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Added

- La versión del juego se muestra en el título de la ventana y en la esquina del
  menú principal (`src/core/version.py` como fuente única).

### Changed

- Rutas centralizadas en `src/core/paths.py`, preparadas para el empaquetado:
  los recursos se resuelven contra la carpeta del bundle y los datos de usuario
  (`config.ini`, puntuaciones) contra una ruta escribible. En desarrollo no
  cambia nada salvo que las rutas pasan a ser absolutas (ya no dependen del
  directorio desde el que se lanza el juego).

## [0.1.2] - 2026-09-10

Refactor interno (cierre del item 14 de la auditoría) y un ajuste de jugabilidad.
Sin cambios incompatibles.

### Changed

- Al derrotar al jefe y pasar de nivel ya no desaparece **ninguna** bala en
  vuelo (antes solo se conservaban las del jefe; ahora también las del jugador).
- Interno (item 14 de la auditoría, reducir el objeto-Dios `Juego`): al reiniciar
  una partida el jugador se restablece "in situ" en vez de recrearse; los
  managers mecánicos (`Entity`, `Effect`, `Collision`) reciben sus dependencias
  explícitas en vez del `Juego` entero, y `CollisionManager` comunica los
  cambios de estado (puntuación, loot, daño al jugador) por un contrato `reglas`
  en lugar de escribir atributos de `Juego`. Sin cambios visibles.

## [0.1.1] - 2026-09-10

Correcciones de bugs y pulido posteriores a la 0.1.0. Sin cambios incompatibles.

### Added

- Menú de opciones: etiquetas **"Música"** y **"Efectos"** sobre cada slider.
- HUD en modo desarrollo: contador de tiempo de juego (`t: N.N s`), útil para ver
  que el reloj se detiene en pausa.

### Changed

- El tiempo del juego pasa a un **reloj propio** (`Juego.tiempo_juego`) que solo
  avanza mientras se juega. Elimina de raíz la clase de bugs de pausa (disparo en
  ráfaga al reanudar, salto directo a la pelea del jefe, invulnerabilidad
  descuadrada). Se eliminan los métodos `actualizar_pausa`.

### Fixed

- **Tirón de ~200-400 ms** (imagen congelada) al cambiar de música: aparición del
  jefe, muerte del jefe y Game Over. Los OGG se cargan desde RAM y la pista se
  corta en seco (`stop()`) en vez de con `fadeout()`, que bloqueaba la carga
  siguiente.
- Menú de opciones: las flechas ◄ ► de los sliders de volumen saltaban al
  máximo/mínimo; ahora suben/bajan de 0.10 en 0.10.
- Menú de opciones: al pulsar las flechas del slider de efectos rápido, el sonido
  de prueba solo se oía la primera vez.
- Game Over: pulsar `Esc`/`P` reanudaba la partida con los temporizadores
  descuadrados. El teclado ya no hace nada en esa pantalla.

### Removed

- Código muerto: `hud._dibujar_atributo`, `hud._dibujar_texto`,
  `input._manejar_clic_soltado`.

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

[Unreleased]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Guille87/Galactic-Guardian/releases/tag/v0.1.0
