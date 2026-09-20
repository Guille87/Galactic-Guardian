class HitStop:
    """Congelado breve de la partida tras un golpe fuerte ("hit-stop").

    Solo lleva la cuenta de los milisegundos que faltan; quien lo usa
    (`Juego.actualizar`) es quien deja de avanzar la simulación mientras está
    activo. Se gasta con tiempo real (`dt`), no con el reloj de juego, que es
    justo lo que está parado."""

    def __init__(self):
        self.restante_ms = 0.0

    @property
    def activo(self):
        return self.restante_ms > 0

    def agregar(self, ms):
        """Pide `ms` de congelado. No se suman: se queda el mayor, para que dos
        golpes seguidos no encadenen una parada larga."""
        self.restante_ms = max(self.restante_ms, ms)

    def actualizar(self, dt):
        if self.restante_ms > 0:
            self.restante_ms = max(0.0, self.restante_ms - dt * 1000)

    def reiniciar(self):
        self.restante_ms = 0.0
