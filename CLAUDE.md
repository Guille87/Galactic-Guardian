# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Galactic Guardian is a 2D top-down space shooter built with **pygame-ce** and **pygame_gui**. The window is a fixed 600x800. Code, comments, identifiers, and docstrings are in **Spanish** — follow that convention when adding code.

## Commands

```bash
# Setup (Windows)
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Run the game (from the repo root)
python main.py

# Tests (headless; conftest.py forces the SDL dummy drivers)
pip install -r requirements-dev.txt
pytest
pytest --cov --cov-report=term-missing
```

`requirements.txt` pins `pygame-ce==2.5.8` and `pygame-gui==0.6.14` (note: `pygame-ce`, not vanilla `pygame`). `requirements-dev.txt` adds `pytest` + `pytest-cov`. `pyproject.toml` holds the pytest/coverage config and `version`. CI (`.github/workflows/ci.yml`) runs the suite on Python 3.11–3.13 and refreshes the coverage badge; `main` is branch-protected (PR + green CI required). No linter is configured. See `CONTRIBUTING.md` for the workflow and release process.

## Runtime data & config (gitignored)

`.gitignore` excludes `*.ini` and `*.json`, so these files exist only locally and are recreated on demand:
- `config.ini` — persisted music/effects volume (`[VOLUMEN]` section), read/written by `src/core/config.py`.
- `data/saves/puntuaciones.json` — high-score table (`{nombre: puntos}`), managed by `SistemaClasificacion` (`src/ui/scoreboard.py`). Paths here are **relative to the current working directory**, so the game must be launched from the project root.

Assets live under `data/assets/` (`imagenes/`, `musica/`, `sonidos/`). Logical asset names map to relative paths in `src/core/config.py`: `RECURSOS` + `EXPLOSIONES` (images), `SONIDOS` (short SFX, loaded into RAM as `mixer.Sound`), and `MUSICA` (background tracks — the raw OGG **bytes** are read into RAM at startup and played with `mixer.music.load(BytesIO(...))`; still decoded on the fly, not decompressed). Add new assets to the right dict, not by hardcoding paths.

Tunable gameplay/loop constants (window size, FPS, wave-phase thresholds, spawn cadence, invuln/contact windows) live in `src/core/settings.py`. Entity-local constants stay on their class (`Jugador.CONFIG`, `EnemigoBase.TAMANO_ESTANDAR`, `Bala.TAMANO`, …).

## Architecture

### Entry point & state flow

`main.py` initializes pygame, builds the singleton `ResourceManager`, loads every asset up front (`cargar_activos_del_juego`), builds one shared `AudioManager`, then runs a **top-level state machine**: `estado` cycles between `"MENU"` and `"JUGAR"` until `"SALIR"`. `MenuManager.ejecutar()` and `Juego.ejecutar()` each run their own loop and **return the next state string** — they never instantiate each other or call `sys.exit()`. `MenuManager` (`src/ui/menu.py`) is itself a sub-state machine (`PRINCIPAL` / `OPCIONES` / `PUNTUACIONES`); its persistent instance is reused each time control returns to the menu (`ejecutar()` resets its own state on entry).

Exit routing: the window's X button → `"SALIR"` (app quits after `pygame.quit()` in `main.py`); "Salir" from pause (after the confirm dialog) and "Salir" on Game Over → `"MENU"`. `Juego` exposes `volver_al_menu()` / `salir_del_juego()` which just set `self.resultado` + `self.ejecutando = False`.

`engine.py` still imports `MenuManager` function-locally in `mostrar_opciones_juego` (pause → options opens a throwaway `MenuManager` sharing the same `AudioManager`); `menu.py` no longer imports `engine`.

### The `Juego` "god object" + manager pattern

`Juego` holds all match state (score, level, `pausado`, `estado_game_over`, `pidiendo_nombre`, sprite groups, difficulty timers) and delegates behavior to managers, each of which takes `juego` (or the resource/audio managers) in its constructor and reaches back into it for shared state:

