# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Added

- **Cifras flotantes de daño:** cada impacto sobre un enemigo muestra el daño que hace (amarillo) y
  los que recibe tu nave lo muestran en rojo. Los impactos seguidos al mismo objetivo se suman en
  una sola cifra para no llenar la pantalla. Se pueden apagar en Opciones > Pantalla.
  Entran con un "pop" (nacen pequeñas, crecen un poco de más y se asientan) y terminan
  desvaneciéndose; el enemigo que embiste a tu nave también muestra su daño, aunque seas
  invulnerable.
- **La salud en cifras** ("SALUD: 87/150") bajo las vidas, en rojo cuando queda poca.
- **Monedas de depuración:** en la pantalla Mejoras, al ejecutar desde el código fuente,
  F2 da 1000 monedas para probar el árbol sin jugar (no existe en el juego empaquetado).
- **Herramienta de balance** (`tools/balance.py`, solo para desarrollo). Un modelo
  analítico de la campaña que, con los datos reales del juego, estima para cada
  nivel cuánto daño se recibe, cuánto se tarda en matar al jefe y cuántas
  muertes cuesta, con builds del árbol de referencia y tres perfiles de jugador;
  simula una partida y la progresión entre partidas para calcular cuántas
  hacen falta para completar la campaña. Está validado contra el juego real.
  Con ella se diseñó el reequilibrio de abajo, y `tests/test_diseno_balance.py`
  guarda sus objetivos como pruebas (la primera partida nunca gana, el nivel 1 se
  supera sin mejoras, con el árbol entero se gana, la campaña lleva unas 20
  partidas a un jugador medio).
- **Regeneración** (rama Defensa): recuperas salud poco a poco cuando pasan 3
  segundos sin recibir daño.
- **Disparo triple**, además del doble, y más **disparos por segundo** y **velocidad**
  desde el árbol.
- La pantalla **Mejoras** se **desplaza** (rueda del ratón, barra lateral, teclas o
  **arrastrando con el ratón** como en el móvil) para que quepan los 30 nodos del
  árbol. Las mejoras se compran al soltar el clic, para distinguir un toque de un arrastre.
- Con **disparo doble** las balas salen de los cañones de las alas de la nave; con
  **triple**, de los dos cañones y del morro.

### Changed

- **Reequilibrio de la dificultad y la progresión.** Todo el poder viene ahora
  del árbol de mejoras y la campaña está pensada para llevar unas 20 partidas:
  - **La nave base** empieza con velocidad 5 (antes 4), 4 disparos por segundo
    (antes ~2,9) y 1 bala; el tope de velocidad se queda en 6 y el de cadencia
    sube a 8 disparos por segundo.
  - **Árbol de 30 mejoras**, diez por rama. Las últimas de Ataque (Daño III y IV,
    Cadencia III y IV) llevan el daño a 30 y los disparos a 8 por segundo; Defensa
    suma Blindaje IV y V, Regeneración II y otra Vida extra; Utilidad, Botín III y IV
    (+125 % de monedas en total con Botín I y II), Maestría II y Motores III y IV. La
    velocidad sube en cuatro pasos de +5 % (Motores I–IV) hasta el tope de 6. Comprarlo todo cuesta 39 250 monedas con nuevos costes
    y efectos; la cadencia y la velocidad se leen en el juego como
    "+25 % de velocidad de ataque" y "+5 % de velocidad" en vez de milisegundos.
  - **Dificultad por tablas de nivel** (`src/core/escalado.py`): vida de los
    enemigos, vida del jefe y daño enemigo por nivel; el primer nivel hace un 40 %
    menos de daño, así que se supera sin mejoras. Los enemigos aparecen más
    despacio (900–1100 ms entre uno y otro en el nivel 1, 400–600 en el 5).
  - **Enemigos más manejables:** el tipo 1 cae más despacio (2–3 en vez de 2–4), el 2 pasa a
    2,5–3,5 y el 3 a 3,5–5,5 (antes 3–6); la bala del tipo 2 va más rápida (5) y la del
    tipo 3 más lenta (6, igual que la velocidad máxima de la nave).
  - **Monedas:** 1 por cada 70 puntos (antes 100).
  - **Sin fin:** la vida sigue creciendo por oleada con el mismo paso que entre
    los dos últimos niveles, y el ritmo de aparición sigue el de la campaña.
  - Quien tuviera mejoras compradas del árbol anterior **recupera todo lo gastado**
    al cargar la partida guardada y empieza con el árbol vacío.
