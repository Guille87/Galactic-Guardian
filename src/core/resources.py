import pygame


class ResourceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.resources = {}
            cls._instance.image_paths = {}
            cls._instance.music_data = {}
            cls._instance.spritesheets = {}   # nombre -> lista de fotogramas (Surface)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'scaled_resources'):
            self.scaled_resources = {}  # Cache para versiones reescaladas / rotadas

    def load_image(self, name, path):
        """Carga una imagen y la convierte al formato de la pantalla.

        `convert()` / `convert_alpha()` evitan que cada blit tenga que convertir
        el formato al vuelo (imprescindible para el fondo a pantalla completa).
        """
        surface = pygame.image.load(path)
        if surface.get_flags() & pygame.SRCALPHA or surface.get_alpha() is not None:
            surface = surface.convert_alpha()
        else:
            surface = surface.convert()
        self.resources[name] = surface
        self.image_paths[name] = path  # Guarda la ruta de la imagen asociada

    def load_spritesheet(self, name, path, columnas, filas, cantidad=None):
        """Carga una hoja de sprites y la corta en fotogramas iguales.

        La hoja es una rejilla regular de `columnas` x `filas` celdas del mismo
        tamaño, sin márgenes entre ellas; los fotogramas se numeran de izquierda a
        derecha y de arriba abajo. `cantidad` es cuántos son válidos cuando las
        últimas celdas de la rejilla están vacías (por defecto, todas).
        Se recuperan con `get_frames`."""
        hoja = pygame.image.load(path).convert_alpha()
        ancho, alto = hoja.get_size()
        if columnas < 1 or filas < 1 or ancho % columnas or alto % filas:
            raise ValueError(
                f"La hoja '{name}' ({ancho}x{alto}) no se divide en {columnas}x{filas} celdas iguales")
        total = columnas * filas
        cantidad = total if cantidad is None else cantidad
        if not 1 <= cantidad <= total:
            raise ValueError(f"La hoja '{name}' tiene {total} celdas y se piden {cantidad} fotogramas")

        ancho_f, alto_f = ancho // columnas, alto // filas
        self.spritesheets[name] = [
            hoja.subsurface(pygame.Rect((n % columnas) * ancho_f, (n // columnas) * alto_f, ancho_f, alto_f)).copy()
            for n in range(cantidad)
        ]

    def load_sound(self, name, path):
        self.resources[name] = pygame.mixer.Sound(path)

    def load_music(self, name, path):
        """Carga los bytes (OGG comprimido) de una pista de música en memoria.

        Son unos pocos MB en total. `pygame.mixer.music.load()` desde una ruta
        abre el archivo en el hilo principal y bloquea ~200-400 ms (tirón al
        cambiar de música); desde un BytesIO en RAM es instantáneo. La música
        se sigue decodificando al vuelo, no se descomprime entera.
        """
        with open(path, "rb") as f:
            self.music_data[name] = f.read()

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

    def get_frames(self, name, size=None):
        """Fotogramas de una hoja cargada con `load_spritesheet`, como lista nueva.

        Con `size` devuelve cada uno reescalado a ese tamaño (cacheado, como
        `get_image_scaled`); sin él, a tamaño original."""
        frames = self.spritesheets.get(name)
        if frames is None:
            print(f"ERROR: No se encontró la hoja de sprites: {name}")
            return []
        if size is None:
            return list(frames)

        cache_key = f"{name}_frames_{size[0]}x{size[1]}"
        if cache_key not in self.scaled_resources:
            self.scaled_resources[cache_key] = [
                pygame.transform.scale(f, size).convert_alpha() for f in frames
            ]
        return list(self.scaled_resources[cache_key])

    def get_image_rotated(self, name, size, angle):
        """Devuelve la imagen escalada y rotada, cacheada por (nombre, tamaño, ángulo).

        Evita reescalar/rotar una `Surface` por cada proyectil creado.
        """
        ang = int(round(angle)) % 360
        cache_key = f"{name}_{size[0]}x{size[1]}_r{ang}"

        cached = self.scaled_resources.get(cache_key)
        if cached is None:
            base = self.get_image_scaled(name, size)
            if base is None:
                return None
            cached = pygame.transform.rotate(base, ang) if ang else base
            self.scaled_resources[cache_key] = cached
        return cached

    def get_image_path(self, name):
        return self.image_paths.get(name)

    def get_music_data(self, name):
        return self.music_data.get(name)

    def get_sound(self, name):
        # Devuelve el sonido correspondiente al nombre dado, si existe
        return self.resources.get(name)

    def load_font(self, name, path, size):
        self.resources[name] = pygame.font.Font(path, size)

    def get_font(self, name):
        return self.resources.get(name)
