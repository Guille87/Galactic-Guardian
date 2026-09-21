"""Progresión entre partidas: monedas y mejoras permanentes compradas.

`Progresion` guarda el saldo y las mejoras compradas en `data/saves/progresion.json`
(carpeta de datos de usuario, así que sobrevive a las actualizaciones). Se escribe
en cada cambio, de forma atómica (archivo temporal + reemplazo), y una carga
tolerante: un archivo ilegible o con datos raros no rompe el juego (se aparta a
`.corrupto` y se empieza de cero) y los datos sueltos inválidos se ignoran.

No conoce pygame ni la partida: `Juego` le ingresa monedas y le pide el `Bonus`;
el menú compra y restablece.
"""

import json
import os
import shutil

from src.core import mejoras, paths

VERSION_ARCHIVO = 2

# Lo que costaban las 12 mejoras de la versión 1 del archivo (el árbol de 4 nodos por
# rama): al cambiar el árbol se devuelve lo gastado en ellas, sin perder nada.
_COSTES_V1 = {f"{rama}_{n}": n * 100 for rama in ("ataque", "defensa", "utilidad") for n in (1, 2, 3, 4)}

# Resultados de `comprar`
OK = "ok"
YA_COMPRADA = "ya_comprada"
BLOQUEADA = "bloqueada"
SIN_SALDO = "sin_saldo"
DESCONOCIDA = "desconocida"

# Estados de una mejora (`estado`)
COMPRADA = "comprada"
DISPONIBLE = "disponible"


class Progresion:
    def __init__(self, ruta=None, persistir=True):
        """`ruta`: archivo de guardado (por defecto el del usuario). Con
        `persistir=False` todo queda en memoria y no se toca el disco."""
        self.persistir = persistir
        self.ruta = ruta or os.path.join(paths.dir_datos_usuario(), "data", "saves", "progresion.json")
        self.monedas = 0
        self.compradas = set()
        if persistir:
            self._cargar()

    # ------------------------------------------------------------- consulta
    def estado(self, id_):
        """`COMPRADA`, `DISPONIBLE` (su requisito ya está comprado) o `BLOQUEADA`."""
        if id_ in self.compradas:
            return COMPRADA
        mejora = mejoras.POR_ID[id_]
        if mejora.requiere is None or mejora.requiere in self.compradas:
            return DISPONIBLE
        return BLOQUEADA

    def bonus(self):
        return mejoras.calcular_bonus(self.compradas)

    def gastado(self):
        return sum(mejoras.POR_ID[i].coste for i in self.compradas)

    # ------------------------------------------------------------- acciones
    def ingresar(self, cantidad):
        """Suma monedas al saldo (las negativas o cero se ignoran)."""
        if cantidad > 0:
            self.monedas += int(cantidad)
            self._guardar()

    def comprar(self, id_):
        """Intenta comprar una mejora; devuelve `OK` o el motivo por el que no."""
        mejora = mejoras.POR_ID.get(id_)
        if mejora is None:
            return DESCONOCIDA
        if id_ in self.compradas:
            return YA_COMPRADA
        if self.estado(id_) == BLOQUEADA:
            return BLOQUEADA
        if self.monedas < mejora.coste:
            return SIN_SALDO
        self.monedas -= mejora.coste
        self.compradas.add(id_)
        self._guardar()
        return OK

    def restablecer(self):
        """Deshace todas las compras y devuelve **todas** las monedas gastadas."""
        devuelto = self.gastado()
        self.monedas += devuelto
        self.compradas.clear()
        self._guardar()
        return devuelto

    # ------------------------------------------------------------ persistencia
    def _guardar(self):
        if not self.persistir:
            return
        datos = {"version": VERSION_ARCHIVO, "monedas": self.monedas, "mejoras": sorted(self.compradas)}
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            temporal = self.ruta + ".tmp"
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2)
            os.replace(temporal, self.ruta)
        except OSError as e:
            print(f"No se pudo guardar la progresión: {e}")

    def _cargar(self):
        if not os.path.exists(self.ruta):
            return
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, dict):
                raise ValueError("el archivo no es un objeto JSON")
            monedas = datos.get("monedas", 0)
            ids = datos.get("mejoras", [])
            if not isinstance(monedas, int) or isinstance(monedas, bool) or not isinstance(ids, list):
                raise ValueError("campos con un tipo inesperado")
        except (OSError, ValueError) as e:      # `JSONDecodeError` es un `ValueError`
            print(f"Archivo de progresión ilegible ({e}); se aparta y se empieza de cero.")
            try:
                shutil.copyfile(self.ruta, self.ruta + ".corrupto")
            except OSError:
                pass
            return
        self.monedas = max(0, monedas)
        if datos.get("version", 1) < VERSION_ARCHIVO:
            # Archivo de un árbol anterior: sus ids ya no significan lo mismo, así que se
            # devuelven las monedas gastadas y se empieza con el árbol nuevo vacío.
            self.monedas += sum(_COSTES_V1.get(i, 0) for i in ids if isinstance(i, str))
            self.compradas = set()
            print("Árbol de mejoras actualizado: se han devuelto las monedas gastadas en el anterior.")
            self._guardar()
            return
        # Solo mejoras que existen, y solo las alcanzables: una cuya anterior no
        # esté comprada (archivo editado a mano) se descarta y se devuelve su coste.
        self.compradas = {i for i in ids if isinstance(i, str) and i in mejoras.POR_ID}
        cambiado = True
        while cambiado:
            cambiado = False
            for id_ in list(self.compradas):
                requiere = mejoras.POR_ID[id_].requiere
                if requiere is not None and requiere not in self.compradas:
                    self.compradas.discard(id_)
                    self.monedas += mejoras.POR_ID[id_].coste
                    cambiado = True