- **Salud y daño en números reales.** La nave tiene ahora **50 de salud** (antes 5
  puntos), su bala hace **10** de daño (antes 1), las balas enemigas **10**, el
  cañón pesado del jefe **20** y el choque con un enemigo **10**; los enemigos
  pasan a 10, 20 y 30 de vida y el jefe a 1000 (más lo que suben por nivel). Es
  lo de antes multiplicado por 10, **el juego se comporta igual**: se comprobó
  con partidas deterministas idénticas fotograma a fotograma antes y después. Es
  el paso previo al reequilibrio, que ya podrá usar valores intermedios.
- **La salud bajo la nave es ahora una barra** (con una marca cada 10 de salud, así
  se ve cuántos impactos normales aguanta, hasta 4 marcas) en vez de puntitos. Mide
  siempre lo mismo, y se queda entera dentro de la pantalla aunque la nave esté en el borde.
- **Sin ítems de curación, la salud vuelve por otros caminos.** En el sin fin,
  cada oleada nueva recupera el 40 % de la salud máxima y derrotar a un jefe la
  deja completa; en la campaña sigue curándose del todo al pasar de nivel.
- La mejora "Suerte" (que subía la probabilidad de ítems) desaparece con los
  ítems; el árbol nuevo tiene **Botín I** y **Botín II** (+25 % de monedas cada una).
- Los nodos del árbol de **Mejoras** llevan ahora el icono de los antiguos ítems
  (daño, cadencia, reparación y velocidad) en la esquina, atenuado mientras la
  mejora está bloqueada; las que no tienen un icono a juego, solo texto.

### Removed

- **Los ítems de la partida.** Los enemigos ya no sueltan potenciadores de daño,
  cadencia y velocidad ni curación: la nave solo mejora con las mejoras
  permanentes del árbol. Desaparecen el objeto, el reparto de botín, el contador
  de "piedad", el sonido de recogida y los métodos con los que la nave se
  mejoraba en la partida.

## [0.9.0] - 2026-09-20

Llega la progresión entre partidas: monedas y un árbol de mejoras permanentes.
Sin cambios incompatibles con partidas ni configuración anteriores.

### Added

- **Progresión entre partidas.** Ganas **monedas** jugando (1 por cada 100 puntos,
  con lo que ya cuenta el combo, el nivel y la oleada) y las gastas en la nueva
  pantalla **Mejoras** del menú principal: un árbol de tres ramas —**Ataque**,
  **Defensa** y **Utilidad**— con cuatro mejoras cada una, que se desbloquean en
  orden. Suben con lo que empieza la nave (daño, cadencia, disparo doble,
  salud, vidas, escudo de reaparición, velocidad, más monedas, más ítems y un
  combo más fácil), sin tocar los topes, así que los ítems de la partida siguen
  importando.
  - **Restablecer** deshace todas las compras y devuelve todas las monedas
    gastadas, sin coste.
  - Las monedas se cobran al terminar la partida por cualquier camino (Game Over,
    victoria, salir al menú o cerrar la ventana), y también al acabar cada nivel;
    Game Over y victoria muestran "Monedas: +N (total M)".
  - Se guarda en `data/saves/progresion.json`, en la carpeta de datos de usuario
    (sobrevive a las actualizaciones). Un archivo dañado no rompe el juego: se
    aparta a `.corrupto` y se empieza de cero.
  - Costes, efectos y ritmo de monedas son de primera pasada (`mejoras.py`,
    `settings.MONEDAS_PUNTOS`).
