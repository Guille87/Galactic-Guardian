import time

import pygame
import pygame_gui

from galactic_guardian.juego import configuracion
from galactic_guardian.resources.resource_manager import ResourceManager
from galactic_guardian.juego.juego_principal import Juego
from galactic_guardian.ui.boton import Boton


# Instancia global de ResourceManager
resource_manager = ResourceManager()


def crear_pantalla():
    # Configuración de la pantalla
    pantalla_ancho = 600
    pantalla_alto = 800
    pantalla = pygame.display.set_mode((pantalla_ancho, pantalla_alto))
    pygame.display.set_caption("Galactic Guardian")
    return pantalla


def mostrar_menu(pantalla):
    # Cargar la configuración de música y sonido
    volumen_musica, volumen_efectos = configuracion.cargar_configuracion()

    # Iniciar música de fondo si aún no se ha iniciado
    if not resource_manager.is_music_playing("skyfire_theme"):
        resource_manager.play_music("skyfire_theme", loops=-1)
        resource_manager.set_music_volume("skyfire_theme", volumen_musica)

    # Obtener la imagen de fondo
    fondo = resource_manager.get_image("imagen_fondo1")

    # Crear el texto del título del juego
    titulo_font = pygame.font.Font(None, 76)
    titulo_surface = titulo_font.render("Galactic Guardian", True, (255, 255, 255))
    titulo_rect = titulo_surface.get_rect(center=(pantalla.get_width() // 2, 150))  # Centrar en la parte superior de la pantalla

    # Definir las propiedades del botón "Jugar"
    boton_ancho = 200
    boton_alto = 50
    boton_color = (0, 255, 0, 100)  # Verde brillante
    texto_color = (255, 255, 255)  # Blanco
    font = pygame.font.Font(None, 36)

    # Crear el botón "Jugar"
    boton_jugar = Boton("Jugar", boton_color, texto_color, pantalla.get_rect().centerx, 350, boton_ancho, boton_alto, radio_borde=10)

    # Definir las propiedades del botón "Opciones"
    boton_opciones_ancho = 200
    boton_opciones_alto = 50
    boton_opciones_color = (0, 0, 255, 128)  # Azul brillante y semitransparente

    # Crear el botón "Opciones"
    boton_opciones = Boton("Opciones", boton_opciones_color, texto_color, pantalla.get_rect().centerx, boton_jugar.rect.bottom + 20, boton_opciones_ancho,
                           boton_opciones_alto, radio_borde=10)

    while True:
        pygame.display.set_caption("Galactic Guardian")

        volumen_musica, volumen_efectos = configuracion.cargar_configuracion()

        resource_manager.set_music_volume("skyfire_theme", volumen_musica)

        pantalla.blit(fondo, (0, 0))  # Dibujar la imagen de fondo en toda la pantalla

        # Dibujar el título del juego en la pantalla
        pantalla.blit(titulo_surface, titulo_rect)

        # Dibujar los botones en la pantalla
        boton_jugar.dibujar(pantalla, font)
        boton_opciones.dibujar(pantalla, font)

        # Manejar eventos de usuario, como clics de mouse o pulsaciones de teclas
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pass
                    if boton_jugar.clic_en_boton(event.pos):
                        iniciar_juego(pantalla.get_width(), pantalla.get_height(), volumen_musica, volumen_efectos)
                    elif boton_opciones.clic_en_boton(event.pos):
                        mostrar_opciones(pantalla, volumen_musica, volumen_efectos)

        # Actualizar la pantalla
        pygame.display.flip()


def iniciar_juego(pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos):
    # Detener la música antes de salir de menu.py
    if resource_manager.is_music_playing("skyfire_theme"):
        resource_manager.stop_music("skyfire_theme")
    juego = Juego(pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos)
    juego.ejecutar()


def mostrar_opciones(pantalla, volumen_musica, volumen_efectos):
    pygame.display.set_caption("Opciones")

    manager = pygame_gui.UIManager((600, 800))

    # Cargar la imagen de fondo
    fondo = resource_manager.get_image("imagen_fondo1")

    texto_font = pygame.font.Font(None, 36)
    texto_surface = texto_font.render("Opciones", True, (255, 255, 255))
    texto_rect = texto_surface.get_rect(center=(300, 50))

    # Definir el texto de los controles
    controles_texto = ["CONTROLES",
                       "Moverse: W A S D o flechas de dirección",
                       "Disparar: Barra espaciadora o botón izquierdo del ratón",
                       "Pausar: Escape o P"]

    # Definir la fuente para el texto de los controles
    texto_font_controles = pygame.font.Font(None, 26)
    texto_color = (255, 255, 0)

    # Crear superficies de texto para los controles
    controles_surfaces = [texto_font_controles.render(texto, True, texto_color) for texto in controles_texto]

    # Obtener los rectángulos de las superficies de texto
    controles_rects = [texto_surface.get_rect(topleft=(50, 450 + i * 40)) for i, texto_surface in enumerate(controles_surfaces)]

    # Crear control deslizante para la música
    musica_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(relative_rect=pygame.Rect((50, 150), (500, 50)),
                                                                                start_value=volumen_musica,
                                                                                value_range=(0, 1),
                                                                                manager=manager,
                                                                                click_increment=0.1)

    musica_texto_surface = texto_font.render("Música:", True, (255, 255, 255))
    musica_texto_rect = musica_texto_surface.get_rect(topleft=(50, 120))

    # Crear control deslizante para los efectos de sonido
    efectos_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(relative_rect=pygame.Rect((50, 250), (500, 50)),
                                                                                 start_value=volumen_efectos,
                                                                                 value_range=(0, 1),
                                                                                 manager=manager,
                                                                                 click_increment=0.1)

    # Crear botón de guardar
    boton_guardar = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50, 350), (200, 50)),
                                                 text='Guardar',
                                                 manager=manager)

    # Crear botón de volver atrás
    boton_volver = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 350), (200, 50)),
                                                text='Volver',
                                                manager=manager)

    efectos_texto_surface = texto_font.render("Efectos de Sonido:", True, (255, 255, 255))
    efectos_texto_rect = efectos_texto_surface.get_rect(topleft=(50, 220))

    # Construir las rutas a los efectos de sonido
    efecto_disparo = resource_manager.get_sound("laser_gun")
    efecto_golpe = resource_manager.get_sound("hit")
    efecto_item = resource_manager.get_sound("item_take")

    # Lista de efectos de sonido
    efectos_sonido = [efecto_disparo, efecto_golpe, efecto_item]

    # Definir una bandera para controlar si el sonido de cambio de volumen está reproduciéndose
    sonido_reproduciendose = False
    tiempo_final_reproduccion = 0

    clock = pygame.time.Clock()
    ejecutando = True

    while ejecutando:
        tiempo_delta = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ejecutando = False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == musica_slider:
                        volumen_musica = event.value
                        resource_manager.set_music_volume("skyfire_theme", volumen_musica)
                    elif event.ui_element == efectos_slider:
                        volumen_efectos = event.value
                        # Iterar sobre los efectos de sonido y actualizar su volumen
                        for efecto in efectos_sonido:
                            efecto.set_volume(volumen_efectos)
                        # Reproducir un sonido al cambiar el volumen de los efectos de sonido
                        if not sonido_reproduciendose:
                            sonido_reproduciendose = True
                            # Reproducir el efecto de sonido
                            efecto_cambio_volumen = resource_manager.get_sound("laser_gun")
                            efecto_cambio_volumen.set_volume(volumen_efectos)
                            efecto_cambio_volumen.play()
                            # Obtener la duración del sonido de cambio de volumen
                            duracion_sonido = efecto_cambio_volumen.get_length()
                            # Establecer el tiempo final de reproducción
                            tiempo_final_reproduccion = time.time() + duracion_sonido
                elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == boton_guardar:
                        # Después de guardar la configuración, actualizar los valores de volumen
                        configuracion.guardar_configuracion(volumen_musica, volumen_efectos)
                        return
                    elif event.ui_element == boton_volver:
                        return  # Salir de la función mostrar_opciones

            manager.process_events(event)

        # Verificar si ha pasado el tiempo de reproducción del sonido
        if sonido_reproduciendose and time.time() >= tiempo_final_reproduccion:
            sonido_reproduciendose = False

        manager.update(tiempo_delta)

        pantalla.blit(fondo, (0, 0))
        pantalla.blit(texto_surface, texto_rect)
        pantalla.blit(musica_texto_surface, musica_texto_rect)
        pantalla.blit(efectos_texto_surface, efectos_texto_rect)

        # Dibujar los controles en la pantalla
        for control_surface, control_rect in zip(controles_surfaces, controles_rects):
            pantalla.blit(control_surface, control_rect)

        manager.draw_ui(pantalla)

        pygame.display.update()

    pygame.quit()
