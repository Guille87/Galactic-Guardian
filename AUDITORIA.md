# Auditoría integral — Galactic Guardian

> Revisión de arquitectura, rendimiento (Pygame), jugabilidad y bugs.
> Base analizada: `main.py`, `src/core/*`, `src/managers/*`, `src/entities/*`, `src/ui/*`, `src/visual/*`.

---

## Estado de implementación

- **Fase 1 (estabilidad) — HECHA** (rama `fase-1-estabilidad`): C4, C5, C6, C7, C8, C3, B1, B2 + ruta del icono.
- **Fase 2 (rendimiento) — HECHA**: C1, C2, P1, P4, P5, P6 (+ `SONIDOS`/`MUSICA` separados, tamaños de bala saneados).
- **Fase 3 (arquitectura) — pendiente**: P2, P3, C9, C11, B3, `dt` (C10), módulo `settings`, adelgazar el objeto-Dios.
- **Fase 4 (jugabilidad) — pendiente**: J1, J2, J3, J4, J5, J6, J7.

---

## 1. Resumen general del estado del proyecto

El proyecto está **funcional y razonablemente organizado** para su tamaño (~2.000 líneas). La refactorización reciente introdujo un patrón de *managers* (`EntityManager`, `CollisionManager`, `WaveManager`, `RenderManager`, `EffectManager`, `UIManager`, `AudioManager`, `InputHandler`) que separa bien las responsabilidades **a nivel de intención**. La estructura de carpetas (`core`, `managers`, `entities`, `ui`, `visual`) es clara.

Sin embargo, la convivencia de código de hace 2 años con los retoques de hace 6 meses ha dejado **inconsistencias estructurales de fondo** que hoy son deuda técnica activa:

- **Objeto‑Dios `Juego`**: todos los managers reciben `self` (el juego completo) y escriben directamente en sus atributos. No hay encapsulación real; es acoplamiento total disfrazado de modularidad.
- **Doble sistema de sprites**: enemigos y balas viven en listas Python planas; ítems, explosiones y destellos en un `pygame.sprite.Group`; fondo y jugador se actualizan a mano. Tres modelos distintos en el mismo bucle.
- **Dos modelos de colisión** (círculo por distancia para balas, `colliderect` para cuerpo a cuerpo) y **hitboxes desalineadas** con los sprites.
- **Sin delta time**: toda la física depende de que el bucle mantenga 60 FPS exactos.
- **Rendimiento**: se carga imagen **desde disco por cada bala disparada**, la música se carga como `Sound` (todas las pistas OGG decodificadas en RAM), y los fondos a pantalla completa se blitean sin `convert()`.
- **API obsoleta de `pygame_gui`** en el menú de opciones (`event.user_type` / `USEREVENT`), casi con seguridad rota tras la actualización de dependencias.
- Varias **rutas de cierre distintas** (`sys.exit`, `pygame.quit(); exit()`, `return False`) y **bucles anidados con busy‑wait** (100 % CPU).
- Contador `enemigos_activos` **solo se decrementa, nunca se incrementa** → siempre negativo (código muerto/roto).

**Veredicto:** no hay nada que impida jugar el nivel 1, pero el rendimiento se degrada en la fase del jefe, el menú de opciones probablemente no responde, salir al menú principal desde pausa cierra el proceso, y la curva de dificultad (salud enemiga ×2 por nivel) es matemáticamente insostenible más allá del nivel 2‑3.

---

## 2. Problemas CRÍTICOS / alto impacto (con solución concreta)

### C1. Carga de `Surface` desde disco dentro del bucle principal — por cada proyectil

`src/entities/base/projectile_base.py:9`

```python
class Proyectil(pygame.sprite.Sprite):
    def __init__(self, ruta_imagen, x, y, danio, velocidad, tamano=(50, 50)):
        super().__init__()
        img = pygame.image.load(ruta_imagen).convert_alpha()   # ← disco + decode + scale + (rotate)
        self.image = pygame.transform.scale(img, tamano)
```

