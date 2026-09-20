import math
import time
import webbrowser

import pygame
import pygame_gui

from src.core import config, controles, i18n, settings, updates
from src.core.i18n import t
from src.core.version import __version__
from src.ui.components.button import Boton

# Escalón de las flechas ◄ ► (0.1). El arrastre de la barra es libre; solo se
# redondea a 2 decimales para no guardar basura de coma flotante.
_PASO_VOLUMEN = settings.VOLUMEN_PASO
_DECIMALES_VOLUMEN = 2


def _clamp_volumen(v):
    """Recorta a [0, 1] y redondea (arrastre libre).

    Un valor fuera de [0, 1], aunque sea por 1e-17, hace que `pygame_gui` cree
    el slider fuera de rango y lo deje sin responder.
    """
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.5
    return round(min(1.0, max(0.0, v)), _DECIMALES_VOLUMEN)


def _paso_volumen(v, subir):
    """Múltiplo de `_PASO_VOLUMEN` inmediatamente por encima/debajo de `v`.

    0.27 → flecha arriba 0.3, flecha abajo 0.2. 0.20 → 0.3 / 0.1.
    """
    n = round(v / _PASO_VOLUMEN, 6)
    objetivo = (math.floor(n) + 1 if subir else math.ceil(n) - 1) * _PASO_VOLUMEN
    return _clamp_volumen(objetivo)


