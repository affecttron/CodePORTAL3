

import pygame
from settings import TILE_SIZE



class Tile:

    def __init__(self, grid_x, grid_y, tile_id, registry):
        self._grid_x = grid_x
        self._grid_y = grid_y
        self._tile_id = tile_id
        self._registry = registry
        self._definition = registry.get_tile(tile_id)
        self._animation_frame = 0

    def get_pixel_x(self):
        return self._grid_x * TILE_SIZE

    def get_pixel_y(self):
        return self._grid_y * TILE_SIZE

    def get_rect(self):
        return pygame.Rect(
            self.get_pixel_x(),
            self.get_pixel_y(),
            TILE_SIZE,
            TILE_SIZE
        )

    def get_grid_x(self):
        return self._grid_x

    def get_grid_y(self):
        return self._grid_y


    def is_solid(self):
        if self._definition is None:
            return False
        return self._definition.is_solid()

    def kills_player(self):
        if self._definition is None:
            return False
        return self._definition.kills_player()

    def is_portal(self):
        if self._definition is None:
            return False
        return self._definition.is_portal()

    def get_level_id(self):
        if self._definition is None:
            return 0
        return self._definition.get_level_id()

    def is_decoration(self):
        if self._definition is None:
            return False
        return self._definition.is_decoration()

    def is_climbable(self):
        if self._definition is None:
            return False
        return self._definition.is_climbable()

    def get_type(self):
        return self._tile_id

    def get_name(self):
        if self._definition is None:
            return self._tile_id
        return self._definition.get_name()


    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        # Izmantojam registry universālo zīmēšanu
        self._registry.draw_tile(screen, self._tile_id, x, y, self._animation_frame)

        # Atjauninām animāciju
        self._animation_frame += 1


    def to_dict(self):
        return {
            "type": self._tile_id,
            "x": self._grid_x,
            "y": self._grid_y
        }


class SolidTile(Tile):

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)

    def is_solid(self):
        return True


class PortalTile(Tile):

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._is_active = True
        self._is_completed = False

    def deactivate(self):
        self._is_active = False
        self._is_completed = True

    def activate(self):
        self._is_active = True

    def is_active(self):
        return self._is_active

    def is_completed(self):
        return self._is_completed

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        if self._is_active:
            # Normāli zīmējam
            self._registry.draw_tile(screen, self._tile_id, x, y, self._animation_frame)
        else:
            # Pelēks - pabeigts
            pygame.draw.rect(screen, (60, 60, 60), (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, (100, 100, 100), (x, y, TILE_SIZE, TILE_SIZE), 3)

        self._animation_frame += 1


class HazardTile(Tile):

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)

    def kills_player(self):
        # Garantējam, ka nogalina
        return True



def create_tile(tile_id, grid_x, grid_y, registry):
    # Iegūstam definīciju
    definition = registry.get_tile(tile_id)
    if definition is None:
        # Nezināms tile - parastā Tile klase
        return Tile(grid_x, grid_y, tile_id, registry)

    # Izvēlamies klasi pēc rekvizītiem
    if definition.is_portal():
        return PortalTile(grid_x, grid_y, tile_id, registry)
    elif definition.kills_player():
        return HazardTile(grid_x, grid_y, tile_id, registry)
    elif definition.is_solid():
        return SolidTile(grid_x, grid_y, tile_id, registry)
    else:
        # Dekorācijas, kāpnes, monētas, atslēgas, spawn - parastā Tile
        return Tile(grid_x, grid_y, tile_id, registry)