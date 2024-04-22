import math
import random

import pygame
import os
from .bala_enemigo import BalaEnemigo
from .item import Item
from ..resources.resource_manager import ResourceManager


# Crear una instancia global de ResourceManager
resource_manager = ResourceManager()


class EnemigoBase(pygame.sprite.Sprite):
    def __init__(self, imagen, x, y, pantalla_ancho, salud):
        super().__init__()
        # Carga la imagen original de la nave enemiga
        self.imagen_original = pygame.image.load(imagen)
        # Escala la imagen a una fracción de su tamaño original
        self.image = pygame.transform.scale(self.imagen_original, (50, 50))
        self.rect = self.image.get_rect(x=x, y=y)
        self.velocidad_x = random.uniform(-2, 2)  # Velocidad horizontal aleatoria
        self.velocidad_y = random.uniform(2, 4)  # Velocidad vertical aleatoria
        self.pantalla_ancho = pantalla_ancho
        self.salud = salud  # Puntos de salud inicial

    def movimiento_enemigo(self):
        self.rect.y += self.velocidad_y
        self.rect.x += self.velocidad_x

        # Revisa si el enemigo alcanza los bordes de la pantalla
        if self.rect.left < 0 or self.rect.right > self.pantalla_ancho:
            self.velocidad_x *= -1  # Invierte la dirección horizontal si alcanza un borde

    def take_damage(self, damage, jugador):
        self.salud -= damage
        if self.salud <= 0:
            self.die(jugador)

    def die(self, jugador):
        # Obtener las rutas de las imágenes de los objetos del ResourceManager
        ruta_potenciador_danio = resource_manager.get_image_path("potenciador_danio")
        ruta_potenciador_cadencia = resource_manager.get_image_path("potenciador_cadencia")
        ruta_potenciador_velocidad = resource_manager.get_image_path("potenciador_velocidad")
        ruta_curacion = resource_manager.get_image_path("curacion")

        # Lista de rutas de las imágenes de los objetos
        lista_rutas_objetos = [ruta_potenciador_danio, ruta_potenciador_cadencia, ruta_potenciador_velocidad, ruta_curacion]

        # Lista de nombres de los archivos de imagen de los objetos
        lista_objetos = ["potenciador_danio.png", "potenciador_cadencia.png", "potenciador_velocidad.png", "curacion.png"]
        item = None
        if jugador.salud == jugador.salud_maxima:  # Verifica si la salud del jugador está al máximo
            lista_objetos.remove("curacion.png")  # Elimina el objeto de curacion de la lista
        if jugador.velocidad == jugador.velocidad_maxima:
            lista_objetos.remove("potenciador_velocidad.png")
        if jugador.cadencia_disparo == jugador.cadencia_disparo_maxima:
            lista_objetos.remove("potenciador_cadencia.png")
        if jugador.disparo_triple:
            lista_objetos.remove("potenciador_danio.png")
        if lista_objetos:
            ruta_imagen_base = random.choice(lista_rutas_objetos)  # Selecciona una ruta base aleatoria de la lista
            if isinstance(self, EnemigoTipo1) and random.random() < 0.55:
                nombre_imagen = random.choice(lista_objetos)  # Selecciona aleatoriamente un nombre de imagen de la lista
                ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                item = Item(nombre_imagen, ruta_imagen)
            elif isinstance(self, EnemigoTipo2) and random.random() < 0.51:
                nombre_imagen = random.choice(lista_objetos)
                ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                item = Item(nombre_imagen, ruta_imagen)
            elif isinstance(self, EnemigoTipo2) and random.random() < 0.52:
                nombre_imagen = random.choice(lista_objetos)
                ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                item = Item(nombre_imagen, ruta_imagen)
            if item:
                item.set_posicion(self.rect.x, self.rect.y)
        return item

    def aumentar_vida(self, cantidad):
        self.salud += cantidad


class EnemigoTipo1(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, salud=1):
        super().__init__(imagen, x, y, pantalla_ancho, salud=salud)
        # Atributos específicos del tipo de enemigo 1
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(1, 4)
        self.radio = 16  # Definir el radio de la hitbox circular


class EnemigoTipo2(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, lista_balas_enemigas, jugador, salud=2):
        super().__init__(imagen, x, y, pantalla_ancho, salud=salud)
        # Atributos específicos del tipo de enemigo 2
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(2, 4)
        self.lista_balas_enemigas = lista_balas_enemigas  # Guarda la referencia a la lista de balas enemigas
        self.jugador = jugador  # Guarda la referencia al jugador
        self.tiempo_ultimo_ataque = 0  # Inicializa el tiempo del último ataque
        self.radio = 16  # Definir el radio de la hitbox circular

    def disparo_enemigo(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_ataque > 3000:  # 3000 milisegundos = 3 segundos
            # Calcular el vector de dirección hacia el jugador
            direccion_x = self.jugador.rect.centerx - self.rect.centerx
            direccion_y = self.jugador.rect.centery - self.rect.centery
            magnitud = math.sqrt(direccion_x ** 2 + direccion_y ** 2)
            if magnitud != 0:
                direccion_x /= magnitud
                direccion_y /= magnitud
            # Calcular el ángulo de rotación en grados
            angulo = math.degrees(math.atan2(-direccion_y, direccion_x))

            # Construir la ruta a la imagen de la bala del enemigo
            ruta_imagen_bala_enemigo = resource_manager.get_image_path("bala_enemigo")

            # Crear la bala en la posición del enemigo
            bala_enemigo = BalaEnemigo(ruta_imagen_bala_enemigo, self.rect.centerx, self.rect.bottom, direccion_x, direccion_y,
                                       velocidad=5, danio=1)
            # Girar la bala en la dirección correcta
            bala_enemigo.girar(angulo)

            self.tiempo_ultimo_ataque = tiempo_actual  # Actualiza el tiempo del último ataque
            return bala_enemigo
        else:
            return None


class EnemigoTipo3(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, lista_balas_enemigas, jugador, salud=3):
        super().__init__(imagen, x, y, pantalla_ancho, salud=salud)
        # Atributos específicos del tipo de enemigo 3
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(3, 6)
        self.lista_balas_enemigas = lista_balas_enemigas
        self.jugador = jugador
        self.tiempo_ultimo_ataque = 0
        self.radio = 16  # Definir el radio de la hitbox circular

    def disparo_enemigo(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_ataque > 1500:
            # Calcular el vector de dirección hacia el jugador
            direccion_x = self.jugador.rect.centerx - self.rect.centerx
            direccion_y = self.jugador.rect.centery - self.rect.centery
            magnitud = math.sqrt(direccion_x ** 2 + direccion_y ** 2)
            if magnitud != 0:
                direccion_x /= magnitud
                direccion_y /= magnitud
            # Calcular el ángulo de rotación en grados
            angulo = math.degrees(math.atan2(-direccion_y, direccion_x))

            # Construir la ruta a la imagen de la bala del enemigo
            ruta_imagen_bala_enemigo = resource_manager.get_image_path("bala_enemigo2")

            # Crear la bala en la posición del enemigo
            bala_enemigo = BalaEnemigo(ruta_imagen_bala_enemigo, self.rect.centerx, self.rect.bottom, direccion_x, direccion_y,
                                       velocidad=7, danio=2)
            # Girar la bala en la dirección correcta
            bala_enemigo.girar(angulo)

            self.tiempo_ultimo_ataque = tiempo_actual  # Actualiza el tiempo del último ataque
            return bala_enemigo
        else:
            return None
