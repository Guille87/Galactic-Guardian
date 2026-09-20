import random

from src.core.niveles import definicion_nivel
from src.entities.enemies import EnemigoTipo1, Jefe, EnemigoBase


class WaveManager:
    def __init__(self, resource_manager, audio_manager, pantalla_ancho, pantalla_alto):
        self.rm = resource_manager
        self.am = audio_manager
        self.ancho = pantalla_ancho
        self.alto = pantalla_alto

        self.jefe_generado = False
        self.tiempo_inicio_espera_jefe = 0

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
            return tipo_clase(img_final, x, y, self.ancho, self.alto, nivel, jugador)

        if tipo_clase == EnemigoTipo1:
            return EnemigoTipo1(img_final, x, y, self.ancho, nivel)

        # Tipos 2 y 3 comparten firma de constructor
        return tipo_clase(img_final, x, y, self.ancho, nivel, jugador)

    def _obtener_config_enemigo(self, tiempo_nivel, tiempo_juego, nivel):
        """
        Decide qué enemigo toca generar según la definición del nivel
        (`src/core/niveles.py`) y el tiempo transcurrido en él.
        Retorna (ClaseEnemigo, nombre_recurso, es_jefe)
        """
        definicion = definicion_nivel(nivel)

        # Fase Jefe
        if tiempo_nivel >= definicion.tiempo_jefe_ms:
            if not self.jefe_generado:
                return self._procesar_fase_jefe(tiempo_juego, definicion)
            return None, None, False

        # Fases de enemigos normales: la última cuyo `desde_ms` ya se alcanzó
        fase = definicion.fases[0]
        for candidata in definicion.fases:
            if tiempo_nivel >= candidata.desde_ms:
                fase = candidata
        tipo = random.choice(fase.enemigos)
        return tipo, tipo.RECURSO, False

    def _procesar_fase_jefe(self, tiempo_juego, definicion):
        """Cambio de música y margen de espera antes de que aparezca el jefe.

        Usa el reloj de juego (se congela en pausa), no `get_ticks()`.
        """
        if self.tiempo_inicio_espera_jefe == 0:
            self.tiempo_inicio_espera_jefe = tiempo_juego
            self.am.detener_musica(definicion.musica)
            self.am.reproducir_musica(definicion.musica_jefe)

        if tiempo_juego - self.tiempo_inicio_espera_jefe >= definicion.espera_jefe_ms:
            self.jefe_generado = True
            return definicion.jefe, definicion.jefe.RECURSO, True

        return None, None, False
