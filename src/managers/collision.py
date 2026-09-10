import pygame

from src.core import settings


class CollisionManager:
    """Detección de colisiones y su respuesta **mecánica**.

    Colaboradores explícitos (mecánica pura): los grupos de entidades, el
    jugador, los efectos, el audio y el registro de cooldown de contacto.

    Las consecuencias de **reglas de partida** (puntuación, loot, progresión de
    nivel, muerte/reaparición del jugador) NO se aplican aquí: se delegan en
    `reglas`, que debe ofrecer dos métodos:

      - ``reglas.al_eliminar_enemigo(enemigo)`` — puntuación, loot, transición
        de jefe. Se llama **después** de que este manager haya hecho la parte
        mecánica (``kill``, explosión, purga del cooldown).
      - ``reglas.manejar_impacto_jugador()`` — destello / explosión / pérdida de
        vida y reaparición. Se llama tras aplicar el daño al jugador.

    Colisiones:
      - Balas <-> naves: colisión circular (``collide_circle``, usa ``radius``).
      - Contacto cuerpo a cuerpo y recogida de ítems: colisión rectangular.
    """

    def __init__(self, entity_manager, jugador, effect_manager, audio_manager,
                 enemigos_golpeados, reglas):
        self.em = entity_manager
        self.jugador = jugador
        self.efectos = effect_manager
        self.audio = audio_manager
        self.enemigos_golpeados = enemigos_golpeados
        self.reglas = reglas

    def actualizar(self, tiempo_juego):
        self._balas_jugador_vs_enemigos()
        self._balas_enemigo_vs_jugador()
        self._contacto_cuerpo_a_cuerpo(tiempo_juego)
        self._jugador_vs_items()

    # ------------------------------------------------------------------
    def _balas_jugador_vs_enemigos(self):
        impactos = pygame.sprite.groupcollide(
            self.em.balas, self.em.enemigos, True, False,
            collided=pygame.sprite.collide_circle,
        )
        for bala, enemigos_tocados in impactos.items():
            enemigo = enemigos_tocados[0]  # una bala daña a un solo enemigo
            enemigo.take_damage(bala.danio)
            if enemigo.salud <= 0:
                self._eliminar_enemigo(enemigo)

        # Un solo "golpe" por frame, no uno por bala (evita saturar el mixer)
        if impactos:
            self.audio.reproducir_efecto("golpe")

    def _balas_enemigo_vs_jugador(self):
        tocadas = pygame.sprite.spritecollide(
            self.jugador, self.em.balas_enemigo, True,
            collided=pygame.sprite.collide_circle,
        )
        for bala in tocadas:
            self.jugador.recibir_danio(bala.danio)
            self.reglas.manejar_impacto_jugador()

        if tocadas:
            self.audio.reproducir_efecto("golpe")

    def _contacto_cuerpo_a_cuerpo(self, ahora):
        for enemigo in pygame.sprite.spritecollide(self.jugador, self.em.enemigos, False):
            ultimo = self.enemigos_golpeados.get(enemigo, 0)
            if ahora - ultimo >= settings.CONTACTO_COOLDOWN_MS:
                self.jugador.recibir_danio(settings.DANIO_CONTACTO)
                self.audio.reproducir_efecto("golpe")
                self.enemigos_golpeados[enemigo] = ahora
                self.reglas.manejar_impacto_jugador()
                enemigo.salud -= 1

            if enemigo.salud <= 0:
                self._eliminar_enemigo(enemigo)

    def _jugador_vs_items(self):
        for item in pygame.sprite.spritecollide(self.jugador, self.em.items, True):
            self.audio.reproducir_efecto("item")
            item.aplicar_efecto(self.jugador)

    # ------------------------------------------------------------------
    def _eliminar_enemigo(self, enemigo):
        if enemigo not in self.em.enemigos:
            return  # ya procesado en este mismo frame (p. ej. dos balas a la vez)

        enemigo.kill()
        self.enemigos_golpeados.pop(enemigo, None)
        self.efectos.crear_explosion(enemigo.rect.center)

        # Puntuación, loot y transición de jefe: reglas de partida.
        self.reglas.al_eliminar_enemigo(enemigo)
