import math
import time
import webbrowser

import pygame
import pygame_gui

from src.core import config, controles, i18n, mejoras, paths, preferencias, settings, updates
from src.core.progresion import BLOQUEADA, COMPRADA, DISPONIBLE, SIN_SALDO, Progresion
from src.core.i18n import t
from src.core.version import __version__
from src.ui.components.button import Boton

# Pestañas de Opciones, en el orden en que se muestran; el nombre es también el
# sufijo de su clave de texto (`opciones.<nombre>`).
PESTANAS = ("controles", "idioma", "audio", "pantalla")

# Menú principal: el título y los cinco botones forman un bloque centrado en la
# pantalla (como el de la pausa); el aviso de nueva versión, que solo aparece a
# veces, va debajo para no reservar un hueco vacío entre el título y los botones.
_MENU_TITULO_Y = 150        # centro del título
_MENU_BOTONES_Y = 265       # borde superior del primer botón
_MENU_BOTONES_PASO = 70     # separación entre botones (altura 50 + 20)
_MENU_AVISO_Y = 700         # centro del texto del aviso; su botón va justo debajo

# Pantalla "Mejoras": tres columnas (una por rama) de nodos, en una zona que se
# desplaza cuando las ramas son más largas de lo que cabe (rueda del ratón, barra
# lateral o teclas). Los rects de los nodos se guardan en coordenadas del contenido
# (el primero en y = 0); `_rect_pantalla` los pasa a coordenadas de pantalla.
_MEJ_COL_X = (15, 215, 415)     # borde izquierdo de cada columna
_MEJ_ANCHO = 170
_MEJ_AREA = pygame.Rect(0, 210, 600, 456)   # zona visible de los nodos
_MEJ_ALTO = 98
_MEJ_PASO = 112                 # de un nodo al siguiente (alto + hueco para el conector)
_MEJ_PASO_RUEDA = 56            # píxeles que desplaza un "clic" de la rueda o una flecha
MONEDAS_DEPURACION = 1000      # lo que da la tecla F2 de depuración en Mejoras
_MEJ_UMBRAL_ARRASTRE = 6          # píxeles que hay que mover el ratón pulsado para que deje de ser un clic
_MEJ_BARRA_X = 590              # barra de desplazamiento (a la derecha de la tercera columna)
_MEJ_BARRA_ANCHO = 6
_MEJ_AVISO_MS = 2500            # cuánto dura un aviso de la pantalla
_MEJ_ICONO = 28                 # lado del icono de un nodo (esquina superior derecha)


def _rect_mejora(rama_i, orden):
    """Rect del nodo número `orden` (0, 1, 2...) de la rama número `rama_i`, en
    coordenadas del contenido."""
    return pygame.Rect(_MEJ_COL_X[rama_i], orden * _MEJ_PASO, _MEJ_ANCHO, _MEJ_ALTO)