Cada disparo del jugador (hasta 3 balas con *triple*, cada ~150 ms) y cada bala enemiga/jefe (el jefe dispara cada 250 ms) construye un `Proyectil`, que:
1. Lee el PNG del disco.
2. Lo decodifica.
3. Lo escala a **50×50** (enorme para una bala).
4. Lo rota (`girar`).

En la fase del jefe esto son **decenas de `image.load` por segundo**. Es el cuello de botella nº 1.

Además `tamano=(50,50)` por defecto: las balas ocupan 50 px pero su `radio` de colisión es 16 → desajuste visual/hitbox gigante, y trabajo de escalado/rotado inútil.

**Solución:** cachear la `Surface` ya escalada/rotada en el `ResourceManager` y pasarla al proyectil como superficie, no como ruta.

```python
# ResourceManager: añadir cache de rotaciones
def get_image_rotated(self, name, size, angle):
    key = f"{name}_{size[0]}x{size[1]}_r{int(angle)}"
    if key not in self.scaled_resources:
        base = self.get_image_scaled(name, size)
        self.scaled_resources[key] = pygame.transform.rotate(base, angle)
    return self.scaled_resources[key]

# Proyectil: recibe Surface, no ruta
class Proyectil(pygame.sprite.Sprite):
    def __init__(self, image, x, y, danio, velocidad):
        super().__init__()
        self.image = image                 # ya cacheada y orientada
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)   # posición flotante para dt
        self.danio, self.velocidad, self.radio = danio, velocidad, 6
```

Tamaño de bala recomendado: **(12, 24)** para la del jugador, con `radio` 4‑6.

---

### C2. La música se reproduce como `pygame.mixer.Sound`, no como `pygame.mixer.music`

`src/core/resources.py:22` y `src/core/audio.py:42-49`

```python
def load_sound(self, name, path):
    self.resources[name] = pygame.mixer.Sound(path)   # ← también las 5 pistas de música OGG
```

Consecuencias:
- Las **5 pistas OGG se decodifican íntegras en memoria** al arrancar (`cargar_activos_del_juego`), no se *streamean*.
- Cada pista ocupa un **canal del mixer** (solo hay 8 por defecto). Música + SFX simultáneos → canales agotados → efectos que se cortan.
- Es posible tener **dos pistas de música sonando a la vez** (el bug C3 lo provoca).
- No hay *fade in/out* ni control real de "música de fondo".

**Solución:** separar música (streaming) de SFX (memoria).

```python
# ResourceManager
def load_music(self, name, path):
    self.music_paths[name] = path        # NO se carga en RAM

# AudioManager
def reproducir_musica(self, nombre, loops=-1, fade_ms=400):
    if self.pista_actual == nombre:
        return
    ruta = self.rm.music_paths.get(nombre)
    if ruta:
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.set_volume(self.vol_musica)
        pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        self.pista_actual = nombre

def detener_toda_la_musica(self, fade_ms=300):
    pygame.mixer.music.fadeout(fade_ms)
    self.pista_actual = None
```

Esto elimina también `musica_activa` como diccionario y toda la lógica de sincronización manual.

Complementario: inicializar el mixer con buffer pequeño **antes** de `pygame.init()` para reducir latencia:

```python
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(16)
```

---

### C3. `Juego` crea un segundo `AudioManager` distinto al del menú

`src/core/engine.py:46`

```python
self.audio_manager = AudioManager(self.rm, volumen_musica, volumen_efectos)
```

`main.py` ya construyó un `AudioManager` que usa `MenuManager`. Al lanzar partida, `Juego` construye **otro**. Ahora hay dos objetos con dos diccionarios `musica_activa` independientes que se desincronizan: el menú "cree" que suena `skyfire_theme`, el juego reproduce `rain_of_lasers` en otro canal, y `detener_musica` de uno no afecta al otro. En la práctica hoy funciona por casualidad (el menú para su pista justo antes), pero es frágil y fue casi con seguridad introducido en una de las dos etapas sin darse cuenta.

**Solución:** un único `AudioManager` inyectado.

