"""Pantalla "Mejoras" del menú (src/ui/menu.py) y las monedas en las pantallas finales."""
import pygame
import pytest

from src.core import i18n, mejoras, settings
from src.core.engine import Juego
from src.ui.menu import MenuManager


@pytest.fixture
def menu(rm, audio, scoreboard, progresion):
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion)


def _clic_principal(menu, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    menu._menu_principal()


def _clic(menu, pos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    menu._menu_mejoras()


def _clic_nodo(menu, id_):
    """Un toque completo (pulsar y soltar) sobre un nodo: es al soltar cuando compra."""
    pos = menu._rect_pantalla(id_).center
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))
    menu._menu_mejoras()


# --- Acceso desde el menú principal ------------------------------------------

def test_el_boton_mejoras_abre_la_pantalla(menu):
    _clic_principal(menu, menu.btn_mejoras.rect.center)
    assert menu.estado == "MEJORAS"


def test_los_seis_botones_del_menu_caben_en_orden_y_sin_solaparse(menu):
    botones = [menu.btn_jugar, menu.btn_sin_fin, menu.btn_mejoras, menu.btn_opciones, menu.btn_puntos, menu.btn_salir]
    for arriba, abajo in zip(botones, botones[1:]):
        assert arriba.rect.bottom < abajo.rect.top
    assert botones[-1].rect.bottom < menu.btn_actualizar.rect.top            # el aviso sigue debajo


def test_el_bloque_de_seis_botones_sigue_centrado(menu):
    from src.ui import menu as modulo

    alto_titulo = menu.font_titulo.size("Galactic Guardian")[1]
    arriba = modulo._MENU_TITULO_Y - alto_titulo / 2
    abajo = menu.btn_salir.rect.bottom
    assert abs((arriba + abajo) / 2 - settings.ALTO / 2) <= 20


# --- Geometría ---------------------------------------------------------------

def test_los_nodos_no_se_solapan_y_caben_a_lo_ancho(menu):
    rects = list(menu._rects_mejoras.values())
    assert len(rects) == len(mejoras.MEJORAS)
    ancho = pygame.Rect(0, 0, settings.ANCHO, 10_000)
    assert all(ancho.contains(r) for r in rects)
    for i, a in enumerate(rects):
        assert not any(a.colliderect(b) for b in rects[i + 1:])


def test_la_zona_de_nodos_no_invade_las_cabeceras_ni_los_botones(menu):
    from src.ui import menu as modulo
    zona = modulo._MEJ_AREA
    assert zona.top >= 190 + 18                                  # bajo las cabeceras de las ramas
    for boton in (menu.btn_restablecer_mejoras.rect, menu.btn_volver_mejoras.rect):
        assert not zona.colliderect(boton) and pygame.Rect(0, 0, settings.ANCHO, settings.ALTO).contains(boton)
    assert zona.right <= settings.ANCHO


# --- Comprar y restablecer ---------------------------------------------------

def test_pulsar_un_nodo_lo_compra_y_descuenta(menu, progresion):
    progresion.ingresar(150)
    _clic_nodo(menu, "ataque_1")
    assert progresion.compradas == {"ataque_1"} and progresion.monedas == 150 - mejoras.POR_ID["ataque_1"].coste


def test_sin_saldo_avisa_y_no_compra(menu, progresion):
    progresion.ingresar(mejoras.POR_ID["ataque_1"].coste - 1)
    _clic_nodo(menu, "ataque_1")
    assert not progresion.compradas and progresion.monedas == mejoras.POR_ID["ataque_1"].coste - 1
    assert menu._aviso_mejoras[0] == "No tienes monedas suficientes"


def test_un_nodo_bloqueado_avisa_y_no_compra(menu, progresion):
    progresion.ingresar(10_000)
    _clic_nodo(menu, "ataque_3")
    assert not progresion.compradas and progresion.monedas == 10_000
    assert menu._aviso_mejoras[0] == "Compra antes la mejora anterior"


def test_pulsar_una_comprada_no_hace_nada(menu, progresion):
    progresion.ingresar(500)
    _clic_nodo(menu, "ataque_1")
    saldo = progresion.monedas
    _clic_nodo(menu, "ataque_1")
    assert progresion.monedas == saldo and menu._aviso_mejoras is None


