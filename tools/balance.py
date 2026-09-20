"""Herramienta de balance de la campaña (script de desarrollo, no parte del juego).

    python tools/balance.py                 # informe del juego tal como está
    python tools/balance.py --perfil todos  # con los tres perfiles de jugador
    python tools/balance.py --niveles       # detalle por fase de cada nivel

Es un **modelo analítico**: no simula la partida, la estima con fórmulas sencillas a
partir de los datos reales del juego (`niveles.py`, las clases de enemigos, `mejoras.py`,
`Jugador.CONFIG`, `settings`). Por eso no sabe esquivar como tú: unos pocos supuestos
(los "perfiles") dicen cuánto acierta, cuánto se esquiva y qué combo se mantiene un
jugador torpe, medio o hábil. Sirve como brújula para fijar la curva de dificultad y
la economía; los números definitivos se afinan jugando.

Qué calcula, para una nave (una combinación de mejoras) y un nivel:

- **Afluencia**: vida de enemigos que entra por segundo ÷ el DPS que aciertas. Si pasa
  de 1, los enemigos entran más rápido de lo que los matas y se acumulan.
- **TTK del jefe**: segundos que se tarda en matarlo.
- **Daño esperado** (en puntos de salud) por las balas y los choques de las fases y por
  el jefe, y las **muertes esperadas** = daño ÷ salud máxima.
- **Puntos y monedas** del nivel, con el combo medio del perfil.

Con eso simula una **partida esperada** (se juega nivel a nivel hasta gastar las vidas) y
una **progresión** (partida tras partida, gastando las monedas en el árbol) para estimar
cuántas partidas lleva completar la campaña.
"""
import argparse
import math
import os
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Callable

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src.core import mejoras, niveles, settings  # noqa: E402
from src.entities.enemies import EnemigoTipo2, EnemigoTipo3  # noqa: E402
from src.entities.player import Jugador  # noqa: E402

ALTO_PANTALLA = settings.ALTO
BALAS_POR_TIPO = {"simple": 1, "doble": 2, "triple": 3}
NIVELES_CAMPANA = settings.NIVEL_MAX
MAX_PARTIDAS = 400          # tope de la simulación de progresión


# ----------------------------------------------------------------------------- perfiles
@dataclass(frozen=True)
class Perfil:
    """Cómo juega alguien: supuestos, no datos medidos (ajustables)."""
    nombre: str
    precision: float        # fracción de tu DPS que acierta a enemigos normales
    precision_jefe: float   # ídem con el jefe (es grande: se acierta más)
    impacto_bala: float     # fracción del daño teórico de las balas enemigas que te alcanza
    impacto_contacto: float # fracción de los enemigos que se te escapan y llegan a chocar contigo
    impacto_jefe: float     # ídem con las balas del jefe (apuntadas y lentas: se esquivan más)
    combo_medio: float      # multiplicador de puntuación medio que mantienes
    sin_golpe: float        # fracción del tiempo que pasas sin recibir daño (cuando regenera la salud)


PERFILES = {
    "torpe": Perfil("torpe", 0.45, 0.70, 0.22, 0.15, 0.13, 1.5, 0.35),
    "medio": Perfil("medio", 0.55, 0.80, 0.15, 0.10, 0.08, 2.0, 0.50),
    "habil": Perfil("hábil", 0.65, 0.85, 0.10, 0.07, 0.05, 2.7, 0.65),
}


# ----------------------------------------------------------------------------- nave
@dataclass(frozen=True)
class Nave:
    salud: int
    vidas: int
    danio: int
    balas: int
    disparos_s: float
    velocidad: float
    invulnerable_ms: int
    monedas_pct: float
    regen_s: float = 0.0            # salud que se recupera por segundo sin recibir daño

    @property
    def dps(self):
        return self.danio * self.balas * self.disparos_s


