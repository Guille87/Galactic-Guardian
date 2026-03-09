from efectos.destello import Destello
from efectos.destello_constante import DestelloConstante
from entidades.explosion import Explosion

class EffectManager:
    def __init__(self, juego):
        self.juego = juego
        # Guardamos las imágenes de explosión aquí para no pedirlas cada vez
        self.explosion_images = [
            self.juego.rm.get_image(f"explosion_{i}") for i in range(1, 12)
        ]

    def crear_explosion(self, posicion):
        """Crea una animación de explosión en el centro dado."""
        explosion = Explosion(posicion, self.explosion_images)
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