```python
# menu.py  _lanzar_juego
juego = Juego(self.pantalla, self.am, self.clasificacion, self.rm)

# engine.py __init__
def __init__(self, pantalla, audio_manager, clasificacion, resource_manager):
    self.audio_manager = audio_manager
```

---

### C4. Menú de opciones usa la API vieja de `pygame_gui` (`USEREVENT` / `user_type`)

`src/ui/menu.py:122-143`

```python
if event.type == pygame.USEREVENT:
    if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
        ...
    elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
```

`requirements.txt` fija `pygame-gui==0.6.14`. Desde 0.6.0 los eventos se emiten con **su propio `event.type`** (`pygame_gui.UI_BUTTON_PRESSED`, `pygame_gui.UI_HORIZONTAL_SLIDER_MOVED`), y `event.user_type` **ya no existe** → o el menú de opciones no reacciona a nada, o lanza `AttributeError`. Este es el ejemplo más claro de "retoque de hace 6 meses que rompió lo viejo" (se actualizó la dependencia sin migrar el código).

**Solución:**

```python
for event in pygame.event.get():
    if event.type == pygame.QUIT:
        self.ejecutando = False

    if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
        if event.ui_element == self.slider_musica:
            self.vol_musica = event.value
            self.am.actualizar_volumen_musica(self.vol_musica)
        elif event.ui_element == self.slider_efectos:
            self.vol_efectos = event.value
            self.am.actualizar_volumen_efectos(self.vol_efectos)
            self._feedback_sonoro()

    elif event.type == pygame_gui.UI_BUTTON_PRESSED:
        if event.ui_element == self.btn_guardar:
            config.guardar_configuracion(self.vol_musica, self.vol_efectos)
            self.opciones_cargadas = False
            self.estado = "PRINCIPAL"
        elif event.ui_element == self.btn_volver:
            self.opciones_cargadas = False
            self.estado = "PRINCIPAL"

    self.ui_manager.process_events(event)
```

---

### C5. `pygame.time.Clock()` nuevo en cada frame del menú de opciones

`src/ui/menu.py:114`

```python
time_delta = pygame.time.Clock().tick(60) / 1000.0
```

Se crea un `Clock` **nuevo cada frame**; `tick()` sobre un reloj recién creado devuelve ~0 → `time_delta ≈ 0` → `pygame_gui` no anima ni procesa temporizadores correctamente. Además `_menu_opciones` se llama desde dos bucles (`ejecutar` y `mostrar_solo_opciones`) que **también** hacen `clock.tick(60)` → doble limitación / contención de FPS.

**Solución:** un solo `Clock` de instancia (`self.clock` en `__init__`), y que **solo el bucle principal** llame a `tick`. `_menu_opciones` recibe `time_delta` como parámetro.

---

### C6. Salir al menú principal desde el juego cierra el proceso

`src/core/engine.py:228-242`

```python
def mostrar_menu_principal(self):
    ...
    menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)
    menu.ejecutar()
    pygame.quit()
    import sys
    sys.exit()
```

Se lanza un `MenuManager` anidado y, al volver, se mata el proceso. Efecto para el jugador: pulsar "Salir" en Game Over → "menú principal" → cualquier acción → la app se cierra sola. Hay **tres rutas de cierre** en el código (`InputHandler` hace `sys.exit()` en QUIT, `menu.py:181` hace `pygame.quit(); exit()`, `engine.ejecutar` devuelve `False`), y ninguna comparte limpieza.

**Solución:** un único bucle de estados de alto nivel en `main.py` (máquina de estados `MENU`/`JUGANDO`), y que `Juego.ejecutar()` **devuelva** un resultado (`"MENU"`, `"SALIR"`, `"REINICIAR"`) en vez de instanciar menús o llamar a `sys.exit`.

```python
# main.py
estado = "MENU"
while estado != "SALIR":
    if estado == "MENU":
        estado = menu.ejecutar()          # devuelve "JUGAR" o "SALIR"
    elif estado == "JUGAR":
        estado = Juego(...).ejecutar()    # devuelve "MENU" o "SALIR"
pygame.quit()
```

---

