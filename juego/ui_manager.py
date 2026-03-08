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
                               self.juego.jugador.DANIO_MAXIMO, (10, 70), self.colores_atributos["Ataque"])

        # Cálculo de cadencia (puedes mover esta lógica al jugador luego)
        cadencia_val = round(1 / (self.juego.jugador.cadencia_disparo / 1000), 2)
        cadencia_max = round(1 / (self.juego.jugador.CADENCIA_DISPARO_MAXIMA / 1000), 2)
        self._dibujar_atributo(pantalla, "Vel. Ataque", cadencia_val, cadencia_max, (10, 120),
                               self.colores_atributos["Vel. Ataque"])

        self._dibujar_atributo(pantalla, "Velocidad", self.juego.jugador.velocidad,
                               self.juego.jugador.VELOCIDAD_MAXIMA, (10, 170), self.colores_atributos["Velocidad"])

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
        barra_x = jefe.rect.centerx - jefe.rect.width // 2
        barra_y = jefe.rect.bottom - 210

        ancho_total = jefe.rect.width
        ancho_actual = ancho_total * (jefe.salud / jefe.salud_maxima)

        # Fondo rojo y borde blanco
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