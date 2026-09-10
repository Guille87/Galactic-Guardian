# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Guille87/Galactic-Guardian/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                  |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------- | -------: | -------: | ------: | --------: |
| main.py                               |       41 |       23 |     44% |     32-75 |
| src/core/audio.py                     |       40 |        2 |     95% |     34-35 |
| src/core/config.py                    |       23 |        0 |    100% |           |
| src/core/engine.py                    |      174 |       30 |     83% |187-188, 224, 230-242, 256-260, 268-293 |
| src/core/input.py                     |       92 |       44 |     52% |47-48, 51-52, 84-114, 119-142 |
| src/core/resources.py                 |       58 |        4 |     93% |78, 84, 94, 97 |
| src/core/settings.py                  |       36 |        0 |    100% |           |
| src/entities/base/movimiento.py       |       18 |        0 |    100% |           |
| src/entities/base/projectile\_base.py |       14 |        1 |     93% |        28 |
| src/entities/bullet.py                |       10 |        0 |    100% |           |
| src/entities/bullet\_enemy.py         |       11 |        0 |    100% |           |
| src/entities/enemies.py               |      129 |       20 |     84% |74, 140-146, 149-153, 178, 191-196, 199-204 |
| src/entities/items.py                 |       20 |        0 |    100% |           |
| src/entities/player.py                |      103 |        4 |     96% |93, 101, 174-175 |
| src/managers/collision.py             |       69 |        0 |    100% |           |
| src/managers/effects.py               |       29 |        0 |    100% |           |
| src/managers/entities.py              |       58 |        6 |     90% |49-50, 54-55, 75-76 |
| src/managers/render.py                |       80 |        1 |     99% |       120 |
| src/managers/waves.py                 |       60 |        8 |     87% |36, 46-47, 54, 60, 79, 83-84 |
| src/ui/components/button.py           |       40 |        7 |     82% | 34-39, 51 |
| src/ui/hud.py                         |      107 |       13 |     88% |82, 155-173 |
| src/ui/menu.py                        |      160 |       79 |     51% |69-72, 77-102, 146, 160, 166-168, 172-178, 187-193, 214-231, 236-268 |
| src/ui/scoreboard.py                  |       33 |        2 |     94% |     37-38 |
| src/visual/background.py              |       22 |        2 |     91% |    27, 30 |
| src/visual/explosions.py              |       20 |        0 |    100% |           |
| src/visual/flash.py                   |       22 |        0 |    100% |           |
| src/visual/flash\_constant.py         |       11 |        1 |     91% |        17 |
| **TOTAL**                             | **1480** |  **247** | **83%** |           |


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