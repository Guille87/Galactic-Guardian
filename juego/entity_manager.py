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
            bala.bala_jugador()
        for bala_e in self.balas_enemigo[:]:
            bala_e.bala_enemigo()

    def _actualizar_enemigos(self):
        for enemigo in self.enemigos:
            enemigo.movimiento_enemigo()
            enemigo.update()

            # Lógica de disparo automática de enemigos
            if isinstance(enemigo, (EnemigoTipo2, EnemigoTipo3)):
                bala = enemigo.disparo_enemigo()
                if bala: self.agregar_bala_enemigo(bala)

            if isinstance(enemigo, Jefe):
                b1 = enemigo.disparo_jefe()
                b2 = enemigo.disparo_rapido()
                if b1: self.agregar_bala_enemigo(b1)
                if b2: self.agregar_bala_enemigo(b2)

    def _limpiar_entidades_fuera(self):
        """Elimina lo que sobra y actualiza contadores del juego."""
        # Filtrar enemigos que se salen
        salidos = [e for e in self.enemigos if self.juego.fuera_de_pantalla(e.rect)]
        self.juego.enemigos_activos -= len(salidos)

        self.enemigos = [e for e in self.enemigos if not self.juego.fuera_de_pantalla(e.rect)]
        self.balas = [b for b in self.balas if not self.juego.fuera_de_pantalla(b.rect)]
        self.balas_enemigo = [b for b in self.balas_enemigo if not self.juego.fuera_de_pantalla(b.rect)]

    def vaciar_todo(self):
        self.balas.clear()
        self.balas_enemigo.clear()
        self.enemigos.clear()