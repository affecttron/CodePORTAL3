

import math
import pygame
from settings import TILE_SIZE



class Tile:

    # Izveido tile tīkla pozīcijā ar reģistru
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

    # Atgriež x koordināti pikseļos
    def get_pixel_x(self):
        return self._grid_x * TILE_SIZE

    # Atgriež y koordināti pikseļos
    def get_pixel_y(self):
        return self._grid_y * TILE_SIZE

    # Atgriež sadursmes taisnstūri
    def get_rect(self):
        return self._rect

    # Atgriež x pozīciju tīklā
    def get_grid_x(self):
        return self._grid_x

    # Atgriež y pozīciju tīklā
    def get_grid_y(self):
        return self._grid_y

    # Vai tile bloķē kustību
    def is_solid(self):
        if self._definition is None:
            return False
        return self._definition.is_solid()

    # Vai spēlētājs mirst pieskaroties
    def kills_player(self):
        if self._definition is None:
            return False
        return self._definition.kills_player()

    # Vai šis tile ir portāls
    def is_portal(self):
        if self._definition is None:
            return False
        return self._definition.is_portal()

    # Atgriež saistītā līmeņa numuru
    def get_level_id(self):
        if self._definition is None:
            return 0
        return self._definition.get_level_id()

    # Vai tile ir tikai dekorācija
    def is_decoration(self):
        if self._definition is None:
            return False
        return self._definition.is_decoration()

    # Vai tile pieder fona slānim
    def is_background(self):
        if self._definition is None:
            return False
        return self._definition.is_background()

    # Vai pa šo tile var rāpties
    def is_climbable(self):
        if self._definition is None:
            return False
        return self._definition.is_climbable()

    # Atgriež tile tipa identifikatoru
    def get_type(self):
        return self._tile_id

    # Atgriež tile nosaukumu
    def get_name(self):
        if self._definition is None:
            return self._tile_id
        return self._definition.get_name()

    # Zīmē tile ekrānā ar animāciju
    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        x = self.get_pixel_x() - camera_offset_x
        y = self.get_pixel_y() - camera_offset_y

        # Izmantojam registry universālo zīmēšanu
        self._registry.draw_tile(screen, self._tile_id, x, y, self._animation_frame)

        # Atjauninām animāciju
        self._animation_frame += 1

    # Pārveido tile vārdnīcā saglabāšanai
    def to_dict(self):
        return {
            "type": self._tile_id,
            "x": self._grid_x,
            "y": self._grid_y
        }


class SolidTile(Tile):

    # Inicializē cieto tile
    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)

    # Ciets tile vienmēr bloķē ceļu
    def is_solid(self):
        return True


class PortalTile(Tile):

    # Inicializē portāla tile aktīvā stāvoklī
    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._is_active = True
        self._is_completed = False

    # Deaktivē portālu pēc uzdevuma pabeigšanas
    def deactivate(self):
        self._is_active = False
        self._is_completed = True

    # Aktivē portālu atkārtotai lietošanai
    def activate(self):
        self._is_active = True

    # Vai portāls pašlaik aktīvs
    def is_active(self):
        return self._is_active

    # Vai portāls jau pabeigts
    def is_completed(self):
        return self._is_completed

    # Zīmē portālu, pelēku ja pabeigts
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

    # Inicializē bīstamo tile
    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)

    # Bīstams tile vienmēr nogalina spēlētāju
    def kills_player(self):
        # Garantējam, ka nogalina
        return True


class DoorExitTile(Tile):

    # Izveido izejas durvis ar diviem tiles
    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._rect = pygame.Rect(
            grid_x * TILE_SIZE, grid_y * TILE_SIZE,
            TILE_SIZE * 2, TILE_SIZE * 2,
        )
        self._locked = True
        self._font_label = pygame.font.SysFont("bahnschrift", 14, bold=True)
        self._font_exit  = pygame.font.SysFont("bahnschrift", 28, bold=True)

    # Atslēdz durvis uz nākamo pasauli
    def unlock(self):
        self._locked = False

    # Aizslēdz durvis
    def lock(self):
        self._locked = True

    # Vai durvis pašlaik aizslēgtas
    def is_locked(self):
        return self._locked

    # Zīmē durvis ar slēgtu vai atvērtu izskatu
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
            # Vārti
            pygame.draw.rect(screen, dim_red, (x + 8,     y + 8, 12, h - 16))
            pygame.draw.rect(screen, dim_red, (x + w - 20, y + 8, 12, h - 16))
            # Piekaramā slēdzeņa arka
            cx = x + w // 2
            cy = y + h // 2
            pygame.draw.rect(screen, border_color, (cx - 12, cy - 22, 6,  20))
            pygame.draw.rect(screen, border_color, (cx +  6, cy - 22, 6,  20))
            pygame.draw.rect(screen, border_color, (cx - 12, cy - 22, 24,  6))
            # Slēdzeņa korpuss
            pygame.draw.rect(screen, border_color, (cx - 18, cy - 6, 36, 28))
            # Etiķete
            lbl = self._font_label.render("LOCKED", True, border_color)
            screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 20))
        else:
            pulse = 0.5 + 0.5 * math.sin(now / 300.0)
            g = int(200 + 55 * pulse)
            border_color = (0, g, g)
            # Skenlīniju aizpildījums
            for sy in range(y + 4, y + h - 4, 6):
                pygame.draw.line(screen, (0, 50, 50), (x + 4, sy), (x + w - 4, sy))
            # Mirgojošs teksts EXIT
            if (now // 400) % 2 == 0:
                exit_surf = self._font_exit.render("EXIT", True, (0, 255, 255))
                screen.blit(exit_surf, (
                    x + w // 2 - exit_surf.get_width() // 2,
                    y + h // 2 - exit_surf.get_height() // 2,
                ))
            # Etiķete
            lbl = self._font_label.render("-> NEXT LEVEL", True, (0, 255, 255))
            screen.blit(lbl, (x + w // 2 - lbl.get_width() // 2, y + h - 20))

        # Apmale
        pygame.draw.rect(screen, border_color, (x, y, w, h), 2)
        # Stūru akcenti
        al = 8
        for cx2, cy2, dx, dy in [
            (x,     y,     1,  1), (x + w - 1, y,     -1,  1),
            (x,     y + h - 1, 1, -1), (x + w - 1, y + h - 1, -1, -1),
        ]:
            pygame.draw.line(screen, border_color, (cx2, cy2), (cx2 + dx * al, cy2))
            pygame.draw.line(screen, border_color, (cx2, cy2), (cx2, cy2 + dy * al))


class BackgroundTile(Tile):

    _pattern_cache = {}
    _tint_surf = None   # Kopīga tumšā pārklājuma virsma

    # Izveido fona tile ar zīmēšanas virsmu
    def __init__(self, grid_x, grid_y, tile_id, registry):
        super().__init__(grid_x, grid_y, tile_id, registry)
        self._draw_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        if BackgroundTile._tint_surf is None:
            BackgroundTile._tint_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            BackgroundTile._tint_surf.fill((0, 0, 0, 90))

    # Iegūst vai izveido diagnostikas raksta virsmu
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

    # Zīmē fona tile ar tumšu pārklājumu
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


# Izveido pareizā tipa tile no definīcijas
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
        # Dekorācijas, kāpnes, monētas, atslēgas, spawn - parastā Tile
        return Tile(grid_x, grid_y, tile_id, registry)
