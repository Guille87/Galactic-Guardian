# Roadmap

Documento vivo: qué está hecho, qué se está haciendo y qué vendrá después. No es un
compromiso de fechas; el orden se reajusta por impacto. El detalle de cada versión
está en [`CHANGELOG.md`](CHANGELOG.md).

## Hecho

- **Auditoría integral** (Fases 1–4) — estabilidad, rendimiento, arquitectura y
  jugabilidad. Detalle en [`AUDITORIA.md`](AUDITORIA.md).
- **Repositorio** — licencia MIT, `requirements` saneados, `pyproject.toml`,
  `.gitattributes`, `.gitignore` acotado, `CONTRIBUTING.md`.
- **Tests** — suite `pytest` headless (~84 % de cobertura).
- **Integración continua** — GitHub Actions (Python 3.11–3.13) + badge de cobertura;
  `main` protegido.
- **Fase 5 — bugs conocidos** — arreglados todos. Ver `CHANGELOG.md` → `[0.1.1]`.
- **Item 14 de la auditoría** — adelgazar el objeto-Dios `Juego`: managers
  mecánicos con dependencias explícitas; Vista/Controlador mantiene `Juego` a
  propósito. Ver `[0.1.2]`.
- **Empaquetado** — `GalacticGuardian.spec`, `.zip` portable e instalador Windows
  (Inno Setup) adjuntos automáticamente a cada Release. Ver `[0.1.3]`.
- **Actualización desde el juego** — aviso de nueva versión en el menú y botón
  *Actualizar* que descarga el instalador y se aplica solo en la versión
  instalada. Ver `[0.1.4]`.
- **Campaña con final** — `settings.NIVEL_MAX` niveles fijos; música de victoria,
  pantalla de "nivel completado" con selector de nivel (rejugar los ya
  superados en la partida actual), y pantalla de victoria final tras el último
  jefe. Ver `[0.2.0]`.
- **Menú de opciones — reasignar teclas** — tecla principal de mover/disparar/
  pausa reasignable (WASD + Espacio + P por defecto); flechas y Esc fijas,
  aviso si dos acciones chocan, botón de restaurar por defecto. Persistido en
  `config.ini`. Ver `[0.3.0]`.
- **Verificación del instalador** — la actualización desde el juego comprueba el
  SHA-256 del instalador (campo `digest` de la API de Releases de GitHub, sin
  tocar `build.yml`) antes de ejecutarlo. Ver `[0.4.0]`.
- **Localización (i18n)** — inglés y español, catálogo por idioma en
  `data/assets/idiomas/`, selector en Opciones con cambio al instante y
  arranque en el idioma del sistema. Añadir otro idioma es un JSON más. Ver
  `[0.4.0]`.
- **Modo sin fin** — oleadas de 45 s sin techo, jefe cada 5, ranking propio y
  pestañas Campaña / Sin fin en Puntuaciones. La curva es de primera pasada y
  quiere partidas de prueba para afinarla (`src/core/sin_fin.py`). Ver
  `[0.5.0]`.
- **Combo de puntuación** — racha de bajas sin recibir daño que sube el
  multiplicador de ×1 a ×5 (umbrales en `settings.py`); se rompe al primer golpe,
  se conserva entre niveles y oleadas, y el HUD lo muestra con una barra. Ver
  `[0.8.0]`.
- **Screen shake** — la pantalla tiembla (solo el mundo, no el HUD) al recibir un
  impacto, perder una vida y derrotar al jefe. Modelo de "trauma" con
  constantes en `settings.py`. Ver `[0.6.0]`.
- **Opción para desactivar el temblor** — pestaña **Pantalla** en Opciones con un
  interruptor del screen shake (accesibilidad), guardado en `config.ini`. Ver
  `[0.7.0]`.
- **Oleadas y niveles como datos** — cada nivel se define en una tabla
  (`src/core/niveles.py`); `WaveManager` solo la lee. Añadir contenido es
  "editar una tabla". Ver `[0.4.0]`.
- **Progresión entre partidas** — monedas ganadas jugando (puntuación ÷ 100) y un
  árbol de 12 mejoras permanentes en tres ramas (Ataque, Defensa, Utilidad), con
  pantalla propia en el menú, guardado en `data/saves/progresion.json` y
  restablecer gratis. Los costes y el ritmo de monedas son de primera pasada y
  quieren partidas de prueba. Ver `[0.9.0]`.