### C7. Busy‑wait a 100 % de CPU en diálogos anidados

`src/core/input.py:117-128` (`mostrar_confirmacion_salida`) y `src/ui/menu.py:171-184`

```python
while True:
    for evento in pygame.event.get():
        ...
    # ← sin clock.tick(): el bucle gira tan rápido como pueda
```

Mientras el diálogo "¿Seguro que quieres salir?" está abierto, un núcleo de CPU va al 100 %. Igual en `mostrar_solo_opciones`.

**Solución:** añadir `self.juego.reloj.tick(30)` (o 60) al final de cada iteración de esos bucles, y manejar `pygame.QUIT` de forma limpia.

---

### C8. `reiniciar_juego()` se invoca en mitad del bucle de colisiones

`src/managers/collision.py:57-60`

```python
if isinstance(enemigo, Jefe):
    self.juego.jefe_derrotado = True
    self.juego.jefe = None
    self.juego.reiniciar_juego()      # vacía listas, all_sprites, recrea estado…
```

`reiniciar_juego` limpia `entity_manager`, vacía `all_sprites`, resetea temporizadores y relanza música — **todo mientras `CollisionManager.actualizar()` sigue ejecutando** las siguientes fases (`_colisiones_bala_enemigo`, `_colisiones_jugador_enemigo`, `_colisiones_jugador_items`) sobre un estado que acaba de ser reconstruido en el mismo frame. Hoy no crashea porque se itera sobre copias (`[:]`), pero es una bomba de relojería ante cualquier cambio.

**Solución:** diferir la transición. Marcar `self.juego.pendiente_reinicio = True` y procesarla en un único punto al final de `Juego.actualizar()`, nunca desde dentro de un manager.

---

### C9. Fuga de memoria: `enemigos_golpeados` nunca se limpia

`src/managers/collision.py:89-94` + `src/core/engine.py:73`

```python
self.juego.enemigos_golpeados[enemigo] = tiempo_actual
```

El diccionario usa **el objeto enemigo como clave** y solo se vacía en `reiniciar_juego`. Cada enemigo que toca al jugador queda como clave permanente durante todo el nivel, **manteniendo viva su referencia** aunque ya haya sido eliminado de las listas y del grupo. En una partida larga son cientos de entradas + sprites que no se recolectan.

**Solución:** usar `weakref.WeakKeyDictionary`, o purgar en `_eliminar_enemigo` / `_limpiar_entidades_fuera`:

```python
self.juego.enemigos_golpeados.pop(enemigo, None)   # al eliminar/descartar un enemigo
```

---

### C10. Sin delta time — la física depende de mantener 60 FPS exactos

`src/core/engine.py:270,277` (`self.reloj.tick(60)`, valor de retorno ignorado), `player.py:59`, `enemies.py:29`, `bullet.py:9`, etc.

Todo el movimiento es `self.rect.x += velocidad`. Si el equipo baja a 40 FPS (fase del jefe, muchas balas), **el juego va a cámara lenta**; en un monitor sin vsync que corra a 144, `tick(60)` lo mantiene, pero cualquier stutter altera la jugabilidad. Además `rect` es entero: acumular fracciones (`velocidad 0.5` del fondo, `0.5` de mejora de velocidad) **pierde precisión**.

**Solución:** posición en `pygame.math.Vector2` flotante, velocidades en **px/segundo**, y `dt` propagado:

```python
# engine.ejecutar
dt = self.reloj.tick(60) / 1000.0
self.actualizar(dt)
...
# player.mover(teclas, limites, dt):
self.pos += direccion * self.velocidad * dt      # velocidad ~ 360 px/s
self.rect.center = round(self.pos.x), round(self.pos.y)
```

---

### C11. `enemigos_activos` solo se decrementa

`src/core/engine.py:38`, `collision.py:55`, `entities.py:79` — nunca hay un `+= 1`. `agregar_enemigo` no lo toca. El contador es siempre 0 o negativo. Si algo lo usa para lógica de oleadas en el futuro, fallará silenciosamente.

