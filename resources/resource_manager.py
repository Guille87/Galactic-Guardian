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
        if not hasattr(self, 'scaled_resources'):
            self.scaled_resources = {}  # Cache para versiones reescalada

    def load_image(self, name, path):
        self.resources[name] = pygame.image.load(path)
        self.image_paths[name] = path  # Guarda la ruta de la imagen asociada

    def load_sound(self, name, path):
        self.resources[name] = pygame.mixer.Sound(path)

    def get_image(self, name):
        return self.resources.get(name)

    def get_image_scaled(self, name, size):
        """Devuelve una imagen reescalada. Si ya se escaló antes, la saca del caché."""
        cache_key = f"{name}_{size[0]}x{size[1]}"

        if cache_key not in self.scaled_resources:
            original = self.get_image(name)
            if original:
                # Convert_alpha() es vital para el rendimiento de Pygame
                scaled = pygame.transform.scale(original, size).convert_alpha()
                self.scaled_resources[cache_key] = scaled
            else:
                print(f"ERROR: No se encontró el recurso: {name}")
                return None

        return self.scaled_resources[cache_key]

    def get_image_path(self, name):
        return self.image_paths.get(name)

    def get_sound(self, name):
        # Devuelve el sonido correspondiente al nombre dado, si existe
        return self.resources.get(name)

    def load_font(self, name, path, size):
        self.resources[name] = pygame.font.Font(path, size)

    def get_font(self, name):
        return self.resources.get(name)