- **Hojas de sprites** — una animación puede ser una sola imagen con los
  fotogramas en una rejilla (`config.HOJAS`, `load_spritesheet` / `get_frames`);
  la explosión ya se carga así. Ver `[0.9.0]`.

## En curso / próximo (por orden)

**Ya no se añadirán assets nuevos** (arte ni sonido): el autor los reserva para
un futuro juego en Unity. Aquí se sigue añadiendo lógica y sistemas, y como
mucho algún icono suelto; lo que dependía de arte nuevo está en "Descartado".

### 1 · Reequilibrio: daño real, ítems fuera y árbol ampliado
Cambio grande decidido por el autor, en **cuatro pasos**, cada uno con su PR y
probado por separado:

0. **Cerrar la progresión** actual (PR + release), para partir de una base estable.
1. **Quitar los ítems de la partida — hecho** (potenciadores y curación: `Item`, loot,
   contador de "piedad", su sonido y la mejora "Suerte") y **reutilizar sus
   iconos** en el árbol si quedan bien (daño y cadencia se parecen; si no, texto).
2. **Números reales, sin cambiar el juego — hecho**: todo ×10 (bala 10, salud 50, bala
   enemiga 10, jefe pesado 20, vida de enemigos ×10). La salud pasa a **barra**
   y las barras de estadísticas se ajustan al máximo alcanzable. Con pruebas de
   equivalencia (tests y simulación) para demostrar que no cambia nada.
3. **Reequilibrio completo** (empezado: la **herramienta de balance** ya está, `tools/balance.py`, y una **propuesta de números** en `tools/propuesta.py`, pendiente de que el autor la revise):
   - Base nueva: velocidad **5** (tope 6, igual), **4 disparos/s** (antes 2,9;
     tope 8 en lugar del 6,7 actual, que salía de 1000 ÷ 150 ms), daño 10, salud 50.
   - Hasta **2 y 3 balas** por disparo y más daño desde el árbol.
   - **Árbol ampliado** (~6 mejoras por rama; nodos compactos con icono y una
     descripción en un panel inferior): Ataque (daño, cadencia, disparo doble y
     triple), Defensa (blindaje, vida extra, escudo, **regeneración**), Utilidad
     (motores hasta el tope, botín, combo).
   - **Dificultad en tablas por nivel** (multiplicador de vida y de daño
     enemigo, en `niveles.py`) en vez de fórmulas; curva propia en el sin fin.
   - **Economía recalculada** con el objetivo de que la campaña lleve unas **20
     partidas**: el nivel 1 se supera sin mejoras y el 5 exige la mayor parte del
     árbol.
   - **Herramienta de balance** (script aparte): para builds de referencia (0 %,
     25 %, 50 %, 75 %, 100 % del árbol) imprime, por nivel, el tiempo de matar al
     jefe, la afluencia de vida enemiga frente al DPS y el daño entrante. Es un
     modelo analítico: da el punto de partida y se afina jugando.
   - **Cifras flotantes de daño** al golpear (y al recibir), con la posibilidad de
     apagarlas desde Opciones junto al temblor.
   - Migrar el guardado de progresión al cambiar los ids del árbol, sin perder
     las compras.
- **Curación sin ítems**: campaña, cura total al pasar de nivel (como hoy); sin
  fin, una parte al cambiar de oleada; y una mejora de Defensa da regeneración.

### 2 · Patrones de disparo reutilizables
- Abanico, dirigido, ráfaga… para enemigos y jefes, con los sprites que ya hay.
  Es la vía para dar variedad sin arte nuevo, y prepara el punto siguiente.

### 3 · Jefe con fases
- Por umbral de vida, cambiando de patrón (depende de los patrones de disparo).

### 4 · Mini-jefe
- Variante reforzada y más grande de un enemigo normal (más vida, quizá un
  patrón extra) — reutiliza el sprite existente, sin ser una pieza nueva.

