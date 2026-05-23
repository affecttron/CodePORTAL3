import os

import pygame


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Design resolution

DESIGN_WIDTH = 2560
DESIGN_HEIGHT = 1440


def _detect_display_size():
    try:
        if not pygame.display.get_init():
            pygame.display.init()
        info = pygame.display.Info()
        w, h = int(info.current_w), int(info.current_h)
        if w > 0 and h > 0:
            return w, h
    except pygame.error as exc:
        print(f"[settings] display detection failed ({exc}) — falling back to design size")
    return DESIGN_WIDTH, DESIGN_HEIGHT


DISPLAY_WIDTH, DISPLAY_HEIGHT = _detect_display_size()

# SCREEN_WIDTH/HEIGHT remain the virtual canvas size so all existing layout
# code keeps working unchanged. The display window uses DISPLAY_WIDTH/HEIGHT.
SCREEN_WIDTH = DESIGN_WIDTH
SCREEN_HEIGHT = DESIGN_HEIGHT

FPS = 60
TITLE = "CODE Portal 3"
FULLSCREEN = True



# TILE

TILE_SIZE = 64                    # Viens tile = 64x64 pikseļi
WORLD_WIDTH_TILES = 120            # Pasaule platumā (tiles)
WORLD_HEIGHT_TILES = 40           # Pasaule augstumā (tiles) — 17 spēles, atlikušais bedrēm
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE     # = 3840 px
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE   # = 2560 px


# FIZIKA 

GRAVITY = 0.8                     # Cik ātri spēlētājs krīt
JUMP_STRENGTH = -16               # Lēciena spēks (negatīvs = uz augšu)
MOVE_SPEED = 6                    # Staigāšanas ātrums (px/kadrā)
MAX_FALL_SPEED = 18               # Maksimālais kritiena ātrums
CLIMB_SPEED = 5                   # Rāpšanās ātrums pa kāpnēm (px/kadrā)


# KAMERA

CAMERA_SMOOTHNESS_X = 0.11        # Cik strauji kamera seko horizontāli (mazāks = vienmērīgāks)
CAMERA_SMOOTHNESS_Y = 0.18        # Vertikāli — nedaudz straujāks (lai redz, kur lec)
CAMERA_VERTICAL_ANCHOR = 0.56     # Spēlētāja vertikālā pozīcija ekrānā (0.5 = centrā, >0.5 = zemāk)
CAMERA_LOOKAHEAD_MAX = 220        # Cik tālu kamera "skatās uz priekšu" kustības virzienā (px)
CAMERA_LOOKAHEAD_LERP = 0.04      # Cik lēni kamera pielāgo look-ahead vērtību
CAMERA_MOTION_BLUR = True         # Vai motion-blur trail efekts ir ieslēgts
CAMERA_BLUR_MIN_SPEED = 1.0       # Zem šī kameras ātruma — bez blur
CAMERA_BLUR_ALPHA_GAIN = 9        # Cik strauji blur biezums aug ar ātrumu
CAMERA_BLUR_ALPHA_MAX = 85        # Maksimālā trail alpha



PLAYER_WIDTH = 48
PLAYER_HEIGHT = 64
PLAYER_SPAWN_X = 100              # Sākuma pozīcija X
PLAYER_SPAWN_Y = 500              # Sākuma pozīcija Y



# Pamata krāsas
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)

# neoni
NEON_RED = (255, 0, 64)           # 1. līmenis
NEON_YELLOW = (255, 215, 0)       # 2. līmenis
NEON_GREEN = (0, 255, 65)         # 3. līmenis
NEON_PINK = (255, 16, 240)
NEON_CYAN = (0, 255, 255)

# Fons
BACKGROUND_COLOR = (10, 10, 25)



# UZDEVUMU SISTĒMA
TIME_LIMIT_PER_TASK = 60          # Sekundes vienam uzdevumam
MAX_ATTEMPTS = 3                  # Mēģinājumu skaits


# OVERCLOCK — laika logs papildus punktiem par ātru izpildi
OVERCLOCK_DURATION_MS = 15000     # 15 sekundes logam (sākas pēc typewriter)
OVERCLOCK_BONUS_POINTS = 10       # Papildu punkti, ja iesniegts logā


TASKS_FILE = os.path.join(BASE_DIR, "data", "tasks.json")
SCORES_FILE = os.path.join(BASE_DIR, "data", "scores.csv")
LOG_FILE = os.path.join(BASE_DIR, "data", "log.txt")
LEVELS_FOLDER = os.path.join(BASE_DIR, "data", "levels")
TILES_REGISTRY_FILE = os.path.join(BASE_DIR, "data", "tiles_registry.json")

# Resursu mapes
IMAGES_FOLDER = os.path.join(BASE_DIR, "assets", "images")
SOUNDS_FOLDER = os.path.join(BASE_DIR, "assets", "sounds")
FONTS_FOLDER = os.path.join(BASE_DIR, "assets", "fonts")

# SKAŅA
SOUND_VOLUME = 0.7
MUSIC_VOLUME = 0.3
AMBIENCE_VOLUME = 0.04        # Fona ambient skaņas — ļoti klusas
AMBIENCE_MIN_GAP_MS = 8000        # Min pauze starp ambient skaņām
AMBIENCE_MAX_GAP_MS = 25000       # Max pauze starp ambient skaņām
AMBIENCE_INITIAL_DELAY_MS = 30000 # Pauze pirms pirmās ambient skaņas



EDITOR_GRID_COLOR = (60, 60, 80)



# TILE TIPI (izmantos JSON failos)

TILE_GROUND = "ground"
TILE_PLATFORM = "platform"
TILE_PORTAL_RED = "portal_red"
TILE_PORTAL_YELLOW = "portal_yellow"
TILE_PORTAL_GREEN = "portal_green"
TILE_SPAWN = "spawn"

#  tile tipi
ALL_TILE_TYPES = [
    TILE_GROUND,
    TILE_PLATFORM,
    TILE_PORTAL_RED,
    TILE_PORTAL_YELLOW,
    TILE_PORTAL_GREEN,
    TILE_SPAWN,
]

# EXIT DOOR
TILE_DOOR_EXIT = "door_exit"

# Pasaules Grutibas
WORLD_LABELS = ["INITIATION", "INFILTRATION", "CORE BREACH"]

WORLD_CONFIGS = [
    # world_index 0
    {"task_count": 1, "overclock_ms": 15000, "max_attempts": 3},
    # world_index 1
    {"task_count": 2, "overclock_ms": 12000, "max_attempts": 3},
    # world_index 2
    {"task_count": 3, "overclock_ms":  9000, "max_attempts": 2},
]


def get_world_config(world_index):
    if world_index < len(WORLD_CONFIGS):
        return WORLD_CONFIGS[world_index]
    extra = world_index - len(WORLD_CONFIGS)
    return {
        "task_count":   WORLD_CONFIGS[-1]["task_count"]   + extra + 1,
        "overclock_ms": max(3000, WORLD_CONFIGS[-1]["overclock_ms"] - (extra + 1) * 1000),
        "max_attempts": 2,
    }