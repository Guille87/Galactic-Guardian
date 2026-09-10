import pygame

from src.ui.components.button import Boton


class InputHandler:
    """Capa Controlador: traduce eventos de pygame en llamadas a métodos del
    `Juego`. Recibe el `Juego` completo por diseño (item 14 de la auditoría)."""

    def __init__(self, juego):
        self.juego = juego

    def manejar_eventos(self):
        """Captura eventos de Pygame y los deriva a las funciones correctas."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                # Cerrar la ventana (X) => cerrar la aplicación por completo.
                # No matamos el proceso aquí: dejamos que el bucle principal
                # haga su limpieza y propague el estado "SALIR".
                self.juego.salir_del_juego()
                return False

            # --- ENTRADA DE TEXTO (GAME OVER) ---
            if self.juego.pidiendo_nombre:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_RETURN:
                        if self.juego.nombre_entrada.strip():
                            self.juego.clasificacion.agregar_puntuacion(
                                self.juego.nombre_entrada, self.juego.puntuacion
                            )
                            self.juego.pidiendo_nombre = False
                            self.juego.estado_game_over = True
                    elif evento.key == pygame.K_BACKSPACE:
                        self.juego.nombre_entrada = self.juego.nombre_entrada[:-1]
                    elif len(self.juego.nombre_entrada) < 15:
                        # Filtrar solo caracteres imprimibles
                        if evento.unicode.isprintable():
                            self.juego.nombre_entrada += evento.unicode
                continue  # Saltamos el resto del procesamiento si estamos escribiendo

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
            self.juego.disparar()

        return True

    def _manejar_teclas_presionadas(self, tecla):
        # En Game Over el teclado no hace nada: la pantalla se maneja solo con el
        # ratón y `juego.pausado` ya está en True como "congelado".
        if self.juego.estado_game_over:
            return

        if tecla == pygame.K_ESCAPE or tecla == pygame.K_p:
            if not self.juego.pausado:
                self.juego.pausar_juego()
            else:
                self.juego.reanudar_juego()

        elif tecla == pygame.K_SPACE and not self.juego.pausado:
            self.juego.disparando = True

        elif tecla == pygame.K_F1:
            self.juego.debug_hitboxes = not self.juego.debug_hitboxes

    def _manejar_teclas_soltadas(self, tecla):
        if tecla == pygame.K_SPACE:
            self.juego.disparando = False

    def _manejar_clic_presionado(self, evento):
        # Prioridad: ¿Estamos en Game Over?
        if self.juego.estado_game_over:
            if evento.button == 1:
                if self.juego.boton_reintentar and self.juego.boton_reintentar.clic_en_boton(evento.pos):
                    self.juego.estado_game_over = False
                    self.juego.reiniciar_juego()
                elif self.juego.boton_salir_post and self.juego.boton_salir_post.clic_en_boton(evento.pos):
                    self.juego.volver_al_menu()
                    return False
            return True  # Evento consumido

        # ¿Estamos en pausa?
        if self.juego.pausado:
            # Lógica de botones en pausa
            if evento.button == 1:  # Clic izquierdo
                if self.juego.boton_opciones.clic_en_boton(evento.pos):
                    self.juego.mostrar_opciones_juego()
                    if not self.juego.ejecutando:
                        return False
                elif self.juego.boton_salir.clic_en_boton(evento.pos):
                    decision = self.mostrar_confirmacion_salida()
                    if decision == "MENU":
                        self.juego.volver_al_menu()
                        return False
                    elif decision == "SALIR":
                        self.juego.salir_del_juego()
                        return False
        # Juego activo
        else:
            if evento.button == 1:
                self.juego.disparando = True
        return True

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

        # Bucle de bloqueo para obtener respuesta.
        # "MENU"  -> el jugador confirma volver al menú principal
        # "SALIR" -> cerró la ventana: propagar cierre de la aplicación
        # "CONTINUAR" -> cancela y sigue jugando
        while True:
            self.juego.reloj.tick(30)  # evita el busy-wait al 100 % de CPU
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return "SALIR"

                if evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_si.clic_en_boton(evento.pos):
                        return "MENU"
                    elif boton_no.clic_en_boton(evento.pos):
                        return "CONTINUAR"