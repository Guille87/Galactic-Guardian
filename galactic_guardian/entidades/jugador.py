import math

import pygame

from galactic_guardian.efectos.destello_constante import DestelloConstante
from galactic_guardian.resources.resource_manager import ResourceManager
from .bala import Bala

# Instancia global de ResourceManager
resource_manager = ResourceManager()


class Jugador(pygame.sprite.Sprite):
    TAMANO_NAVE = (50, 50)
    DANIO_INICIAL = 1
    VIDAS_INICIALES = 1
    SALUD_INICIAL = 3
    VELOCIDAD_INICIAL = 4
    CADENCIA_DISPARO_INICIAL = 350
    DANIO_MAXIMO = 3
    SALUD_MAXIMA = 5
    VELOCIDAD_MAXIMA = 6
    CADENCIA_DISPARO_MAXIMA = 150

    def __init__(self, imagen, pantalla_ancho, pantalla_alto, all_sprites):
        super().__init__()
        self.imagen_original = pygame.image.load(imagen)
        self.image = pygame.transform.scale(self.imagen_original, Jugador.TAMANO_NAVE)
        self.rect = self.image.get_rect(centerx=pantalla_ancho // 2, bottom=pantalla_alto - 10)
        self.danio = Jugador.DANIO_INICIAL
        self.vidas = Jugador.VIDAS_INICIALES
        self.salud = Jugador.SALUD_INICIAL
        self.velocidad = Jugador.VELOCIDAD_INICIAL
        self.cadencia_disparo = Jugador.CADENCIA_DISPARO_INICIAL
        self.danio_maximo = Jugador.DANIO_MAXIMO  # Cantidad de daño máximo que puede infligir la nave del jugador
        self.salud_maxima = Jugador.SALUD_MAXIMA  # Establece la salud máxima del jugador
        self.velocidad_maxima = Jugador.VELOCIDAD_MAXIMA  # Establece la velocidad máxima de la nave del jugador
        self.cadencia_disparo_maxima = Jugador.CADENCIA_DISPARO_MAXIMA  # Cadencia de disparo máxima en milisegundos
        self.ultimo_disparo = pygame.time.get_ticks()  # Tiempo del último disparo
        self.disparo_doble = False  # Atributo para rastrear el disparo doble
        self.disparo_triple = False  # Atributo para rastrear el disparo triple
        self.radio = 16  # Definir el radio de la hitbox circular
        self.invulnerable = False  # Atributo para rastrear la invulnerabilidad
        self.tiempo_invulnerable = 0
        self.destello_constante = None
        self.all_sprites = all_sprites  # Guardar una referencia al grupo de entidades

    def mover(self, teclas_presionadas, pantalla):
        """
        Mueve al jugador según las teclas presionadas.

        Args:
            teclas_presionadas (dict): Diccionario que contiene el estado de las teclas presionadas.
            pantalla (Surface): Superficie de la pantalla del juego.
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
        self.rect.clamp_ip(pantalla.get_rect().inflate(-15, -45))

    def disparar(self):
        """
        Realiza un disparo si ha pasado suficiente tiempo desde el último disparo.

        Returns:
            tuple: Una tupla que contiene las nuevas balas creadas.
        """
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
            nuevas_balas = self._crear_balas()
            self.ultimo_disparo = tiempo_actual
            return nuevas_balas
        return None, None, None

    def _crear_balas(self):
        """
        Crea nuevas instancias de balas del jugador.

        Returns:
            list: Una lista que contiene las nuevas balas creadas.
        """
        ruta_imagen_bala_jugador = resource_manager.get_image_path("bala_jugador1")
        angulo = math.degrees(math.atan2(45, 0))
        nuevas_balas = []

        if self.disparo_triple:
            for i in range(-1, 2):
                nueva_bala = Bala(ruta_imagen_bala_jugador, self.rect.centerx + i * 15, self.rect.top + 10, self.danio)
                nueva_bala.girar(angulo)
                nuevas_balas.append(nueva_bala)
        elif self.disparo_doble:
            for i in range(2):
                nueva_bala = Bala(ruta_imagen_bala_jugador, self.rect.centerx + (i - 0.5) * 15, self.rect.top + 10, self.danio)
                nueva_bala.girar(angulo)
                nuevas_balas.append(nueva_bala)
        else:
            nueva_bala = Bala(ruta_imagen_bala_jugador, self.rect.centerx, self.rect.top + 10, self.danio)
            nueva_bala.girar(angulo)
            nuevas_balas.append(nueva_bala)

        return nuevas_balas

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
                # Agregar el destello constante al grupo de entidades
                self.all_sprites.add(self.destello_constante)

    def aumentar_salud(self, cantidad):
        """
        Aumenta la salud del jugador.
        :param cantidad: Cantidad de salud que se va a aumentar.
        """
        self.salud += cantidad
        if self.salud > self.salud_maxima:
            self.salud = self.salud_maxima

    def modificar_cadencia(self, cantidad):
        """
        Modifica la cadencia de disparo del jugador.

        Args:
            cantidad (int): Cantidad en milisegundos que se va a modificar la cadencia de disparo.
        """
        self.cadencia_disparo += cantidad
        if self.cadencia_disparo <= self.cadencia_disparo_maxima:
            self.cadencia_disparo = self.cadencia_disparo_maxima

    def modificar_danio(self, cantidad):
        """
        Modifica el daño de las balas del jugador y desbloquea disparos dobles o triples si es necesario.

        Args:
            cantidad (int): Cantidad de daño que se va a modificar.
        """
        if self.disparo_doble and not self.disparo_triple:
            self.disparo_triple = True
            print("¡Disparo triple desbloqueado!")
        if not self.disparo_doble and self.danio >= self.danio_maximo:
            self.disparo_doble = True
            print("¡Disparo doble desbloqueado!")
        self.danio += cantidad
        if self.danio > self.danio_maximo:
            self.danio = self.danio_maximo

    def modificar_velocidad(self, cantidad):
        """
        Modifica la velocidad de movimiento del jugador.

        Args:
            cantidad (int): Cantidad de velocidad que se va a modificar.
        """
        self.velocidad += cantidad
        if self.velocidad > self.velocidad_maxima:
            self.velocidad = self.velocidad_maxima

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
