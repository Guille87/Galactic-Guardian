class AudioManager:
    def __init__(self, resource_manager, volumen_musica, volumen_efectos):
        self.resource_manager = resource_manager
        self.vol_musica = volumen_musica
        self.vol_efectos = volumen_efectos

        # Diccionario interno para saber qué música está sonando
        self.musica_activa = {}

        # Diccionario de efectos para acceso rápido
        self.efectos = {
            "disparo": self.resource_manager.get_sound("laser_gun"),
            "golpe": self.resource_manager.get_sound("hit"),
            "item": self.resource_manager.get_sound("item_take")
        }

        self.actualizar_volumen_musica(volumen_musica)
        self.actualizar_volumen_efectos(volumen_efectos)


    def actualizar_volumen_musica(self, nuevo_vol):
        """Ajusta solo el volumen de la música."""
        self.vol_musica = nuevo_vol
        for nombre in self.musica_activa:
            track = self.resource_manager.get_sound(nombre)
            if track:
                track.set_volume(self.vol_musica)

    def actualizar_volumen_efectos(self, nuevo_vol):
        """Ajusta solo el volumen de los efectos de sonido."""
        self.vol_efectos = nuevo_vol
        for sonido in self.efectos.values():
            if sonido:
                sonido.set_volume(self.vol_efectos)

    def reproducir_efecto(self, nombre):
        """Reproduce un efecto de sonido por su clave."""
        sonido = self.efectos.get(nombre)
        if sonido:
            sonido.play()

    def reproducir_musica(self, nombre, loops=-1):
        """Gestiona la reproducción de música de fondo."""
        if nombre not in self.musica_activa:
            track = self.resource_manager.get_sound(nombre)
            if track:
                track.set_volume(self.vol_musica)
                track.play(loops=loops)
                self.musica_activa[nombre] = track

    def detener_musica(self, nombre):
        """Detiene una pista de música específica."""
        if nombre in self.musica_activa:
            self.musica_activa[nombre].stop()
            del self.musica_activa[nombre]

    def detener_toda_la_musica(self):
        """Limpia el canal de música."""
        for track in self.musica_activa.values():
            track.stop()
        self.musica_activa.clear()