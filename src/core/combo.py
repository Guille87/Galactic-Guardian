"""Combo de puntuación (lógica pura, sin pygame).

La **racha** cuenta las bajas seguidas sin recibir daño; el **multiplicador** de
puntuación sale de ella según `settings.COMBO_UMBRALES` (×1 al principio, +1 por
cada umbral alcanzado). Solo se rompe al recibir un golpe (`romper`): no caduca
por tiempo.
"""

from src.core import settings


class Combo:
    def __init__(self, factor=1.0):
        """`factor` multiplica los umbrales de `settings.COMBO_UMBRALES` (una mejora
        permanente lo baja: `<1` = el combo sube más fácil)."""
        self.racha = 0
        self.umbrales = tuple(max(1, round(u * factor)) for u in settings.COMBO_UMBRALES)

    @property
    def multiplicador(self):
        return 1 + sum(1 for umbral in self.umbrales if self.racha >= umbral)

    @property
    def es_maximo(self):
        return self.multiplicador == 1 + len(self.umbrales)

    def progreso(self):
        """Fracción (0..1) que falta recorrer hasta el siguiente escalón; 1.0 en el máximo."""
        if self.es_maximo:
            return 1.0
        nivel = self.multiplicador - 1                       # escalones ya superados
        desde = self.umbrales[nivel - 1] if nivel else 0
        hasta = self.umbrales[nivel]
        return (self.racha - desde) / (hasta - desde)

    def sumar_baja(self):
        self.racha += 1

    def romper(self):
        self.racha = 0
