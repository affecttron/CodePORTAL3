import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

_FAR_COUNT  = 100
_NEAR_COUNT = 55

_ANGLE = -0.35

_FAR_COLOR  = (60, 90, 100)
_NEAR_COLOR = (90, 140, 155)


def _new_drop(near: bool, start: bool = False) -> list:
    speed  = random.uniform(12, 18) if near else random.uniform(6, 10)
    length = random.uniform(14, 22) if near else random.uniform(8, 13)
    x = random.uniform(-40, SCREEN_WIDTH + 40)
    y = random.uniform(0, SCREEN_HEIGHT) if start else random.uniform(-length, 0)
    return [x, y, speed, length]


class Rain:

    def __init__(self):
        self._far  = [_new_drop(near=False, start=True) for _ in range(_FAR_COUNT)]
        self._near = [_new_drop(near=True,  start=True) for _ in range(_NEAR_COUNT)]

    def update(self):
        for drop in self._far:
            drop[1] += drop[2]
            drop[0] += _ANGLE * drop[2]
            if drop[1] > SCREEN_HEIGHT + 5:
                drop[:] = _new_drop(near=False)

        for drop in self._near:
            drop[1] += drop[2]
            drop[0] += _ANGLE * drop[2]
            if drop[1] > SCREEN_HEIGHT + 5:
                drop[:] = _new_drop(near=True)

    def draw(self, surface: pygame.Surface) -> None:
        for x, y, _, length in self._far:
            x1, y1 = int(x), int(y)
            x2 = int(x + _ANGLE * length)
            y2 = int(y + length)
            pygame.draw.line(surface, _FAR_COLOR, (x1, y1), (x2, y2), 1)

        for x, y, _, length in self._near:
            x1, y1 = int(x), int(y)
            x2 = int(x + _ANGLE * length)
            y2 = int(y + length)
            pygame.draw.line(surface, _NEAR_COLOR, (x1, y1), (x2, y2), 1)
