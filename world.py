import json
import os
import pygame
from tile import create_tile, Platform, Portal
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE,
    TILE_GROUND, TILE_PLATFORM, TILE_SPAWN,
    TILE_PORTAL_RED, TILE_PORTAL_YELLOW, TILE_PORTAL_GREEN,
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    LEVELS_FOLDER,
)


class World:
    """2D pasaules klase - tur tiles un nodrošina to apstrādi."""

    def __init__(self):
        self._tiles = []
        self._platforms = [] 
        self._portals = [] 
        self._spawn_x = PLAYER_SPAWN_X
        self._spawn_y = PLAYER_SPAWN_Y
        self._world_width = WORLD_WIDTH
        self._world_height = WORLD_HEIGHT


    def add_tile(self, tile_type, grid_x, grid_y):
        """Pievieno tile pasaulei."""
        # Ja tas ir spawn punkts - tikai saglabā pozīciju
        if tile_type == TILE_SPAWN:
            self._spawn_x = grid_x * TILE_SIZE
            self._spawn_y = grid_y * TILE_SIZE
            return

        self.remove_tile(grid_x, grid_y)

        new_tile = create_tile(tile_type, grid_x, grid_y)
        self._tiles.append(new_tile)

        if isinstance(new_tile, Platform):
            self._platforms.append(new_tile)
        elif isinstance(new_tile, Portal):
            self._portals.append(new_tile)

    def remove_tile(self, grid_x, grid_y):
        """Noņem tile pēc režģa pozīcijas."""
        # Atrodam tile šajā vietā
        tile_to_remove = None
        for t in self._tiles:
            if t.get_grid_x() == grid_x and t.get_grid_y() == grid_y:
                tile_to_remove = t
                break

        if tile_to_remove:
            self._tiles.remove(tile_to_remove)
            if tile_to_remove in self._platforms:
                self._platforms.remove(tile_to_remove)
            if tile_to_remove in self._portals:
                self._portals.remove(tile_to_remove)

    def get_tile_at(self, grid_x, grid_y):
        """Atgriež tile konkrētā pozīcijā vai None."""
        for t in self._tiles:
            if t.get_grid_x() == grid_x and t.get_grid_y() == grid_y:
                return t
        return None

    def clear(self):
        """Notīra visus tiles."""
        self._tiles.clear()
        self._platforms.clear()
        self._portals.clear()

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """Zīmē visus tiles uz ekrāna (ar kameras nobīdi)."""
        for t in self._tiles:
            tile_x = t.get_pixel_x() - camera_offset_x
            tile_y = t.get_pixel_y() - camera_offset_y

            if -TILE_SIZE <= tile_x <= screen.get_width() and \
               -TILE_SIZE <= tile_y <= screen.get_height():
                t.draw(screen, camera_offset_x, camera_offset_y)

    # coalisions

    def get_solid_rects(self):
        """Atgriež visu cieto tiles taisnstūrus (sadursmēm)."""
        return [p.get_rect() for p in self._platforms]

    def check_portal_collision(self, player_rect):
        """Pārbauda, vai spēlētājs pieskaras portālam.
        Atgriež Portal objektu vai None."""
        for portal in self._portals:
            if portal.is_active() and player_rect.colliderect(portal.get_rect()):
                return portal
        return None


    def save_to_file(self, filename):
        """Saglabā pasauli JSON failā."""
        # Pārliecināmies, ka mape eksistē
        os.makedirs(LEVELS_FOLDER, exist_ok=True)

        # Pilns ceļš
        filepath = os.path.join(LEVELS_FOLDER, filename)

        # Sagatavojam datus
        data = {
            "spawn": {
                "x": self._spawn_x // TILE_SIZE,
                "y": self._spawn_y // TILE_SIZE
            },
            "tiles": [t.to_dict() for t in self._tiles]
        }


        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Pasaule saglabāta: {filepath}")

    def load_from_file(self, filename):
        """Ielādē pasauli no JSON faila."""
        filepath = os.path.join(LEVELS_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"❌ Fails neatrasts: {filepath}")
            return False


        self.clear()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        #spawnpoint
        if "spawn" in data:
            self._spawn_x = data["spawn"]["x"] * TILE_SIZE
            self._spawn_y = data["spawn"]["y"] * TILE_SIZE

        for tile_data in data.get("tiles", []):
            self.add_tile(
                tile_data["type"],
                tile_data["x"],
                tile_data["y"]
            )

        print(f"✅ Pasaule ielādēta: {filepath} ({len(self._tiles)} tiles)")
        return True


    # DEMO PASAULE

    def create_demo_world(self):
        """Izveido vienkāršu demo pasauli ar grīdu, platformām un portāliem."""
        self.clear()

        # Grīda visā pasaules platumā (apakšējā rinda)
        for x in range(60):
            self.add_tile(TILE_GROUND, x, 16)

        # Dažas lidojošas platformas
        # 1. platformu grupa (kreisajā pusē)
        for x in range(4, 8):
            self.add_tile(TILE_PLATFORM, x, 12)

        # 2. platformu grupa (vidū)
        for x in range(12, 16):
            self.add_tile(TILE_PLATFORM, x, 10)

        # 3. platformu grupa (augstāk)
        for x in range(18, 22):
            self.add_tile(TILE_PLATFORM, x, 8)


        self.add_tile(TILE_PORTAL_RED, 8, 15)      # Sarkans (1. līmenis)
        self.add_tile(TILE_PORTAL_YELLOW, 25, 15)  # Dzeltens (2. līmenis)
        self.add_tile(TILE_PORTAL_GREEN, 40, 15)   # Zaļš (3. līmenis)

        self._spawn_x = 2 * TILE_SIZE
        self._spawn_y = 14 * TILE_SIZE


    def get_tiles(self):
        return self._tiles

    def get_platforms(self):
        return self._platforms

    def get_portals(self):
        return self._portals

    def get_spawn_position(self):
        return (self._spawn_x, self._spawn_y)

    def get_world_size(self):
        return (self._world_width, self._world_height)

    def get_tile_count(self):
        return len(self._tiles)