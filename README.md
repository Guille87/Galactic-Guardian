# Galactic Guardian

[![CI](https://github.com/Guille87/Galactic-Guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Guille87/Galactic-Guardian/actions/workflows/ci.yml)
[![Cobertura](https://raw.githubusercontent.com/Guille87/Galactic-Guardian/python-coverage-comment-action-data/badge.svg)](https://github.com/Guille87/Galactic-Guardian/tree/python-coverage-comment-action-data)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

Juego de naves 2D (shoot 'em up) hecho con **pygame-ce**. Sobrevive el mayor tiempo
posible, destruye oleadas de enemigos, mejora tu nave entre partidas y derrota al
jefe de cada nivel.

## Características

- **Oleadas por fases:** la dificultad y los tipos de enemigo cambian según avanza el nivel, hasta que aparece el jefe.
- **Dos modos:** una **campaña** de niveles con jefe final y un modo **sin fin** de oleadas cada vez más duras (con un jefe cada 5), cada uno con su propia tabla de puntuaciones.
- **Progresión:** gana monedas jugando y gástalas en un árbol de 30 mejoras permanentes (ataque, defensa y utilidad) desde el menú: disparo doble y triple, más daño y cadencia, regeneración, botín... Toda la potencia de la nave sale de ahí.
- **Cifras de daño:** cada impacto muestra el daño que hace (y el que recibes); se pueden apagar en Opciones.
- **Combo de puntuación:** cada baja seguida sin que te den sube el multiplicador hasta ×5; el primer golpe lo rompe.
- **Guardado de partida:** el juego apunta el último nivel (o oleada) al que has llegado y puedes continuar desde ahí aunque pierdas o cierres el juego.
- **Tabla de puntuaciones** local, con entrada de nombre al conseguir un top 10.

## Cómo jugar

| Acción | Teclas |
|---|---|
| Mover | Flechas o `W` `A` `S` `D` |
| Disparar | `Espacio` o clic izquierdo |
| Pausa | `Esc` o `P` |
| Depuración (hitboxes) | `F1` — muestra los círculos de colisión; vuelve a pulsar para ocultarlo |
| Depuración (monedas) | `F2` en la pantalla Mejoras — +1000 monedas; solo ejecutando desde el código |

Objetivo: aguanta con vida, gana monedas para mejorar tu nave entre partidas y derrota al jefe
para pasar de nivel. En **Sin fin** no hay final: aguanta cuantas oleadas puedas y sube en su ranking.

## Descargar y jugar (Windows)

En la página de [**Releases**](https://github.com/Guille87/Galactic-Guardian/releases):

- **`GalacticGuardian-vX.Y.Z-setup.exe`** — instalador (sin permisos de administrador).
  Crea acceso directo y desinstalador, y desde el menú del juego puedes
  actualizar a nuevas versiones con un clic.
- **`GalacticGuardian-vX.Y.Z-windows.zip`** — portable: descomprime y ejecuta
  `GalacticGuardian.exe`.

La configuración y las puntuaciones se guardan en `%APPDATA%\GalacticGuardian`.

## Ejecutar desde el código

Necesitas **Python 3.11 o superior**.

```bash
git clone https://github.com/Guille87/Galactic-Guardian.git
cd Galactic-Guardian
```

Crea y activa un entorno virtual:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

Instala las dependencias y ejecuta:

```bash
pip install -r requirements.txt
python main.py
```

> Ejecutando desde el código, `config.ini` y las puntuaciones se guardan en la
> raíz del proyecto.

## Desarrollo

```bash
pip install -r requirements-dev.txt   # incluye las de runtime + pytest
pytest                                # suite completa
pytest --cov --cov-report=term-missing
```

Ejecutar desde el código fuente activa ayudas de desarrollo en pantalla (números de
estadísticas, vida del jefe...); en un build empaquetado no aparecen.

Estructura del código:

| Carpeta | Contenido |
|---|---|
| `src/core/` | bucle de juego (`engine`), configuración (`config`, `settings`), datos de niveles, dificultad y mejoras (`niveles`, `escalado`, `mejoras`), progresión, recursos, audio, entrada |
| `src/managers/` | entidades, colisiones, oleadas, render, efectos |
| `src/entities/` | jugador, enemigos, balas |
| `src/ui/` | menú, HUD, tabla de puntuaciones |
| `src/visual/` | fondo, explosiones, destellos, cifras de daño, temblor de pantalla |
| `tools/` | herramienta de balance de la campaña (solo desarrollo) |
| `tests/` | suite de `pytest` (headless) |

Más detalle de la arquitectura en [`CLAUDE.md`](CLAUDE.md).

## Documentación

- [`ROADMAP.md`](ROADMAP.md) — qué está hecho y qué viene.
- [`CHANGELOG.md`](CHANGELOG.md) — historial de versiones.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — cómo contribuir y publicar versiones.
- [`AUDITORIA.md`](AUDITORIA.md) — auditoría de estabilidad, rendimiento, arquitectura y jugabilidad.

## Licencia

[MIT](LICENSE) © 2024-2026 Guillermo Amado.

## Contacto

¿Preguntas o sugerencias? Abre un [issue](https://github.com/Guille87/Galactic-Guardian/issues)
o escribe a **guillermo_amado@hotmail.es**.
