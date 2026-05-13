
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
FPS = 260
TITLE = "CODE Portal 3"
FULLSCREEN = True



# TILE

TILE_SIZE = 64                    # Viens tile = 64x64 pikseļi
WORLD_WIDTH_TILES = 120            # Pasaule platumā (tiles)
WORLD_HEIGHT_TILES = 17           # Pasaule augstumā (tiles)
WORLD_WIDTH = WORLD_WIDTH_TILES * TILE_SIZE     # = 3840 px
WORLD_HEIGHT = WORLD_HEIGHT_TILES * TILE_SIZE   # = 1088 px


# FIZIKA 

GRAVITY = 0.8                     # Cik ātri spēlētājs krīt
JUMP_STRENGTH = -16               # Lēciena spēks (negatīvs = uz augšu)
MOVE_SPEED = 6                    # Staigāšanas ātrums (px/kadrā)
MAX_FALL_SPEED = 18               # Maksimālais kritiena ātrums



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
NEON_PURPLE = (157, 0, 255)

# Fons
BACKGROUND_COLOR = (10, 10, 25)   
PLATFORM_COLOR = (60, 70, 90)     
GROUND_COLOR = (30, 30, 50)



# UZDEVUMU SISTĒMA
TIME_LIMIT_PER_TASK = 60          # Sekundes vienam uzdevumam
MAX_ATTEMPTS = 3                  # Mēģinājumu skaits
SPEED_BONUS_TIME = 15             # Sekundes ātruma bonusam
SPEED_BONUS_POINTS = 25


TASKS_FILE = "data/tasks.json"
SCORES_FILE = "data/scores.csv"
LOG_FILE = "data/log.txt"
LEVELS_FOLDER = "data/levels"

# Resursu mapes
IMAGES_FOLDER = "assets/images"
SOUNDS_FOLDER = "assets/sounds"
FONTS_FOLDER = "assets/fonts"



EDITOR_TOOLBAR_HEIGHT = 100
EDITOR_GRID_COLOR = (60, 60, 80)
EDITOR_HIGHLIGHT_COLOR = (255, 255, 0, 128)   # Dzeltens ar caurspīdību



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