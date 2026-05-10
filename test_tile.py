import pygame
import sys
from tile import Tile, Platform, Portal, create_tile
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, TILE_SIZE,
    TILE_GROUND, TILE_PLATFORM, TILE_PORTAL_RED, TILE_PORTAL_YELLOW, TILE_PORTAL_GREEN
)

# Inicializējam pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tile sistēmas tests")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# === LOĢIKAS TESTS (drukājam terminālā) ===
print("=== TILE KLASES TESTS ===\n")

# 1. Izveidojam dažādus tiles
ground = Platform(0, 16, TILE_GROUND)
platform = Platform(5, 12, TILE_PLATFORM)
portal_r = Portal(10, 14, TILE_PORTAL_RED)
portal_y = Portal(15, 14, TILE_PORTAL_YELLOW)
portal_g = Portal(20, 14, TILE_PORTAL_GREEN)

print("--- Pamata informācija ---")
print(f"Ground:    režģī ({ground.get_grid_x()}, {ground.get_grid_y()}), pikseļos ({ground.get_pixel_x()}, {ground.get_pixel_y()})")
print(f"Platform:  režģī ({platform.get_grid_x()}, {platform.get_grid_y()}), pikseļos ({platform.get_pixel_x()}, {platform.get_pixel_y()})")
print(f"Portal R:  līmenis {portal_r.get_level_id()}, aktīvs: {portal_r.is_active()}")
print(f"Portal Y:  līmenis {portal_y.get_level_id()}, aktīvs: {portal_y.is_active()}")
print(f"Portal G:  līmenis {portal_g.get_level_id()}, aktīvs: {portal_g.is_active()}")
print()

print("--- Vai tiles ir cieti? ---")
print(f"Ground:   {ground.is_solid()}    ← jābūt True")
print(f"Platform: {platform.is_solid()}  ← jābūt True")
print(f"Portal:   {portal_r.is_solid()}  ← jābūt False (var iet cauri)")
print()

# 2. Polimorfisms - tā pati metode, dažādi rezultāti!
print("--- Polimorfisms (visi tiles vienā sarakstā) ---")
tiles = [ground, platform, portal_r, portal_y, portal_g]
for t in tiles:
    print(f"  {type(t).__name__}: tips '{t.get_type()}'")
print()

# 3. JSON eksportēšana
print("--- JSON dati (saglabāšanai) ---")
for t in tiles:
    print(f"  {t.to_dict()}")
print()

# 4. Factory funkcija
print("--- Factory funkcija ---")
test_tile = create_tile(TILE_PORTAL_RED, 5, 5)
print(f"create_tile('portal_red', 5, 5) → {type(test_tile).__name__}, līmenis: {test_tile.get_level_id()}")
print()

print("✅ LOĢIKAS TESTS PABEIGTS!\n")
print("--- VIZUĀLAIS TESTS ---")
print("Loga taustiņi:")
print("  ESC = aizvērt")
print()

# === VIZUĀLAIS TESTS (pygame logs) ===
# Izveidojam tiles, ko parādīt
demo_tiles = []

# Grīda apakšā
for x in range(30):
    demo_tiles.append(create_tile(TILE_GROUND, x, 16))

# Dažas platformas
demo_tiles.append(create_tile(TILE_PLATFORM, 5, 12))
demo_tiles.append(create_tile(TILE_PLATFORM, 6, 12))
demo_tiles.append(create_tile(TILE_PLATFORM, 12, 10))
demo_tiles.append(create_tile(TILE_PLATFORM, 13, 10))
demo_tiles.append(create_tile(TILE_PLATFORM, 20, 13))

# 3 portāli
demo_tiles.append(create_tile(TILE_PORTAL_RED, 8, 15))
demo_tiles.append(create_tile(TILE_PORTAL_YELLOW, 15, 15))
demo_tiles.append(create_tile(TILE_PORTAL_GREEN, 22, 15))

# Galvenais cikls
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Tīrām ekrānu
    screen.fill(BACKGROUND_COLOR)

    # Zīmējam visus tiles (polimorfisms - katrs zīmē sevi savādāk!)
    for t in demo_tiles:
        t.draw(screen)

    # UI tekstu uz augšu
    info = font.render("Tile sistēmas tests - ESC, lai izietu", True, (255, 255, 255))
    screen.blit(info, (20, 20))

    info2 = font.render("Polimorfisms: visi tiles vienā ciklā, bet katrs zīmē sevi savādāk!", True, (200, 200, 200))
    screen.blit(info2, (20, 50))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print("✅ Vizuālais tests pabeigts!")
sys.exit()