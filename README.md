# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------- | -------: | -------: | ------: | --------: |
| main.py                               |       71 |       51 |     28% |38-67, 71-119 |
| src/core/audio.py                     |       40 |        0 |    100% |           |
| src/core/config.py                    |       40 |        0 |    100% |           |
| src/core/controles.py                 |       10 |        0 |    100% |           |
| src/core/engine.py                    |      271 |       25 |     91% |257-258, 310-315, 404-407, 429, 437-462 |
| src/core/i18n.py                      |       31 |        0 |    100% |           |
| src/core/input.py                     |      135 |       38 |     72% |61-62, 101-108, 128-143, 184-207 |
| src/core/niveles.py                   |       13 |        0 |    100% |           |
| src/core/paths.py                     |       23 |        3 |     87% |32, 44, 46 |
| src/core/resources.py                 |       58 |        4 |     93% |78, 84, 94, 97 |
| src/core/settings.py                  |       34 |        0 |    100% |           |
| src/core/updates.py                   |      145 |       19 |     87% |74-79, 117-131, 150-151, 159, 189-192 |
| src/core/version.py                   |        1 |        0 |    100% |           |
| src/entities/base/movimiento.py       |       18 |        0 |    100% |           |
| src/entities/base/projectile\_base.py |       14 |        1 |     93% |        28 |
| src/entities/bullet.py                |       10 |        0 |    100% |           |
| src/entities/bullet\_enemy.py         |       11 |        0 |    100% |           |
| src/entities/enemies.py               |      134 |        3 |     98% |74, 207, 215 |
| src/entities/items.py                 |       20 |        0 |    100% |           |
| src/entities/player.py                |      110 |        2 |     98% |  111, 119 |
| src/managers/collision.py             |       53 |        0 |    100% |           |
| src/managers/effects.py               |       31 |        0 |    100% |           |
| src/managers/entities.py              |       60 |        1 |     98% |        85 |
| src/managers/render.py                |      142 |        1 |     99% |       222 |
| src/managers/waves.py                 |       48 |        0 |    100% |           |
| src/ui/components/button.py           |       40 |        6 |     85% |     34-39 |
| src/ui/hud.py                         |      108 |       13 |     88% |86, 159-177 |
| src/ui/menu.py                        |      348 |       35 |     90% |124-127, 137-138, 146-148, 150, 152, 352, 392, 418, 433-435, 469-470, 513-529, 549-553 |
| src/ui/scoreboard.py                  |       45 |        2 |     96% |     56-57 |
| src/visual/background.py              |       22 |        1 |     95% |        30 |
| src/visual/explosions.py              |       20 |        0 |    100% |           |
| src/visual/flash.py                   |       22 |        0 |    100% |           |
| src/visual/flash\_constant.py         |       11 |        0 |    100% |           |
| **TOTAL**                             | **2139** |  **205** | **90%** |           |


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