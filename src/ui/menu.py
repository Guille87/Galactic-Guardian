import time

import pygame
import pygame_gui

from src.core import config, settings
from src.ui.components.button import Boton


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
        self.opciones_cargadas = False

        # Reloj único de la instancia (no crear uno nuevo por frame)
        self.clock = pygame.time.Clock()

        # Estado inicial
        self.estado = "PRINCIPAL"  # Posibles: PRINCIPAL, OPCIONES, PUNTUACIONES
        self.ejecutando = True
        self.resultado = None  # "JUGAR" | "SALIR"

        # Cargar config inicial
        self.vol_musica, self.vol_efectos = config.cargar_configuracion()
        self._crear_botones()

        # Control de feedback sonoro
        self.sonido_reproduciendose = False
        self.tiempo_final_reproduccion = 0

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
        self.opciones_cargadas = False

        self._preparar_musica()  # Solo activamos la música aquí, al lanzar el menú completo

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
        pygame.display.set_caption("Galactic Guardian - Menú")
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_jugar.clic_en_boton(event.pos):
                    self.am.detener_musica("skyfire_theme")
                    self.ejecutando = False
                    self.resultado = "JUGAR"
                elif self.btn_opciones.clic_en_boton(event.pos):
                    self.estado = "OPCIONES"
                elif self.btn_puntos.clic_en_boton(event.pos):
                    self.estado = "PUNTUACIONES"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        titulo = self.font_titulo.render("Galactic Guardian", True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(300, 150)))

        self.btn_jugar.dibujar(self.pantalla, self.font_estandar)
        self.btn_opciones.dibujar(self.pantalla, self.font_estandar)
        self.btn_puntos.dibujar(self.pantalla, self.font_estandar)
        pygame.display.flip()

    def _inicializar_interfaz_opciones(self):
        """Crea el UIManager y los elementos de la interfaz solo una vez."""
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
        self.opciones_cargadas = True

    def _feedback_sonoro_efectos(self):
        """Reproduce un sonido de prueba al mover el slider de efectos (con anti-spam)."""
        ahora = time.time()
        if not self.sonido_reproduciendose or ahora >= self.tiempo_final_reproduccion:
            sonido_test = self.rm.get_sound("laser_gun")
            if sonido_test:
                self.sonido_reproduciendose = True
                sonido_test.play()
                self.tiempo_final_reproduccion = ahora + sonido_test.get_length()

    def _menu_opciones(self, time_delta):
        """Lógica de la pantalla de opciones usando pygame_gui."""
        # Solo inicializamos la UI si acabamos de entrar al estado
        if not self.opciones_cargadas:
            self._inicializar_interfaz_opciones()

        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.estado = "PRINCIPAL"
                self.resultado = "SALIR"

            # --- Eventos de pygame_gui (API 0.6+: cada evento con su propio type) ---
            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_element == self.slider_musica:
                    self.vol_musica = event.value
                    self.am.actualizar_volumen_musica(self.vol_musica)
                elif event.ui_element == self.slider_efectos:
                    self.vol_efectos = event.value
                    self.am.actualizar_volumen_efectos(self.vol_efectos)
                    self._feedback_sonoro_efectos()

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.btn_guardar:
                    config.guardar_configuracion(self.vol_musica, self.vol_efectos)
                    self.opciones_cargadas = False  # Limpiar para la próxima vez
                    self.estado = "PRINCIPAL"
                elif event.ui_element == self.btn_volver:
                    self.opciones_cargadas = False
                    self.estado = "PRINCIPAL"

            self.ui_manager.process_events(event)

        # Dibujado
        self.ui_manager.update(time_delta)
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
        self.estado = "OPCIONES"
        self.opciones_cargadas = False  # Forzamos la carga de la UI

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
