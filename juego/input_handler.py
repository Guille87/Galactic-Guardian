import pygame
import sys

from ui.boton import Boton


class InputHandler:
    def __init__(self, juego):
        self.juego = juego

    def manejar_eventos(self):
        """Captura eventos de Pygame y los deriva a las funciones correctas."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                # Si cierra la ventana (X), aquí sí cerramos el programa
                import sys
                pygame.quit()
                sys.exit()

            # --- TECLAS ---
            elif evento.type == pygame.KEYDOWN:
                self._manejar_teclas_presionadas(evento.key)

            elif evento.type == pygame.KEYUP:
                self._manejar_teclas_soltadas(evento.key)

            # --- RATÓN ---
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if not self._manejar_clic_presionado(evento):
                    return False

            elif evento.type == pygame.MOUSEBUTTONUP:
                if evento.button == 1:
                    self.juego.disparando = False

        # Si no está pausado y la bandera está activa, dispara
        if not self.juego.pausado and self.juego.disparando:
            self.juego._disparar()

        return True

    def _manejar_teclas_presionadas(self, tecla):
        if tecla == pygame.K_ESCAPE or tecla == pygame.K_p:
            if not self.juego.pausado:
                self.juego._pausar_juego()
            else:
                self.juego._reanudar_juego()

        elif tecla == pygame.K_SPACE and not self.juego.pausado:
            self.juego.disparando = True

    def _manejar_teclas_soltadas(self, tecla):
        if tecla == pygame.K_SPACE:
            self.juego.disparando = False

    def _manejar_clic_presionado(self, evento):
        if self.juego.pausado:
            # Lógica de botones en pausa
            if evento.button == 1:  # Clic izquierdo
                if self.juego.boton_opciones.clic_en_boton(evento.pos):
                    self.juego.mostrar_opciones_juego()
                elif self.juego.boton_salir.clic_en_boton(evento.pos):
                    decision = self.mostrar_confirmacion_salida()
                    if decision == "SALIR":
                        return False
        else:
            if evento.button == 1:
                self.juego.disparando = True
        return True

    def _manejar_clic_soltado(self, boton):
        if boton == 1 and not self.juego.pausado:
            self.juego.disparando = False

    def mostrar_confirmacion_salida(self):
        """Gestiona el bucle de espera para la confirmación de salida."""
        # Creamos los botones necesarios para el diálogo
        centro_x = self.juego.pantalla_ancho // 2
        boton_si = Boton("Sí", (50, 50, 50), (255, 255, 255),
                         centro_x - 100, 320, 100, 50)
        boton_no = Boton("No", (50, 50, 50), (255, 255, 255),
                         centro_x + 110, 320, 100, 50)

        # Delegamos el dibujo al UIManager
        self.juego.ui_manager.dibujar_confirmacion_salida(self.juego.pantalla, boton_si, boton_no)

        # Bucle de bloqueo para obtener respuesta
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    import sys
                    sys.exit()

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_si.clic_en_boton(evento.pos):
                        return "SALIR"
                    elif boton_no.clic_en_boton(evento.pos):
                        return "CONTINUAR"