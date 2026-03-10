import pygame

from entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from entidades.item import Item


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
            img = self.juego.rm.get_image_scaled(tipo_item, Item.TAMANO_ESTANDAR)
            nuevo_item = Item(tipo_item, img, enemigo.rect.centerx, enemigo.rect.centery)

            self.juego.all_sprites.add(nuevo_item)
            self.juego.enemigos_eliminados = 0

        # Puntuación y lógica de Jefe
        puntuacion = self._obtener_puntuacion(enemigo)
        self.juego.puntuacion += puntuacion * self.juego.nivel
        self.juego.enemigos_activos -= 1

        if isinstance(enemigo, Jefe):
            self.juego.jefe_derrotado = True
            self.juego.jefe = None
            self.juego.reiniciar_juego()

    @staticmethod
    def _obtener_puntuacion(enemigo):
        if isinstance(enemigo, EnemigoTipo1): return 1
        if isinstance(enemigo, EnemigoTipo2): return 2
        if isinstance(enemigo, EnemigoTipo3): return 3
        if isinstance(enemigo, Jefe): return 1000
        return 0

    def _colisiones_bala_enemigo(self):
        em = self.juego.entity_manager
        for bala in em.balas_enemigo[:]:
            if bala.comprobar_colision(self.juego.jugador):
                if bala in em.balas_enemigo:
                    em.balas_enemigo.remove(bala)
                self.juego.jugador.reducir_salud(bala.danio)
                self.juego.manejar_impacto_jugador()
                self.juego.audio_manager.reproducir_efecto("golpe")

    def _colisiones_jugador_enemigo(self):
        em = self.juego.entity_manager
        tiempo_actual = pygame.time.get_ticks()

        for enemigo in em.enemigos[:]:
            # VALIDACIÓN: Si el enemigo es None, lo saltamos
            if enemigo is None:
                continue

            if self.juego.jugador.rect.colliderect(enemigo.rect):
                tiempo_ultima_colision = self.juego.enemigos_golpeados.get(enemigo, 0)

                if tiempo_actual - tiempo_ultima_colision >= 2000:
                    self.juego.jugador.reducir_salud(1)
                    self.juego.audio_manager.reproducir_efecto("golpe")
                    self.juego.enemigos_golpeados[enemigo] = tiempo_actual
                    self.juego.manejar_impacto_jugador()
                    enemigo.salud -= 1

                if enemigo.salud <= 0:
                    self._eliminar_enemigo(enemigo)

    def _colisiones_jugador_items(self):
        for sprite in self.juego.all_sprites:
            if isinstance(sprite, Item) and self.juego.jugador.rect.colliderect(sprite.rect):
                self.juego.audio_manager.reproducir_efecto("item")
                sprite.aplicar_efecto(self.juego.jugador)
                sprite.kill()