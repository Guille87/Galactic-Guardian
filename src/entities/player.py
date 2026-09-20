import pygame

from src.core import controles, settings
from src.core.mejoras import Bonus
from .bullet import Bala
from .base.movimiento import MovimientoSubpixel


class Jugador(pygame.sprite.Sprite, MovimientoSubpixel):
    # Constantes de clase para configuración (Mantenible)
    CONFIG = {
        "tamano": (50, 50),
        "salud_max": 50,
        "vidas_init": 3,
        "vel_base": 4,             # velocidad al empezar (px/frame-a-60fps)
        "vel_max": 6,
        "cadencia_base": 350,      # ms entre disparos al empezar
        "cadencia_max": 150,       # ms entre disparos como mínimo
        "danio_base": 10,          # daño de tu bala al empezar
        "danio_max": 30
    }

    destello_constante = None   # halo de invulnerabilidad en pantalla (lo crea `EffectManager`)

    def __init__(self, imagen, pantalla_ancho, pantalla_alto, bonus=None):
        super().__init__()
        # Mejoras permanentes (ver `mejoras.py`): suben el valor de arranque.
        self.bonus = bonus or Bonus()
        # Recibimos la Surface ya escalada y cacheada por el ResourceManager
        self.image = imagen
        self.rect = self.image.get_rect()

        self._init_subpixel()
        self._vel_actual = pygame.Vector2()  # para el suavizado opcional

        # Estado de partida (posición, estadísticas, armas, timers): se fija en
        # `reiniciar` para poder restablecerlo sin recrear el objeto.
        self.reiniciar(pantalla_ancho, pantalla_alto)

    def reiniciar(self, pantalla_ancho, pantalla_alto):
        """Restablece al jugador a su estado inicial de una partida nueva.

        No recrea el objeto: `engine.reiniciar_juego` lo llama en la ruta "partida
        desde cero" para que los managers puedan conservar la referencia al
        jugador (ver auditoría, item 14)."""
        # 1. Posición inicial
        self.rect.centerx = pantalla_ancho // 2
        self.rect.bottom = pantalla_alto - 10

        # 2. Atributos de Estado (Estadísticas)
        # (las mejoras permanentes suben el arranque, nunca los topes de `CONFIG`)
        b = self.bonus
        self.vidas = self.CONFIG["vidas_init"] + b.vidas_extra
        self.salud_maxima = self.CONFIG["salud_max"] + b.salud_extra
        self.salud = self.salud_maxima
        self.velocidad = min(self.CONFIG["vel_max"], self.CONFIG["vel_base"] + b.velocidad_extra)
        self.danio = min(self.CONFIG["danio_max"], self.CONFIG["danio_base"] + b.danio_extra)

        # 3. Sistema de Armas
        self.cadencia_disparo = max(self.CONFIG["cadencia_max"], self.CONFIG["cadencia_base"] - b.cadencia_menos_ms)
        self.ultimo_disparo = 0
        self.tipo_disparo = b.disparo_inicial  # simple, doble, triple

        # 4. Estado Físico
        self.terminar_invulnerabilidad()
        self.radius = settings.RADIO_JUGADOR

        # 5. Acumuladores de movimiento sub-pixel
        self._resto.update(0, 0)
        self._ultimo_desplazamiento.update(0, 0)
        self._vel_actual.update(0, 0)

    def recentrar(self, pantalla_ancho, pantalla_alto):
        """Vuelve a la posición de salida sin tocar estadísticas ni mejoras.

        Se usa en la transición entre niveles de la campaña: el nivel
        siguiente empieza con la nave en su sitio de siempre, no donde haya
        quedado tras salir volando por arriba de la pantalla."""
        self.rect.centerx = pantalla_ancho // 2
        self.rect.bottom = pantalla_alto - 10
        self._resto.update(0, 0)
        self._ultimo_desplazamiento.update(0, 0)
        self._vel_actual.update(0, 0)

    @property
    def danio_maximo(self):
        return self.CONFIG["danio_max"]

    @property
    def velocidad_maxima(self):
        return self.CONFIG["vel_max"]

    @property
    def cadencia_disparo_maxima(self):
        return self.CONFIG["cadencia_max"]

    def mover(self, teclas, pantalla, dt, mapa_teclas=None):
        """Mueve al jugador según las teclas presionadas (independiente de FPS).

        Las flechas son fijas; `mapa_teclas` (acción -> tecla) añade la
        reasignable, WASD por defecto (`controles.POR_DEFECTO`)."""
        mapa_teclas = mapa_teclas or controles.POR_DEFECTO
        dx = (teclas[pygame.K_RIGHT] or teclas[mapa_teclas["derecha"]]) \
            - (teclas[pygame.K_LEFT] or teclas[mapa_teclas["izquierda"]])
        dy = (teclas[pygame.K_DOWN] or teclas[mapa_teclas["abajo"]]) \
            - (teclas[pygame.K_UP] or teclas[mapa_teclas["arriba"]])

        # Normalizar la diagonal para que no sea 1.41x más rápida
        direccion = pygame.Vector2(dx, dy)
        if direccion.length_squared() > 0:
            direccion.scale_to_length(1.0)
        objetivo = direccion * self.velocidad

        # Suavizado opcional (settings.JUGADOR_SUAVIZADO; 1.0 = instantáneo)
        s = settings.JUGADOR_SUAVIZADO
        if s >= 1.0:
            self._vel_actual.update(objetivo)
        else:
            self._vel_actual = self._vel_actual.lerp(objetivo, min(1.0, s * dt * settings.FPS))

        self._desplazar(self._vel_actual.x, self._vel_actual.y, dt)

        # Obtenemos el rect de la superficie si es necesario
        if isinstance(pantalla, pygame.Surface):
            rect_limite = pantalla.get_rect()
        else:
            rect_limite = pantalla

        # Limita el movimiento del jugador para que no salga de los bordes de la pantalla
        self.rect.clamp_ip(rect_limite.inflate(-15, -45))

    def disparar(self, tiempo_actual, imagen_bala):
        """Lógica de control de tiempo para disparar."""
        if tiempo_actual - self.ultimo_disparo > self.cadencia_disparo:
            self.ultimo_disparo = tiempo_actual
            return self._generar_balas(imagen_bala)
        return []

    def _generar_balas(self, imagen_bala):
        """Crea las instancias de balas según el power-up actual.

        `imagen_bala` es la `Surface` ya escalada y orientada (cacheada por el
        ResourceManager)."""
        balas = []

        pos_x = self.rect.centerx
        pos_y = self.rect.top + 10

        if self.tipo_disparo == "triple":
            offsets = [-15, 0, 15]
        elif self.tipo_disparo == "doble":
            offsets = [-10, 10]
        else:
            offsets = [0]

        for offset in offsets:
            balas.append(Bala(imagen_bala, pos_x + offset, pos_y, self.danio))

        return balas

    def recibir_danio(self, cantidad):
        if not self.invulnerable:  # Verificar si la nave es vulnerable
            self.salud = max(0, self.salud - cantidad)
            return True
        return False

    def curar(self, cantidad):
        """
        Aumenta la salud del jugador.
        :param cantidad: Cantidad de salud que se va a aumentar.
        """
        self.salud = min(self.salud_maxima, self.salud + cantidad)

    def reducir_vidas(self, cantidad):
        self.vidas = max(0, self.vidas - cantidad)

    def update(self, dt=0, tiempo_juego=0):
        """Actualiza el estado del jugador en cada fotograma.

        `tiempo_juego` es el reloj de juego en ms (se congela en pausa).
        """
        if self.invulnerable and tiempo_juego > self.tiempo_invulnerable:
            self.terminar_invulnerabilidad()

    def terminar_invulnerabilidad(self):
        """Quita la invulnerabilidad **y** su halo. Siempre juntas: si el flag se
        apaga sin retirar el sprite, `update` ya no lo retira nunca (solo mira el
        halo mientras `invulnerable`) y el halo se queda en pantalla para siempre
        aunque la nave sea vulnerable."""
        self.invulnerable = False
        self.tiempo_invulnerable = 0
        if self.destello_constante:
            self.destello_constante.kill()
            self.destello_constante = None

    def obtener_cadencia_visual(self):
        """
        Convierte la cadencia (ms) en disparos por segundo para la UI.
        Ejemplo: 250 ms -> 4.0 disparos/seg.
        """
        return round(1000 / self.cadencia_disparo, 1)

    def obtener_cadencia_max_visual(self):
        """Devuelve el límite máximo de disparos por segundo."""
        return round(1000 / self.CONFIG["cadencia_max"], 1)