**Solución:** incrementar en `EntityManager.agregar_enemigo`, o —mejor— eliminar el atributo y usar `len(self.entity_manager.enemigos)` cuando haga falta.

---

## 3. Rendimiento en Pygame (prioridad media‑alta)

### P1. Imágenes sin `convert()` — fondos a pantalla completa

`src/core/resources.py:18-19`

```python
def load_image(self, name, path):
    self.resources[name] = pygame.image.load(path)   # sin .convert()/.convert_alpha()
```

`get_image("imagen_fondo1")` devuelve una `Surface` en el formato del archivo, no el de la pantalla → **cada `blit` hace conversión de formato al vuelo**. El fondo se blitea **dos veces por frame** (`ScrollingBackground.draw`) a 600×800. Es de lo más caro que hace el juego por frame.

**Solución:** convertir al cargar (ya con `set_mode` hecho en `main.py` antes de cargar recursos):

```python
def load_image(self, name, path):
    surf = pygame.image.load(path)
    surf = surf.convert_alpha() if _tiene_alfa(path) else surf.convert()
    self.resources[name] = surf
```

### P2. Doble `update()` del jugador por frame

`src/core/engine.py:274-275`

```python
self.actualizar()          # dentro llama a self.jugador.update()
self.all_sprites.update()   # el jugador también está en all_sprites → update() otra vez
```

`Jugador` se añade a `all_sprites` en su `__init__`. Se actualiza dos veces. Hoy es casi inocuo (solo revisa expiración de invulnerabilidad) pero refleja la confusión de tener 3 sistemas de sprites. **Decидir uno:** o todo en grupos (`enemigos`, `balas_jugador`, `balas_enemigo`, `items`, `efectos`, `jugador`) y `Group.update(dt)` / `Group.draw()`, o todo manual. Recomendado: grupos.

### P3. Colisiones O(n·m) en Python puro, sin `spritecollide`

`src/managers/collision.py` — dobles bucles con `math.hypot` por par. En fase de jefe (bala rápida cada 250 ms + normal cada 1500 ms + enemigos) el número de pares crece. Pygame ya trae detección vectorizada en C:

```python
# Con grupos + colisión circular:
impactos = pygame.sprite.groupcollide(
    self.balas_jugador, self.enemigos, True, False,
    collided=pygame.sprite.collide_circle
)
for bala, enemigos in impactos.items():
    for e in enemigos:
        e.take_damage(bala.danio)
        ...
```

Requiere que cada sprite tenga `self.radius` (nota: `collide_circle` usa `radius`, el código actual usa `radio` en español — unificar). Para hitboxes precisas de naves con formas irregulares, `pygame.sprite.collide_mask` + `self.mask = pygame.mask.from_surface(image)` (creada **una vez**, no por frame).

### P4. `Boton` y fuentes reconstruidos por frame

- `RenderManager._dibujar_pantalla_game_over` crea `pygame.font.SysFont(None, 72)` **cada frame** (`render.py:50`) y `Boton(...)` nuevos cada frame (`render.py:58-61`).
- `RenderManager._dibujar_botones_pausa` crea dos `Boton` por frame (`render.py:96-99`).
- `Boton.dibujar` crea una `Surface` SRCALPHA nueva y redibuja 4 círculos + 2 rects **en cada llamada** (`button.py:20-43`).

**Solución:** crear fuentes en `__init__`; crear los botones una sola vez (al entrar en pausa / game over); que `Boton` cachee su `Surface` renderizada y solo la re‑blitee.

### P5. `RenderManager` recrea superficies grises por frame en pausa

`render.py:109-122` — `img.copy()` + `fill(BLEND_RGB_MULT)` de fondo y de cada sprite, cada frame, mientras el juego está pausado (estado estático). Generar el "frame gris" **una vez** al pausar y blitearlo tal cual.

### P6. Rotación de balas no cacheada

`Proyectil.girar` rota la `Surface` por instancia. Las balas del jugador **siempre** van a 90°: pre‑rotar una vez. Las enemigas van a ángulo arbitrario hacia el jugador: cachear por ángulo cuantizado (p. ej. pasos de 5°) vía `get_image_rotated` (ver C1).