def nave_de(ids):
    """La nave que sale de comprar las mejoras `ids` (igual que `Jugador.reiniciar`)."""
    c, b = Jugador.CONFIG, mejoras.calcular_bonus(ids)
    cadencia = max(c["cadencia_max"], c["cadencia_base"] - b.cadencia_menos_ms)
    return Nave(
        salud=c["salud_max"] + b.salud_extra,
        vidas=c["vidas_init"] + b.vidas_extra,
        danio=min(c["danio_max"], c["danio_base"] + b.danio_extra),
        balas=BALAS_POR_TIPO[b.disparo_inicial],
        disparos_s=1000 / cadencia,
        velocidad=min(c["vel_max"], c["vel_base"] + b.velocidad_extra),
        invulnerable_ms=settings.JUGADOR_INVULNERABLE_MS + b.invulnerable_extra_ms,
        monedas_pct=b.monedas_pct,
    )


# ----------------------------------------------------------------------------- modelo
def vida_enemigo(clase, nivel):
    """Vida de un enemigo (o del jefe) en un nivel: la misma fórmula que `EnemigoBase`."""
    paso = settings.SALUD_PASO_NIVEL
    return max(paso, round(clase.SALUD_BASE / paso * (1 + clase.FACTOR_NIVEL * (nivel - 1))) * paso)


@dataclass(frozen=True)
class Modelo:
    """Todo lo que depende del diseño y no de la nave. El juego actual es `MODELO_ACTUAL`;
    una propuesta de reequilibrio es una copia con alguna pieza cambiada (`replace`)."""
    nombre: str = "actual"
    definicion: Callable = niveles.definicion_nivel        # nivel -> DefinicionNivel
    vida: Callable = vida_enemigo                          # (clase, nivel) -> vida
    danio_x: Callable = lambda nivel: 1.0                  # multiplicador del daño enemigo por nivel
    arbol: tuple = field(default_factory=lambda: mejoras.MEJORAS)
    nave: Callable = nave_de                               # ids de mejoras -> Nave
    monedas_puntos: int = settings.MONEDAS_PUNTOS          # puntos que valen una moneda


MODELO_ACTUAL = Modelo()

# Daño de las balas de cada tipo (lo que hace UNA bala enemiga)
def _danio_bala(clase):
    return {EnemigoTipo2: settings.DANIO_BALA_TIPO2, EnemigoTipo3: settings.DANIO_BALA_TIPO3}.get(clase, 0)


# ----------------------------------------------------------------------------- un nivel
@dataclass
class Fase:
    desde_s: float
    duracion_s: float
    afluencia: float
    danio: float
    bajas: float
    puntos: float


@dataclass
class ResultadoNivel:
    nivel: int
    fases: list
    ttk_jefe: float
    vida_jefe: int
    danio_jefe: float
    duracion_s: float
    puntos: float
    curacion: float = 0.0           # salud recuperada por regeneración durante el nivel

    @property
    def afluencia_max(self):
        return max(f.afluencia for f in self.fases)

    @property
    def danio_fases(self):
        return sum(f.danio for f in self.fases)

    @property
    def danio(self):
        """Daño recibido, ya descontada la regeneración (nunca negativo)."""
        return max(0.0, self.danio_fases + self.danio_jefe - self.curacion)

    def muertes(self, nave):
        """Veces que se pierde toda la salud, en esperanza: daño ÷ salud máxima."""
        return self.danio / nave.salud


