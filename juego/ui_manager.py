import pygame


class UIManager:
    def __init__(self, juego):
        self.juego = juego
        self.fuente_pequena = pygame.font.SysFont(None, 24)
        self.fuente_media = pygame.font.SysFont(None, 36)

        # Colores consistentes
        self.colores_atributos = {
            "Ataque": (255, 0, 0),
            "Vel. Ataque": (0, 255, 0),
            "Velocidad": (0, 0, 255)
        }

    def dibujar_interfaz(self, pantalla):
        """Coordina el dibujo de todos los elementos de la UI."""
        self._mostrar_estadisticas(pantalla)
        self._dibujar_barras_jugador(pantalla)
        if self.juego.jefe is not None:
            self._dibujar_barra_salud_jefe(pantalla)
        self._mostrar_fps(pantalla)

    def _mostrar_estadisticas(self, pantalla):
        color = (128, 128, 128) if self.juego.pausado else (255, 255, 255)

        # Vidas y Puntuación
        self._dibujar_texto(pantalla, f"Vidas: {self.juego.jugador.vidas}", (10, 10), color)
        self._dibujar_texto(pantalla, f"Puntuación: {self.juego.puntuacion}", (10, 40), color)

        # Atributos con barras
        self._dibujar_atributo(pantalla, "Ataque", self.juego.jugador.danio,
                               self.juego.jugador.danio_maximo, (10, 70), self.colores_atributos["Ataque"])

        # Cálculo de cadencia (puedes mover esta lógica al jugador luego)
        cadencia_val = round(1 / (self.juego.jugador.cadencia_disparo / 1000), 2)
        cadencia_max = round(1 / (self.juego.jugador.cadencia_disparo_maxima / 1000), 2)
        self._dibujar_atributo(pantalla, "Vel. Ataque", cadencia_val, cadencia_max, (10, 120),
                               self.colores_atributos["Vel. Ataque"])

        self._dibujar_atributo(pantalla, "Velocidad", self.juego.jugador.velocidad,
                               self.juego.jugador.CONFIG["vel_max"], (10, 170), self.colores_atributos["Velocidad"])

    def _dibujar_barras_jugador(self, pantalla):
        """Dibuja las mini-barras de salud bajo la nave."""
        barra_x = self.juego.jugador.rect.centerx - 25
        barra_y = self.juego.jugador.rect.bottom + 10

        for i in range(self.juego.jugador.salud_maxima):
            color = (0, 255, 0) if i < self.juego.jugador.salud else (150, 150, 150)
            pygame.draw.rect(pantalla, color, (barra_x + i * 10, barra_y, 8, 10))

        # Borde exterior
        rect_borde = pygame.Rect(barra_x, barra_y, self.juego.jugador.salud_maxima * 10, 10)
        pygame.draw.rect(pantalla, (255, 255, 255), rect_borde, 1)

    def _dibujar_barra_salud_jefe(self, pantalla):
        jefe = self.juego.jefe
        # Posición fija en la parte superior central
        ancho_total = 400
        barra_x = (self.juego.pantalla_ancho - ancho_total) // 2
        barra_y = 50

        ancho_actual = ancho_total * (max(0, jefe.salud) / jefe.salud_maxima)

        # Dibujar nombre del jefe arriba de la barra
        texto_jefe = self.fuente_pequena.render("JEFE", True, (255, 255, 255))
        pantalla.blit(texto_jefe, (barra_x, barra_y - 20))

        # Fondo rojo (salud actual) y borde blanco
        pygame.draw.rect(pantalla, (255, 0, 0), (barra_x, barra_y, ancho_actual, 15))
        pygame.draw.rect(pantalla, (255, 255, 255), (barra_x, barra_y, ancho_total, 15), 1)

    def _dibujar_atributo(self, pantalla, nombre, valor, maximo, pos, color):
        texto = self.fuente_pequena.render(f"{nombre}: {valor}", True, (255, 255, 255))
        pantalla.blit(texto, pos)

        ancho_barra = 100
        incremento = ancho_barra / float(maximo)

        # Barra de fondo/borde
        pygame.draw.rect(pantalla, (255, 255, 255), (pos[0], pos[1] + 20, ancho_barra, 10), 1)
        # Relleno
        pygame.draw.rect(pantalla, color, (pos[0], pos[1] + 20, valor * incremento, 10))

        # Divisiones visuales
        for i in range(int(maximo) + 1):
            x = pos[0] + i * incremento
            pygame.draw.line(pantalla, (255, 255, 255), (x, pos[1] + 21), (x, pos[1] + 29), 1)

    def _mostrar_fps(self, pantalla):
        fps = int(self.juego.reloj.get_fps())
        color = (128, 128, 128) if self.juego.pausado else (255, 255, 255)
        texto = self.fuente_pequena.render(f"FPS: {fps}", True, color)
        pantalla.blit(texto, (self.juego.pantalla_ancho - texto.get_width() - 10, 10))

    def _dibujar_texto(self, pantalla, texto, pos, color):
        surface = self.fuente_pequena.render(texto, True, color)
        pantalla.blit(surface, pos)

    def dibujar_confirmacion_salida(self, pantalla, boton_si, boton_no):
        """Dibuja el cuadro de diálogo de confirmación."""
        # 1. Fondo oscuro traslúcido
        fondo_oscuro = pygame.Surface((self.juego.pantalla_ancho, self.juego.pantalla_alto))
        fondo_oscuro.set_alpha(200)
        fondo_oscuro.fill((0, 0, 0))
        pantalla.blit(fondo_oscuro, (0, 0))

        # 2. Cuadro de diálogo
        rect_dialogo = pygame.Rect(50, 200, 500, 200)
        pygame.draw.rect(pantalla, (255, 255, 255), rect_dialogo)

        # 3. Texto
        texto = self.fuente_media.render("¿Estás seguro de que deseas salir?", True, (0, 0, 0))
        texto_rect = texto.get_rect(center=(rect_dialogo.centerx, rect_dialogo.centery - 50))
        pantalla.blit(texto, texto_rect)

        # 4. Dibujar botones (que el manager recibe ya creados)
        boton_si.dibujar(pantalla, self.fuente_media)
        boton_no.dibujar(pantalla, self.fuente_media)

        pygame.display.flip()

    def dibujar_entrada_nombre(self, pantalla, nombre_actual):
        """Dibuja la interfaz para introducir el nombre en el Game Over."""
        # 1. Fondo (usamos el fondo del juego para consistencia)
        pantalla.blit(self.juego.background.img1, (0, 0))

        # 2. Capa oscura traslúcida para resaltar el texto
        overlay = pygame.Surface((self.juego.pantalla_ancho, self.juego.pantalla_alto))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        pantalla.blit(overlay, (0, 0))

        # 3. Textos
        titulo = self.fuente_media.render("¡NUEVA PUNTUACIÓN TOP!", True, (255, 215, 0))  # Dorado
        instrucciones = self.fuente_pequena.render("Introduce tu nombre y pulsa ENTER:", True, (200, 200, 200))
        nombre_surface = self.fuente_media.render(nombre_actual + "_", True, (255, 255, 255))

        # Posicionamiento centrado
        cx, cy = self.juego.pantalla_ancho // 2, self.juego.pantalla_alto // 2

        pantalla.blit(titulo, titulo.get_rect(center=(cx, cy - 60)))
        pantalla.blit(instrucciones, instrucciones.get_rect(center=(cx, cy - 20)))
        pantalla.blit(nombre_surface, nombre_surface.get_rect(center=(cx, cy + 40)))