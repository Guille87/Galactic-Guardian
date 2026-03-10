import math
import random

import pygame

from .bala_enemigo import BalaEnemigo


class EnemigoBase(pygame.sprite.Sprite):
    TAMANO_ESTANDAR = (48, 48)

    def __init__(self, imagen_surface, x, y, pantalla_ancho, nivel, salud_base):
        super().__init__()
        self.image = imagen_surface
        self.rect = self.image.get_rect(x=x, y=y)
        self.pantalla_ancho = pantalla_ancho
        self.radio = 16

        # Escalado de salud por nivel: Salud * 2^(nivel-1)
        self.salud_maxima = salud_base * (2 ** (nivel - 1))
        self.salud = self.salud_maxima

        self.velocidad_x = random.uniform(-2, 2)
        self.velocidad_y = random.uniform(2, 4)

    def movimiento_enemigo(self):
        """Lógica de rebote lateral y descenso."""
        self.rect.y += self.velocidad_y
        self.rect.x += self.velocidad_x

        # Revisa si el enemigo alcanza los bordes de la pantalla
        if self.rect.left < 0 or self.rect.right > self.pantalla_ancho:
            self.velocidad_x *= -1  # Invierte la dirección horizontal si alcanza un borde

    def take_damage(self, damage):
        self.salud -= damage

    def die(self, jugador, enemigos_eliminados):
        """Determina si suelta un ítem al morir."""
        return self.generate_item(jugador, enemigos_eliminados)

    def generate_item(self, jugador, enemigos_eliminados):
        """Lógica de probabilidad de loot basada en el estado del jugador."""
        pool = ["potenciador_danio", "potenciador_cadencia", "potenciador_velocidad", "curacion"]

        if jugador.salud >= jugador.salud_maxima:
            pool.remove("curacion")
        if jugador.velocidad >= jugador.velocidad_maxima:
            pool.remove("potenciador_velocidad")
        if jugador.cadencia_disparo <= jugador.cadencia_disparo_maxima:
            pool.remove("potenciador_cadencia")
        if jugador.tipo_disparo == "triple":
            pool.remove("potenciador_danio")

        if not pool: return None

        prob = 0.05
        if isinstance(self, EnemigoTipo2): prob = 0.1
        if isinstance(self, EnemigoTipo3): prob = 0.2
        if isinstance(self, Jefe): prob = 1.0

        if random.random() < prob or enemigos_eliminados >= 10:
            return random.choice(pool)
        return None

    def _crear_proyectil_hacia_jugador(self, ruta_imagen, danio, velocidad, jugador):
        dx = jugador.rect.centerx - self.rect.centerx
        dy = jugador.rect.centery - self.rect.centery
        distancia = math.hypot(dx, dy)

        if distancia == 0: return None

        # Normalizar vector
        ux, uy = dx / distancia, dy / distancia
        angulo = math.degrees(math.atan2(-uy, ux))

        bala = BalaEnemigo(ruta_imagen, self.rect.centerx, self.rect.bottom, ux, uy, danio, velocidad)
        bala.girar(angulo)
        return bala


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

    def disparo_enemigo(self, ahora, ruta_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(ruta_bala, 2, 4, self.jugador)
        return None


class EnemigoTipo3(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, nivel, jugador):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud_base=3)
        # Atributos específicos del tipo de enemigo 3
        self.jugador = jugador
        self.velocidad_y = random.uniform(3, 6)
        self.tiempo_ultimo_ataque = 0
        self.cadencia = 1500

    def disparo_enemigo(self, ahora, ruta_bala):
        if ahora - self.tiempo_ultimo_ataque > self.cadencia:
            self.tiempo_ultimo_ataque = ahora
            return self._crear_proyectil_hacia_jugador(ruta_bala, 2, 7, self.jugador)
        return None


class Jefe(EnemigoBase):
    TAMANO_JEFE = (200, 200)

    def __init__(self, imagen_surface, x, y, pantalla_ancho, pantalla_alto, nivel, jugador):
        super().__init__(imagen_surface, x, y, pantalla_ancho, nivel, salud_base=100)
        # Atributos específicos del jefe
        self.pantalla_alto = pantalla_alto
        self.jugador = jugador
        self.radio = 80  # Definir el radio de la hitbox circular del jefe
        self.velocidad_y = 2  # Velocidad vertical de descenso
        self.velocidad_x = 3  # Velocidad lateral tras llegar a su posición
        self.ultimo_disparo_normal = 0
        self.ultimo_disparo_rapido = 0

    def movimiento_enemigo(self):
        """
        Anulamos el movimiento base.
        El jefe maneja su propia posición en update.
        """
        pass

    def update(self):
        """Lógica de patrulla del Jefe."""
        # Descenso inicial
        if self.rect.y < self.pantalla_alto // 4:
            self.rect.y += self.velocidad_y
        else:
            # Movimiento lateral
            self.rect.x += self.velocidad_x
            if self.rect.left < 0 or self.rect.right > self.pantalla_ancho:
                self.velocidad_x *= -1

    def disparo_jefe(self, ahora, ruta_bala):
        if ahora - self.ultimo_disparo_normal > 1500:
            self.ultimo_disparo_normal = ahora
            return self._crear_proyectil_hacia_jugador(ruta_bala, 3, 7, self.jugador)
        else:
            return None

    def disparo_rapido(self, ahora, ruta_bala):
        if ahora - self.ultimo_disparo_rapido > 250:
            self.ultimo_disparo_rapido = ahora
            return self._crear_proyectil_hacia_jugador(ruta_bala, 1, 4, self.jugador)
        else:
            return None
