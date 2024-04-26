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
    def __init__(self, imagen, x, y, pantalla_ancho, nivel, salud):
        super().__init__()
        # Carga la imagen original de la nave enemiga
        self.imagen_original = pygame.image.load(imagen)
        # Escala la imagen a una fracción de su tamaño original
        self.image = pygame.transform.scale(self.imagen_original, (50, 50))
        self.rect = self.image.get_rect(x=x, y=y)
        self.velocidad_x = random.uniform(-2, 2)  # Velocidad horizontal aleatoria
        self.velocidad_y = random.uniform(2, 4)  # Velocidad vertical aleatoria
        self.pantalla_ancho = pantalla_ancho
        self.salud = salud * (2 ** nivel-1)  # Ajuste de la salud según el nivel

    def movimiento_enemigo(self):
        self.rect.y += self.velocidad_y
        self.rect.x += self.velocidad_x

        # Revisa si el enemigo alcanza los bordes de la pantalla
        if self.rect.left < 0 or self.rect.right > self.pantalla_ancho:
            self.velocidad_x *= -1  # Invierte la dirección horizontal si alcanza un borde

    def take_damage(self, damage):
        self.salud -= damage

    def die(self, jugador, enemigos_eliminados):
        item = self.generate_item(jugador, enemigos_eliminados)
        return item

    def generate_item(self, jugador, enemigos_eliminados):
        lista_objetos = ["potenciador_danio.png", "potenciador_cadencia.png", "potenciador_velocidad.png", "curacion.png"]
        item = None

        if jugador.salud == jugador.salud_maxima:
            lista_objetos.remove("curacion.png")
        if jugador.velocidad == jugador.velocidad_maxima:
            lista_objetos.remove("potenciador_velocidad.png")
        if jugador.cadencia_disparo == jugador.cadencia_disparo_maxima:
            lista_objetos.remove("potenciador_cadencia.png")
        if jugador.disparo_triple:
            lista_objetos.remove("potenciador_danio.png")

        if lista_objetos:
            ruta_imagen_base = random.choice([
                resource_manager.get_image_path("potenciador_danio"),
                resource_manager.get_image_path("potenciador_cadencia"),
                resource_manager.get_image_path("potenciador_velocidad"),
                resource_manager.get_image_path("curacion")
            ])
            if isinstance(self, EnemigoTipo1):
                if random.random() < 0.05 or enemigos_eliminados >= 10:  # 5% de probabilidad para EnemigoTipo1
                    nombre_imagen = random.choice(lista_objetos)
                    ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                    item = Item(nombre_imagen, ruta_imagen)
            elif isinstance(self, EnemigoTipo2):
                if random.random() < 0.1 or enemigos_eliminados >= 10:  # 10% de probabilidad para EnemigoTipo2
                    nombre_imagen = random.choice(lista_objetos)
                    ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                    item = Item(nombre_imagen, ruta_imagen)
            elif isinstance(self, EnemigoTipo3):
                if random.random() < 0.2 or enemigos_eliminados >= 10:  # 20% de probabilidad para EnemigoTipo3
                    nombre_imagen = random.choice(lista_objetos)
                    ruta_imagen = os.path.join(ruta_imagen_base, nombre_imagen)
                    item = Item(nombre_imagen, ruta_imagen)

        if item:
            item.set_posicion(self.rect.x, self.rect.y)
        return item

    def aumentar_vida(self, cantidad):
        self.salud += cantidad

    def generate_enemy_bullet(self, image_key, danio, velocidad, jugador):
        direccion_x = jugador.rect.centerx - self.rect.centerx
        direccion_y = jugador.rect.centery - self.rect.centery
        magnitud = math.sqrt(direccion_x ** 2 + direccion_y ** 2)

        if magnitud != 0:
            direccion_x /= magnitud
            direccion_y /= magnitud

        angulo = math.degrees(math.atan2(-direccion_y, direccion_x))
        ruta_imagen_bala_enemigo = resource_manager.get_image_path(image_key)

        bala_enemigo = BalaEnemigo(ruta_imagen_bala_enemigo, self.rect.centerx, self.rect.bottom, direccion_x, direccion_y,
                                   danio=danio, velocidad=velocidad)
        bala_enemigo.girar(angulo)
        return bala_enemigo


class EnemigoTipo1(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, nivel, salud=1):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud=salud)
        # Atributos específicos del tipo de enemigo 1
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(1, 4)
        self.radio = 16  # Definir el radio de la hitbox circular


