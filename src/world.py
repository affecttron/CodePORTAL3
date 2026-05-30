import json
import os
import pygame
from tile import create_tile, SolidTile, PortalTile, HazardTile, DoorExitTile, BackgroundTile
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE,
    TILE_SPAWN, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    LEVELS_FOLDER,
)


class World:

    # Izveido tukšu pasauli ar reģistru
    def __init__(self, registry=None):
        self._tiles = []
        self._tile_at = {}
        self._platforms = []
        self._portals = []
        self._hazards = []
        self._climbables = []
        self._doors = []
        self._bg_tiles = []
        self._bg_tile_at = {}
        # Per-frame collision lists — rebuilt lazily, invalidated on edits.
        self._solid_rects_cache = None
        self._climbable_rects_cache = None
        self._spawn_x = PLAYER_SPAWN_X
        self._spawn_y = PLAYER_SPAWN_Y
        self._world_width = WORLD_WIDTH
        self._world_height = WORLD_HEIGHT
        self._registry = registry

    # === TILE PĀRVALDĪBA ===
    # Pievieno tile norādītā tīkla pozīcijā
    def add_tile(self, tile_type, grid_x, grid_y):
        # Spawn = tikai pozīcija
        if tile_type == TILE_SPAWN:
            self._spawn_x = grid_x * TILE_SIZE
            self._spawn_y = grid_y * TILE_SIZE
            return

        if self._registry is None:
            print(f"Nav registry - nevar pievienot '{tile_type}'")
            return

        new_tile = create_tile(tile_type, grid_x, grid_y, self._registry)

        if isinstance(new_tile, BackgroundTile):
            self.remove_bg_tile(grid_x, grid_y)
            self._bg_tiles.append(new_tile)
            self._bg_tile_at[(grid_x, grid_y)] = new_tile
            return

        # Noņemam veco šajā vietā
        self.remove_tile(grid_x, grid_y)

        self._tiles.append(new_tile)
        self._tile_at[(grid_x, grid_y)] = new_tile

        # Sadalām pa sarakstiem
        if isinstance(new_tile, SolidTile):
            self._platforms.append(new_tile)
            self._solid_rects_cache = None
        elif isinstance(new_tile, PortalTile):
            self._portals.append(new_tile)
        elif isinstance(new_tile, HazardTile):
            self._hazards.append(new_tile)
        elif isinstance(new_tile, DoorExitTile):
            self._doors.append(new_tile)
            # Register all 4 grid cells so any cell can be right-clicked to remove
            self._tile_at[(grid_x + 1, grid_y    )] = new_tile
            self._tile_at[(grid_x,     grid_y + 1)] = new_tile
            self._tile_at[(grid_x + 1, grid_y + 1)] = new_tile

        if new_tile.is_climbable():
            self._climbables.append(new_tile)
            self._climbable_rects_cache = None

    # Noņem tile no norādītās pozīcijas
    def remove_tile(self, grid_x, grid_y):
        tile_to_remove = self._tile_at.pop((grid_x, grid_y), None)
        if tile_to_remove is None:
            return

        if isinstance(tile_to_remove, DoorExitTile):
            root_gx = tile_to_remove.get_grid_x()
            root_gy = tile_to_remove.get_grid_y()
            for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                self._tile_at.pop((root_gx + dx, root_gy + dy), None)
            if tile_to_remove in self._doors:
                self._doors.remove(tile_to_remove)

        self._tiles.remove(tile_to_remove)
        if tile_to_remove in self._platforms:
            self._platforms.remove(tile_to_remove)
            self._solid_rects_cache = None
        if tile_to_remove in self._portals:
            self._portals.remove(tile_to_remove)
        if tile_to_remove in self._hazards:
            self._hazards.remove(tile_to_remove)
        if tile_to_remove in self._climbables:
            self._climbables.remove(tile_to_remove)
            self._climbable_rects_cache = None

    # Noņem fona tile no norādītās pozīcijas
    def remove_bg_tile(self, grid_x, grid_y):
        tile = self._bg_tile_at.pop((grid_x, grid_y), None)
        if tile is not None and tile in self._bg_tiles:
            self._bg_tiles.remove(tile)

    # Atgriež tile pie norādītajām koordinātēm
    def get_tile_at(self, grid_x, grid_y):
        return self._tile_at.get((grid_x, grid_y))

    # Atgriež fona tile pie norādītajām koordinātēm
    def get_bg_tile_at(self, grid_x, grid_y):
        return self._bg_tile_at.get((grid_x, grid_y))

    # Notīra visu pasauli līdz tukšumam
    def clear(self):
        self._tiles.clear()
        self._tile_at.clear()
        self._platforms.clear()
        self._portals.clear()
        self._hazards.clear()
        self._climbables.clear()
        self._doors.clear()
        self._bg_tiles.clear()
        self._bg_tile_at.clear()
        self._solid_rects_cache = None
        self._climbable_rects_cache = None

    # === ZĪMĒŠANA ===
    # Zīmē visas redzamās tiles ekrānā
    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        sw, sh = screen.get_size()
        gx_min = camera_offset_x // TILE_SIZE
        gy_min = camera_offset_y // TILE_SIZE
        gx_max = (camera_offset_x + sw) // TILE_SIZE
        gy_max = (camera_offset_y + sh) // TILE_SIZE

        for gy in range(gy_min, gy_max + 1):
            for gx in range(gx_min, gx_max + 1):
                t = self._bg_tile_at.get((gx, gy))
                if t is not None:
                    t.draw(screen, camera_offset_x, camera_offset_y)

        seen = set()
        for gy in range(gy_min, gy_max + 1):
            for gx in range(gx_min, gx_max + 1):
                t = self._tile_at.get((gx, gy))
                if t is not None and id(t) not in seen:
                    seen.add(id(t))
                    t.draw(screen, camera_offset_x, camera_offset_y)

    # === SADURSMES ===
    # Atgriež cieto tile taisnstūrus sadursmēm
    def get_solid_rects(self):
        if self._solid_rects_cache is None:
            self._solid_rects_cache = [p.get_rect() for p in self._platforms]
        return self._solid_rects_cache

    # Atgriež kāpšanas tile taisnstūrus
    def get_climbable_rects(self):
        if self._climbable_rects_cache is None:
            self._climbable_rects_cache = [c.get_rect() for c in self._climbables]
        return self._climbable_rects_cache

    # Pārbauda sadursmi ar aktīvu portālu
    def check_portal_collision(self, player_rect):
        for portal in self._portals:
            if portal.is_active() and player_rect.colliderect(portal.get_rect()):
                return portal
        return None

    # Pārbauda sadursmi ar bīstamu flīzi
    def check_hazard_collision(self, player_rect):
        for hazard in self._hazards:
            if player_rect.colliderect(hazard.get_rect()):
                return hazard
        return None

    # Pārbauda vai spēlētājs pieskaras durvīm
    def check_door_collision(self, player_rect):
        for door in self._doors:
            if player_rect.colliderect(door.get_rect()):
                return True
        return False

    # Atslēdz visas izejas durvis
    def unlock_door(self):
        for door in self._doors:
            door.unlock()

    # Aizslēdz visas izejas durvis
    def lock_doors(self):
        for door in self._doors:
            door.lock()

    # Atgriež portālu skaitu pasaulē
    def get_portal_count(self):
        return len(self._portals)

    # Atgriež durvju sarakstu
    def get_doors(self):
        return self._doors

    # === JSON SAGLABĀŠANA ===
    # Saglabā pasauli JSON failā
    def save_to_file(self, filename):
        os.makedirs(LEVELS_FOLDER, exist_ok=True)
        filepath = os.path.join(LEVELS_FOLDER, filename)

        data = {
            "spawn": {
                "x": self._spawn_x // TILE_SIZE,
                "y": self._spawn_y // TILE_SIZE
            },
            "tiles": [t.to_dict() for t in self._tiles],
            "bg_tiles": [t.to_dict() for t in self._bg_tiles],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Saglabāts: {filepath}")

    # Ielādē pasauli no JSON faila
    def load_from_file(self, filename):
        filepath = os.path.join(LEVELS_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"Fails neatrasts: {filepath}")
            return False

        self.clear()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Spawn
        if "spawn" in data:
            self._spawn_x = int(data["spawn"]["x"]) * TILE_SIZE
            self._spawn_y = int(data["spawn"]["y"]) * TILE_SIZE

        for tile_data in data.get("tiles", []):
            self.add_tile(tile_data["type"], tile_data["x"], tile_data["y"])

        for tile_data in data.get("bg_tiles", []):
            self.add_tile(tile_data["type"], tile_data["x"], tile_data["y"])

        print(f"Ielādēts: {filepath} ({len(self._tiles)} tiles, {len(self._bg_tiles)} bg tiles)")
        return True

    # === DEMO PASAULE ===
    # Izveido demonstrācijas pasauli testēšanai
    def create_demo_world(self):
        self.clear()

        if self._registry is None:
            print("Nav registry - demo netiks izveidots")
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
    # Atgriež visu tile sarakstu
    def get_tiles(self):
        return self._tiles

    # Atgriež cieto platformu sarakstu
    def get_platforms(self):
        return self._platforms

    # Atgriež portālu sarakstu
    def get_portals(self):
        return self._portals

    # Atgriež bīstamo tile sarakstu
    def get_hazards(self):
        return self._hazards

    # Atgriež spēlētāja sākuma pozīciju
    def get_spawn_position(self):
        return (self._spawn_x, self._spawn_y)

    # Atgriež pasaules izmēru pikseļos
    def get_world_size(self):
        return (self._world_width, self._world_height)

    # Atgriež kopējo tile skaitu
    def get_tile_count(self):
        return len(self._tiles) + len(self._bg_tiles)
