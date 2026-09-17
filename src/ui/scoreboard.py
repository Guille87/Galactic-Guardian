import json
import os

from src.core import paths


class SistemaClasificacion:
    def __init__(self, ruta_archivo=None):
        self.ruta_archivo = ruta_archivo or os.path.join(
            paths.dir_datos_usuario(), "data", "saves", "puntuaciones.json"
        )
        self._asegurar_directorio()
        self.puntuaciones = self.cargar_puntuaciones()

    def _asegurar_directorio(self):
        """Crea la carpeta de guardado si no existe."""
        directorio = os.path.dirname(self.ruta_archivo)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio)

    def agregar_puntuacion(self, nombre, puntos, nivel=None):
        """Añade o actualiza la puntuación de un usuario (y el nivel alcanzado)."""
        puntos_actuales = self._puntos_de(self.puntuaciones.get(nombre))
        if puntos > puntos_actuales:
            self.puntuaciones[nombre] = {"puntos": puntos, "nivel": nivel}
            self.guardar_puntuaciones()

    @staticmethod
    def _puntos_de(valor):
        """Puntos de una entrada, sea del formato nuevo (dict) o del antiguo
        (un `int` suelto, de antes de que se guardara el nivel alcanzado)."""
        if isinstance(valor, dict):
            return valor.get("puntos", 0)
        return valor or 0

    def obtener_puntuaciones_top(self, n=10):
        """Lista de `(nombre, puntos, nivel)` ordenada de mayor a menor puntos.

        `nivel` es `None` en entradas guardadas antes de que existiera la
        campaña (formato antiguo: solo un número suelto).
        """
        filas = []
        for nombre, valor in self.puntuaciones.items():
            if isinstance(valor, dict):
                filas.append((nombre, valor.get("puntos", 0), valor.get("nivel")))
            else:
                filas.append((nombre, valor, None))
        filas.sort(key=lambda fila: fila[1], reverse=True)
        return filas[:n]

    def guardar_puntuaciones(self):
        """Persistencia de datos en formato JSON."""
        try:
            with open(self.ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(self.puntuaciones, f, indent=4)
        except IOError as e:
            print(f"Error de E/S al guardar: {e}")

    def cargar_puntuaciones(self):
        """Carga datos desde el archivo, manejando errores de formato."""
        if not os.path.exists(self.ruta_archivo):
            return {}

        try:
            with open(self.ruta_archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Archivo de puntuaciones corrupto o ilegible: {e}")
            return {}