def _ajustar_texto(fuente, texto, ancho):
    """Parte `texto` en líneas que quepan en `ancho` píxeles (por palabras)."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if actual and fuente.size(prueba)[0] > ancho:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas

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
    máquina de alto nivel: "JUGAR" (campaña), "JUGAR_SIN_FIN" o "SALIR". El
    objeto es persistente: se reutiliza cada vez que se vuelve al menú desde la
    partida.

    `sistema_clasificacion` es el ranking de la campaña y `clasificacion_sin_fin`
    el del modo sin fin (la pausa, que solo abre Opciones, no lo necesita).
    """

    def __init__(self, pantalla, resource_manager, audio_manager, sistema_clasificacion,
                 clasificacion_sin_fin=None, progresion=None):
        self.pantalla = pantalla
        self.rm = resource_manager
        self.am = audio_manager
        self.clasificacion = sistema_clasificacion
        self.clasificacion_sin_fin = clasificacion_sin_fin
        # Monedas y mejoras (pantalla "Mejoras"); sin ella, una en memoria que no toca el disco
        self.progresion = progresion if progresion is not None else Progresion(persistir=False)
        self._aviso_mejoras = None              # (texto, instante en que caduca)
        self._iconos_mejoras = {}               # (imagen, atenuado) -> Surface del icono
        self._scroll_mejoras = 0                # píxeles desplazados de la zona de nodos
        self._arrastrando_barra = False         # el ratón tiene agarrada la barra de desplazamiento
        self._arrastre_mejoras = None           # pulsación en la zona de nodos: [pos, scroll inicial, ya se arrastró]
        self._rects_mejoras = {                 # id de mejora -> Rect de su nodo
            m.id: _rect_mejora(i, orden)
            for i, rama in enumerate(mejoras.RAMAS) for orden, m in enumerate(mejoras.de_la_rama(rama))
        }
        self._modo_puntuaciones = settings.MODO_CAMPANA   # ranking que enseña la pantalla de Puntuaciones
        self._pestanas_puntuaciones = {}                  # modo -> Rect de su pestaña (lo rellena el dibujado)
        self.font_titulo = pygame.font.Font(None, 76)
        self.font_estandar = pygame.font.Font(None, 36)
        self.font_version = pygame.font.Font(None, 24)
        self.font_mini = pygame.font.Font(None, 20)
        self.ui_manager = None          # UI de opciones (pygame_gui); se crea una vez

        # Reloj único de la instancia (no crear uno nuevo por frame)
        self.clock = pygame.time.Clock()

        # Estado inicial
        self.estado = "PRINCIPAL"  # Posibles: PRINCIPAL, OPCIONES, PUNTUACIONES, MEJORAS
        self.ejecutando = True
        self.resultado = None  # "JUGAR" | "JUGAR_SIN_FIN" | "SALIR"

        # Estado inicial de Opciones (ver `_sincronizar_estado`)
        self._sincronizar_estado()
        self._idioma_ui = None               # idioma con el que se construyó la UI de Opciones
        self._instantanea = None             # lo que había al entrar en Opciones (lo restaura Volver)
        self._pestana = PESTANAS[0]          # pestaña de Opciones que se está viendo
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
            t("menu.actualizar"), (255, 170, 0, 160), (0, 0, 0), cx, _MENU_AVISO_Y + 17, 320, 44, 10,
        )
        # `btn_jugar` es el de la campaña (el "Jugar" de siempre)
        y = [_MENU_BOTONES_Y + i * _MENU_BOTONES_PASO for i in range(6)]
        self.btn_jugar = Boton(t("menu.campana"), (0, 255, 0, 100), (255, 255, 255), cx, y[0], 200, 50, 10)
        self.btn_sin_fin = Boton(t("menu.sin_fin"), (170, 0, 255, 128), (255, 255, 255), cx, y[1], 200, 50, 10)
        self.btn_mejoras = Boton(t("menu.mejoras"), (255, 130, 0, 140), (255, 255, 255), cx, y[2], 200, 50, 10)
        self.btn_opciones = Boton(t("comun.opciones"), (0, 0, 255, 128), (255, 255, 255), cx, y[3], 200, 50, 10)
        self.btn_puntos = Boton(t("menu.puntuaciones"), (255, 255, 0, 128), (255, 255, 255), cx, y[4], 200, 50, 10)
        self.btn_salir = Boton(t("comun.salir"), (255, 0, 0, 150), (255, 255, 255), cx, y[5], 200, 50, 10)
        # Botones de la pantalla "Mejoras"
        self.btn_restablecer_mejoras = Boton(t("mejoras.restablecer"), (255, 130, 0, 150), (255, 255, 255),
                                             150, 705, 200, 50, 10)
        self.btn_volver_mejoras = Boton(t("comun.volver"), (0, 0, 255, 128), (255, 255, 255), 450, 705, 200, 50, 10)

    def ejecutar(self):
        """Bucle principal del menú. Devuelve el siguiente estado
        ("JUGAR"/"JUGAR_SIN_FIN"/"SALIR")."""
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
            elif self.estado == "MEJORAS":
                self._menu_mejoras()

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
                elif self.btn_sin_fin.clic_en_boton(event.pos):
                    self.am.detener_musica("skyfire_theme")
                    self.ejecutando = False
                    self.resultado = "JUGAR_SIN_FIN"
                elif self.btn_mejoras.clic_en_boton(event.pos):
                    self._abrir_mejoras()
                elif self.btn_opciones.clic_en_boton(event.pos):
                    self._abrir_opciones()
                elif self.btn_puntos.clic_en_boton(event.pos):
                    self._modo_puntuaciones = settings.MODO_CAMPANA
                    self.estado = "PUNTUACIONES"
                elif self.btn_salir.clic_en_boton(event.pos):
                    if self._confirmar_salida():
                        self.ejecutando = False
                        self.resultado = "SALIR"

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        titulo = self.font_titulo.render("Galactic Guardian", True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(300, _MENU_TITULO_Y)))

        self._dibujar_aviso_actualizacion()

        self.btn_jugar.dibujar(self.pantalla, self.font_estandar)
        self.btn_sin_fin.dibujar(self.pantalla, self.font_estandar)
        self.btn_mejoras.dibujar(self.pantalla, self.font_estandar)
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
        """Entra en Opciones (desde el menú o desde la pausa).

        Los cambios se aplican al instante como vista previa, pero **Volver los
        descarta** y solo **Guardar** los confirma (y los escribe en disco). Por
        eso aquí se toma una instantánea de lo que se puede tocar, que
        `_deshacer_cambios` restaura."""
        self._pestana = PESTANAS[0]          # siempre se entra por la primera
        self._instantanea = {
            "vol_musica": self.am.vol_musica,
            "vol_efectos": self.am.vol_efectos,
            "idioma": i18n.idioma_actual(),
            "controles": dict(self.controles),
            "temblor": preferencias.temblor_activado(),
        }
        self._preparar_ui_opciones()

    def _deshacer_cambios(self):
        """Restaura lo que había al entrar en Opciones (botón Volver, o cerrar la
        ventana). No toca `config.ini`: nada de lo descartado llegó a guardarse."""
        inst = self._instantanea
        if inst is None:
            return
        self.vol_musica, self.vol_efectos = inst["vol_musica"], inst["vol_efectos"]
        self.am.actualizar_volumen_musica(self.vol_musica)
        self.am.actualizar_volumen_efectos(self.vol_efectos)
        self.controles = dict(inst["controles"])
        preferencias.establecer_temblor(inst["temblor"])
        if inst["idioma"] != i18n.idioma_actual():
            i18n.establecer_idioma(inst["idioma"])
            self._crear_botones()          # la UI de Opciones se rehace sola (`_idioma_ui`)

    def _preparar_ui_opciones(self):
        """Crea la UI de Opciones (una vez) y sincroniza los sliders con los
        volúmenes actuales, ya saneados. También la rehace si cambió el idioma."""
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
        self._actualizar_boton_temblor()       # puede haberse cambiado desde otro `MenuManager`
        self._mostrar_pestana(self._pestana)   # la UI puede venir con otra pestaña a la vista

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
        self.pantalla.blit(surf, surf.get_rect(center=(300, _MENU_AVISO_Y)))
        if d is None:
            self.btn_actualizar.dibujar(self.pantalla, self.font_version)

    def _inicializar_interfaz_opciones(self):
        """Crea el UIManager y los elementos de la interfaz **una sola vez**.

        Las opciones se reparten en pestañas (Audio / Idioma / Controles): cada
        una es un grupo de elementos que se muestra u oculta (`_mostrar_pestana`).
        Guardar y Volver son comunes a todas: actúan sobre lo tocado en cualquiera.

        Antes se recreaba en cada entrada, dejando varios UIManager vivos."""
        # Las etiquetas (Música/Efectos y el aviso de las flechas) se centran
        # por defecto en pygame_gui; con este tema quedan alineadas a la
        # izquierda, al ras de los sliders y los botones.
        tema = {"label": {"misc": {"text_horiz_alignment": "left"}}}
        self.ui_manager = pygame_gui.UIManager((settings.ANCHO, settings.ALTO), tema)
        self._idioma_ui = i18n.idioma_actual()
        self._elementos_pestana = {nombre: [] for nombre in PESTANAS}

        # Pestañas: una fila de botones bajo el título (la activa queda marcada).
        self._botones_pestana = {}   # UIButton -> nombre de pestaña
        for nombre, x in zip(PESTANAS, (50, 178, 306, 434)):
            boton = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((x, 120), (116, 44)),
                text=t(f"opciones.{nombre}"), manager=self.ui_manager,
            )
            self._botones_pestana[boton] = nombre

        # --- Audio ---
        self._elementos_pestana["audio"] += [
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((50, 210), (200, 24)), text=t("opciones.musica"), manager=self.ui_manager
            ),
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((50, 310), (200, 24)), text=t("opciones.efectos"), manager=self.ui_manager
            ),
        ]
        # Sliders (click_increment: las flechas ◄ ► mueven el volumen de poco en poco)
        self.slider_musica = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 240), (500, 50)),
            start_value=self.vol_musica, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )
        self.slider_efectos = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect((50, 340), (500, 50)),
            start_value=self.vol_efectos, value_range=(0, 1),
            click_increment=settings.VOLUMEN_PASO, manager=self.ui_manager
        )
        self._elementos_pestana["audio"] += [self.slider_musica, self.slider_efectos]

        # --- Idioma: un botón por idioma disponible (el actual queda marcado).
        # Se aplica al instante; ver `_cambiar_idioma`.
        self._botones_idioma = {}   # UIButton -> código de idioma
        for codigo, x in zip(i18n.IDIOMAS, (50, 330)):
            boton = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((x, 220), (220, 44)),
                text=i18n.NOMBRES[codigo], manager=self.ui_manager,
            )
            self._botones_idioma[boton] = codigo
            self._elementos_pestana["idioma"].append(boton)
        self._marcar_idioma_actual()

        # --- Controles: un botón por acción reasignable. Las flechas y Esc son
        # fijas (siempre funcionan, no aparecen como botón) — el aviso de arriba
        # es justo para que el jugador sepa que no hace falta tocar nada si le
        # vale con ellas. Clic en un botón -> queda "escuchando" la próxima
        # tecla (ver `_procesar_tecla_reasignada`); Esc cancela sin cambiar nada.
        self._elementos_pestana["controles"].append(pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 210), (500, 22)),
            text=t("opciones.aviso_teclas_fijas"), manager=self.ui_manager,
        ))
        self._botones_controles = {}   # acción -> UIButton
        self._acciones_por_boton = {}  # UIButton -> acción (inverso, para los eventos de clic)
        filas = (("arriba", "abajo"), ("izquierda", "derecha"), ("disparar", "pausa"))
        for fila, (accion_izq, accion_der) in enumerate(filas):
            y = 245 + fila * 54
            for accion, x in ((accion_izq, 50), (accion_der, 330)):
                boton = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect((x, y), (220, 44)),
                    text=self._texto_boton_control(accion), manager=self.ui_manager,
                )
                self._botones_controles[accion] = boton
                self._acciones_por_boton[boton] = accion
                self._elementos_pestana["controles"].append(boton)
        self.btn_restaurar_controles = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 447), (300, 40)),
            text=t("opciones.restaurar"), manager=self.ui_manager,
        )
        self._elementos_pestana["controles"].append(self.btn_restaurar_controles)

        # --- Pantalla: interruptor del temblor de pantalla. Se aplica al instante;
        # se guarda con "Guardar".
        self.btn_temblor = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 220), (500, 44)), text="", manager=self.ui_manager,
        )
        self._elementos_pestana["pantalla"] += [
            self.btn_temblor,
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((50, 274), (500, 22)),
                text=t("opciones.temblor_ayuda"), manager=self.ui_manager,
            ),
        ]
        self._actualizar_boton_temblor()

        # Botones comunes (siempre visibles)
        self.btn_guardar = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 722), (200, 50)), text=t("comun.guardar"), manager=self.ui_manager
        )
        self.btn_volver = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((350, 722), (200, 50)), text=t("comun.volver"), manager=self.ui_manager
        )
        self._mostrar_pestana(self._pestana)

    def _mostrar_pestana(self, nombre):
        """Muestra los elementos de una pestaña y oculta los de las demás.

        Los ocultos no reciben clics (así no estorban los que quedan encima)."""
        if self._reasignando_accion is not None:          # dejar de escuchar una tecla a medias
            self._actualizar_texto_control(self._reasignando_accion)
            self._reasignando_accion = None
        self._pestana = nombre
        for otra, elementos in self._elementos_pestana.items():
            for elemento in elementos:
                if otra == nombre:
                    elemento.show()
                else:
                    elemento.hide()
        for boton, de_esta in self._botones_pestana.items():
            if de_esta == nombre:
                boton.select()
            else:
                boton.unselect()

    def _actualizar_boton_temblor(self):
        """Texto y marca del interruptor según el estado actual de los efectos."""
        activos = preferencias.temblor_activado()
        estado = t("comun.si") if activos else t("comun.no")
        self.btn_temblor.set_text(t("opciones.temblor", estado=estado))
        if activos:
            self.btn_temblor.select()
        else:
            self.btn_temblor.unselect()

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
        if self.ui_manager is None:                 # entrada directa sin pasar por _abrir_opciones
            self._abrir_opciones()
        elif self._idioma_ui != i18n.idioma_actual():
            self._preparar_ui_opciones()            # idioma cambiado: rehacer la UI con los textos nuevos

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
                self._deshacer_cambios()
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

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self._botones_pestana:
                self._mostrar_pestana(self._botones_pestana[event.ui_element])

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self._botones_idioma:
                self._cambiar_idioma(self._botones_idioma[event.ui_element])

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.btn_temblor:
                preferencias.establecer_temblor(not preferencias.temblor_activado())
                self._actualizar_boton_temblor()

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self._acciones_por_boton:
                self._empezar_reasignacion(self._acciones_por_boton[event.ui_element])

            elif event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == self.btn_restaurar_controles:
                self.controles = dict(controles.POR_DEFECTO)
                for accion in controles.ACCIONES:
                    self._actualizar_texto_control(accion)

            elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.btn_guardar:
                    config.guardar_configuracion(self.vol_musica, self.vol_efectos, self.controles,
                                                 idioma=i18n.idioma_actual(),
                                                 temblor=preferencias.temblor_activado())
                    self.estado = "PRINCIPAL"
                elif event.ui_element == self.btn_volver:
                    self._deshacer_cambios()
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

        if (self._pestana == "controles" and self._aviso_conflicto
                and time.time() < self._aviso_conflicto_hasta):
            aviso = self.font_version.render(self._aviso_conflicto, True, (255, 120, 120))
            self.pantalla.blit(aviso, (50, 497))

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

    # ------------------------------------------------------------------ MEJORAS
    def _abrir_mejoras(self):
        self._aviso_mejoras = None
        self._scroll_mejoras = 0
        self._arrastrando_barra = False
        self._arrastre_mejoras = None
        self.estado = "MEJORAS"

    def _altura_contenido(self):
        """Alto total de las ramas (la más larga), más un pequeño margen abajo."""
        filas = max((len(mejoras.de_la_rama(r)) for r in mejoras.RAMAS), default=0)
        return max(0, filas * _MEJ_PASO - (_MEJ_PASO - _MEJ_ALTO)) + 8

    def _scroll_maximo(self):
        return max(0, self._altura_contenido() - _MEJ_AREA.height)

    def _desplazar_mejoras(self, pixeles):
        """Mueve la zona de nodos (positivo = hacia abajo), sin salirse del contenido."""
        self._scroll_mejoras = max(0, min(self._scroll_maximo(), self._scroll_mejoras + pixeles))

    def _rect_pantalla(self, id_):
        """Rect de un nodo en la pantalla (según lo desplazado que esté)."""
        return self._rects_mejoras[id_].move(0, _MEJ_AREA.top - self._scroll_mejoras)

    def _rect_barra(self):
        """`(pista, agarrador)` de la barra de desplazamiento, o `None` si no hace falta."""
        maximo = self._scroll_maximo()
        if maximo <= 0:
            return None
        pista = pygame.Rect(_MEJ_BARRA_X, _MEJ_AREA.top, _MEJ_BARRA_ANCHO, _MEJ_AREA.height)
        alto = max(30, round(_MEJ_AREA.height * _MEJ_AREA.height / self._altura_contenido()))
        y = pista.top + round((pista.height - alto) * self._scroll_mejoras / maximo)
        return pista, pygame.Rect(pista.left, y, pista.width, alto)

    def _arrastrar_barra_a(self, y):
        """Coloca el agarrador de la barra con su centro en `y` (coordenada de pantalla)."""
        barra = self._rect_barra()
        if barra is None:
            return
        pista, agarrador = barra
        recorrido = pista.height - agarrador.height
        fraccion = (y - agarrador.height / 2 - pista.top) / recorrido if recorrido else 0
        self._scroll_mejoras = max(0, min(self._scroll_maximo(), round(fraccion * self._scroll_maximo())))

    def _evento_mejoras(self, event):
        """Rueda, barra lateral y teclas de desplazamiento de la pantalla de mejoras."""
        if event.type == pygame.MOUSEWHEEL:
            self._desplazar_mejoras(-event.y * _MEJ_PASO_RUEDA)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2 and paths.es_desarrollo():      # depuración: monedas gratis
                self.progresion.ingresar(MONEDAS_DEPURACION)
            elif event.key == pygame.K_UP:
                self._desplazar_mejoras(-_MEJ_PASO_RUEDA)
            elif event.key == pygame.K_DOWN:
                self._desplazar_mejoras(_MEJ_PASO_RUEDA)
            elif event.key == pygame.K_PAGEUP:
                self._desplazar_mejoras(-_MEJ_AREA.height)
            elif event.key == pygame.K_PAGEDOWN:
                self._desplazar_mejoras(_MEJ_AREA.height)
            elif event.key == pygame.K_HOME:
                self._scroll_mejoras = 0
            elif event.key == pygame.K_END:
                self._scroll_mejoras = self._scroll_maximo()
        elif event.type == pygame.MOUSEMOTION:
            if self._arrastrando_barra:
                self._arrastrar_barra_a(event.pos[1])
            elif self._arrastre_mejoras is not None:
                if event.buttons[0]:
                    self._arrastrar_contenido(event.pos)
                else:                                       # se soltó fuera de la ventana
                    self._arrastre_mejoras = None
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._arrastrando_barra = False
            arrastre, self._arrastre_mejoras = self._arrastre_mejoras, None
            if arrastre is not None and not arrastre[2]:    # un toque, no un arrastre: es una compra
                self._comprar_en(arrastre[0])

    def _arrastrar_contenido(self, pos):
        """Arrastrar con el ratón pulsado (como en el móvil): el contenido sigue al puntero.
        Hasta que se mueve `_MEJ_UMBRAL_ARRASTRE` px cuenta como un toque y no como un arrastre,
        para que un clic con un pequeño temblor de la mano siga comprando."""
        origen, scroll_inicial, arrastrado = self._arrastre_mejoras
        dy = pos[1] - origen[1]
        if not arrastrado and abs(dy) < _MEJ_UMBRAL_ARRASTRE:
            return
        self._arrastre_mejoras[2] = True
        self._scroll_mejoras = max(0, min(self._scroll_maximo(), scroll_inicial - dy))

    def _avisar_mejoras(self, texto):
        self._aviso_mejoras = (texto, pygame.time.get_ticks() + _MEJ_AVISO_MS)

    def _clic_mejoras(self, pos):
        """Volver, Restablecer o comprar el nodo pulsado."""
        if self.btn_volver_mejoras.clic_en_boton(pos):
            self.estado = "PRINCIPAL"
        elif self.btn_restablecer_mejoras.clic_en_boton(pos):
            devuelto = self.progresion.restablecer()
            self._avisar_mejoras(t("mejoras.aviso_restablecido", n=devuelto) if devuelto
                                 else t("mejoras.aviso_nada"))
        elif self._clic_en_barra(pos):
            pass
        elif _MEJ_AREA.collidepoint(pos):
            # Todavía no se sabe si es un toque (comprar) o el inicio de un arrastre: lo decide
            # el ratón al soltarse (`_evento_mejoras`).
            self._arrastre_mejoras = [pos, self._scroll_mejoras, False]

    def _comprar_en(self, pos):
        """Compra la mejora que hay en `pos` (solo cuenta lo que se ve dentro de la zona)."""
        if not _MEJ_AREA.collidepoint(pos):
            return
        for id_ in self._rects_mejoras:
            if self._rect_pantalla(id_).collidepoint(pos):
                resultado = self.progresion.comprar(id_)
                if resultado == SIN_SALDO:
                    self._avisar_mejoras(t("mejoras.aviso_sin_saldo"))
                elif resultado == BLOQUEADA:
                    self._avisar_mejoras(t("mejoras.aviso_bloqueada"))
                break

    def _clic_en_barra(self, pos):
        """Si `pos` cae en la barra de desplazamiento, la agarra (o salta a ese punto)."""
        barra = self._rect_barra()
        if barra is None or not barra[0].inflate(14, 0).collidepoint(pos):
            return False
        if not barra[1].collidepoint(pos):
            self._arrastrar_barra_a(pos[1])
        self._arrastrando_barra = True
        return True

    def _icono_mejora(self, nombre, atenuado):
        """Icono de un nodo (cacheado); atenuado si la mejora aún está bloqueada."""
        clave = (nombre, atenuado)
        if clave not in self._iconos_mejoras:
            icono = self.rm.get_image_scaled(nombre, (_MEJ_ICONO, _MEJ_ICONO)).copy()
            if atenuado:
                icono.set_alpha(70)
            self._iconos_mejoras[clave] = icono
        return self._iconos_mejoras[clave]

    def _dibujar_nodo_mejora(self, mejora, rect):
        estado = self.progresion.estado(mejora.id)
        asequible = self.progresion.monedas >= mejora.coste
        if estado == COMPRADA:
            fondo, borde, color_pie, pie = (30, 100, 55), (120, 230, 150), (150, 255, 170), t("mejoras.comprada")
        elif estado == DISPONIBLE:
            fondo, borde = ((30, 70, 140), (130, 190, 255)) if asequible else ((45, 45, 65), (110, 110, 140))
            color_pie = (255, 215, 0) if asequible else (255, 130, 130)
            pie = t("mejoras.coste", n=mejora.coste)
        else:
            fondo, borde, color_pie, pie = (25, 25, 30), (70, 70, 80), (110, 110, 120), t("mejoras.bloqueada")
        bloqueada = estado == BLOQUEADA

        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(capa, (*fondo, 215), capa.get_rect(), border_radius=8)
        self.pantalla.blit(capa, rect)
        pygame.draw.rect(self.pantalla, borde, rect, 2, border_radius=8)

        if mejora.icono:
            self.pantalla.blit(self._icono_mejora(mejora.icono, bloqueada),
                               (rect.right - _MEJ_ICONO - 8, rect.y + 4))

        color_texto = (130, 130, 140) if bloqueada else (255, 255, 255)
        nombre = self.font_version.render(t(f"mejoras.{mejora.id}.nombre"), True, color_texto)
        self.pantalla.blit(nombre, (rect.x + 10, rect.y + 8))
        y = rect.y + 32
        for linea in _ajustar_texto(self.font_mini, t(f"mejoras.{mejora.id}.desc"), rect.width - 20)[:3]:
            texto = self.font_mini.render(linea, True, (170, 170, 180) if bloqueada else (215, 215, 225))
            self.pantalla.blit(texto, (rect.x + 10, y))
            y += 16
        surf_pie = self.font_version.render(pie, True, color_pie)
        self.pantalla.blit(surf_pie, (rect.x + 10, rect.bottom - 26))

    def _menu_mejoras(self):
        """Pantalla de mejoras permanentes: tres ramas de cuatro mejoras que se
        compran con las monedas ganadas jugando. Clic en un nodo = comprarlo."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.estado = "PRINCIPAL"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._clic_mejoras(event.pos)
            else:
                self._evento_mejoras(event)

        self.pantalla.blit(self.rm.get_image("imagen_fondo1"), (0, 0))
        self.pantalla.blit(self._overlay_oscuro(), (0, 0))

        titulo = self.font_titulo.render(t("mejoras.titulo"), True, (255, 255, 255))
        self.pantalla.blit(titulo, titulo.get_rect(center=(300, 65)))
        monedas = self.font_estandar.render(t("mejoras.monedas", n=self.progresion.monedas), True, (255, 215, 0))
        self.pantalla.blit(monedas, monedas.get_rect(center=(300, 122)))
        texto_pista = t("mejoras.pista", n=settings.MONEDAS_PUNTOS)
        if self._scroll_maximo() > 0:
            texto_pista += "  ·  " + t("mejoras.pista_desplazar")
        pista = self.font_mini.render(texto_pista, True, (160, 160, 170))
        self.pantalla.blit(pista, pista.get_rect(center=(300, 150)))

        for i, rama in enumerate(mejoras.RAMAS):
            cabecera = self.font_estandar.render(t(f"mejoras.rama_{rama}"), True, (255, 255, 255))
            self.pantalla.blit(cabecera, cabecera.get_rect(center=(_MEJ_COL_X[i] + _MEJ_ANCHO // 2, 190)))

        # Los nodos se dibujan recortados a su zona, para que al desplazarse no invadan
        # las cabeceras ni los botones.
        self.pantalla.set_clip(_MEJ_AREA)
        for rama in mejoras.RAMAS:
            cadena = mejoras.de_la_rama(rama)
            for orden, mejora in enumerate(cadena):
                rect = self._rect_pantalla(mejora.id)
                if rect.bottom < _MEJ_AREA.top or rect.top > _MEJ_AREA.bottom:
                    continue
                if orden:                                    # conector con el nodo anterior
                    hecha = self.progresion.estado(cadena[orden - 1].id) == COMPRADA
                    x = rect.centerx
                    pygame.draw.line(self.pantalla, (255, 215, 0) if hecha else (80, 80, 90),
                                     (x, rect.top - (_MEJ_PASO - _MEJ_ALTO)), (x, rect.top), 3)
                self._dibujar_nodo_mejora(mejora, rect)
        self.pantalla.set_clip(None)

        barra = self._rect_barra()
        if barra is not None:
            pista_barra, agarrador = barra
            pygame.draw.rect(self.pantalla, (50, 50, 60), pista_barra, border_radius=3)
            pygame.draw.rect(self.pantalla, (200, 200, 215) if self._arrastrando_barra else (140, 140, 160),
                             agarrador, border_radius=3)

        if self._aviso_mejoras is not None:
            texto, hasta = self._aviso_mejoras
            if pygame.time.get_ticks() < hasta:
                aviso = self.font_version.render(texto, True, (255, 220, 120))
                self.pantalla.blit(aviso, aviso.get_rect(center=(300, 675)))
            else:
                self._aviso_mejoras = None

        if paths.es_desarrollo():
            depuracion = self.font_mini.render(f"DEBUG  F2: +{MONEDAS_DEPURACION} monedas", True, (255, 90, 90))
            self.pantalla.blit(depuracion, (10, 10))

        self.btn_restablecer_mejoras.dibujar(self.pantalla, self.font_estandar)
        self.btn_volver_mejoras.dibujar(self.pantalla, self.font_estandar)
        pygame.display.flip()

    def _clasificacion_de(self, modo):
        return self.clasificacion_sin_fin if modo == settings.MODO_SIN_FIN else self.clasificacion

    def _dibujar_pestanas_puntuaciones(self, y):
        """Pestañas Campaña / Sin fin de la pantalla de Puntuaciones; guarda sus
        rects para que el clic sepa cuál se ha pulsado."""
        ancho, alto, hueco = 170, 38, 10
        x = (settings.ANCHO - (2 * ancho + hueco)) // 2
        for modo, clave in ((settings.MODO_CAMPANA, "puntuaciones.modo_campana"),
                            (settings.MODO_SIN_FIN, "puntuaciones.modo_sin_fin")):
            rect = pygame.Rect(x, y, ancho, alto)
            self._pestanas_puntuaciones[modo] = rect
            activa = modo == self._modo_puntuaciones
            fondo = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(fondo, (255, 255, 0, 150) if activa else (60, 60, 60, 170),
                             fondo.get_rect(), border_radius=8)
            self.pantalla.blit(fondo, rect)
            color = (255, 255, 255) if activa else (170, 170, 170)
            texto = self.font_version.render(t(clave), True, color)
            self.pantalla.blit(texto, texto.get_rect(center=rect.center))
            x += ancho + hueco

    def _menu_puntuaciones(self):
        """Pantalla de puntuaciones: pestañas Campaña / Sin fin; un clic fuera de
        ellas vuelve al menú."""
        fondo = self.rm.get_image("imagen_fondo1")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False
                self.resultado = "SALIR"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for modo, rect in self._pestanas_puntuaciones.items():
                    if rect.collidepoint(event.pos):
                        self._modo_puntuaciones = modo
                        break
                else:
                    self.estado = "PRINCIPAL"

        # Después de los eventos: una pestaña recién pulsada se dibuja ya con su ranking
        clasificacion = self._clasificacion_de(self._modo_puntuaciones)
        puntuaciones_top = clasificacion.obtener_puntuaciones_top() if clasificacion else []

        # Dibujado
        self.pantalla.blit(fondo, (0, 0))
        self.pantalla.blit(self._overlay_oscuro(), (0, 0))

        # Título
        txt_titulo = self.font_titulo.render(t("puntuaciones.titulo"), True, (255, 255, 255))
        self.pantalla.blit(txt_titulo, txt_titulo.get_rect(center=(300, 90)))
        self._dibujar_pestanas_puntuaciones(140)

        # Listado de puntos: cabecera + filas en columnas (nº, nombre, puntos, nivel/oleada).
        # `x` en "Puntos" es el borde derecho de la columna (texto alineado a la derecha).
        if puntuaciones_top:
            col_progreso = ("puntuaciones.col_oleada" if self._modo_puntuaciones == settings.MODO_SIN_FIN
                            else "puntuaciones.col_nivel")
            columnas = (("#", 60, "izq"), (t("puntuaciones.col_nombre"), 110, "izq"),
                        (t("puntuaciones.col_puntos"), 420, "der"), (t(col_progreso), 480, "izq"))
            y = 205
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
