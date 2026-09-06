import pygame

from src.core import settings
from src.entities.enemies import Jefe
from src.entities.items import Item


class CollisionManager:
    """Resolución de colisiones usando grupos de sprites de pygame.

    - Balas <-> naves: colisión circular (`collide_circle`, usa `sprite.radius`).
    - Contacto cuerpo a cuerpo y recogida de ítems: colisión rectangular.
    """

    def __init__(self, juego):
        self.juego = juego

    def actualizar(self):
        self._balas_jugador_vs_enemigos()
        self._balas_enemigo_vs_jugador()
        self._contacto_cuerpo_a_cuerpo()
        self._jugador_vs_items()

    # ------------------------------------------------------------------
    def _balas_jugador_vs_enemigos(self):
        em = self.juego.entity_manager
        impactos = pygame.sprite.groupcollide(
            em.balas, em.enemigos, True, False,
            collided=pygame.sprite.collide_circle,
        )
        for bala, enemigos_tocados in impactos.items():
            enemigo = enemigos_tocados[0]  # una bala daña a un solo enemigo
            enemigo.take_damage(bala.danio)
            if enemigo.salud <= 0:
                self._eliminar_enemigo(enemigo)

        # Un solo "golpe" por frame, no uno por bala (evita saturar el mixer)
        if impactos:
            self.juego.audio_manager.reproducir_efecto("golpe")

    def _balas_enemigo_vs_jugador(self):
        em = self.juego.entity_manager
        tocadas = pygame.sprite.spritecollide(
            self.juego.jugador, em.balas_enemigo, True,
            collided=pygame.sprite.collide_circle,
        )
        for bala in tocadas:
            self.juego.jugador.recibir_danio(bala.danio)
            self.juego.manejar_impacto_jugador()

        if tocadas:
            self.juego.audio_manager.reproducir_efecto("golpe")

    def _contacto_cuerpo_a_cuerpo(self):
        em = self.juego.entity_manager
        ahora = pygame.time.get_ticks()

        for enemigo in pygame.sprite.spritecollide(self.juego.jugador, em.enemigos, False):
            ultimo = self.juego.enemigos_golpeados.get(enemigo, 0)
            if ahora - ultimo >= settings.CONTACTO_COOLDOWN_MS:
                self.juego.jugador.recibir_danio(settings.DANIO_CONTACTO)
                self.juego.audio_manager.reproducir_efecto("golpe")
                self.juego.enemigos_golpeados[enemigo] = ahora
                self.juego.manejar_impacto_jugador()
                enemigo.salud -= 1

            if enemigo.salud <= 0:
                self._eliminar_enemigo(enemigo)

    def _jugador_vs_items(self):
        em = self.juego.entity_manager
        for item in pygame.sprite.spritecollide(self.juego.jugador, em.items, True):
            self.juego.audio_manager.reproducir_efecto("item")
            item.aplicar_efecto(self.juego.jugador)

    # ------------------------------------------------------------------
    def _eliminar_enemigo(self, enemigo):
        em = self.juego.entity_manager
        if enemigo not in em.enemigos:
            return  # ya procesado en este mismo frame (p. ej. dos balas a la vez)

        enemigo.kill()
        self.juego.enemigos_golpeados.pop(enemigo, None)

        # Efecto visual
        self.juego.effect_manager.crear_explosion(enemigo.rect.center)

        # Loot (con contador de "piedad")
        self.juego.enemigos_eliminados += 1
        tipo_item = enemigo.die(self.juego.jugador, self.juego.enemigos_eliminados)
        if tipo_item:
            self._spawnear_item(tipo_item, enemigo.rect.center)
            self.juego.enemigos_eliminados = 0

        # Puntuación
        self.juego.puntuacion += enemigo.valor_puntuacion * self.juego.nivel

        # Jefe derrotado -> transición diferida (la ejecuta Juego.actualizar)
        if isinstance(enemigo, Jefe):
            self.juego.jefe_derrotado = True
            self.juego.jefe = None
            self.juego.pendiente_reinicio = True

    def _spawnear_item(self, tipo, posicion):
        img = self.juego.rm.get_image_scaled(tipo, Item.TAMANO_ESTANDAR)
        nuevo_item = Item(tipo, img, posicion[0], posicion[1])
        self.juego.entity_manager.items.add(nuevo_item)
