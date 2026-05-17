import logging
import os
import random

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
        offset_y = -(camera_y * self._scroll_speed) + self._y_offset

        x = offset_x - self._width
        while x < SCREEN_WIDTH:
            screen.blit(self._image, (x, offset_y))
            x += self._width


class ParallaxBackground:

    # scroll_speed: 0.0 = static (far), 1.0 = locked to world (near)
    CYBERPUNK_LAYERS = (
        ("layer1_sky.png",       0.05),
        ("layer2_stars.png",     0.15),
        ("layer3_city_far.png",  0.3),
        ("layer4_city_mid.png",  0.5),
        ("layer5_city_near.png", 0.75),
    )

    def __init__(self):
        self._layers = []
        self._sky_color = (10, 10, 25)

    def add_layer(self, image, scroll_speed, y_offset=0):
        layer = ParallaxLayer(image, scroll_speed, y_offset)
        self._layers.append(layer)
        return layer

    def add_layer_from_file(self, filename, scroll_speed, y_offset=0):
        filepath = os.path.join(IMAGES_FOLDER, "backgrounds", filename)

        if not os.path.exists(filepath):
            log.warning("Slānis nav atrasts: %s", filepath)
            return None

        try:
            image = pygame.image.load(filepath)
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            if image.get_height() != SCREEN_HEIGHT:
                ratio = SCREEN_HEIGHT / image.get_height()
                new_width = int(image.get_width() * ratio)
                image = pygame.transform.scale(image, (new_width, SCREEN_HEIGHT))

            log.info("Slānis ielādēts: %s (ātrums %s)", filename, scroll_speed)
            return self.add_layer(image, scroll_speed, y_offset)
        except pygame.error as e:
            log.error("Kļūda ielādējot %s: %s", filename, e)
            return None

    def add_color_layer(self, color, scroll_speed, height_ratio=1.0):
        layer_height = int(SCREEN_HEIGHT * height_ratio)
        image = pygame.Surface((SCREEN_WIDTH * 2, layer_height), pygame.SRCALPHA)
        image.fill(color)
        y_offset = SCREEN_HEIGHT - layer_height
        return self.add_layer(image, scroll_speed, y_offset)

    def add_gradient_layer(self, color_top, color_bottom, scroll_speed):
        column = pygame.Surface((1, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            column.set_at((0, y), (r, g, b))
        image = pygame.transform.scale(column, (SCREEN_WIDTH * 2, SCREEN_HEIGHT))
        return self.add_layer(image, scroll_speed, 0)

    def add_silhouette_layer(self, color, scroll_speed, building_count=10):
        layer_width = SCREEN_WIDTH * 2
        image = pygame.Surface((layer_width, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Local RNG so we don't trample the global seed used elsewhere in the game
        rng = random.Random(int(scroll_speed * 1000))
        x = 0
        while x < layer_width:
            building_width = rng.randint(60, 150)
            building_height = rng.randint(200, 500)
            building_y = SCREEN_HEIGHT - building_height

            pygame.draw.rect(image, color, (x, building_y, building_width, building_height))

            for _ in range(rng.randint(5, 15)):
                window_x = x + rng.randint(5, building_width - 10)
                window_y = building_y + rng.randint(10, building_height - 20)
                window_color = rng.choice([
                    (255, 200, 100),
                    (255, 100, 200),
                    (100, 200, 255),
                    (100, 255, 200),
                ])
                pygame.draw.rect(image, window_color, (window_x, window_y, 4, 4))

            x += building_width + rng.randint(5, 20)

        return self.add_layer(image, scroll_speed, 0)

    def add_stars_layer(self, scroll_speed, star_count=200):
        layer_width = SCREEN_WIDTH * 2
        image = pygame.Surface((layer_width, SCREEN_HEIGHT), pygame.SRCALPHA)

        rng = random.Random(42)
        for _ in range(star_count):
            star_x = rng.randint(0, layer_width)
            star_y = rng.randint(0, SCREEN_HEIGHT // 2)
            brightness = rng.randint(100, 255)
            color = (brightness, brightness, brightness)
            size = rng.choice([1, 1, 1, 2])
            pygame.draw.rect(image, color, (star_x, star_y, size, size))

        return self.add_layer(image, scroll_speed, 0)

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
        for filename, speed in self.CYBERPUNK_LAYERS:
            if self.add_layer_from_file(filename, speed) is not None:
                loaded_count += 1

        if loaded_count == 0:
            log.warning("Neviens slānis nav ielādēts - izmanto placeholder")
            self._create_placeholder_scene()
        else:
            log.info("Parallax: %d/%d slāņi ielādēti", loaded_count, len(self.CYBERPUNK_LAYERS))

    def _create_placeholder_scene(self):
        self.add_stars_layer(scroll_speed=0.05, star_count=150)
        self.add_silhouette_layer(color=(20, 15, 40), scroll_speed=0.15)
        self.add_silhouette_layer(color=(30, 25, 55), scroll_speed=0.3)
        self.add_silhouette_layer(color=(40, 35, 70), scroll_speed=0.5)
        self.add_silhouette_layer(color=(50, 40, 80), scroll_speed=0.75)
