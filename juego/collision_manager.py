import pygame
from entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe
from entidades.explosion import Explosion
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
        for bala in self.juego.balas[:]:
            for enemigo in self.juego.enemigos[:]:
                if bala.comprobar_colision(enemigo):
                    self._procesar_impacto_enemigo(bala, enemigo)
                    break

    def _procesar_impacto_enemigo(self, bala, enemigo):
        enemigo.take_damage(bala.danio)
        self.juego.audio_manager.reproducir_efecto("golpe")

        # Eliminar bala
        if bala in self.juego.balas:
            self.juego.balas.remove(bala)

        if enemigo.salud <= 0:
            self._eliminar_enemigo(enemigo)

    def _eliminar_enemigo(self, enemigo):
        if enemigo in self.juego.enemigos:
            self.juego.enemigos.remove(enemigo)

        # Efectos visuales
        self.juego.effect_manager.crear_explosion(enemigo.rect.center)

        # Soltar ítem
        self.juego.enemigos_eliminados += 1
        objeto = enemigo.die(self.juego.jugador, self.juego.enemigos_eliminados)
        if objeto:
            self.juego.all_sprites.add(objeto)
            self.juego.enemigos_eliminados = 0

        # Puntuación y lógica de Jefe
        puntuacion = self._obtener_puntuacion(enemigo)
        self.juego.puntuacion += puntuacion * self.juego.nivel
        self.juego.enemigos_activos -= 1

        if isinstance(enemigo, Jefe):
            self.juego.jefe_derrotado = True
            self.juego.jefe = None
            self.juego.reiniciar_juego()

    def _obtener_puntuacion(self, enemigo):
        if isinstance(enemigo, EnemigoTipo1): return 1
        if isinstance(enemigo, EnemigoTipo2): return 2
        if isinstance(enemigo, EnemigoTipo3): return 3
        if isinstance(enemigo, Jefe): return 1000
        return 0

    def _colisiones_bala_enemigo(self):
        for bala in self.juego.balas_enemigo[:]:
            if bala.comprobar_colision(self.juego.jugador):
                if bala in self.juego.balas_enemigo:
                    self.juego.balas_enemigo.remove(bala)
                self.juego.jugador.reducir_salud(bala.danio)
                self.juego.manejar_impacto_jugador()
                self.juego.audio_manager.reproducir_efecto("golpe")

    def _colisiones_jugador_enemigo(self):
        for enemigo in self.juego.enemigos[:]:
            # VALIDACIÓN: Si el enemigo es None, lo saltamos
            if enemigo is None:
                continue

            if self.juego.jugador.rect.colliderect(enemigo.rect):
                self.juego.colision_jugador_enemigo(enemigo)

    def _colisiones_jugador_items(self):
        for sprite in self.juego.all_sprites:
            if isinstance(sprite, Item) and self.juego.jugador.rect.colliderect(sprite.rect):
                self.juego.audio_manager.reproducir_efecto("item")
                sprite.aplicar_efecto(self.juego.jugador)
                sprite.kill()