import pygame

from src.entities.enemies import Jefe
from src.entities.items import Item


class CollisionManager:
    def __init__(self, juego):
        self.juego = juego  # Referencia al juego principal para acceder a sus listas y sonidos

    def actualizar(self):
        """Coordina todas las detecciones de colisiones."""
        self._colisiones_bala_jugador()
        self._colisiones_bala_enemigo()
        self._colisiones_jugador_enemigo()
        self._colisiones_jugador_items()

    def _colisiones_bala_jugador(self):
        """Balas del jugador impactando enemigos."""
        em = self.juego.entity_manager
        for bala in em.balas[:]:
            for enemigo in em.enemigos[:]:
                if bala.comprobar_colision(enemigo):
                    self._procesar_impacto_enemigo(bala, enemigo)
                    break

    def _procesar_impacto_enemigo(self, bala, enemigo):
        enemigo.take_damage(bala.danio)
        self.juego.audio_manager.reproducir_efecto("golpe")

        # Eliminar bala
        if bala in self.juego.entity_manager.balas:
            self.juego.entity_manager.balas.remove(bala)

        if enemigo.salud <= 0:
            self._eliminar_enemigo(enemigo)

    def _eliminar_enemigo(self, enemigo):
        if enemigo in self.juego.entity_manager.enemigos:
            self.juego.entity_manager.enemigos.remove(enemigo)

        # Efectos visuales
        self.juego.effect_manager.crear_explosion(enemigo.rect.center)

        # Soltar ítem
        self.juego.enemigos_eliminados += 1
        tipo_item = enemigo.die(self.juego.jugador, self.juego.enemigos_eliminados)

        if tipo_item:
            self._spawnear_item(tipo_item, enemigo.rect.center)
            self.juego.enemigos_eliminados = 0

        # Puntuación y lógica de Jefe
        self.juego.puntuacion += enemigo.valor_puntuacion * self.juego.nivel
        self.juego.enemigos_activos -= 1

        if isinstance(enemigo, Jefe):
            self.juego.jefe_derrotado = True
            self.juego.jefe = None
            self.juego.reiniciar_juego()

    def _spawnear_item(self, tipo, posicion):
        img = self.juego.rm.get_image_scaled(tipo, Item.TAMANO_ESTANDAR)
        nuevo_item = Item(tipo, img, posicion[0], posicion[1])
        self.juego.all_sprites.add(nuevo_item)

    def _colisiones_bala_enemigo(self):
        """Balas enemigas impactando al jugador."""
        em = self.juego.entity_manager
        for bala in em.balas_enemigo[:]:
            if bala.comprobar_colision(self.juego.jugador):
                if bala in em.balas_enemigo:
                    em.balas_enemigo.remove(bala)
                self.juego.jugador.recibir_danio(bala.danio)
                self.juego.manejar_impacto_jugador()
                self.juego.audio_manager.reproducir_efecto("golpe")

    def _colisiones_jugador_enemigo(self):
        """Colisión directa entre naves."""
        em = self.juego.entity_manager
        tiempo_actual = pygame.time.get_ticks()

        for enemigo in em.enemigos[:]:
            # VALIDACIÓN: Si el enemigo es None, lo saltamos
            if enemigo is None:
                continue

            if self.juego.jugador.rect.colliderect(enemigo.rect):
                tiempo_ultima_colision = self.juego.enemigos_golpeados.get(enemigo, 0)

                if tiempo_actual - tiempo_ultima_colision >= 2000:
                    self.juego.jugador.recibir_danio(1)
                    self.juego.audio_manager.reproducir_efecto("golpe")
                    self.juego.enemigos_golpeados[enemigo] = tiempo_actual
                    self.juego.manejar_impacto_jugador()
                    enemigo.salud -= 1

                if enemigo.salud <= 0:
                    self._eliminar_enemigo(enemigo)

    def _colisiones_jugador_items(self):
        """Recogida de power-ups."""
        for sprite in self.juego.all_sprites:
            if isinstance(sprite, Item) and self.juego.jugador.rect.colliderect(sprite.rect):
                self.juego.audio_manager.reproducir_efecto("item")
                sprite.aplicar_efecto(self.juego.jugador)
                sprite.kill()