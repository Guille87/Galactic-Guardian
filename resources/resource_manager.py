import pygame


class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.resources = {}
            cls._instance.music_playing = {}  # Diccionario para mantener el estado de la música
        return cls._instance

    def __init__(self):
        self.resources = {}
        self.image_paths = {}

    def load_image(self, name, path):
        image = pygame.image.load(path)
        self.resources[name] = image
        self.image_paths[name] = path  # Guarda la ruta de la imagen asociada

    def get_image(self, name):
        return self.resources.get(name)

    def get_image_path(self, name):
        return self.image_paths.get(name)

    def load_sound(self, name, path):
        sound = pygame.mixer.Sound(path)
        self.resources[name] = sound

    def get_sound(self, name):
        # Devuelve el sonido correspondiente al nombre dado, si existe
        return self.resources.get(name)

    def load_font(self, name, path, size):
        font = pygame.font.Font(path, size)
        self.resources[name] = font

    def get_font(self, name):
        return self.resources.get(name)

    def set_music_volume(self, name, volume):
        music_sound = self.resources.get(name)
        if music_sound:
            music_sound.set_volume(volume)

    def play_music(self, name, loops=-1):
        music_sound = self.resources.get(name)
        if music_sound:
            music_sound.play(loops=loops)
            self.music_playing[name] = True  # Actualiza el estado de reproducción de la música

    def is_music_playing(self, name):
        return self.music_playing.get(name, False)

    def stop_music(self, name):
        music_sound = self.resources.get(name)
        if music_sound:
            music_sound.stop()
            self.music_playing[name] = False  # Actualiza el estado de reproducción de la música
