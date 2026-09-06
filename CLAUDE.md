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

# Run the game
python main.py
```

There is no test suite, linter config, or build step. `requirements.txt` pins `pygame-ce==2.5.7` and `pygame-gui==0.6.14` (note: `pygame-ce`, not vanilla `pygame`).

## Runtime data & config (gitignored)

`.gitignore` excludes `*.ini` and `*.json`, so these files exist only locally and are recreated on demand:
- `config.ini` — persisted music/effects volume (`[VOLUMEN]` section), read/written by `src/core/config.py`.
- `data/saves/puntuaciones.json` — high-score table (`{nombre: puntos}`), managed by `SistemaClasificacion` (`src/ui/scoreboard.py`). Paths here are **relative to the current working directory**, so the game must be launched from the project root.

Assets live under `data/assets/` (`imagenes/`, `musica/`, `sonidos/`). Logical asset names map to relative paths in `src/core/config.py`: `RECURSOS` + `EXPLOSIONES` (images), `SONIDOS` (short SFX, loaded into RAM as `mixer.Sound`), and `MUSICA` (background tracks — only the path is registered; played via `mixer.music` streaming). Add new assets to the right dict, not by hardcoding paths.

## Architecture

### Entry point & state flow

`main.py` initializes pygame, builds the singleton `ResourceManager`, loads every asset up front (`cargar_activos_del_juego`), builds one shared `AudioManager`, then runs a **top-level state machine**: `estado` cycles between `"MENU"` and `"JUGAR"` until `"SALIR"`. `MenuManager.ejecutar()` and `Juego.ejecutar()` each run their own loop and **return the next state string** — they never instantiate each other or call `sys.exit()`. `MenuManager` (`src/ui/menu.py`) is itself a sub-state machine (`PRINCIPAL` / `OPCIONES` / `PUNTUACIONES`); its persistent instance is reused each time control returns to the menu (`ejecutar()` resets its own state on entry).

Exit routing: the window's X button → `"SALIR"` (app quits after `pygame.quit()` in `main.py`); "Salir" from pause (after the confirm dialog) and "Salir" on Game Over → `"MENU"`. `Juego` exposes `volver_al_menu()` / `salir_del_juego()` which just set `self.resultado` + `self.ejecutando = False`.

`engine.py` still imports `MenuManager` function-locally in `mostrar_opciones_juego` (pause → options opens a throwaway `MenuManager` sharing the same `AudioManager`); `menu.py` no longer imports `engine`.

### The `Juego` "god object" + manager pattern

`Juego` holds all match state (score, level, `pausado`, `estado_game_over`, `pidiendo_nombre`, sprite groups, difficulty timers) and delegates behavior to managers, each of which takes `juego` (or the resource/audio managers) in its constructor and reaches back into it for shared state:

- **`InputHandler`** (`src/core/input.py`) — translates pygame events into `Juego` method calls; owns the pause/game-over/name-entry input modes and the blocking quit-confirmation dialog (which now `tick(30)`s to avoid a CPU-spin). `manejar_eventos()` returns `False` to end the game loop; `QUIT` sets `salir_del_juego()` rather than killing the process. Continuous fire is a flag (`juego.disparando`) polled each frame.
- **`EntityManager`** (`src/managers/entities.py`) — owns plain Python lists `balas`, `balas_enemigo`, `enemigos`; updates their movement, drives enemy/boss auto-fire, and culls off-screen entities. Items and explosions instead live in `juego.all_sprites` (a `pygame.sprite.Group`).
- **`CollisionManager`** (`src/managers/collision.py`) — all collision resolution: player bullets↔enemies, enemy bullets↔player, body contact (2s per-enemy cooldown via `juego.enemigos_golpeados`), player↔items. Also handles score and loot drops. On boss death it sets `juego.pendiente_reinicio = True`; the actual `reiniciar_juego()` runs at the end of `Juego.actualizar()` (never mid-collision).
- **`WaveManager`** (`src/managers/waves.py`) — time-based spawn director. Phases switch at fixed elapsed-ms thresholds (`TIEMPO_FASE_2/3/JEFE`); at the boss phase it swaps music and waits before spawning `Jefe`. Requests pre-scaled images from `ResourceManager`.
- **`RenderManager`** (`src/managers/render.py`) — orchestrates all per-frame drawing. Real pause takes a fast path: on the first paused frame it snapshots `pantalla`, multiplies it to grey once (`_frame_pausa`), and just re-blits that + text + buttons until unpaused (any active-game render resets `_frame_pausa`). Game Over / name-entry set `juego.pausado = True` too but are excluded from that path and get their own overlay. Overlay buttons (`boton_reintentar`, `boton_salir_post`, `boton_opciones`, `boton_salir`) are created **once**, lazily, and cached on `juego`; `InputHandler` reads those attributes. Fonts are built in `__init__`. `Boton` caches its own rendered `Surface`.
- **`EffectManager`** (`src/managers/effects.py`) — explosions and screen flashes (`src/visual/`).
- **`UIManager`** (`src/ui/hud.py`) — HUD and overlay text/box drawing.
- **`AudioManager`** (`src/core/audio.py`) — music/effect playback and volume. **One instance**, built in `main.py` and injected into both `MenuManager` and `Juego`. Music is streamed through `pygame.mixer.music` (one track at a time); `reproducir_musica(nombre)` is idempotent (no-ops if `nombre == pista_actual`), `detener_musica`/`detener_toda_la_musica` fade out. Effect names in code (`"disparo"`, `"golpe"`, `"item"`) are aliases over the `SONIDOS` keys (`laser_gun`, `hit`, `item_take`). `main.py` calls `pygame.mixer.pre_init(44100,-16,2,512)` before `pygame.init()` and bumps to 16 channels.

### Game loop (`Juego.ejecutar`)

Each frame at 60 FPS: `input_handler.manejar_eventos()` → if `pausado`, draw only → else `actualizar()` (player move, spawn check, `entity_manager.actualizar()`, `collision_manager.actualizar()`, background) → `all_sprites.update()` → `dibujar()`.

Pause correctness depends on time bookkeeping: `pausar_juego`/`reanudar_juego` record pause duration and shift every future timestamp (spawn timers, invulnerability, and each enemy's `actualizar_pausa`). Any new time-gated behavior must add the same offset in `reanudar_juego`. (Known gap, Phase 3: `WaveManager` boss-wait timer, `Explosion`, `Item` and `Destello` timers are not yet offset.)

The `pygame_gui` options screen uses the 0.6+ event API (`event.type == pygame_gui.UI_BUTTON_PRESSED` / `UI_HORIZONTAL_SLIDER_MOVED`), not the old `USEREVENT` + `event.user_type`. `MenuManager` keeps a single `self.clock`; only the outer loop calls `tick(60)`.

### Entities

`ResourceManager` (`src/core/resources.py`) is a `__new__`-based singleton. `load_image` runs `.convert()` / `.convert_alpha()` at load (so blits don't convert per-frame). `get_image_scaled` caches by `name_WxH`; `get_image_rotated(name, size, angle)` caches by `name_WxH_r<deg>` — projectiles now get a ready-made oriented `Surface` from here instead of loading/scaling/rotating per bullet. `get_image_path` still exists for other callers; `get_music_path` / `load_music` register music paths without decoding.

Enemies (`src/entities/enemies.py`): `EnemigoBase` → `EnemigoTipo1/2/3` and `Jefe`. Health scales as `salud_base * 2**(nivel-1)` (audit flags this as too steep — Phase 4). Loot probability rises by type (5% / 10% / 20% / 100% boss) and is forced after 10 kills; the drop pool is filtered by what the player still needs. `Jefe` overrides `movimiento_enemigo` (no-op) and drives its own patrol in `update`. The `disparo_*` methods take `(ahora, rm, nombre_bala)` and build the projectile through `rm.get_image_rotated`.

Projectiles: `src/entities/base/projectile_base.py` (`Proyectil`) is the shared base for `Bala` (`bullet.py`) and `BalaEnemigo` (`bullet_enemy.py`). **They receive a cached `Surface`, never a path** — no disk I/O per shot, no per-instance rotate. Size/orientation constants: `Bala.TAMANO`/`Bala.ANGULO`, `BalaEnemigo.TAMANO`. Collision is still centre-distance vs `radio` (16 for bullets; unchanged). Player upgrades (damage/cadence/speed, `tipo_disparo` up to `"triple"`) live on `Jugador` (`src/entities/player.py`); `Item` (`src/entities/items.py`) applies power-up effects on pickup.

### Directory layout

```
src/core/      engine, config, resources, audio, input
src/managers/  entities, collision, waves, render, effects
src/entities/  player, enemies, bullet, bullet_enemy, items, base/
src/ui/        menu, hud, scoreboard, components/button.py
src/visual/    background (parallax scroll), explosions, flash
```