class MenuManager:
    """
    Clase principal para gestionar las pantallas del menú (Estado).

    `ejecutar()` corre el bucle del menú y devuelve el siguiente estado de la
    máquina de alto nivel: "JUGAR" o "SALIR". El objeto es persistente: se
    reutiliza cada vez que se vuelve al menú desde la partida.
    """

    def __init__(self, pantalla, resource_manager, audio_manager, sistema_clasificacion):
        self.pantalla = pantalla
        self.rm = resource_manager
        self.am = audio_manager
        self.clasificacion = sistema_clasificacion
        self.font_titulo = pygame.font.Font(None, 76)
        self.font_estandar = pygame.font.Font(None, 36)
        self.font_version = pygame.font.Font(None, 24)
        self.ui_manager = None          # UI de opciones (pygame_gui); se crea una vez

        # Reloj único de la instancia (no crear uno nuevo por frame)
        self.clock = pygame.time.Clock()

        # Estado inicial
        self.estado = "PRINCIPAL"  # Posibles: PRINCIPAL, OPCIONES, PUNTUACIONES
        self.ejecutando = True
        self.resultado = None  # "JUGAR" | "SALIR"

        # Estado inicial de Opciones (ver `_sincronizar_estado`)
        self._sincronizar_estado()
        self._idioma_ui = None               # idioma con el que se construyó la UI de Opciones
        self._reasignando_accion = None      # acción esperando una pulsación, o None
        self._aviso_conflicto = None
        self._aviso_conflicto_hasta = 0
        self._crear_botones()

        # Control de feedback sonoro
        self.sonido_reproduciendose = False
        self.tiempo_final_reproduccion = 0
        # (destino, sube) de una flecha ◄ ► pulsada este frame, pendiente de
        # cuadrar al escalón al final del frame.
        self._flecha_pendiente = None
        # destino cuyo próximo UI_HORIZONTAL_SLIDER_MOVED hay que ignorar (es el
        # que pygame_gui emite tras una flecha que ya hemos cuadrado).
        self._ignorar_moved = None

        # Aviso de nueva versión (comprobación en segundo plano, best-effort)
        self.actualizaciones = updates.ComprobadorActualizaciones()
        self._descarga = None          # updates.DescargaActualizacion en curso
        self._descarga_fallo = False

    def _sincronizar_estado(self):
        """Vuelve a leer de la fuente de verdad lo que Opciones muestra.

        Volúmenes: los del `AudioManager` compartido, que son los que suenan
        ahora (los del `config.ini` pueden ser más viejos: un cambio hecho desde
        la pausa se aplica al instante pero solo se guarda con "Guardar").
        Teclas: las de `config.ini`, que es de donde lee cada partida nueva.

        Sin esto, el menú principal (persistente) enseñaba en Opciones lo que
        leyó al crearse y, al pulsar Guardar, pisaba con ello lo cambiado desde
        la pausa (que usa otro `MenuManager`, temporal)."""
        self.vol_musica = _clamp_volumen(self.am.vol_musica)
        self.vol_efectos = _clamp_volumen(self.am.vol_efectos)
        self.controles = config.cargar_controles()

    def _preparar_musica(self):
        """Usa el AudioManager para gestionar la música del menú."""
        self.am.reproducir_musica("skyfire_theme")

    def _crear_botones(self):
        """Botones del menú principal (sus textos se cachean: se rehacen al
        cambiar de idioma)."""
        self._idioma_botones = i18n.idioma_actual()
        cx = self.pantalla.get_rect().centerx
        self.btn_actualizar = Boton(
            t("menu.actualizar"), (255, 170, 0, 160), (0, 0, 0), cx, 270, 320, 44, 10,
        )
        self.btn_jugar = Boton(t("menu.jugar"), (0, 255, 0, 100), (255, 255, 255), cx, 350, 200, 50, 10)
        self.btn_opciones = Boton(t("comun.opciones"), (0, 0, 255, 128), (255, 255, 255), cx, 420, 200, 50, 10)
        self.btn_puntos = Boton(t("menu.puntuaciones"), (255, 255, 0, 128), (255, 255, 255), cx, 490, 200, 50, 10)
        self.btn_salir = Boton(t("comun.salir"), (255, 0, 0, 150), (255, 255, 255), cx, 560, 200, 50, 10)

    def ejecutar(self):
        """Bucle principal del menú. Devuelve el siguiente estado ("JUGAR"/"SALIR")."""
        # Reinicio de estado por si volvemos desde una partida
        self.ejecutando = True
        self.estado = "PRINCIPAL"
        self.resultado = None
        self._sincronizar_estado()                         # por si Opciones se tocó desde la pausa
        if self._idioma_botones != i18n.idioma_actual():   # ídem el idioma
            self._crear_botones()

        self._preparar_musica()  # Solo activamos la música aquí, al lanzar el menú completo
        self.actualizaciones.comprobar_en_segundo_plano()  # no-op si ya se lanzó

        while self.ejecutando:
            time_delta = self.clock.tick(settings.FPS) / 1000.0

            if self.estado == "PRINCIPAL":
                self._menu_principal()
            elif self.estado == "OPCIONES":
                self._menu_opciones(time_delta)
            elif self.estado == "PUNTUACIONES":
                self._menu_puntuaciones()

        return self.resultado or "SALIR"

    def _menu_principal(self):
        pygame.display.set_caption(t("ventana.titulo_menu", version=__version__))
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and not self._descargando_actualizacion():
                info = self.actualizaciones.resultado
                if isinstance(info, dict) and self._descarga is None \
                        and self.btn_actualizar.clic_en_boton(event.pos):
                    self._pulsar_actualizar(info)
                elif self.btn_jugar.clic_en_boton(event.pos):
                    self.am.detener_musica("skyfire_theme")
                    self.ejecutando = False
                    self.resultado = "JUGAR"
                elif self.btn_opciones.clic_en_boton(event.pos):
                    self._abrir_opciones()
                elif self.btn_puntos.clic_en_boton(event.pos):
                    self.estado = "PUNTUACIONES"
                elif self.btn_salir.clic_en_boton(event.pos):
                    if self._confirmar_salida():
                        self.ejecutando = False
                        self.resultado = "SALIR"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        titulo = self.font_titulo.render("Galactic Guardian", True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(300, 150)))

        self._dibujar_aviso_actualizacion()

        self.btn_jugar.dibujar(self.pantalla, self.font_estandar)
        self.btn_opciones.dibujar(self.pantalla, self.font_estandar)
        self.btn_puntos.dibujar(self.pantalla, self.font_estandar)
        self.btn_salir.dibujar(self.pantalla, self.font_estandar)

        # Versión, esquina inferior derecha
        txt_version = self.font_version.render(f"v{__version__}", True, (150, 150, 150))
        self.pantalla.blit(
            txt_version,
            txt_version.get_rect(bottomright=(settings.ANCHO - 8, settings.ALTO - 6)),
        )
        pygame.display.flip()

    def _confirmar_salida(self):
        """Diálogo bloqueante "¿Seguro que quieres salir?". Devuelve True si
        se confirma (también al cerrar la ventana con la X)."""
        cx = self.pantalla.get_rect().centerx
        boton_si = Boton(t("comun.si"), (50, 50, 50), (255, 255, 255), cx - 100, 320, 100, 50)
        boton_no = Boton(t("comun.no"), (50, 50, 50), (255, 255, 255), cx + 110, 320, 100, 50)

        fondo_oscuro = pygame.Surface((settings.ANCHO, settings.ALTO))
        fondo_oscuro.set_alpha(200)
        fondo_oscuro.fill((0, 0, 0))
        self.pantalla.blit(fondo_oscuro, (0, 0))

        rect_dialogo = pygame.Rect(50, 200, 500, 200)
        pygame.draw.rect(self.pantalla, (255, 255, 255), rect_dialogo)
        texto = self.font_estandar.render(t("menu.confirmar_salida"), True, (0, 0, 0))
        self.pantalla.blit(texto, texto.get_rect(center=(rect_dialogo.centerx, rect_dialogo.centery - 50)))
        boton_si.dibujar(self.pantalla, self.font_estandar)
        boton_no.dibujar(self.pantalla, self.font_estandar)
        pygame.display.flip()

        while True:
            self.clock.tick(settings.FPS)   # evita el busy-wait al 100 % de CPU
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    return True
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if boton_si.clic_en_boton(evento.pos):
                        return True
                    if boton_no.clic_en_boton(evento.pos):
                        return False

    def _abrir_opciones(self):
        """Entra en la pantalla de opciones: crea la UI (una vez) y sincroniza
        los sliders con los volúmenes actuales, ya saneados."""
        self.estado = "OPCIONES"
        self._flecha_pendiente = None
        self._ignorar_moved = None
        self._reasignando_accion = None
        self._aviso_conflicto = None
        # Recortar antes de crear/tocar el slider: un valor fuera de [0, 1]
        # (aunque sea por 1e-17) hace que pygame_gui lo ignore y el slider quede
        # descuadrado y sin responder.
        self.vol_musica = _clamp_volumen(self.vol_musica)
        self.vol_efectos = _clamp_volumen(self.vol_efectos)
        if self.ui_manager is not None and self._idioma_ui != i18n.idioma_actual():
            self.ui_manager = None       # construida en otro idioma (p. ej. cambiado desde la pausa)
        if self.ui_manager is None:
            self._inicializar_interfaz_opciones()
        self.slider_musica.set_current_value(self.vol_musica)
        self.slider_efectos.set_current_value(self.vol_efectos)
        for accion in controles.ACCIONES:      # por si quedó "Pulsa una tecla…" a medias
            self._actualizar_texto_control(accion)

    def _descargando_actualizacion(self):
        """True mientras la descarga está en curso (ni terminada ni fallida):
        se bloquea el resto del menú para no interrumpirla a medio camino."""
        return self._descarga is not None and not self._descarga.terminada and not self._descarga.error

    def _pulsar_actualizar(self, info):
        """Botón "Actualizar": descarga+instala si es la versión instalada y hay
        instalador **con hash para verificarlo**; si no (o si la descarga ya
        falló antes, p. ej. por un hash que no coincide) abre la web."""
        if (updates.puede_autoactualizar() and info.get("instalador_url")
                and info.get("instalador_sha256") and not self._descarga_fallo):
            self._descarga = updates.DescargaActualizacion(
                info["instalador_url"], info["instalador_sha256"])
            self._descarga.empezar()
        else:
            webbrowser.open(info["url"])

    def _dibujar_aviso_actualizacion(self):
        """Banner de nueva versión: botón, progreso de descarga o error."""
        info = self.actualizaciones.resultado
        if not isinstance(info, dict):
            return

        d = self._descarga
        if d is not None and d.terminada:
            # Descarga lista: lanzar el instalador y salir del juego.
            updates.lanzar_instalador(d.ruta)
            self.ejecutando = False
            self.resultado = "SALIR"
            return
        if d is not None and d.error:
            self._descarga = None
            self._descarga_fallo = True
            d = None

        if d is not None:
            texto = t("menu.actualizacion_descargando", pct=int(d.progreso * 100))
        elif self._descarga_fallo:
            texto = t("menu.actualizacion_fallo")
        else:
            texto = t("menu.actualizacion_disponible", version=info["version"])

        surf = self.font_version.render(texto, True, (255, 220, 120))
        self.pantalla.blit(surf, surf.get_rect(center=(300, 235)))
        if d is None:
            self.btn_actualizar.dibujar(self.pantalla, self.font_version)

    def _inicializar_interfaz_opciones(self):
        """Crea el UIManager y los elementos de la interfaz **una sola vez**.

        Antes se recreaba en cada entrada, dejando varios UIManager vivos."""
        # Las etiquetas (Música/Efectos/Controles y el aviso de las flechas)
        # se centran por defecto en pygame_gui; con este tema quedan alineadas
        # a la izquierda, al ras de los sliders y los botones.
        tema = {"label": {"misc": {"text_horiz_alignment": "left"}}}
        self.ui_manager = pygame_gui.UIManager((settings.ANCHO, settings.ALTO), tema)
        self._idioma_ui = i18n.idioma_actual()

        # Etiquetas
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 120), (200, 24)), text=t("opciones.musica"), manager=self.ui_manager
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 220), (200, 24)), text=t("opciones.efectos"), manager=self.ui_manager
        )

        # Sliders (click_increment: las flechas ◄ ► mueven el volumen de poco en poco)
        self.slider_musica = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 150), (500, 50)),
            start_value=self.vol_musica, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )
        self.slider_efectos = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 250), (500, 50)),
            start_value=self.vol_efectos, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )

        # Idioma: un botón por idioma disponible (el actual queda marcado). Se
        # aplica al instante; ver `_cambiar_idioma`.
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 320), (200, 24)), text=t("opciones.idioma"), manager=self.ui_manager
        )
        self._botones_idioma = {}   # UIButton -> código de idioma
        for codigo, x in zip(i18n.IDIOMAS, (50, 330)):
            boton = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((x, 350), (220, 44)),
                text=i18n.NOMBRES[codigo], manager=self.ui_manager,
            )
            self._botones_idioma[boton] = codigo
        self._marcar_idioma_actual()

        # Controles: un botón por acción reasignable. Las flechas y Esc son
        # fijas (siempre funcionan, no aparecen como botón) — el aviso de abajo
        # es justo para que el jugador sepa que no hace falta tocar nada si le
        # vale con ellas. Clic en un botón -> queda "escuchando" la próxima
        # tecla (ver `_procesar_tecla_reasignada`); Esc cancela sin cambiar nada.
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 410), (200, 24)), text=t("opciones.controles"), manager=self.ui_manager
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 434), (500, 22)),
            text=t("opciones.aviso_teclas_fijas"), manager=self.ui_manager,
        )
        self._botones_controles = {}   # acción -> UIButton
        self._acciones_por_boton = {}  # UIButton -> acción (inverso, para los eventos de clic)
        filas = (("arriba", "abajo"), ("izquierda", "derecha"), ("disparar", "pausa"))
        for fila, (accion_izq, accion_der) in enumerate(filas):
            y = 462 + fila * 54
            for accion, x in ((accion_izq, 50), (accion_der, 330)):
                boton = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((x, y), (220, 44)),
                    text=self._texto_boton_control(accion), manager=self.ui_manager,
                )
                self._botones_controles[accion] = boton
                self._acciones_por_boton[boton] = accion
        self.btn_restaurar_controles = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 624), (300, 40)),
            text=t("opciones.restaurar"), manager=self.ui_manager,
        )

        # Botones
        self.btn_guardar = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 722), (200, 50)), text=t("comun.guardar"), manager=self.ui_manager
        )
        self.btn_volver = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((350, 722), (200, 50)), text=t("comun.volver"), manager=self.ui_manager
        )

    def _marcar_idioma_actual(self):
        for boton, codigo in self._botones_idioma.items():
            if codigo == i18n.idioma_actual():
                boton.select()
            else:
                boton.unselect()

    def _cambiar_idioma(self, codigo):
        """Aplica un idioma al instante (como el volumen; se guarda con "Guardar").

        Los textos de los botones están cacheados (los de este menú y, en una
        partida, los de `Juego`), así que se rehacen: los del menú principal ya,
        y la UI de Opciones cuando `_menu_opciones` ve que `_idioma_ui` ya no es
        el actual (al empezar el próximo frame, no en mitad de un bucle de
        eventos que aún referencia los elementos viejos)."""
        if codigo == i18n.idioma_actual():
            return
        i18n.establecer_idioma(codigo)
        self._crear_botones()

    def _texto_boton_control(self, accion):
        return t("opciones.control_boton", accion=controles.etiqueta(accion),
                 tecla=controles.nombre_tecla(self.controles[accion]))

    def _actualizar_texto_control(self, accion):
        self._botones_controles[accion].set_text(self._texto_boton_control(accion))

    def _empezar_reasignacion(self, accion):
        if self._reasignando_accion is not None:
            self._actualizar_texto_control(self._reasignando_accion)   # restaura la anterior
        self._reasignando_accion = accion
        self._botones_controles[accion].set_text(t("opciones.pulsa_tecla"))

    def _procesar_tecla_reasignada(self, tecla):
        accion = self._reasignando_accion
        self._reasignando_accion = None
        if tecla == pygame.K_ESCAPE:
            self._actualizar_texto_control(accion)
            return
        conflicto = next((a for a, t in self.controles.items() if a != accion and t == tecla), None)
        if conflicto:
            self._aviso_conflicto = t("opciones.tecla_en_uso", tecla=controles.nombre_tecla(tecla),
                                     accion=controles.etiqueta(conflicto))
            self._aviso_conflicto_hasta = time.time() + 3.0
            self._actualizar_texto_control(accion)
            return
        self.controles[accion] = tecla
        self._actualizar_texto_control(accion)

    def _overlay_oscuro(self):
        """Capa negra semitransparente entre el fondo estrellado y el texto de
        Opciones y Puntuaciones: sin ella el cielo (blanco sobre negro) le comía
        el contraste al texto. Se crea una sola vez y se reutiliza."""
        if not hasattr(self, "_overlay_oscuro_surf"):
            overlay = pygame.Surface((settings.ANCHO, settings.ALTO))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self._overlay_oscuro_surf = overlay
        return self._overlay_oscuro_surf

    def _feedback_sonoro_efectos(self, reiniciar=False):
        """Sonido de prueba al ajustar el volumen de efectos.

        Al arrastrar el slider llegan muchos eventos seguidos, así que se deja
        terminar el sonido antes de repetirlo. Con las flechas (`reiniciar=True`)
        cada pulsación corta y relanza el sonido para oír el volumen nuevo.
        """
        sonido = self.rm.get_sound("laser_gun")
        if not sonido:
            return
        ahora = time.time()
        if reiniciar:
            sonido.stop()
        elif self.sonido_reproduciendose and ahora < self.tiempo_final_reproduccion:
            return
        self.sonido_reproduciendose = True
        sonido.play()
        self.tiempo_final_reproduccion = ahora + sonido.get_length()

    def _fijar_volumen(self, destino, valor, feedback_reiniciar=False):
        """Propaga un volumen ya validado: estado + slider + audio (+ prueba)."""
        slider = self.slider_musica if destino == "musica" else self.slider_efectos
        if destino == "musica":
            self.vol_musica = valor
            self.am.actualizar_volumen_musica(valor)
        else:
            self.vol_efectos = valor
            self.am.actualizar_volumen_efectos(valor)
        slider.set_current_value(valor)   # re-fija por si pygame_gui lo descuadró
        if destino == "efectos":
            self._feedback_sonoro_efectos(reiniciar=feedback_reiniciar)

    def _menu_opciones(self, time_delta):
        """Lógica de la pantalla de opciones usando pygame_gui."""
        if self.ui_manager is None or self._idioma_ui != i18n.idioma_actual():
            # entrada directa sin pasar por _abrir_opciones, o idioma cambiado:
            # se rehace la UI con los textos del idioma actual
            self._abrir_opciones()

        fondo = self.rm.get_image("imagen_fondo1")

        # {botón de flecha: (destino, sube?)}
        flechas = {
            self.slider_musica.left_button:   ("musica", False),
            self.slider_musica.right_button:  ("musica", True),
            self.slider_efectos.left_button:  ("efectos", False),
            self.slider_efectos.right_button: ("efectos", True),
        }
        sliders = {self.slider_musica: "musica", self.slider_efectos: "efectos"}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.estado = "PRINCIPAL"
                self.resultado = "SALIR"

            # --- Reasignación de teclas: la siguiente pulsación es la respuesta ---
            elif event.type == pygame.KEYDOWN and self._reasignando_accion is not None:
                self._procesar_tecla_reasignada(event.key)

            # --- Eventos de pygame_gui (API 0.6+: cada evento con su propio type) ---
            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in flechas:
                # Solo marcamos la dirección; el ajuste se hace al final del frame.
                self._flecha_pendiente = flechas[event.ui_element]

            elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED and event.ui_element in sliders:
                destino = sliders[event.ui_element]
                if self._ignorar_moved == destino:
                    # MOVED tardío de una flecha que ya cuadramos el frame anterior.
                    self._ignorar_moved = None
                    event.ui_element.set_current_value(
                        self.vol_musica if destino == "musica" else self.vol_efectos)
                elif self._flecha_pendiente is None or self._flecha_pendiente[0] != destino:
                    # Arrastre de la barra: valor libre, solo recortado.
                    self._fijar_volumen(destino, _clamp_volumen(event.ui_element.get_current_value()))

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self._botones_idioma:
                self._cambiar_idioma(self._botones_idioma[event.ui_element])

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self._acciones_por_boton:
                self._empezar_reasignacion(self._acciones_por_boton[event.ui_element])

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.btn_restaurar_controles:
                self.controles = dict(controles.POR_DEFECTO)
                for accion in controles.ACCIONES:
                    self._actualizar_texto_control(accion)

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.btn_guardar:
                    config.guardar_configuracion(self.vol_musica, self.vol_efectos, self.controles,
                                             idioma=i18n.idioma_actual())
                    self.estado = "PRINCIPAL"
                elif event.ui_element == self.btn_volver:
                    self.estado = "PRINCIPAL"

            self.ui_manager.process_events(event)

        # Flecha ◄ ►: pygame_gui ya ha aplicado su propio ±0.1 en este mismo
        # frame. Lo corregimos AQUÍ (antes de dibujar) al múltiplo de 0.1
        # anterior/siguiente al valor que había, para que no se vea el salto
        # intermedio; el MOVED que pygame_gui emite se ignora el próximo frame.
        if self._flecha_pendiente is not None:
            destino, sube = self._flecha_pendiente
            self._flecha_pendiente = None
            actual = self.vol_musica if destino == "musica" else self.vol_efectos
            self._fijar_volumen(destino, _paso_volumen(actual, sube), feedback_reiniciar=True)
            self._ignorar_moved = destino

        self.ui_manager.update(time_delta)

        # Al MANTENER pulsada una flecha >0.2 s, pygame_gui arranca un
        # desplazamiento continuo y rápido del slider. Reseteamos su acumulador
        # mientras la flecha siga pulsada para que solo cuente el clic limpio.
        for sl in (self.slider_musica, self.slider_efectos):
            if sl.left_button.held or sl.right_button.held:
                sl.button_held_repeat_acc = 0.0
        self.pantalla.blit(fondo, (0, 0))
        self.pantalla.blit(self._overlay_oscuro(), (0, 0))

        # Renderizar textos (Título, etiquetas de sliders)
        txt_opciones = self.font_titulo.render(t("opciones.titulo"), True, (255, 255, 255))
        self.pantalla.blit(txt_opciones, (50, 50))

        if self._aviso_conflicto and time.time() < self._aviso_conflicto_hasta:
            aviso = self.font_version.render(self._aviso_conflicto, True, (255, 120, 120))
            self.pantalla.blit(aviso, (50, 582))

        self.ui_manager.draw_ui(self.pantalla)
        pygame.display.flip()

    def mostrar_solo_opciones(self):
        """Muestra las opciones y retorna el control cuando se pulsa Guardar o Volver.

        Se usa desde la pausa de la partida. Devuelve "SALIR" si el usuario cerró
        la ventana (para que el motor propague el cierre), o None en caso normal.
        """
        self._abrir_opciones()

        bucle_opciones = True
        while bucle_opciones:
            time_delta = self.clock.tick(settings.FPS) / 1000.0
            self._menu_opciones(time_delta)

            # Salida normal: Guardar o Volver dejan el estado en PRINCIPAL
            if self.estado == "PRINCIPAL":
                bucle_opciones = False

            # Cierre de ventana durante la pausa: re-emitimos QUIT y salimos
            if self.resultado == "SALIR":
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return "SALIR"

        return None

    def _dibujar_fila_puntuaciones(self, textos, columnas, y, color):
        """Dibuja una fila de la tabla de puntuaciones (o su cabecera).

        `columnas`: `(etiqueta, x, alineacion)` por columna — `alineacion` es
        "izq" (x = borde izquierdo del texto) o "der" (x = borde derecho).
        """
        for texto, (_, x, alineacion) in zip(textos, columnas):
            surf = self.font_version.render(texto, True, color)
            px = x - surf.get_width() if alineacion == "der" else x
            self.pantalla.blit(surf, (px, y))

    def _menu_puntuaciones(self):
        """Pantalla de puntuaciones"""
        # Espera un clic para volver
        fondo = self.rm.get_image("imagen_fondo1")
        puntuaciones_top = self.clasificacion.obtener_puntuaciones_top()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.estado = "PRINCIPAL"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        self.pantalla.blit(self._overlay_oscuro(), (0, 0))

        # Título
        txt_titulo = self.font_titulo.render(t("puntuaciones.titulo"), True, (255, 255, 255))
        self.pantalla.blit(txt_titulo, txt_titulo.get_rect(center=(300, 100)))

        # Listado de puntos: cabecera + filas en columnas (nº, nombre, puntos, nivel).
        # `x` en "Puntos" es el borde derecho de la columna (texto alineado a la derecha).
        if puntuaciones_top:
            columnas = (("#", 60, "izq"), (t("puntuaciones.col_nombre"), 110, "izq"),
                       (t("puntuaciones.col_puntos"), 420, "der"), (t("puntuaciones.col_nivel"), 480, "izq"))
            y = 170
            self._dibujar_fila_puntuaciones(
                [c[0] for c in columnas], columnas, y, (200, 200, 200))
            y += 36

            for i, (nombre, puntos, nivel) in enumerate(puntuaciones_top, start=1):
                textos = (str(i), nombre, str(puntos), str(nivel) if nivel else "—")
                self._dibujar_fila_puntuaciones(textos, columnas, y, (255, 255, 255))
                y += 36
        else:
            aviso = self.font_estandar.render(t("puntuaciones.vacio"), True, (200, 200, 200))
            self.pantalla.blit(aviso, aviso.get_rect(center=(300, 400)))

        # Mensaje de salida
        txt_salir = self.font_estandar.render(t("puntuaciones.volver"), True, (150, 150, 150))
        self.pantalla.blit(txt_salir, txt_salir.get_rect(center=(300, 750)))

        pygame.display.flip()
