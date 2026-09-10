import math
import random

import pygame

from src.core import settings
from .bullet_enemy import BalaEnemigo
from .base.movimiento import MovimientoSubpixel


class EnemigoBase(pygame.sprite.Sprite, MovimientoSubpixel):
    TAMANO_ESTANDAR = (48, 48)
    FACTOR_NIVEL = settings.DIFICULTAD_FACTOR_ENEMIGO

    def __init__(self, imagen_surface, x, y, pantalla_ancho, nivel, salud_base):
        super().__init__()
        self.image = imagen_surface
        self.rect = self.image.get_rect(x=x, y=y)
        self.pantalla_ancho = pantalla_ancho
        self.radius = settings.RADIO_ENEMIGO
        self.valor_puntuacion = 1
        self._init_subpixel()

        # Escalado de salud lineal por nivel: base * (1 + FACTOR * (nivel - 1))
        self.salud_maxima = max(1, round(salud_base * (1 + self.FACTOR_NIVEL * (nivel - 1))))
        self.salud = self.salud_maxima

        self.velocidad_x = random.uniform(-2, 2)
        self.velocidad_y = random.uniform(2, 4)

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

    def die(self, jugador, enemigos_eliminados):
        """Determina si suelta un ítem al morir."""
        return self.generate_item(jugador, enemigos_eliminados)

    CANDIDATOS_LOOT = ("potenciador_danio", "potenciador_cadencia", "potenciador_velocidad", "curacion")

    @staticmethod
    def _loot_util(tipo, jugador):
        """¿Le sirve al jugador este power-up ahora mismo?"""
        if tipo == "curacion":
            return jugador.salud < jugador.salud_maxima
        if tipo == "potenciador_velocidad":
            return jugador.velocidad < jugador.velocidad_maxima
        if tipo == "potenciador_cadencia":
            return jugador.cadencia_disparo > jugador.cadencia_disparo_maxima
        if tipo == "potenciador_danio":
            return jugador.tipo_disparo != "triple"
        return True

    def generate_item(self, jugador, enemigos_eliminados):
        """Lógica de probabilidad de loot basada en el estado del jugador."""
        pool = [t for t in self.CANDIDATOS_LOOT if self._loot_util(t, jugador)]

        if not pool: return None

        prob = 0.05
        if isinstance(self, EnemigoTipo2): prob = 0.1
        if isinstance(self, EnemigoTipo3): prob = 0.2
        if isinstance(self, Jefe): prob = 1.0

        if random.random() < prob or enemigos_eliminados >= 10:
            return random.choice(pool)
        return None

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
    def __init__(self, imagen, x, y, pantalla_ancho, nivel):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud_base=1)
        # Atributos específicos del tipo de enemigo 1
        self.velocidad_x = random.uniform(-3, 3)


class EnemigoTipo2(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, nivel, jugador):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud_base=2)
        # Atributos específicos del tipo de enemigo 2
        self.jugador = jugador  # Guarda la referencia al jugador
        self.tiempo_ultimo_ataque = 0  # Inicializa el tiempo del último ataque
        self.cadencia = 3000
        self.valor_puntuacion = 2

    def disparo_enemigo(self, ahora, rm, nombre_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, settings.DANIO_BALA_TIPO2, settings.VEL_BALA_TIPO2, self.jugador)
        return None



class EnemigoTipo3(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, nivel, jugador):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud_base=3)
        # Atributos específicos del tipo de enemigo 3
        self.jugador = jugador
        self.velocidad_y = random.uniform(3, 6)
        self.tiempo_ultimo_ataque = 0
        self.cadencia = 1500
        self.valor_puntuacion = 3

    def disparo_enemigo(self, ahora, rm, nombre_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, settings.DANIO_BALA_TIPO3, settings.VEL_BALA_TIPO3, self.jugador)
        return None



class Jefe(EnemigoBase):
    TAMANO_JEFE = (200, 200)
    FACTOR_NIVEL = settings.DIFICULTAD_FACTOR_JEFE

    def __init__(self, imagen_surface, x, y, pantalla_ancho, pantalla_alto, nivel, jugador):
        super().__init__(imagen_surface, x, y, pantalla_ancho, nivel, salud_base=100)
        # Atributos específicos del jefe
        self.pantalla_alto = pantalla_alto
        self.jugador = jugador
        self.radius = settings.RADIO_JEFE  # hitbox circular del jefe
        self.velocidad_y = 2  # Velocidad vertical de descenso
        self.velocidad_x = 3  # Velocidad lateral tras llegar a su posición
        self.ultimo_disparo_normal = 0
        self.ultimo_disparo_rapido = 0
        self.valor_puntuacion = 1000

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
        if ahora - self.ultimo_disparo_normal > 1500:
            self.ultimo_disparo_normal = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, settings.DANIO_JEFE_NORMAL, settings.VEL_JEFE_NORMAL, self.jugador)
        else:
            return None

    def disparo_rapido(self, ahora, rm, nombre_bala):
        if ahora - self.ultimo_disparo_rapido > 250:
            self.ultimo_disparo_rapido = ahora
            return self._crear_proyectil_hacia_jugador(
                rm, nombre_bala, settings.DANIO_JEFE_RAPIDA, settings.VEL_JEFE_RAPIDA, self.jugador)
        else:
            return None

