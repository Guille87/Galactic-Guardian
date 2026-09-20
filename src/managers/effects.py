from src.core import preferencias
from src.visual.flash import Destello
from src.visual.flash_constant import DestelloConstante
from src.visual.explosions import Explosion
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

    def _preparar_frames_explosion(self):
        """Fotogramas de la explosión (hoja "explosion") ya escalados y cacheados."""
        return self.rm.get_frames("explosion", self.TAMANO_EXPLOSION)

    def crear_explosion(self, posicion):
        """Crea una animación de explosión en el centro dado."""
        if self.explosion_frames:
            explosion = Explosion(posicion, self.explosion_frames)
            self.entity_manager.efectos.add(explosion)

    # El temblor se puede apagar desde Opciones (`preferencias.temblor_activado()`),
    # también a mitad de uno.
    def agregar_temblor(self, cantidad):
        """Suma trauma al temblor de pantalla (ver `settings.TEMBLOR_*`)."""
        if preferencias.temblor_activado():
            self.temblor.agregar(cantidad)

    def desplazamiento_temblor(self):
        """`(dx, dy)` del temblor para este frame; `(0, 0)` si está apagado."""
        return self.temblor.desplazamiento() if preferencias.temblor_activado() else (0, 0)

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