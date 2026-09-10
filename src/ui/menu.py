import math
import time
import webbrowser

import pygame
import pygame_gui

from src.core import config, settings
from src.core.updates import ComprobadorActualizaciones
from src.core.version import __version__
from src.ui.components.button import Boton

# Escalón de las flechas ◄ ► (0.1). El arrastre de la barra es libre; solo se
# redondea a 2 decimales para no guardar basura de coma flotante.
_PASO_VOLUMEN = settings.VOLUMEN_PASO
_DECIMALES_VOLUMEN = 2


def _clamp_volumen(v):
    """Recorta a [0, 1] y redondea (arrastre libre).

    Un valor fuera de [0, 1], aunque sea por 1e-17, hace que `pygame_gui` cree
    el slider fuera de rango y lo deje sin responder.
    """
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.5
    return round(min(1.0, max(0.0, v)), _DECIMALES_VOLUMEN)


def _paso_volumen(v, subir):
    """Múltiplo de `_PASO_VOLUMEN` inmediatamente por encima/debajo de `v`.

    0.27 → flecha arriba 0.3, flecha abajo 0.2. 0.20 → 0.3 / 0.1.
    """
    n = round(v / _PASO_VOLUMEN, 6)
    objetivo = (math.floor(n) + 1 if subir else math.ceil(n) - 1) * _PASO_VOLUMEN
    return _clamp_volumen(objetivo)


