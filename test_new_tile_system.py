import pygame
import sys
from tile_registry import TileRegistry
from world import World
from player_sprite import PlayerSprite
from camera import Camera
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR

print("=== JAUNĀ TILE SISTĒMA - INTEGRĒTS TESTS ===\n")

# Inicializējam pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jaunā tile sistēma - staigā, lec, izvairies no mietiņiem!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)
big_font = pygame.font.SysFont("Arial", 48, bold=True)

# 1. Ielādējam tile registry
print("--- Ielādējam registry ---")
registry = TileRegistry()
registry.load()
print()

# 2. Izveidojam pasauli ar registry
world = World(registry=registry)

# Veidojam interesantu pasauli ar jauniem tile veidiem
# Grīda
for x in range(60):
    world.add_tile("ground", x, 16)

# Platformas
for x in range(5, 9):
    world.add_tile("platform", x, 12)
for x in range(12, 16):
    world.add_tile("platform", x, 10)
for x in range(20, 24):
    world.add_tile("platform", x, 8)

# Sienas
for y in range(10, 16):
    world.add_tile("wall", 30, y)

# ⚠️ BĪSTAMIE - mietiņi!
for x in range(18, 20):
    world.add_tile("spike", x, 15)
for x in range(33, 36):
    world.add_tile("spike", x, 15)

# Portāli
world.add_tile("portal_red", 10, 15)
world.add_tile("portal_yellow", 25, 15)
world.add_tile("portal_green", 45, 15)

# Dekorācijas
world.add_tile("neon_sign", 3, 13)
world.add_tile("monitor", 15, 9)
world.add_tile("lamp", 22, 7)
world.add_tile("crate", 27, 15)
world.add_tile("barrel", 28, 15)

# Kāpnes
for y in range(12, 16):
    world.add_tile("ladder", 40, y)

# 3. Spēlētājs un kamera
player = PlayerSprite(100, 500)
camera = Camera()
camera.set_target(player)

# Statistika
deaths = 0
portal_touches = 0

print("✅ Pasaule izveidota!")
print(f"   Tiles kopā: {world.get_tile_count()}")
print(f"   Platformas: {len(world.get_platforms())}")
print(f"   Portāli: {len(world.get_portals())}")
print(f"   Bīstamie: {len(world.get_hazards())}")
print()
print("--- VADĪBA ---")
print("  A/D = staigāt")
print("  SPACE = lekt")
print("  R = respawn")
print("  ESC = aizvērt")
print()

# Game over efekts
game_over_timer = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                player.jump()
            if event.key == pygame.K_r:
                player.respawn(100, 500)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.move_left()
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.move_right()
    else:
        player.stop()

    # Atjaunina
    player.update(world.get_solid_rects())
    camera.update()

    # Pārbauda bīstamus tiles
    hazard = world.check_hazard_collision(player.get_rect())
    if hazard and game_over_timer == 0:
        deaths += 1
        game_over_timer = 60  # 1 sekunde
        player.respawn(100, 500)

    if game_over_timer > 0:
        game_over_timer -= 1

    # Pārbauda portālus
    portal = world.check_portal_collision(player.get_rect())

    # Zīmē
    screen.fill(BACKGROUND_COLOR)
    cam_x, cam_y = camera.get_offset()
    world.draw(screen, cam_x, cam_y)
    player.draw(screen, cam_x, cam_y)

    # UI
    info = [
        f"Tiles: {world.get_tile_count()}",
        f"Nāves: {deaths}",
        f"Portāli: {len(world.get_portals())} | Bīstamie: {len(world.get_hazards())}",
    ]
    for i, line in enumerate(info):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (20, 20 + i * 28))

    # Portāla efekts
    if portal:
        msg = big_font.render(f"PORTĀLS! Līmenis {portal.get_level_id()}", True, (255, 255, 0))
        rect = msg.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(msg, rect)

    # Nāves efekts
    if game_over_timer > 30:
        msg = big_font.render("NĀVE! Mietiņi nogalina!", True, (255, 50, 50))
        rect = msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(msg, rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print(f"\n📊 Statistika: {deaths} nāves")
print("✅ Tests pabeigts!")
sys.exit()