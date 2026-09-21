import math
import random
import weakref

import pygame
import pygame.freetype

from src.core import settings
from src.core import sin_fin
from src.core.combo import Combo
from src.core.mejoras import Bonus
from src.core.niveles import definicion_nivel
from src.core.version import __version__
from src.entities.enemies import Jefe
from src.entities.player import Jugador
from src.entities.bullet import Bala
from src.visual.background import ScrollingBackground
from src.managers.collision import CollisionManager
from src.managers.effects import EffectManager
from src.managers.entities import EntityManager
from src.core.input import InputHandler
from src.managers.render import RenderManager
from src.ui.hud import UIManager
from src.managers.waves import WaveManager


class Juego:
    def __init__(self, pantalla, audio_manager, clasificacion, resource_manager,
                 modo=settings.MODO_CAMPANA, progresion=None, guardado=None, continuar=False):
        # 1. Configuración básica y Hardware
        # `modo`: campaña (niveles fijos con jefe final) o sin fin (oleadas sin
        # techo). `clasificacion` es el ranking de ese modo: quien crea el `Juego`
        # elige cuál pasar.
        self.modo = modo
        # Progresión entre partidas: las mejoras compradas dan un `Bonus` a la nave
        # y las monedas se cobran de la puntuación (`_cobrar_monedas`). Sin ella
        # (`None`) el juego es el de siempre.
        self.progresion = progresion
        self.bonus = progresion.bonus() if progresion else Bonus()
        self.monedas_cobradas = 0   # monedas de esta partida ya ingresadas
        # Punto de control de este modo (ver `guardado.py`). Con `continuar`, la partida arranca
        # en el nivel u oleada guardado y con su puntuación (vidas y salud, las de partida nueva).
        self.guardado = guardado
        self.rm = resource_manager
        self.pantalla = pantalla
        self.pantalla_ancho = pantalla.get_width()
        self.pantalla_alto = pantalla.get_height()
        self.reloj = pygame.time.Clock()

        # 2. Estado de la Partida
        self.puntuacion = 0
        self.combo = Combo(self.bonus.combo_factor)   # bajas seguidas sin daño -> multiplicador
        self.nivel = 1   # nivel de la campaña, o nº de oleada en el modo sin fin
        if continuar and guardado is not None and guardado.existe:
            self.nivel = guardado.nivel
            self.puntuacion = guardado.puntuacion
            self.monedas_cobradas = self._monedas_de(self.puntuacion)   # esos puntos ya se cobraron en su día
        self.pausado = False
        self.estado_game_over = False
        self.pidiendo_nombre = False
        self.pidiendo_nombre_para = None   # "game_over" | "victoria": a qué pantalla ir tras registrar el nombre
        self.nombre_entrada = ""
        self.jefe_derrotado = False
        self.disparando = False
        self.pendiente_reinicio = False  # Transición diferida (ver actualizar())
        self.debug_hitboxes = False      # F1: dibuja los círculos de colisión

        # Campaña: pantallas de fin de nivel / victoria final (ver ROADMAP)
        self.estado_nivel_completado = False
        self.estado_victoria_final = False
        self.mostrando_seleccion_nivel = False
        self.enemigos_eliminados_nivel = 0   # total del nivel (para la pantalla de resumen)

        # Transición de cierre de nivel al derrotar al jefe: la nave se centra,
        # sube y desaparece con el fondo acelerando, antes de mostrar la
        # pantalla de nivel completado / victoria. Mientras dura, el jugador no
        # se controla (ver InputHandler) y actualizar() la mueve por su cuenta.
        self.transicion_activa = False
        self.transicion_fase = None          # "centrar" | "subir" | "espera"
        self.transicion_tiempo_fase = 0.0    # ms transcurridos en la fase actual

        # Control de la máquina de estados de alto nivel
        self.ejecutando = True
        self.resultado = "MENU"  # "MENU" | "SALIR"

        # Cadencia de aparición de enemigos (viene de la definición del nivel)
        self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION = self._definicion().intervalo_spawn

        # 3. Entidades principales y estado compartido por los managers
        self.background = ScrollingBackground(
            self.rm.get_image("imagen_fondo1"),
            self.rm.get_image("imagen_fondo2"),
            self.pantalla_alto,
            velocidad=settings.FONDO_VELOCIDAD_NORMAL,
        )
        self.jugador = Jugador(
            self.rm.get_image_scaled("jugador", Jugador.CONFIG["tamano"]),
            self.pantalla_ancho,
            self.pantalla_alto,
            self.bonus,
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
        self.audio_manager.reproducir_musica(self._definicion().musica)
        self.clasificacion = clasificacion

        self.jefe = None

        # Botones de overlays (los crea RenderManager una sola vez y los cachea)
        self.boton_reanudar = None
        self.boton_opciones = None
        self.boton_salir = None
        self.boton_reintentar = None
        self.boton_salir_post = None
        self.boton_continuar = None
        self.boton_elegir_nivel = None
        self.botones_seleccion_nivel = None   # lista, se recrea si cambia el nivel máximo
        self.boton_reintentar_final = None
        self.boton_menu_final = None

    def _definicion(self):
        """Definición del nivel (campaña) o de la oleada (sin fin) en curso."""
        if self.modo == settings.MODO_SIN_FIN:
            return sin_fin.definicion_oleada(self.nivel)
        return definicion_nivel(self.nivel)

    def pausar_juego(self):
        """Pausa el juego. `tiempo_juego` deja de avanzar solo (no se llama a
        actualizar mientras `pausado`), así que no hay nada más que hacer."""
        self.pausado = True

    def reanudar_juego(self):
        self.pausado = False

    def reiniciar_juego(self, nivel_forzado=None):
        """Restablece el estado para una nueva partida, el siguiente nivel, o
        (`nivel_forzado`) un nivel concreto elegido a mano en el selector."""
        avance_nivel = self.jefe_derrotado and nivel_forzado is None
        if not avance_nivel:
            self._cobrar_monedas()   # la puntuación va a ponerse a cero: cobrar antes lo pendiente
        if nivel_forzado is not None:
            # Selector de nivel: arranca ese nivel como una partida nueva.
            self.nivel = nivel_forzado
            self.jefe_derrotado = False
            self.jugador.reiniciar(self.pantalla_ancho, self.pantalla_alto)
            self.puntuacion = 0
            self.monedas_cobradas = 0
            self.combo.romper()
        elif self.jefe_derrotado:
            self.nivel += 1
            self.jefe_derrotado = False
            # La transición ya movió a la nave fuera de la pantalla: el nivel
            # nuevo empieza con ella en su sitio de siempre (mejoras y vidas
            # intactas, y el combo sigue) y con la barra de salud llena.
            self.jugador.recentrar(self.pantalla_ancho, self.pantalla_alto)
            self.jugador.curar(self.jugador.salud_maxima)
        else:
            # Partida desde cero: se restablece al jugador in situ (sin recrearlo)
            # para que los managers puedan conservar su referencia.
            self.jugador.reiniciar(self.pantalla_ancho, self.pantalla_alto)
            self.puntuacion = 0
            self.monedas_cobradas = 0
            self.combo.romper()
            if self.modo == settings.MODO_SIN_FIN:
                self.nivel = 1   # la campaña reintenta el nivel; el sin fin vuelve a la oleada 1

        self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION = self._definicion().intervalo_spawn

        # Reiniciar todos los valores del juego a sus estados iniciales
        self.entity_manager.vaciar_todo(avance_nivel=avance_nivel)
        self.enemigos_golpeados.clear()
        self.effect_manager.temblor.reiniciar()
        self.enemigos_eliminados_nivel = 0
        self.tiempo_proximo_enemigo = 0
        self.tiempo_juego = 0.0
        self.inicio_juego = 0.0
        # El avance de nivel conserva el jugador: hay que resetear sus timers
        # para que no queden "en el pasado" respecto al reloj recién puesto a 0.
        self.jugador.ultimo_disparo = 0
        # Ojo: el avance de nivel conserva los efectos en vuelo, y el halo de
        # invulnerabilidad es uno: hay que retirarlo con ella, no solo apagar el flag.
        self.jugador.terminar_invulnerabilidad()
        self.pausado = False
        self.estado_game_over = False
        self.estado_nivel_completado = False
        self.mostrando_seleccion_nivel = False
        self.estado_victoria_final = False
        self.transicion_activa = False
        self.transicion_fase = None
        self.transicion_tiempo_fase = 0.0
        self.background.velocidad = settings.FONDO_VELOCIDAD_NORMAL

        # Resetear el WaveManager para que el jefe pueda volver a salir en el siguiente nivel
        self.wave_manager.jefe_generado = False
        self.wave_manager.tiempo_inicio_espera_jefe = 0
        self.pendiente_reinicio = False

        # Detenemos la música
        self.audio_manager.detener_toda_la_musica()
        # Aseguramos que suene la música del nivel
        self.audio_manager.reproducir_musica(self._definicion().musica)

    # --- Contrato "reglas" que consume CollisionManager -------------------
    def al_eliminar_enemigo(self, enemigo):
        """Consecuencias de reglas al destruir un enemigo.

        Lo llama `CollisionManager` tras encargarse de la parte mecánica
        (`kill`, explosión, purga del cooldown): aquí solo van puntuación, combo
        y la transición diferida cuando cae el jefe. Los enemigos ya no sueltan
        nada: el poder de la nave viene solo de las mejoras permanentes.
        """
        self.enemigos_eliminados_nivel += 1

        self.combo.sumar_baja()   # antes de puntuar: la baja que sube de escalón ya cuenta con él
        self.puntuacion += enemigo.valor_puntuacion * self.nivel * self.combo.multiplicador

        if isinstance(enemigo, Jefe):
            self.jefe = None
            self.effect_manager.agregar_temblor(settings.TEMBLOR_JEFE)
            if self.modo == settings.MODO_SIN_FIN:
                # Sin fin: no hay cierre de nivel, la partida sigue con la oleada
                # siguiente (se llevan las balas del jefe, como en la campaña).
                self.entity_manager.balas_enemigo.empty()
                self._avanzar_oleada(curar_todo=True)   # premio por el jefe: salud completa
            else:
                # Campaña: transición diferida (la ejecuta Juego.actualizar)
                self.jefe_derrotado = True
                self.pendiente_reinicio = True

    def manejar_impacto_jugador(self):
        """Procesa el daño visual y lógico del jugador"""
        if self.jugador.vidas <= 0: return

        if self.jugador.salud > 0:
            self.effect_manager.crear_destello_recibir_danio()
            if not self.jugador.invulnerable:   # invulnerable: el impacto no cuenta
                self.effect_manager.agregar_temblor(settings.TEMBLOR_GOLPE)
                self.combo.romper()
                self.jugador.marcar_golpe(self.tiempo_juego)     # reinicia la espera de la regeneración
        else:
            self.combo.romper()
            self.effect_manager.crear_explosion(self.jugador.rect.center)
            self.effect_manager.agregar_temblor(settings.TEMBLOR_MUERTE)
            self._procesar_muerte_jugador()

    def _procesar_muerte_jugador(self):
        """Lógica interna de pérdida de vida y reaparición."""
        self.jugador.rect.centerx = self.pantalla_ancho // 2
        self.jugador.rect.bottom = self.pantalla_alto - 10
        self.jugador.reducir_vidas(1)

        if self.jugador.vidas > 0:
            self.jugador.invulnerable = True
            self.jugador.tiempo_invulnerable = (
                self.tiempo_juego + settings.JUGADOR_INVULNERABLE_MS + self.bonus.invulnerable_extra_ms)
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
        self.effect_manager.temblor.actualizar(dt)   # también durante la transición de fin de nivel

        if self.transicion_activa:
            # Cierre de nivel en curso: la nave no se controla (ver
            # InputHandler), no se generan enemigos y no hay nada con lo que
            # colisionar (el jefe ya ha muerto). Solo movemos la nave "sola",
            # el fondo, y dejamos que efectos/ítems terminen su animación.
            self._actualizar_transicion_nivel(dt)
            self.entity_manager.actualizar(dt, self.tiempo_juego)
            return

        # 1. Entradas y Generación
        teclas = pygame.key.get_pressed()
        self.jugador.mover(teclas, self.pantalla, dt, self.input_handler.mapa_teclas)
        self._gestionar_generacion_enemigos()

        # 2. Física y Colisiones
        self.entity_manager.actualizar(dt, self.tiempo_juego)
        self.collision_manager.actualizar(self.tiempo_juego)

        # 2b. Transición diferida: si el jefe murió durante la resolución de
        # colisiones, arrancamos aquí la secuencia de cierre de nivel (nunca
        # desde dentro de un manager).
        if self.pendiente_reinicio:
            self.pendiente_reinicio = False
            self._iniciar_transicion_fin_de_nivel()
            return

        # 3. Cosmética
        self.background.update(dt)
        self.jugador.update(dt, self.tiempo_juego)

    def _gestionar_generacion_enemigos(self):
        """Maneja el timing para spawnear enemigos mediante el WaveManager."""
        ahora = self.tiempo_juego
        if self.modo == settings.MODO_SIN_FIN and self._oleada_agotada(ahora):
            self._avanzar_oleada()
        if ahora > self.tiempo_proximo_enemigo:
            nuevo = self.wave_manager.spawn_enemigo(
                ahora - self.inicio_juego, ahora, self.jugador, self.nivel, self._definicion()
            )
            if nuevo:
                self.entity_manager.agregar_enemigo(nuevo)

                if isinstance(nuevo, Jefe):
                    self.jefe = nuevo

            self.tiempo_proximo_enemigo = ahora + random.randint(self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION)

    def _oleada_agotada(self, ahora):
        """Sin fin: una oleada normal acaba por tiempo; la de jefe, al caer este
        (ver `al_eliminar_enemigo`)."""
        return (not sin_fin.es_oleada_de_jefe(self.nivel)
                and ahora - self.inicio_juego >= sin_fin.OLEADA_MS)

    def _avanzar_oleada(self, curar_todo=False):
        """Sin fin: pasa a la oleada siguiente sin tocar nada de lo que hay en
        pantalla (enemigos, balas): solo cambia la definición. Sin ítems de
        curación, cada oleada nueva recupera una parte de la salud
        (`SIN_FIN_CURACION_OLEADA`) y derrotar a un jefe la deja completa."""
        salud_max = self.jugador.salud_maxima
        self.jugador.curar(salud_max if curar_todo else math.ceil(settings.SIN_FIN_CURACION_OLEADA * salud_max))
        self.nivel += 1
        self._guardar_punto_de_control(self.nivel)
        self.inicio_juego = self.tiempo_juego
        definicion = self._definicion()
        self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION = definicion.intervalo_spawn
        self.wave_manager.jefe_generado = False
        self.wave_manager.tiempo_inicio_espera_jefe = 0
        # Tras una oleada de jefe vuelve la música normal (idempotente si ya suena).
        self.audio_manager.reproducir_musica(definicion.musica)

    def juego_terminado(self):
        """Muestra el mensaje de "Game Over" y las opciones de "Reintentar" y "Salir"."""
        self.pausado = True  # Usamos el estado de pausa para detener la actualización
        # Detener música de fondo
        self.audio_manager.detener_toda_la_musica()
        # Iniciar música Game Over de fondo
        self.audio_manager.reproducir_musica("defeated_tune")
        self._pedir_nombre_o_mostrar("game_over")

    def _iniciar_transicion_fin_de_nivel(self):
        """Arranca la secuencia de cierre de nivel justo al derrotar al jefe.

        Quita las balas en vuelo (del jefe y del jugador) y silencia el
        disparo; `_actualizar_transicion_nivel` se encarga del resto fotograma
        a fotograma hasta que `_finalizar_transicion_fin_de_nivel` muestre la
        pantalla correspondiente.
        """
        self.audio_manager.detener_toda_la_musica()
        self.audio_manager.reproducir_musica("victory_tune")
        self.entity_manager.balas.empty()
        self.entity_manager.balas_enemigo.empty()
        self.disparando = False

        self.transicion_activa = True
        self.transicion_fase = "centrar"
        self.transicion_tiempo_fase = 0.0

    def _actualizar_transicion_nivel(self, dt):
        """Fotograma a fotograma de la secuencia: centrar -> subir -> esperar.

        Valores ajustables en `settings.py`: `TRANSICION_VEL_LATERAL` (rapidez
        al centrarse), `TRANSICION_VEL_SUBIDA` (rapidez al subir),
        `TRANSICION_FONDO_ACELERACION` / `TRANSICION_FONDO_RAMPA_MS` (cuánto y
        en cuánto tiempo se acelera el fondo) y `TRANSICION_ESPERA_MS` (pausa
        tras desaparecer la nave, antes de la pantalla).
        """
        factor = dt * settings.FPS
        jugador = self.jugador
        centro_x = self.pantalla_ancho // 2

        if self.transicion_fase == "centrar":
            paso = settings.TRANSICION_VEL_LATERAL * factor
            diferencia = centro_x - jugador.rect.centerx
            if abs(diferencia) <= paso:
                jugador.rect.centerx = centro_x
                self.transicion_fase = "subir"
            else:
                jugador.rect.centerx += paso if diferencia > 0 else -paso

        elif self.transicion_fase == "subir":
            jugador.rect.y -= settings.TRANSICION_VEL_SUBIDA * factor

            # El fondo acelera de forma gradual mientras la nave sube.
            rampa = min(1.0, self.transicion_tiempo_fase / settings.TRANSICION_FONDO_RAMPA_MS)
            self.background.velocidad = settings.FONDO_VELOCIDAD_NORMAL * (
                1 + rampa * (settings.TRANSICION_FONDO_ACELERACION - 1)
            )
            self.transicion_tiempo_fase += dt * 1000

            if jugador.rect.bottom < -settings.TRANSICION_MARGEN_SALIDA:   # ha desaparecido por arriba
                self.transicion_fase = "espera"
                self.transicion_tiempo_fase = 0.0

        elif self.transicion_fase == "espera":
            self.transicion_tiempo_fase += dt * 1000
            if self.transicion_tiempo_fase >= settings.TRANSICION_ESPERA_MS:
                self._finalizar_transicion_fin_de_nivel()
                return

        self.background.update(dt)

    def _finalizar_transicion_fin_de_nivel(self):
        """Termina la transición y muestra "nivel completado" o la victoria
        final si era el último nivel de la campaña."""
        self._cobrar_monedas()   # punto de control: lo ganado hasta aquí ya no se pierde
        self.transicion_activa = False
        self.transicion_fase = None
        self.background.velocidad = settings.FONDO_VELOCIDAD_NORMAL
        self.pausado = True

        if self.nivel >= settings.NIVEL_MAX:
            if self.guardado is not None:
                self.guardado.borrar()          # campaña completada: no queda nada que continuar
            self._pedir_nombre_o_mostrar("victoria")
        else:
            self._guardar_punto_de_control(self.nivel + 1)   # ya cuenta aunque se cierre en el resumen
            self.estado_nivel_completado = True

    def _cualifica_para_el_top10(self):
        top = self.clasificacion.obtener_puntuaciones_top()
        return len(top) < 10 or self.puntuacion > top[-1][1]

    def _pedir_nombre_o_mostrar(self, destino):
        """`destino`: "game_over" o "victoria". Si la puntuación entra en el
        top 10 se pide el nombre primero (`pidiendo_nombre_para` recuerda a qué
        pantalla ir después); si no, se muestra esa pantalla directamente."""
        self._cobrar_monedas()   # fin de partida (Game Over / victoria): las pantallas muestran lo cobrado
        if self._cualifica_para_el_top10():
            self.pidiendo_nombre = True
            self.pidiendo_nombre_para = destino
            self.nombre_entrada = ""
        elif destino == "game_over":
            self.estado_game_over = True
        else:
            self.estado_victoria_final = True

    def _cobrar_monedas(self):
        """Ingresa en la progresión las monedas que aún no se han cobrado de esta
        partida (`MONEDAS_PUNTOS` puntos por moneda, más el % de la mejora
        "Botín"). Es idempotente: llamarla varias veces no duplica nada, así que
        se llama en cada forma de terminar o pausar el progreso de una partida."""
        if self.progresion is None:
            return
        total = self._monedas_de(self.puntuacion)
        nuevas = total - self.monedas_cobradas
        if nuevas > 0:
            self.progresion.ingresar(nuevas)
            self.monedas_cobradas = total

    def _monedas_de(self, puntuacion):
        """Monedas que dan `puntuacion` puntos (con el % de la mejora "Botín")."""
        return int((puntuacion // settings.MONEDAS_PUNTOS) * (1 + self.bonus.monedas_pct))

    def _guardar_punto_de_control(self, nivel):
        """Apunta en el guardado que se continuará en `nivel` con la puntuación actual (ver
        `guardado.py`). Se llama al terminar un nivel de la campaña y al cambiar de oleada."""
        if self.guardado is not None:
            self.guardado.guardar_punto(nivel, self.puntuacion)

    def volver_al_menu(self):
        """Solicita terminar la partida y devolver el control al menú principal."""
        self._cobrar_monedas()
        self.resultado = "MENU"
        self.ejecutando = False

    def salir_del_juego(self):
        """Solicita cerrar la aplicación por completo."""
        self._cobrar_monedas()
        self.resultado = "SALIR"
        self.ejecutando = False

    def _invalidar_botones(self):
        """Olvida los botones de los overlays: `RenderManager` los vuelve a crear
        (con los textos del idioma actual) la próxima vez que se dibujen."""
        for nombre in ("boton_reanudar", "boton_opciones", "boton_salir", "boton_reintentar",
                       "boton_salir_post", "boton_continuar", "boton_elegir_nivel",
                       "botones_seleccion_nivel", "boton_reintentar_final", "boton_menu_final"):
            setattr(self, nombre, None)

    def mostrar_opciones_juego(self):
        """Abre la pantalla de opciones sobre la pausa de la partida."""
        from src.ui.menu import MenuManager
        menu = MenuManager(self.pantalla, self.rm, self.audio_manager, self.clasificacion)

        resultado = menu.mostrar_solo_opciones()
        self._invalidar_botones()   # por si se cambió de idioma: sus textos están cacheados
        # Las teclas que quedan en el menú: las nuevas si se pulsó "Guardar" y las
        # de antes si se pulsó "Volver" (que descarta los cambios).
        self.input_handler.mapa_teclas = menu.controles
        if resultado == "SALIR":
            self.salir_del_juego()

    def dibujar(self):
        """Lógica de dibujo delegada al RenderManager."""
        self.render_manager.renderizar_todo()

    def ejecutar(self):
        """Ejecuta el bucle de la partida. Devuelve el siguiente estado ("MENU"/"SALIR")."""
        self.ejecutando = True

        while self.ejecutando:
            pygame.display.set_caption(f"Galactic Guardian v{__version__}")

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
        self._cobrar_monedas()   # por si se salió por un camino que no la cobró (idempotente)
        self.audio_manager.detener_toda_la_musica()
        return self.resultado