- **Hojas de sprites.** Una animación puede ser ahora una sola imagen con todos
  sus fotogramas en una rejilla (`config.HOJAS`, `ResourceManager.load_spritesheet`
  y `get_frames`), en vez de un archivo por fotograma. Pensado para los assets
  nuevos, que suelen venir así.

### Changed

- **Menú principal con seis botones**: entra **Mejoras** (título y botones siguen
  centrados como un bloque; el aviso de nueva versión, debajo).
- Las pantallas de Game Over y de victoria muestran también la puntuación y las
  monedas ganadas.
- La explosión se carga desde una hoja (`explosion.png`, 4×3 celdas) en lugar de
  11 archivos sueltos: se ve exactamente igual (comprobado píxel a píxel) y ocupa
  menos.

## [0.8.0] - 2026-09-20

Llega el combo de puntuación y el menú principal queda centrado. Sin cambios
incompatibles con partidas ni configuración anteriores; las puntuaciones nuevas
serán mayores por el multiplicador.

### Added

- **Combo de puntuación.** Cada baja seguida sin recibir daño sube tu racha, y
  con ella el multiplicador de puntuación: ×2 a las 10 bajas, ×3 a las 25, ×4 a
  las 50 y ×5 a las 90 (el tope). Se rompe al primer golpe que te llega (o al
  perder una vida); no caduca por tiempo. Se conserva al pasar de nivel en la
  campaña y entre oleadas en el sin fin. El HUD muestra "COMBO ×n" con una barra
  hacia el siguiente escalón, bajo la puntuación. Los umbrales están en
  `settings.py` (`COMBO_UMBRALES`).

### Changed

- **Menú principal centrado.** El título y los cinco botones forman ahora un
  bloque centrado en la pantalla, como en la pausa, en vez de quedar caídos hacia
  abajo. El aviso de nueva versión pasa a mostrarse debajo de los botones.
- **Las puntuaciones ahora se multiplican por el combo**, así que serán mayores
  que antes; las que ya tenías guardadas no cambian y quedarán por debajo.

## [0.7.0] - 2026-09-20

Se puede desactivar el temblor de pantalla y se arregla un halo que se quedaba
puesto al pasar de nivel. Sin cambios incompatibles con partidas, configuración
ni puntuaciones anteriores.

### Added

- **Opción para desactivar el temblor de pantalla**, en una pestaña nueva de
  Opciones, **Pantalla**. Como el resto de Opciones, se aplica al instante,
  **Volver** lo descarta y **Guardar** lo confirma (`[PANTALLA]` en `config.ini`;
  activado por defecto).

### Fixed

- **Campaña: el halo de invulnerabilidad se quedaba en pantalla al pasar de
  nivel.** Si derrotabas al jefe mientras aún tenías el escudo de reaparición
  (los 3 s tras perder una vida), la nave llegaba al nivel siguiente con el halo
  blanco puesto y no se iba nunca, como si fuera invencible. La nave sí recibía
  daño (era solo el halo), pero parecía lo contrario. Ahora el halo se retira
  siempre a la vez que la invulnerabilidad.

## [0.6.0] - 2026-09-20

La pantalla tiembla al recibir golpes y se arregla la salud al avanzar de nivel.
Sin cambios incompatibles con partidas, configuración ni puntuaciones anteriores.

### Added

- **Temblor de pantalla.** El mundo (fondo, enemigos, balas y nave) tiembla al
  recibir un impacto, al perder una vida y, con más fuerza, al derrotar al jefe.
  El HUD se queda quieto para poder leerse. Los golpes se acumulan y el temblor
  se apaga solo; se congela en pausa. Los valores están en `settings.py`
  (`TEMBLOR_*`).

