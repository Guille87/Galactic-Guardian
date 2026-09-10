# Galactic Guardian

[![CI](https://github.com/Guille87/Galactic-Guardian/actions/workflows/ci.yml/badge.svg)](https://github.com/Guille87/Galactic-Guardian/actions/workflows/ci.yml)
[![Cobertura](https://raw.githubusercontent.com/Guille87/Galactic-Guardian/python-coverage-comment-action-data/badge.svg)](https://github.com/Guille87/Galactic-Guardian/tree/python-coverage-comment-action-data)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

Juego de naves 2D (shoot 'em up) hecho con **pygame-ce**. Sobrevive el mayor tiempo
posible, destruye oleadas de enemigos, mejora tu nave con potenciadores y derrota al
jefe de cada nivel.

## Características

- **Oleadas por fases:** la dificultad y los tipos de enemigo cambian según avanza el nivel, hasta que aparece el jefe.
- **Mejoras de nave:** daño, cadencia de disparo (hasta triple), velocidad y curación, con probabilidad de aparición según lo que necesites.
- **Tabla de puntuaciones** local, con entrada de nombre al conseguir un top 10.

## Cómo jugar

| Acción | Teclas |
|---|---|
| Mover | Flechas o `W` `A` `S` `D` |
| Disparar | `Espacio` o clic izquierdo |
| Pausa | `Esc` o `P` |
| Depuración (hitboxes) | `F1` — muestra los círculos de colisión; vuelve a pulsar para ocultarlo |

Objetivo: aguanta con vida, recoge las mejoras que sueltan los enemigos y derrota al jefe
para pasar de nivel.

## Instalación

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

> El juego debe ejecutarse desde la raíz del proyecto (guarda `config.ini` y las
> puntuaciones en rutas relativas a esa carpeta).

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
| `src/core/` | bucle de juego (`engine`), configuración (`config`, `settings`), recursos, audio, entrada |
| `src/managers/` | entidades, colisiones, oleadas, render, efectos |
| `src/entities/` | jugador, enemigos, balas, ítems |
| `src/ui/` | menú, HUD, tabla de puntuaciones |
| `src/visual/` | fondo, explosiones, destellos |
| `tests/` | suite de `pytest` (headless) |

Más detalle de la arquitectura en [`CLAUDE.md`](CLAUDE.md).

## Documentación

- [`ROADMAP.md`](ROADMAP.md) — qué está hecho y qué viene.
- [`CHANGELOG.md`](CHANGELOG.md) — historial de versiones.
- [`AUDITORIA.md`](AUDITORIA.md) — auditoría de estabilidad, rendimiento, arquitectura y jugabilidad.
- Guía de contribución (`CONTRIBUTING.md`): en preparación.

## Licencia

[MIT](LICENSE) © 2024-2026 Guillermo Amado.

## Contacto

¿Preguntas o sugerencias? Abre un [issue](https://github.com/Guille87/Galactic-Guardian/issues)
o escribe a **guillermo_amado@hotmail.es**.
