import math

import pygame

from src.core import preferencias, settings
from src.core.i18n import t


class UIManager:
    """Capa Vista: HUD y overlays de texto. Recibe el `Juego` completo por diseño
    (solo lo lee); ver auditoría, item 14."""

    SALUD_BAJA = 0.3                 # por debajo de esta fracción la salud se pinta en rojo
    COLOR_SALUD_BAJA = (255, 90, 90)

    def __init__(self, juego):
        self.juego = juego
        self.fuente_pequena = pygame.font.SysFont(None, 22, bold=True)
        self.fuente_media = pygame.font.SysFont(None, 32, bold=True)

        # Colores y Configuración
        self.COLOR_TEXTO = (240, 240, 240)
        self.COLOR_BORDE = (200, 200, 200)
        self.COLOR_FONDO_BARRA = (40, 40, 40)
        self.COLOR_COMBO = (255, 215, 0)

        # Colores consistentes
        self.COLORES_STATS = {
            "ataque": (255, 0, 0),
            "vel_ataque": (0, 255, 0),
            "velocidad": (0, 0, 255)
        }

    def dibujar_interfaz(self, pantalla):
        """Coordina el dibujo de todos los elementos de la UI."""
        self._dibujar_hud_basico(pantalla)
        self._dibujar_barras_atributos(pantalla)
        self._dibujar_indicador_salud_nave(pantalla)

        if self.juego.jefe:
            self._dibujar_barra_salud_jefe(pantalla)

        if preferencias.mostrar_fps():
            self._mostrar_fps(pantalla)
        if settings.DEBUG:
            self._mostrar_tiempo_juego(pantalla)

    def _dibujar_hud_basico(self, pantalla):
        """Dibuja puntuación y vidas en las esquinas."""
        color = (150, 150, 150) if self.juego.pausado else self.COLOR_TEXTO

        # Puntuación arriba a la derecha para que no estorbe a los stats
        txt_puntos = self.fuente_media.render(f"{self.juego.puntuacion:06d}", True, color)
        pantalla.blit(txt_puntos, (self.juego.pantalla_ancho - txt_puntos.get_width() - 20, 40))

        # Bajo la puntuación, de arriba abajo: oleada en curso (sin fin) y combo
        y = 70
        if self.juego.modo == settings.MODO_SIN_FIN:
            txt_oleada = self.fuente_pequena.render(t("hud.oleada", n=self.juego.nivel), True, color)
            pantalla.blit(txt_oleada, (self.juego.pantalla_ancho - txt_oleada.get_width() - 20, y))
            y += 22
        self._dibujar_combo(pantalla, y, pausado=self.juego.pausado)

        # Vidas arriba a la izquierda
        txt_vidas = self.fuente_pequena.render(t("hud.vidas", n=self.juego.jugador.vidas), True, color)
        pantalla.blit(txt_vidas, (20, 20))

        # Salud en cifras, bajo las vidas: rojo cuando queda poca
        jugador = self.juego.jugador
        salud = math.ceil(max(0, jugador.salud))
        if self.juego.pausado:
            color_salud = color
        elif salud <= jugador.salud_maxima * self.SALUD_BAJA:
            color_salud = self.COLOR_SALUD_BAJA
        else:
            color_salud = self.COLOR_TEXTO
        txt_salud = self.fuente_pequena.render(t("hud.salud", n=salud, max=jugador.salud_maxima), True, color_salud)
        pantalla.blit(txt_salud, (20, 38))

    def _dibujar_combo(self, pantalla, y, pausado):
        """"COMBO ×n" con una barrita hacia el siguiente escalón. En ×1 no se
        dibuja nada, para no ensuciar la pantalla."""
        combo = self.juego.combo
        if combo.multiplicador <= 1:
            return
        color = (150, 150, 150) if pausado else self.COLOR_COMBO
        txt = self.fuente_pequena.render(t("hud.combo", n=combo.multiplicador), True, color)
        derecha = self.juego.pantalla_ancho - 20
        pantalla.blit(txt, (derecha - txt.get_width(), y))

        ancho, alto = 100, 6
        x, by = derecha - ancho, y + txt.get_height() + 2
        pygame.draw.rect(pantalla, self.COLOR_FONDO_BARRA, (x, by, ancho, alto))
        pygame.draw.rect(pantalla, color, (x, by, ancho * combo.progreso(), alto))
        pygame.draw.rect(pantalla, self.COLOR_BORDE, (x, by, ancho, alto), 1)

    def _dibujar_barras_atributos(self, pantalla):
        """Dibuja los paneles de estadísticas del jugador."""
        jugador = self.juego.jugador
        # Agrupamos los datos para iterar (Evita repetir código de dibujo)
        # Nota: La cadencia ahora se pide al jugador, él sabe cómo calcularla
        # `extra`: texto opcional solo-debug. En "Velocidad" mostramos los píxeles
        # realmente movidos el último frame (para detectar asimetrías de movimiento).
        vel_real = jugador._ultimo_desplazamiento.length() if hasattr(jugador, "_ultimo_desplazamiento") else 0.0
        stats = [
            ("ataque", jugador.danio, jugador.danio_maximo, None),
            ("vel_ataque", jugador.obtener_cadencia_visual(), jugador.obtener_cadencia_max_visual(), None),
            ("velocidad", jugador.velocidad, jugador.CONFIG["vel_max"], f"real {vel_real:.2f} px/frame"),
        ]

        start_y = 60
        for clave, val, max_val, extra in stats:
            self._dibujar_barra_con_etiqueta(
                pantalla, t(f"hud.{clave}"), val, max_val,
                (20, start_y), self.COLORES_STATS[clave], extra
            )
            start_y += 45

    def _dibujar_barra_con_etiqueta(self, pantalla, etiqueta, valor, maximo, pos, color, extra=None):
        """Dibuja una barra de progreso estandarizada con su nombre.

        En modo DEBUG (ejecución desde el IDE) añade el valor numérico y, si se
        pasa, un `extra` de diagnóstico.
        """
        if settings.DEBUG:
            texto = f"{etiqueta}: {valor:g}/{maximo:g}"      # `:g` quita ceros de más
            if extra:
                texto += f"  [{extra}]"
        else:
            texto = etiqueta
        txt = self.fuente_pequena.render(texto, True, self.COLOR_TEXTO)
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

    # Barra de salud bajo la nave: siempre del mismo ancho (más salud máxima no la alarga: con
    # el árbol entero eran 100 y se salía por los bordes), con marcas oscuras que la parten en
    # tramos de `SALUD_POR_MARCA` de salud como mucho `MARCAS_MAX` marcas, y siempre entera dentro
    # de la pantalla aunque la nave esté pegada al borde.
    ANCHO_BARRA_SALUD = 48
    SALUD_POR_MARCA = 10          # una marca oscura cada tantos puntos de salud...
    MARCAS_MAX = 4                # ...pero nunca más de tantas marcas
    MARGEN_BARRA_SALUD = 2        # separación mínima con el borde de la pantalla

    def _dibujar_indicador_salud_nave(self, pantalla):
        """Barra de salud directamente bajo la nave del jugador."""
        jugador = self.juego.jugador
        ancho = self.ANCHO_BARRA_SALUD
        x = jugador.rect.centerx - ancho // 2
        x = max(self.MARGEN_BARRA_SALUD, min(self.juego.pantalla_ancho - self.MARGEN_BARRA_SALUD - ancho, x))
        y = jugador.rect.bottom + 12
        alto = 6

        pygame.draw.rect(pantalla, (60, 60, 60), (x, y, ancho, alto))
        llenado = round(ancho * max(0, jugador.salud) / jugador.salud_maxima)
        pygame.draw.rect(pantalla, (0, 255, 100), (x, y, llenado, alto))
        # Marcas oscuras: una cada 10 de salud (lo que quita un impacto normal), hasta un máximo
        marcas = min(self.MARCAS_MAX, jugador.salud_maxima // self.SALUD_POR_MARCA - 1)
        tramos = marcas + 1
        for i in range(1, tramos):
            px = x + round(ancho * i / tramos)
            pygame.draw.line(pantalla, (20, 20, 20), (px, y), (px, y + alto - 1))

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
        txt_nombre = self.fuente_media.render(t("hud.jefe_nombre"), True, (255, 50, 50))
        pantalla.blit(txt_nombre, (x, y - 25))

        # Fondo y Salud
        pygame.draw.rect(pantalla, (20, 20, 20), (x, y, ancho_barra, 12))
        pygame.draw.rect(pantalla, (255, 0, 0), (x, y, ancho_barra * porcentaje, 12))
        pygame.draw.rect(pantalla, (255, 255, 255), (x, y, ancho_barra, 12), 1)

        # Vida en números (solo desarrollo)
        if settings.DEBUG:
            txt_hp = self.fuente_pequena.render(
                f"{max(0, int(jefe.salud))} / {jefe.salud_maxima}  (nivel {self.juego.nivel})",
                True, self.COLOR_TEXTO
            )
            pantalla.blit(txt_hp, (x, y + 16))

    def _mostrar_fps(self, pantalla):
        fps = str(int(self.juego.reloj.get_fps()))
        txt = self.fuente_pequena.render(f"FPS: {fps}", True, (100, 100, 100))
        pantalla.blit(txt, (self.juego.pantalla_ancho - txt.get_width() - 10, 5))

    def _mostrar_tiempo_juego(self, pantalla):
        """Reloj de juego (solo DEBUG): sube jugando, se detiene en pausa."""
        seg = self.juego.tiempo_juego / 1000
        txt = self.fuente_pequena.render(f"t: {seg:6.1f} s", True, (100, 100, 100))
        pantalla.blit(txt, (self.juego.pantalla_ancho - txt.get_width() - 10, 24))

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
        texto = self.fuente_media.render(t("hud.confirmar_salida"), True, (0, 0, 0))
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
        titulo = self.fuente_media.render(t("hud.nueva_puntuacion"), True, (255, 215, 0))  # Dorado
        instrucciones = self.fuente_pequena.render(t("hud.introduce_nombre"), True, (200, 200, 200))
        nombre_surface = self.fuente_media.render(nombre_actual + "_", True, (255, 255, 255))

        # Posicionamiento centrado
        cx, cy = self.juego.pantalla_ancho // 2, self.juego.pantalla_alto // 2

        pantalla.blit(titulo, titulo.get_rect(center=(cx, cy - 60)))
        pantalla.blit(instrucciones, instrucciones.get_rect(center=(cx, cy - 20)))
        pantalla.blit(nombre_surface, nombre_surface.get_rect(center=(cx, cy + 40)))