### Fixed

- **Campaña: la salud se restablece al empezar el nivel siguiente.** Antes la
  nave arrancaba el nivel con la barra de salud que traía del anterior (las
  mejoras y las vidas se siguen conservando). Repetir un nivel ya la restauraba.

## [0.5.0] - 2026-09-20

Llega el modo sin fin, con su propio ranking. Sin cambios incompatibles con
partidas, configuración ni puntuaciones anteriores.

### Added

- **Modo sin fin.** Nuevo botón **Sin fin** en el menú principal (el de siempre
  pasa a llamarse **Campaña**). Oleadas de 45 s sin techo: cada una trae más
  enemigos por segundo (hasta un suelo de 200 ms entre apariciones) y más vida,
  y **cada 5 oleadas sale un jefe** —sin más enemigos mientras dura— tras el que
  la partida sigue sin pantallas intermedias. La puntuación se multiplica por el
  número de oleada. Al morir, Game Over con la oleada alcanzada y Reintentar
  vuelve a la oleada 1. La curva vive en `src/core/sin_fin.py`.
- **Ranking propio del sin fin**, en `puntuaciones_sin_fin.json`: no se mezcla con
  el de la campaña. La pantalla de Puntuaciones tiene pestañas **Campaña / Sin
  fin** (la del sin fin muestra la columna *Oleada* en vez de *Nivel*).
- El HUD del sin fin muestra la oleada en curso bajo la puntuación.

## [0.4.0] - 2026-09-20

El juego se puede jugar en inglés, y Opciones se reorganiza en pestañas. Sin
cambios incompatibles con partidas o configuración anteriores.

### Added

- **Inglés.** El juego está traducido al inglés y hay un selector de **Idioma**
  en Opciones (Español / English) que se aplica al instante y se guarda en
  `config.ini`. La primera vez, el juego arranca en el idioma de Windows si es
  inglés y en español en cualquier otro caso. Cada idioma es un JSON en
  `data/assets/idiomas/`; ver `CONTRIBUTING.md` para añadir otros.

### Changed

- Opciones se reparte en **pestañas**: Controles, Idioma y Audio (se abre por
  Controles). Guardar y Volver son comunes a todas: actúan sobre lo tocado en
  cualquiera.
- Opciones: **Volver descarta** los cambios (volumen, idioma y teclas vuelven a
  como estaban al entrar) y **Guardar** los confirma, dejándolos en la sesión y
  escribiéndolos en `config.ini`. Mientras estás en la pantalla los cambios se
  aplican al instante como vista previa. Antes Volver dejaba el volumen y el
  idioma cambiados durante la sesión (sin guardarlos) pero descartaba las teclas.
- Pantalla de Puntuaciones: fondo estrellado oscurecido con una capa
  semitransparente (como en Opciones) para que la tabla se lea mejor.
- Interno: los textos del juego salen ya de un catálogo por idioma
  (`data/assets/idiomas/es.json`) a través de `t(...)` en vez de estar escritos
  en cada pantalla (comprobado comparando capturas de todas las pantallas,
  idénticas píxel a píxel).
- Interno: las oleadas y los niveles pasan a ser **datos**. Cada nivel de la
  campaña se define en una tabla (`src/core/niveles.py`): fases y reparto de
  enemigos, cuándo llega el jefe, cadencia de aparición y música del nivel y del
  jefe. `WaveManager` ya no tiene lógica de niveles, solo lee esa definición. Sin
  cambios visibles: los cinco niveles reproducen exactamente los tiempos y la
  dificultad de antes, pero ahora se pueden retocar (o distinguir) uno a uno. Las
  constantes `TIEMPO_FASE_*`, `TIEMPO_JEFE`, `GEN_*` de `settings.py` desaparecen.

### Fixed

