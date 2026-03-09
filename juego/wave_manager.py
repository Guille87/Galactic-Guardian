import pygame
import random
from entidades.enemigo import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe


class WaveManager:
    def __init__(self, resource_manager, audio_manager, pantalla_ancho, pantalla_alto):
        self.rm = resource_manager
        self.am = audio_manager
        self.ancho = pantalla_ancho
        self.alto = pantalla_alto

        # Tiempos de fase (en milisegundos)
        self.TIEMPO_FASE_2 = 22000
        self.TIEMPO_FASE_3 = 42000
        self.TIEMPO_JEFE = 62000

        self.jefe_generado = False
        self.tiempo_inicio_espera_jefe = 0
        self.tiempo_espera_jefe = 5000

    def spawn_enemigo(self, tiempo_actual, balas_enemigo, jugador, nivel):
        """
        Decide y crea la instancia del enemigo correspondiente.
        Retorna la instancia del enemigo o None.
        """
        tipo_enemigo, ruta_imagen, es_jefe = self._obtener_config_enemigo(tiempo_actual)

        if not tipo_enemigo:
            return None

        # Coordenadas de aparición
        x = random.randint(50, self.ancho - 100)
        y = -50

        # Lógica de instanciación
        if es_jefe:
            x = (self.ancho - 200) // 2
            y = -150
            return Jefe(ruta_imagen, x, y, self.ancho, self.alto, balas_enemigo, jugador, nivel)

        if tipo_enemigo == EnemigoTipo1:
            return EnemigoTipo1(ruta_imagen, x, y, self.ancho, nivel)

        # Tipos 2 y 3 comparten firma de constructor
        return tipo_enemigo(ruta_imagen, x, y, self.ancho, balas_enemigo, jugador, nivel)

    def _obtener_config_enemigo(self, tiempo_actual):
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
        if self.tiempo_inicio_espera_jefe == 0:
            self.tiempo_inicio_espera_jefe = pygame.time.get_ticks()
            self.am.detener_musica("rain_of_lasers")
            self.am.reproducir_musica("deathmatch_theme")

        if pygame.time.get_ticks() - self.tiempo_inicio_espera_jefe >= self.tiempo_espera_jefe:
            self.jefe_generado = True
            return Jefe, self._get_ruta(Jefe), True

        return None, None, False