- **`InputHandler`** (`src/core/input.py`) — translates pygame events into `Juego` method calls; owns the pause/game-over/name-entry input modes and the blocking quit-confirmation dialog (which now `tick(30)`s to avoid a CPU-spin). `manejar_eventos()` returns `False` to end the game loop; `QUIT` sets `salir_del_juego()` rather than killing the process. Continuous fire is a flag (`juego.disparando`) polled each frame.
- **`EntityManager`** (`src/managers/entities.py`) — owns five `pygame.sprite.Group`s: `balas`, `balas_enemigo`, `enemigos`, `items`, `efectos` (explosions + destellos). `actualizar(dt)` updates every group, drives enemy/boss auto-fire, and `kill()`s off-screen entities. There is **no `juego.all_sprites`** anymore; the player is a lone `Sprite` held on `juego.jugador`.
- **`CollisionManager`** (`src/managers/collision.py`) — resolution via `pygame.sprite.groupcollide` / `spritecollide`. Bullets↔ships use `collide_circle` (needs `sprite.radius` — the attribute is `radius`, not `radio`); body contact and item pickup use rect collision (`CONTACTO_COOLDOWN_MS` per-enemy cooldown via `juego.enemigos_golpeados`, a `WeakKeyDictionary` also purged explicitly on death/despawn). `_eliminar_enemigo` guards against double-processing when several bullets kill one enemy in a frame. On boss death it sets `juego.pendiente_reinicio = True`; the actual `reiniciar_juego()` runs at the end of `Juego.actualizar()` (never mid-collision).
- **`WaveManager`** (`src/managers/waves.py`) — time-based spawn director. Phases switch at fixed elapsed-ms thresholds (`TIEMPO_FASE_2/3/JEFE`); at the boss phase it swaps music and waits before spawning `Jefe`. Requests pre-scaled images from `ResourceManager`.
- **`RenderManager`** (`src/managers/render.py`) — orchestrates all per-frame drawing. Real pause takes a fast path: on the first paused frame it snapshots `pantalla`, multiplies it to grey once (`_frame_pausa`), and just re-blits that + text + buttons until unpaused (any active-game render resets `_frame_pausa`). Game Over / name-entry set `juego.pausado = True` too but are excluded from that path and get their own overlay. Overlay buttons (`boton_reintentar`, `boton_salir_post`, `boton_opciones`, `boton_salir`) are created **once**, lazily, and cached on `juego`; `InputHandler` reads those attributes. Fonts are built in `__init__`. `Boton` caches its own rendered `Surface`.
- **`EffectManager`** (`src/managers/effects.py`) — explosions and screen flashes (`src/visual/`).
- **`UIManager`** (`src/ui/hud.py`) — HUD and overlay text/box drawing.
- **`AudioManager`** (`src/core/audio.py`) — music/effect playback and volume. **One instance**, built in `main.py` and injected into both `MenuManager` and `Juego`. Music: one track at a time via `pygame.mixer.music`, loaded from the in-RAM OGG bytes (`get_music_data` → `BytesIO`) so a track switch never stalls the main loop. `reproducir_musica(nombre)` is idempotent (no-ops if `nombre == pista_actual`) and fades the new track **in**; `detener_musica`/`detener_toda_la_musica` do a hard `music.stop()` — **not `fadeout()`**, because a pending fadeout makes the next `music.load()` block until it finishes (~200-300 ms hitch). Effect names in code (`"disparo"`, `"golpe"`, `"item"`) are aliases over the `SONIDOS` keys (`laser_gun`, `hit`, `item_take`). `main.py` calls `pygame.mixer.pre_init(44100,-16,2,512)` before `pygame.init()` and bumps to 16 channels.

### Game loop (`Juego.ejecutar`)

Each frame: `input_handler.manejar_eventos()` → if `pausado`, draw only → else compute `dt = min(reloj.tick(FPS)/1000, 3/FPS)` and `actualizar(dt)` (player move, spawn check, `entity_manager.actualizar(dt)`, `collision_manager.actualizar()`, background) → `dibujar()`.

**Delta time**: all movement is FPS-independent. Speeds are still expressed in px/frame-at-60fps; `MovimientoSubpixel._desplazar(vx, vy, dt)` (`src/entities/base/movimiento.py`) multiplies by `dt*FPS` and carries the sub-pixel remainder so fractional speeds aren't lost to the integer `rect`. The `rect` stays the source of truth, so code that repositions it directly (respawn, boss bounce) doesn't desync. At exactly 60 FPS behaviour is identical to the old frame-based code.

**Game clock**: `Juego.tiempo_juego` (ms) is a monotonic clock that **only advances inside `actualizar(dt)`** (`self.tiempo_juego += dt*1000`). Since `actualizar` isn't called while `pausado` / game over, it freezes on its own — no manual pause bookkeeping. All game-logic time reads `juego.tiempo_juego`, never `pygame.time.get_ticks()`: cadences (`jugador.ultimo_disparo`, `enemigo.tiempo_ultimo_ataque`, `jefe.ultimo_disparo_*`), invulnerability deadline, wave-phase clock (`ahora - inicio_juego`), boss-wait (`WaveManager._procesar_fase_jefe(tiempo_juego)`), and the `enemigos_golpeados` contact-cooldown timestamps. `pausar_juego`/`reanudar_juego` only flip `self.pausado`. `Jugador.update(dt, tiempo_juego)` and `WaveManager.spawn_enemigo(tiempo_nivel, tiempo_juego, ...)` take the clock. `reiniciar_juego` resets `tiempo_juego`/`inicio_juego` to 0 and the player's timers. Any new time-gated behavior must read `juego.tiempo_juego` or be dt-based.

