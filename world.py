import json
import os
import pygame
from tile import create_tile, SolidTile, PortalTile, HazardTile
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE,
    TILE_SPAWN, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    LEVELS_FOLDER,
)


class World:

    def __init__(self, registry=None):
        self._tiles = []
        self._platforms = []
        self._portals = []
        self._hazards = []
        self._climbables = []
        self._spawn_x = PLAYER_SPAWN_X
        self._spawn_y = PLAYER_SPAWN_Y
        self._world_width = WORLD_WIDTH
        self._world_height = WORLD_HEIGHT
        self._registry = registry

    # === TILE PĀRVALDĪBA ===
    def add_tile(self, tile_type, grid_x, grid_y):
        # Spawn = tikai pozīcija
        if tile_type == TILE_SPAWN:
            self._spawn_x = grid_x * TILE_SIZE
            self._spawn_y = grid_y * TILE_SIZE
            return

        if self._registry is None:
            print(f"⚠️ Nav registry - nevar pievienot '{tile_type}'")
            return

        # Noņemam veco šajā vietā
        self.remove_tile(grid_x, grid_y)

        # Izveidojam jaunu
        new_tile = create_tile(tile_type, grid_x, grid_y, self._registry)
        self._tiles.append(new_tile)

        # Sadalām pa sarakstiem
        if isinstance(new_tile, SolidTile):
            self._platforms.append(new_tile)
        elif isinstance(new_tile, PortalTile):
            self._portals.append(new_tile)
        elif isinstance(new_tile, HazardTile):
            self._hazards.append(new_tile)

        if new_tile.is_climbable():
            self._climbables.append(new_tile)

    def remove_tile(self, grid_x, grid_y):
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
            if tile_to_remove in self._hazards:
                self._hazards.remove(tile_to_remove)
            if tile_to_remove in self._climbables:
                self._climbables.remove(tile_to_remove)

    def get_tile_at(self, grid_x, grid_y):
        for t in self._tiles:
            if t.get_grid_x() == grid_x and t.get_grid_y() == grid_y:
                return t
        return None

    def clear(self):
        self._tiles.clear()
        self._platforms.clear()
        self._portals.clear()
        self._hazards.clear()
        self._climbables.clear()

    # === ZĪMĒŠANA ===
    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        for t in self._tiles:
            tile_x = t.get_pixel_x() - camera_offset_x
            tile_y = t.get_pixel_y() - camera_offset_y
            # Tikai redzamos
            if -TILE_SIZE <= tile_x <= screen.get_width() and \
               -TILE_SIZE <= tile_y <= screen.get_height():
                t.draw(screen, camera_offset_x, camera_offset_y)

    # === SADURSMES ===
    def get_solid_rects(self):
        return [p.get_rect() for p in self._platforms]

    def get_climbable_rects(self):
        return [c.get_rect() for c in self._climbables]

    def check_portal_collision(self, player_rect):
        for portal in self._portals:
            if portal.is_active() and player_rect.colliderect(portal.get_rect()):
                return portal
        return None

    def check_hazard_collision(self, player_rect):
        for hazard in self._hazards:
            if player_rect.colliderect(hazard.get_rect()):
                return hazard
        return None

    # === JSON SAGLABĀŠANA ===
    def save_to_file(self, filename):
        os.makedirs(LEVELS_FOLDER, exist_ok=True)
        filepath = os.path.join(LEVELS_FOLDER, filename)

        data = {
            "spawn": {
                "x": self._spawn_x // TILE_SIZE,
                "y": self._spawn_y // TILE_SIZE
            },
            "tiles": [t.to_dict() for t in self._tiles]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Saglabāts: {filepath}")

    def load_from_file(self, filename):
        filepath = os.path.join(LEVELS_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"❌ Fails neatrasts: {filepath}")
            return False

        self.clear()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Spawn
        if "spawn" in data:
            self._spawn_x = data["spawn"]["x"] * TILE_SIZE
            self._spawn_y = data["spawn"]["y"] * TILE_SIZE

        # Tiles
        for tile_data in data.get("tiles", []):
            self.add_tile(tile_data["type"], tile_data["x"], tile_data["y"])

        print(f"✅ Ielādēts: {filepath} ({len(self._tiles)} tiles)")
        return True

    # === DEMO PASAULE ===
    def create_demo_world(self):
        self.clear()

        if self._registry is None:
            print("⚠️ Nav registry - demo netiks izveidots")
            return

        # Grīda
        for x in range(60):
            self.add_tile("ground", x, 16)

        # Platformas
        for x in range(4, 8):
            self.add_tile("platform", x, 12)
        for x in range(12, 16):
            self.add_tile("platform", x, 10)
        for x in range(18, 22):
            self.add_tile("platform", x, 8)

        # 3 portāli
        self.add_tile("portal_red", 8, 15)
        self.add_tile("portal_yellow", 25, 15)
        self.add_tile("portal_green", 40, 15)

        # Spawn
        self._spawn_x = 2 * TILE_SIZE
        self._spawn_y = 14 * TILE_SIZE

    # === GETTERS ===
    def get_tiles(self):
        return self._tiles

    def get_platforms(self):
        return self._platforms

    def get_portals(self):
        return self._portals

    def get_hazards(self):
        return self._hazards

    def get_spawn_position(self):
        return (self._spawn_x, self._spawn_y)

    def get_world_size(self):
        return (self._world_width, self._world_height)

    def get_tile_count(self):
        return len(self._tiles)