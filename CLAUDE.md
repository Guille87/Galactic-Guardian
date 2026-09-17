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

`.gitignore` excludes `/config.ini` and `/data/saves/`, so these files exist only locally and are recreated on demand:
- `config.ini` — persisted music/effects volume (`[VOLUMEN]` section), read/written by `src/core/config.py`.
- `data/saves/puntuaciones.json` — high-score table, managed by `SistemaClasificacion` (`src/ui/scoreboard.py`): `{nombre: {"puntos": N, "nivel": M}}` (`nivel` = how far the run got). Reads accept the old plain-`int`-per-name shape too (`nivel` comes back as `None`); a name only gets rewritten to the new shape when its score improves. `obtener_puntuaciones_top()` returns `(nombre, puntos, nivel)` triples.

Path resolution goes through **`src/core/paths.py`** (`src/core/version.py` holds `__version__`, kept in sync with `pyproject.toml`):
- `paths.recurso(...)` → read-only bundled assets. Dev: project root. Frozen (PyInstaller): `sys._MEIPASS`.
- `paths.dir_datos_usuario()` → writable dir for `config.ini` + saves. Dev: project root (paths are now absolute, so the CWD no longer matters). Frozen: the OS user-data dir (`%APPDATA%\GalacticGuardian`, `~/Library/Application Support/…`, `~/.local/share/…`) so user data survives an app-folder replace and works from a protected install path.

Assets live under `data/assets/` (`imagenes/`, `musica/`, `sonidos/`). Logical asset names map to relative paths in `src/core/config.py`: `RECURSOS` + `EXPLOSIONES` (images), `SONIDOS` (short SFX, loaded into RAM as `mixer.Sound`), and `MUSICA` (background tracks — the raw OGG **bytes** are read into RAM at startup and played with `mixer.music.load(BytesIO(...))`; still decoded on the fly, not decompressed). Add new assets to the right dict, not by hardcoding paths.

Tunable gameplay/loop constants (window size, FPS, wave-phase thresholds, spawn cadence, invuln/contact windows) live in `src/core/settings.py`. Entity-local constants stay on their class (`Jugador.CONFIG`, `EnemigoBase.TAMANO_ESTANDAR`, `Bala.TAMANO`, …).

## Architecture

### Entry point & state flow

`main.py` initializes pygame, builds the singleton `ResourceManager`, loads every asset up front (`cargar_activos_del_juego`), builds one shared `AudioManager`, then runs a **top-level state machine**: `estado` cycles between `"MENU"` and `"JUGAR"` until `"SALIR"`. `MenuManager.ejecutar()` and `Juego.ejecutar()` each run their own loop and **return the next state string** — they never instantiate each other or call `sys.exit()`. `MenuManager` (`src/ui/menu.py`) is itself a sub-state machine (`PRINCIPAL` / `OPCIONES` / `PUNTUACIONES`); its persistent instance is reused each time control returns to the menu (`ejecutar()` resets its own state on entry).

Exit routing: the window's X button → `"SALIR"` (app quits after `pygame.quit()` in `main.py`); "Salir" from pause (after the confirm dialog) and "Salir" on Game Over → `"MENU"`. `Juego` exposes `volver_al_menu()` / `salir_del_juego()` which just set `self.resultado` + `self.ejecutando = False`.

`engine.py` still imports `MenuManager` function-locally in `mostrar_opciones_juego` (pause → options opens a throwaway `MenuManager` sharing the same `AudioManager`); `menu.py` no longer imports `engine`.

### The `Juego` "god object" + manager pattern

`Juego` holds all match state (score, level, `pausado`, `estado_game_over`, `pidiendo_nombre`, sprite groups, difficulty timers) and delegates behavior to managers. Audit item 14 (shrinking the god object) is in progress: the **mechanical** managers now take explicit collaborators, the **view/controller** ones still take `juego` by design.

