import random

import pygame
import pygame.freetype

from entidades.enemigo import EnemigoTipo2, EnemigoTipo3, Jefe
from entidades.jugador import Jugador
from juego.audio_manager import AudioManager
from juego.background_manager import ScrollingBackground
from juego.collision_manager import CollisionManager
from juego.effect_manager import EffectManager
from juego.entity_manager import EntityManager
from juego.input_handler import InputHandler
from juego.render_manager import RenderManager
from juego.ui_manager import UIManager
from juego.wave_manager import WaveManager


class Juego:
    def __init__(self, pantalla, volumen_musica, volumen_efectos, clasificacion, resource_manager):
        # 1. Configuración básica y Hardware
        self.rm = resource_manager
        self.pantalla = pantalla
        self.pantalla_ancho = pantalla.get_width()
        self.pantalla_alto = pantalla.get_height()
        self.reloj = pygame.time.Clock()

        # 2. Estado de la Partida
        self.puntuacion = 0
        self.nivel = 1
        self.pausado = False
        self.estado_game_over = False
        self.pidiendo_nombre = False
        self.nombre_entrada = ""
        self.jefe_derrotado = False
        self.disparando = False
        self.all_sprites = pygame.sprite.Group()
        self.enemigos_activos = 0
        self.enemigos_eliminados = 0

        # Parámetros de dificultad
        self.MIN_TIEMPO_GENERACION = 800
        self.MAX_TIEMPO_GENERACION = 1000

        # 3. Managers (El "Cerebro" distribuido)
        self.audio_manager = AudioManager(self.rm, volumen_musica, volumen_efectos)
        self.entity_manager = EntityManager(self)
        self.effect_manager = EffectManager(self)
        self.ui_manager = UIManager(self)
        self.render_manager = RenderManager(self)
        self.wave_manager = WaveManager(resource_manager, self.audio_manager, self.pantalla_ancho, self.pantalla_alto)
        self.input_handler = InputHandler(self)
        self.collision_manager = CollisionManager(self)

        # 4. Entidades Principales
        self.background = ScrollingBackground(
            self.rm.get_image("imagen_fondo1"),
            self.rm.get_image("imagen_fondo2"),
            self.pantalla_alto
        )
        self.jugador = Jugador(
            self.rm.get_image_path("jugador"),
            self.pantalla_ancho,
            self.pantalla_alto,
            self.all_sprites
        )

        # 5. Control de Tiempos y Flujo
        self.inicio_juego = pygame.time.get_ticks()
        self.tiempo_proximo_enemigo = 0
        self.tiempo_pausa = 0
        self.tiempo_entre_enemigos = 0
        self.enemigos_golpeados = {}

        # 6. Inicialización de Estado de Juego
        self.audio_manager.reproducir_musica("rain_of_lasers")
        self.clasificacion = clasificacion

        self.jefe = None

        # Inicialización de botones
        self.boton_opciones = None
        self.boton_salir = None

    def pausar_juego(self):
        """Pausa el juego y guarda el tiempo en que se pausó."""
        self.pausado = True
        self.tiempo_pausa = pygame.time.get_ticks()

    def reanudar_juego(self):
        """Reanuda el juego y ajusta los tiempos para sincronizarlos con el tiempo pausado."""
        self.pausado = False
        tiempo_actual = pygame.time.get_ticks()
        tiempo_pausado = tiempo_actual - self.tiempo_pausa

        self.tiempo_proximo_enemigo += tiempo_pausado
        self.tiempo_entre_enemigos += tiempo_pausado
        self.jugador.tiempo_invulnerable += tiempo_pausado  # Actualizar el tiempo de invulnerabilidad del jugador

        for enemigo in self.entity_manager.enemigos:
            if isinstance(enemigo, (EnemigoTipo2, EnemigoTipo3)):
                enemigo.tiempo_ultimo_ataque += tiempo_pausado
            if isinstance(enemigo, Jefe):
                enemigo.tiempo_ultimo_disparo += tiempo_pausado
                enemigo.tiempo_ultimo_disparo_rapido += tiempo_pausado

    def reiniciar_juego(self):
        """Restablece el estado para una nueva partida o nivel."""
        if self.jefe_derrotado:
            self.nivel += 1
            self.jefe_derrotado = False

            # Aumentar dificultad
            self.MIN_TIEMPO_GENERACION = max(200, self.MIN_TIEMPO_GENERACION - 200)
            self.MAX_TIEMPO_GENERACION = max(200, self.MAX_TIEMPO_GENERACION - 200)
        else:
            # Partida desde cero
            self.jugador = Jugador(self.rm.get_image_path("jugador"), self.pantalla_ancho, self.pantalla_alto, self.all_sprites)
            self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION = 800, 1000
            self.puntuacion = 0

        # Reiniciar todos los valores del juego a sus estados iniciales
        self.entity_manager.vaciar_todo()
        self.all_sprites.empty()
        self.all_sprites.add(self.jugador)
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

    def manejar_impacto_jugador(self):
        """Procesa el daño visual y lógico del jugador"""
        if self.jugador.vidas <= 0: return

        if self.jugador.salud > 0:
            self.effect_manager.crear_destello_recibir_danio()
        else:
            self.effect_manager.crear_explosion(self.jugador.rect.center)
            self._procesar_muerte_jugador()

    def _procesar_muerte_jugador(self):
        """Lógica interna de pérdida de vida y reaparición."""
        self.jugador.rect.centerx = self.pantalla_ancho // 2
        self.jugador.rect.bottom = self.pantalla_alto - 10
        self.jugador.reducir_vidas(1)

        if self.jugador.vidas > 0:
            self.jugador.invulnerable = True
            self.jugador.tiempo_invulnerable = pygame.time.get_ticks() + 3000
            self.jugador.curar(self.jugador.salud_maxima)
            self.effect_manager.crear_destello_invulnerabilidad()

    def disparar(self):
        """Extrae las balas del jugador y las registra en el manager de entidades."""
        # 1. Obtenemos el tiempo actual
        ahora = pygame.time.get_ticks()

        # 2. Obtenemos la ruta de la imagen desde el RM que ya tiene Juego
        ruta_bala = self.rm.get_image_path("bala_jugador1")

        # Llama a la función disparar del jugador para obtener las nuevas balas
        nuevas_balas = self.jugador.disparar(ahora, ruta_bala)

        # Verifica si hay nuevas balas y las agrega a la lista de balas
        for i, bala in enumerate(nuevas_balas):
            self.entity_manager.agregar_bala_jugador(bala)
            if i == 0:  # Reproduce el sonido solo para la primera bala
                self.audio_manager.reproducir_efecto("disparo")

    def actualizar(self):
        """Actualiza el estado del juego."""
        if self.jugador.vidas <= 0:
            self.juego_terminado()
            return

        # 1. Entradas y Generación
        teclas = pygame.key.get_pressed()
        self.jugador.mover(teclas, self.pantalla)
        self._gestionar_generacion_enemigos()

        # 2. Física y Colisiones
        self.entity_manager.actualizar()
        self.collision_manager.actualizar()

        # 3. Cosmética
        self.background.update()
        self.jugador.update()

    def _gestionar_generacion_enemigos(self):
        """Maneja el timing para spawnear enemigos mediante el WaveManager."""
        ahora = pygame.time.get_ticks()
        if ahora > self.tiempo_proximo_enemigo:
            nuevo = self.wave_manager.spawn_enemigo(
                ahora - self.inicio_juego, self.entity_manager.balas_enemigo, self.jugador, self.nivel
            )
            if nuevo:
                self.entity_manager.agregar_enemigo(nuevo)

                if isinstance(nuevo, Jefe):
                    self.jefe = nuevo

            self.tiempo_proximo_enemigo = ahora + random.randint(800, 1000)

    def juego_terminado(self):
        """Muestra el mensaje de "Game Over" y las opciones de "Reintentar" y "Salir"."""
        self.pausado = True  # Usamos el estado de pausa para detener la actualización
        # Detener música de fondo
        self.audio_manager.detener_toda_la_musica()
        # Iniciar música Game Over de fondo
        self.audio_manager.reproducir_musica("defeated_tune")

        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()
        if len(puntuaciones_top) < 10 or self.puntuacion > puntuaciones_top[-1][1]:
            # La puntuación del jugador está entre las 10 mejores o es superior a la última de las 10 mejores
            self.pidiendo_nombre = True
            self.nombre_entrada = ""
        else:
            self.estado_game_over = True

    def mostrar_menu_principal(self):
        """Muestra el menú principal del juego."""
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
        """Muestra el menú principal del juego."""
        from juego.menu import MenuManager
        menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)

        menu.mostrar_solo_opciones()

    def dibujar(self):
        """Lógica de dibujo delegada al RenderManager."""
        self.render_manager.renderizar_todo()

    def ejecutar(self):
        """Ejecuta el juego."""
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
