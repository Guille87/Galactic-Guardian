import json


class SistemaClasificacion:
    def __init__(self, archivo_puntuaciones="puntuaciones.json"):
        self.archivo_puntuaciones = archivo_puntuaciones
        self.puntuaciones = self.cargar_puntuaciones()

    def agregar_puntuacion(self, nombre_usuario, puntuacion):
        self.puntuaciones[nombre_usuario] = puntuacion
        self.guardar_puntuaciones()
        self.cerrar_archivo()

    def cerrar_archivo(self):
        """Cerrar el archivo de puntuaciones."""
        # Cerrar el archivo solo si está abierto
        if hasattr(self, 'archivo'):
            self.archivo.close()

    def obtener_puntuaciones_top(self, n=10):
        puntuaciones_ordenadas = sorted(self.puntuaciones.items(), key=lambda x: x[1], reverse=True)
        return puntuaciones_ordenadas[:n]

    def guardar_puntuaciones(self):
        try:
            with open(self.archivo_puntuaciones, "w") as self.archivo:
                json.dump(self.puntuaciones, self.archivo)
        except Exception as e:
            print("Error al guardar puntuaciones:", e)

    def cargar_puntuaciones(self):
        try:
            with open(self.archivo_puntuaciones, "r") as f:
                puntuaciones = json.load(f)
        except FileNotFoundError:
            puntuaciones = {}
        except Exception as e:
            print("Error al cargar puntuaciones:", e)
            puntuaciones = {}
        return puntuaciones
