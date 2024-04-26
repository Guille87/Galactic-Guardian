import random

import pygame
import pygame.freetype

from galactic_guardian.efectos.destello import Destello
from galactic_guardian.efectos.destello_constante import DestelloConstante
from galactic_guardian.entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from galactic_guardian.entidades.explosion import Explosion
from galactic_guardian.entidades.item import Item
from galactic_guardian.entidades.jugador import Jugador
from galactic_guardian.juego import menu
from galactic_guardian.resources.resource_manager import ResourceManager
from galactic_guardian.ui.boton import Boton

# Instancia global de ResourceManager
resource_manager = ResourceManager()


class Juego:
    def __init__(self, pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos, clasificacion):
        # Inicialización de variables
        self.volumen_musica = volumen_musica
        self.volumen_efectos = volumen_efectos
        self.pantalla_ancho = pantalla_ancho
        self.pantalla_alto = pantalla_alto
        self.puntuacion = 0
        self.nivel = 1
        self.jefe = None
        self.jefe_generado = False
        self.jefe_derrotado = False
        self.enemigos_activos = 0
        self.enemigos_eliminados = 0
        self.max_enemigos_para_objeto = 10
        self.tiempo_espera_jefe = 5000
        self.tiempo_inicio_espera_jefe = 0
        self.disparando = False
        self.pausado = False
        self.tiempo_pausa = 0
        self.tiempo_proximo_enemigo = 0
        self.tiempo_entre_enemigos = 0
        self.MIN_TIEMPO_GENERACION = 800
        self.MAX_TIEMPO_GENERACION = 1000

        self.clasificacion = clasificacion

        # Inicialización de recursos
        self.all_sprites = pygame.sprite.Group()
        self.EFECTO_DISPARO = resource_manager.get_sound("laser_gun")
        self.EFECTO_GOLPE = resource_manager.get_sound("hit")
        self.EFECTO_ITEM = resource_manager.get_sound("item_take")
        # Configuración de volúmenes
        self.EFECTO_DISPARO.set_volume(volumen_efectos)
        self.EFECTO_GOLPE.set_volume(volumen_efectos)
        self.EFECTO_ITEM.set_volume(volumen_efectos)
        if not resource_manager.is_music_playing("rain_of_lasers"):
            resource_manager.play_music("rain_of_lasers", loops=-1)
            resource_manager.set_music_volume("rain_of_lasers", volumen_musica)
        # Obtener imágenes
        self.ruta_imagen_jugador = resource_manager.get_image_path("jugador")
        self.fondo_imagen1 = resource_manager.get_image("imagen_fondo1")
        self.fondo_imagen2 = resource_manager.get_image("imagen_fondo2")
        self.explosion_images = [resource_manager.get_image(f"explosion_{i}") for i in range(1, 12)]

        # Inicialización de la pantalla
        self.pantalla = menu.crear_pantalla()

        # Inicialización de botones
        self.boton_opciones = None
        self.boton_salir = None
        # Inicialización de jugadores, enemigos, balas, etc.
        self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)

        self.enemigos = []
        self.balas = []
        self.balas_enemigo = []
        # Inicialización de tiempo
        self.inicio_juego = pygame.time.get_ticks()
        # Inicialización de posiciones de fondo
        self.pos_y_fondo1 = 0
        self.pos_y_fondo2 = -self.pantalla_alto
        # Inicialización de diccionario de enemigos golpeados
        self.enemigos_golpeados = {}
        # Configuración del reloj
        self.reloj = pygame.time.Clock()

    def generar_enemigo(self):
        """
        Genera un nuevo enemigo en una posición aleatoria en la parte superior de la pantalla.
        """
        tiempo_transcurrido = pygame.time.get_ticks() - self.inicio_juego  # Calcular el tiempo transcurrido en milisegundos
        tiempo_espera = 2000  # 2 segundos en milisegundos
        nuevo_enemigo = None  # Inicializar como None

        if tiempo_transcurrido >= tiempo_espera:
            ancho_enemigo = 50
            alto_enemigo = 10
            x_enemigo = random.randint(50, self.pantalla_ancho - ancho_enemigo - 50)
            y_enemigo = -alto_enemigo  # Genera el enemigo arriba de la pantalla

            # Construir la ruta al directorio de las imágenes de los enemigos
            ruta_enemigo1 = resource_manager.get_image_path("enemigo1")
            ruta_enemigo2 = resource_manager.get_image_path("enemigo2")
            ruta_enemigo3 = resource_manager.get_image_path("enemigo3")
            ruta_enemigo_jefe = resource_manager.get_image_path("jefe1")

            # Restar el tiempo entre enemigos que se ha acumulado durante la pausa
            tiempo_transcurrido -= self.tiempo_entre_enemigos

            # Elige el tipo de enemigo según el tiempo transcurrido
            if tiempo_transcurrido >= 62000:  # Después de 62 segundos en milisegundos
                if not self.jefe_generado and self.enemigos_activos == 0:
                    # Detener música de fondo
                    resource_manager.stop_music("rain_of_lasers")
                    if not resource_manager.is_music_playing("deathmatch_theme"):
                        resource_manager.play_music("deathmatch_theme", loops=-1)
                        resource_manager.set_music_volume("deathmatch_theme", self.volumen_musica)
                    # Inicia el temporizador para esperar antes de generar al jefe
                    if self.tiempo_inicio_espera_jefe == 0:
                        self.tiempo_inicio_espera_jefe = pygame.time.get_ticks()
                    # Verifica si ha pasado el tiempo de espera para generar al jefe
                    tiempo_transcurrido_jefe = pygame.time.get_ticks() - self.tiempo_inicio_espera_jefe
                    if tiempo_transcurrido_jefe >= self.tiempo_espera_jefe:
                        tipo_enemigo = Jefe
                        ruta_imagen = ruta_enemigo_jefe
                        # Calcular las coordenadas x e y del jefe
                        x_enemigo = (self.pantalla_ancho - 200) // 2
                        y_enemigo = -150  # Genera el jefe en la parte superior de la pantalla
                        nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.pantalla_alto, self.balas_enemigo,
                                                     self.jugador, self.nivel)
                        self.jefe = nuevo_enemigo
                        self.jefe_generado = True  # Marca que el jefe ya ha sido generado
            elif tiempo_transcurrido >= 42000:  # Después de 42 segundos en milisegundos
                tipo_enemigo = random.choice([EnemigoTipo1, EnemigoTipo2, EnemigoTipo3])
                if tipo_enemigo == EnemigoTipo1:
                    ruta_imagen = ruta_enemigo1
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.nivel)
                elif tipo_enemigo == EnemigoTipo2:
                    ruta_imagen = ruta_enemigo2
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador, self.nivel)
                else:
                    ruta_imagen = ruta_enemigo3
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador, self.nivel)
            elif tiempo_transcurrido >= 22000:  # Después de 22 segundos en milisegundos
                tipo_enemigo = random.choice([EnemigoTipo1, EnemigoTipo2])
                if tipo_enemigo == EnemigoTipo1:
                    ruta_imagen = ruta_enemigo1
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.nivel)
                else:
                    ruta_imagen = ruta_enemigo2
                    nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.balas_enemigo, self.jugador, self.nivel)
            else:
                tipo_enemigo = EnemigoTipo1
                ruta_imagen = ruta_enemigo1
                nuevo_enemigo = tipo_enemigo(ruta_imagen, x_enemigo, y_enemigo, self.pantalla_ancho, self.nivel)

            if nuevo_enemigo:
                self.enemigos_activos += 1

            return nuevo_enemigo

    def mostrar_confirmacion_salida(self):
        # Crea un rectángulo para el fondo oscuro
        fondo_oscuro = pygame.Surface((self.pantalla_ancho, self.pantalla_alto))
        fondo_oscuro.set_alpha(200)  # Configura la transparencia
        fondo_oscuro.fill((0, 0, 0))  # Color oscuro

        # Dibuja el fondo oscuro en la pantalla
        self.pantalla.blit(fondo_oscuro, (0, 0))

        # Crea un rectángulo para el cuadro de diálogo
        rectangulo_dialogo = pygame.Rect(50, 200, 500, 200)
        pygame.draw.rect(self.pantalla, (255, 255, 255), rectangulo_dialogo)

        # Dibuja el texto del cuadro de diálogo
        font = pygame.font.SysFont(None, 36)
        texto = font.render("¿Estás seguro de que deseas salir?", True, (0, 0, 0))
        texto_rect = texto.get_rect(center=(rectangulo_dialogo.centerx, rectangulo_dialogo.centery - 50))
        self.pantalla.blit(texto, texto_rect)

        # Dibuja los botones "Sí" y "No"
        boton_si = Boton("Sí", (50, 50, 50), (255, 255, 255), rectangulo_dialogo.centerx - 100, rectangulo_dialogo.bottom - 80,
                         100, 50)
        boton_no = Boton("No", (50, 50, 50), (255, 255, 255), rectangulo_dialogo.centerx + 110, rectangulo_dialogo.bottom - 80,
                         100, 50)
        boton_si.dibujar(self.pantalla, font)
        boton_no.dibujar(self.pantalla, font)

        # Actualiza la pantalla
        pygame.display.flip()

        # Espera la respuesta del usuario
        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_si.clic_en_boton(evento.pos):
                        self.mostrar_menu_principal()
                    elif boton_no.clic_en_boton(evento.pos):
                        return

    def manejar_eventos(self):
        """
        Maneja los eventos de pygame.
        """
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False  # Indica que el juego debe terminar
            elif evento.type == pygame.KEYDOWN:
                self._manejar_tecla_presionada(evento.key)
            elif evento.type == pygame.KEYUP:
                self._manejar_tecla_soltada(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                self._manejar_click_presionado(evento.button)
                if self.pausado:
                    if evento.button == 1:
                        if self.boton_opciones.clic_en_boton(evento.pos):
                            self.mostrar_opciones_juego()
                        elif self.boton_salir.clic_en_boton(evento.pos):
                            self.mostrar_confirmacion_salida()
            elif evento.type == pygame.MOUSEBUTTONUP:
                self._manejar_click_soltado(evento.button)

            # Si el juego está pausado, no manejar otros eventos
        if self.pausado:
            return True

            # Si la tecla de disparo está presionada, crea una nueva bala
        if self.disparando:
            self._disparar()

        return True

    def _manejar_tecla_presionada(self, tecla):
        """
        Maneja el evento de tecla presionada.
        Si se presiona la tecla de escape o P, pausa o reanuda el juego.
        Si se presiona la tecla de espacio, activa el disparo si el juego no está pausado.
        """
        if tecla == pygame.K_ESCAPE or tecla == pygame.K_p:
            if not self.pausado:
                self._pausar_juego()
            else:
                self._reanudar_juego()
        elif tecla == pygame.K_SPACE:
            if not self.pausado:
                self.disparando = True
                self._disparar()

    def _manejar_tecla_soltada(self, tecla):
        """
        Maneja el evento de tecla soltada.
        Si se suelta la tecla de espacio, desactiva el disparo si el juego no está pausado.
        """
        if tecla == pygame.K_SPACE:
            if not self.pausado:
                self.disparando = False

    def _manejar_click_presionado(self, boton):
        """
        Maneja el evento de clic de ratón presionado.
        Si se presiona el botón izquierdo del ratón, activa el disparo si el juego no está pausado.
        """
        if boton == 1:  # Botón izquierdo del ratón
            if not self.pausado:
                self.disparando = True
                self._disparar()

    def _manejar_click_soltado(self, boton):
        """
        Maneja el evento de clic de ratón soltado.
        Si se suelta el botón izquierdo del ratón, desactiva el disparo si el juego no está pausado.
        """
        if boton == 1:  # Botón izquierdo del ratón
            if not self.pausado:
                self.disparando = False

    def _pausar_juego(self):
        """
        Pausa el juego y guarda el tiempo en que se pausó.
        """
        self.pausado = True
        self.tiempo_pausa = pygame.time.get_ticks()

    def _reanudar_juego(self):
        """
        Reanuda el juego y ajusta los tiempos para sincronizarlos con el tiempo pausado.
        """
        self.pausado = False
        tiempo_actual = pygame.time.get_ticks()
        tiempo_pausado = tiempo_actual - self.tiempo_pausa
        self.tiempo_proximo_enemigo += tiempo_pausado
        self.tiempo_entre_enemigos += tiempo_pausado
        self.jugador.tiempo_invulnerable += tiempo_pausado  # Actualizar el tiempo de invulnerabilidad del jugador
        for enemigo in self.enemigos:
            if isinstance(enemigo, EnemigoTipo2) or isinstance(enemigo, EnemigoTipo3):
                enemigo.tiempo_ultimo_ataque += tiempo_pausado
            if isinstance(enemigo, Jefe):
                enemigo.tiempo_ultimo_disparo += tiempo_pausado
                enemigo.tiempo_ultimo_disparo_rapido += tiempo_pausado

    def _disparar(self):
        """
        Maneja la lógica de disparo del jugador.
        """
        # Llama a la función disparar del jugador para obtener las nuevas balas
        nuevas_balas = self.jugador.disparar()

        primera_bala = True  # Bandera para verificar si ya se disparó la primera bala
        # Verifica si hay nuevas balas y las agrega a la lista de balas
        for bala in nuevas_balas:
            if bala:
                self.balas.append(bala)
                if primera_bala:  # Reproduce el sonido solo para la primera bala
                    self.EFECTO_DISPARO.play()
                    primera_bala = False  # Cambia la bandera después del primer disparo

    def actualizar(self):
        """
        Actualiza el estado del juego.
        """
        if self.jugador.vidas <= 0:
            self.juego_terminado()
            return

        self.actualizar_jugador()
        self.generar_enemigos()
        self.actualizar_enemigos()
        self.eliminar_elementos_fuera_de_pantalla()
        self.eliminar_colisiones_bala_jugador()
        self.eliminar_colisiones_bala_enemigo()
        self.mover_fondo()
        self.jugador.update()

    def eliminar_elementos_fuera_de_pantalla(self):
        """
        Elimina los elementos (balas, enemigos y objetos) que están fuera de la pantalla.
        """
        enemigos_salidos = []  # Lista para almacenar los enemigos que han salido fuera de la pantalla
        for enemigo in self.enemigos:
            if enemigo and self.fuera_de_pantalla(enemigo.rect):
                enemigos_salidos.append(enemigo)

        # Reducir en 1 el contador de enemigos_activos por cada enemigo que ha salido de la pantalla
        self.enemigos_activos -= len(enemigos_salidos)

        self.balas = [bala for bala in self.balas if not (bala is not None and self.fuera_de_pantalla(bala.rect))]
        self.enemigos = [enemigo for enemigo in self.enemigos if not (enemigo is not None and self.fuera_de_pantalla(enemigo.rect))]
        self.balas_enemigo = [bala_enemiga for bala_enemiga in self.balas_enemigo if
                              not (bala_enemiga is not None and self.fuera_de_pantalla(bala_enemiga.rect))]
        self.all_sprites = pygame.sprite.Group([item for item in self.all_sprites if not (item is not None and self.fuera_de_pantalla(item.rect))])

    def fuera_de_pantalla(self, rect):
        """
        Verifica si un rectángulo está fuera de la pantalla.

        Args:
            rect: Rectángulo a verificar.

        Returns:
            bool: True si el rectángulo está fuera de la pantalla, False en caso contrario.
        """
        return rect.bottom < 0 or rect.top > self.pantalla_alto or rect.right < 0 or rect.left > self.pantalla_ancho

    def eliminar_colisiones_bala_jugador(self):
        """
        Elimina las colisiones entre las balas del jugador y los enemigos.
        """
        for bala in self.balas:
            bala.bala_jugador()
            self.eliminar_colision_bala_enemigo(bala)

    def eliminar_colision_bala_enemigo(self, bala):
        """
        Elimina las colisiones entre las balas de los enemigos y el jugador.

        Args:
            bala: Bala del enemigo a comprobar.
        """
        for enemigo in self.enemigos:
            if bala.comprobar_colision(enemigo):
                self.procesar_colision_bala_enemigo(bala, enemigo)
                break

    def procesar_colision_bala_enemigo(self, bala, enemigo):
        """
        Procesa la colisión entre una bala y un enemigo.

        Args:
            bala: Bala del jugador.
            enemigo: Enemigo colisionado.
        """
        balas_a_eliminar = [bala, enemigo]
        # Reducir la salud del enemigo según el daño de la bala del jugador
        enemigo.take_damage(bala.danio)
        if enemigo.salud <= 0:
            self.enemigos.remove(enemigo)
            # Incrementa el contador de enemigos eliminados
            self.enemigos_eliminados += 1
            explosion = Explosion(enemigo.rect.center, self.explosion_images)
            self.all_sprites.add(explosion)  # Añadir la explosión al grupo de sprites
            objeto = enemigo.die(self.jugador, self.enemigos_eliminados)  # Crear un objeto cuando el enemigo muere
            if objeto is not None or self.enemigos_eliminados >= self.enemigos_eliminados:
                if objeto is not None:
                    self.all_sprites.add(objeto)
                    # Restablece el contador de enemigos eliminados
                    self.enemigos_eliminados = 0
            # Aumentar la puntuación según el tipo de enemigo eliminado y el nivel actual
            puntuacion_enemigo = 0
            if isinstance(enemigo, EnemigoTipo1):
                puntuacion_enemigo = 1
            elif isinstance(enemigo, EnemigoTipo2):
                puntuacion_enemigo = 2
            elif isinstance(enemigo, EnemigoTipo3):
                puntuacion_enemigo = 3
            elif isinstance(enemigo, Jefe):
                puntuacion_enemigo = 1000
                self.jefe_derrotado = True
                self.reiniciar_juego()
            self.puntuacion += puntuacion_enemigo * self.nivel
            # Decrementa el contador de enemigos en pantalla
            self.enemigos_activos -= 1
        self.EFECTO_GOLPE.play()
        self.eliminar_elementos(balas_a_eliminar)

    def manejar_impacto_jugador(self):
        """
        Maneja el impacto en el jugador.
        Si el jugador tiene vidas restantes.
        Si la salud del jugador es mayor que 0, crea un destello en la posición del jugador.
        Si la salud del jugador llega a 0, crea una explosión en la posición del jugador,
        reposiciona al jugador en el centro de la parte inferior de la pantalla,
        reduce una vida y, si quedan vidas restantes, aumenta la salud del jugador en 5.
        """
        if self.jugador.vidas > 0:
            if self.jugador.salud > 0:
                self.crear_destello()
            else:
                self.jugador_explota()
                self.reposicionar_jugador()
                self.reducir_vidas_y_aumentar_salud()

    def crear_destello(self):
        """
        Crea un destello en la posición del jugador.
        """
        if not self.jugador.invulnerable:
            destello = Destello(self.jugador)
            self.all_sprites.add(destello)

    def jugador_explota(self):
        """
        Crea una explosión en la posición del jugador.
        """
        explosion = Explosion(self.jugador.rect.center, self.explosion_images)
        self.all_sprites.add(explosion)

    def reposicionar_jugador(self):
        """
        Reposiciona al jugador en el centro inferior de la pantalla.
        """
        self.jugador.rect.centerx = self.pantalla_ancho // 2
        self.jugador.rect.bottom = self.pantalla_alto - 10

    def reducir_vidas_y_aumentar_salud(self):
        """
        Reduce una vida al jugador y aumenta su salud si quedan vidas restantes.
        """
        self.jugador.reducir_vidas(1)
        self.jugador.invulnerable = True
        self.jugador.tiempo_invulnerable = pygame.time.get_ticks() + 3000
        self.crear_destello_constante()
        if self.jugador.vidas > 0:
            self.jugador.aumentar_salud(self.jugador.salud_maxima)

    def crear_destello_constante(self):
        """
        Crea un destello constante en la posición del jugador.
        """
        self.jugador.destello_constante = DestelloConstante(self.jugador)
        self.all_sprites.add(self.jugador.destello_constante)

    def eliminar_colisiones_bala_enemigo(self):
        """
        Maneja las colisiones entre las balas del enemigo y el jugador.
        Si una bala del enemigo colisiona con el jugador, la elimina, maneja el impacto en el jugador
        y reproduce un efecto de golpe.
        También elimina las balas del enemigo que están fuera de la pantalla.
        """
        balas_enemigas_a_eliminar = []
        for bala_enemiga in self.balas_enemigo:
            bala_enemiga.bala_enemigo()
            if bala_enemiga.comprobar_colision(self.jugador):
                self.eliminar_elementos([bala_enemiga])
                self.jugador.reducir_salud(bala_enemiga.danio)
                self.manejar_impacto_jugador()
                self.EFECTO_GOLPE.play()
            elif self.fuera_de_pantalla(bala_enemiga.rect):
                balas_enemigas_a_eliminar.append(bala_enemiga)
        self.eliminar_elementos(balas_enemigas_a_eliminar)

    def eliminar_elementos(self, elementos):
        """
        Elimina los elementos dados de las listas correspondientes.

        Args:
            elementos (list): Lista de elementos a eliminar.
        """
        for elemento in elementos:
            if elemento in self.balas:
                self.balas.remove(elemento)
            elif elemento in self.balas_enemigo:
                self.balas_enemigo.remove(elemento)

    def actualizar_jugador(self):
        """
        Actualiza la posición del jugador en función de las teclas presionadas.
        """
        teclas_presionadas = pygame.key.get_pressed()
        self.jugador.mover(teclas_presionadas, self.pantalla)
        self.detectar_colisiones_objetos()

    def detectar_colisiones_objetos(self):
        """
        Detecta y maneja las colisiones entre el jugador y los objetos.
        """
        for objeto in self.all_sprites:
            if isinstance(objeto, Item) and self.jugador.rect.colliderect(objeto.rect):
                self.EFECTO_ITEM.play()
                self.aplicar_efecto_y_eliminar(objeto)

    def aplicar_efecto_y_eliminar(self, objeto):
        """
        Aplica los efectos del objeto al jugador y lo elimina del juego.
        """
        objeto.aplicar_efecto(self.jugador)
        objeto.kill()

    def generar_enemigos(self):
        """
        Genera nuevos enemigos de forma aleatoria.
        """
        if not self.pausado and pygame.time.get_ticks() > self.tiempo_proximo_enemigo:
            if self.jugador.vidas > 0:  # Solo generar enemigos si el jugador está vivo
                self.enemigos.append(self.generar_enemigo())
                self.tiempo_proximo_enemigo = pygame.time.get_ticks() + random.randint(self.MIN_TIEMPO_GENERACION, self.MAX_TIEMPO_GENERACION)

    def actualizar_enemigos(self):
        """
        Actualiza la posición y comportamiento de los enemigos.
        """
        for enemigo in self.enemigos:
            if enemigo is not None:  # Verificar si enemigo no es None
                enemigo.movimiento_enemigo()
                enemigo.update()
                if self.jugador.rect.colliderect(enemigo.rect):
                    self.colision_jugador_enemigo(enemigo)

                if isinstance(enemigo, EnemigoTipo2):
                    nueva_bala_enemigo = enemigo.disparo_enemigo()
                    if nueva_bala_enemigo:
                        self.balas_enemigo.append(nueva_bala_enemigo)
                if isinstance(enemigo, EnemigoTipo3):
                    nueva_bala_enemigo = enemigo.disparo_enemigo()
                    if nueva_bala_enemigo:
                        self.balas_enemigo.append(nueva_bala_enemigo)
                if isinstance(enemigo, Jefe):
                    nueva_bala_enemigo1 = enemigo.disparo_jefe()
                    nueva_bala_enemigo2 = enemigo.disparo_rapido()
                    if nueva_bala_enemigo1:
                        self.balas_enemigo.append(nueva_bala_enemigo1)
                    if nueva_bala_enemigo2:
                        self.balas_enemigo.append(nueva_bala_enemigo2)

    def colision_jugador_enemigo(self, enemigo):
        """
        Maneja la colisión entre el jugador y un enemigo.

        Args:
            enemigo: Enemigo colisionado.
        """
        # Verificar si ya ha pasado suficiente tiempo desde la última colisión con este enemigo
        tiempo_actual = pygame.time.get_ticks()
        tiempo_ultima_colision = self.enemigos_golpeados.get(enemigo, 0)
        if tiempo_actual - tiempo_ultima_colision >= 2000:  # 2000 milisegundos = 2 segundos
            self.jugador.reducir_salud(1)
            self.EFECTO_GOLPE.play()
            self.enemigos_golpeados[enemigo] = tiempo_actual  # Registrar el tiempo de la última colisión
            self.manejar_impacto_jugador()
            enemigo.salud -= 1
        if enemigo.salud <= 0:
            explosion = Explosion(enemigo.rect.center, self.explosion_images)
            self.all_sprites.add(explosion)  # Añadir la explosión al grupo de sprites
            self.enemigos.remove(enemigo)
            # Decrementa el contador de enemigos en pantalla
            self.enemigos_activos -= 1
            # Incrementa el contador de enemigos eliminados
            self.enemigos_eliminados += 1

    def mover_fondo(self):
        """
        Mueve el fondo del juego.
        """
        self.pos_y_fondo1 += 0.5
        self.pos_y_fondo2 += 0.5
        if self.pos_y_fondo1 >= self.pantalla_alto:
            self.pos_y_fondo1 = -self.pantalla_alto
        if self.pos_y_fondo2 >= self.pantalla_alto:
            self.pos_y_fondo2 = -self.pantalla_alto

    def mostrar_game_over(self):
        """
        Muestra el mensaje de "Game Over".
        """
        self.all_sprites.empty()  # Eliminar todos los sprites
        font_game_over = pygame.font.SysFont(None, 72)  # Fuente y tamaño del texto
        texto_game_over = font_game_over.render("Game Over", True, (255, 255, 255))  # Texto, antialiasing y color
        texto_rect = texto_game_over.get_rect(center=(self.pantalla_ancho // 2, self.pantalla_alto // 2 - 150))  # Centrar el texto un poco más arriba
        self.pantalla.blit(texto_game_over, texto_rect)  # Mostrar el texto "Game Over"

    def juego_terminado(self):
        """
        Muestra el mensaje de "Game Over" y las opciones de "Reintentar" y "Salir".
        """
        # Detener música de fondo
        resource_manager.stop_music("rain_of_lasers")
        resource_manager.stop_music("deathmatch_theme")

        # Iniciar música Game Over de fondo si aún no se ha iniciado
        if not resource_manager.is_music_playing("defeated_tune"):
            resource_manager.play_music("defeated_tune", loops=-1)
            resource_manager.set_music_volume("defeated_tune", self.volumen_musica)

        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()
        if len(puntuaciones_top) < 10 or self.puntuacion > puntuaciones_top[-1][1]:
            self.mostrar_game_over()
            # La puntuación del jugador está entre las 10 mejores o es superior a la última de las 10 mejores
            nombre_jugador = self.mostrar_cuadro_dialogo("Introduce tu nombre: ")
            self.clasificacion.agregar_puntuacion(nombre_jugador, self.puntuacion)

        # Actualizar la pantalla para borrar el texto "Introduce tu nombre"
        self.pantalla.blit(self.fondo_imagen1, (0, 0))

        # Cargar la fuente para los botones
        font = pygame.font.Font(None, 36)

        # Crear el botón "Reintentar"
        boton_reintentar = Boton("Reintentar", (255, 0, 0, 128), (255, 255, 255), self.pantalla.get_rect().centerx, 400,
                                 200, 50, radio_borde=10)

        # Crear el botón "Salir"
        boton_salir = Boton("Salir", (255, 0, 255, 128), (255, 255, 255), self.pantalla.get_rect().centerx, 470,
                            200, 50, radio_borde=10)

        self.mostrar_game_over()
        # Dibujar el botón en la pantalla
        boton_reintentar.dibujar(self.pantalla, font)
        boton_salir.dibujar(self.pantalla, font)

        pygame.display.flip()  # Actualizar la pantalla

        while True:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    return False
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if boton_reintentar.clic_en_boton(evento.pos):
                        self.reiniciar_juego()  # Reiniciar el juego si el jugador hace clic en "Reintentar"
                        return True
                    elif boton_salir.clic_en_boton(evento.pos):
                        # Volver al menú principal si el jugador hace clic en "Salir"
                        self.mostrar_menu_principal()
                        return True

    def mostrar_cuadro_dialogo(self, mensaje):
        font_dialogo = pygame.freetype.SysFont(None, 24)
        entrada = ""
        ingresando = True
        while ingresando:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        ingresando = False
                    elif event.key == pygame.K_BACKSPACE:
                        entrada = entrada[:-1]
                    else:
                        entrada += event.unicode

            self.pantalla.blit(self.fondo_imagen1, (0, 0))
            texto_surface, _ = font_dialogo.render(mensaje + entrada, (255, 255, 255))
            self.pantalla.blit(texto_surface, ((self.pantalla.get_width() - texto_surface.get_width()) // 2,
                                               (self.pantalla.get_height() - texto_surface.get_height()) // 2))
            pygame.display.flip()

        return entrada

    def mostrar_menu_principal(self):
        """
        Muestra el menú principal del juego.
        """
        # Detener música
        resource_manager.stop_music("rain_of_lasers")
        resource_manager.stop_music("deathmatch_theme")
        resource_manager.stop_music("defeated_tune")

        # Iniciar música de fondo del menú si aún no se ha iniciado
        if not resource_manager.is_music_playing("skyfire_theme"):
            resource_manager.play_music("skyfire_theme", loops=-1)
            resource_manager.set_music_volume("skyfire_theme", self.volumen_musica)

        from galactic_guardian.juego.menu import mostrar_menu
        mostrar_menu(self.pantalla)

    def mostrar_opciones_juego(self):
        """
        Muestra el menú principal del juego.
        """
        from galactic_guardian.juego.menu import mostrar_opciones
        mostrar_opciones(self.pantalla, self.volumen_musica, self.volumen_efectos)

    def reiniciar_juego(self):
        """
        Reinicia el juego.
        """
        if self.jefe_derrotado:
            self.nivel += 1
            self.jefe_derrotado = False
            self.MIN_TIEMPO_GENERACION -= 200
            self.MAX_TIEMPO_GENERACION -= 200
            if self.MIN_TIEMPO_GENERACION <= 200:
                self.MIN_TIEMPO_GENERACION = 200
            if self.MAX_TIEMPO_GENERACION <= 200:
                self.MAX_TIEMPO_GENERACION = 200
            # Detener música Jefe
            resource_manager.stop_music("deathmatch_theme")
        else:
            self.jugador = Jugador(self.ruta_imagen_jugador, self.pantalla_ancho, self.pantalla_alto, self.all_sprites)
            self.MIN_TIEMPO_GENERACION = 800
            self.MAX_TIEMPO_GENERACION = 1000
            self.puntuacion = 0
            self.balas = []
            self.balas_enemigo = []
            # Detener música Game Over
            resource_manager.stop_music("defeated_tune")

        # Reiniciar todos los valores del juego a sus estados iniciales
        self.enemigos = []
        self.enemigos_golpeados = {}
        self.tiempo_proximo_enemigo = 0
        self.jefe_generado = False
        self.inicio_juego = pygame.time.get_ticks()
        self.enemigos_activos = 0
        self.tiempo_inicio_espera_jefe = 0

        if not resource_manager.is_music_playing("rain_of_lasers"):
            resource_manager.play_music("rain_of_lasers", loops=-1)
            resource_manager.set_music_volume("rain_of_lasers", self.volumen_musica)

        # Continuar ejecutando el juego
        self.ejecutar()

    def dibujar(self):
        """
        Dibuja en la pantalla.
        """
        # Blitgear la imagen de fondo en la pantalla con un tono gris si el juego está pausado
        if self.pausado:
            self.dibujar_fondo_en_gris()
        else:
            self.pantalla.blit(self.fondo_imagen1, (0, self.pos_y_fondo1))
            self.pantalla.blit(self.fondo_imagen2, (0, self.pos_y_fondo2))

        if self.jugador.vidas <= 0:
            return  # Salir de la función si el juego ha terminado

        # Dibujar todos los sprites en el grupo de sprites
        self.all_sprites.draw(self.pantalla)

        # Dibujar balas y enemigos
        self.dibujar_elementos(self.balas)
        self.dibujar_elementos(self.balas_enemigo)
        self.dibujar_elementos(self.enemigos)

        # Dibujar jugador
        if self.pausado:
            self.dibujar_sprite_en_gris(self.jugador)
            self.mostrar_texto_centralizado("Juego Pausado", (255, 255, 255))
            self.dibujar_botones_pausa()
        else:
            self.pantalla.blit(self.jugador.image, self.jugador.rect)

        # Mostrar texto de vidas
        font = pygame.font.SysFont(None, 24)  # Fuente y tamaño del texto
        color_texto_vidas = (128, 128, 128) if self.pausado else (255, 255, 255)
        self.mostrar_texto("Vidas: ", (10, 10), color_texto_vidas, self.jugador.vidas, font)
        self.dibujar_barra_salud()
        if self.jefe_generado:
            self.dibujar_barra_salud_jefe()

        # Mostrar puntuación
        self.mostrar_texto("Puntuación: ", (10, 40), color_texto_vidas, self.puntuacion, font)

        # Define el diccionario de colores para cada atributo
        colores_atributos = {
            "Ataque": (255, 0, 0),  # Rojo
            "Vel. Ataque": (0, 255, 0),  # Verde
            "Velocidad": (0, 0, 255)  # Azul
        }

        # Mostrar texto y barras de atributos
        self.mostrar_atributo("Ataque", self.jugador.danio, self.jugador.DANIO_MAXIMO, (10, 70), colores_atributos["Ataque"])
        self.mostrar_atributo("Vel. Ataque", round(1 / (self.jugador.cadencia_disparo / 1000), 2),
                              round(1 / (Jugador.CADENCIA_DISPARO_MAXIMA / 1000), 2), (10, 120), colores_atributos["Vel. Ataque"])

        self.mostrar_atributo("Velocidad", self.jugador.velocidad, Jugador.VELOCIDAD_MAXIMA, (10, 170), colores_atributos["Velocidad"])

        # Mostrar FPS en la esquina superior derecha
        self.mostrar_texto_fps()

        pygame.display.flip()  # Actualiza la pantalla

    def mostrar_atributo(self, nombre, valor, maximo, posicion, color):
        """
        Muestra un texto y una barra de atributo en la pantalla.
        """
        font = pygame.font.SysFont(None, 24)  # Fuente y tamaño del texto
        texto = font.render(f"{nombre}: {valor}", True, (255, 255, 255))  # Texto, antialiasing y color
        self.pantalla.blit(texto, posicion)

        # Calcular el tamaño de la barra de atributo
        ancho_barra = 100  # Ancho total de la barra
        incremento = ancho_barra / float(maximo)  # Ancho de cada incremento en la barra

        # Dibujar la barra de atributo completa con borde blanco
        barra_rect = pygame.Rect(posicion[0], posicion[1] + 20, ancho_barra, 10)
        pygame.draw.rect(self.pantalla, (255, 255, 255), barra_rect, 1)  # Borde blanco de la barra

        # Calcular el ancho de la porción de la barra que representa el valor actual
        ancho_valor = valor * incremento

        # Dibujar la porción de la barra que representa el valor actual del atributo
        barra_valor_rect = pygame.Rect(posicion[0], posicion[1] + 20, ancho_valor, 10)
        pygame.draw.rect(self.pantalla, color, barra_valor_rect)  # Barra de atributo

        # Dibujar las divisiones en la barra de atributo
        for i in range(int(maximo) + 1):
            x = posicion[0] + i * incremento
            pygame.draw.line(self.pantalla, (255, 255, 255), (x, posicion[1] + 21), (x, posicion[1] + 29), 1)  # Barra vertical

    def dibujar_botones_pausa(self):
        # Definir los parámetros para los botones
        ancho_boton = 150
        alto_boton = 50
        color_fondo_boton_opciones = (0, 255, 255, 150)
        color_fondo_boton_salir = (255, 0, 0, 150)
        color_texto_boton = (255, 255, 255)

        # Calcular posiciones de los botones
        centro_x = self.pantalla_ancho // 2
        y_opciones = self.pantalla_alto // 2 + 50
        y_salir = self.pantalla_alto // 2 + 120

        # Crear botones
        self.boton_opciones = Boton("Opciones", color_fondo_boton_opciones, color_texto_boton, centro_x, y_opciones, ancho_boton, alto_boton,
                                    radio_borde=10)
        self.boton_salir = Boton("Salir", color_fondo_boton_salir, color_texto_boton, centro_x, y_salir, ancho_boton, alto_boton, radio_borde=10)

        # Dibujar botones
        self.boton_opciones.dibujar(self.pantalla, pygame.font.SysFont(None, 30))
        self.boton_salir.dibujar(self.pantalla, pygame.font.SysFont(None, 30))

    def mostrar_texto_centralizado(self, texto, color):
        """
        Muestra un texto en el centro de la pantalla.
        """
        font = pygame.font.SysFont(None, 36)  # Fuente y tamaño del texto
        texto_surface = font.render(texto, True, color)  # Texto, antialiasing y color
        texto_rect = texto_surface.get_rect(center=(self.pantalla_ancho // 2, self.pantalla_alto // 2))
        self.pantalla.blit(texto_surface, texto_rect)

    def dibujar_fondo_en_gris(self):
        """
        Dibuja el fondo en la pantalla con un tono gris cuando el juego está pausado.
        """
        fondo_gris1 = self.fondo_imagen1.copy()
        fondo_gris1.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
        self.pantalla.blit(fondo_gris1, (0, self.pos_y_fondo1))

        fondo_gris2 = self.fondo_imagen2.copy()
        fondo_gris2.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
        self.pantalla.blit(fondo_gris2, (0, self.pos_y_fondo2))

    def dibujar_elementos(self, elementos):
        """
        Dibuja una lista de elementos en la pantalla.
        """
        for elemento in elementos:
            if elemento is not None:
                if self.pausado:
                    self.dibujar_sprite_en_gris(elemento)
                else:
                    self.pantalla.blit(elemento.image, elemento.rect)

    def dibujar_sprite_en_gris(self, sprite):
        """
        Dibuja un sprite con tono grisáceo en la pantalla.
        """
        sprite_image_gris = sprite.image.copy()
        sprite_image_gris.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT)
        self.pantalla.blit(sprite_image_gris, sprite.rect)

    def mostrar_texto(self, texto_prefijo, posicion, color, valor=None, fuente=None):
        """
        Muestra un texto en la pantalla.
        """
        if fuente is None:
            fuente = pygame.font.SysFont(None, 36)  # Fuente y tamaño del texto

        # Si se pasa un valor, concatenarlo al texto prefijo
        if valor is not None:
            texto = f"{texto_prefijo}{valor}"
        else:
            texto = texto_prefijo

        texto_renderizado = fuente.render(texto, True, color)  # Texto, antialiasing y color
        self.pantalla.blit(texto_renderizado, posicion)

    def dibujar_barra_salud(self):
        """
        Dibuja la barra de salud del jugador en la pantalla del juego.
        """
        # Calcular la posición inicial de la barra de salud
        barra_x = self.jugador.rect.centerx - 25  # Centrar el rectángulo en relación con la barra de salud
        barra_y = self.jugador.rect.bottom + 10  # Ajustar la posición vertical para que esté debajo de la nave

        # Dibujar las barras verticales de la barra de salud
        for i in range(self.jugador.salud_maxima):
            if i < self.jugador.salud:  # Las barras de salud activas serán verdes
                color = (0, 255, 0)
            else:  # Las barras de salud inactivas serán grises
                color = (150, 150, 150)

            # Calcular la posición y el tamaño de cada barra de salud
            barra_salud_rect = pygame.Rect(barra_x + i * 10, barra_y, 8, 10)
            pygame.draw.rect(self.pantalla, color, barra_salud_rect)

        # Dibujar el rectángulo blanco alrededor de la barra de salud
        rectangulo_salud = pygame.Rect(barra_x, barra_y, self.jugador.salud_maxima * 10, 10)  # El ancho total de la barra de salud
        pygame.draw.rect(self.pantalla, (255, 255, 255), rectangulo_salud, 1)  # Grosor del borde: 1

    def dibujar_barra_salud_jefe(self):
        """
        Dibuja la barra de salud del jefe en la pantalla del juego.
        """
        # Calcular la posición inicial de la barra de salud del jefe
        barra_x = self.jefe.rect.centerx - self.jefe.rect.width // 2  # Centrar el rectángulo en relación con el jefe
        barra_y = self.jefe.rect.bottom - 210  # Posición vertical encima del jefe

        # Calcular el ancho de la barra de salud del jefe en relación con su salud actual y máxima
        ancho_barra = self.jefe.rect.width * (self.jefe.salud / self.jefe.salud_maxima)

        # Dibujar el rectángulo rojo encima del jefe para la barra de salud
        alto_barra = 15  # Altura fija de la barra de salud del jefe
        barra_salud_rect = pygame.Rect(barra_x, barra_y, ancho_barra, alto_barra)
        pygame.draw.rect(self.pantalla, (255, 0, 0), barra_salud_rect)

        # Dibujar el rectángulo blanco alrededor de la barra de salud del jefe
        rectangulo_salud = pygame.Rect(barra_x, barra_y, self.jefe.rect.width, alto_barra)
        pygame.draw.rect(self.pantalla, (255, 255, 255), rectangulo_salud, 1)  # Grosor del borde: 1

    def mostrar_texto_fps(self):
        """
        Muestra el FPS en la pantalla.
        """
        font_fps = pygame.font.SysFont(None, 24)  # Fuente y tamaño del texto
        # Texto, antialiasing y color
        texto_fps = font_fps.render(f"FPS: {int(self.reloj.get_fps())}", True, (128, 128, 128) if self.pausado else (255, 255, 255))
        self.pantalla.blit(texto_fps, (self.pantalla_ancho - texto_fps.get_width() - 10, 10))  # Mostrar el texto en la esquina superior derecha

    def ejecutar(self):
        """
        Ejecuta el juego.
        """
        ejecutando = True

        while ejecutando:
            pygame.display.set_caption("Galactic Guardian")
            ejecutando = self.manejar_eventos()

            # Si el juego está pausado, solo dibujar la pantalla y continuar al siguiente ciclo
            if self.pausado:
                self.dibujar()
                self.reloj.tick(60)
                continue

            # Actualizar el juego solo si el juego no está pausado
            self.actualizar()
            self.all_sprites.update()  # Actualizar todos los sprites
            self.dibujar()
            self.reloj.tick(60)

        pygame.quit()
