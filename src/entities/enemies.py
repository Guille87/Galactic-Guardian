import math
import random

import pygame

from src.core import escalado, settings
from .bullet_enemy import BalaEnemigo
from .base.movimiento import MovimientoSubpixel


class EnemigoBase(pygame.sprite.Sprite, MovimientoSubpixel):
    TAMANO_ESTANDAR = (48, 48)

    # Datos de cada tipo, como atributos de clase para poder leerlos sin crear un
    # enemigo (p. ej. `tools/balance.py`). Las subclases los sobrescriben.
    SALUD_BASE = 10          # vida en el nivel 1
    VALOR = 1                # puntos que da (antes de multiplicar por nivel y combo)
    VEL_Y = (2, 3)           # rango de velocidad de caída (px/frame-a-60fps)
    CADENCIA = None          # ms entre disparos (None = no dispara)

    def __init__(self, imagen_surface, x, y, pantalla_ancho, nivel):
        super().__init__()
        self.image = imagen_surface
        self.rect = self.image.get_rect(x=x, y=y)
        self.pantalla_ancho = pantalla_ancho
        self.radius = settings.RADIO_ENEMIGO
        self.valor_puntuacion = self.VALOR
        self._init_subpixel()

        # Vida y daño por nivel: tablas de `escalado.py`.
        self.salud_maxima = self.vida_en_nivel(nivel)
        self.salud = self.salud_maxima
        self.danio_x = escalado.danio_x(nivel)

        self.velocidad_x = random.uniform(-2, 2)
        self.velocidad_y = random.uniform(*self.VEL_Y)

    @classmethod
    def vida_en_nivel(cls, nivel):
        """Vida de este tipo de enemigo en `nivel` (sin crear uno: la usa `tools/balance.py`)."""
        return max(1, round(cls.SALUD_BASE * escalado.vida_x(nivel)))

    def danio_escalado(self, base):
        """`base` de daño ajustado a la dificultad del nivel de este enemigo (nunca menos de 1)."""
        return max(1, round(base * self.danio_x))

    def movimiento_enemigo(self, dt):
        """Lógica de rebote lateral y descenso (independiente de FPS)."""
        self._desplazar(self.velocidad_x, self.velocidad_y, dt)
        self._rebotar_en_bordes()

    def _rebotar_en_bordes(self):
        """Rebote lateral con recolocación en el borde.

        Se fija la posición al borde y se fuerza la dirección hacia dentro con
        un módulo mínimo (`REBOTE_MIN_VX`): así ni un frame lento que empuje al
        sprite varios píxeles fuera, ni un enemigo con giro casi vertical, lo
        dejan pegado a la pared.
        """
        vx = max(abs(self.velocidad_x), settings.REBOTE_MIN_VX)
        if self.rect.left < 0:
            self.rect.left = 0
            self.velocidad_x = vx
            self._resto.x = 0.0
        elif self.rect.right > self.pantalla_ancho:
            self.rect.right = self.pantalla_ancho
            self.velocidad_x = -vx
            self._resto.x = 0.0

    def take_damage(self, damage):
        self.salud -= damage

    def _crear_proyectil_hacia_jugador(self, rm, nombre_bala, danio, velocidad, jugador):
        # La bala aparece en la parte baja del enemigo: el vector director se
        # calcula DESDE ese mismo punto (antes se calculaba desde el centro y la
        # bala salía desviada, sobre todo con el jugador muy a un lado).
        origen_x, origen_y = self.rect.centerx, self.rect.bottom
        dx = jugador.rect.centerx - origen_x
        dy = jugador.rect.centery - origen_y
        distancia = math.hypot(dx, dy)

        if distancia == 0: return None

        # Normalizar vector
        ux, uy = dx / distancia, dy / distancia
        angulo = math.degrees(math.atan2(-uy, ux))

        # Imagen ya escalada y rotada (cacheada por el ResourceManager)
        imagen = rm.get_image_rotated(nombre_bala, BalaEnemigo.TAMANO, angulo)

        return BalaEnemigo(imagen, origen_x, origen_y, ux, uy, danio, velocidad)



class EnemigoTipo1(EnemigoBase):
    RECURSO = "enemigo1"   # nombre lógico de su sprite en config.RECURSOS
    SALUD_BASE = 10

    def __init__(self, imagen, x, y, pantalla_ancho, nivel):
        super().__init__(imagen, x, y, pantalla_ancho, nivel)
        # Atributos específicos del tipo de enemigo 1
        self.velocidad_x = random.uniform(-3, 3)