**Restart (`reiniciar_juego`)**: two paths. Level advance (`jefe_derrotado`) keeps the same `Jugador` and its upgrades, bumps `nivel`, tightens spawn cadence, and `EntityManager.vaciar_todo(avance_nivel=True)` clears only enemies + items — **every projectile (player and enemy bullets) and effect already in flight survives** so nothing pops out on boss death. Full restart resets the `Jugador` **in place** via `Jugador.reiniciar(ancho, alto)` (same instance — managers may hold the reference; audit item 14) and `vaciar_todo()` clears everything. `enemigos_golpeados` is `.clear()`ed, never reassigned, for the same reason.

The `pygame_gui` options screen uses the 0.6+ event API (`event.type == pygame_gui.UI_BUTTON_PRESSED` / `UI_HORIZONTAL_SLIDER_MOVED`), not the old `USEREVENT` + `event.user_type`. `MenuManager` keeps a single `self.clock`; only the outer loop calls `tick(settings.FPS)`.

### Entities

`ResourceManager` (`src/core/resources.py`) is a `__new__`-based singleton. `load_image` runs `.convert()` / `.convert_alpha()` at load (so blits don't convert per-frame). `get_image_scaled` caches by `name_WxH`; `get_image_rotated(name, size, angle)` caches by `name_WxH_r<deg>` — projectiles now get a ready-made oriented `Surface` from here instead of loading/scaling/rotating per bullet. `get_image_path` still exists for other callers; `get_music_path` / `load_music` register music paths without decoding.

Enemies (`src/entities/enemies.py`): `EnemigoBase` → `EnemigoTipo1/2/3` and `Jefe`. Health scales **linearly**: `salud_base * (1 + FACTOR_NIVEL*(nivel-1))`, `FACTOR_NIVEL` a class attr (`settings.DIFICULTAD_FACTOR_ENEMIGO` / `_JEFE`). Loot probability rises by type (5% / 10% / 20% / 100% boss) and is forced after 10 kills; `generate_item` filters `CANDIDATOS_LOOT` by `_loot_util` (no list mutation). `Jefe` overrides `movimiento_enemigo` (no-op) and drives its own patrol in `update`. The `disparo_*` methods take `(ahora, rm, nombre_bala)`, read damage/speed from `settings`, and build the projectile through `rm.get_image_rotated`.

Projectiles: `src/entities/base/projectile_base.py` (`Proyectil`, which mixes in `MovimientoSubpixel`) is the shared base for `Bala` (`bullet.py`) and `BalaEnemigo` (`bullet_enemy.py`). **They receive a cached `Surface`, never a path** — no disk I/O per shot, no per-instance rotate. Size/orientation constants: `Bala.TAMANO`/`Bala.ANGULO`, `BalaEnemigo.TAMANO`. Collision is `collide_circle` on `radius`, set per class from `RADIUS` (`settings.RADIO_*`). Every `update(self, dt=0)` and `Jugador.mover(teclas, pantalla, dt)` takes `dt`. `Jugador.mover` normalizes the diagonal and applies optional smoothing (`settings.JUGADOR_SUAVIZADO`). Player upgrades (damage/cadence/speed, `tipo_disparo` up to `"triple"`) live on `Jugador` (`src/entities/player.py`); `Item` (`src/entities/items.py`) applies power-up effects on pickup.

**F1** toggles `juego.debug_hitboxes` → `RenderManager._dibujar_hitboxes` draws the real collision circles.

### Still open

The "god object": managers still take the whole `juego` (audit item 14). Balance values in `settings.py` are first-pass and want playtesting. See `AUDITORIA.md`.

### Directory layout

```
src/core/      engine, config, settings, resources, audio, input
src/managers/  entities, collision, waves, render, effects
src/entities/  player, enemies, bullet, bullet_enemy, items, base/ (projectile_base, movimiento)
src/ui/        menu, hud, scoreboard, components/button.py
src/visual/    background (parallax scroll), explosions, flash, flash_constant
tests/         suite pytest headless (conftest.py + test_*.py, uno por módulo)
.github/       workflows/ci.yml, dependabot.yml
```
