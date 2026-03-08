import pygame
import random
from entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe


class WaveManager:
    def __init__(self, resource_manager, pantalla_ancho, pantalla_alto):
        self.rm = resource_manager
        self.ancho = pantalla_ancho
        self.alto = pantalla_alto

        # Tiempos de fase (en milisegundos)
        self.TIEMPO_FASE_2 = 22000
        self.TIEMPO_FASE_3 = 42000
        self.TIEMPO_JEFE = 62000

        self.jefe_generado = False
        self.tiempo_inicio_espera_jefe = 0
        self.tiempo_espera_jefe = 5000

    def obtener_config_enemigo(self, tiempo_actual):
        """
        Decide qué enemigo toca generar según el tiempo.
        Retorna (ClaseEnemigo, ruta_imagen, es_jefe)
        """
        # Fase Jefe
        if tiempo_actual >= self.TIEMPO_JEFE:
            if not self.jefe_generado:
                return self._procesar_fase_jefe()
            return None, None, False

        # Fase 3 (Mezcla de los 3 tipos)
        if tiempo_actual >= self.TIEMPO_FASE_3:
            tipo = random.choice([EnemigoTipo1, EnemigoTipo2, EnemigoTipo3])
            return tipo, self._get_ruta(tipo), False

        # Fase 2 (Tipo 1 y 2)
        if tiempo_actual >= self.TIEMPO_FASE_2:
            tipo = random.choice([EnemigoTipo1, EnemigoTipo2])
            return tipo, self._get_ruta(tipo), False

        # Fase 1 (Solo Tipo 1)
        return EnemigoTipo1, self.rm.get_image_path("enemigo1"), False

    def _get_ruta(self, clase_enemigo):
        mapping = {
            EnemigoTipo1: "enemigo1",
            EnemigoTipo2: "enemigo2",
            EnemigoTipo3: "enemigo3",
            Jefe: "jefe1"
        }
        return self.rm.get_image_path(mapping[clase_enemigo])

    def _procesar_fase_jefe(self):
        """Lógica interna para el cambio de música y espera del jefe."""
        # Cambiar música (Delegamos esto al RM)
        self.rm.stop_music("rain_of_lasers")
        if not self.rm.is_music_playing("deathmatch_theme"):
            self.rm.play_music("deathmatch_theme", loops=-1)

        if self.tiempo_inicio_espera_jefe == 0:
            self.tiempo_inicio_espera_jefe = pygame.time.get_ticks()

        if pygame.time.get_ticks() - self.tiempo_inicio_espera_jefe >= self.tiempo_espera_jefe:
            self.jefe_generado = True
            return Jefe, self._get_ruta(Jefe), True

        return None, None, False