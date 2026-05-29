import json
import os
import pygame
from settings import TILE_SIZE, IMAGES_FOLDER, TILES_REGISTRY_FILE


class TileDefinition:

    # Izveido flīzes definīciju no JSON datiem
    def __init__(self, data, image=None):
        self._id = data["id"]
        self._name = data.get("name", self._id)
        self._image_filename = data.get("image", "")
        self._image = image

        # ipasibas
        self._solid = data.get("solid", False)
        self._kills = data.get("kills", False)
        self._is_portal = data.get("portal", False)
        self._level_id = data.get("level_id", 0)
        self._climbable = data.get("climbable", False)
        self._decoration = data.get("decoration", False)
        self._special = data.get("special", "")
        self._door_exit = data.get("door_exit", False)
        self._background = data.get("background", False)

        # animācija
        self._frames = []
        self._frame_speed = data.get("frame_speed", 6)

        # fallback
        fc = data.get("fallback_color", [128, 128, 128])
        self._fallback_color = tuple(fc)

    # Atgriež flīzes unikālo identifikatoru
    def get_id(self):
        return self._id

    # Atgriež flīzes lasāmo nosaukumu
    def get_name(self):
        return self._name

    # Atgriež flīzes attēlu
    def get_image(self):
        return self._image

    # Vai flīzei ir ielādēts attēls
    def has_image(self):
        return self._image is not None

    # Atgriež rezerves krāsu bez attēla
    def get_fallback_color(self):
        return self._fallback_color

    # Animācija
    def set_frames(self, frames):
        self._frames = frames

    def get_frames(self):
        return self._frames

    def get_frame_speed(self):
        return self._frame_speed

    def is_animated(self):
        return bool(self._frames)

    # Vai flīze bloķē kustību
    def is_solid(self):
        return self._solid

    # Vai flīze nogalina spēlētāju
    def kills_player(self):
        return self._kills

    # Vai flīze ir portāls
    def is_portal(self):
        return self._is_portal

    # Atgriež saistītā līmeņa numuru
    def get_level_id(self):
        return self._level_id

    # Vai pa šo flīzi var rāpties
    def is_climbable(self):
        return self._climbable

    # Vai flīze ir dekoratīva
    def is_decoration(self):
        return self._decoration

    # Atgriež īpašā tipa apzīmējumu
    def get_special(self):
        return self._special

    # Vai šī ir spawn vieta
    def is_spawn(self):
        return self._special == "spawn"

    # Vai flīze ir izejas durvis
    def is_door_exit(self):
        return self._door_exit

    # Vai flīze pieder fonā
    def is_background(self):
        return self._background