- Opciones desde el menú principal ya no enseña (ni guarda) valores viejos tras
  cambiar algo desde la pausa de una partida: el volumen, las teclas reasignadas
  y el idioma se releen de donde están de verdad. Antes, por ejemplo, subir el
  volumen en la pausa y luego pulsar Guardar en el menú principal lo dejaba en
  el valor anterior.

### Security

- La actualización desde el juego **verifica el instalador** antes de ejecutarlo:
  se compara su SHA-256 con el que publica GitHub para esa Release. Si no
  coincide (descarga corrupta o alterada) se descarta y se ofrece abrir la web
  de descargas; si la Release no trae hash, tampoco se instala solo. No hay
  cambios en el proceso de publicación.

## [0.3.0] - 2026-09-20

Controles reasignables y varias mejoras de menús. Sin cambios incompatibles con
partidas o configuración anteriores.

### Added

- **Menú de opciones — Controles**: la tecla "principal" de mover
  (arriba/abajo/izquierda/derecha), disparar y pausa ahora se puede reasignar
  (por defecto WASD + Espacio + P, como hasta ahora). Las flechas y Esc siguen
  funcionando siempre, sin poder tocarse — red de seguridad para no quedarse
  sin poder moverse o pausar. Aviso si dos acciones chocan en la misma tecla
  (no se aplica el cambio); botón para restaurar los valores por defecto.
  Persistido en `config.ini`.
- Botón **Reanudar** en la pantalla de pausa, encima de Opciones (antes solo se
  podía reanudar con Esc/P).
- Botón **Salir** en el menú principal, con confirmación (antes solo se podía
  cerrar el juego con la X de la ventana).
- El selector de nivel ("Elegir nivel" tras completar uno) ahora incluye
  también el **siguiente** nivel, no solo los ya superados — para poder seguir
  avanzando sin salir de esa pantalla. Elegirlo conserva las mejoras y la
  puntuación (como Continuar); rejugar un nivel anterior sigue empezando la
  nave desde cero.

### Changed

- Pantalla de pausa: el título y los botones se centran juntos como un bloque
  (antes el título estaba en el centro y los botones colgaban por debajo).
- Pantalla de Opciones: etiquetas alineadas a la izquierda con los sliders y
  botones, y fondo estrellado oscurecido para que el texto se lea mejor.

### Fixed

- El aviso de nueva versión se cacheaba 24 h: recién publicada una Release, el
  juego podía tardar hasta un día en avisar aunque se abriera antes. Ahora la
  caché dura 6 h.
- Mientras se descarga la actualización, el resto del menú (Jugar, Opciones,
  Puntuaciones) ya no responde a los clics: antes se podía interrumpir la
  descarga a medias saliendo a jugar.

## [0.2.0] - 2026-09-17

El juego deja de ser infinito: primera versión con una campaña que se puede
completar. Sin cambios incompatibles con partidas o configuración anteriores.

### Added

- **El juego ahora tiene un final.** Campaña de `settings.NIVEL_MAX` niveles fijos
  (5 de partida). Al derrotar a un jefe que no es el último: las balas propias y
  las suyas desaparecen, suena `Victory Tune.ogg` (hasta ahora sin usar) y una
  breve transición cinemática mueve la nave sola —se centra, sube y desaparece
  por arriba mientras el fondo acelera— antes de mostrar la pantalla de **"Nivel
  completado"** (puntuación, enemigos destruidos, tiempo del nivel) con dos
  opciones: continuar al siguiente nivel o **elegir nivel** (rejugar cualquiera
  de los ya superados en la partida actual). Durante la transición el jugador no
  puede moverse, disparar ni pausar. Al continuar, la nave del nivel nuevo
  aparece en su sitio de siempre (las mejoras se conservan). Al derrotar al jefe
  del último nivel hay una pantalla de **victoria final**, con entrada en la
  tabla de puntuaciones si corresponde.
