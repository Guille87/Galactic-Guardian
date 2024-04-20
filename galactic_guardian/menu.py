import time

import pygame
import pygame_gui
from galactic_guardian import configuracion


def crear_pantalla():
    # Inicializa Pygame
    pygame.init()

    # Configuración de la pantalla
    pantalla_ancho = 600
    pantalla_alto = 800
    pantalla = pygame.display.set_mode((pantalla_ancho, pantalla_alto))
    pygame.display.set_caption("Menú")
    return pantalla


def mostrar_menu(pantalla):
    # Cargar la configuración de música y sonido
    volumen_musica, volumen_efectos = configuracion.cargar_configuracion()

    # Inicializar música de fondo
    pygame.mixer.music.load('musica/SkyFire.ogg')  # Archivo de música de fondo
    pygame.mixer.music.set_volume(volumen_musica)  # Establecer volumen de la música de fondo
    pygame.mixer.music.play(-1)  # Reproducir música de fondo en bucle

    # Cargar la imagen de fondo
    fondo = pygame.image.load("imagenes/fondo1.png").convert_alpha()

    # Ajustes icono
    icono = pygame.image.load('imagenes/favicon.png')
    pygame.display.set_icon(icono)

    # Definir las propiedades del botón "Jugar"
    boton_ancho = 200
    boton_alto = 50
    boton_color = (0, 255, 0, 100)  # Verde brillante
    texto_color = (255, 255, 255)  # Blanco
    font = pygame.font.Font(None, 36)

    # Crear una superficie para el botón "Jugar" con transparencia
    boton_jugar_surface = pygame.Surface((boton_ancho, boton_alto), pygame.SRCALPHA)
    pygame.draw.rect(boton_jugar_surface, boton_color, boton_jugar_surface.get_rect(), border_radius=10)  # Dibujar el botón "Jugar" en la superficie

    # Crear el rectángulo del botón "Jugar" y centrarlo en la pantalla
    boton_jugar_rect = boton_jugar_surface.get_rect(centerx=pantalla.get_rect().centerx, y=350)

    # Crear el texto del título del juego
    titulo_font = pygame.font.Font(None, 76)
    titulo_surface = titulo_font.render("Galactic Guardian", True, texto_color)
    titulo_rect = titulo_surface.get_rect(center=(pantalla.get_width() // 2, 150))  # Centrar en la parte superior de la pantalla

    # Definir las propiedades del botón "Opciones"
    boton_opciones_ancho = 200
    boton_opciones_alto = 50
    boton_opciones_color = (0, 0, 255, 128)  # Azul brillante y semitransparente

    # Crear una superficie para el botón "Opciones" con transparencia
    boton_opciones_surface = pygame.Surface((boton_opciones_ancho, boton_opciones_alto), pygame.SRCALPHA)
    pygame.draw.rect(boton_opciones_surface, boton_opciones_color, boton_opciones_surface.get_rect(),
                     border_radius=10)  # Dibujar el botón "Opciones" en la superficie

    # Crear el rectángulo del botón "Opciones" y centrarlo horizontalmente en la pantalla debajo del botón "Jugar"
    boton_opciones_rect = boton_opciones_surface.get_rect(centerx=pantalla.get_rect().centerx, y=boton_jugar_rect.bottom + 20)

    while True:
        pygame.display.set_caption("Galactic Guardian")

        volumen_musica, volumen_efectos = configuracion.cargar_configuracion()

        pygame.mixer.music.set_volume(volumen_musica)  # Establecer volumen de la música de fondo

        pantalla.blit(fondo, (0, 0))  # Dibujar la imagen de fondo en toda la pantalla

        # Dibujar el título del juego en la pantalla
        pantalla.blit(titulo_surface, titulo_rect)

        # Dibujar el botón en la pantalla
        pantalla.blit(boton_jugar_surface, boton_jugar_rect)

        # Crear el texto "Jugar" y centrarlo en el botón
        texto_surface = font.render("Jugar", True, texto_color)
        texto_rect = texto_surface.get_rect(center=boton_jugar_rect.center)
        pantalla.blit(texto_surface, texto_rect)

        # Dibujar el botón "Opciones" en la pantalla
        pantalla.blit(boton_opciones_surface, boton_opciones_rect)

        # Crear el texto "Opciones" y centrarlo en el botón
        texto_opciones_surface = font.render("Opciones", True, texto_color)
        texto_opciones_rect = texto_opciones_surface.get_rect(center=boton_opciones_rect.center)
        pantalla.blit(texto_opciones_surface, texto_opciones_rect)

        # Manejar eventos de usuario, como clics de mouse o pulsaciones de teclas
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if boton_jugar_rect.collidepoint(event.pos):
                        iniciar_juego(pantalla.get_width(), pantalla.get_height(), volumen_musica, volumen_efectos)
                    elif boton_opciones_rect.collidepoint(event.pos):
                        mostrar_opciones(pantalla, volumen_musica, volumen_efectos)

        # Actualizar la pantalla
        pygame.display.flip()


def iniciar_juego(pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos):
    from juego import Juego
    juego = Juego(pantalla_ancho, pantalla_alto, volumen_musica, volumen_efectos)
    juego.ejecutar()


def mostrar_opciones(pantalla, volumen_musica, volumen_efectos):
    pygame.display.set_caption("Opciones")

    manager = pygame_gui.UIManager((600, 800))

    # Cargar la imagen de fondo
    fondo = pygame.image.load("imagenes/fondo1.png").convert_alpha()

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
                                                                                start_value=0.5,
                                                                                value_range=(0, 1),
                                                                                manager=manager,
                                                                                click_increment=0.1)

    musica_texto_surface = texto_font.render("Música:", True, (255, 255, 255))
    musica_texto_rect = musica_texto_surface.get_rect(topleft=(50, 120))

    # Crear control deslizante para los efectos de sonido
    efectos_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(relative_rect=pygame.Rect((50, 250), (500, 50)),
                                                                                 start_value=0.5,
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

    # Definir efectos de sonido
    efecto_disparo = pygame.mixer.Sound('sonidos/laser-gun.wav')  # Efecto de sonido del disparo
    efecto_golpe = pygame.mixer.Sound('sonidos/hit.wav')  # Archivo de efecto de sonido de golpe
    efecto_item = pygame.mixer.Sound('sonidos/item-take.wav')  # Efecto de sonido del objeto

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
                        pygame.mixer.music.set_volume(volumen_musica)  # Actualizar el volumen de la música
                    elif event.ui_element == efectos_slider:
                        volumen_efectos = event.value
                        # Iterar sobre los efectos de sonido y actualizar su volumen
                        for efecto in efectos_sonido:
                            efecto.set_volume(volumen_efectos)
                        # Reproducir un sonido al cambiar el volumen de los efectos de sonido
                        if not sonido_reproduciendose:
                            sonido_reproduciendose = True
                            # Reproducir el efecto de sonido
                            efecto_cambio_volumen = pygame.mixer.Sound('sonidos/laser-gun.wav')
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
