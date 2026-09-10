import pygame
from src.ui.components.button import Boton


class RenderManager:
    def __init__(self, juego):
        self.juego = juego
        self.pantalla = juego.pantalla
        self.font_pausa = pygame.font.SysFont(None, 48)
        self.font_botones = pygame.font.SysFont(None, 30)
        self.font_game_over = pygame.font.SysFont(None, 72)
        self.font_debug = pygame.font.SysFont(None, 20)

        # Snapshot desaturado de la pausa (se genera una sola vez por pausa)
        self._frame_pausa = None

    def renderizar_todo(self):
        """Función principal que orquesta el dibujo de cada frame."""
        # --- Camino rápido: PAUSA real (escena estática) ---
        # Game Over / entrada de nombre también ponen juego.pausado = True para
        # congelar la lógica, pero tienen su propio overlay más abajo.
        pausa_real = (self.juego.pausado
                      and not self.juego.estado_game_over
                      and not self.juego.pidiendo_nombre)
        if pausa_real:
            self._renderizar_pausa()
            pygame.display.flip()
            return

        # Fuera de la pausa real: invalidamos el snapshot
        self._frame_pausa = None

        # 1. Fondo
        self.juego.background.draw(self.pantalla)

        # 2. Entidades del mundo (solo si no es Game Over / entrada de nombre)
        if not self.juego.estado_game_over and not self.juego.pidiendo_nombre:
            self._dibujar_entidades()
            self.pantalla.blit(self.juego.jugador.image, self.juego.jugador.rect)
            if self.juego.debug_hitboxes:
                self._dibujar_hitboxes()
            self.juego.ui_manager.dibujar_interfaz(self.pantalla)

        # 3. Overlays superiores
        if self.juego.pidiendo_nombre:
            self.juego.ui_manager.dibujar_entrada_nombre(self.pantalla, self.juego.nombre_entrada)
        elif self.juego.estado_game_over:
            self._dibujar_pantalla_game_over()

        pygame.display.flip()

    # ------------------------------------------------------------------ PAUSA
    def _renderizar_pausa(self):
        """Dibuja la pausa reutilizando un snapshot desaturado de la escena."""
        if self._frame_pausa is None:
            self._frame_pausa = self.pantalla.copy()
            self._frame_pausa.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_MULT)

        self.pantalla.blit(self._frame_pausa, (0, 0))
        self._mostrar_texto_centralizado("Juego Pausado", (255, 255, 255))
        self._dibujar_botones_pausa()

    def _dibujar_botones_pausa(self):
        # Se crean una única vez y se cachean en el juego
        if self.juego.boton_opciones is None:
            centro_x = self.juego.pantalla_ancho // 2
            y_opciones = self.juego.pantalla_alto // 2 + 50
            y_salir = self.juego.pantalla_alto // 2 + 120
            self.juego.boton_opciones = Boton("Opciones", (0, 255, 255, 150), (255, 255, 255),
                                              centro_x, y_opciones, 150, 50, radio_borde=10)
            self.juego.boton_salir = Boton("Salir", (255, 0, 0, 150), (255, 255, 255),
                                           centro_x, y_salir, 150, 50, radio_borde=10)

        self.juego.boton_opciones.dibujar(self.pantalla, self.font_botones)
        self.juego.boton_salir.dibujar(self.pantalla, self.font_botones)

    # -------------------------------------------------------------- GAME OVER
    def _dibujar_pantalla_game_over(self):
        """Dibuja la UI de fin de juego."""
        self.pantalla.blit(self.juego.background.img1, (0, 0))

        texto_surf = self.font_game_over.render("Game Over", True, (255, 255, 255))
        texto_rect = texto_surf.get_rect(center=(self.juego.pantalla_ancho // 2,
                                                 self.juego.pantalla_alto // 2 - 150))
        self.pantalla.blit(texto_surf, texto_rect)

        # Botones creados una sola vez y cacheados
        if self.juego.boton_reintentar is None:
            centro_x = self.juego.pantalla_ancho // 2
            self.juego.boton_reintentar = Boton("Reintentar", (255, 0, 0, 128), (255, 255, 255),
                                                centro_x, 400, 200, 50, radio_borde=10)
            self.juego.boton_salir_post = Boton("Salir", (255, 0, 255, 128), (255, 255, 255),
                                                centro_x, 470, 200, 50, radio_borde=10)

        self.juego.boton_reintentar.dibujar(self.pantalla, self.font_botones)
        self.juego.boton_salir_post.dibujar(self.pantalla, self.font_botones)

    # ------------------------------------------------------------- ENTIDADES
    def _dibujar_entidades(self):
        """Dibuja los grupos de sprites en orden de capas (de atrás a delante)."""
        em = self.juego.entity_manager
        for grupo in (em.efectos, em.items, em.balas, em.balas_enemigo, em.enemigos):
            grupo.draw(self.pantalla)

    def _dibujar_hitboxes(self):
        """Overlay de depuración (tecla F1): círculos de colisión reales."""
        em = self.juego.entity_manager

        def circulo(sprite, color):
            r = int(getattr(sprite, "radius", 0))
            if r > 0:
                pygame.draw.circle(self.pantalla, color, sprite.rect.center, r, 1)

        circulo(self.juego.jugador, (0, 255, 0))
        for e in em.enemigos:
            circulo(e, (255, 80, 80))
        for b in em.balas:
            circulo(b, (120, 200, 255))
        for b in em.balas_enemigo:
            circulo(b, (255, 180, 80))

        # Aviso: cómo salir del modo debug (por si se pulsó F1 sin querer)
        aviso = self.font_debug.render("F1: modo debug ACTIVADO — pulsa F1 para ocultarlo", True, (0, 255, 0))
        self.pantalla.blit(aviso, (10, self.juego.pantalla_alto - aviso.get_height() - 8))

    # ---------------------------------------------------------------- HELPERS
    def _mostrar_texto_centralizado(self, texto, color):
        texto_surface = self.font_pausa.render(texto, True, color)
        texto_rect = texto_surface.get_rect(center=(self.juego.pantalla_ancho // 2, self.juego.pantalla_alto // 2))
        self.pantalla.blit(texto_surface, texto_rect)