### P7. `Destello.set_alpha` sobre superficie con alfa por píxel no funciona

`src/visual/flash.py:22` — `self.image` se crea con `SRCALPHA` y un círculo `(255,0,0,200)`; luego `set_alpha()` **se ignora** en superficies con alfa por píxel. El *fade* del destello de daño probablemente no se ve. Usar re‑fill con alfa decreciente o `special_flags=BLEND_RGBA_MULT`.

---

## 4. Jugabilidad y mecánicas (prioridad media)

### J1. Curva de dificultad exponencial insostenible

`src/entities/enemies.py:21`

```python
self.salud_maxima = salud_base * (2 ** (nivel - 1))
```

Nivel 1→3: salud enemiga ×1, ×2, ×4. Jefe base 100 → nivel 4 = **800 HP**, nivel 6 = 3200. El daño del jugador tiene tope duro (`danio_max = 3`, `cadencia_max = 150 ms`, triple disparo) → DPS máximo ≈ 60. A partir del nivel 3 el jefe es una esponja de >30 s y los enemigos básicos (base 1 → 8 HP) aguantan varios impactos, rompiendo la sensación de "barrer" enemigos débiles.

**Sugerencia:** escalado sublineal y separado por rol.

```python
FACTOR_NIVEL = 1 + 0.35 * (nivel - 1)          # +35 % por nivel, lineal
self.salud_maxima = round(salud_base * FACTOR_NIVEL)
# Jefe aparte:
self.salud_maxima = round(salud_base * (1 + 0.6 * (nivel - 1)))
```

Y subir un poco los topes del jugador, o añadir mejora de "daño porcentual" para que el progreso acompañe.

### J2. El jefe tarda 62 s en aparecer — cada nivel

`src/managers/waves.py:16` (`TIEMPO_JEFE = 62000`) y `reiniciar_juego` reinicia `inicio_juego`. Un minuto de relleno con solo Tipo 1 los primeros 22 s. Se siente lento y repetitivo.

**Sugerencia:** comprimir las fases y escalar los umbrales a la baja por nivel (`TIEMPO_JEFE * max(0.5, 1 - 0.1*(nivel-1))`), o disparar el jefe por **nº de enemigos eliminados** en vez de por tiempo (más satisfactorio y auto‑ajustado a la habilidad del jugador).

### J3. Hitboxes desalineadas con los sprites

| Entidad | Sprite | `radio` colisión | Radio visual aprox. |
|---|---|---|---|
| Jugador | 50×50 | 16 | ~25 |
| Enemigo estándar | 48×48 | 16 | ~24 |
| Jefe | 200×200 | 80 | ~100 |
| Bala jugador | **50×50** | 16 | ~25 |
| Bala enemiga | 50×50 | 16 | ~25 |

Las balas midiendo 50 px es claramente un valor heredado que nadie ajustó. Un shmup quiere: **hitbox del jugador pequeña y generosa** (~6‑8 px, "grazing"), **balas pequeñas** (~4‑6 px), **enemigos con hitbox ≈ visual**. Ahora mismo las balas enemigas de 50 px con radio 16 dan sensación de "me ha dado sin tocarme" o al revés según el arte.

**Sugerencia:** bala jugador `(10,22)` r≈4; bala enemiga `(16,16)` r≈6; jugador r≈8; enemigo r≈20; jefe r≈95. Añadir un modo debug que dibuje los círculos (`pygame.draw.circle(..., 1)`) para calibrar.

### J4. Movimiento del jugador "clunky"

- Sin aceleración/deceleración: arranque y parada instantáneos.
- Sin normalizar diagonal: moverse en diagonal es √2 ≈ 1.41× más rápido (`player.py:59-60`).
- `clamp_ip(rect_limite.inflate(-15, -45))` — márgenes asimétricos y mágicos.

**Sugerencia:**

```python
d = pygame.math.Vector2(dx, dy)
if d.length_squared() > 0:
    d = d.normalize()
self.vel = self.vel.lerp(d * self.velocidad, 0.25)   # suavizado
self.pos += self.vel * dt
```