def analizar_nivel(nave, nivel, perfil, modelo=MODELO_ACTUAL):
    d = modelo.definicion(nivel)
    dx = modelo.danio_x(nivel)
    lam = 1000 / ((d.intervalo_spawn[0] + d.intervalo_spawn[1]) / 2)      # enemigos por segundo
    dps_ef = nave.dps * perfil.precision
    fases = []
    for i, fase in enumerate(d.fases):
        fin = d.fases[i + 1].desde_ms if i + 1 < len(d.fases) else d.tiempo_jefe_ms
        dur = (fin - fase.desde_ms) / 1000
        reparto = Counter(fase.enemigos)
        total = sum(reparto.values())
        vida_media = sum(n / total * modelo.vida(c, nivel) for c, n in reparto.items())
        afluencia = lam * vida_media / dps_ef

        danio_s = bajas_s = puntos_s = 0.0
        for clase, n in reparto.items():
            cuota = n / total
            vida = modelo.vida(clase, nivel)
            vel_y = (clase.VEL_Y[0] + clase.VEL_Y[1]) / 2 * settings.FPS       # px/s
            t_pantalla = ALTO_PANTALLA / vel_y
            t_matar = vida / dps_ef * max(1.0, afluencia)                      # con cola si hay afluencia
            muertos = min(1.0, t_pantalla / t_matar)                           # mueren antes de salir
            if clase.CADENCIA:
                disparos = 1 + math.floor(min(t_pantalla, t_matar) / (clase.CADENCIA / 1000))
                danio_s += lam * cuota * disparos * _danio_bala(clase) * dx * perfil.impacto_bala
            danio_s += lam * cuota * (1 - muertos) * perfil.impacto_contacto * settings.DANIO_CONTACTO * dx
            bajas_s += lam * cuota * muertos
            puntos_s += lam * cuota * muertos * clase.VALOR * nivel
        fases.append(Fase(fase.desde_ms / 1000, dur, afluencia, danio_s * dur, bajas_s * dur, puntos_s * dur))

    vida_jefe = modelo.vida(d.jefe, nivel)
    ttk = vida_jefe / (nave.dps * perfil.precision_jefe)
    entrante = (1000 / d.jefe.CADENCIA_NORMAL) * settings.DANIO_JEFE_NORMAL \
        + (1000 / d.jefe.CADENCIA_RAPIDA) * settings.DANIO_JEFE_RAPIDA           # HP/s si todo impactara
    danio_jefe = ttk * entrante * modelo.danio_x(nivel) * perfil.impacto_jefe
    puntos = (sum(f.puntos for f in fases) + d.jefe.VALOR * nivel) * perfil.combo_medio
    duracion = (d.tiempo_jefe_ms + d.espera_jefe_ms) / 1000 + ttk
    curacion = nave.regen_s * perfil.sin_golpe * duracion
    return ResultadoNivel(nivel, fases, ttk, vida_jefe, danio_jefe, duracion, puntos, curacion)


# ----------------------------------------------------------------------------- una partida
@dataclass
class Partida:
    niveles: list
    nivel_alcanzado: float          # 5.0 = llegó al final; 2.4 = murió el 40 % del nivel 3
    victoria: bool
    puntos: float
    monedas: int
    minutos: float


def jugar(nave, perfil, modelo=MODELO_ACTUAL, niveles_campana=NIVELES_CAMPANA):
    """Partida esperada: se juega nivel a nivel hasta que las muertes esperadas gastan las vidas."""
    muertes = puntos = segundos = 0.0
    hechos = []
    for n in range(1, niveles_campana + 1):
        r = analizar_nivel(nave, n, perfil, modelo)
        hechos.append(r)
        if muertes + r.muertes(nave) >= nave.vidas:
            fraccion = (nave.vidas - muertes) / r.muertes(nave)
            puntos += r.puntos * fraccion
            segundos += r.duracion_s * fraccion
            return Partida(hechos, n - 1 + fraccion, False, puntos, _monedas(puntos, nave, modelo), segundos / 60)
        muertes += r.muertes(nave)
        puntos += r.puntos
        segundos += r.duracion_s
    return Partida(hechos, float(niveles_campana), True, puntos, _monedas(puntos, nave, modelo), segundos / 60)


