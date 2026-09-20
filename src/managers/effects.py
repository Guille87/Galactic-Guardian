from src.core import preferencias
from src.visual.flash import Destello
from src.visual.flash_constant import DestelloConstante
from src.visual.explosions import Explosion
from src.visual.hit_stop import HitStop
from src.visual.screen_shake import Temblor


class EffectManager:
    TAMANO_EXPLOSION = (64, 64)

    def __init__(self, resource_manager, entity_manager, jugador):
        self.rm = resource_manager
        self.entity_manager = entity_manager
        self.jugador = jugador
        # Pre-cargamos y escalamos la secuencia de animación una sola vez
        self.explosion_frames = self._preparar_frames_explosion()
        self.temblor = Temblor()   # lo avanza `Juego.actualizar` y lo aplica `RenderManager`
        self.hit_stop = HitStop()  # lo gasta `Juego.actualizar`, que no simula mientras está activo

    def _preparar_frames_explosion(self):
        """Prepara y cachea los frames de la explosión escalados."""
        frames = []
        for i in range(1, 12):
            nombre = f"explosion_{i}"
            # Usamos la nueva función del ResourceManager para obtenerlas optimizadas
            img = self.rm.get_image_scaled(nombre, self.TAMANO_EXPLOSION)
            if img:
                frames.append(img)
        return frames

    def crear_explosion(self, posicion):
        """Crea una animación de explosión en el centro dado."""
        if self.explosion_frames:
            explosion = Explosion(posicion, self.explosion_frames)
            self.entity_manager.efectos.add(explosion)

    # Temblor y hit-stop son "efectos de pantalla": se apagan juntos desde
    # Opciones (`preferencias.efectos_pantalla()`), también a mitad de uno.
    def agregar_temblor(self, cantidad):
        """Suma trauma al temblor de pantalla (ver `settings.TEMBLOR_*`)."""
        if preferencias.efectos_pantalla():
            self.temblor.agregar(cantidad)

    def desplazamiento_temblor(self):
        """`(dx, dy)` del temblor para este frame; `(0, 0)` si los efectos están apagados."""
        return self.temblor.desplazamiento() if preferencias.efectos_pantalla() else (0, 0)

    def agregar_hit_stop(self, ms):
        """Pide un congelado breve de la partida (ver `settings.HIT_STOP_*`)."""
        if preferencias.efectos_pantalla():
            self.hit_stop.agregar(ms)

    @property
    def congelado(self):
        """True mientras la partida está detenida por un hit-stop."""
        return self.hit_stop.activo and preferencias.efectos_pantalla()

    def crear_destello_recibir_danio(self):
        """Crea el destello rojo efímero sobre el jugador."""
        if not self.jugador.invulnerable:
            destello = Destello(self.jugador)
            self.entity_manager.efectos.add(destello)

    def crear_destello_invulnerabilidad(self):
        """Crea el halo blanco constante de invulnerabilidad."""
        # Solo crear si no hay uno ya activo
        if self.jugador.destello_constante is None:
            destello = DestelloConstante(self.jugador)
            self.jugador.destello_constante = destello
            self.entity_manager.efectos.add(destello)