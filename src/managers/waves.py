import random

from src.core import settings
from src.entities.enemies import EnemigoTipo1, EnemigoTipo2, EnemigoTipo3, Jefe, EnemigoBase


class WaveManager:
    def __init__(self, resource_manager, audio_manager, pantalla_ancho, pantalla_alto):
        self.rm = resource_manager
        self.am = audio_manager
        self.ancho = pantalla_ancho
        self.alto = pantalla_alto

        # Tiempos de fase (en milisegundos)
        self.TIEMPO_FASE_2 = settings.TIEMPO_FASE_2
        self.TIEMPO_FASE_3 = settings.TIEMPO_FASE_3
        self.TIEMPO_JEFE = settings.TIEMPO_JEFE

        self.jefe_generado = False
        self.tiempo_inicio_espera_jefe = 0
        self.tiempo_espera_jefe = settings.TIEMPO_ESPERA_JEFE

    def spawn_enemigo(self, tiempo_nivel, tiempo_juego, jugador, nivel):
        """
        Decide y crea la instancia del enemigo correspondiente.

        `tiempo_nivel`: ms transcurridos en el nivel actual (para las fases).
        `tiempo_juego`: reloj de juego absoluto en ms (para la espera del jefe).
        Retorna la instancia del enemigo o None.
        """
        tipo_clase, nombre_recurso, es_jefe = self._obtener_config_enemigo(
            tiempo_nivel, tiempo_juego, nivel
        )

        if not tipo_clase:
            return None

        # Determinar el tamaño adecuado según el tipo
        tamano = Jefe.TAMANO_JEFE if es_jefe else EnemigoBase.TAMANO_ESTANDAR

        # Solicitar la imagen ya escalada y optimizada al ResourceManager
        img_final = self.rm.get_image_scaled(nombre_recurso, tamano)

        # Calcular coordenadas de aparición
        if es_jefe:
            x = (self.ancho - tamano[0]) // 2
            y = -150
        else:
            x = random.randint(50, self.ancho - 100)
            y = -50

        # Lógica de instanciación
        if es_jefe:
            return Jefe(img_final, x, y, self.ancho, self.alto, nivel, jugador)

        if tipo_clase == EnemigoTipo1:
            return EnemigoTipo1(img_final, x, y, self.ancho, nivel)

        # Tipos 2 y 3 comparten firma de constructor
        return tipo_clase(img_final, x, y, self.ancho, nivel, jugador)

    @staticmethod
    def _escala_nivel(nivel):
        """Los umbrales de fase se comprimen a niveles altos (el jefe llega antes)."""
        return max(settings.TIEMPO_ESCALA_SUELO,
                   1 - settings.TIEMPO_ESCALA_NIVEL * (nivel - 1))

    def _obtener_config_enemigo(self, tiempo_nivel, tiempo_juego, nivel):
        """
        Decide qué enemigo toca generar según el tiempo del nivel.
        Retorna (ClaseEnemigo, ruta_imagen, es_jefe)
        """
        f = self._escala_nivel(nivel)

        # Fase Jefe
        if tiempo_nivel >= self.TIEMPO_JEFE * f:
            if not self.jefe_generado:
                return self._procesar_fase_jefe(tiempo_juego)
            return None, None, False

        # Fase 3 (Mezcla de los 3 tipos)
        if tiempo_nivel >= self.TIEMPO_FASE_3 * f:
            tipo = random.choice([EnemigoTipo1, EnemigoTipo2, EnemigoTipo3])
            return tipo, self._get_ruta(tipo), False

        # Fase 2 (Tipo 1 y 2)
        if tiempo_nivel >= self.TIEMPO_FASE_2 * f:
            tipo = random.choice([EnemigoTipo1, EnemigoTipo2])
            return tipo, self._get_ruta(tipo), False

        # Fase 1 (Solo Tipo 1)
        return EnemigoTipo1, "enemigo1", False

    @staticmethod
    def _get_ruta(clase_enemigo):
        mapping = {
            EnemigoTipo1: "enemigo1",
            EnemigoTipo2: "enemigo2",
            EnemigoTipo3: "enemigo3",
            Jefe: "jefe1"
        }
        return mapping[clase_enemigo]

    def _procesar_fase_jefe(self, tiempo_juego):
        """Cambio de música y margen de espera antes de que aparezca el jefe.

        Usa el reloj de juego (se congela en pausa), no `get_ticks()`.
        """
        if self.tiempo_inicio_espera_jefe == 0:
            self.tiempo_inicio_espera_jefe = tiempo_juego
            self.am.detener_musica("rain_of_lasers")
            self.am.reproducir_musica("deathmatch_theme")

        if tiempo_juego - self.tiempo_inicio_espera_jefe >= self.tiempo_espera_jefe:
            self.jefe_generado = True
            return Jefe, "jefe1", True

        return None, None, False
