import os
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, IMAGES_FOLDER


class ParallaxLayer:
    """Viens parallax slānis."""

    def __init__(self, image, scroll_speed, y_offset=0):
        # 0.0 = nekustās (tāli), 1.0 = kustās ar pasauli (tuvi)
        self._image = image
        self._scroll_speed = scroll_speed
        self._y_offset = y_offset
        self._width = image.get_width()
        self._height = image.get_height()

    def draw(self, screen, camera_x, camera_y):
        """Zīmē slāni ar parallax efektu un atkārtošanos."""
        # Aprēķinām nobīdi
        offset_x = -(camera_x * self._scroll_speed) % self._width
        offset_y = -(camera_y * self._scroll_speed) + self._y_offset

        # Zīmējam slāni atkārtoti (lai aizpilda visu ekrānu)
        x = offset_x - self._width
        while x < SCREEN_WIDTH:
            screen.blit(self._image, (x, offset_y))
            x += self._width


class ParallaxBackground:
    """Parallax fona pārvaldnieks ar vairākiem slāņiem."""

    def __init__(self):
        self._layers = []
        self._sky_color = (10, 10, 25)  # Pamata fons, ja nav slāņu

    def add_layer(self, image, scroll_speed, y_offset=0):
        """Pievieno slāni. Slāņi tiek zīmēti secīgi (pirmais = tālākais)."""
        layer = ParallaxLayer(image, scroll_speed, y_offset)
        self._layers.append(layer)

    def add_layer_from_file(self, filename, scroll_speed, y_offset=0):
        """Mēģina ielādēt attēlu un pievienot kā slāni."""
        filepath = os.path.join(IMAGES_FOLDER, "backgrounds", filename)

        if not os.path.exists(filepath):
            print(f"⚠️ Slānis nav atrasts: {filepath}")
            return False

        try:
            image = pygame.image.load(filepath).convert_alpha()
            # Mērogojam, ja vajag
            if image.get_height() != SCREEN_HEIGHT:
                ratio = SCREEN_HEIGHT / image.get_height()
                new_width = int(image.get_width() * ratio)
                image = pygame.transform.scale(image, (new_width, SCREEN_HEIGHT))

            self.add_layer(image, scroll_speed, y_offset)
            print(f"✅ Slānis ielādēts: {filename} (ātrums {scroll_speed})")
            return True
        except pygame.error as e:
            print(f"❌ Kļūda ielādējot {filename}: {e}")
            return False

    def add_color_layer(self, color, scroll_speed, height_ratio=1.0):
        """Pievieno krāsainu slāni (placeholder, ja nav attēla)."""
        layer_height = int(SCREEN_HEIGHT * height_ratio)
        image = pygame.Surface((SCREEN_WIDTH * 2, layer_height), pygame.SRCALPHA)
        image.fill(color)
        y_offset = SCREEN_HEIGHT - layer_height
        self.add_layer(image, scroll_speed, y_offset)

    def add_gradient_layer(self, color_top, color_bottom, scroll_speed):
        """Pievieno gradient krāsu slāni (placeholder)."""
        image = pygame.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            pygame.draw.line(image, (r, g, b), (0, y), (SCREEN_WIDTH * 2, y))
        self.add_layer(image, scroll_speed, 0)

    def add_silhouette_layer(self, color, scroll_speed, building_count=10):
        """Pievieno pilsētas siluetu (placeholder dekorēšanai)."""
        import random
        layer_width = SCREEN_WIDTH * 2
        image = pygame.Surface((layer_width, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Zīmējam dažādus ēku siluetus
        random.seed(int(scroll_speed * 1000))  # Konsistenti, lai vienmēr vienāds
        x = 0
        while x < layer_width:
            building_width = random.randint(60, 150)
            building_height = random.randint(200, 500)
            building_y = SCREEN_HEIGHT - building_height

            # Galvenā ēka
            pygame.draw.rect(image, color, (x, building_y, building_width, building_height))

            # Loga gaismas (random)
            for _ in range(random.randint(5, 15)):
                window_x = x + random.randint(5, building_width - 10)
                window_y = building_y + random.randint(10, building_height - 20)
                window_color = random.choice([
                    (255, 200, 100),  # Dzeltens
                    (255, 100, 200),  # Rozā
                    (100, 200, 255),  # Zils
                    (100, 255, 200),  # Zaļš
                ])
                pygame.draw.rect(image, window_color, (window_x, window_y, 4, 4))

            x += building_width + random.randint(5, 20)

        self.add_layer(image, scroll_speed, 0)

    def add_stars_layer(self, scroll_speed, star_count=200):
        """Pievieno zvaigžņu slāni."""
        import random
        layer_width = SCREEN_WIDTH * 2
        image = pygame.Surface((layer_width, SCREEN_HEIGHT), pygame.SRCALPHA)

        random.seed(42)  # Konsistenti zvaigznes
        for _ in range(star_count):
            star_x = random.randint(0, layer_width)
            star_y = random.randint(0, SCREEN_HEIGHT // 2)
            brightness = random.randint(100, 255)
            color = (brightness, brightness, brightness)
            size = random.choice([1, 1, 1, 2])  # Lielākoties mazas
            pygame.draw.rect(image, color, (star_x, star_y, size, size))

        self.add_layer(image, scroll_speed, 0)

    def draw(self, screen, camera_x, camera_y):
        """Zīmē visus slāņus pareizajā kārtībā (no aizmugures uz priekšu)."""
        # Pamata fons
        screen.fill(self._sky_color)

        # Visi slāņi
        for layer in self._layers:
            layer.draw(screen, camera_x, camera_y)

    def set_sky_color(self, color):
        """Iestata pamata fona krāsu."""
        self._sky_color = color

    def get_layer_count(self):
        return len(self._layers)

    def clear(self):
        self._layers.clear()


    def create_cyberpunk_scene(self):
        """Izveido kiberpunka ainu no failiem (vai placeholder, ja faili nav)."""
        self.clear()
        self.set_sky_color((10, 5, 30))


        layers_config = [
            ("layer1_sky.png",       0.05),  # Vistālāk
            ("layer2_stars.png",     0.15),
            ("layer3_city_far.png",  0.3),
            ("layer4_city_mid.png",  0.5),
            ("layer5_city_near.png", 0.75),  # Tuvāk
        ]

        loaded_count = 0
        for filename, speed in layers_config:
            if self.add_layer_from_file(filename, speed):
                loaded_count += 1

        # Ja neviens slānis nav ielādēts - izmanto placeholder
        if loaded_count == 0:
            print("⚠️ Neviens slānis nav ielādēts - izmanto placeholder")
            self._create_placeholder_scene()
        else:
            print(f"✅ Parallax: {loaded_count}/{len(layers_config)} slāņi ielādēti")

    def _create_placeholder_scene(self):
        """Placeholder ar krāsainiem siluetiem (kā iepriekš)."""
        self.add_stars_layer(scroll_speed=0.05, star_count=150)
        self.add_silhouette_layer(color=(20, 15, 40), scroll_speed=0.15)
        self.add_silhouette_layer(color=(30, 25, 55), scroll_speed=0.3)
        self.add_silhouette_layer(color=(40, 35, 70), scroll_speed=0.5)
        self.add_silhouette_layer(color=(50, 40, 80), scroll_speed=0.75)