def test_restablecer_devuelve_las_monedas_y_avisa(menu, progresion):
    progresion.ingresar(500)
    _clic_nodo(menu, "ataque_1")
    _clic_nodo(menu, "defensa_1")
    _clic(menu, menu.btn_restablecer_mejoras.rect.center)
    assert progresion.monedas == 500 and not progresion.compradas
    gastado = mejoras.POR_ID["ataque_1"].coste + mejoras.POR_ID["defensa_1"].coste
    assert menu._aviso_mejoras[0] == f"Compras deshechas: +{gastado} monedas"


def test_restablecer_sin_compras_avisa_que_no_hay_nada(menu):
    _clic(menu, menu.btn_restablecer_mejoras.rect.center)
    assert menu._aviso_mejoras[0] == "No hay nada que restablecer"


# --- Salir y avisos ----------------------------------------------------------

def test_volver_y_escape_vuelven_al_menu(menu):
    menu._abrir_mejoras()
    _clic(menu, menu.btn_volver_mejoras.rect.center)
    assert menu.estado == "PRINCIPAL"

    menu._abrir_mejoras()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    menu._menu_mejoras()
    assert menu.estado == "PRINCIPAL"


def test_cerrar_la_ventana_en_mejoras_sale_del_juego(menu):
    menu._abrir_mejoras()
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    menu._menu_mejoras()
    assert menu.ejecutando is False and menu.resultado == "SALIR"


def test_el_aviso_caduca(menu):
    menu._aviso_mejoras = ("hola", pygame.time.get_ticks() - 1)             # ya caducado
    menu._menu_mejoras()
    assert menu._aviso_mejoras is None


def test_el_aviso_se_muestra_mientras_no_caduca(menu):
    menu._avisar_mejoras("hola")
    menu._menu_mejoras()
    assert menu._aviso_mejoras is not None


def test_abrir_la_pantalla_borra_el_aviso_anterior(menu):
    menu._avisar_mejoras("viejo")
    menu._abrir_mejoras()
    assert menu._aviso_mejoras is None


# --- Dibujado e idioma -------------------------------------------------------

@pytest.mark.parametrize("codigo", i18n.IDIOMAS)
def test_la_pantalla_se_dibuja_en_todos_los_estados_e_idiomas(menu, progresion, codigo):
    i18n.establecer_idioma(codigo)
    menu._crear_botones()
    progresion.ingresar(700)
    menu._abrir_mejoras()
    menu._menu_mejoras()                                      # casi todo bloqueado
    for id_ in ("ataque_1", "ataque_2", "defensa_1"):
        _clic_nodo(menu, id_)                                 # comprados, disponibles y sin saldo mezclados
    menu._menu_mejoras()


def test_los_botones_de_mejoras_siguen_el_idioma(menu):
    assert menu.btn_restablecer_mejoras.texto == "Restablecer" and menu.btn_mejoras.texto == "Mejoras"
    i18n.establecer_idioma("en")
    menu._crear_botones()
    assert menu.btn_restablecer_mejoras.texto == "Reset" and menu.btn_mejoras.texto == "Upgrades"


def test_sin_progresion_el_menu_usa_una_en_memoria(rm, audio, scoreboard):
    """La pausa crea un `MenuManager` sin progresión: no debe fallar ni tocar el disco."""
    sin = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard)
    assert sin.progresion.persistir is False
    sin._abrir_mejoras()
    sin._menu_mejoras()


def test_menu_y_partida_comparten_la_misma_cuenta(menu, audio, scoreboard, rm, progresion):
    juego = Juego(pygame.display.get_surface(), audio, scoreboard, rm, progresion=progresion)
    juego.puntuacion = 7 * settings.MONEDAS_PUNTOS
    juego.volver_al_menu()
    assert menu.progresion.monedas == 7


# --- Monedas en las pantallas finales ---------------------------------------

def test_game_over_y_victoria_incluyen_las_monedas(juego, monkeypatch):
    lineas = []
    monkeypatch.setattr(juego.render_manager, "_dibujar_estadisticas",
                        lambda l, y, color=(255, 255, 255): lineas.append(list(l)))
    juego.puntuacion = 9 * settings.MONEDAS_PUNTOS
    juego._cobrar_monedas()
    juego.estado_game_over = True
    juego.dibujar()
    assert any("Monedas: +9 (total 9)" in l for l in lineas)

    lineas.clear()
    juego.estado_game_over = False
    juego.estado_victoria_final = True
    juego.dibujar()
    assert any("Monedas: +9 (total 9)" in l for l in lineas)


