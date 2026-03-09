import pygame
from ui.boton import Boton


class RenderManager:
    def __init__(self, juego):
        self.juego = juego
        self.pantalla = juego.pantalla
        self.font_pausa = pygame.font.SysFont(None, 48)
        self.font_botones = pygame.font.SysFont(None, 30)

    def renderizar_todo(self):
        """Método principal que orquestra el dibujo de cada frame."""
        if self.juego.estado_game_over:
            self._dibujar_pantalla_game_over()
            return  # No dibujamos nada más si es Game Over total

        if self.juego.pausado:
            self._dibujar_fondo_en_gris()
        else:
            self.pantalla.blit(self.juego.fondo_imagen1, (0, self.juego.pos_y_fondo1))
            self.pantalla.blit(self.juego.fondo_imagen2, (0, self.juego.pos_y_fondo2))

        # Si el jugador murió, no dibujamos más elementos del mundo
        if self.juego.jugador.vidas <= 0:
            pygame.display.flip()
            return

        # Dibujar Sprites (Balas, Enemigos, Items, Explosiones)
        self._dibujar_entidades()

        # Dibujar Jugador
        if self.juego.pausado:
            self._dibujar_sprite_en_gris(self.juego.jugador)
            self._mostrar_texto_centralizado("Juego Pausado", (255, 255, 255))
            self._dibujar_botones_pausa()
        else:
            self.pantalla.blit(self.juego.jugador.image, self.juego.jugador.rect)

        # Interfaz de Usuario (Salud, Puntos, Nivel)
        self.juego.ui_manager.dibujar_interfaz(self.pantalla)

        pygame.display.flip()

    def _dibujar_pantalla_game_over(self):
        """Dibuja la UI de fin de juego."""
        self.pantalla.blit(self.juego.fondo_imagen1, (0, 0))
        self.juego.mostrar_game_over()

        # Dibujar botones de Reintentar y Salir
        centro_x = self.juego.pantalla_ancho // 2
        self.juego.boton_reintentar = Boton("Reintentar", (255, 0, 0, 128), (255, 255, 255),
                                            centro_x, 400, 200, 50, radio_borde=10)
        self.juego.boton_salir_post = Boton("Salir", (255, 0, 255, 128), (255, 255, 255),
                                            centro_x, 470, 200, 50, radio_borde=10)

        self.juego.boton_reintentar.dibujar(self.pantalla, self.font_botones)
        self.juego.boton_salir_post.dibujar(self.pantalla, self.font_botones)
        pygame.display.flip()

    def _dibujar_entidades(self):
        """Dibuja todos los grupos de elementos, aplicando gris si está pausado."""
        em = self.juego.entity_manager
        # Listas extraídas del manager
        listas_elementos = [em.balas, em.balas_enemigo, em.enemigos]

        # Primero los sprites generales (explosiones, items, etc)
        for sprite in self.juego.all_sprites:
            if self.juego.pausado:
                self._dibujar_sprite_en_gris(sprite)
            else:
                self.pantalla.blit(sprite.image, sprite.rect)

        # Luego las listas específicas
        for lista in listas_elementos:
            for elemento in lista:
                if elemento:
                    if self.juego.pausado:
                        self._dibujar_sprite_en_gris(elemento)
                    else:
                        self.pantalla.blit(elemento.image, elemento.rect)

    def _dibujar_botones_pausa(self):
        centro_x = self.juego.pantalla_ancho // 2
        y_opciones = self.juego.pantalla_alto // 2 + 50
        y_salir = self.juego.pantalla_alto // 2 + 120

        # Los botones se crean/actualizan aquí para el RenderManager
        self.juego.boton_opciones = Boton("Opciones", (0, 255, 255, 150), (255, 255, 255),
                                          centro_x, y_opciones, 150, 50, radio_borde=10)
        self.juego.boton_salir = Boton("Salir", (255, 0, 0, 150), (255, 255, 255),
                                       centro_x, y_salir, 150, 50, radio_borde=10)

        self.juego.boton_opciones.dibujar(self.pantalla, self.font_botones)
        self.juego.boton_salir.dibujar(self.pantalla, self.font_botones)

    def _mostrar_texto_centralizado(self, texto, color):
        texto_surface = self.font_pausa.render(texto, True, color)
        texto_rect = texto_surface.get_rect(center=(self.juego.pantalla_ancho // 2, self.juego.pantalla_alto // 2))
        self.pantalla.blit(texto_surface, texto_rect)

    def _dibujar_fondo_en_gris(self):
        for img, pos_y in [(self.juego.fondo_imagen1, self.juego.pos_y_fondo1),
                           (self.juego.fondo_imagen2, self.juego.pos_y_fondo2)]:
            img_gris = img.copy()
            img_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
            self.pantalla.blit(img_gris, (0, pos_y))

    def _dibujar_sprite_en_gris(self, sprite):
        if hasattr(sprite, 'image'):
            img_gris = sprite.image.copy()
            img_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
            self.pantalla.blit(img_gris, sprite.rect)