import math

import pygame

from .bala import Bala
from galactic_guardian.efectos.destello_constante import DestelloConstante


class Jugador(pygame.sprite.Sprite):
    def __init__(self, imagen, pantalla_ancho, pantalla_alto, all_sprites):
        super().__init__()
        # Carga la imagen original de la nave
        self.imagen_original = pygame.image.load(imagen)
        # Escala la imagen a una fracción de su tamaño original
        self.image = pygame.transform.scale(self.imagen_original, (50, 50))
        self.rect = self.image.get_rect(centerx=pantalla_ancho // 2, bottom=pantalla_alto - 10)
        self.danio = 1  # Cantidad de daño que inflige la nave del jugador
        self.danio_maximo = 3  # Cantidad de daño máximo que puede infligir la nave del jugador
        self.vidas = 2  # Establece las vidas iniciales del jugador
        self.salud = 3  # Establece la salud inicial del jugador
        self.salud_maxima = 5  # Establece la salud máxima del jugador
        self.velocidad = 4  # Establece la velocidad de la nave del jugador
        self.velocidad_maxima = 6  # Establece la velocidad máxima de la nave del jugador
        self.cadencia_disparo = 350  # Cadencia de disparo en milisegundos
        self.cadencia_disparo_maxima = 150  # Cadencia de disparo máxima en milisegundos
        self.ultimo_disparo = pygame.time.get_ticks()  # Tiempo del último disparo
        self.disparo_doble = False  # Atributo para rastrear el disparo doble
        self.disparo_triple = False  # Atributo para rastrear el disparo triple
        self.radio = 16  # Definir el radio de la hitbox circular
        self.invulnerable = False  # Atributo para rastrear la invulnerabilidad
        self.tiempo_invulnerable = 0
        self.destello_constante = None
        self.all_sprites = all_sprites  # Guardar una referencia al grupo de sprites

    def mover(self, teclas_presionadas, pantalla_alto, pantalla_ancho):
        """
        Mueve al jugador según las teclas presionadas.
        """
        if teclas_presionadas[pygame.K_UP] or teclas_presionadas[pygame.K_w]:
            self.rect.y -= self.velocidad
        if teclas_presionadas[pygame.K_DOWN] or teclas_presionadas[pygame.K_s]:
            self.rect.y += self.velocidad
        if teclas_presionadas[pygame.K_LEFT] or teclas_presionadas[pygame.K_a]:
            self.rect.x -= self.velocidad
        if teclas_presionadas[pygame.K_RIGHT] or teclas_presionadas[pygame.K_d]:
            self.rect.x += self.velocidad

        # Limita el movimiento del jugador para que no salga de los bordes de la pantalla
        if self.rect.left < 5:
            self.rect.left = 5
        elif self.rect.right > pantalla_ancho - 5:
            self.rect.right = pantalla_ancho - 5
        elif self.rect.top < 30:
            self.rect.top = 30
        elif self.rect.bottom > pantalla_alto - 25:
            self.rect.bottom = pantalla_alto - 25

    def disparar(self):
        tiempo_actual = pygame.time.get_ticks()

        # Si el jugador tiene el poder de disparo triple, dispara tres balas
        if self.disparo_triple:
            if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
                angulo1 = math.degrees(math.atan2(45, 0))
                angulo2 = math.degrees(math.atan2(45, 0))
                angulo3 = math.degrees(math.atan2(45, 0))

                nueva_bala1 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx - 15, self.rect.top + 10, self.danio)
                nueva_bala2 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx, self.rect.top + 10, self.danio)
                nueva_bala3 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx + 15, self.rect.top + 10, self.danio)

                nueva_bala1.girar(angulo1)
                nueva_bala2.girar(angulo2)
                nueva_bala3.girar(angulo3)

                self.ultimo_disparo = tiempo_actual
                return nueva_bala1, nueva_bala2, nueva_bala3

        # Si el jugador tiene el poder de disparo doble, dispara dos balas
        elif self.disparo_doble:
            if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
                angulo1 = math.degrees(math.atan2(45, 0))
                angulo2 = math.degrees(math.atan2(45, 0))

                nueva_bala1 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx - 10, self.rect.top + 10, self.danio)
                nueva_bala2 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx + 10, self.rect.top + 10, self.danio)

                nueva_bala1.girar(angulo1)
                nueva_bala2.girar(angulo2)

                self.ultimo_disparo = tiempo_actual
                return nueva_bala1, nueva_bala2, None

        # Si no tiene mejoras de disparo, dispara una sola bala
        else:
            if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
                # Calcular el ángulo de rotación en grados
                angulo = math.degrees(math.atan2(45, 0))

                # Crear la bala
                nueva_bala1 = Bala('imagenes/balas/bala_jugador1.png', self.rect.centerx, self.rect.top + 10, self.danio)

                # Gira la bala en la dirección correcta
                nueva_bala1.girar(angulo)

                # Actualizar el tiempo del último disparo
                self.ultimo_disparo = tiempo_actual
                return nueva_bala1, None, None
        return None, None, None   # Devuelve None para todos los tipos de balas si no se dispara

    def reducir_salud(self, damage):
        """
        Reduce la salud del jugador.
        :param damage: Cantidad de salud que se va a reducir.
        """
        if not self.invulnerable:  # Verificar si la nave es vulnerable
            self.salud -= damage
            if self.salud <= 0 < self.vidas:
                self.salud = 0  # Evita que la salud sea negativa
                self.invulnerable = True  # Hacer la nave invulnerable
                self.tiempo_invulnerable = pygame.time.get_ticks() + 3000
                # Crear el destello constante alrededor del jugador
                self.destello_constante = DestelloConstante(self)
                # Agregar el destello constante al grupo de sprites
                self.all_sprites.add(self.destello_constante)

    def aumentar_salud(self, cantidad):
        """
        Aumenta la salud del jugador.
        :param cantidad: Cantidad de salud que se va a aumentar.
        """
        self.salud += cantidad

    def reducir_vidas(self, cantidad):
        """
        Reduce la salud del jugador.
        :param cantidad: Cantidad de vidas que se va a reducir.
        """
        self.vidas -= cantidad
        if self.vidas < 0:
            self.vidas = 0  # Evita que las vidas sea negativa

    def update(self):
        """
        Actualiza el estado del jugador en cada fotograma.
        """
        # Verifica si la nave es invulnerable y si ya pasaron los 3 segundos
        if self.invulnerable and pygame.time.get_ticks() > self.tiempo_invulnerable:
            self.invulnerable = False  # Hacer que la nave sea vulnerable nuevamente
            # Eliminar el destello constante
            if self.destello_constante:
                self.destello_constante.kill()