def test_sin_progresion_las_pantallas_finales_no_hablan_de_monedas(rm, audio, scoreboard, monkeypatch):
    j = Juego(pygame.display.get_surface(), audio, scoreboard, rm)
    lineas = []
    monkeypatch.setattr(j.render_manager, "_dibujar_estadisticas",
                        lambda l, y, color=(255, 255, 255): lineas.append(list(l)))
    j.estado_game_over = True
    j.dibujar()
    assert lineas and not any("Monedas" in x for l in lineas for x in l)


# --- Iconos en los nodos ---------------------------------------------------------

def test_los_iconos_de_las_mejoras_son_imagenes_cargadas():
    from src.core import config, mejoras

    con_icono = [m for m in mejoras.MEJORAS if m.icono]
    assert con_icono                                            # alguna lleva
    assert all(m.icono in config.RECURSOS for m in con_icono)


def test_el_icono_se_dibuja_en_la_esquina_superior_derecha_solo_si_la_mejora_lo_tiene(menu, monkeypatch):
    from src.ui import menu as modulo

    llamadas = []
    magenta = pygame.Surface((modulo._MEJ_ICONO, modulo._MEJ_ICONO))
    magenta.fill((255, 0, 255))
    monkeypatch.setattr(menu, "_icono_mejora", lambda nombre, atenuado: llamadas.append(nombre) or magenta)
    menu._abrir_mejoras()
    menu._menu_mejoras()

    visibles = [m for m in mejoras.MEJORAS
                if m.icono and menu._rect_pantalla(m.id).colliderect(modulo._MEJ_AREA)]     # los demás están fuera de la zona
    assert visibles and len(llamadas) == len(visibles)          # ni uno más ni uno menos
    rect = menu._rect_pantalla("ataque_1")
    centro = (rect.right - 8 - modulo._MEJ_ICONO // 2, rect.y + 4 + modulo._MEJ_ICONO // 2)
    assert menu.pantalla.get_at(centro)[:3] == (255, 0, 255)


def test_el_icono_atenuado_de_una_mejora_bloqueada_se_cachea_aparte(menu):
    normal = menu._icono_mejora("curacion", False)
    atenuado = menu._icono_mejora("curacion", True)
    assert normal is menu._icono_mejora("curacion", False)      # caché
    assert normal is not atenuado and atenuado.get_alpha() < 255
    assert normal.get_size() == (28, 28)


# --- Zona desplazable ----------------------------------------------------------------

@pytest.fixture
def menu_largo(monkeypatch, rm, audio, scoreboard, progresion):
    """Un `MenuManager` con un árbol de 8 filas en la rama de ataque (no cabe en la zona)."""
    extra = tuple(mejoras.Mejora(f"ataque_{i}", "ataque", 100 * i, {"danio_extra": 10}, requiere=f"ataque_{i - 1}")
                  for i in range(5, 9))
    nuevas = mejoras.MEJORAS + extra
    monkeypatch.setattr(mejoras, "MEJORAS", nuevas)
    monkeypatch.setattr(mejoras, "POR_ID", {m.id: m for m in nuevas})
    return MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion)


def _evento(menu, tipo, **datos):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(tipo, **datos))
    menu._menu_mejoras()


def test_un_arbol_que_cabe_no_se_desplaza_ni_dibuja_barra(monkeypatch, rm, audio, scoreboard, progresion):
    corto = tuple(m for m in mejoras.MEJORAS if int(m.id.split("_")[1]) <= 3)
    monkeypatch.setattr(mejoras, "MEJORAS", corto)
    monkeypatch.setattr(mejoras, "POR_ID", {m.id: m for m in corto})
    menu = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion)
    assert menu._scroll_maximo() == 0 and menu._rect_barra() is None
    menu._desplazar_mejoras(500)
    assert menu._scroll_mejoras == 0


def test_un_arbol_largo_se_puede_desplazar_y_tiene_barra(menu_largo):
    assert menu_largo._scroll_maximo() > 0
    pista, agarrador = menu_largo._rect_barra()
    assert pista.contains(agarrador) and agarrador.top == pista.top            # arranca arriba del todo


def test_el_scroll_tiene_tope_arriba_y_abajo(menu_largo):
    menu_largo._desplazar_mejoras(-999)
    assert menu_largo._scroll_mejoras == 0
    menu_largo._desplazar_mejoras(999_999)
    assert menu_largo._scroll_mejoras == menu_largo._scroll_maximo()
    assert menu_largo._rect_barra()[1].bottom == menu_largo._rect_barra()[0].bottom      # agarrador abajo del todo


