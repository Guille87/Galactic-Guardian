"""Constantes globales del juego.

Punto único para los números que antes estaban repartidos por varios módulos
(dimensiones de ventana, FPS, umbrales de oleada, ritmo de generación, balance).
Las constantes propias de una entidad concreta siguen viviendo en su clase
(`Jugador.CONFIG`, `EnemigoBase.TAMANO_ESTANDAR`, `Bala.TAMANO`, ...).
"""

import sys

# True al ejecutar desde el código fuente (IDE); False en un build empaquetado
# (PyInstaller pone sys.frozen). Activa ayudas de desarrollo en el HUD.
DEBUG = not getattr(sys, "frozen", False)

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
TIEMPO_FASE_2 = 20000
TIEMPO_FASE_3 = 38000
TIEMPO_JEFE = 52000
TIEMPO_ESPERA_JEFE = 5000    # margen tras cambiar la música antes de que aparezca

# Compresión de esos umbrales por nivel: en el nivel N se multiplican por
# max(TIEMPO_ESCALA_SUELO, 1 - TIEMPO_ESCALA_NIVEL * (N - 1)).
TIEMPO_ESCALA_NIVEL = 0.12
TIEMPO_ESCALA_SUELO = 0.6

# --- Menú de opciones ---
VOLUMEN_PASO = 0.1  # cuánto sube/baja el volumen con las flechas del slider

# --- Jugador ---
JUGADOR_INVULNERABLE_MS = 3000
CONTACTO_COOLDOWN_MS = 2000  # daño por contacto cuerpo a cuerpo (por enemigo)

# --- Balance de daño (en "pips" de una barra de 5) ---
# Escala legible: disparo normal = 1, cañón pesado del jefe = 2, contacto = 1.
DANIO_CONTACTO = 1
DANIO_BALA_TIPO2 = 1
DANIO_BALA_TIPO3 = 1
DANIO_JEFE_NORMAL = 2
DANIO_JEFE_RAPIDA = 1

# Velocidad de las balas enemigas (px/frame-a-60fps)
VEL_BALA_TIPO2 = 4
VEL_BALA_TIPO3 = 7
VEL_JEFE_NORMAL = 7
VEL_JEFE_RAPIDA = 4

# --- Escalado de salud por nivel (lineal, no exponencial) ---
# salud = salud_base * (1 + FACTOR * (nivel - 1))
DIFICULTAD_FACTOR_ENEMIGO = 0.5
DIFICULTAD_FACTOR_JEFE = 0.6

# --- Hitboxes circulares (radio en px). Sprites: jugador 50, enemigo 48,
#     jefe 200, bala jugador 18, bala enemiga 24. ---
RADIO_JUGADOR = 8       # pequeño y permisivo (estilo shmup)
RADIO_ENEMIGO = 20      # ~ tamaño visible
RADIO_JEFE = 95
RADIO_BALA_JUGADOR = 7
RADIO_BALA_ENEMIGO = 9

# --- Movimiento del jugador ---
# 1.0 = respuesta instantánea (comportamiento clásico). < 1.0 suaviza el
# arranque/parada (p. ej. 0.5). La diagonal siempre se normaliza.
JUGADOR_SUAVIZADO = 1.0

# --- Rebote de enemigos en los bordes laterales ---
# Velocidad horizontal mínima (px/frame-a-60fps) tras rebotar: evita que un
# enemigo con giro casi vertical se quede "pegado" a la pared.
REBOTE_MIN_VX = 1.2
