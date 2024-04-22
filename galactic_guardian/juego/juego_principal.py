import random

import pygame

from galactic_guardian.efectos.destello import Destello
from galactic_guardian.efectos.destello_constante import DestelloConstante
from galactic_guardian.entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3
from galactic_guardian.entidades.explosion import Explosion
from galactic_guardian.entidades.item import Item
from galactic_guardian.entidades.jugador import Jugador
from galactic_guardian.juego import menu
from galactic_guardian.resources.resource_manager import ResourceManager
from galactic_guardian.ui.boton import Boton


# Instancia global de ResourceManager
resource_manager = ResourceManager()


class Juego:
    def __init__(self, pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos):

        self.volumen_musica = volumen_musica

        self.all_sprites = pygame.sprite.Group()

        # Rangos para la generación de enemigos
        self.MIN_TIEMPO_GENERACION = 200
        self.MAX_TIEMPO_GENERACION = 1000
        self.tiempo_proximo_enemigo = 0

        # Obtener los efectos de sonido del ResourceManager
        self.EFECTO_DISPARO = resource_manager.get_sound("laser_gun")
        self.EFECTO_GOLPE = resource_manager.get_sound("hit")
        self.EFECTO_ITEM = resource_manager.get_sound("item_take")

        # Establecer los volúmenes de los efectos de sonido
        self.EFECTO_DISPARO.set_volume(volumen_efectos)
        self.EFECTO_GOLPE.set_volume(volumen_efectos)
        self.EFECTO_ITEM.set_volume(volumen_efectos)

        self.pantalla_ancho = pantalla_ancho
        self.pantalla_alto = pantalla_alto
        self.pantalla = menu.crear_pantalla()  # Crea la ventana del juego

        # Cargar imagen del fondo
        self.fondo_imagen1 = resource_manager.get_image("imagen_fondo1")
        self.fondo_imagen2 = resource_manager.get_image("imagen_fondo2")
        self.pos_y_fondo1 = 0
        self.pos_y_fondo2 = -self.pantalla_alto  # Iniciar la segunda imagen arriba de la pantalla

        # Iniciar música de fondo si aún no se ha iniciado
        if not resource_manager.is_music_playing("skyfire_theme"):
            resource_manager.play_music("skyfire_theme", loops=-1)
            resource_manager.set_music_volume("skyfire_theme", volumen_musica)

        # Lista para almacenar los enemigos
        self.enemigos = []

        # Lista para almacenar las balas
        self.balas = []

        # Lista para almacenar las balas de los enemigos
        self.balas_enemigo = []

        # Diccionario para almacenar el estado de golpe de cada enemigo
        self.enemigos_golpeados = []

        # Obtener las imágenes de explosión del ResourceManager
        self.explosion_images = [resource_manager.get_image(f"explosion_{i}") for i in range(1, 12)]

        # Configuración del reloj para limitar la velocidad de fotogramas (FPS)
        self.reloj = pygame.time.Clock()

        # Bandera para indicar si la tecla de disparo está presionada
        self.disparando = False

        # Bandera para indicar si el juego está pausado
        self.pausado = False  # Estado de pausa del juego

        # Tiempo en el que se pausó el juego
        self.tiempo_pausa = None

        # Obtener la imagen del jugador del ResourceManager
        self.ruta_imagen_jugador = resource_manager.get_image_path("jugador")

        # Inicializa el jugador
        self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)

        # Obtener el tiempo en milisegundos en el que comienza el juego
        self.inicio_juego = pygame.time.get_ticks()

    def generar_enemigo(self):
        """
        Genera un nuevo enemigo en una posición aleatoria en la parte superior de la pantalla.
        """
        tiempo_transcurrido = pygame.time.get_ticks() - self.inicio_juego  # Calcular el tiempo transcurrido en milisegundos
        tiempo_espera = 2000  # 2 segundos en milisegundos

        if tiempo_transcurrido >= tiempo_espera:
            ancho_enemigo = 50
            alto_enemigo = 10
            x_enemigo = random.randint(50, self.pantalla_ancho - ancho_enemigo - 50)
            y_enemigo = -alto_enemigo  # Genera el enemigo arriba de la pantalla

            # Construir la ruta al directorio de las imágenes de los enemigos
            ruta_enemigo1 = resource_manager.get_image_path("enemigo1")
            ruta_enemigo2 = resource_manager.get_image_path("enemigo2")
            ruta_enemigo3 = resource_manager.get_image_path("enemigo3")

            # Elige el tipo de enemigo según el tiempo transcurrido
            if tiempo_transcurrido >= 30000:  # Después de 30 segundos en milisegundos
                tipo_enemigo = random.choice([EnemigoTipo1, EnemigoTipo2, EnemigoTipo3])
                if tipo_enemigo == EnemigoTipo1:
                    ruta_imagen = ruta_enemigo1
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho)
                elif tipo_enemigo == EnemigoTipo2:
                    ruta_imagen = ruta_enemigo2
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador)
                else:
                    ruta_imagen = ruta_enemigo3
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador)
            elif tiempo_transcurrido >= 15000:  # Después de 15 segundos en milisegundos
                tipo_enemigo = random.choice([EnemigoTipo1, EnemigoTipo2])
                if tipo_enemigo == EnemigoTipo1:
                    ruta_imagen = ruta_enemigo1
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho)
                else:
                    ruta_imagen = ruta_enemigo2
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador)
            else:
                tipo_enemigo = EnemigoTipo1
                ruta_imagen = ruta_enemigo1
                nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho)

            return nuevo_enemigo

    def manejar_eventos(self):
        """
        Maneja los eventos de pygame.
        """
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False  # Indica que el juego debe terminar
            elif evento.type == pygame.KEYDOWN:
                self._manejar_tecla_presionada(evento.key)
            elif evento.type == pygame.KEYUP:
                self._manejar_tecla_soltada(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                self._manejar_click_presionado(evento.button)
            elif evento.type == pygame.MOUSEBUTTONUP:
                self._manejar_click_soltado(evento.button)

            # Si el juego está pausado, no manejar otros eventos
        if self.pausado:
            return True

            # Si la tecla de disparo está presionada, crea una nueva bala
        if self.disparando:
            self._disparar()

        return True

    def _manejar_tecla_presionada(self, tecla):
        """
        Maneja el evento de tecla presionada.
        Si se presiona la tecla de escape, pausa o reanuda el juego.
        Si se presiona la tecla de espacio, activa el disparo si el juego no está pausado.
        """
        if tecla == pygame.K_ESCAPE:
            if not self.pausado:
                self._pausar_juego()
            else:
                self._reanudar_juego()
        elif tecla == pygame.K_SPACE:
            if not self.pausado:
                self.disparando = True
                self._disparar()

    def _manejar_tecla_soltada(self, tecla):
        """
        Maneja el evento de tecla soltada.
        Si se suelta la tecla de espacio, desactiva el disparo si el juego no está pausado.
        """
        if tecla == pygame.K_SPACE:
            if not self.pausado:
                self.disparando = False

    def _manejar_click_presionado(self, boton):
        """
        Maneja el evento de clic de ratón presionado.
        Si se presiona el botón izquierdo del ratón, activa el disparo si el juego no está pausado.
        """
        if boton == 1:  # Botón izquierdo del ratón
            if not self.pausado:
                self.disparando = True
                self._disparar()

    def _manejar_click_soltado(self, boton):
        """
        Maneja el evento de clic de ratón soltado.
        Si se suelta el botón izquierdo del ratón, desactiva el disparo si el juego no está pausado.
        """
        if boton == 1:  # Botón izquierdo del ratón
            if not self.pausado:
                self.disparando = False

    def _pausar_juego(self):
        """
        Pausa el juego y guarda el tiempo en que se pausó.
        """
        self.pausado = True
        self.tiempo_pausa = pygame.time.get_ticks()

    def _reanudar_juego(self):
        """
        Reanuda el juego y ajusta los tiempos para sincronizarlos con el tiempo pausado.
        """
        self.pausado = False
        tiempo_actual = pygame.time.get_ticks()
        tiempo_pausado = tiempo_actual - self.tiempo_pausa
        self.tiempo_proximo_enemigo += tiempo_pausado
        self.jugador.tiempo_invulnerable += tiempo_pausado  # Actualizar el tiempo de invulnerabilidad del jugador
        for enemigo in self.enemigos:
            if isinstance(enemigo, EnemigoTipo2) or isinstance(enemigo, EnemigoTipo3):
                enemigo.tiempo_ultimo_ataque += tiempo_pausado

    def _disparar(self):
        """
        Maneja la lógica de disparo del jugador.
        """
        # Llama a la función disparar del jugador para obtener las nuevas balas
        nueva_bala1, nueva_bala2, nueva_bala3 = self.jugador.disparar()

        # Verifica si hay una nueva bala y la agrega a la lista de balas
        if nueva_bala1:
            self.balas.append(nueva_bala1)
            self.EFECTO_DISPARO.play()

        # Verifica si hay una segunda nueva bala y la agrega a la lista de balas
        if nueva_bala2:
            self.balas.append(nueva_bala2)

        # Verifica si hay una tercera nueva bala y la agrega a la lista de balas
        if nueva_bala3:
            self.balas.append(nueva_bala3)

    def actualizar(self):
        """
        Actualiza el estado del juego.
        """
        if self.jugador.vidas <= 0:
            self.juego_terminado()
            return

        self.actualizar_jugador()
        self.generar_enemigos()
        self.actualizar_enemigos()
        self.eliminar_elementos_fuera_de_pantalla()
        self.eliminar_colisiones_bala_jugador()
        self.eliminar_colisiones_bala_enemigo()
        self.mover_fondo()
        self.jugador.update()

    def eliminar_elementos_fuera_de_pantalla(self):
        """
        Elimina los elementos (balas, enemigos y objetos) que están fuera de la pantalla.
        """
        self.balas = [bala for bala in self.balas if not (bala is not None and self.fuera_de_pantalla(bala.rect))]
        self.enemigos = [enemigo for enemigo in self.enemigos if not (enemigo is not None and self.fuera_de_pantalla(enemigo.rect))]
        self.balas_enemigo = [bala_enemiga for bala_enemiga in self.balas_enemigo if
                              not (bala_enemiga is not None and self.fuera_de_pantalla(bala_enemiga.rect))]
        self.all_sprites = pygame.sprite.Group([item for item in self.all_sprites if not (item is not None and self.fuera_de_pantalla(item.rect))])

    def fuera_de_pantalla(self, rect):
        """
        Verifica si un rectángulo está fuera de la pantalla.

        Args:
            rect: Rectángulo a verificar.

        Returns:
            bool: True si el rectángulo está fuera de la pantalla, False en caso contrario.
        """
        return rect.bottom < 0 or rect.top > self.pantalla_alto or rect.right < 0 or rect.left > self.pantalla_ancho

    def eliminar_colisiones_bala_jugador(self):
        """
        Elimina las colisiones entre las balas del jugador y los enemigos.
        """
        for bala in self.balas:
            bala.bala_jugador()
            self.eliminar_colision_bala_enemigo(bala)

    def eliminar_colision_bala_enemigo(self, bala):
        """
        Elimina las colisiones entre las balas de los enemigos y el jugador.

        Args:
            bala: Bala del enemigo a comprobar.
        """
        for enemigo in self.enemigos:
            if bala.comprobar_colision(enemigo):
                self.procesar_colision_bala_enemigo(bala, enemigo)
                break

    def procesar_colision_bala_enemigo(self, bala, enemigo):
        """
        Procesa la colisión entre una bala y un enemigo.

        Args:
            bala: Bala del jugador.
            enemigo: Enemigo colisionado.
        """
        balas_a_eliminar = [bala, enemigo]
        # Reducir la salud del enemigo según el daño de la bala del jugador
        enemigo.take_damage(bala.danio, self.jugador)
        if enemigo.salud <= 0:
            self.enemigos.remove(enemigo)
            explosion = Explosion(enemigo.rect.center, self.explosion_images)
            self.all_sprites.add(explosion)  # Añadir la explosión al grupo de entidades
            objeto = enemigo.die(self.jugador)  # Crear un objeto cuando el enemigo muere
            if objeto:
                self.all_sprites.add(objeto)
        self.EFECTO_GOLPE.play()
        self.eliminar_elementos(balas_a_eliminar)

    def manejar_impacto_jugador(self):
        """
        Maneja el impacto en el jugador.
        Si el jugador tiene vidas restantes.
        Si la salud del jugador es mayor que 0, crea un destello en la posición del jugador.
        Si la salud del jugador llega a 0, crea una explosión en la posición del jugador,
        reposiciona al jugador en el centro de la parte inferior de la pantalla,
        reduce una vida y, si quedan vidas restantes, aumenta la salud del jugador en 5.
        """
        if self.jugador.vidas > 0:
            if self.jugador.salud > 0:
                self.crear_destello()
            else:
                self.jugador_explota()
                self.reposicionar_jugador()
                self.reducir_vidas_y_aumentar_salud()

    def crear_destello(self):
        """
        Crea un destello en la posición del jugador.
        """
        if not self.jugador.invulnerable:
            destello = Destello(self.jugador)
            self.all_sprites.add(destello)

    def jugador_explota(self):
        """
        Crea una explosión en la posición del jugador.
        """
        explosion = Explosion(self.jugador.rect.center, self.explosion_images)
        self.all_sprites.add(explosion)

    def reposicionar_jugador(self):
        """
        Reposiciona al jugador en el centro inferior de la pantalla.
        """
        self.jugador.rect.centerx = self.pantalla_ancho // 2
        self.jugador.rect.bottom = self.pantalla_alto - 10

    def reducir_vidas_y_aumentar_salud(self):
        """
        Reduce una vida al jugador y aumenta su salud si quedan vidas restantes.
        """
        self.jugador.reducir_vidas(1)
        self.jugador.invulnerable = True
        self.jugador.tiempo_invulnerable = pygame.time.get_ticks() + 3000
        self.crear_destello_constante()
        if self.jugador.vidas > 0:
            self.jugador.aumentar_salud(self.jugador.salud_maxima)

    def crear_destello_constante(self):
        """
        Crea un destello constante en la posición del jugador.
        """
        self.jugador.destello_constante = DestelloConstante(self.jugador)
        self.all_sprites.add(self.jugador.destello_constante)

    def eliminar_colisiones_bala_enemigo(self):
        """
        Maneja las colisiones entre las balas del enemigo y el jugador.
        Si una bala del enemigo colisiona con el jugador, la elimina, maneja el impacto en el jugador
        y reproduce un efecto de golpe.
        También elimina las balas del enemigo que están fuera de la pantalla.
        """
        balas_enemigas_a_eliminar = []
        for bala_enemiga in self.balas_enemigo:
            bala_enemiga.bala_enemigo()
            if bala_enemiga.comprobar_colision(self.jugador):
                self.eliminar_elementos([bala_enemiga])
                self.jugador.reducir_salud(bala_enemiga.danio)
                self.manejar_impacto_jugador()
                self.EFECTO_GOLPE.play()
            elif self.fuera_de_pantalla(bala_enemiga.rect):
                balas_enemigas_a_eliminar.append(bala_enemiga)
        self.eliminar_elementos(balas_enemigas_a_eliminar)

    def eliminar_elementos(self, elementos):
        """
        Elimina los elementos dados de las listas correspondientes.

        Args:
            elementos (list): Lista de elementos a eliminar.
        """
        for elemento in elementos:
            if elemento in self.balas:
                self.balas.remove(elemento)
            elif elemento in self.balas_enemigo:
                self.balas_enemigo.remove(elemento)

    def actualizar_jugador(self):
        """
        Actualiza la posición del jugador en función de las teclas presionadas.
        """
        teclas_presionadas = pygame.key.get_pressed()
        self.jugador.mover(teclas_presionadas, self.pantalla_alto, self.pantalla_ancho)
        self.detectar_colisiones_objetos()

    def detectar_colisiones_objetos(self):
        """
        Detecta y maneja las colisiones entre el jugador y los objetos.
        """
        for objeto in self.all_sprites:
            if isinstance(objeto, Item) and self.jugador.rect.colliderect(objeto.rect):
                self.EFECTO_ITEM.play()
                self.aplicar_efecto_y_eliminar(objeto)

    def aplicar_efecto_y_eliminar(self, objeto):
        """
        Aplica los efectos del objeto al jugador y lo elimina del juego.
        """
        objeto.aplicar_efecto(self.jugador)
        objeto.kill()

    def generar_enemigos(self):
        """
        Genera nuevos enemigos de forma aleatoria.
        """
        if not self.pausado and pygame.time.get_ticks() > self.tiempo_proximo_enemigo:
            if self.jugador.vidas > 0:  # Solo generar enemigos si el jugador está vivo
                self.enemigos.append(self.generar_enemigo())
                self.tiempo_proximo_enemigo = pygame.time.get_ticks() + random.randint(self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION)

    def actualizar_enemigos(self):
        """
        Actualiza la posición y comportamiento de los enemigos.
        """
        for enemigo in self.enemigos:
            if enemigo is not None:  # Verificar si enemigo no es None
                enemigo.movimiento_enemigo()

                if self.jugador.rect.colliderect(enemigo.rect):
                    self.colision_jugador_enemigo(enemigo)

                if isinstance(enemigo, EnemigoTipo2):
                    nueva_bala_enemigo = enemigo.disparo_enemigo()
                    if nueva_bala_enemigo:
                        self.balas_enemigo.append(nueva_bala_enemigo)
                if isinstance(enemigo, EnemigoTipo3):
                    nueva_bala_enemigo = enemigo.disparo_enemigo()
                    if nueva_bala_enemigo:
                        self.balas_enemigo.append(nueva_bala_enemigo)

    def colision_jugador_enemigo(self, enemigo):
        """
        Maneja la colisión entre el jugador y un enemigo.

        Args:
            enemigo: Enemigo colisionado.
        """
        enemigo_golpeado = (enemigo.rect, False)
        if enemigo_golpeado not in self.enemigos_golpeados:
            self.jugador.reducir_salud(1)
            self.EFECTO_GOLPE.play()
            self.enemigos_golpeados.append(enemigo_golpeado)
            self.manejar_impacto_jugador()
        enemigo.salud -= 1
        if enemigo.salud <= 0:
            explosion = Explosion(enemigo.rect.center, self.explosion_images)
            self.all_sprites.add(explosion)  # Añadir la explosión al grupo de entidades
            self.enemigos.remove(enemigo)

    def mover_fondo(self):
        """
        Mueve el fondo del juego.
        """
        self.pos_y_fondo1 += 0.5
        self.pos_y_fondo2 += 0.5
        if self.pos_y_fondo1 >= self.pantalla_alto:
            self.pos_y_fondo1 = -self.pantalla_alto
        if self.pos_y_fondo2 >= self.pantalla_alto:
            self.pos_y_fondo2 = -self.pantalla_alto

    def mostrar_game_over(self):
        """
        Muestra el mensaje de "Game Over".
        """
        self.all_sprites.empty()  # Eliminar todas las entidades
        font_game_over = pygame.font.SysFont(None, 72)  # Fuente y tamaño del texto
        texto_game_over = font_game_over.render("Game Over", True, (255, 255, 255))  # Texto, antialiasing y color
        texto_rect = texto_game_over.get_rect(center=(self.pantalla_ancho // 2, self.pantalla_alto // 2 - 150))  # Centrar el texto un poco más arriba
        self.pantalla.blit(texto_game_over, texto_rect)  # Mostrar el texto "Game Over"

    def juego_terminado(self):
        """
        Muestra el mensaje de "Game Over" y la opción de "Reintentar".
        """
        # Detener música de fondo
        resource_manager.stop_music("skyfire_theme")

        # Iniciar música Game Over de fondo si aún no se ha iniciado
        if not resource_manager.is_music_playing("defeated_tune"):
            resource_manager.play_music("defeated_tune", loops=-1)
            resource_manager.set_music_volume("defeated_tune", self.volumen_musica)

        # Cargar la fuente para el botón "Reintentar"
        font = pygame.font.Font(None, 36)

        # Crear el botón "Reintentar"
        boton_reintentar = Boton("Reintentar", (255, 0, 0, 128), (255, 255, 255), 200, 400, 200, 50,
                                 radio_borde=10)

        # Crear el botón "Salir"
        boton_salir = Boton("Salir", (255, 0, 255, 128), (255, 255, 255), 200, 470, 200, 50,
                            radio_borde=10)

        # Dibujar el botón en la pantalla
        boton_reintentar.dibujar(self.pantalla, font)
        boton_salir.dibujar(self.pantalla, font)

        pygame.display.flip()  # Actualizar la pantalla

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    return False
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_reintentar.clic_en_boton(evento.pos):
                        self.reiniciar_juego()  # Reiniciar el juego si el jugador hace clic en "Reintentar"
                        return True
                    elif boton_salir.clic_en_boton(evento.pos):
                        # Volver al menú principal si el jugador hace clic en "Salir"
                        self.mostrar_menu_principal()
                        return True

    def mostrar_menu_principal(self):
        """
        Muestra el menú principal del juego.
        """
        # Detener música de Game Over
        resource_manager.stop_music("defeated_tune")

        # Iniciar música de fondo del menú si aún no se ha iniciado
        if not resource_manager.is_music_playing("skyfire_theme"):
            resource_manager.play_music("skyfire_theme", loops=-1)
            resource_manager.set_music_volume("skyfire_theme", self.volumen_musica)

        from galactic_guardian.juego.menu import mostrar_menu
        mostrar_menu(self.pantalla)

    def reiniciar_juego(self):
        """
        Reinicia el juego.
        """
        # Reiniciar todos los valores del juego a sus estados iniciales
        self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)
        self.enemigos = []
        self.balas = []
        self.balas_enemigo = []
        self.enemigos_golpeados = []
        self.tiempo_proximo_enemigo = 0
        self.inicio_juego = pygame.time.get_ticks()
        # Detener música Game Over de fondo
        resource_manager.stop_music("defeated_tune")
        if not resource_manager.is_music_playing("skyfire_theme"):
            resource_manager.play_music("skyfire_theme", loops=-1)
            resource_manager.set_music_volume("skyfire_theme", self.volumen_musica)

        # Continuar ejecutando el juego
        self.ejecutar()

    def dibujar_barra_salud(self):
        """
        Dibuja la barra de salud del jugador en la pantalla del juego.
        """
        # Calcular la posición inicial de la barra de salud
        barra_x = self.jugador.rect.centerx - 25  # Centrar el rectángulo en relación con la barra de salud
        barra_y = self.jugador.rect.bottom + 10  # Ajustar la posición vertical para que esté debajo de la nave

        # Dibujar las barras verticales de la barra de salud
        for i in range(self.jugador.salud_maxima):
            if i < self.jugador.salud:  # Las barras de salud activas serán verdes
                color = (0, 255, 0)
            else:  # Las barras de salud inactivas serán grises
                color = (150, 150, 150)

            # Calcular la posición y el tamaño de cada barra de salud
            barra_salud_rect = pygame.Rect(barra_x + i * 10, barra_y, 8, 10)
            pygame.draw.rect(self.pantalla, color, barra_salud_rect)

        # Dibujar el rectángulo blanco alrededor de la barra de salud
        rectangulo_salud = pygame.Rect(barra_x, barra_y, self.jugador.salud_maxima * 10, 10)  # El ancho total de la barra de salud
        pygame.draw.rect(self.pantalla, (255, 255, 255), rectangulo_salud, 1)  # Grosor del borde: 1

    def dibujar(self):
        """
        Dibuja en la pantalla.
        """
        # Blitgear la imagen de fondo en la pantalla
        self.pantalla.blit(self.fondo_imagen1, (0, self.pos_y_fondo1))
        self.pantalla.blit(self.fondo_imagen2, (0, self.pos_y_fondo2))

        if self.jugador.vidas <= 0:
            self.mostrar_game_over()
            return  # Salir de la función si el juego ha terminado

        # Dibujar todas las entidades en el grupo de entidades
        self.all_sprites.draw(self.pantalla)

        for enemigo in self.enemigos:
            if enemigo is not None:  # Verifica si enemigo no es None
                if self.pausado:
                    enemigo_image_gris = enemigo.image.copy()
                    enemigo_image_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
                    self.pantalla.blit(enemigo_image_gris, enemigo.rect)
                else:
                    self.pantalla.blit(enemigo.image, enemigo.rect)  # Dibujar enemigos

        for bala in self.balas:
            if self.pausado:
                # Convertir la imagen de la bala a escala de grises si el juego está pausado
                bala_image_gris = bala.image.copy()
                bala_image_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
                self.pantalla.blit(bala_image_gris, bala.rect)
            else:
                self.pantalla.blit(bala.image, bala.rect)  # Dibujar balas

        for bala_enemiga in self.balas_enemigo:
            if self.pausado:
                # Convertir la imagen de la bala a escala de grises si el juego está pausado
                bala_image_gris = bala_enemiga.image.copy()
                bala_image_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
                self.pantalla.blit(bala_image_gris, bala_enemiga.rect)
            else:
                self.pantalla.blit(bala_enemiga.image, bala_enemiga.rect)  # Dibujar balas enemigas

        if self.pausado:
            # Dibujar jugador con tono grisáceo si el juego está pausado
            jugador_image_gris = self.jugador.image.copy()
            jugador_image_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
            self.pantalla.blit(jugador_image_gris, self.jugador.rect)

            # Dibujar rectángulo semitransparente sobre toda la pantalla
            pantalla_sombreada = pygame.Surface((self.pantalla_ancho, self.pantalla_alto))
            pantalla_sombreada.set_alpha(128)  # Establecer transparencia (0: completamente transparente, 255: completamente opaco)
            pantalla_sombreada.fill((128, 128, 128))  # Rellenar con color negro
            self.pantalla.blit(pantalla_sombreada, (0, 0))

            # Mostrar texto de juego pausado en el centro de la pantalla
            font = pygame.font.SysFont(None, 36)  # Fuente y tamaño del texto
            texto = font.render("Juego Pausado", True, (255, 255, 255))  # Texto, antialiasing y color
            texto_rect = texto.get_rect(center=(self.pantalla_ancho // 2, self.pantalla_alto // 2))  # Centrar el texto
            self.pantalla.blit(texto, texto_rect)

            # Mostrar texto de vidas
            color_texto_vidas = (128, 128, 128)  # Color gris si el juego está pausado
        else:
            self.pantalla.blit(self.jugador.image, self.jugador.rect)
            # Mostrar texto de vidas
            color_texto_vidas = (255, 255, 255)  # Color blanco si el juego está en curso

        # Mostrar Vidas en la esquina superior izquierda
        font = pygame.font.SysFont(None, 36)  # Fuente y tamaño del texto
        texto_vidas = font.render(f"Vidas: {self.jugador.vidas}", True, color_texto_vidas)  # Texto, antialiasing y color
        self.pantalla.blit(texto_vidas, (10, 10))  # Mostrar el texto en la posición (10, 10)

        self.dibujar_barra_salud()

        # Mostrar FPS en la esquina superior derecha
        font_fps = pygame.font.SysFont(None, 24)  # Fuente y tamaño del texto
        texto_fps = font_fps.render(f"FPS: {int(self.reloj.get_fps())}", True, (255, 255, 255))  # Texto, antialiasing y color
        self.pantalla.blit(texto_fps, (self.pantalla_ancho - texto_fps.get_width() - 10, 10))  # Mostrar el texto en la esquina superior derecha

        pygame.display.flip()  # Actualiza la pantalla

    def ejecutar(self):
        """
        Ejecuta el juego.
        """
        ejecutando = True

        while ejecutando:
            ejecutando = self.manejar_eventos()

            # Si el juego está pausado, solo dibujar la pantalla y continuar al siguiente ciclo
            if self.pausado:
                self.dibujar()
                self.reloj.tick(60)
                continue

            # Actualizar el juego solo si el juego no está pausado
            self.actualizar()
            self.all_sprites.update()  # Actualizar todas las entidades
            self.dibujar()
            self.reloj.tick(60)

        pygame.quit()