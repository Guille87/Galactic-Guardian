import random

import pygame
import pygame.freetype

from entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from entidades.item import Item
from entidades.jugador import Jugador
from juego.audio_manager import AudioManager
from juego.collision_manager import CollisionManager
from juego.effect_manager import EffectManager
from juego.input_handler import InputHandler
from juego.render_manager import RenderManager
from juego.ui_manager import UIManager
from juego.wave_manager import WaveManager


class Juego:
    def __init__(self, pantalla, volumen_musica, volumen_efectos, clasificacion, resource_manager):
        # Inicialización de variables
        self.volumen_musica = volumen_musica
        self.volumen_efectos = volumen_efectos
        self.pantalla = pantalla
        self.pantalla_ancho = pantalla.get_width()
        self.pantalla_alto = pantalla.get_height()
        self.puntuacion = 0
        self.nivel = 1
        self.jefe = None
        self.jefe_derrotado = False
        self.enemigos_activos = 0
        self.enemigos_eliminados = 0
        self.max_enemigos_para_objeto = 10
        self.tiempo_espera_jefe = 5000
        self.disparando = False
        self.pausado = False
        self.tiempo_pausa = 0
        self.tiempo_proximo_enemigo = 0
        self.tiempo_entre_enemigos = 0
        self.MIN_TIEMPO_GENERACION = 800
        self.MAX_TIEMPO_GENERACION = 1000
        self.rm = resource_manager
        self.estado_game_over = False

        self.audio_manager = AudioManager(self.rm, volumen_musica, volumen_efectos)
        self.effect_manager = EffectManager(self)
        self.ui_manager = UIManager(self)
        self.render_manager = RenderManager(self)

        self.wave_manager = WaveManager(resource_manager, self.audio_manager, self.pantalla_ancho, self.pantalla_alto)

        self.input_handler = InputHandler(self)
        self.collision_manager = CollisionManager(self)

        # Iniciar música inicial
        self.audio_manager.reproducir_musica("rain_of_lasers")

        self.clasificacion = clasificacion

        # Inicialización de recursos
        self.all_sprites = pygame.sprite.Group()
        # Obtener imágenes
        self.ruta_imagen_jugador = resource_manager.get_image_path("jugador")
        self.fondo_imagen1 = resource_manager.get_image("imagen_fondo1")
        self.fondo_imagen2 = resource_manager.get_image("imagen_fondo2")
        self.explosion_images = [resource_manager.get_image(f"explosion_{i}") for i in range(1, 12)]

        # Inicialización de botones
        self.boton_opciones = None
        self.boton_salir = None
        # Inicialización de jugadores, enemigos, balas, etc.
        self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)

        self.enemigos = []
        self.balas = []
        self.balas_enemigo = []
        # Inicialización de tiempo
        self.inicio_juego = pygame.time.get_ticks()
        # Inicialización de posiciones de fondo
        self.pos_y_fondo1 = 0
        self.pos_y_fondo2 = -self.pantalla_alto
        # Inicialización de diccionario de enemigos golpeados
        self.enemigos_golpeados = {}
        # Configuración del reloj
        self.reloj = pygame.time.Clock()

    def generar_enemigo(self):
        """
        Genera un nuevo enemigo en una posición aleatoria en la parte superior de la pantalla.
        """
        tiempo_transcurrido = pygame.time.get_ticks() - self.inicio_juego - self.tiempo_entre_enemigos

        # Pedimos al manager qué debemos generar
        tipo_enemigo, ruta_imagen, es_jefe = self.wave_manager.obtener_config_enemigo(tiempo_transcurrido)

        if not tipo_enemigo:
            return None

        # Coordenadas básicas
        x_enemigo = random.randint(50, self.pantalla_ancho - 100)
        y_enemigo = -50

        # Instanciar según el tipo
        if es_jefe:
            x_enemigo = (self.pantalla_ancho - 200) // 2
            y_enemigo = -150  # Genera el enemigo arriba de la pantalla

            nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho,
                                         self.pantalla_alto, self.balas_enemigo, self.jugador, self.nivel)
            self.jefe = nuevo_enemigo

        elif tipo_enemigo == EnemigoTipo1:
            nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.nivel)
        else:  # Tipos 2 y 3
            nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho,
                                         self.balas_enemigo, self.jugador, self.nivel)

        self.enemigos_activos += 1
        return nuevo_enemigo

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
        self.tiempo_entre_enemigos += tiempo_pausado
        self.jugador.tiempo_invulnerable += tiempo_pausado  # Actualizar el tiempo de invulnerabilidad del jugador
        for enemigo in self.enemigos:
            if isinstance(enemigo, EnemigoTipo2) or isinstance(enemigo, EnemigoTipo3):
                enemigo.tiempo_ultimo_ataque += tiempo_pausado
            if isinstance(enemigo, Jefe):
                enemigo.tiempo_ultimo_disparo += tiempo_pausado
                enemigo.tiempo_ultimo_disparo_rapido += tiempo_pausado

    def _disparar(self):
        """
        Maneja la lógica de disparo del jugador.
        """
        # Llama a la función disparar del jugador para obtener las nuevas balas
        nuevas_balas = self.jugador.disparar()

        primera_bala = True  # Bandera para verificar si ya se disparó la primera bala
        # Verifica si hay nuevas balas y las agrega a la lista de balas
        for bala in nuevas_balas:
            if bala:
                self.balas.append(bala)
                if primera_bala:  # Reproduce el sonido solo para la primera bala
                    self.audio_manager.reproducir_efecto("disparo")
                    primera_bala = False  # Cambia la bandera después del primer disparo

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

        self.actualizar_balas()

        self.collision_manager.actualizar()

        self.eliminar_elementos_fuera_de_pantalla()
        self.mover_fondo()
        self.jugador.update()

    def eliminar_elementos_fuera_de_pantalla(self):
        """
        Elimina los elementos (balas, enemigos y objetos) que están fuera de la pantalla.
        """
        enemigos_salidos = []  # Lista para almacenar los enemigos que han salido fuera de la pantalla
        for enemigo in self.enemigos:
            if enemigo and self.fuera_de_pantalla(enemigo.rect):
                enemigos_salidos.append(enemigo)

        # Reducir en 1 el contador de enemigos_activos por cada enemigo que ha salido de la pantalla
        self.enemigos_activos -= len(enemigos_salidos)

        self.balas = [bala for bala in self.balas if not (bala is not None and self.fuera_de_pantalla(bala.rect))]
        self.enemigos = [enemigo for enemigo in self.enemigos if
                         not (enemigo is not None and self.fuera_de_pantalla(enemigo.rect))]
        self.balas_enemigo = [bala_enemiga for bala_enemiga in self.balas_enemigo if
                              not (bala_enemiga is not None and self.fuera_de_pantalla(bala_enemiga.rect))]
        self.all_sprites = pygame.sprite.Group(
            [item for item in self.all_sprites if not (item is not None and self.fuera_de_pantalla(item.rect))])

    def fuera_de_pantalla(self, rect):
        """
        Verifica si un rectángulo está fuera de la pantalla.

        Args:
            rect: Rectángulo a verificar.

        Returns:
            bool: True si el rectángulo está fuera de la pantalla, False en caso contrario.
        """
        return rect.bottom < 0 or rect.top > self.pantalla_alto or rect.right < 0 or rect.left > self.pantalla_ancho

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
                self.effect_manager.crear_destello_recibir_danio()
            else:
                self.effect_manager.crear_explosion(self.jugador.rect.center)
                self.reposicionar_jugador()
                self.reducir_vidas_y_aumentar_salud()

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
        self.effect_manager.crear_destello_invulnerabilidad()

        if self.jugador.vidas > 0:
            self.jugador.aumentar_salud(self.jugador.salud_maxima)

    def actualizar_jugador(self):
        """
        Actualiza la posición del jugador en función de las teclas presionadas.
        """
        teclas_presionadas = pygame.key.get_pressed()
        self.jugador.mover(teclas_presionadas, self.pantalla)
        self.detectar_colisiones_objetos()

    def actualizar_balas(self):
        """Mueve las balas y elimina las que se salen de la pantalla."""
        for bala in self.balas[:]:
            bala.bala_jugador()
            if self.fuera_de_pantalla(bala.rect):
                self.balas.remove(bala)

        for bala_e in self.balas_enemigo[:]:
            bala_e.bala_enemigo()
            if self.fuera_de_pantalla(bala_e.rect):
                self.balas_enemigo.remove(bala_e)

    def detectar_colisiones_objetos(self):
        """
        Detecta y maneja las colisiones entre el jugador y los objetos.
        """
        for objeto in self.all_sprites:
            if isinstance(objeto, Item) and self.jugador.rect.colliderect(objeto.rect):
                self.audio_manager.reproducir_efecto("item")
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
                nuevo_enemigo = self.generar_enemigo()
                if nuevo_enemigo is not None:  # Solo añadir si realmente se creó un enemigo
                    self.enemigos.append(nuevo_enemigo)
                self.tiempo_proximo_enemigo = pygame.time.get_ticks() + random.randint(self.MIN_TIEMPO_GENERACION,
                                                                                       self.MAX_TIEMPO_GENERACION)

    def actualizar_enemigos(self):
        """
        Actualiza la posición y comportamiento de los enemigos.
        """
        for enemigo in self.enemigos:
            if enemigo is not None:  # Verificar si enemigo no es None
                enemigo.movimiento_enemigo()
                enemigo.update()
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
                if isinstance(enemigo, Jefe):
                    nueva_bala_enemigo1 = enemigo.disparo_jefe()
                    nueva_bala_enemigo2 = enemigo.disparo_rapido()
                    if nueva_bala_enemigo1:
                        self.balas_enemigo.append(nueva_bala_enemigo1)
                    if nueva_bala_enemigo2:
                        self.balas_enemigo.append(nueva_bala_enemigo2)

    def colision_jugador_enemigo(self, enemigo):
        """
        Maneja la colisión entre el jugador y un enemigo.

        Args:
            enemigo: Enemigo colisionado.
        """
        # Verificar si ya ha pasado suficiente tiempo desde la última colisión con este enemigo
        tiempo_actual = pygame.time.get_ticks()
        tiempo_ultima_colision = self.enemigos_golpeados.get(enemigo, 0)
        if tiempo_actual - tiempo_ultima_colision >= 2000:  # 2000 milisegundos = 2 segundos
            self.jugador.reducir_salud(1)
            self.audio_manager.reproducir_efecto("golpe")
            self.enemigos_golpeados[enemigo] = tiempo_actual  # Registrar el tiempo de la última colisión
            self.manejar_impacto_jugador()
            enemigo.salud -= 1
        if enemigo.salud <= 0:
            self.effect_manager.crear_explosion(enemigo.rect.center)
            self.enemigos.remove(enemigo)
            # Decrementa el contador de enemigos en pantalla
            self.enemigos_activos -= 1
            # Incrementa el contador de enemigos eliminados
            self.enemigos_eliminados += 1

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
        self.all_sprites.empty()  # Eliminar todos los sprites
        font_game_over = pygame.font.SysFont(None, 72)  # Fuente y tamaño del texto
        texto_game_over = font_game_over.render("Game Over", True, (255, 255, 255))  # Texto, antialiasing y color
        texto_rect = texto_game_over.get_rect(
            center=(self.pantalla_ancho // 2, self.pantalla_alto // 2 - 150))  # Centrar el texto un poco más arriba
        self.pantalla.blit(texto_game_over, texto_rect)  # Mostrar el texto "Game Over"

    def juego_terminado(self):
        """
        Muestra el mensaje de "Game Over" y las opciones de "Reintentar" y "Salir".
        """
        self.pausado = True  # Usamos el estado de pausa para detener la actualización
        # Detener música de fondo
        self.audio_manager.detener_toda_la_musica()
        # Iniciar música Game Over de fondo
        self.audio_manager.reproducir_musica("defeated_tune")

        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()
        if len(puntuaciones_top) < 10 or self.puntuacion > puntuaciones_top[-1][1]:
            # La puntuación del jugador está entre las 10 mejores o es superior a la última de las 10 mejores
            nombre_jugador = self.mostrar_cuadro_dialogo("Introduce tu nombre: ")
            self.clasificacion.agregar_puntuacion(nombre_jugador, self.puntuacion)

        self.estado_game_over = True

    def mostrar_cuadro_dialogo(self, mensaje):
        font_dialogo = pygame.freetype.SysFont(None, 24)
        entrada = ""
        ingresando = True
        while ingresando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    import sys
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        ingresando = False
                    elif event.key == pygame.K_BACKSPACE:
                        entrada = entrada[:-1]
                    else:
                        entrada += event.unicode

            self.pantalla.blit(self.fondo_imagen1, (0, 0))
            texto_surface, _ = font_dialogo.render(mensaje + entrada, (255, 255, 255))
            self.pantalla.blit(texto_surface, ((self.pantalla.get_width() - texto_surface.get_width()) // 2,
                                               (self.pantalla.get_height() - texto_surface.get_height()) // 2))
            pygame.display.flip()

        return entrada

    def mostrar_menu_principal(self):
        """
        Muestra el menú principal del juego.
        """
        # Detener música
        self.audio_manager.detener_toda_la_musica()

        # Iniciar música de fondo del menú si aún no se ha iniciado
        self.audio_manager.reproducir_musica("skyfire_theme")

        from juego.menu import MenuManager
        menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)
        menu.ejecutar()

        pygame.quit()
        import sys
        sys.exit()

    def mostrar_opciones_juego(self):
        """
        Muestra el menú principal del juego.
        """
        from juego.menu import MenuManager
        menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)

        menu.mostrar_solo_opciones()

    def reiniciar_juego(self):
        """
        Reinicia el juego.
        """
        if self.jefe_derrotado:
            self.nivel += 1
            self.jefe_derrotado = False
            self.MIN_TIEMPO_GENERACION -= 200
            self.MAX_TIEMPO_GENERACION -= 200
            if self.MIN_TIEMPO_GENERACION <= 200:
                self.MIN_TIEMPO_GENERACION = 200
            if self.MAX_TIEMPO_GENERACION <= 200:
                self.MAX_TIEMPO_GENERACION = 200
        else:
            self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)
            self.MIN_TIEMPO_GENERACION = 800
            self.MAX_TIEMPO_GENERACION = 1000
            self.puntuacion = 0
            self.balas = []
            self.balas_enemigo = []

        # Reiniciar todos los valores del juego a sus estados iniciales
        self.enemigos = []
        self.enemigos_golpeados = {}
        self.tiempo_proximo_enemigo = 0
        self.inicio_juego = pygame.time.get_ticks()
        self.enemigos_activos = 0
        self.tiempo_entre_enemigos = 0
        self.pausado = False
        self.estado_game_over = False

        # Resetear el WaveManager para que el jefe pueda volver a salir en el siguiente nivel
        self.wave_manager.jefe_generado = False
        self.wave_manager.tiempo_inicio_espera_jefe = 0

        # Detenemos la música
        self.audio_manager.detener_toda_la_musica()
        # Aseguramos que suene la música principal
        self.audio_manager.reproducir_musica("rain_of_lasers")

    def dibujar(self):
        """Lógica de dibujo delegada al RenderManager."""
        self.render_manager.renderizar_todo()

    def ejecutar(self):
        """
        Ejecuta el juego.
        """
        ejecutando = True

        while ejecutando:
            pygame.display.set_caption("Galactic Guardian")

            # Si manejar_eventos() devuelve False, salimos del bucle
            if not self.input_handler.manejar_eventos():
                ejecutando = False
                continue

            # Si el juego está pausado, solo dibujar la pantalla y continuar al siguiente ciclo
            if self.pausado:
                self.dibujar()
                self.reloj.tick(60)
                continue

            # Actualizar el juego solo si el juego no está pausado
            self.actualizar()
            self.all_sprites.update()  # Actualizar todos los sprites
            self.dibujar()
            self.reloj.tick(60)

        self.audio_manager.detener_musica("rain_of_lasers")