- Explicit deps, no `juego` reference: `WaveManager(rm, am, ancho, alto)`, `EntityManager(rm, ancho, alto, enemigos_golpeados)`, `EffectManager(rm, entity_manager, jugador)`, `CollisionManager(entity_manager, jugador, effect_manager, audio, enemigos_golpeados, reglas)`. This works because the identities they capture (`jugador`, `enemigos_golpeados`) are stable across `reiniciar_juego` (reset in place / `.clear()`ed, never rebound).
- `CollisionManager`'s `reglas` **is** the `Juego` — but a named narrow role, not attribute access: the manager only calls `reglas.al_eliminar_enemigo(enemigo)` (score, loot, boss transition) and `reglas.manejar_impacto_jugador()` (flash / death / respawn). Everything mechanical (collide, `take_damage`, `kill`, explosion, cooldown bookkeeping, SFX, `item.aplicar_efecto`) stays in the manager.
- Still take `juego` by design: `InputHandler`, `RenderManager`, `UIManager` — the view + controller layer. They legitimately observe the whole match; they only *write* UI flags (`pausado`, `debug_hitboxes`, `nombre_entrada`, cached overlay buttons).

- **`InputHandler`** (`src/core/input.py`) — translates pygame events into `Juego` method calls; owns the pause/game-over/name-entry input modes and the blocking quit-confirmation dialog (which now `tick(30)`s to avoid a CPU-spin). `manejar_eventos()` returns `False` to end the game loop; `QUIT` sets `salir_del_juego()` rather than killing the process. Continuous fire is a flag (`juego.disparando`) polled each frame.
- **`EntityManager`** (`src/managers/entities.py`) — owns five `pygame.sprite.Group`s: `balas`, `balas_enemigo`, `enemigos`, `items`, `efectos` (explosions + destellos). `actualizar(dt, tiempo_juego)` updates every group, drives enemy/boss auto-fire (needs the clock for their cadences), and `kill()`s off-screen entities. There is **no `juego.all_sprites`** anymore; the player is a lone `Sprite` held on `juego.jugador`.
- **`CollisionManager`** (`src/managers/collision.py`) — `actualizar(tiempo_juego)`. Detection via `pygame.sprite.groupcollide` / `spritecollide`. Bullets↔ships use `collide_circle` (needs `sprite.radius` — the attribute is `radius`, not `radio`); body contact and item pickup use rect collision (`CONTACTO_COOLDOWN_MS` per-enemy cooldown in `enemigos_golpeados`, a `WeakKeyDictionary` also purged explicitly on death/despawn). `_eliminar_enemigo` guards against double-processing when several bullets kill one enemy in a frame, then hands off to `reglas.al_eliminar_enemigo`. Boss death → `Juego.al_eliminar_enemigo` sets `pendiente_reinicio = True`; the actual `reiniciar_juego()` runs at the end of `Juego.actualizar()` (never mid-collision).
- **`WaveManager`** (`src/managers/waves.py`) — time-based spawn director. Phases switch at fixed elapsed-ms thresholds (`TIEMPO_FASE_2/3/JEFE`); at the boss phase it swaps music and waits before spawning `Jefe`. Requests pre-scaled images from `ResourceManager`.
- **`RenderManager`** (`src/managers/render.py`) — orchestrates all per-frame drawing. Real pause takes a fast path: on the first paused frame it snapshots `pantalla`, multiplies it to grey once (`_frame_pausa`), and just re-blits that + text + buttons until unpaused (any active-game render resets `_frame_pausa`). Game Over / name-entry set `juego.pausado = True` too but are excluded from that path and get their own overlay. Overlay buttons (`boton_reintentar`, `boton_salir_post`, `boton_opciones`, `boton_salir`) are created **once**, lazily, and cached on `juego`; `InputHandler` reads those attributes. Fonts are built in `__init__`. `Boton` caches its own rendered `Surface`.
- **`EffectManager`** (`src/managers/effects.py`) — explosions and screen flashes (`src/visual/`); adds them to `entity_manager.efectos`.
- **`UIManager`** (`src/ui/hud.py`) — HUD and overlay text/box drawing.
- **`AudioManager`** (`src/core/audio.py`) — music/effect playback and volume. **One instance**, built in `main.py` and injected into both `MenuManager` and `Juego`. Music: one track at a time via `pygame.mixer.music`, loaded from the in-RAM OGG bytes (`get_music_data` → `BytesIO`) so a track switch never stalls the main loop. `reproducir_musica(nombre)` is idempotent (no-ops if `nombre == pista_actual`) and fades the new track **in**; `detener_musica`/`detener_toda_la_musica` do a hard `music.stop()` — **not `fadeout()`**, because a pending fadeout makes the next `music.load()` block until it finishes (~200-300 ms hitch). Effect names in code (`"disparo"`, `"golpe"`, `"item"`) are aliases over the `SONIDOS` keys (`laser_gun`, `hit`, `item_take`). `main.py` calls `pygame.mixer.pre_init(44100,-16,2,512)` before `pygame.init()` and bumps to 16 channels.