class MenuManager:
    """
    Clase principal para gestionar las pantallas del menú (Estado).

    `ejecutar()` corre el bucle del menú y devuelve el siguiente estado de la
    máquina de alto nivel: "JUGAR" o "SALIR". El objeto es persistente: se
    reutiliza cada vez que se vuelve al menú desde la partida.
    """

    def __init__(self, pantalla, resource_manager, audio_manager, sistema_clasificacion):
        self.pantalla = pantalla
        self.rm = resource_manager
        self.am = audio_manager
        self.clasificacion = sistema_clasificacion
        self.font_titulo = pygame.font.Font(None, 76)
        self.font_estandar = pygame.font.Font(None, 36)
        self.font_version = pygame.font.Font(None, 24)
        self.ui_manager = None          # UI de opciones (pygame_gui); se crea una vez

        # Reloj único de la instancia (no crear uno nuevo por frame)
        self.clock = pygame.time.Clock()

        # Estado inicial
        self.estado = "PRINCIPAL"  # Posibles: PRINCIPAL, OPCIONES, PUNTUACIONES
        self.ejecutando = True
        self.resultado = None  # "JUGAR" | "SALIR"

        # Cargar config inicial
        vol_musica, vol_efectos = config.cargar_configuracion()
        self.vol_musica = _clamp_volumen(vol_musica)
        self.vol_efectos = _clamp_volumen(vol_efectos)
        self._crear_botones()

        # Control de feedback sonoro
        self.sonido_reproduciendose = False
        self.tiempo_final_reproduccion = 0
        # (destino, sube) mientras esperamos el UI_HORIZONTAL_SLIDER_MOVED que
        # pygame_gui emite tras pulsar una flecha ◄ ►; ese MOVED se cuadra al
        # escalón en vez de aplicarse tal cual.
        self._flecha_pendiente = None

        # Aviso de nueva versión (comprobación en segundo plano, best-effort)
        self.actualizaciones = ComprobadorActualizaciones()
        self.btn_actualizar = Boton(
            "Descargar actualización", (255, 170, 0, 160), (0, 0, 0),
            self.pantalla.get_rect().centerx, 270, 320, 44, 10,
        )

    def _preparar_musica(self):
        """Usa el AudioManager para gestionar la música del menú."""
        self.am.reproducir_musica("skyfire_theme")

    def _crear_botones(self):
        cx = self.pantalla.get_rect().centerx
        self.btn_jugar = Boton("Jugar", (0, 255, 0, 100), (255, 255, 255), cx, 350, 200, 50, 10)
        self.btn_opciones = Boton("Opciones", (0, 0, 255, 128), (255, 255, 255), cx, 420, 200, 50, 10)
        self.btn_puntos = Boton("Puntuaciones", (255, 255, 0, 128), (255, 255, 255), cx, 490, 200, 50, 10)

    def ejecutar(self):
        """Bucle principal del menú. Devuelve el siguiente estado ("JUGAR"/"SALIR")."""
        # Reinicio de estado por si volvemos desde una partida
        self.ejecutando = True
        self.estado = "PRINCIPAL"
        self.resultado = None

        self._preparar_musica()  # Solo activamos la música aquí, al lanzar el menú completo
        self.actualizaciones.comprobar_en_segundo_plano()  # no-op si ya se lanzó

        while self.ejecutando:
            time_delta = self.clock.tick(settings.FPS) / 1000.0

            if self.estado == "PRINCIPAL":
                self._menu_principal()
            elif self.estado == "OPCIONES":
                self._menu_opciones(time_delta)
            elif self.estado == "PUNTUACIONES":
                self._menu_puntuaciones()

        return self.resultado or "SALIR"

    def _menu_principal(self):
        pygame.display.set_caption(f"Galactic Guardian v{__version__} - Menú")
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                info = self.actualizaciones.resultado
                if isinstance(info, dict) and self.btn_actualizar.clic_en_boton(event.pos):
                    webbrowser.open(info["url"])
                elif self.btn_jugar.clic_en_boton(event.pos):
                    self.am.detener_musica("skyfire_theme")
                    self.ejecutando = False
                    self.resultado = "JUGAR"
                elif self.btn_opciones.clic_en_boton(event.pos):
                    self._abrir_opciones()
                elif self.btn_puntos.clic_en_boton(event.pos):
                    self.estado = "PUNTUACIONES"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        titulo = self.font_titulo.render("Galactic Guardian", True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(300, 150)))

        self._dibujar_aviso_actualizacion()

        self.btn_jugar.dibujar(self.pantalla, self.font_estandar)
        self.btn_opciones.dibujar(self.pantalla, self.font_estandar)
        self.btn_puntos.dibujar(self.pantalla, self.font_estandar)

        # Versión, esquina inferior derecha
        txt_version = self.font_version.render(f"v{__version__}", True, (150, 150, 150))
        self.pantalla.blit(
            txt_version,
            txt_version.get_rect(bottomright=(settings.ANCHO - 8, settings.ALTO - 6)),
        )
        pygame.display.flip()

    def _abrir_opciones(self):
        """Entra en la pantalla de opciones: crea la UI (una vez) y sincroniza
        los sliders con los volúmenes actuales, ya saneados."""
        self.estado = "OPCIONES"
        self._flecha_pendiente = None
        # Recortar antes de crear/tocar el slider: un valor fuera de [0, 1]
        # (aunque sea por 1e-17) hace que pygame_gui lo ignore y el slider quede
        # descuadrado y sin responder.
        self.vol_musica = _clamp_volumen(self.vol_musica)
        self.vol_efectos = _clamp_volumen(self.vol_efectos)
        if self.ui_manager is None:
            self._inicializar_interfaz_opciones()
        self.slider_musica.set_current_value(self.vol_musica)
        self.slider_efectos.set_current_value(self.vol_efectos)

    def _dibujar_aviso_actualizacion(self):
        """Banner + botón si la comprobación encontró una versión más nueva."""
        info = self.actualizaciones.resultado
        if not isinstance(info, dict):
            return
        texto = self.font_version.render(
            f"Nueva versión v{info['version']} disponible", True, (255, 220, 120)
        )
        self.pantalla.blit(texto, texto.get_rect(center=(300, 235)))
        self.btn_actualizar.dibujar(self.pantalla, self.font_version)

    def _inicializar_interfaz_opciones(self):
        """Crea el UIManager y los elementos de la interfaz **una sola vez**.

        Antes se recreaba en cada entrada, dejando varios UIManager vivos."""
        self.ui_manager = pygame_gui.UIManager((settings.ANCHO, settings.ALTO))

        # Etiquetas
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 120), (200, 24)), text="Música", manager=self.ui_manager
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 220), (200, 24)), text="Efectos", manager=self.ui_manager
        )

        # Sliders (click_increment: las flechas ◄ ► mueven el volumen de poco en poco)
        self.slider_musica = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 150), (500, 50)),
            start_value=self.vol_musica, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )
        self.slider_efectos = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 250), (500, 50)),
            start_value=self.vol_efectos, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )

        # Botones
        self.btn_guardar = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 350), (200, 50)), text='Guardar', manager=self.ui_manager
        )
        self.btn_volver = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((350, 350), (200, 50)), text='Volver', manager=self.ui_manager
        )

    def _feedback_sonoro_efectos(self, reiniciar=False):
        """Sonido de prueba al ajustar el volumen de efectos.

        Al arrastrar el slider llegan muchos eventos seguidos, así que se deja
        terminar el sonido antes de repetirlo. Con las flechas (`reiniciar=True`)
        cada pulsación corta y relanza el sonido para oír el volumen nuevo.
        """
        sonido = self.rm.get_sound("laser_gun")
        if not sonido:
            return
        ahora = time.time()
        if reiniciar:
            sonido.stop()
        elif self.sonido_reproduciendose and ahora < self.tiempo_final_reproduccion:
            return
        self.sonido_reproduciendose = True
        sonido.play()
        self.tiempo_final_reproduccion = ahora + sonido.get_length()

    def _fijar_volumen(self, destino, valor, feedback_reiniciar=False):
        """Propaga un volumen ya validado: estado + slider + audio (+ prueba)."""
        slider = self.slider_musica if destino == "musica" else self.slider_efectos
        if destino == "musica":
            self.vol_musica = valor
            self.am.actualizar_volumen_musica(valor)
        else:
            self.vol_efectos = valor
            self.am.actualizar_volumen_efectos(valor)
        slider.set_current_value(valor)   # re-fija por si pygame_gui lo descuadró
        if destino == "efectos":
            self._feedback_sonoro_efectos(reiniciar=feedback_reiniciar)

    def _menu_opciones(self, time_delta):
        """Lógica de la pantalla de opciones usando pygame_gui."""
        if self.ui_manager is None:                 # entrada directa sin pasar por _abrir_opciones
            self._abrir_opciones()

        fondo = self.rm.get_image("imagen_fondo1")

        # {botón de flecha: (destino, sube?)}
        flechas = {
            self.slider_musica.left_button:   ("musica", False),
            self.slider_musica.right_button:  ("musica", True),
            self.slider_efectos.left_button:  ("efectos", False),
            self.slider_efectos.right_button: ("efectos", True),
        }
        sliders = {self.slider_musica: "musica", self.slider_efectos: "efectos"}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.estado = "PRINCIPAL"
                self.resultado = "SALIR"

            # --- Eventos de pygame_gui (API 0.6+: cada evento con su propio type) ---
            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in flechas:
                # Solo marcamos la dirección. pygame_gui moverá el slider ±0.1 y
                # emitirá un MOVED (siguiente frame); ahí lo cuadramos al escalón.
                self._flecha_pendiente = flechas[event.ui_element]

            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED and event.ui_element in sliders:
                destino = sliders[event.ui_element]
                pend = self._flecha_pendiente
                if pend and pend[0] == destino:
                    # Flecha ◄ ►: al múltiplo de 0.1 anterior/siguiente al valor
                    # que había (cuadra un valor libre; 0.27 -> 0.3 o 0.2).
                    self._flecha_pendiente = None
                    actual = self.vol_musica if destino == "musica" else self.vol_efectos
                    self._fijar_volumen(destino, _paso_volumen(actual, pend[1]),
                                        feedback_reiniciar=True)
                else:
                    # Arrastre de la barra: valor libre, solo recortado.
                    self._fijar_volumen(destino, _clamp_volumen(event.ui_element.get_current_value()))

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.btn_guardar:
                    config.guardar_configuracion(self.vol_musica, self.vol_efectos)
                    self.estado = "PRINCIPAL"
                elif event.ui_element == self.btn_volver:
                    self.estado = "PRINCIPAL"

            self.ui_manager.process_events(event)

        # Dibujado
        self.ui_manager.update(time_delta)

        # pygame_gui, al MANTENER pulsada una flecha >0.2 s, arranca un
        # desplazamiento continuo y rápido del slider (se ve "dispararse" el
        # volumen antes de cuadrarse). Reseteamos su acumulador mientras la
        # flecha siga pulsada para que solo cuente el clic limpio.
        for sl in (self.slider_musica, self.slider_efectos):
            if sl.left_button.held or sl.right_button.held:
                sl.button_held_repeat_acc = 0.0
        self.pantalla.blit(fondo, (0, 0))

        # Renderizar textos (Título, etiquetas de sliders)
        txt_opciones = self.font_titulo.render("Opciones", True, (255, 255, 255))
        self.pantalla.blit(txt_opciones, (50, 50))

        self.ui_manager.draw_ui(self.pantalla)
        pygame.display.flip()

    def mostrar_solo_opciones(self):
        """Muestra las opciones y retorna el control cuando se pulsa Guardar o Volver.

        Se usa desde la pausa de la partida. Devuelve "SALIR" si el usuario cerró
        la ventana (para que el motor propague el cierre), o None en caso normal.
        """
        self._abrir_opciones()

        bucle_opciones = True
        while bucle_opciones:
            time_delta = self.clock.tick(settings.FPS) / 1000.0
            self._menu_opciones(time_delta)

            # Salida normal: Guardar o Volver dejan el estado en PRINCIPAL
            if self.estado == "PRINCIPAL":
                bucle_opciones = False

            # Cierre de ventana durante la pausa: re-emitimos QUIT y salimos
            if self.resultado == "SALIR":
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return "SALIR"

        return None

    def _menu_puntuaciones(self):
        """Pantalla de puntuaciones"""
        # Espera un clic para volver
        fondo = self.rm.get_image("imagen_fondo1")
        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.estado = "PRINCIPAL"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))

        # Título
        txt_titulo = self.font_titulo.render("Puntuaciones", True, (255, 255, 255))
        self.pantalla.blit(txt_titulo, txt_titulo.get_rect(center=(300, 100)))

        # Listado de puntos
        y_offset = 180
        if puntuaciones_top:
            for i, (nombre, puntuacion) in enumerate(puntuaciones_top, start=1):
                texto = f"{i}. {nombre}: {puntuacion}"
                surf = self.font_estandar.render(texto, True, (255, 255, 255))
                self.pantalla.blit(surf, (130, y_offset + i * 45))
        else:
            aviso = self.font_estandar.render("No hay puntuaciones aún", True, (200, 200, 200))
            self.pantalla.blit(aviso, aviso.get_rect(center=(300, 400)))

        # Mensaje de salida
        txt_salir = self.font_estandar.render("Clic para volver", True, (150, 150, 150))
        self.pantalla.blit(txt_salir, txt_salir.get_rect(center=(300, 750)))

        pygame.display.flip()
