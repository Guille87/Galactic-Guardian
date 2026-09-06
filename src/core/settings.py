"""Constantes globales del juego.

Punto único para los números que antes estaban repartidos por varios módulos
(dimensiones de ventana, FPS, umbrales de oleada, ritmo de generación...).
Las constantes propias de una entidad concreta siguen viviendo en su clase
(`Jugador.CONFIG`, `EnemigoBase.TAMANO_ESTANDAR`, `Bala.TAMANO`, ...).
"""

# --- Ventana / bucle ---
ANCHO = 600
ALTO = 800
FPS = 60

# --- Generación de enemigos (ms entre spawns) ---
GEN_MIN_INICIAL = 800
GEN_MAX_INICIAL = 1000
GEN_MIN_SUELO = 200          # límite inferior al subir de nivel
GEN_DECREMENTO_NIVEL = 200   # cuánto baja el intervalo por nivel

# --- Fases de la oleada (ms desde el inicio del nivel) ---
TIEMPO_FASE_2 = 22000
TIEMPO_FASE_3 = 42000
TIEMPO_JEFE = 62000
TIEMPO_ESPERA_JEFE = 5000    # margen tras cambiar la música antes de que aparezca

# --- Jugador ---
JUGADOR_INVULNERABLE_MS = 3000
CONTACTO_COOLDOWN_MS = 2000  # daño por contacto cuerpo a cuerpo (por enemigo)