### Game loop (`Juego.ejecutar`)

Each frame: `input_handler.manejar_eventos()` → if `pausado`, draw only → else compute `dt = min(reloj.tick(FPS)/1000, 3/FPS)` and `actualizar(dt)` (player move, spawn check, `entity_manager.actualizar(dt)`, `collision_manager.actualizar()`, background) → `dibujar()`.

**Delta time**: all movement is FPS-independent. Speeds are still expressed in px/frame-at-60fps; `MovimientoSubpixel._desplazar(vx, vy, dt)` (`src/entities/base/movimiento.py`) multiplies by `dt*FPS` and carries the sub-pixel remainder so fractional speeds aren't lost to the integer `rect`. The `rect` stays the source of truth, so code that repositions it directly (respawn, boss bounce) doesn't desync. At exactly 60 FPS behaviour is identical to the old frame-based code.

**Game clock**: `Juego.tiempo_juego` (ms) is a monotonic clock that **only advances inside `actualizar(dt)`** (`self.tiempo_juego += dt*1000`). Since `actualizar` isn't called while `pausado` / game over, it freezes on its own — no manual pause bookkeeping. All game-logic time reads `juego.tiempo_juego`, never `pygame.time.get_ticks()`: cadences (`jugador.ultimo_disparo`, `enemigo.tiempo_ultimo_ataque`, `jefe.ultimo_disparo_*`), invulnerability deadline, wave-phase clock (`ahora - inicio_juego`), boss-wait (`WaveManager._procesar_fase_jefe(tiempo_juego)`), and the `enemigos_golpeados` contact-cooldown timestamps. `pausar_juego`/`reanudar_juego` only flip `self.pausado`. `Jugador.update(dt, tiempo_juego)` and `WaveManager.spawn_enemigo(tiempo_nivel, tiempo_juego, ...)` take the clock. `reiniciar_juego` resets `tiempo_juego`/`inicio_juego` to 0 and the player's timers. Any new time-gated behavior must read `juego.tiempo_juego` or be dt-based.