class EnemigoTipo2(EnemigoBase):
    RECURSO = "enemigo2"
    SALUD_BASE = 20
    VALOR = 2
    CADENCIA = 3000
    VEL_Y = (2.5, 3.5)

    def __init__(self, imagen, x, y, pantalla_ancho, nivel, jugador):
        super().__init__(imagen, x, y, pantalla_ancho, nivel)
        # Atributos específicos del tipo de enemigo 2
        self.jugador = jugador  # Guarda la referencia al jugador
        self.tiempo_ultimo_ataque = 0  # Inicializa el tiempo del último ataque
        self.cadencia = self.CADENCIA

    def disparo_enemigo(self, ahora, rm, nombre_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, self.danio_escalado(settings.DANIO_BALA_TIPO2), settings.VEL_BALA_TIPO2, self.jugador)
        return None



class EnemigoTipo3(EnemigoBase):
    RECURSO = "enemigo3"
    SALUD_BASE = 30
    VALOR = 3
    CADENCIA = 1500
    VEL_Y = (3.5, 5.5)

    def __init__(self, imagen, x, y, pantalla_ancho, nivel, jugador):
        super().__init__(imagen, x, y, pantalla_ancho, nivel)
        # Atributos específicos del tipo de enemigo 3
        self.jugador = jugador
        # (se vuelve a sortear: quitar esta llamada cambiaría la secuencia de números aleatorios)
        self.velocidad_y = random.uniform(*self.VEL_Y)
        self.tiempo_ultimo_ataque = 0
        self.cadencia = self.CADENCIA

    def disparo_enemigo(self, ahora, rm, nombre_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, self.danio_escalado(settings.DANIO_BALA_TIPO3), settings.VEL_BALA_TIPO3, self.jugador)
        return None



class Jefe(EnemigoBase):
    RECURSO = "jefe1"
    TAMANO_JEFE = (200, 200)
    SALUD_BASE = escalado.VIDA_JEFE[0]
    VALOR = 1000
    CADENCIA_NORMAL = 1500   # ms entre disparos pesados
    CADENCIA_RAPIDA = 250    # ms entre disparos rápidos

    @classmethod
    def vida_en_nivel(cls, nivel):
        return escalado.vida_jefe(nivel)

    def __init__(self, imagen_surface, x, y, pantalla_ancho, pantalla_alto, nivel, jugador):
        super().__init__(imagen_surface, x, y, pantalla_ancho, nivel)
        # Atributos específicos del jefe
        self.pantalla_alto = pantalla_alto
        self.jugador = jugador
        self.radius = settings.RADIO_JEFE  # hitbox circular del jefe
        self.velocidad_y = 2  # Velocidad vertical de descenso
        self.velocidad_x = 3  # Velocidad lateral tras llegar a su posición
        self.ultimo_disparo_normal = 0
        self.ultimo_disparo_rapido = 0

    def movimiento_enemigo(self, dt):
        """
        Anulamos el movimiento base.
        El jefe maneja su propia posición en update.
        """
        pass

    def update(self, dt=0):
        """Lógica de patrulla del Jefe (independiente de FPS)."""
        # Descenso inicial
        if self.rect.y < self.pantalla_alto // 4:
            self._desplazar(0, self.velocidad_y, dt)
        else:
            # Movimiento lateral con rebote que no se atasca en el borde
            self._desplazar(self.velocidad_x, 0, dt)
            self._rebotar_en_bordes()

    def disparo_jefe(self, ahora, rm, nombre_bala):
        if ahora - self.ultimo_disparo_normal > self.CADENCIA_NORMAL:
            self.ultimo_disparo_normal = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, self.danio_escalado(settings.DANIO_JEFE_NORMAL), settings.VEL_JEFE_NORMAL, self.jugador)
        else:
            return None

    def disparo_rapido(self, ahora, rm, nombre_bala):
        if ahora - self.ultimo_disparo_rapido > self.CADENCIA_RAPIDA:
            self.ultimo_disparo_rapido = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, self.danio_escalado(settings.DANIO_JEFE_RAPIDA), settings.VEL_JEFE_RAPIDA, self.jugador)
        else:
            return None

