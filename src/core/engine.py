import random
import weakref

import pygame
import pygame.freetype

from src.core import settings
from src.entities.enemies import Jefe
from src.entities.player import Jugador
from src.entities.bullet import Bala
from src.entities.items import Item
from src.visual.background import ScrollingBackground
from src.managers.collision import CollisionManager
from src.managers.effects import EffectManager
from src.managers.entities import EntityManager
from src.core.input import InputHandler
from src.managers.render import RenderManager
from src.ui.hud import UIManager
from src.managers.waves import WaveManager


class Juego:
    def __init__(self, pantalla, audio_manager, clasificacion, resource_manager):
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
        self.pendiente_reinicio = False  # Transición diferida (ver actualizar())
        self.debug_hitboxes = False      # F1: dibuja los círculos de colisión

        # Control de la máquina de estados de alto nivel
        self.ejecutando = True
        self.resultado = "MENU"  # "MENU" | "SALIR"
        self.enemigos_eliminados = 0  # contador de "piedad" para el loot

        # Parámetros de dificultad
        self.MIN_TIEMPO_GENERACION = settings.GEN_MIN_INICIAL
        self.MAX_TIEMPO_GENERACION = settings.GEN_MAX_INICIAL

        # 3. Entidades principales y estado compartido por los managers
        self.background = ScrollingBackground(
            self.rm.get_image("imagen_fondo1"),
            self.rm.get_image("imagen_fondo2"),
            self.pantalla_alto
        )
        self.jugador = Jugador(
            self.rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]),
            self.pantalla_ancho,
            self.pantalla_alto,
        )
        # {enemigo: ts del último contacto}. WeakKeyDictionary: si el enemigo se
        # destruye, su entrada desaparece sola (además de purgarse al morir/salir).
        # Se vacía con .clear() al reiniciar, nunca se reasigna: los managers
        # guardan la referencia.
        self.enemigos_golpeados = weakref.WeakKeyDictionary()

        # 4. Managers (El "Cerebro" distribuido)
        self.audio_manager = audio_manager  # Compartido con el menú (inyectado)
        self.entity_manager = EntityManager(
            self.rm, self.pantalla_ancho, self.pantalla_alto, self.enemigos_golpeados
        )
        self.effect_manager = EffectManager(self.rm, self.entity_manager, self.jugador)
        self.ui_manager = UIManager(self)
        self.render_manager = RenderManager(self)
        self.wave_manager = WaveManager(resource_manager, self.audio_manager, self.pantalla_ancho, self.pantalla_alto)
        self.input_handler = InputHandler(self)
        self.collision_manager = CollisionManager(
            self.entity_manager, self.jugador, self.effect_manager,
            self.audio_manager, self.enemigos_golpeados, self,
        )

        # 5. Control de Tiempos y Flujo
        # Reloj de juego en ms. Solo avanza dentro de actualizar(dt), así que en
        # pausa / Game Over se congela solo: NINGÚN temporizador necesita ajuste
        # manual al reanudar. Toda la lógica del juego lo lee en vez de get_ticks().
        self.tiempo_juego = 0.0
        self.inicio_juego = 0.0            # "tiempo 0" del nivel actual
        self.tiempo_proximo_enemigo = 0

        # 6. Inicialización de Estado de Juego
        self.audio_manager.reproducir_musica("rain_of_lasers")
        self.clasificacion = clasificacion

        self.jefe = None

        # Botones de overlays (los crea RenderManager una sola vez y los cachea)
        self.boton_opciones = None
        self.boton_salir = None
        self.boton_reintentar = None
        self.boton_salir_post = None

    def pausar_juego(self):
        """Pausa el juego. `tiempo_juego` deja de avanzar solo (no se llama a
        actualizar mientras `pausado`), así que no hay nada más que hacer."""
        self.pausado = True

    def reanudar_juego(self):
        self.pausado = False

    def reiniciar_juego(self):
        """Restablece el estado para una nueva partida o nivel."""
        avance_nivel = self.jefe_derrotado
        if self.jefe_derrotado:
            self.nivel += 1
            self.jefe_derrotado = False

            # Aumentar dificultad
            self.MIN_TIEMPO_GENERACION = max(settings.GEN_MIN_SUELO,
                                             self.MIN_TIEMPO_GENERACION - settings.GEN_DECREMENTO_NIVEL)
            self.MAX_TIEMPO_GENERACION = max(settings.GEN_MIN_SUELO,
                                             self.MAX_TIEMPO_GENERACION - settings.GEN_DECREMENTO_NIVEL)
        else:
            # Partida desde cero: se restablece al jugador in situ (sin recrearlo)
            # para que los managers puedan conservar su referencia.
            self.jugador.reiniciar(self.pantalla_ancho, self.pantalla_alto)
            self.MIN_TIEMPO_GENERACION = settings.GEN_MIN_INICIAL
            self.MAX_TIEMPO_GENERACION = settings.GEN_MAX_INICIAL
            self.puntuacion = 0

        # Reiniciar todos los valores del juego a sus estados iniciales
        self.entity_manager.vaciar_todo(avance_nivel=avance_nivel)
        self.enemigos_golpeados.clear()
        self.tiempo_proximo_enemigo = 0
        self.tiempo_juego = 0.0
        self.inicio_juego = 0.0
        # El avance de nivel conserva el jugador: hay que resetear sus timers
        # para que no queden "en el pasado" respecto al reloj recién puesto a 0.
        self.jugador.ultimo_disparo = 0
        self.jugador.tiempo_invulnerable = 0
        self.jugador.invulnerable = False
        self.pausado = False
        self.estado_game_over = False

        # Resetear el WaveManager para que el jefe pueda volver a salir en el siguiente nivel
        self.wave_manager.jefe_generado = False
        self.wave_manager.tiempo_inicio_espera_jefe = 0
        self.pendiente_reinicio = False

        # Detenemos la música
        self.audio_manager.detener_toda_la_musica()
        # Aseguramos que suene la música principal
        self.audio_manager.reproducir_musica("rain_of_lasers")

    # --- Contrato "reglas" que consume CollisionManager -------------------
    def al_eliminar_enemigo(self, enemigo):
        """Consecuencias de reglas al destruir un enemigo.

        Lo llama `CollisionManager` tras encargarse de la parte mecánica
        (`kill`, explosión, purga del cooldown): aquí solo van puntuación, loot
        y la transición diferida cuando cae el jefe.
        """
        self.enemigos_eliminados += 1
        tipo_item = enemigo.die(self.jugador, self.enemigos_eliminados)
        if tipo_item:
            self._spawnear_item(tipo_item, enemigo.rect.center)
            self.enemigos_eliminados = 0

        self.puntuacion += enemigo.valor_puntuacion * self.nivel

        # Jefe derrotado -> transición diferida (la ejecuta Juego.actualizar)
        if isinstance(enemigo, Jefe):
            self.jefe_derrotado = True
            self.jefe = None
            self.pendiente_reinicio = True

    def _spawnear_item(self, tipo, posicion):
        img = self.rm.get_image_scaled(tipo, Item.TAMANO_ESTANDAR)
        self.entity_manager.items.add(Item(tipo, img, posicion[0], posicion[1]))

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
            self.jugador.tiempo_invulnerable = self.tiempo_juego + settings.JUGADOR_INVULNERABLE_MS
            self.jugador.curar(self.jugador.salud_maxima)
            self.effect_manager.crear_destello_invulnerabilidad()

    def disparar(self):
        """Extrae las balas del jugador y las registra en el manager de entidades."""
        # 2. Superficie de la bala ya escalada y orientada (cacheada en el RM)
        imagen_bala = self.rm.get_image_rotated("bala_jugador1", Bala.TAMANO, Bala.ANGULO)

        # Llama a la función disparar del jugador para obtener las nuevas balas
        nuevas_balas = self.jugador.disparar(self.tiempo_juego, imagen_bala)

        # Verifica si hay nuevas balas y las agrega a la lista de balas
        for i, bala in enumerate(nuevas_balas):
            self.entity_manager.agregar_bala_jugador(bala)
            if i == 0:  # Reproduce el sonido solo para la primera bala
                self.audio_manager.reproducir_efecto("disparo")

    def actualizar(self, dt):
        """Actualiza el estado del juego. `dt` en segundos."""
        if self.jugador.vidas <= 0:
            self.juego_terminado()
            return

        # El reloj de juego solo corre aquí: en pausa / Game Over se congela.
        self.tiempo_juego += dt * 1000

        # 1. Entradas y Generación
        teclas = pygame.key.get_pressed()
        self.jugador.mover(teclas, self.pantalla, dt)
        self._gestionar_generacion_enemigos()

        # 2. Física y Colisiones
        self.entity_manager.actualizar(dt, self.tiempo_juego)
        self.collision_manager.actualizar(self.tiempo_juego)

        # 2b. Transición diferida: si el jefe murió durante la resolución de
        # colisiones, reiniciamos aquí (nunca desde dentro de un manager).
        if self.pendiente_reinicio:
            self.pendiente_reinicio = False
            self.reiniciar_juego()
            return

        # 3. Cosmética
        self.background.update(dt)
        self.jugador.update(dt, self.tiempo_juego)

    def _gestionar_generacion_enemigos(self):
        """Maneja el timing para spawnear enemigos mediante el WaveManager."""
        ahora = self.tiempo_juego
        if ahora > self.tiempo_proximo_enemigo:
            nuevo = self.wave_manager.spawn_enemigo(
                ahora - self.inicio_juego, ahora, self.jugador, self.nivel
            )
            if nuevo:
                self.entity_manager.agregar_enemigo(nuevo)

                if isinstance(nuevo, Jefe):
                    self.jefe = nuevo

            self.tiempo_proximo_enemigo = ahora + random.randint(self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION)

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

    def volver_al_menu(self):
        """Solicita terminar la partida y devolver el control al menú principal."""
        self.resultado = "MENU"
        self.ejecutando = False

    def salir_del_juego(self):
        """Solicita cerrar la aplicación por completo."""
        self.resultado = "SALIR"
        self.ejecutando = False

    def mostrar_opciones_juego(self):
        """Abre la pantalla de opciones sobre la pausa de la partida."""
        from src.ui.menu import MenuManager
        menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)

        if menu.mostrar_solo_opciones() == "SALIR":
            self.salir_del_juego()

    def dibujar(self):
        """Lógica de dibujo delegada al RenderManager."""
        self.render_manager.renderizar_todo()

    def ejecutar(self):
        """Ejecuta el bucle de la partida. Devuelve el siguiente estado ("MENU"/"SALIR")."""
        self.ejecutando = True

        while self.ejecutando:
            pygame.display.set_caption("Galactic Guardian")

            # Si manejar_eventos() devuelve False, salimos del bucle
            if not self.input_handler.manejar_eventos():
                self.ejecutando = False
                continue

            # Si el juego está pausado, solo dibujar la pantalla y continuar al siguiente ciclo
            if self.pausado:
                self.dibujar()
                self.reloj.tick(settings.FPS)
                continue

            # dt en segundos, acotado para evitar saltos tras un parón (breakpoint,
            # arrastre de ventana, primer frame...)
            dt = min(self.reloj.tick(settings.FPS) / 1000.0, 3.0 / settings.FPS)

            self.actualizar(dt)
            self.dibujar()

        # Limpieza única de audio al abandonar la partida
        self.audio_manager.detener_toda_la_musica()
        return self.resultado