class TileRegistry:

    # Izveido tukšu reģistru no konfigurācijas faila
    def __init__(self, registry_file=TILES_REGISTRY_FILE):
        self._registry_file = registry_file
        self._categories = []          # Saraksts ar kategorijām (nosaukumi)
        self._tiles_by_id = {}          # {id: TileDefinition}
        self._tiles_by_category = {}    # {category_name: [TileDefinition, ...]}
        self._loaded_images_count = 0
        self._missing_images_count = 0

    # Ielādē visas flīzes no JSON reģistra
    def load(self):
        if not os.path.exists(self._registry_file):
            print(f"Registry fails neatrasts: {self._registry_file}")
            return False


        with open(self._registry_file, "r", encoding="utf-8") as f:
            data = json.load(f)


        self._categories = []
        self._tiles_by_id = {}
        self._tiles_by_category = {}
        self._loaded_images_count = 0
        self._missing_images_count = 0

        for cat_data in data.get("categories", []):
            cat_name = cat_data["name"]
            self._categories.append(cat_name)
            self._tiles_by_category[cat_name] = []

            for tile_data in cat_data.get("tiles", []):
                image = self._try_load_image(tile_data.get("image", ""))
                tile_def = TileDefinition(tile_data, image)

                if tile_data.get("animated", False):
                    frames = self._try_load_sprite_sheet(
                        tile_data.get("sprite_sheet", ""),
                        tile_data.get("frame_count", 1),
                    )
                    tile_def.set_frames(frames)

                self._tiles_by_id[tile_def.get_id()] = tile_def
                self._tiles_by_category[cat_name].append(tile_def)

        print(f"Registry ielādēts:")
        print(f"   Kategorijas: {len(self._categories)}")
        print(f"   Tile veidi: {len(self._tiles_by_id)}")
        print(f"   Attēli ielādēti: {self._loaded_images_count}")
        print(f"   Trūkst attēlu: {self._missing_images_count} (izmantos fallback krāsu)")

        return True

    # Ielādē animācijas kadrus no sprite faila
    def _try_load_sprite_sheet(self, filename, frame_count):
        if not filename or frame_count < 1:
            return []
        full_path = os.path.join(IMAGES_FOLDER, "animated tiles", filename)
        if not os.path.exists(full_path):
            print(f"Sprite sheet nav atrasts: {full_path}")
            return []
        try:
            sheet = pygame.image.load(full_path).convert_alpha()
            sw, sh = sheet.get_width(), sheet.get_height()
            frame_w = sw // frame_count
            frames = []
            for i in range(frame_count):
                frame = pygame.Surface((frame_w, sh), pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, sh))
                if frame_w != TILE_SIZE or sh != TILE_SIZE:
                    frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                frames.append(frame)
            self._loaded_images_count += 1
            return frames
        except pygame.error as e:
            print(f"Nevarēja ielādēt sprite sheet {filename}: {e}")
            self._missing_images_count += 1
            return []

    # Mēģina ielādēt attēlu un mērogot pareizi
    def _try_load_image(self, filename):
        if not filename:
            return None

        # Pilns ceļš uz attēlu failu
        full_path = os.path.join(IMAGES_FOLDER, "tiles", filename)

        # ja nav faila
        if not os.path.exists(full_path):
            self._missing_images_count += 1
            return None

        try:
            image = pygame.image.load(full_path)
            try:
                image = image.convert_alpha()
            except pygame.error:
                pass
            if image.get_width() != TILE_SIZE or image.get_height() != TILE_SIZE:
                image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            self._loaded_images_count += 1
            return image
        except pygame.error as e:
            print(f"Nevarēja ielādēt {filename}: {e}")
            self._missing_images_count += 1
            return None

    # Atgriež flīzes definīciju pēc ID
    def get_tile(self, tile_id):
        return self._tiles_by_id.get(tile_id)

    # Pārbauda vai reģistrā ir šāda flīze
    def has_tile(self, tile_id):
        return tile_id in self._tiles_by_id

    # Atgriež visu flīžu ID sarakstu
    def get_all_tile_ids(self):
        return list(self._tiles_by_id.keys())

    # Atgriež kategoriju nosaukumu sarakstu
    def get_categories(self):
        return self._categories.copy()

    # Atgriež flīzes konkrētā kategorijā
    def get_tiles_in_category(self, category_name):
        return self._tiles_by_category.get(category_name, [])

    # Atgriež reģistrēto flīžu skaitu
    def get_tile_count(self):
        return len(self._tiles_by_id)

    # Zīmē flīzi ekrānā ar animāciju
    def draw_tile(self, screen, tile_id, x, y, animation_frame=0):
        tile_def = self.get_tile(tile_id)
        if tile_def is None:
            pygame.draw.rect(screen, (255, 0, 255), (x, y, TILE_SIZE, TILE_SIZE))
            return

        frames = tile_def.get_frames()
        if frames:
            idx = (animation_frame // tile_def.get_frame_speed()) % len(frames)
            screen.blit(frames[idx], (x, y))
        elif tile_def.has_image():
            screen.blit(tile_def.get_image(), (x, y))
        else:
            color = tile_def.get_fallback_color()
            pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))

            if tile_def.is_portal():
                pulse = abs((animation_frame % 60) - 30) / 30  # 0 līdz 1
                center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                radius = int(TILE_SIZE // 3 + pulse * 5)
                pygame.draw.circle(screen, color, center, radius, 3)
