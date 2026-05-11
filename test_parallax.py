import pygame
import sys
from parallax_background import ParallaxBackground
from world import World
from player_sprite import PlayerSprite
from camera import Camera
from tile_registry import TileRegistry
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

print("=== PARALLAX FONA TESTS ===\n")

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Parallax fons - kustini un redzi efektu!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)

# Tile registry
registry = TileRegistry()
registry.load()

# Pasaule
world = World(registry=registry)
world.create_demo_world()

# Spēlētājs un kamera
spawn_x, spawn_y = world.get_spawn_position()
player = PlayerSprite(spawn_x, spawn_y)
camera = Camera()
camera.set_target(player)

# ⭐ PARALLAX!
parallax = ParallaxBackground()
parallax.create_cyberpunk_scene()
print(f"✅ Parallax ar {parallax.get_layer_count()} slāņiem!")
print()
print("VADĪBA:")
print("  A/D = staigāt (redzi parallax efektu!)")
print("  SPACE = lekt")
print("  ESC = aizvērt")

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

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.move_left()
    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.move_right()
    else:
        player.stop()

    player.update(world.get_solid_rects())
    camera.update()

    cam_x, cam_y = camera.get_offset()

    # ⭐ ZĪMĒŠANAS KĀRTĪBA - ļoti svarīgi!
    # 1. Parallax fons (vistālāk)
    parallax.draw(screen, cam_x, cam_y)

    # 2. Pasaule (tiles)
    world.draw(screen, cam_x, cam_y)

    # 3. Spēlētājs (priekšā)
    player.draw(screen, cam_x, cam_y)

    # UI
    info = font.render(f"Kamera: ({cam_x}, {cam_y}) | Parallax slāņi: {parallax.get_layer_count()}", True, (255, 255, 255))
    screen.blit(info, (20, 20))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print("✅ Tests pabeigts!")
sys.exit()