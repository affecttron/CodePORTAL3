import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

# Cik daudz tālo pilienu ir vienlaicīgi
_FAR_COUNT  = 100
# Cik daudz tuvo pilienu ir vienlaicīgi
_NEAR_COUNT = 55

# Par cik pikseļiem piliens pārvietojas pa kreisi katru kadru (slīpums)
_ANGLE = -0.35

# Tālo pilienu krāsa
_FAR_COLOR  = (60, 90, 100)
# Tuvo pilienu krāsa
_NEAR_COLOR = (90, 140, 155)


# Ģenerē jaunu pilienu ar nejaušu ātrumu, garumu un pozīciju
def _new_drop(near: bool, start: bool = False) -> list:
    # Tuvie pilieni ir ātrāki un garāki lai izskatās tuvāki spēlētājam
    speed  = random.uniform(12, 18) if near else random.uniform(6, 10)
    length = random.uniform(14, 22) if near else random.uniform(8, 13)
    # Platāks diapazons nekā ekrāns lai pilieni neparādās no malas
    x = random.uniform(-40, SCREEN_WIDTH + 40)
    # Spēles sākumā pilieni ir pa visu ekrānu, citādi parādās no augšas
    y = random.uniform(0, SCREEN_HEIGHT) if start else random.uniform(-length, 0)
    return [x, y, speed, length]


class Rain:

    # Izveido abus slāņus un aizpilda ekrānu ar pieniem uzreiz
    def __init__(self):
        self._far  = [_new_drop(near=False, start=True) for _ in range(_FAR_COUNT)]
        self._near = [_new_drop(near=True,  start=True) for _ in range(_NEAR_COUNT)]

    # Katru kadru pavieto pilienus uz leju un nedaudz pa kreisi
    def update(self):
        for drop in self._far:
            drop[1] += drop[2]           # y pieaug par ātrumu
            drop[0] += _ANGLE * drop[2]  # x mainās atbilstoši slīpumam
            if drop[1] > SCREEN_HEIGHT + 5:
                drop[:] = _new_drop(near=False)

        for drop in self._near:
            drop[1] += drop[2]
            drop[0] += _ANGLE * drop[2]
            if drop[1] > SCREEN_HEIGHT + 5:
                drop[:] = _new_drop(near=True)

    # Zīmē katru pilienu kā īsu slīpu līniju uz ekrāna
    def draw(self, surface: pygame.Surface) -> None:
        for x, y, _, length in self._far:
            x1, y1 = int(x), int(y)
            # Otrais gals nobīdīts pa slīpumu lai redzams vēja efekts
            x2 = int(x + _ANGLE * length)
            y2 = int(y + length)
            pygame.draw.line(surface, _FAR_COLOR, (x1, y1), (x2, y2), 1)

        for x, y, _, length in self._near:
            x1, y1 = int(x), int(y)
            x2 = int(x + _ANGLE * length)
            y2 = int(y + length)
            pygame.draw.line(surface, _NEAR_COLOR, (x1, y1), (x2, y2), 1)
