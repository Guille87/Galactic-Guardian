# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------- | -------: | -------: | ------: | --------: |
| main.py                               |       99 |       74 |     25% |49-86, 90-172 |
| src/core/audio.py                     |       40 |        0 |    100% |           |
| src/core/combo.py                     |       22 |        0 |    100% |           |
| src/core/config.py                    |      114 |        6 |     95% |113-114, 137-138, 173-174 |
| src/core/controles.py                 |       10 |        0 |    100% |           |
| src/core/engine.py                    |      362 |       11 |     97% |499-502, 580, 599-609 |
| src/core/escalado.py                  |       15 |        0 |    100% |           |
| src/core/guardado.py                  |       68 |        6 |     91% |62-63, 75-76, 97-98 |
| src/core/i18n.py                      |       57 |       16 |     72% |44-51, 56-63 |
| src/core/input.py                     |      139 |       30 |     78% |60-62, 102-109, 137-139, 149-150, 191-214 |
| src/core/mejoras.py                   |       34 |        0 |    100% |           |
| src/core/niveles.py                   |       13 |        0 |    100% |           |
| src/core/novedades.py                 |        6 |        1 |     83% |        47 |
| src/core/paths.py                     |       25 |        3 |     88% |38, 50, 52 |
| src/core/preferencias.py              |       20 |        0 |    100% |           |
| src/core/progresion.py                |      104 |        4 |     96% |106-107, 125-126 |
| src/core/resources.py                 |       81 |        4 |     95% |122, 128, 138, 141 |
| src/core/settings.py                  |       53 |        0 |    100% |           |
| src/core/sin\_fin.py                  |       30 |        0 |    100% |           |
| src/core/updates.py                   |      145 |       19 |     87% |74-79, 117-131, 150-151, 159, 189-192 |
| src/core/version.py                   |        1 |        0 |    100% |           |
| src/entities/base/movimiento.py       |       18 |        0 |    100% |           |
| src/entities/base/projectile\_base.py |       14 |        1 |     93% |        28 |
| src/entities/bullet.py                |       10 |        0 |    100% |           |
| src/entities/bullet\_enemy.py         |       11 |        0 |    100% |           |
| src/entities/enemies.py               |      130 |        0 |    100% |           |
| src/entities/player.py                |      104 |        3 |     97% |105, 134, 142 |
| src/managers/collision.py             |       53 |        0 |    100% |           |
| src/managers/effects.py               |       55 |        0 |    100% |           |
| src/managers/entities.py              |       58 |        1 |     98% |        83 |
| src/managers/render.py                |      182 |        1 |     99% |       282 |
| src/managers/waves.py                 |       48 |        0 |    100% |           |
| src/ui/components/button.py           |       40 |        6 |     85% |     34-39 |
| src/ui/hud.py                         |      150 |       13 |     91% |130, 216-234 |
| src/ui/menu.py                        |      990 |       52 |     95% |258, 260, 262, 274-275, 289, 493, 815, 855, 881, 1008-1024, 1075, 1146, 1347-1353, 1359-1362, 1369-1380, 1383, 1393, 1418-1419, 1488-1489 |
| src/ui/scoreboard.py                  |       45 |        2 |     96% |     58-59 |
| src/visual/background.py              |       22 |        1 |     95% |        30 |
| src/visual/explosions.py              |       20 |        0 |    100% |           |
| src/visual/flash.py                   |       22 |        0 |    100% |           |
| src/visual/flash\_constant.py         |       11 |        0 |    100% |           |
| src/visual/floating\_text.py          |       62 |        0 |    100% |           |
| src/visual/screen\_shake.py           |       21 |        0 |    100% |           |
| **TOTAL**                             | **3504** |  **254** | **93%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/Guille87/Galactic-Guardian/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Guille87/Galactic-Guardian/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FGuille87%2FGalactic-Guardian%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.