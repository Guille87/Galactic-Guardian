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
  jefe. Ver `[Unreleased]` → próxima versión. El modo sin fin queda pendiente
  como **modo aparte** (ver backlog).

## En curso / próximo (por orden)

### 1 · Menú de opciones — vídeo
- Ventana **1×** / **2×** y **pantalla completa** (`pygame.SCALED`, resolución
  lógica 600×800 fija). Se persiste en `config.ini`.

### 2 · Menú de opciones — reasignar teclas
- Mapa de controles configurable (mover, disparar, pausa) persistido en
  `config.ini`. UI de "pulsa una tecla" con aviso si choca con otra acción y
  botón de restaurar por defecto.
- El menú de opciones pasa a tener secciones (Sonido / Vídeo / Controles).

### 3 · Oleadas y niveles como datos (antes de meter contenido nuevo)
- Sacar la definición de fases/enemigos/jefe/música de cada nivel de
  `WaveManager` a una tabla de datos. Añadir contenido pasa a ser "editar una
  tabla", no tocar lógica — y es el paso natural antes de sumar enemigos.
- De la mano: **object pooling de proyectiles** (reutilizar balas en vez de
  crear/destruir constantemente) — mejora de rendimiento, se hace en el mismo
  frente porque toca el mismo código de gestión de entidades.

### 4 · Contenido nuevo (según lleguen los assets)
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
  a subir de prioridad en cuanto la campaña (#1) esté lista.
- **Guardado de partida**: no a mitad de nivel, sino "partida en curso" que se
  pueda cerrar y continuar más tarde — con autoguardado de seguridad en puntos
  concretos (cambio de nivel, por ejemplo) para no perder progreso si el juego
  crashea o se cierra sin querer.
- **Multiplicador de puntuación / combo**: sube mientras no recibes daño, se
  reinicia al primer golpe.
- **Bomba de pantalla** (ver #5 — depende del asset).
- **Varias naves jugables** con estadísticas distintas. Pendiente de pensar qué
  estadísticas además de daño/cadencia/velocidad tienen sentido (vida máxima,
  tamaño de hitbox = facilidad para esquivar, un disparo especial propio,
  regeneración, capacidad de ítems…) — mirar referencias de otros shoot 'em ups
  antes de diseñarlas.
- **Screen shake y hit-stop** al impactar/morir — baratos, sin assets.
- **Partículas de impacto** (hoy solo hay explosión al morir, no al golpear) —
  pendiente de revisar qué assets encajan.
- **Intro / transiciones entre niveles** con narrativa ligera — el autor revisa
  y ajusta, la redacción la propone Claude.
- **HUD reescalable y más limpio** — con cuidado: el juego es vertical (nave
  abajo, enemigos desde arriba) y hay que comprobar cómo queda en cada cambio.
- **GIF del juego en el README**.
- **Soporte de mando (Xbox)** — el autor tiene un mando para probarlo.
- **Localización (i18n)**: preparar el código para inglés/español desde ya (que
  el texto nuevo no quede cableado a pelo) aunque la traducción al inglés se
  haga más adelante.
- **`Modo sin fin (arcade)`**: ahora que hay campaña con final, recuperar el
  bucle infinito de antes como modo aparte, con su propio ranking.
- **Mini-jefes / Boss Rush**: encadenar solo jefes. No prioritario; depende de
  cuántos jefes acabe teniendo la campaña.
- **Logros** — no ahora, posible más adelante.
- **Checksum del instalador** (`SHA256SUMS` en la Release + verificación antes
  de ejecutar el instalador descargado). Barato, cuando se vuelva a tocar
  `build.yml`.
- **Builds de Linux/macOS** en `build.yml` — hoy no se pueden probar; se
  retoma si hace falta.
- **Publicación en itch.io** — la hace el autor; candidato natural: cuando la
  campaña (#1) y algo del contenido nuevo (#5) estén listos, para enseñar algo
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