def test_la_rueda_del_raton_desplaza_y_no_pasa_de_los_topes(menu_largo):
    from src.ui import menu as modulo
    menu_largo._abrir_mejoras()
    _evento(menu_largo, pygame.MOUSEWHEEL, x=0, y=-1)                   # rueda hacia abajo
    assert menu_largo._scroll_mejoras == modulo._MEJ_PASO_RUEDA
    _evento(menu_largo, pygame.MOUSEWHEEL, x=0, y=1)
    assert menu_largo._scroll_mejoras == 0
    _evento(menu_largo, pygame.MOUSEWHEEL, x=0, y=1)
    assert menu_largo._scroll_mejoras == 0
    _evento(menu_largo, pygame.MOUSEWHEEL, x=0, y=-500)
    assert menu_largo._scroll_mejoras == menu_largo._scroll_maximo()


def test_las_teclas_desplazan(menu_largo):
    for tecla, comprobar in (
        (pygame.K_DOWN, lambda m: m._scroll_mejoras > 0),
        (pygame.K_UP, lambda m: m._scroll_mejoras == 0),
        (pygame.K_PAGEDOWN, lambda m: m._scroll_mejoras > 0),
        (pygame.K_HOME, lambda m: m._scroll_mejoras == 0),
        (pygame.K_END, lambda m: m._scroll_mejoras == m._scroll_maximo()),
        (pygame.K_PAGEUP, lambda m: m._scroll_mejoras < m._scroll_maximo()),
    ):
        _evento(menu_largo, pygame.KEYDOWN, key=tecla)
        assert comprobar(menu_largo), pygame.key.name(tecla)


def test_arrastrar_el_agarrador_de_la_barra_desplaza_el_contenido(menu_largo):
    pista, agarrador = menu_largo._rect_barra()
    _clic(menu_largo, agarrador.center)                                 # lo agarra
    assert menu_largo._arrastrando_barra
    _evento(menu_largo, pygame.MOUSEMOTION, pos=(agarrador.centerx, pista.bottom), rel=(0, 0), buttons=(1, 0, 0))
    assert menu_largo._scroll_mejoras == menu_largo._scroll_maximo()    # arrastrado hasta el fondo
    _evento(menu_largo, pygame.MOUSEBUTTONUP, button=1, pos=(agarrador.centerx, pista.bottom))
    assert not menu_largo._arrastrando_barra
    _evento(menu_largo, pygame.MOUSEMOTION, pos=(agarrador.centerx, pista.top), rel=(0, 0), buttons=(0, 0, 0))
    assert menu_largo._scroll_mejoras == menu_largo._scroll_maximo()    # ya no lo sigue


def test_pulsar_en_la_pista_de_la_barra_salta_a_ese_punto(menu_largo):
    pista, _ = menu_largo._rect_barra()
    _clic(menu_largo, (pista.centerx, pista.bottom - 2))
    assert menu_largo._scroll_mejoras > menu_largo._scroll_maximo() * 0.8


def test_un_clic_en_la_barra_no_compra_nada(menu_largo, progresion):
    progresion.ingresar(10_000)
    pista, _ = menu_largo._rect_barra()
    _clic(menu_largo, pista.center)
    assert not progresion.compradas


def test_un_nodo_desplazado_fuera_de_la_zona_no_se_puede_pulsar(menu_largo, progresion):
    progresion.ingresar(10_000)
    menu_largo._desplazar_mejoras(999_999)
    fuera = menu_largo._rect_pantalla("ataque_1")                       # ya subió por encima de la zona
    assert fuera.bottom < 210 or fuera.top < 210
    _clic(menu_largo, (fuera.centerx, 100))                             # sobre el título, no en la zona
    assert not progresion.compradas


def test_un_nodo_que_se_ve_tras_desplazar_se_compra_en_su_nueva_posicion(menu_largo, progresion):
    progresion.ingresar(10_000)
    for id_ in ("ataque_1", "ataque_2", "ataque_3", "ataque_4"):
        assert progresion.comprar(id_) == "ok"
    menu_largo._desplazar_mejoras(999_999)
    _clic_nodo(menu_largo, "ataque_5")                                   # 5.º de la rama: solo visible desplazado
    assert "ataque_5" in progresion.compradas