**Restart (`reiniciar_juego(nivel_forzado=None)`)**: three paths, chosen by `nivel_forzado` then `jefe_derrotado`. Level advance (`jefe_derrotado`, no `nivel_forzado`) keeps the same `Jugador` and its upgrades, bumps `nivel`, re-centers it with `Jugador.recentrar(ancho, alto)` (position + sub-pixel accumulators only, no stats — the level-end transition, below, leaves the ship off-screen), and `EntityManager.vaciar_todo(avance_nivel=True)` clears only enemies + items — **every projectile (player and enemy bullets) and effect already in flight survives** so nothing pops out on boss death (the transition itself already cleared bullets earlier; see below). Full restart (`nivel_forzado=None`, no `jefe_derrotado`) and level-select (`nivel_forzado=N`, from the campaign's level-select screen) both reset the `Jugador` **in place** via `Jugador.reiniciar(ancho, alto)` (same instance — managers may hold the reference; audit item 14), zero `puntuacion`, and `vaciar_todo()` clears everything; level-select additionally sets `self.nivel = nivel_forzado` directly. `enemigos_golpeados` is `.clear()`ed, never reassigned, for the same reason. Spawn cadence for `self.nivel` comes from `settings.gen_intervalo_para_nivel(nivel)` — a pure function of the level number (not iteratively-decremented state), precisely so level-select can jump straight to the right difficulty. `reiniciar_juego` also resets `self.background.velocidad` to `settings.FONDO_VELOCIDAD_NORMAL` and clears any leftover transition state, in case it's ever called while one was active.

**Campaign (fixed `settings.NIVEL_MAX` levels)**: killing the boss (`Juego.al_eliminar_enemigo`) sets `jefe_derrotado` + the deferred `pendiente_reinicio`, processed at the end of `actualizar()` by `_iniciar_transicion_fin_de_nivel()` — `reiniciar_juego()` isn't called until the player clicks through the resulting screen. That method swaps to `victory_tune`, empties `entity_manager.balas`/`balas_enemigo` (bullets don't linger through the transition or the overlay) and `disparando = False`, then sets `transicion_activa = True` / `transicion_fase = "centrar"`. While `transicion_activa`, `actualizar()` takes a **separate branch**: `_actualizar_transicion_nivel(dt)` scripts the ship instead of reading input (`InputHandler` also blocks Esc/Space/F1/clicks while `transicion_activa`, and the final `disparar()` guard checks it too) — `"centrar"` slides `jugador.rect.centerx` to mid-screen at `settings.TRANSICION_VEL_LATERAL` px/frame-60fps (Y untouched), `"subir"` then moves it straight up at `TRANSICION_VEL_SUBIDA` until `rect.bottom < 0`, ramping `background.velocidad` from `FONDO_VELOCIDAD_NORMAL` up to `× TRANSICION_FONDO_ACELERACION` over `TRANSICION_FONDO_RAMPA_MS` ms, and `"espera"` just waits `TRANSICION_ESPERA_MS` ms. `pausado` stays **False** the whole time (so `actualizar()` keeps being called at all — `Juego.ejecutar()` skips it entirely when `pausado`); `entity_manager.actualizar` keeps running too (so the boss's explosion/any loot finish naturally) but `collision_manager` and enemy spawning are skipped (nothing left to collide with). `_finalizar_transicion_fin_de_nivel()` ends the sequence, resets `background.velocidad`, sets `pausado = True`, and:
- below `NIVEL_MAX` → `estado_nivel_completado = True` (its own overlay: stats for the level just cleared — `puntuacion`, `enemigos_eliminados_nivel`, `tiempo_juego` — with **Continuar** → `reiniciar_juego()` and **Elegir nivel** → `mostrando_seleccion_nivel = True`, a list of buttons for levels `1..nivel` already cleared this run, session-only, no cross-run persistence). Picking one calls `reiniciar_juego(nivel_forzado=n)`.
- at `NIVEL_MAX` → `_pedir_nombre_o_mostrar("victoria")`, shared with `juego_terminado()`'s Game Over path (`"game_over"`): both funnel through the same top-10 check (`_cualifica_para_el_top10`) and `pidiendo_nombre_para` remembers which overlay (`estado_game_over` vs `estado_victoria_final`) to show once the name is entered (`InputHandler`'s `K_RETURN` handler branches on it, and now also passes `nivel=self.juego.nivel` to `agregar_puntuacion`). The final screen (`estado_victoria_final`) offers **Jugar de nuevo** (`reiniciar_juego(nivel_forzado=1)`) and **Menú**.

