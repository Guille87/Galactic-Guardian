"""src/core/audio.py — AudioManager (música desde RAM + efectos)."""
import pygame


def test_reproducir_musica_fija_pista_actual(audio):
    audio.reproducir_musica("skyfire_theme")
    assert audio.pista_actual == "skyfire_theme"


def test_reproducir_musica_es_idempotente(audio):
    audio.reproducir_musica("skyfire_theme")
    audio.reproducir_musica("skyfire_theme")     # no debe fallar ni recargar
    assert audio.pista_actual == "skyfire_theme"


def test_cambiar_de_pista(audio):
    audio.reproducir_musica("skyfire_theme")
    audio.reproducir_musica("rain_of_lasers")
    assert audio.pista_actual == "rain_of_lasers"


def test_transicion_detener_y_reproducir(audio):
    """La secuencia real en las transiciones (jefe, Game Over): parar + poner otra."""
    audio.reproducir_musica("rain_of_lasers")
    audio.detener_musica("rain_of_lasers")
    audio.reproducir_musica("deathmatch_theme")
    assert audio.pista_actual == "deathmatch_theme"
    assert pygame.mixer.music.get_busy()


def test_detener_musica(audio):
    audio.reproducir_musica("rain_of_lasers")
    audio.detener_musica("rain_of_lasers")
    assert audio.pista_actual is None


def test_detener_toda_la_musica(audio):
    audio.reproducir_musica("rain_of_lasers")
    audio.detener_toda_la_musica()
    assert audio.pista_actual is None


def test_pista_desconocida_no_crashea(audio):
    audio.reproducir_musica("no_existe")
    assert audio.pista_actual is None


def test_volumen_efectos_se_propaga(audio):
    audio.actualizar_volumen_efectos(0.42)
    for sonido in audio.efectos.values():
        if sonido:
            assert abs(sonido.get_volume() - 0.42) < 0.05


def test_efecto_desconocido_no_crashea(audio):
    audio.reproducir_efecto("no_existe")   # sin excepción
