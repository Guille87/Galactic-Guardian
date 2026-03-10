import pygame

from entidades.enemigo import EnemigoTipo2, EnemigoTipo3, Jefe


class EntityManager:
    def __init__(self, juego):
        self.juego = juego
        self.balas = []
        self.balas_enemigo = []
        self.enemigos = []
        self.items = juego.all_sprites  # Compartimos el grupo de items/explosiones

    def agregar_enemigo(self, enemigo):
        if enemigo:
            self.enemigos.append(enemigo)

    def agregar_bala_jugador(self, bala):
        if bala:
            self.balas.append(bala)

    def agregar_bala_enemigo(self, bala):
        if bala:
            self.balas_enemigo.append(bala)

    def actualizar(self):
        """Actualiza el movimiento y lógica de todas las entidades."""
        self._actualizar_balas()
        self._actualizar_enemigos()
        self._limpiar_entidades_fuera()

    def _actualizar_balas(self):
        for bala in self.balas[:]:
            bala.update()
        for bala_e in self.balas_enemigo[:]:
            bala_e.update()

    def _actualizar_enemigos(self):
        ahora = pygame.time.get_ticks()

        for enemigo in self.enemigos:
            enemigo.movimiento_enemigo()
            enemigo.update()

            # 1. Lógica para Enemigos Tipo 2 y 3
            # Lógica de disparo automática de enemigos
            if isinstance(enemigo, (EnemigoTipo2, EnemigoTipo3)):
                # Elegimos la imagen según el tipo
                key_bala = "bala_enemigo" if isinstance(enemigo, EnemigoTipo2) else "bala_enemigo2"
                ruta_bala = self.juego.rm.get_image_path(key_bala)

                bala = enemigo.disparo_enemigo(ahora, ruta_bala)
                if bala:
                    self.agregar_bala_enemigo(bala)

            # 2. Lógica específica del Jefe
            if isinstance(enemigo, Jefe):
                # El jefe suele usar ambos tipos de bala
                ruta_normal = self.juego.rm.get_image_path("bala_enemigo2")
                ruta_rapida = self.juego.rm.get_image_path("bala_enemigo")

                b1 = enemigo.disparo_jefe(ahora, ruta_normal)
                b2 = enemigo.disparo_rapido(ahora, ruta_rapida)

                if b1: self.agregar_bala_enemigo(b1)
                if b2: self.agregar_bala_enemigo(b2)

    def _limpiar_entidades_fuera(self):
        """Elimina lo que sobra y actualiza contadores del juego."""

        def esta_fuera(rect):
            return (
                    rect.bottom < 0 or rect.top > self.juego.pantalla_alto or
                    rect.right < 0 or rect.left > self.juego.pantalla_ancho
            )

        # Filtrar enemigos que se salen
        salidos = [e for e in self.enemigos if esta_fuera(e.rect)]
        self.juego.enemigos_activos -= len(salidos)

        # Reasignar listas filtrando las que NO están fuera
        self.enemigos = [e for e in self.enemigos if not esta_fuera(e.rect)]
        self.balas = [b for b in self.balas if not esta_fuera(b.rect)]
        self.balas_enemigo = [b for b in self.balas_enemigo if not esta_fuera(b.rect)]

    def vaciar_todo(self):
        self.balas.clear()
        self.balas_enemigo.clear()
        self.enemigos.clear()