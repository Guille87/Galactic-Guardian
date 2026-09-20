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

# --- Campaña ---
NIVEL_MAX = 5   # nº fijo de niveles; el jefe del último da la pantalla de victoria

# --- Modos de juego ---
MODO_CAMPANA = "campana"
MODO_SIN_FIN = "sin_fin"   # oleadas sin techo; la curva está en src/core/sin_fin.py

# --- Fondo ---
FONDO_VELOCIDAD_NORMAL = 0.5   # px/frame-a-60fps del scroll normal

# --- Transición de fin de nivel (al derrotar al jefe) ---
# La nave se centra en horizontal, sube recta y desaparece por arriba; el fondo
# acelera mientras tanto; unos segundos después se muestra "nivel completado".
TRANSICION_VEL_LATERAL = 6          # px/frame-a-60fps al centrarse en horizontal
TRANSICION_VEL_SUBIDA = 10          # px/frame-a-60fps al subir y desaparecer
TRANSICION_FONDO_ACELERACION = 3.0  # multiplicador máx. de velocidad del fondo al subir la nave
TRANSICION_FONDO_RAMPA_MS = 1500    # ms hasta que el fondo llega a esa velocidad máxima
TRANSICION_ESPERA_MS = 2000         # ms de espera tras desaparecer la nave, antes de la pantalla
# Margen extra (px) por encima de "desaparecida" (rect.bottom < 0): la barra de
# vida se dibuja bajo la nave, así que sin este margen se la ve un instante
# asomando por arriba de la pantalla.
TRANSICION_MARGEN_SALIDA = 40

# Fases, cadencia de aparición y jefe de cada nivel: ver src/core/niveles.py

# --- Temblor de pantalla (ver src/visual/screen_shake.py) ---
# Trauma 0..1: el desplazamiento es TEMBLOR_MAX_PX * trauma² (golpe 0.5 ≈ 3.5 px,
# perder una vida 0.85 ≈ 10 px, jefe derrotado 1.0 = 14 px). Decae solo.
TEMBLOR_MAX_PX = 14
TEMBLOR_DECAIMIENTO = 2.0   # trauma que se pierde por segundo
TEMBLOR_GOLPE = 0.5         # la nave recibe un impacto
TEMBLOR_MUERTE = 0.85       # la nave pierde una vida
TEMBLOR_JEFE = 1.0          # el jefe cae

# --- Combo de puntuación (ver src/core/combo.py) ---
# Bajas seguidas sin recibir daño para llegar a ×2, ×3, ×4 y ×5 (el último es el tope).
COMBO_UMBRALES = (10, 25, 50, 90)

# --- Progresión entre partidas (ver src/core/progresion.py y mejoras.py) ---
MONEDAS_PUNTOS = 70    # 1 moneda por cada tantos puntos de la partida (ver tools/balance.py)

# --- Curación (sin ítems que la den) ---
SIN_FIN_CURACION_OLEADA = 0.4   # fracción de la salud máxima que se recupera al cambiar de oleada

# --- Menú de opciones ---
VOLUMEN_PASO = 0.1  # cuánto sube/baja el volumen con las flechas del slider

# --- Jugador ---
JUGADOR_INVULNERABLE_MS = 3000
JUGADOR_REGEN_ESPERA_MS = 3000   # sin recibir daño durante tanto, la regeneración empieza a curar
CONTACTO_COOLDOWN_MS = 2000  # daño por contacto cuerpo a cuerpo (por enemigo)

# --- Balance de daño (números reales) ---
# Salud y daño son números reales, no "puntos": la nave tiene 50 de salud (ver
# `Jugador.CONFIG`), su bala hace 10, la del enemigo normal 10 y el cañón pesado
# del jefe 20. (Antes eran 5, 1, 1 y 2: esto es lo mismo multiplicado por 10.)
DANIO_CONTACTO = 10           # lo que pierdes al chocar con un enemigo
DANIO_EMBESTIDA = 10          # lo que pierde el enemigo en ese choque
DANIO_BALA_TIPO2 = 10
DANIO_BALA_TIPO3 = 10
DANIO_JEFE_NORMAL = 20
DANIO_JEFE_RAPIDA = 10

# Velocidad de las balas enemigas (px/frame-a-60fps)
VEL_BALA_TIPO2 = 5
VEL_BALA_TIPO3 = 6
VEL_JEFE_NORMAL = 7
VEL_JEFE_RAPIDA = 4

# (La vida y el daño de los enemigos por nivel están en `escalado.py`.)

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