def test_abrir_la_pantalla_vuelve_arriba_y_suelta_la_barra(menu_largo):
    menu_largo._desplazar_mejoras(999_999)
    menu_largo._arrastrando_barra = True
    menu_largo._abrir_mejoras()
    assert menu_largo._scroll_mejoras == 0 and not menu_largo._arrastrando_barra


def test_los_nodos_desplazados_no_invaden_las_cabeceras(menu_largo):
    from src.ui import menu as modulo
    menu_largo._abrir_mejoras()
    menu_largo._menu_mejoras()
    y = modulo._MEJ_AREA.top - 4                                        # entre las cabeceras y la zona
    antes = [tuple(menu_largo.pantalla.get_at((x, y))) for x in range(20, 580, 7)]
    menu_largo._desplazar_mejoras(300)
    menu_largo._menu_mejoras()
    despues = [tuple(menu_largo.pantalla.get_at((x, y))) for x in range(20, 580, 7)]
    assert antes == despues


class _Espia:
    """Envuelve una fuente y apunta los textos que se dibujan con ella."""
    def __init__(self, real, frases):
        self.real, self.frases = real, frases

    def render(self, texto, *args):
        self.frases.append(texto)
        return self.real.render(texto, *args)

    def size(self, texto):
        return self.real.size(texto)


def _textos_dibujados(menu, monkeypatch):
    frases = []
    monkeypatch.setattr(menu, "font_mini", _Espia(menu.font_mini, frases))
    menu._menu_mejoras()
    return frases


def test_la_pista_avisa_de_que_se_puede_desplazar_solo_si_hace_falta(menu_largo, monkeypatch, rm, audio, scoreboard,
                                                                    progresion):
    assert any("rueda" in f for f in _textos_dibujados(menu_largo, monkeypatch))
    corto = MenuManager(pygame.display.get_surface(), rm, audio, scoreboard, None, progresion)
    monkeypatch.setattr(mejoras, "MEJORAS", mejoras.MEJORAS[:3])
    monkeypatch.setattr(mejoras, "POR_ID", {m.id: m for m in mejoras.MEJORAS})
    assert not any("rueda" in f for f in _textos_dibujados(corto, monkeypatch))


def test_la_pista_de_monedas_usa_el_ritmo_real_del_juego(menu_largo, monkeypatch):
    assert any(f"por cada {settings.MONEDAS_PUNTOS} puntos" in f for f in _textos_dibujados(menu_largo, monkeypatch))


@pytest.mark.parametrize("idioma", i18n.IDIOMAS)
def test_ninguna_descripcion_pasa_de_tres_lineas(menu, idioma):
    """Con más de tres líneas el texto pisaría el pie de la tarjeta (coste / estado)."""
    from src.ui import menu as modulo
    antes = i18n.idioma_actual()
    i18n.establecer_idioma(idioma)
    try:
        for m in mejoras.MEJORAS:
            lineas = modulo._ajustar_texto(menu.font_mini, i18n.t(f"mejoras.{m.id}.desc"), modulo._MEJ_ANCHO - 20)
            assert len(lineas) <= 3, (idioma, m.id, lineas)
    finally:
        i18n.establecer_idioma(antes)


# --- Arrastrar con el ratón (como en el móvil) -----------------------------------

def _gesto(menu, inicio, *puntos, botones=(1, 0, 0), soltar=True):
    """Pulsa en `inicio`, mueve el ratón por `puntos` y suelta en el último."""
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=inicio))
    for p in puntos:
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=p, rel=(0, 0), buttons=botones))
    if soltar:
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=puntos[-1] if puntos else inicio))
    menu._menu_mejoras()


def test_arrastrar_hacia_arriba_desplaza_el_contenido_hacia_abajo(menu_largo):
    y = 400
    _gesto(menu_largo, (300, y), (300, y - 40), (300, y - 100))
    assert menu_largo._scroll_mejoras == 100                            # el contenido sigue al puntero


def test_arrastrar_hacia_abajo_vuelve_hacia_arriba_y_respeta_los_topes(menu_largo):
    menu_largo._desplazar_mejoras(150)
    _gesto(menu_largo, (300, 300), (300, 340))
    assert menu_largo._scroll_mejoras == 110
    _gesto(menu_largo, (300, 300), (300, 900))                          # más allá del principio
    assert menu_largo._scroll_mejoras == 0
    _gesto(menu_largo, (300, 600), (300, -3000))                        # más allá del final
    assert menu_largo._scroll_mejoras == menu_largo._scroll_maximo()


