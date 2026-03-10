from efectos.destello import Destello
from efectos.destello_constante import DestelloConstante
from entidades.explosion import Explosion

class EffectManager:
    TAMANO_EXPLOSION = (64, 64)

    def __init__(self, juego):
        self.juego = juego
        # Pre-cargamos y escalamos la secuencia de animación una sola vez
        self.explosion_frames = self._preparar_frames_explosion()

    def _preparar_frames_explosion(self):
        """Prepara y cachea los frames de la explosión escalados."""
        frames = []
        for i in range(1, 12):
            nombre = f"explosion_{i}"
            # Usamos la nueva función del ResourceManager para obtenerlas optimizadas
            img = self.juego.rm.get_image_scaled(nombre, self.TAMANO_EXPLOSION)
            if img:
                frames.append(img)
        return frames

    def crear_explosion(self, posicion):
        """Crea una animación de explosión en el centro dado."""
        if self.explosion_frames:
            explosion = Explosion(posicion, self.explosion_frames)
            self.juego.all_sprites.add(explosion)

    def crear_destello_recibir_danio(self):
        """Crea el destello rojo efímero sobre el jugador."""
        if not self.juego.jugador.invulnerable:
            destello = Destello(self.juego.jugador)
            self.juego.all_sprites.add(destello)

    def crear_destello_invulnerabilidad(self):
        """Crea el halo blanco constante de invulnerabilidad."""
        # Solo crear si no hay uno ya activo
        if self.juego.jugador.destello_constante is None:
            destello = DestelloConstante(self.juego.jugador)
            self.juego.jugador.destello_constante = destello
            self.juego.all_sprites.add(destello)