### 5 · Habilidades nuevas (antes "ítems")
- Al quitar los ítems de la partida, el **escudo temporal** y la **bomba de
  pantalla** (daño en área + limpia balas) dejan de encajar como objetos que
  caen; podrían volver como habilidades del árbol. Cada una necesitaría un icono
  suelto. Pendiente de decidir cuando termine el reequilibrio.

## Backlog — con intención clara de hacerse

- **Guardado de partida**: no a mitad de nivel, sino "partida en curso" que se
  pueda cerrar y continuar más tarde — con autoguardado de seguridad en puntos
  concretos (cambio de nivel, por ejemplo) para no perder progreso si el juego
  crashea o se cierra sin querer.
- **Partículas de impacto** (hoy solo hay explosión al morir, no al golpear) —
  dibujadas por código, sin assets.
- **Intro / transiciones entre niveles** con narrativa ligera — el autor revisa
  y ajusta, la redacción la propone Claude.
- **HUD reescalable y más limpio** — con cuidado: el juego es vertical (nave
  abajo, enemigos desde arriba) y hay que comprobar cómo queda en cada cambio.
- **GIF del juego en el README**.
- **Soporte de mando (Xbox)** — el autor tiene un mando para probarlo.
- **Mini-jefes / Boss Rush**: encadenar solo jefes. No prioritario; depende de
  cuántos jefes acabe teniendo la campaña.
- **Logros** — no ahora, posible más adelante.
- **Builds de Linux/macOS** en `build.yml` — hoy no se pueden probar; se
  retoma si hace falta.
- **Publicación en itch.io** — la hace el autor; candidato natural: cuando la
  progresión y algo del contenido nuevo estén listos, para enseñar algo
  más que el juego base.
- **Ranking online** — necesita un sitio donde guardar las puntuaciones
  (servidor/base de datos). El juego tiene que seguir siendo 100 % gratis de
  mantener, así que solo si aparece una opción con capa gratuita seria y sin
  complicar demasiado el proyecto. Sin prisa.

## Descartado (por ahora)

- **Assets nuevos en general** (arte y sonido) — el autor prefiere reservarlos
  para un futuro juego en Unity, que le resulta más cómodo para trabajar en un
  videojuego. Este proyecto sigue con el arte que tiene. Las hojas de sprites ya
  están listas por si algún día hicieran falta, pero no se espera usarlas. Lo que
  dependía de arte nuevo queda aquí:
  - **Enemigos nuevos** — necesitaban un set de arte de un mismo autor.
  - **Eventos ambientales** (lluvia de asteroides, campo de minas) — necesitan
    sprites nuevos.
  - **Varias naves jugables** con estadísticas distintas — necesitan arte por
    nave. La variedad de estadísticas la cubrirán las mejoras permanentes de la
    progresión, sobre la nave actual.
- **Reto diario con semilla fija + ranking del día** — complejidad que no
  compensa para lo que se busca con este juego.
- **Accesibilidad dedicada** (reducir destellos, modo daltónico) — no se
  considera necesaria para el alcance actual del juego.
- **Object pooling de proyectiles** — medido y descartado: crear una bala cuesta
  ~0,46 µs y reutilizarla ~0,44 µs, así que no ahorra nada. Lo que escala es
  cada bala *viva* (mover + colisionar + dibujar, ~1–2 µs por frame), que el
  pooling no reduce: con 300 balas a la vez el frame usa ~5 % del presupuesto
  de 16,7 ms; con 1.000, ~12 %; con 2.000, ~23 % (headless, esta máquina). Más
  cadencia o más tipos de bala no cambian eso. Volver a mirarlo solo si aparecen
  miles de balas simultáneas o lentitud medida con un profiler; entonces las
  palancas serían colisiones más baratas o dibujar menos, no el pooling.
- **Hit-stop** (congelar la partida unos milisegundos al perder una vida o
  derrotar al jefe) — implementado y descartado tras probarlo: no convenció al
  autor, y el screen shake solo ya da el peso al golpe que se buscaba. Se probó
  con 150 ms al perder una vida y 250 ms con el jefe.
- **Menú de opciones — vídeo** (ventana 1×/2×/pantalla completa/automático,
  `pygame.SCALED`) — implementado y descartado tras probarlo: la experiencia
  con varios tamaños de ventana no convenció al autor. El juego se queda fijo
  a 600×800.