def test_un_arrastre_no_compra_al_soltar(menu_largo, progresion):
    progresion.ingresar(10_000)
    centro = menu_largo._rect_pantalla("ataque_1").center
    _gesto(menu_largo, centro, (centro[0], centro[1] + 60))
    assert not progresion.compradas


def test_un_toque_con_un_pequeno_temblor_sigue_comprando(menu_largo, progresion):
    progresion.ingresar(10_000)
    centro = menu_largo._rect_pantalla("ataque_1").center
    _gesto(menu_largo, centro, (centro[0], centro[1] + 3))              # menos que el umbral
    assert "ataque_1" in progresion.compradas and menu_largo._scroll_mejoras == 0


def test_pulsar_sin_soltar_todavia_no_compra(menu_largo, progresion):
    progresion.ingresar(10_000)
    centro = menu_largo._rect_pantalla("ataque_1").center
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=centro))
    menu_largo._menu_mejoras()
    assert not progresion.compradas


def test_al_arrastrar_se_puede_seguir_hasta_un_nodo_lejano_y_comprarlo(menu_largo, progresion):
    progresion.ingresar(10_000)
    for id_ in ("ataque_1", "ataque_2", "ataque_3", "ataque_4"):
        progresion.comprar(id_)
    _gesto(menu_largo, (300, 600), (300, -3000))                        # hasta el fondo
    _clic_nodo(menu_largo, "ataque_5")
    assert "ataque_5" in progresion.compradas


def test_soltar_fuera_de_la_ventana_no_deja_el_arrastre_colgado(menu_largo):
    _gesto(menu_largo, (300, 400), (300, 380), soltar=False)            # pulsa y arrastra, sin soltar
    assert menu_largo._arrastre_mejoras is not None
    _gesto_sin_boton = pygame.event.Event(pygame.MOUSEMOTION, pos=(300, 300), rel=(0, 0), buttons=(0, 0, 0))
    pygame.event.clear()
    pygame.event.post(_gesto_sin_boton)
    menu_largo._menu_mejoras()
    assert menu_largo._arrastre_mejoras is None


def test_pulsar_en_un_boton_o_en_la_barra_no_inicia_un_arrastre_del_contenido(menu_largo):
    _clic(menu_largo, menu_largo.btn_restablecer_mejoras.rect.center)
    assert menu_largo._arrastre_mejoras is None
    pista, agarrador = menu_largo._rect_barra()
    _clic(menu_largo, agarrador.center)
    assert menu_largo._arrastre_mejoras is None and menu_largo._arrastrando_barra


def test_abrir_la_pantalla_cancela_un_arrastre_a_medias(menu_largo):
    menu_largo._arrastre_mejoras = [(0, 0), 0, True]
    menu_largo._abrir_mejoras()
    assert menu_largo._arrastre_mejoras is None


# --- Monedas de depuración (F2) --------------------------------------------------

def _tecla(menu, tecla):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla))
    menu._menu_mejoras()


def test_f2_da_monedas_al_ejecutar_desde_el_codigo(menu, progresion):
    from src.ui.menu import MONEDAS_DEPURACION
    antes = progresion.monedas
    _tecla(menu, pygame.K_F2)
    _tecla(menu, pygame.K_F2)
    assert progresion.monedas == antes + 2 * MONEDAS_DEPURACION


def test_f2_no_hace_nada_en_el_juego_empaquetado(menu, progresion, monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.delenv("GG_DEPURACION", raising=False)
    antes = progresion.monedas
    _tecla(menu, pygame.K_F2)
    assert progresion.monedas == antes


def test_la_variable_gg_depuracion_lo_activa_tambien_en_el_empaquetado(menu, progresion, monkeypatch):
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setenv("GG_DEPURACION", "1")
    _tecla(menu, pygame.K_F2)
    assert progresion.monedas > 0


def test_el_aviso_de_depuracion_solo_se_dibuja_en_desarrollo(menu, monkeypatch):
    frases = _textos_dibujados(menu, monkeypatch)
    assert any("DEBUG" in f for f in frases)
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.delenv("GG_DEPURACION", raising=False)
    assert not any("DEBUG" in f for f in _textos_dibujados(menu, monkeypatch))
