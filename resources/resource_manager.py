import pygame


class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.resources = {}
            cls._instance.image_paths = {}
        return cls._instance

    def __init__(self):
        # El init debe estar vacío o controlado para no resetear los diccionarios del Singleton
        pass

    def load_image(self, name, path):
        self.resources[name] = pygame.image.load(path)
        self.image_paths[name] = path  # Guarda la ruta de la imagen asociada

    def load_sound(self, name, path):
        self.resources[name] = pygame.mixer.Sound(path)

    def get_image(self, name):
        return self.resources.get(name)

    def get_image_path(self, name):
        return self.image_paths.get(name)

    def get_sound(self, name):
        # Devuelve el sonido correspondiente al nombre dado, si existe
        return self.resources.get(name)

    def load_font(self, name, path, size):
        self.resources[name] = pygame.font.Font(path, size)

    def get_font(self, name):
        return self.resources.get(name)