class EnemigoTipo2(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, lista_balas_enemigas, jugador, nivel, salud=2):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud=salud)
        # Atributos específicos del tipo de enemigo 2
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(2, 4)
        self.lista_balas_enemigas = lista_balas_enemigas  # Guarda la referencia a la lista de balas enemigas
        self.jugador = jugador  # Guarda la referencia al jugador
        self.danio = 2
        self.velocidad_disparo = 7
        self.tiempo_ultimo_ataque = 0  # Inicializa el tiempo del último ataque
        self.tiempo_entre_disparos = 3000
        self.radio = 16  # Definir el radio de la hitbox circular

    def disparo_enemigo(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_ataque > self.tiempo_entre_disparos:
            bala_enemigo = self.generate_enemy_bullet("bala_enemigo", self.danio, self.velocidad_disparo, self.jugador)
            self.tiempo_ultimo_ataque = tiempo_actual
            return bala_enemigo
        else:
            return None


class EnemigoTipo3(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, lista_balas_enemigas, jugador, nivel, salud=3):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud=salud)
        # Atributos específicos del tipo de enemigo 3
        self.velocidad_x = random.uniform(-3, 3)
        self.velocidad_y = random.uniform(3, 6)
        self.lista_balas_enemigas = lista_balas_enemigas
        self.jugador = jugador
        self.danio = 2
        self.velocidad_disparo = 7
        self.tiempo_ultimo_ataque = 0
        self.tiempo_entre_disparos = 1500
        self.radio = 16  # Definir el radio de la hitbox circular

    def disparo_enemigo(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_ataque > self.tiempo_entre_disparos:
            bala_enemigo = self.generate_enemy_bullet("bala_enemigo2", self.danio, self.velocidad_disparo, self.jugador)
            self.tiempo_ultimo_ataque = tiempo_actual
            return bala_enemigo
        else:
            return None


class Jefe(EnemigoBase):
    def __init__(self, imagen, x, y, pantalla_ancho, pantalla_alto, lista_balas_enemigas, jugador, nivel, salud=100, tamano=(200, 200)):
        super().__init__(imagen, x, y, pantalla_ancho, nivel, salud=salud)
        # Carga la imagen del jefe con el tamaño deseado
        self.image = pygame.transform.scale(pygame.image.load(imagen), tamano)
        self.rect = self.image.get_rect(x=x, y=y)
        # Atributos específicos del jefe
        self.velocidad_y = 1  # Velocidad vertical de descenso
        self.velocidad_x = 0  # Velocidad horizontal de movimiento lateral
        self.radio = 50  # Definir el radio de la hitbox circular del jefe
        self.pantalla_alto = pantalla_alto
        self.lista_balas_enemigas = lista_balas_enemigas
        self.jugador = jugador
        self.danio_disparo = 2
        self.danio_disparo_rapido = 1
        self.velocidad_disparo = 7
        self.velocidad_disparo_rapido = 3
        self.tiempo_ultimo_disparo = 0
        self.tiempo_ultimo_disparo_rapido = 0
        self.tiempo_entre_disparos_rapidos = 200  # Tiempo entre cada disparo rápido en milisegundos

    def update(self):
        self.movimiento_jefe()

    def movimiento_jefe(self):
        if self.rect.y < self.pantalla_alto // 4:
            # Incrementa la posición vertical para que baje hacia la mitad de la pantalla
            self.rect.y += self.velocidad_y
        else:
            # Calcula la nueva posición X e Y para el movimiento lateral
            nuevo_x = self.rect.x + self.velocidad_x
            nuevo_y = self.rect.y

            self.velocidad_y = 0

            # Oscilación de la velocidad lateral entre dos valores
            '''amplitud = 2  # Amplitud de la oscilación
            frecuencia = 0.1  # Frecuencia de la oscilación (ajusta según lo deseado)
            fase = pygame.time.get_ticks() * frecuencia  # Fase de la oscilación basada en el tiempo
            velocidad_oscilante = amplitud * math.sin(fase)  # Velocidad oscilante'''

            # Limita el movimiento del jefe para que no salga de los bordes de la pantalla
            if nuevo_x > self.pantalla_ancho - self.rect.width:
                nuevo_x = self.pantalla_ancho - self.rect.width
            elif nuevo_y > self.pantalla_alto // 4:
                self.velocidad_x = 1
                nuevo_y = self.pantalla_alto // 4

            # Actualiza la posición del jefe
            self.rect.x = nuevo_x
            self.rect.y = nuevo_y

    def disparo_jefe(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_disparo > 1500:
            bala_enemigo = self.generate_enemy_bullet("bala_enemigo2", self.danio_disparo, self.velocidad_disparo, self.jugador)
            self.tiempo_ultimo_disparo = tiempo_actual
            return bala_enemigo
        else:
            return None

    def disparo_rapido(self):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_disparo_rapido > self.tiempo_entre_disparos_rapidos:
            bala_enemigo = self.generate_enemy_bullet("bala_enemigo", self.danio_disparo_rapido, self.velocidad_disparo_rapido, self.jugador)
            self.tiempo_ultimo_disparo_rapido = tiempo_actual
            return bala_enemigo
        else:
            return None