All the transition's speeds/timings are tunable constants in `settings.py`: `TRANSICION_VEL_LATERAL`, `TRANSICION_VEL_SUBIDA`, `TRANSICION_FONDO_ACELERACION`, `TRANSICION_FONDO_RAMPA_MS`, `TRANSICION_ESPERA_MS`, plus `FONDO_VELOCIDAD_NORMAL` for the baseline scroll speed.

The three post-transition states (`estado_nivel_completado`, `mostrando_seleccion_nivel`, `estado_victoria_final`) behave like `estado_game_over`: `InputHandler` checks them **before** the generic pause-click branch (same buttons-only, keyboard-inert treatment — see `_manejar_teclas_presionadas`'s guard), and `RenderManager` treats them as `overlay_propio` (no world entities drawn, own background+buttons, excluded from the pause fast-path). Their buttons are created lazily and cached on `juego` (`boton_continuar`, `boton_elegir_nivel`, `botones_seleccion_nivel` — a list rebuilt when `nivel` grows, `boton_reintentar_final`, `boton_menu_final`), same pattern as the Game Over buttons. `transicion_activa` is **not** one of these overlay states (`pausado` stays `False` while it runs, on purpose — see above) — it gets its own, separate guards in `InputHandler` and its own early-return branch in `Juego.actualizar()`; `RenderManager` needs no special case for it since the normal draw path (entities + player + HUD) is exactly what should be visible while the ship flies off.

`MenuManager` runs a background update check on entry: `src/core/updates.py` (`ComprobadorActualizaciones`) hits the GitHub "latest release" API in a daemon thread, compares `tag_name` to `__version__`, caches the answer (incl. the `*-setup.exe` asset URL) in `%APPDATA%` for 6 hours (`updates._CACHE_TTL`), and is fully best-effort (any failure → silent, no banner). If a newer version exists, `_menu_principal` shows a banner + `btn_actualizar`:
- **frozen** + installer asset present → `DescargaActualizacion` downloads the setup in a thread (banner shows `%`), then `lanzar_instalador` runs it `/SILENT` and the menu returns `"SALIR"`. `installer.iss` (Inno Setup, per-user, `AppId` fixed for in-place upgrade, `CloseApplications=yes`) closes the game, replaces files, and its `[Run]` entry relaunches it. User data in `%APPDATA%` is untouched. While a download is in progress (`_descargando_actualizacion()`), `_menu_principal` ignores clicks on every other button (Jugar/Opciones/Puntuaciones included) so leaving the menu can't abandon it mid-way.
- otherwise (running from source, or download failed) → opens the releases page in a browser.
Env var `GG_SIN_COMPROBAR_ACTUALIZACIONES` disables the check (set in `tests/conftest.py`). `build.yml` publishes the `.zip` and the `-setup.exe` on every Release.

The `pygame_gui` options screen uses the 0.6+ event API (`event.type == pygame_gui.UI_BUTTON_PRESSED` / `UI_HORIZONTAL_SLIDER_MOVED`), not the old `USEREVENT` + `event.user_type`. `MenuManager` keeps a single `self.clock` (only the outer loop `tick`s) and a single `self.ui_manager`, built lazily once by `_inicializar_interfaz_opciones` and re-synced on each entry by `_abrir_opciones`. Volume handling for **both** sliders: dragging the bar is free (`UI_HORIZONTAL_SLIDER_MOVED` → `_clamp_volumen`, just `[0,1]` + round to 2 dp); an ◄ ► arrow click sets `_flecha_pendiente = (destino, sube)` on `UI_BUTTON_PRESSED`, and **after** the event loop (same frame, before drawing) the value is snapped to the multiple of `VOLUMEN_PASO` just above/below the previous value (`_paso_volumen`, so `0.25` → `0.3`/`0.2`) — pygame_gui has already applied its own `±increment` during `process_events`, and correcting it in-frame avoids a one-frame visual jump. The `MOVED` pygame_gui then posts is ignored next frame via `_ignorar_moved`. Every applied value is pushed back with `set_current_value` — a value outside `[0,1]`, even by `1e-17`, makes `pygame_gui` silently freeze the slider. `button_held_repeat_acc` is zeroed on any held arrow so pygame_gui's hold-to-fast-scroll never kicks in (it made the volume visibly overshoot before settling).

### Entities

`ResourceManager` (`src/core/resources.py`) is a `__new__`-based singleton. `load_image` runs `.convert()` / `.convert_alpha()` at load (so blits don't convert per-frame). `get_image_scaled` caches by `name_WxH`; `get_image_rotated(name, size, angle)` caches by `name_WxH_r<deg>` — projectiles now get a ready-made oriented `Surface` from here instead of loading/scaling/rotating per bullet. `get_image_path` still exists for other callers; `get_music_path` / `load_music` register music paths without decoding.

Enemies (`src/entities/enemies.py`): `EnemigoBase` → `EnemigoTipo1/2/3` and `Jefe`. Health scales **linearly**: `salud_base * (1 + FACTOR_NIVEL*(nivel-1))`, `FACTOR_NIVEL` a class attr (`settings.DIFICULTAD_FACTOR_ENEMIGO` / `_JEFE`). Loot probability rises by regular-enemy type (5% / 10% / 20%) and is forced after 10 kills; `generate_item` filters `CANDIDATOS_LOOT` by `_loot_util` (no list mutation). `Jefe` overrides `die()` to always return `None` — **the boss never drops loot**, not even via the 10-kill mercy counter (`generate_item`'s `Jefe` branch is unreachable and documented as such). `Jefe` also overrides `movimiento_enemigo` (no-op) and drives its own patrol in `update`. The `disparo_*` methods take `(ahora, rm, nombre_bala)`, read damage/speed from `settings`, and build the projectile through `rm.get_image_rotated`.

Projectiles: `src/entities/base/projectile_base.py` (`Proyectil`, which mixes in `MovimientoSubpixel`) is the shared base for `Bala` (`bullet.py`) and `BalaEnemigo` (`bullet_enemy.py`). **They receive a cached `Surface`, never a path** — no disk I/O per shot, no per-instance rotate. Size/orientation constants: `Bala.TAMANO`/`Bala.ANGULO`, `BalaEnemigo.TAMANO`. Collision is `collide_circle` on `radius`, set per class from `RADIUS` (`settings.RADIO_*`). Every `update(self, dt=0)` and `Jugador.mover(teclas, pantalla, dt)` takes `dt`. `Jugador.mover` normalizes the diagonal and applies optional smoothing (`settings.JUGADOR_SUAVIZADO`). Player upgrades (damage/cadence/speed, `tipo_disparo` up to `"triple"`) live on `Jugador` (`src/entities/player.py`); `Item` (`src/entities/items.py`) applies power-up effects on pickup.

**F1** toggles `juego.debug_hitboxes` → `RenderManager._dibujar_hitboxes` draws the real collision circles.

### Still open

The "god object": audit item 14 is largely done — every mechanical manager (Wave, Entity, Effect, Collision) takes explicit deps and no longer reaches into `juego`; `CollisionManager` talks back through the `reglas` contract. `InputHandler` / `RenderManager` / `UIManager` still take `juego` **on purpose** (view + controller layer). What's left is optional polish, not a structural problem. Balance values in `settings.py` are first-pass and want playtesting. See `AUDITORIA.md`.

### Directory layout

```
src/core/      engine, config, settings, resources, audio, input, paths, version, updates
src/managers/  entities, collision, waves, render, effects
src/entities/  player, enemies, bullet, bullet_enemy, items, base/ (projectile_base, movimiento)
src/ui/        menu, hud, scoreboard, components/button.py
src/visual/    background (parallax scroll), explosions, flash, flash_constant
tests/         suite pytest headless (conftest.py + test_*.py, uno por módulo)
.github/       workflows/ (ci.yml, build.yml), dependabot.yml
```
