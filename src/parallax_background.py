import logging
import os

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, IMAGES_FOLDER

log = logging.getLogger(__name__)


class ParallaxLayer:

    def __init__(self, image, scroll_speed, y_offset=0):
        self._image = image
        self._scroll_speed = scroll_speed
        self._y_offset = y_offset
        self._width = image.get_width()
        self._height = image.get_height()

    def draw(self, screen, camera_x, camera_y):
        offset_x = -(camera_x * self._scroll_speed) % self._width

        raw_offset_y = -(camera_y * self._scroll_speed) + self._y_offset
        min_offset_y = SCREEN_HEIGHT - self._height
        offset_y = max(min_offset_y, min(self._y_offset, raw_offset_y))

        x = offset_x - self._width
        while x < SCREEN_WIDTH:
           screen.blit(self._image, (x, offset_y))
           x += self._width


class ParallaxBackground:

    CYBERPUNK_LAYERS = (
        ("layer1_sky.png",       0.05, 1.0),
        ("layer2_stars.png",     0.15, 1.0),
        ("layer3_city_far.png",  0.3,  0.75),
        ("layer4_city_mid.png",  0.5,  0.85),
        ("layer5_city_near.png", 0.75, 0.93),
    )

    def __init__(self):
        self._layers = []
        self._sky_color = (10, 10, 25)

    def add_layer(self, image, scroll_speed, y_offset=0):
        layer = ParallaxLayer(image, scroll_speed, y_offset)
        self._layers.append(layer)
        return layer

    def add_layer_from_file(self, filename, scroll_speed, y_offset=0, scale=1.0):
        filepath = os.path.join(IMAGES_FOLDER, "backgrounds", filename)

        if not os.path.exists(filepath):
            log.warning("Slānis nav atrasts: %s", filepath)
            return None

        try:
            image = pygame.image.load(filepath).convert_alpha()
            target_h = int(SCREEN_HEIGHT * scale)
            ratio = target_h / image.get_height()
            new_width = int(image.get_width() * ratio)
            image = pygame.transform.scale(image, (new_width, target_h))

            log.info("Slānis ielādēts: %s (ātrums %s, mērogs %.0f%%)", filename, scroll_speed, scale * 100)
            return self.add_layer(image, scroll_speed, y_offset)
        except pygame.error as e:
            log.error("Kļūda ielādējot %s: %s", filename, e)
            return None

    def draw(self, screen, camera_x, camera_y):
        screen.fill(self._sky_color)
        for layer in self._layers:
            layer.draw(screen, camera_x, camera_y)

    def set_sky_color(self, color):
        self._sky_color = color

    def get_layer_count(self):
        return len(self._layers)

    def clear(self):
        self._layers.clear()

    def create_cyberpunk_scene(self):
        self.clear()
        self.set_sky_color((10, 5, 30))

        loaded_count = 0
        for filename, speed, scale in self.CYBERPUNK_LAYERS:
            if self.add_layer_from_file(filename, speed, scale=scale) is not None:
                loaded_count += 1

        if loaded_count == 0:
            log.error("Parallax: neviens fona attēls nav ielādēts no %s", IMAGES_FOLDER)
        else:
            log.info("Parallax: %d/%d slāņi ielādēti", loaded_count, len(self.CYBERPUNK_LAYERS))
