import pygame

from src.entities.enemies import EnemigoTipo2, EnemigoTipo3, Jefe


class EntityManager:
    """Dueño de todos los grupos de sprites de la partida."""

    def __init__(self, juego):
        self.juego = juego
        self.balas = pygame.sprite.Group()          # balas del jugador
        self.balas_enemigo = pygame.sprite.Group()
        self.enemigos = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.efectos = pygame.sprite.Group()        # explosiones y destellos

    # --- Altas ---
    def agregar_enemigo(self, enemigo):
        if enemigo:
            self.enemigos.add(enemigo)

    def agregar_bala_jugador(self, bala):
        if bala:
            self.balas.add(bala)

    def agregar_bala_enemigo(self, bala):
        if bala:
            self.balas_enemigo.add(bala)

    # --- Ciclo por frame ---
    def actualizar(self, dt):
        """Actualiza el movimiento y la lógica de todas las entidades."""
        self.balas.update(dt)
        self.balas_enemigo.update(dt)
        self._actualizar_enemigos(dt)
        self.items.update(dt)
        self.efectos.update(dt)
        self._limpiar_entidades_fuera()

    def _actualizar_enemigos(self, dt):
        ahora = self.juego.tiempo_juego

        for enemigo in self.enemigos:
            enemigo.movimiento_enemigo(dt)
            enemigo.update(dt)

            # Disparo automático de los tipos 2 y 3
            if isinstance(enemigo, (EnemigoTipo2, EnemigoTipo3)):
                key_bala = "bala_enemigo" if isinstance(enemigo, EnemigoTipo2) else "bala_enemigo2"
                self.agregar_bala_enemigo(enemigo.disparo_enemigo(ahora, self.juego.rm, key_bala))

            # Disparo del jefe (dos cadencias)
            if isinstance(enemigo, Jefe):
                self.agregar_bala_enemigo(enemigo.disparo_jefe(ahora, self.juego.rm, "bala_enemigo2"))
                self.agregar_bala_enemigo(enemigo.disparo_rapido(ahora, self.juego.rm, "bala_enemigo"))

    def _limpiar_entidades_fuera(self):
        """Descarta enemigos y balas que se han salido de la pantalla."""
        alto = self.juego.pantalla_alto
        ancho = self.juego.pantalla_ancho

        def esta_fuera(rect):
            return rect.bottom < 0 or rect.top > alto or rect.right < 0 or rect.left > ancho

        for enemigo in list(self.enemigos):
            if esta_fuera(enemigo.rect):
                self.juego.enemigos_golpeados.pop(enemigo, None)
                enemigo.kill()

        for bala in list(self.balas):
            if esta_fuera(bala.rect):
                bala.kill()

        for bala in list(self.balas_enemigo):
            if esta_fuera(bala.rect):
                bala.kill()

    def vaciar_todo(self, avance_nivel=False):
        """Vacía los grupos de sprites.

        Con `avance_nivel=True` (se acaba de derrotar al jefe) se conservan las
        balas enemigas y los efectos ya en vuelo: así las balas del jefe no
        desaparecen de golpe al destruirlo y la explosión termina su animación.
        """
        grupos = [self.balas, self.enemigos, self.items]
        if not avance_nivel:
            grupos += [self.balas_enemigo, self.efectos]
        for grupo in grupos:
            grupo.empty()
