import time

import pygame
import pygame_gui
from juego import configuracion
from ui.boton import Boton


class MenuManager:
    """
    Clase principal para gestionar las pantallas del menú (Estado).
    """

    def __init__(self, pantalla, resource_manager, audio_manager, sistema_clasificacion):
        self.pantalla = pantalla
        self.rm = resource_manager
        self.am = audio_manager
        self.clasificacion = sistema_clasificacion
        self.font_titulo = pygame.font.Font(None, 76)
        self.font_estandar = pygame.font.Font(None, 36)
        self.opciones_cargadas = False

        # Estado inicial
        self.estado = "PRINCIPAL"  # Posibles: PRINCIPAL, OPCIONES, PUNTUACIONES
        self.ejecutando = True

        # Cargar config inicial
        self.vol_musica, self.vol_efectos = configuracion.cargar_configuracion()
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
        """Bucle principal del menú. Controla el flujo entre pantallas."""
        self._preparar_musica()  # Solo activamos la música aquí, al lanzar el menú completo
        clock = pygame.time.Clock()
        while self.ejecutando:
            if self.estado == "PRINCIPAL":
                self._menu_principal()
            elif self.estado == "OPCIONES":
                self._menu_opciones()
            elif self.estado == "PUNTUACIONES":
                self._menu_puntuaciones()

            clock.tick(60)

    def _menu_principal(self):
        pygame.display.set_caption("Galactic Guardian - Menú")
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_jugar.clic_en_boton(event.pos):
                    self._lanzar_juego()
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
        self.ui_manager = pygame_gui.UIManager((600, 800))

        # Sliders
        self.slider_musica = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 150), (500, 50)),
            start_value=self.vol_musica, value_range=(0, 1), manager=self.ui_manager
        )
        self.slider_efectos = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 250), (500, 50)),
            start_value=self.vol_efectos, value_range=(0, 1), manager=self.ui_manager
        )

        # Botones
        self.btn_guardar = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 350), (200, 50)), text='Guardar', manager=self.ui_manager
        )
        self.btn_volver = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((350, 350), (200, 50)), text='Volver', manager=self.ui_manager
        )
        self.opciones_cargadas = True

    def _menu_opciones(self):
        """Lógica de la pantalla de opciones usando pygame_gui."""
        # Solo inicializamos la UI si acabamos de entrar al estado
        if not hasattr(self, 'opciones_cargadas') or not self.opciones_cargadas:
            self._inicializar_interfaz_opciones()

        time_delta = pygame.time.Clock().tick(60) / 1000.0
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False

            # Gestión de eventos de la UI
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.slider_musica:
                        self.vol_musica = event.value
                        # Actualizamos el volumen de toda la música
                        self.am.actualizar_volumen_musica(self.vol_musica)
                    elif event.ui_element == self.slider_efectos:
                        self.vol_efectos = event.value
                        # Actualizamos el volumen de TODOS los efectos
                        self.am.actualizar_volumen_efectos(self.vol_efectos)
                        # Lógica de feedback continuo
                        ahora = time.time()
                        if not self.sonido_reproduciendose or ahora >= self.tiempo_final_reproduccion:
                            # Reproducimos un sonido de prueba
                            sonido_test = self.rm.get_sound("laser_gun")
                            if sonido_test:
                                self.sonido_reproduciendose = True
                                sonido_test.play()
                                # Calculamos cuándo terminará este sonido para permitir el siguiente
                                self.tiempo_final_reproduccion = ahora + sonido_test.get_length()

                elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.btn_guardar:
                        configuracion.guardar_configuracion(self.vol_musica, self.vol_efectos)
                        self.opciones_cargadas = False # Limpiar para la próxima vez
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
        """Muestra las opciones y retorna el control cuando se pulsa Guardar o Volver."""
        self.estado = "OPCIONES"
        self.opciones_cargadas = False  # Forzamos la carga de la UI
        clock = pygame.time.Clock()

        bucle_opciones = True
        while bucle_opciones:
            self._menu_opciones()

            # Condición de salida: si el estado cambia a PRINCIPAL, significa que el usuario pulsó Guardar o Volver.
            if self.estado == "PRINCIPAL":
                bucle_opciones = False

            # Si el usuario cierra la ventana (X)
            for _ in pygame.event.get(pygame.QUIT):
                pygame.quit()
                exit()

            clock.tick(60)


    def _menu_puntuaciones(self):
        """Pantalla de puntuaciones"""
        # Espera un clic para volver
        fondo = self.rm.get_image("imagen_fondo1")
        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
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

    def _lanzar_juego(self):
        from juego.juego_principal import Juego
        self.am.detener_musica("skyfire_theme")

        juego = Juego(self.pantalla, self.vol_musica, self.vol_efectos, self.clasificacion, self.rm)
        juego.ejecutar()

        # Al volver del juego, restauramos música y estado
        self.estado = "PRINCIPAL"
        # Forzamos a que Pygame sepa que el sistema de video sigue activo
        pygame.display.set_mode((600, 800))
        self._preparar_musica()