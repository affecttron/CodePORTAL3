import pygame
from settings import (
    TILE_SIZE,
    PLATFORM_COLOR,
    GROUND_COLOR,
    NEON_RED,
    NEON_YELLOW,
    NEON_GREEN,
    TILE_GROUND,
    TILE_PLATFORM,
    TILE_PORTAL_RED,
    TILE_PORTAL_YELLOW,
    TILE_PORTAL_GREEN,
)


class Tile:
    """Abstrakta bāzes klase visiem tile veidiem.
    Glabā pozīciju režģī un nodrošina kopīgu interfeisu."""

    def __init__(self, grid_x, grid_y, tile_type):
        # Privāti atribūti (iekapsulēšana)
        self._grid_x = grid_x      # Pozīcija režģī (tile koordinātes)
        self._grid_y = grid_y
        self._tile_type = tile_type
        self._is_solid = True       # Vai spēlētājs var stāvēt uz tā?
        self._color = (255, 255, 255)  # Pamata krāsa (pārdefinēta apakšklasēs)

    def get_pixel_x(self):
        """Pozīcija pikseļos (pasaules koordinātes)"""
        return self._grid_x * TILE_SIZE

    def get_pixel_y(self):
        """Pozīcija pikseļos (pasaules koordinātes)"""
        return self._grid_y * TILE_SIZE

    def get_rect(self):
        """Pygame Rect objekts sadursmju pārbaudei"""
        return pygame.Rect(
            self.get_pixel_x(),
            self.get_pixel_y(),
            TILE_SIZE,
            TILE_SIZE
        )

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """Virtuālā metode - tiek pārdefinēta apakšklasēs (polimorfisms!)"""
        # Pamata zīmējums - krāsains taisnstūris
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y
        pygame.draw.rect(screen, self._color, (x, y, TILE_SIZE, TILE_SIZE))

    def to_dict(self):
        """Pārvērš tile par vārdnīcu (JSON saglabāšanai)"""
        return {
            "type": self._tile_type,
            "x": self._grid_x,
            "y": self._grid_y
        }

    # Getters
    def get_grid_x(self):
        return self._grid_x

    def get_grid_y(self):
        return self._grid_y

    def get_type(self):
        return self._tile_type

    def is_solid(self):
        return self._is_solid


class Platform(Tile):
    """Statiska platforma, uz kuras spēlētājs var stāvēt.
    Var būt grīda vai lidojoša platforma."""

    def __init__(self, grid_x, grid_y, tile_type=TILE_PLATFORM):
        # Izsauc bāzes klases konstruktoru
        super().__init__(grid_x, grid_y, tile_type)

        # Krāsa atkarīga no platformas veida
        if tile_type == TILE_GROUND:
            self._color = GROUND_COLOR
        else:
            self._color = PLATFORM_COLOR

        self._is_solid = True  # Platformas ir cietas

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """Pārdefinētā draw() metode - zīmē platformu ar maliņu (polimorfisms!)"""
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        # Pamata taisnstūris
        pygame.draw.rect(screen, self._color, (x, y, TILE_SIZE, TILE_SIZE))

        # Maliņa augšā (gaišāks tonis, izskatās 3D)
        lighter = tuple(min(c + 40, 255) for c in self._color)
        pygame.draw.rect(screen, lighter, (x, y, TILE_SIZE, 6))


class Portal(Tile):
    """Portāls, kas atver uzdevumus.
    3 tipi: sarkans (if/else), dzeltens (cikli), zaļš (funkcijas)."""

    def __init__(self, grid_x, grid_y, tile_type):
        super().__init__(grid_x, grid_y, tile_type)

        self._is_solid = False  # Portāli NAV cieti - var iet cauri

        # Krāsa un līmeņa ID atkarīgs no portāla veida
        if tile_type == TILE_PORTAL_RED:
            self._color = NEON_RED
            self._level_id = 1
        elif tile_type == TILE_PORTAL_YELLOW:
            self._color = NEON_YELLOW
            self._level_id = 2
        elif tile_type == TILE_PORTAL_GREEN:
            self._color = NEON_GREEN
            self._level_id = 3
        else:
            self._color = (255, 255, 255)
            self._level_id = 0

        self._is_active = True       # Vai portāls vēl strādā?
        self._animation_frame = 0    # Animācijas kadrs (pulsēšanai)

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """Pārdefinētā draw() metode - zīmē animētu portālu (polimorfisms!)"""
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        # Centrs
        center_x = x + TILE_SIZE // 2
        center_y = y + TILE_SIZE // 2

        # Pulsācija - rādiuss mainās laika gaitā
        self._animation_frame += 0.1
        pulse = abs(pygame.math.Vector2(1, 0).rotate(self._animation_frame * 30).x) * 10
        radius_outer = TILE_SIZE // 2 - 2 + int(pulse / 2)
        radius_inner = TILE_SIZE // 4

        # Ja portāls nav aktīvs (pabeigts) - pelēks
        if not self._is_active:
            color = (80, 80, 80)
        else:
            color = self._color


        pygame.draw.circle(screen, color, (center_x, center_y), radius_outer, 3)
        pygame.draw.circle(screen, color, (center_x, center_y), radius_inner)

    def deactivate(self):
        """Izslēdz portālu (pēc tā pabeigšanas)"""
        self._is_active = False

    def get_level_id(self):
        return self._level_id

    def is_active(self):
        return self._is_active



def create_tile(tile_type, grid_x, grid_y):
    """Factory funkcija - izveido pareizu tile objektu pēc tipa.
    Šī ir profesionāla pieeja - viena vieta, kur izveidot objektus."""

    if tile_type == TILE_GROUND or tile_type == TILE_PLATFORM:
        return Platform(grid_x, grid_y, tile_type)

    elif tile_type in [TILE_PORTAL_RED, TILE_PORTAL_YELLOW, TILE_PORTAL_GREEN]:
        return Portal(grid_x, grid_y, tile_type)

    else:
        # Nezināms tips - izveidojam parastu Tile
        return Tile(grid_x, grid_y, tile_type)