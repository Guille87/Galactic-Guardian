import pygame
from src.core import settings
from src.ui.components.button import Boton


class RenderManager:
    """Capa Vista: dibuja el estado de la partida. Recibe el `Juego` completo por
    diseño (necesita observarlo entero); solo escribe estado de UI, nunca de
    simulación. Ver auditoría, item 14."""

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
        # Pantallas propias que, como Game Over, congelan la partida
        # (`pausado = True`) pero no usan el camino rápido de pausa ni dibujan
        # las entidades del mundo.
        j = self.juego
        overlay_propio = (j.estado_game_over or j.pidiendo_nombre or j.estado_nivel_completado
                          or j.mostrando_seleccion_nivel or j.estado_victoria_final)

        # --- Camino rápido: PAUSA real (escena estática) ---
        pausa_real = j.pausado and not overlay_propio
        if pausa_real:
            self._renderizar_pausa()
            pygame.display.flip()
            return

        # Fuera de la pausa real: invalidamos el snapshot
        self._frame_pausa = None

        # 1. Fondo
        self.juego.background.draw(self.pantalla)

        # 2. Entidades del mundo (solo si no hay una pantalla propia encima)
        if not overlay_propio:
            self._dibujar_entidades()
            self.pantalla.blit(self.juego.jugador.image, self.juego.jugador.rect)
            if self.juego.debug_hitboxes:
                self._dibujar_hitboxes()
            self.juego.ui_manager.dibujar_interfaz(self.pantalla)

        # 3. Overlays superiores
        if j.pidiendo_nombre:
            self.juego.ui_manager.dibujar_entrada_nombre(self.pantalla, self.juego.nombre_entrada)
        elif j.estado_game_over:
            self._dibujar_pantalla_game_over()
        elif j.estado_nivel_completado:
            self._dibujar_pantalla_nivel_completado()
        elif j.mostrando_seleccion_nivel:
            self._dibujar_pantalla_seleccion_nivel()
        elif j.estado_victoria_final:
            self._dibujar_pantalla_victoria_final()

        pygame.display.flip()

    # ------------------------------------------------------------------ PAUSA
    def _renderizar_pausa(self):
        """Dibuja la pausa reutilizando un snapshot desaturado de la escena."""
        if self._frame_pausa is None:
            self._frame_pausa = self.pantalla.copy()
            self._frame_pausa.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_MULT)

        self.pantalla.blit(self._frame_pausa, (0, 0))
        # Título + 3 botones como un bloque centrado en la pantalla (antes el
        # título estaba en el centro exacto y los botones colgaban por debajo,
        # descuadrando el conjunto hacia abajo cada vez que se añadía uno).
        self._mostrar_texto_centralizado("Juego Pausado", (255, 255, 255), desplazamiento_y=-99)
        self._dibujar_botones_pausa()

    def _dibujar_botones_pausa(self):
        # Se crean una única vez y se cachean en el juego
        if self.juego.boton_reanudar is None:
            centro_x = self.juego.pantalla_ancho // 2
            centro_y = self.juego.pantalla_alto // 2
            self.juego.boton_reanudar = Boton("Reanudar", (0, 255, 0, 150), (255, 255, 255),
                                              centro_x, centro_y - 33, 150, 50, radio_borde=10)
            self.juego.boton_opciones = Boton("Opciones", (0, 255, 255, 150), (255, 255, 255),
                                              centro_x, centro_y + 33, 150, 50, radio_borde=10)
            self.juego.boton_salir = Boton("Salir", (255, 0, 0, 150), (255, 255, 255),
                                           centro_x, centro_y + 99, 150, 50, radio_borde=10)

        self.juego.boton_reanudar.dibujar(self.pantalla, self.font_botones)
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

    # ------------------------------------------------------------ CAMPAÑA
    def _dibujar_estadisticas(self, lineas, y_inicial, color=(255, 255, 255)):
        cx = self.juego.pantalla_ancho // 2
        y = y_inicial
        for linea in lineas:
            surf = self.font_botones.render(linea, True, color)
            self.pantalla.blit(surf, surf.get_rect(center=(cx, y)))
            y += 40
        return y

    def _dibujar_pantalla_nivel_completado(self):
        """Tras derrotar al jefe de un nivel que no es el último."""
        j = self.juego
        self.pantalla.blit(j.background.img1, (0, 0))
        cx = j.pantalla_ancho // 2

        titulo = self.font_game_over.render(f"NIVEL {j.nivel} COMPLETADO", True, (255, 215, 0))
        self.pantalla.blit(titulo, titulo.get_rect(center=(cx, 180)))

        self._dibujar_estadisticas([
            f"Puntuación: {j.puntuacion}",
            f"Enemigos destruidos: {j.enemigos_eliminados_nivel}",
            f"Tiempo: {j.tiempo_juego / 1000:.1f} s",
        ], 280)

        if j.boton_continuar is None:
            j.boton_continuar = Boton("Continuar", (0, 255, 0, 150), (255, 255, 255),
                                      cx, 480, 220, 50, radio_borde=10)
            j.boton_elegir_nivel = Boton("Elegir nivel", (0, 150, 255, 150), (255, 255, 255),
                                         cx, 550, 220, 50, radio_borde=10)
        j.boton_continuar.dibujar(self.pantalla, self.font_botones)
        j.boton_elegir_nivel.dibujar(self.pantalla, self.font_botones)

    def _dibujar_pantalla_seleccion_nivel(self):
        """Elegir nivel: los ya superados en esta partida, más el siguiente
        (el mismo al que llevaría "Continuar", por si el jugador prefiere
        seguir avanzando en vez de rejugar uno anterior)."""
        j = self.juego
        self.pantalla.blit(j.background.img1, (0, 0))
        cx = j.pantalla_ancho // 2

        titulo = self.font_game_over.render("ELEGIR NIVEL", True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(cx, 150)))

        nivel_maximo_listado = min(j.nivel + 1, settings.NIVEL_MAX)
        if j.botones_seleccion_nivel is None or len(j.botones_seleccion_nivel) != nivel_maximo_listado:
            j.botones_seleccion_nivel = []
            y = 250
            for n in range(1, nivel_maximo_listado + 1):
                etiqueta = f"Nivel {n}" + (" (siguiente)" if n == j.nivel + 1 else "")
                boton = Boton(etiqueta, (0, 150, 255, 150), (255, 255, 255),
                             cx, y, 260, 50, radio_borde=10)
                j.botones_seleccion_nivel.append((n, boton))
                y += 70

        for _, boton in j.botones_seleccion_nivel:
            boton.dibujar(self.pantalla, self.font_botones)

    def _dibujar_pantalla_victoria_final(self):
        """Tras derrotar al jefe del último nivel de la campaña."""
        j = self.juego
        self.pantalla.blit(j.background.img1, (0, 0))
        cx = j.pantalla_ancho // 2

        titulo = self.font_game_over.render("¡VICTORIA!", True, (255, 215, 0))
        self.pantalla.blit(titulo, titulo.get_rect(center=(cx, 150)))
        subtitulo = self.font_botones.render("Has completado Galactic Guardian", True, (255, 255, 255))
        self.pantalla.blit(subtitulo, subtitulo.get_rect(center=(cx, 210)))

        self._dibujar_estadisticas([
            f"Puntuación final: {j.puntuacion}",
            f"Nivel: {j.nivel}",
        ], 280)

        if j.boton_reintentar_final is None:
            j.boton_reintentar_final = Boton("Jugar de nuevo", (255, 0, 0, 128), (255, 255, 255),
                                             cx, 450, 220, 50, radio_borde=10)
            j.boton_menu_final = Boton("Menú", (255, 0, 255, 128), (255, 255, 255),
                                       cx, 520, 220, 50, radio_borde=10)
        j.boton_reintentar_final.dibujar(self.pantalla, self.font_botones)
        j.boton_menu_final.dibujar(self.pantalla, self.font_botones)

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
    def _mostrar_texto_centralizado(self, texto, color, desplazamiento_y=0):
        texto_surface = self.font_pausa.render(texto, True, color)
        texto_rect = texto_surface.get_rect(
            center=(self.juego.pantalla_ancho // 2, self.juego.pantalla_alto // 2 + desplazamiento_y))
        self.pantalla.blit(texto_surface, texto_rect)
