import pygame


class AudioManager:
    """Gestión de audio del juego.

    - Música: streaming vía ``pygame.mixer.music`` (una sola pista simultánea).
    - Efectos: ``pygame.mixer.Sound`` cacheados en memoria.
    """

    def __init__(self, resource_manager, volumen_musica, volumen_efectos):
        self.resource_manager = resource_manager
        self.vol_musica = volumen_musica
        self.vol_efectos = volumen_efectos

        # Pista de música actualmente cargada en el reproductor de streaming
        self.pista_actual = None

        # Diccionario de efectos para acceso rápido (alias -> Sound)
        self.efectos = {
            "disparo": self.resource_manager.get_sound("laser_gun"),
            "golpe": self.resource_manager.get_sound("hit"),
            "item": self.resource_manager.get_sound("item_take"),
        }

        pygame.mixer.music.set_volume(volumen_musica)
        self.actualizar_volumen_efectos(volumen_efectos)

    def actualizar_volumen_musica(self, nuevo_vol):
        """Ajusta el volumen de la música en streaming."""
        self.vol_musica = nuevo_vol
        pygame.mixer.music.set_volume(nuevo_vol)

    def actualizar_volumen_efectos(self, nuevo_vol):
        """Ajusta el volumen de todos los efectos de sonido."""
        self.vol_efectos = nuevo_vol
        for sonido in self.efectos.values():
            if sonido:
                sonido.set_volume(nuevo_vol)

    def reproducir_efecto(self, nombre):
        """Reproduce un efecto de sonido por su clave."""
        sonido = self.efectos.get(nombre)
        if sonido:
            sonido.play()

    def reproducir_musica(self, nombre, loops=-1, fade_ms=400):
        """Carga y reproduce una pista de música. Idempotente: si ya está sonando
        esa misma pista, no hace nada."""
        if nombre == self.pista_actual:
            return

        ruta = self.resource_manager.get_music_path(nombre)
        if not ruta:
            return

        pygame.mixer.music.load(ruta)
        pygame.mixer.music.set_volume(self.vol_musica)
        pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        self.pista_actual = nombre

    def detener_musica(self, nombre=None, fade_ms=300):
        """Detiene la música. El parámetro ``nombre`` se mantiene por
        compatibilidad: si se indica y no coincide con la pista actual, no hace
        nada."""
        if nombre is None or nombre == self.pista_actual:
            pygame.mixer.music.fadeout(fade_ms)
            self.pista_actual = None

    def detener_toda_la_musica(self, fade_ms=200):
        """Detiene cualquier música en reproducción."""
        pygame.mixer.music.fadeout(fade_ms)
        self.pista_actual = None