### J5. Sonido de "golpe" en cada impacto de bala

`src/managers/collision.py:29` — con triple disparo + cadencia alta contra el jefe se dispara `reproducir_efecto("golpe")` decenas de veces por segundo: saturación de canales y ruido molesto. Throttlear (máx. 1 cada ~80 ms) o bajar volumen del hit por acumulación.

### J6. Daño recibido inconsistente

`_colisiones_bala_enemigo` resta `bala.danio` (2‑3) de una salud máx. de 5, pero `_colisiones_jugador_enemigo` resta 1 fijo. Y `_procesar_muerte_jugador` cura al máximo al perder vida, borrando el daño parcial. El jugador no tiene forma de leer "cuánto me queda" de forma coherente. Unificar: daño de contacto y de bala en la misma escala, o pasar salud a un valor mayor (p. ej. 100) con daños proporcionales.

### J7. `generate_item` muta la lista `pool` con `.remove()`

`src/entities/enemies.py:45-54` — si dos condiciones intentan quitar el mismo elemento o el elemento no está, `list.remove` lanza `ValueError`. Hoy las condiciones son disjuntas, pero es frágil. Usar comprensión/filtrado:

```python
pool = [i for i in POOL_BASE if self._item_util(i, jugador)]
```

---

## 5. Bugs potenciales adicionales (prioridad según se indica)

| # | Prioridad | Ubicación | Problema |
|---|---|---|---|
| B1 | Alta | `input.py:14-17` | `QUIT` hace `pygame.quit(); sys.exit()` directamente → `Juego.ejecutar` nunca ejecuta su limpieza (`detener_musica`). Debe `return False`. |
| B2 | Alta | `menu.py:180-182` | `for _ in pygame.event.get(pygame.QUIT): pygame.quit(); exit()` consume **solo** eventos QUIT del buffer, dejando el resto sin procesar ese frame (entrada perdida). |
| B3 | Media | `engine.py:96-101` | La pausa ajusta timers de enemigos y jugador, pero **no** `wave_manager.tiempo_inicio_espera_jefe` ni los timers de `Explosion`/`Destello`/`Item`. Tras una pausa larga las explosiones saltan al final y la espera del jefe se descuadra. |
| B4 | Media | `scoreboard.py:6` | Ruta `"data/saves/puntuaciones.json"` relativa al CWD. Ejecutar desde otra carpeta → no carga/guarda. Usar `config.DIR_PROYECTO`. |
| B5 | Media | `resources.py:7-12` | `ResourceManager` es singleton por `__new__` pero `__init__` se re‑ejecuta en cada `ResourceManager()`; `main.py` y `engine`/`menu` lo instancian varias veces. Solo el guard `hasattr(self,'scaled_resources')` evita el reset. Frágil: documentar o usar un módulo con instancia única. |
| B6 | Media | `collision.py:78-99` | `_colisiones_jugador_enemigo`: si el enemigo muere por contacto se llama `_eliminar_enemigo` que hace `enemigos.remove(enemigo)`, pero seguimos dentro de `for enemigo in em.enemigos[:]` — ok por la copia; sin embargo `enemigos_golpeados[enemigo]` queda huérfano (ver C9). |
| B7 | Baja | `engine.py:212-226` | `juego_terminado` reutiliza `self.pausado = True` como "freeze" sin fijar `tiempo_pausa`. Si algún flujo llamara a `reanudar_juego` el ajuste temporal sería enorme. Usar un estado propio (`self.estado = "GAME_OVER"`). |
| B8 | Baja | `enemies.py:133-145` | `Jefe` hereda `movimiento_enemigo` pero lo anula con `pass` y mueve en `update`; el resto de enemigos mueven en `movimiento_enemigo` **y** algunos tienen lógica en `update`. Dos convenciones de movimiento conviviendo. |
| B9 | Baja | `hud.py:117-132` | `_dibujar_atributo` es código muerto (sustituido por `_dibujar_barra_con_etiqueta`). Igual `_dibujar_texto`, `_manejar_clic_soltado` en `input.py:100`. |
| B10 | Baja | `config.py` | `Victory Tune.ogg` se carga pero nunca se reproduce; `_feedback` de sonido en opciones usa `get_sound("laser_gun")` que es un SFX, no el alias `"disparo"`. |
| B11 | Baja | `.idea/` versionado | El repo trackea `.idea/` (incluye `copilot.data.migration.ask2agent.xml`). Añadir a `.gitignore` y `git rm -r --cached .idea`. |
| B12 | Baja | `engine.py:240-242` / `menu.py:181` | `import sys` / `import` dentro de funciones y imports circulares menú↔engine resueltos con imports locales. Señal de que la máquina de estados debería vivir fuera de ambos. |

