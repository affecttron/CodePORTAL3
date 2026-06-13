import os

import pygame


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        print(f"[settings] ekrāna izmēru noteikšana neizdevās ({exc}), izmanto dizaina izmēru")
    return DESIGN_WIDTH, DESIGN_HEIGHT


DISPLAY_WIDTH, DISPLAY_HEIGHT = _detect_display_size()

SCREEN_WIDTH = DESIGN_WIDTH
SCREEN_HEIGHT = DESIGN_HEIGHT

FPS = 60
TITLE = "CODE Portal 3"
FULLSCREEN = True


TILE_SIZE = 64
WORLD_WIDTH_TILES = 120
WORLD_HEIGHT_TILES = 40
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE


GRAVITY = 0.8
JUMP_STRENGTH = -16
MOVE_SPEED = 6
SPRINT_SPEED = 11
MAX_FALL_SPEED = 18
CLIMB_SPEED = 5


CAMERA_SMOOTHNESS_X = 0.11
CAMERA_SMOOTHNESS_Y = 0.18
CAMERA_VERTICAL_ANCHOR = 0.56
CAMERA_LOOKAHEAD_MAX = 220
CAMERA_LOOKAHEAD_LERP = 0.04
CAMERA_MOTION_BLUR = True
CAMERA_BLUR_MIN_SPEED = 1.0
CAMERA_BLUR_ALPHA_GAIN = 9
CAMERA_BLUR_ALPHA_MAX = 85


PLAYER_WIDTH = 48
PLAYER_HEIGHT = 64
PLAYER_SPAWN_X = 100
PLAYER_SPAWN_Y = 500


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)

NEON_RED = (255, 0, 64)
NEON_YELLOW = (255, 215, 0)
NEON_GREEN = (0, 255, 65)
NEON_PINK = (255, 16, 240)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (160, 32, 240)
NEON_ORANGE = (255, 140, 0)

PORTAL_THEME_COLORS = {
    1: (255,   0,  64),
    2: (255, 215,   0),
    3: (  0, 255,  65),
    4: (  0, 255, 255),
    5: (160,  32, 240),
    6: (255, 140,   0),
    7: (255,  16, 240),
    8: ( 80,  80, 120),
    9: (255, 255, 255),
}

BACKGROUND_COLOR = (10, 10, 25)

WORLD_TINT = (101, 112, 130)
WORLD_TINT_ALPHA = 50


TIME_LIMIT_PER_TASK = 60
MAX_ATTEMPTS = 3


OVERCLOCK_DURATION_MS = 15000
OVERCLOCK_BONUS_POINTS = 10


TASKS_FILE = os.path.join(BASE_DIR, "data", "tasks.json")
SCORES_FILE = os.path.join(BASE_DIR, "data", "scores.csv")
LOG_FILE = os.path.join(BASE_DIR, "data", "log.txt")
LEVELS_FOLDER = os.path.join(BASE_DIR, "data", "levels")
TILES_REGISTRY_FILE = os.path.join(BASE_DIR, "data", "tiles_registry.json")

IMAGES_FOLDER = os.path.join(BASE_DIR, "assets", "images")
SOUNDS_FOLDER = os.path.join(BASE_DIR, "assets", "sounds")
FONTS_FOLDER = os.path.join(BASE_DIR, "assets", "fonts")

SOUND_VOLUME = 0.7
MUSIC_VOLUME = 0.3
AMBIENCE_VOLUME = 0.04
AMBIENCE_MIN_GAP_MS = 8000
AMBIENCE_MAX_GAP_MS = 25000
AMBIENCE_INITIAL_DELAY_MS = 30000


EDITOR_GRID_COLOR = (60, 60, 80)


TILE_GROUND = "ground"
TILE_PLATFORM = "platform"
TILE_PORTAL_RED = "portal_red"
TILE_PORTAL_YELLOW = "portal_yellow"
TILE_PORTAL_GREEN = "portal_green"
TILE_SPAWN = "spawn"

ALL_TILE_TYPES = [
    TILE_GROUND,
    TILE_PLATFORM,
    TILE_PORTAL_RED,
    TILE_PORTAL_YELLOW,
    TILE_PORTAL_GREEN,
    TILE_SPAWN,
]

TILE_DOOR_EXIT = "door_exit"

WORLD_LABELS = ["INITIATION", "INFILTRATION", "CORE BREACH"]

WORLD_CONFIGS = [
    {"task_count": 1, "overclock_ms": 15000, "max_attempts": 3, "level_ids": [1, 2, 3]},
    {"task_count": 2, "overclock_ms": 12000, "max_attempts": 3, "level_ids": [4, 5, 6]},
    {"task_count": 3, "overclock_ms":  9000, "max_attempts": 2, "level_ids": [7, 8, 9]},
]


def get_world_config(world_index):
    if world_index < len(WORLD_CONFIGS):
        return WORLD_CONFIGS[world_index]
    extra = world_index - len(WORLD_CONFIGS)
    return {
        "task_count":   WORLD_CONFIGS[-1]["task_count"]   + extra + 1,
        "overclock_ms": max(3000, WORLD_CONFIGS[-1]["overclock_ms"] - (extra + 1) * 1000),
        "max_attempts": 2,
        "level_ids":    [7, 8, 9],
    }
