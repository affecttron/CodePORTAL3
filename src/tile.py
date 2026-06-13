

import math
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
        self._rect = pygame.Rect(
            grid_x * TILE_SIZE, grid_y * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )

    def get_pixel_x(self):
        return self._grid_x * TILE_SIZE

    def get_pixel_y(self):
        return self._grid_y * TILE_SIZE

    def get_rect(self):
        return self._rect

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

    def is_background(self):
        if self._definition is None:
            return False
        return self._definition.is_background()

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

        self._registry.draw_tile(screen, self._tile_id, x, y, self._animation_frame)

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
            self._registry.draw_tile(screen, self._tile_id, x, y, self._animation_frame)
        else:
            pygame.draw.rect(screen, (60, 60, 60), (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, (100, 100, 100), (x, y, TILE_SIZE, TILE_SIZE), 3)

        self._animation_frame += 1


class HazardTile(Tile):

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)

    def kills_player(self):
        return True


class DoorExitTile(Tile):

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._rect = pygame.Rect(
            grid_x * TILE_SIZE, grid_y * TILE_SIZE,
            TILE_SIZE * 2, TILE_SIZE * 2,
        )
        self._locked = True
        self._font_label = pygame.font.SysFont("bahnschrift", 14, bold=True)
        self._font_exit  = pygame.font.SysFont("bahnschrift", 28, bold=True)

    def unlock(self):
        self._locked = False

    def lock(self):
        self._locked = True

    def is_locked(self):
        return self._locked

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y
        w = TILE_SIZE * 2
        h = TILE_SIZE * 2

        sw, sh = screen.get_size()
        if x + w < 0 or x > sw or y + h < 0 or y > sh:
            return

        pygame.draw.rect(screen, (10, 12, 16), (x, y, w, h))
        now = pygame.time.get_ticks()

        if self._locked:
            border_color = (255, 0, 64)
            dim_red      = (60, 0, 15)
            pygame.draw.rect(screen, dim_red, (x + 8,     y + 8, 12, h - 16))
            pygame.draw.rect(screen, dim_red, (x + w - 20, y + 8, 12, h - 16))
            cx = x + w // 2
            cy = y + h // 2
            pygame.draw.rect(screen, border_color, (cx - 12, cy - 22, 6,  20))
            pygame.draw.rect(screen, border_color, (cx +  6, cy - 22, 6,  20))
            pygame.draw.rect(screen, border_color, (cx - 12, cy - 22, 24,  6))
            pygame.draw.rect(screen, border_color, (cx - 18, cy - 6, 36, 28))
            lbl = self._font_label.render("LOCKED", True, border_color)
            screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 20))
        else:
            pulse = 0.5 + 0.5 * math.sin(now / 300.0)
            g = int(200 + 55 * pulse)
            border_color = (0, g, g)
            for sy in range(y + 4, y + h - 4, 6):
                pygame.draw.line(screen, (0, 50, 50), (x + 4, sy), (x + w - 4, sy))
            if (now // 400) % 2 == 0:
                exit_surf = self._font_exit.render("EXIT", True, (0, 255, 255))
                screen.blit(exit_surf, (
                    x + w // 2 - exit_surf.get_width() // 2,
                    y + h // 2 - exit_surf.get_height() // 2,
                ))
            lbl = self._font_label.render("-> NEXT LEVEL", True, (0, 255, 255))
            screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 20))

        pygame.draw.rect(screen, border_color, (x, y, w, h), 2)
        al = 8
        for cx2, cy2, dx, dy in [
            (x,     y,     1,  1), (x + w - 1, y,     -1,  1),
            (x,     y + h - 1, 1, -1), (x + w - 1, y + h - 1, -1, -1),
        ]:
            pygame.draw.line(screen, border_color, (cx2, cy2), (cx2 + dx * al, cy2))
            pygame.draw.line(screen, border_color, (cx2, cy2), (cx2, cy2 + dy * al))


class BackgroundTile(Tile):

    _pattern_cache = {}
    _tint_surf = None

    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._draw_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        if BackgroundTile._tint_surf is None:
            BackgroundTile._tint_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            BackgroundTile._tint_surf.fill((0, 0, 0, 90))

    def _get_pattern_surf(self):
        if self._definition is None:
            return None
        color = self._definition.get_fallback_color()
        if color in BackgroundTile._pattern_cache:
            return BackgroundTile._pattern_cache[color]

        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(color)
        r, g, b = color
        line_color = (min(r + 14, 255), min(g + 14, 255), min(b + 14, 255))
        for i in range(0, TILE_SIZE * 2, 8):
            pygame.draw.line(surf, line_color, (i, 0), (0, i))
            pygame.draw.line(surf, line_color, (i, TILE_SIZE - 1), (TILE_SIZE - 1, i - TILE_SIZE))
        BackgroundTile._pattern_cache[color] = surf
        return surf

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        sw, sh = screen.get_size()
        if x + TILE_SIZE < 0 or x > sw or y + TILE_SIZE < 0 or y > sh:
            return

        if self._definition and self._definition.has_image():
            self._draw_surf.blit(self._definition.get_image(), (0, 0))
        else:
            pat = self._get_pattern_surf()
            if pat:
                self._draw_surf.blit(pat, (0, 0))

        if BackgroundTile._tint_surf is not None:
            self._draw_surf.blit(BackgroundTile._tint_surf, (0, 0))
        screen.blit(self._draw_surf, (x, y))
        self._animation_frame += 1


def create_tile(tile_id, grid_x, grid_y, registry):
    definition = registry.get_tile(tile_id)
    if definition is None:
        return Tile(grid_x, grid_y, tile_id, registry)

    if definition.is_background():
        return BackgroundTile(grid_x, grid_y, tile_id, registry)
    elif definition.is_door_exit():
        return DoorExitTile(grid_x, grid_y, tile_id, registry)
    elif definition.is_portal():
        return PortalTile(grid_x, grid_y, tile_id, registry)
    elif definition.kills_player():
        return HazardTile(grid_x, grid_y, tile_id, registry)
    elif definition.is_solid():
        return SolidTile(grid_x, grid_y, tile_id, registry)
    else:
        return Tile(grid_x, grid_y, tile_id, registry)