---

## 6. Plan de refactor priorizado

### Fase 1 — Estabilidad (rompe cosas hoy)
1. **C4 + C5** — arreglar API de `pygame_gui` y el `Clock` del menú de opciones (el menú de opciones probablemente no funciona).
2. **C6 + B1 + B2** — máquina de estados única en `main.py`; `Juego.ejecutar()` y `MenuManager.ejecutar()` devuelven un estado; eliminar todos los `sys.exit`/`pygame.quit()` internos.
3. **C7** — `tick()` en los bucles anidados (CPU al 100 %).
4. **C3** — un solo `AudioManager` inyectado.
5. **C8** — diferir `reiniciar_juego` fuera del bucle de colisiones.

### Fase 2 — Rendimiento
6. **C1 + P6** — proyectiles reciben `Surface` cacheada del `ResourceManager`; cachear rotaciones; reducir tamaño de bala.
7. **C2** — música por `pygame.mixer.music` (streaming); `mixer.pre_init`.
8. **P1** — `.convert()`/`.convert_alpha()` al cargar; fondo convertido.
9. **P4 + P5** — cachear botones, fuentes y el frame gris de pausa.

### Fase 3 — Arquitectura
10. **P2 + P3** — unificar en grupos de sprites (`pygame.sprite.Group`), pasar a `groupcollide` + `collide_circle`/`collide_mask` (máscara creada una vez). Unificar `radio`→`radius`.
11. **C9 + C11 + B3** — `WeakKeyDictionary` para `enemigos_golpeados`; eliminar `enemigos_activos`; centralizar el ajuste de pausa (que cada objeto con timer implemente `actualizar_pausa`, incluido `WaveManager`, `Explosion`, `Item`).
12. **C10** — introducir `dt` y posiciones `Vector2`. Es el cambio más transversal; hacerlo con los grupos ya unificados.
13. Extraer un módulo `src/core/settings.py` con `ANCHO=600`, `ALTO=800`, `FPS=60`, velocidades, cadencias, umbrales de oleada y factores de dificultad. Hoy están repartidos como números mágicos en 8 archivos.
14. Reducir el objeto‑Dios: los managers deberían recibir **solo lo que usan** (listas, `audio_manager`, callbacks de evento) en vez de `juego` completo; comunicar cambios de estado con eventos/retornos, no escribiendo atributos de `Juego`.

### Fase 4 — Jugabilidad
15. **J3** — recalibrar hitboxes + modo debug de colisiones.
16. **J1 + J2** — escalado de dificultad lineal; jefe por kills o umbrales comprimidos.
17. **J4** — normalizar diagonal + suavizado de movimiento.
18. **J5 + J6** — throttle de SFX de golpe; unificar escala de daño.

---

## 7. Lo que ya está bien (no tocar)

- Separación en carpetas `core/managers/entities/ui/visual`.
- `ResourceManager.get_image_scaled` con cache por tamaño (la idea es correcta; falta extenderla a rotaciones y proyectiles).
- `EffectManager` pre‑carga los frames de explosión una sola vez.
- `Proyectil` como base común de balas (buena jerarquía, mal método de carga).
- `WaveManager` como director de oleadas desacoplado del `Juego`.
- Constantes de configuración del jugador en `Jugador.CONFIG`.
- Manejo de archivo de puntuaciones corrupto (`try/except` en `cargar_puntuaciones`).