def _monedas(puntos, nave, modelo=MODELO_ACTUAL):
    return int(puntos // modelo.monedas_puntos * (1 + nave.monedas_pct))


# ----------------------------------------------------------------------------- el árbol
def orden_de_compra(arbol):
    """Orden en que se compra el árbol: siempre lo más barato que esté disponible."""
    compradas, orden = set(), []
    pendientes = list(arbol)
    while pendientes:
        disponibles = [m for m in pendientes if m.requiere is None or m.requiere in compradas]
        m = min(disponibles, key=lambda x: (x.coste, x.id))
        compradas.add(m.id)
        orden.append(m)
        pendientes.remove(m)
    return orden


def build_al(orden, fraccion):
    """Las mejoras que se han comprado al gastar `fraccion` (0..1) del coste total, en ese orden."""
    presupuesto = fraccion * sum(m.coste for m in orden)
    gastado, ids = 0, []
    for m in orden:
        if gastado + m.coste > presupuesto + 1e-9:
            break
        gastado += m.coste
        ids.append(m.id)
    return ids, gastado


@dataclass
class Progreso:
    partidas_hasta_victoria: int            # 0 = no llega en MAX_PARTIDAS
    curva: list                             # (nº de partida, % del árbol, nivel alcanzado)
    compras: list = field(default_factory=list)     # (nº de partida, id de la mejora comprada tras ella)


def progresion(perfil, modelo=MODELO_ACTUAL):
    """Partida tras partida: se juega, se cobran las monedas y se compra lo siguiente del árbol."""
    orden = orden_de_compra(modelo.arbol)
    total = sum(m.coste for m in orden)
    monedas, comprado, gastado, curva, compras = 0, [], 0, [], []
    for n in range(1, MAX_PARTIDAS + 1):
        nave = modelo.nave(comprado)
        p = jugar(nave, perfil, modelo)
        curva.append((n, gastado / total, p.nivel_alcanzado))
        if p.victoria:
            return Progreso(n, curva, compras)
        monedas += p.monedas
        while len(comprado) < len(orden) and monedas >= orden[len(comprado)].coste:
            m = orden[len(comprado)]
            monedas -= m.coste
            gastado += m.coste
            comprado.append(m.id)
            compras.append((n, m.id))
    return Progreso(0, curva, compras)


# ----------------------------------------------------------------------------- informe
def _cabecera(texto):
    print(f"\n{texto}\n{'-' * len(texto)}")


def _resumen_mejora(m):
    return ", ".join(f"{k} {v:+g}" if isinstance(v, (int, float)) else f"{k}={v}" for k, v in m.efecto.items())


def informe_supuestos(perfiles):
    _cabecera("SUPUESTOS DE CADA PERFIL (no son datos medidos: ajústalos en tools/balance.py)")
    print(f"{'perfil':<8}{'aciertas':>10}{'al jefe':>9}{'balas que':>11}{'choques que':>13}{'balas jefe':>12}{'combo':>7}")
    print(f"{'':<8}{'(DPS)':>10}{'':>9}{'te dan':>11}{'te dan':>13}{'que te dan':>12}{'medio':>7}")
    for p in perfiles:
        print(f"{p.nombre:<8}{p.precision:>10.0%}{p.precision_jefe:>9.0%}{p.impacto_bala:>11.0%}"
              f"{p.impacto_contacto:>13.0%}{p.impacto_jefe:>12.0%}{p.combo_medio:>7.1f}")


def informe_arbol(modelo):
    orden = orden_de_compra(modelo.arbol)
    base = modelo.nave([])
    _cabecera(f"NAVE BASE Y ÁRBOL ({modelo.nombre})")
    print(f"Base: {base.salud} de salud, {base.vidas} vidas, bala de {base.danio} x {base.balas}, "
          f"{base.disparos_s:.1f} disparos/s (DPS {base.dps:.0f}), velocidad {base.velocidad:g}")
    print(f"Coste total del árbol: {sum(m.coste for m in orden)} monedas. Orden de compra (lo más barato disponible):")
    for i, m in enumerate(orden, 1):
        print(f"  {i:>2}. {m.id:<11} {m.coste:>5}   {_resumen_mejora(m)}")


def informe_builds(perfil, fracciones, modelo, detalle):
    orden = orden_de_compra(modelo.arbol)
    for fr in fracciones:
        ids, gastado = build_al(orden, fr)
        nave = modelo.nave(ids)
        _cabecera(f"BUILD {fr:.0%} DEL ÁRBOL ({gastado} monedas, {len(ids)} mejoras) — perfil {perfil.nombre}")
        print(f"Nave: {nave.salud} salud x {nave.vidas} vidas | daño {nave.danio} x {nave.balas} bala(s) | "
              f"{nave.disparos_s:.1f} disp/s | DPS {nave.dps:.0f} (efectivo {nave.dps * perfil.precision:.0f})")
        print(f"{'nivel':>5}{'afluencia':>11}{'TTK jefe':>10}{'daño':>8}{'muertes':>9}{'puntos':>9}   veredicto")
        p = jugar(nave, perfil, modelo)
        for r in p.niveles:
            print(f"{r.nivel:>5}{r.afluencia_max:>11.2f}{r.ttk_jefe:>9.0f}s{r.danio:>8.0f}{r.muertes(nave):>9.2f}"
                  f"{r.puntos:>9.0f}   {_veredicto(r, nave)}")
            if detalle:
                for f in r.fases:
                    print(f"       fase desde {f.desde_s:>4.0f}s ({f.duracion_s:>3.0f}s): afluencia {f.afluencia:>5.2f}, "
                          f"daño {f.danio:>6.0f}, bajas {f.bajas:>5.0f}")
        fin = "VICTORIA" if p.victoria else f"muere en el nivel {int(p.nivel_alcanzado) + 1} (alcanza {p.nivel_alcanzado:.1f})"
        print(f"  -> partida esperada: {fin}; {p.puntos:.0f} puntos = {p.monedas} monedas; ~{p.minutos:.0f} min")


def _veredicto(r, nave):
    m = r.muertes(nave)
    if m < 0.3:
        return "fácil"
    if m < 1.0:
        return "posible"
    if m < nave.vidas:
        return f"duro ({m:.1f} muertes)"
    return "INVIABLE"


def informe_matriz(perfiles, fracciones, modelo):
    orden = orden_de_compra(modelo.arbol)
    _cabecera("PARTIDA ESPERADA: hasta qué nivel llega cada build (5.0 = victoria)")
    print(f"{'build':<8}" + "".join(f"{p.nombre:>10}" for p in perfiles))
    for fr in fracciones:
        ids, _ = build_al(orden, fr)
        fila = [jugar(modelo.nave(ids), p, modelo) for p in perfiles]
        print(f"{fr:<8.0%}" + "".join(f"{('VICTORIA' if x.victoria else f'{x.nivel_alcanzado:.1f}'):>10}" for x in fila))


def informe_progresion(perfiles, modelo, objetivo):
    _cabecera("PROGRESIÓN: partidas seguidas, gastando las monedas en el árbol")
    for p in perfiles:
        pr = progresion(p, modelo)
        texto = f"{pr.partidas_hasta_victoria} partidas" if pr.partidas_hasta_victoria else f"no llega en {MAX_PARTIDAS}"
        marca = ""
        if pr.partidas_hasta_victoria:
            marca = "  (objetivo ~%d)" % objetivo
        print(f"  {p.nombre:<8} completa la campaña en: {texto}{marca}")
    p = perfiles[min(1, len(perfiles) - 1)]
    pr = progresion(p, modelo)
    print(f"\n  Calendario de compras del perfil {p.nombre} (tras cada partida, en el orden barato-primero):")
    por_partida = {}
    for n, id_ in pr.compras:
        por_partida.setdefault(n, []).append(id_)
    for n in sorted(por_partida):
        print(f"    tras la partida {n:>3}: {', '.join(por_partida[n])}")
    huecos = [b - a for a, b in zip(sorted(por_partida), sorted(por_partida)[1:])]
    if huecos:
        print(f"    (la espera más larga entre compras: {max(huecos)} partidas)")
    print(f"\n  Curva del perfil {p.nombre} (partida | árbol comprado | nivel alcanzado):")
    mostrar = {1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 75, 100}
    for n, frac, nivel in pr.curva:
        if n in mostrar or n == len(pr.curva):
            print(f"    {n:>4} | {frac:>5.0%} | {nivel:>4.1f}")


def dps_necesario(nivel, perfil, nave, modelo=MODELO_ACTUAL, muertes_max=1.0):
    """DPS teórico mínimo para superar `nivel` con a lo sumo `muertes_max` muertes esperadas,
    con la salud y las vidas de `nave` (búsqueda por bisección sobre el daño de la bala)."""
    def muertes(dps):
        return analizar_nivel(replace(nave, danio=dps / (nave.balas * nave.disparos_s)),
                              nivel, perfil, modelo).muertes(nave)

    bajo, alto = 1.0, 100_000.0
    if muertes(alto) > muertes_max:
        return math.inf
    for _ in range(60):
        medio = (bajo + alto) / 2
        bajo, alto = (medio, alto) if muertes(medio) > muertes_max else (bajo, medio)
    return alto


def informe_poder_necesario(perfil, modelo, fracciones):
    orden = orden_de_compra(modelo.arbol)
    naves = [(fr, modelo.nave(build_al(orden, fr)[0])) for fr in (min(fracciones), max(fracciones))]
    _cabecera(f"PODER QUE EXIGE CADA NIVEL: DPS teórico para superarlo con <= 1 muerte esperada (perfil {perfil.nombre})")
    cab = f"{'nivel':>5}" + "".join(f"{f'con la nave al {fr:.0%}':>26}" for fr, _ in naves)
    print(cab)
    print(f"{'':>5}" + "".join(f"{f'({n.salud} salud, DPS {n.dps:.0f})':>26}" for _, n in naves))
    for nivel in range(1, NIVELES_CAMPANA + 1):
        celdas = []
        for _, n in naves:
            x = dps_necesario(nivel, perfil, n, modelo)
            celdas.append(f"{'imposible':>26}" if math.isinf(x) else f"{x:>26.0f}")
        print(f"{nivel:>5}" + "".join(celdas))
    techo = max(modelo.nave(build_al(orden, 1.0)[0]).dps, 0)
    print(f"  (el árbol entero da un DPS de {techo:.0f}: un nivel que exija más no se supera con este modelo)")
    print("  'imposible' = ni con DPS infinito se baja de 1 muerte: la densidad de enemigos y sus primeros disparos ya bastan")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Informe de balance de la campaña (modelo analítico).")
    ap.add_argument("--perfil", default="medio", choices=[*PERFILES, "todos"])
    ap.add_argument("--builds", default="0,25,50,75,100", help="porcentaje del coste del árbol, separados por comas")
    ap.add_argument("--niveles", action="store_true", help="detalle por fase de cada nivel")
    ap.add_argument("--objetivo", type=int, default=20, help="partidas que debería llevar completar la campaña")
    args = ap.parse_args(argv)

    perfiles = list(PERFILES.values()) if args.perfil == "todos" else [PERFILES[args.perfil]]
    fracciones = [float(x) / 100 for x in args.builds.split(",")]
    todos = list(PERFILES.values())

    informe_supuestos(perfiles if args.perfil != "todos" else todos)
    informe_arbol(MODELO_ACTUAL)
    for p in perfiles:
        informe_builds(p, fracciones, MODELO_ACTUAL, args.niveles)
    informe_matriz(todos, fracciones, MODELO_ACTUAL)
    informe_poder_necesario(perfiles[0] if args.perfil != "todos" else PERFILES["medio"], MODELO_ACTUAL, fracciones)
    informe_progresion(todos, MODELO_ACTUAL, args.objetivo)


if __name__ == "__main__":
    main()