- Las puntuaciones ahora guardan también el **nivel alcanzado**, visible en una
  tabla con cabecera en el menú de Puntuaciones (antes solo se veían nombre y
  puntos, sin cabecera; la columna de puntos queda alineada a la derecha).

### Changed

- El jefe ya no suelta ningún ítem al morir (antes lo hacía siempre); derrotarlo
  es su propia recompensa.

## [0.1.4] - 2026-09-11

Actualización desde el propio juego e instalador de Windows. Sin cambios
incompatibles.

### Added

- **Actualización desde el menú.** Al abrir el menú se comprueba en segundo plano
  la última Release de GitHub. Si hay una más nueva, aparece un banner con el
  botón **Actualizar**:
  - En la versión instalada: descarga el instalador y lo ejecuta en silencio; el
    juego se cierra, se actualiza y se vuelve a abrir solo.
  - Ejecutando desde el código (o si no hay instalador): abre la página de
    descargas en el navegador.
  Best-effort: silencioso sin red, una consulta al día como mucho (cacheada).
  Se desactiva con la variable de entorno `GG_SIN_COMPROBAR_ACTUALIZACIONES`.
- **Instalador de Windows.** `build.yml` genera también
  `GalacticGuardian-vX.Y.Z-setup.exe` (Inno Setup, instalación por usuario sin
  UAC en `%LOCALAPPDATA%\Programs`, acceso directo y desinstalador) además del
  `.zip` portable.

### Fixed

- Menú de opciones: al pulsar una flecha ◄ ► con el volumen en un valor "a medias"
  (p. ej. 0.25), el deslizador saltaba visualmente a 0.35/0.15 durante un frame
  antes de cuadrarse a 0.3/0.2. Ahora el ajuste se aplica en el mismo frame, sin
  ese parpadeo.

## [0.1.3] - 2026-09-10

Primera versión con ejecutable descargable para Windows y pulido del menú de
opciones. Sin cambios incompatibles.

### Added

- La versión del juego se muestra en el título de la ventana y en la esquina del
  menú principal (`src/core/version.py` como fuente única).
- Empaquetado con PyInstaller: `GalacticGuardian.spec` (build en carpeta para
  Windows), `requirements-build.txt` y `main.py --smoke` (arranque headless que
  valida un ejecutable compilado). Ver `CONTRIBUTING.md`.
- Workflow `build.yml`: al publicar una Release compila el ejecutable de Windows
  y adjunta `GalacticGuardian-vX.Y.Z-windows.zip`. La sección "Descargar y jugar"
  del README apunta a las Releases.

### Fixed

- Menú de opciones: las flechas ◄ ► acumulaban error de coma flotante
  (`0`, `2.7e-17`, `0.30000000000000004`…) y un valor que se salía de `[0, 1]`
  por un `1e-17` dejaba el slider **sin responder** al reabrir las opciones.
  Ahora el arrastre de la barra sigue siendo libre (se guarda tal cual, redondeado
  a 2 decimales) y las flechas saltan al múltiplo de 0.1 anterior/siguiente
  (0.27 → 0.3 o 0.2), recortando siempre a `[0, 1]`.
- Menú de opciones: las flechas del slider de **música** no cambiaban el volumen
  (solo funcionaba arrastrando la barra).
- Menú de opciones: la interfaz (`pygame_gui`) se reconstruía en cada entrada,
  dejando varios gestores vivos; ahora se crea una sola vez.
- Menú de opciones: mantener pulsada una flecha ◄ ► arrancaba el desplazamiento
  rápido de `pygame_gui` y el volumen se "disparaba" antes de asentarse en el
  escalón. Ahora un clic (aunque se mantenga) hace un único paso limpio.

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

[Unreleased]: https://github.com/Guille87/Galactic-Guardian/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Guille87/Galactic-Guardian/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Guille87/Galactic-Guardian/releases/tag/v0.1.0
