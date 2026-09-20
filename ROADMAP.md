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

## En curso / próximo (por orden)

Primero lo que no depende de assets; el contenido nuevo va al final porque
espera a que llegue el arte.

### 1 · Contenido nuevo (según lleguen los assets)
- **Enemigos nuevos** — asset a la espera de que consigas un set de un mismo
  autor (arte consistente).
- **Patrones de disparo reutilizables** (abanico, dirigido, ráfaga…) para
  enemigos y jefes.
- **Jefe con fases** por umbral de vida.
- **Mini-jefe**: variante reforzada y más grande de un enemigo normal (más vida,
  quizá un patrón extra) — encaja en el sistema sin ser una pieza nueva.
- **Ítems nuevos**: **escudo temporal** (confirmado); **bomba de pantalla**
  (daño en área + limpia balas) pendiente de encontrar el icono a juego con el
  resto de assets.
- **Eventos ambientales**: **lluvia de asteroides** (confirmado, assets vistos);
  **campo de minas** (probable, mismo caso).

## Backlog — con intención clara de hacerse

- **Progresión entre partidas**: moneda ganada jugando + mejoras permanentes de
  la nave y/o desbloqueables. Es lo que más ilusión le hace al autor — candidato
  a subir de prioridad cuando acabe la lista de "En curso / próximo" o tras el
  modo sin fin.
- **Guardado de partida**: no a mitad de nivel, sino "partida en curso" que se
  pueda cerrar y continuar más tarde — con autoguardado de seguridad en puntos
  concretos (cambio de nivel, por ejemplo) para no perder progreso si el juego
  crashea o se cierra sin querer.
- **Bomba de pantalla** (ver "Contenido nuevo" — depende del asset).
- **Varias naves jugables** con estadísticas distintas. Pendiente de pensar qué
  estadísticas además de daño/cadencia/velocidad tienen sentido (vida máxima,
  tamaño de hitbox = facilidad para esquivar, un disparo especial propio,
  regeneración, capacidad de ítems…) — mirar referencias de otros shoot 'em ups
  antes de diseñarlas.
- **Partículas de impacto** (hoy solo hay explosión al morir, no al golpear) —
  pendiente de revisar qué assets encajan.
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
  campaña y algo del contenido nuevo estén listos, para enseñar algo
  más que el juego base.
- **Ranking online** — necesita un sitio donde guardar las puntuaciones
  (servidor/base de datos). El juego tiene que seguir siendo 100 % gratis de
  mantener, así que solo si aparece una opción con capa gratuita seria y sin
  complicar demasiado el proyecto. Sin prisa.

## Descartado (por ahora)

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
