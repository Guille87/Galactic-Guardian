"""Guardado de partida: el último nivel (campaña) u oleada (sin fin) al que se ha llegado.

Es un **punto de control**, no una foto de la partida: al terminar un nivel o cambiar de
oleada se apunta el siguiente con la puntuación que llevabas, y "Continuar" arranca ahí
(con las vidas y la salud de partida nueva, sin combo). Se conserva aunque pierdas todas
las vidas o cierres el juego: así, quien va avanzado no tiene que rejugar los niveles
fáciles. Solo se borra al empezar una partida nueva o al completar la campaña.

Un archivo por modo en `data/saves/`, escrito de forma atómica. Es tolerante, como
`progresion.py`: un archivo ilegible o con datos raros no rompe el juego (se aparta a
`.corrupto` y no hay guardado). No conoce pygame ni la partida.
"""

import json
import os
import shutil

from src.core import paths, settings

VERSION_ARCHIVO = 1

_ARCHIVOS = {
    settings.MODO_CAMPANA: "partida_campana.json",
    settings.MODO_SIN_FIN: "partida_sin_fin.json",
}
NIVEL_MAX_SIN_FIN = 10_000       # tope de cordura al leer un archivo (las oleadas no tienen techo)


class Guardado:
    def __init__(self, modo=settings.MODO_CAMPANA, ruta=None, persistir=True):
        """`ruta`: archivo de guardado (por defecto el del usuario para `modo`). Con
        `persistir=False` todo queda en memoria y no se toca el disco."""
        self.modo = modo
        self.persistir = persistir
        self.ruta = ruta or os.path.join(paths.dir_datos_usuario(), "data", "saves", _ARCHIVOS[modo])
        self.nivel = None            # nivel u oleada al que se continúa (None = no hay guardado)
        self.puntuacion = 0
        if persistir:
            self._cargar()

    @property
    def existe(self):
        return self.nivel is not None

    def _nivel_maximo(self):
        return settings.NIVEL_MAX if self.modo == settings.MODO_CAMPANA else NIVEL_MAX_SIN_FIN

    # ------------------------------------------------------------------ escritura
    def guardar_punto(self, nivel, puntuacion):
        """Apunta que se continuará en `nivel` con `puntuacion`. **Nunca retrocede**: rejugar un
        nivel ya superado (selector de niveles) no borra el avance que ya se tenía."""
        nivel, puntuacion = int(nivel), max(0, int(puntuacion))
        if self.existe and nivel < self.nivel:
            return False
        self.nivel, self.puntuacion = min(nivel, self._nivel_maximo()), puntuacion
        self._escribir()
        return True

    def borrar(self):
        """Elimina el guardado (empezar de cero, o campaña completada)."""
        self.nivel, self.puntuacion = None, 0
        if not self.persistir:
            return
        try:
            os.remove(self.ruta)
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"No se pudo borrar la partida guardada: {e}")

    def _escribir(self):
        if not self.persistir:
            return
        datos = {"version": VERSION_ARCHIVO, "modo": self.modo, "nivel": self.nivel,
                 "puntuacion": self.puntuacion}
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            temporal = self.ruta + ".tmp"
            with open(temporal, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2)
            os.replace(temporal, self.ruta)
        except OSError as e:
            print(f"No se pudo guardar la partida: {e}")

    # ------------------------------------------------------------------- lectura
    def _cargar(self):
        if not os.path.exists(self.ruta):
            return
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, dict):
                raise ValueError("el archivo no es un objeto JSON")
            nivel, puntuacion = datos.get("nivel"), datos.get("puntuacion", 0)
            for valor in (nivel, puntuacion):
                if not isinstance(valor, int) or isinstance(valor, bool):
                    raise ValueError("campos con un tipo inesperado")
            if not 1 <= nivel <= self._nivel_maximo() or puntuacion < 0:
                raise ValueError("valores fuera de rango")
            if datos.get("modo", self.modo) != self.modo:
                raise ValueError("el archivo es de otro modo de juego")
        except (OSError, ValueError) as e:      # `JSONDecodeError` es un `ValueError`
            print(f"Partida guardada ilegible ({e}); se ignora.")
            try:
                shutil.copyfile(self.ruta, self.ruta + ".corrupto")
            except OSError:
                pass
            return
        self.nivel, self.puntuacion = nivel, puntuacion
