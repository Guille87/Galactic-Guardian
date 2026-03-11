import json
import os


class SistemaClasificacion:
    def __init__(self, ruta_archivo="data/saves/puntuaciones.json"):
        self.ruta_archivo = ruta_archivo
        self._asegurar_directorio()
        self.puntuaciones = self.cargar_puntuaciones()

    def _asegurar_directorio(self):
        """Crea la carpeta de guardado si no existe."""
        directorio = os.path.dirname(self.ruta_archivo)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio)

    def agregar_puntuacion(self, nombre, puntos):
        """Añade o actualiza la puntuación de un usuario."""
        puntos_actuales = self.puntuaciones.get(nombre, 0)
        if puntos > puntos_actuales:
            self.puntuaciones[nombre] = puntos
            self.guardar_puntuaciones()

    def obtener_puntuaciones_top(self, n=10):
        """Devuelve una lista ordenada de las mejores N puntuaciones."""
        return sorted(
            self.puntuaciones.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

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
