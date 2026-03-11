import pygame


class UIManager:
    def __init__(self, juego):
        self.juego = juego
        self.fuente_pequena = pygame.font.SysFont(None, 22, bold=True)
        self.fuente_media = pygame.font.SysFont(None, 32, bold=True)

        # Colores y Configuración
        self.COLOR_TEXTO = (240, 240, 240)
        self.COLOR_BORDE = (200, 200, 200)
        self.COLOR_FONDO_BARRA = (40, 40, 40)

        # Colores consistentes
        self.COLORES_STATS = {
            "Ataque": (255, 0, 0),
            "Vel. Ataque": (0, 255, 0),
            "Velocidad": (0, 0, 255)
        }

    def dibujar_interfaz(self, pantalla):
        """Coordina el dibujo de todos los elementos de la UI."""
        self._dibujar_hud_basico(pantalla)
        self._dibujar_barras_atributos(pantalla)
        self._dibujar_indicador_salud_nave(pantalla)

        if self.juego.jefe:
            self._dibujar_barra_salud_jefe(pantalla)

        self._mostrar_fps(pantalla)

    def _dibujar_hud_basico(self, pantalla):
        """Dibuja puntuación y vidas en las esquinas."""
        color = (150, 150, 150) if self.juego.pausado else self.COLOR_TEXTO

        # Puntuación arriba a la derecha para que no estorbe a los stats
        txt_puntos = self.fuente_media.render(f"{self.juego.puntuacion:06d}", True, color)
        pantalla.blit(txt_puntos, (self.juego.pantalla_ancho - txt_puntos.get_width() - 20, 40))

        # Vidas arriba a la izquierda
        txt_vidas = self.fuente_pequena.render(f"VIDAS: {self.juego.jugador.vidas}", True, color)
        pantalla.blit(txt_vidas, (20, 20))

    def _dibujar_barras_atributos(self, pantalla):
        """Dibuja los paneles de estadísticas del jugador."""
        jugador = self.juego.jugador
        # Agrupamos los datos para iterar (Evita repetir código de dibujo)
        # Nota: La cadencia ahora se pide al jugador, él sabe cómo calcularla
        stats = [
            ("Ataque", jugador.danio, jugador.danio_maximo),
            ("Vel. Ataque", jugador.obtener_cadencia_visual(), jugador.obtener_cadencia_max_visual()),
            ("Velocidad", jugador.velocidad, jugador.CONFIG["vel_max"])
        ]

        start_y = 60
        for nombre, val, max_val in stats:
            self._dibujar_barra_con_etiqueta(
                pantalla, nombre, val, max_val,
                (20, start_y), self.COLORES_STATS[nombre]
            )
            start_y += 45

    def _dibujar_barra_con_etiqueta(self, pantalla, etiqueta, valor, maximo, pos, color):
        """Dibuja una barra de progreso estandarizada con su nombre."""
        # Etiqueta
        txt = self.fuente_pequena.render(etiqueta, True, self.COLOR_TEXTO)
        pantalla.blit(txt, pos)

        # Dimensiones de la barra
        bx, by = pos[0], pos[1] + 22
        ancho, alto = 120, 8

        # Dibujo
        pygame.draw.rect(pantalla, self.COLOR_FONDO_BARRA, (bx, by, ancho, alto))
        # Calculamos el llenado (asegurando que no sea mayor al 100%)
        llenado = (min(valor, maximo) / maximo) * ancho
        pygame.draw.rect(pantalla, color, (bx, by, llenado, alto))
        pygame.draw.rect(pantalla, self.COLOR_BORDE, (bx, by, ancho, alto), 1)

    def _dibujar_indicador_salud_nave(self, pantalla):
        """Muestra puntos de salud directamente bajo la nave del jugador."""
        jugador = self.juego.jugador
        # Centramos los puntos bajo la nave
        ancho_punto = 8
        espacio = 2
        ancho_total = (jugador.salud_maxima * (ancho_punto + espacio)) - espacio

        x_inicio = jugador.rect.centerx - (ancho_total // 2)
        y = jugador.rect.bottom + 12

        for i in range(jugador.salud_maxima):
            color = (0, 255, 100) if i < jugador.salud else (60, 60, 60)
            pygame.draw.rect(pantalla, color, (x_inicio + i * (ancho_punto + espacio), y, ancho_punto, 6))

    def _dibujar_barra_salud_jefe(self, pantalla):
        """Barra de salud cinemática para el jefe."""
        jefe = self.juego.jefe
        ancho_pantalla = self.juego.pantalla_ancho

        # Barra grande arriba
        ancho_barra = ancho_pantalla - 200
        x = (ancho_pantalla - ancho_barra) // 2
        y = 30

        porcentaje = max(0, jefe.salud) / jefe.salud_maxima

        # Nombre del Jefe con sombra para legibilidad
        txt_nombre = self.fuente_media.render("UNIDAD DE COMBATE PESADA", True, (255, 50, 50))
        pantalla.blit(txt_nombre, (x, y - 25))

        # Fondo y Salud
        pygame.draw.rect(pantalla, (20, 20, 20), (x, y, ancho_barra, 12))
        pygame.draw.rect(pantalla, (255, 0, 0), (x, y, ancho_barra * porcentaje, 12))
        pygame.draw.rect(pantalla, (255, 255, 255), (x, y, ancho_barra, 12), 1)

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
        fps = str(int(self.juego.reloj.get_fps()))
        txt = self.fuente_pequena.render(f"FPS: {fps}", True, (100, 100, 100))
        pantalla.blit(txt, (self.juego.pantalla_ancho - txt.get_width() - 10, 5))

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