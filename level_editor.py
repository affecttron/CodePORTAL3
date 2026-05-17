import pygame
import sys
import os
from world import World
from camera import Camera
from tile_registry import TileRegistry
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, TILE_SIZE,
    EDITOR_GRID_COLOR,
    NEON_CYAN, NEON_YELLOW, WHITE, BLACK, GRAY, DARK_GRAY,
    LEVELS_FOLDER,
)



TOP_BAR_HEIGHT = 40
CATEGORY_BAR_HEIGHT = 40
TOOLBAR_HEIGHT = 140
TOTAL_UI_HEIGHT = TOP_BAR_HEIGHT + CATEGORY_BAR_HEIGHT + TOOLBAR_HEIGHT


BUTTON_SIZE = 70
BUTTON_SPACING = 8


class LevelEditor:

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CODE Portal 3 - Level Editor")
        self._clock = pygame.time.Clock()

        # Fonti
        self._font = pygame.font.SysFont("Arial", 20)
        self._font_small = pygame.font.SysFont("Arial", 14)
        self._font_big = pygame.font.SysFont("Arial", 28, bold=True)

        # Registry
        self._registry = TileRegistry()
        self._registry.load()

        # Pasaule un kamera
        self._world = World(registry=self._registry)
        self._camera = Camera()

        # Kategorijas
        self._categories = self._registry.get_categories()
        self._current_category_index = 0

        # Izvēlētais tile
        self._current_tile_id = None
        self._select_first_tile()

        # Stāvoklis
        self._running = True
        self._show_grid = True
        self._current_filename = "level_1.json"
        self._unsaved_changes = False
        self._message = ""
        self._message_timer = 0
        self._toolbar_scroll = 0  # Scroll, ja tile ir vairāk par ekrāna platumu


        self._mouse_pos = (0, 0)

    def _select_first_tile(self):
        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)
        if tiles:
            self._current_tile_id = tiles[0].get_id()


    def run(self):
        if os.path.exists(os.path.join(LEVELS_FOLDER, self._current_filename)):
            self._world.load_from_file(self._current_filename)
            self._show_message(f"Ielādēts: {self._current_filename}")
        else:
            self._show_message("Jauns līmenis")

        while self._running:
            self._handle_events()
            self._update()
            self._draw()
            self._clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # === NOTIKUMI ===
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

            if event.type == pygame.MOUSEWHEEL:
                mouse_y = pygame.mouse.get_pos()[1]
                if mouse_y >= SCREEN_HEIGHT - TOOLBAR_HEIGHT:
                    self._toolbar_scroll -= event.y * 50
                    self._clamp_scroll()

        self._handle_continuous_input()

    def _handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            self._running = False
            return

        if event.key == pygame.K_g:
            self._show_grid = not self._show_grid
            self._show_message(f"Režģis: {'ON' if self._show_grid else 'OFF'}")
            return

        if event.key == pygame.K_TAB:
            self._current_category_index = (self._current_category_index + 1) % len(self._categories)
            self._select_first_tile()
            self._toolbar_scroll = 0
            self._show_message(f"Kategorija: {self._categories[self._current_category_index]}")
            return

        ctrl_pressed = bool(event.mod & pygame.KMOD_CTRL)
        shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)

        if ctrl_pressed:
            if event.key == pygame.K_s:
                self._world.save_to_file(self._current_filename)
                self._unsaved_changes = False
                self._show_message(f"Saglabāts: {self._current_filename}")
            elif event.key == pygame.K_n:
                self._world.clear()
                self._unsaved_changes = True
                self._show_message("Jauns tukšs līmenis")
            elif event.key == pygame.K_1:
                self._switch_level("level_1.json", force=shift_pressed)
            elif event.key == pygame.K_2:
                self._switch_level("level_2.json", force=shift_pressed)
            elif event.key == pygame.K_3:
                self._switch_level("level_3.json", force=shift_pressed)

    def _handle_mouse_click(self, event):
        screen_x, screen_y = event.pos

        if screen_y < TOP_BAR_HEIGHT:
            return

        if TOP_BAR_HEIGHT <= screen_y < TOP_BAR_HEIGHT + CATEGORY_BAR_HEIGHT:
            self._handle_category_click(screen_x)
            return


        if screen_y >= SCREEN_HEIGHT - TOOLBAR_HEIGHT:
            self._handle_toolbar_click(screen_x, screen_y)
            return


        if screen_y < SCREEN_HEIGHT - TOOLBAR_HEIGHT:
            world_x, world_y = self._camera.screen_to_world(screen_x, screen_y)
            grid_x = int(world_x // TILE_SIZE)
            grid_y = int(world_y // TILE_SIZE)

            if event.button == 1:  # Kreisais - liek tile
                if self._current_tile_id:
                    self._world.add_tile(self._current_tile_id, grid_x, grid_y)
                    self._unsaved_changes = True
            elif event.button == 3:  # Labais - dzēš
                self._world.remove_tile(grid_x, grid_y)
                self._unsaved_changes = True

    def _handle_category_click(self, screen_x):
        x_offset = 20
        for i, cat_name in enumerate(self._categories):
            text_width = self._font.size(cat_name)[0] + 30
            if x_offset <= screen_x <= x_offset + text_width:
                self._current_category_index = i
                self._select_first_tile()
                self._toolbar_scroll = 0
                self._show_message(f"Kategorija: {cat_name}")
                return
            x_offset += text_width + 10

    def _handle_toolbar_click(self, screen_x, screen_y):
        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)

        x_offset = 20 - self._toolbar_scroll
        toolbar_y = SCREEN_HEIGHT - TOOLBAR_HEIGHT + 15

        for tile_def in tiles:
            if x_offset <= screen_x <= x_offset + BUTTON_SIZE and \
               toolbar_y <= screen_y <= toolbar_y + BUTTON_SIZE:
                self._current_tile_id = tile_def.get_id()
                self._show_message(f"Izvēlēts: {tile_def.get_name()}")
                return
            x_offset += BUTTON_SIZE + BUTTON_SPACING

    def _handle_continuous_input(self):
        keys = pygame.key.get_pressed()
        camera_speed = 15
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._camera.move(-camera_speed, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._camera.move(camera_speed, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._camera.move(0, -camera_speed)
        if keys[pygame.K_DOWN] or (keys[pygame.K_s] and not ctrl_pressed):
            self._camera.move(0, camera_speed)

        # ja tur peli
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_y = pygame.mouse.get_pos()[1]


        if mouse_y < SCREEN_HEIGHT - TOOLBAR_HEIGHT and mouse_y > TOP_BAR_HEIGHT + CATEGORY_BAR_HEIGHT:
            if mouse_buttons[0]:  # Kreisais
                self._paint_at_mouse(add=True)
            elif mouse_buttons[2]:  # Labais
                self._paint_at_mouse(add=False)

    def _paint_at_mouse(self, add=True):
        screen_x, screen_y = pygame.mouse.get_pos()
        world_x, world_y = self._camera.screen_to_world(screen_x, screen_y)
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        if add:
            if self._current_tile_id is None:
                return
            existing = self._world.get_tile_at(grid_x, grid_y)
            if existing is None or existing.get_type() != self._current_tile_id:
                self._world.add_tile(self._current_tile_id, grid_x, grid_y)
                self._unsaved_changes = True
        else:
            self._world.remove_tile(grid_x, grid_y)
            self._unsaved_changes = True

    def _clamp_scroll(self):
        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)
        total_width = len(tiles) * (BUTTON_SIZE + BUTTON_SPACING)
        max_scroll = max(0, total_width - SCREEN_WIDTH + 40)

        if self._toolbar_scroll < 0:
            self._toolbar_scroll = 0
        if self._toolbar_scroll > max_scroll:
            self._toolbar_scroll = max_scroll

    def _update(self):
        self._mouse_pos = pygame.mouse.get_pos()
        self._camera.update()

        if self._message_timer > 0:
            self._message_timer -= 1

    def _draw(self):
        self._screen.fill(BACKGROUND_COLOR)

        cam_x, cam_y = self._camera.get_offset()

        # Režģis
        if self._show_grid:
            self._draw_grid(cam_x, cam_y)

        # Pasaule
        self._world.draw(self._screen, cam_x, cam_y)

        # Spawn marker
        self._draw_spawn_marker(cam_x, cam_y)

        # Peles priekšskatījums
        self._draw_mouse_preview(cam_x, cam_y)

        # UI - apakšā un augšā
        self._draw_top_bar()
        self._draw_category_bar()
        self._draw_toolbar()


        if self._message_timer > 0:
            self._draw_message()

        pygame.display.flip()

    def _draw_grid(self, cam_x, cam_y):
        start_x = -(cam_x % TILE_SIZE)
        grid_bottom = SCREEN_HEIGHT - TOOLBAR_HEIGHT
        grid_top = TOP_BAR_HEIGHT + CATEGORY_BAR_HEIGHT

        for x in range(int(start_x), SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                             (x, grid_top), (x, grid_bottom), 1)


        start_y = -(cam_y % TILE_SIZE)
        for y in range(int(start_y), grid_bottom, TILE_SIZE):
            if y >= grid_top:
                pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                                 (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_spawn_marker(self, cam_x, cam_y):
        spawn_x, spawn_y = self._world.get_spawn_position()
        screen_x = spawn_x - cam_x
        screen_y = spawn_y - cam_y

        if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
            pygame.draw.line(self._screen, NEON_YELLOW,
                             (screen_x + 5, screen_y + 5),
                             (screen_x + TILE_SIZE - 5, screen_y + TILE_SIZE - 5), 3)
            pygame.draw.line(self._screen, NEON_YELLOW,
                             (screen_x + TILE_SIZE - 5, screen_y + 5),
                             (screen_x + 5, screen_y + TILE_SIZE - 5), 3)

            spawn_label = self._font_small.render("SPAWN", True, NEON_YELLOW)
            self._screen.blit(spawn_label, (screen_x, screen_y - 20))

    def _draw_mouse_preview(self, cam_x, cam_y):
        mouse_x, mouse_y = self._mouse_pos


        if mouse_y >= SCREEN_HEIGHT - TOOLBAR_HEIGHT:
            return
        if mouse_y <= TOP_BAR_HEIGHT + CATEGORY_BAR_HEIGHT:
            return
        if self._current_tile_id is None:
            return

        world_x, world_y = self._camera.screen_to_world(mouse_x, mouse_y)
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        preview_x = grid_x * TILE_SIZE - cam_x
        preview_y = grid_y * TILE_SIZE - cam_y


        tile_def = self._registry.get_tile(self._current_tile_id)
        if tile_def:
            color = tile_def.get_fallback_color()
            preview_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            preview_surface.fill((*color, 128))
            self._screen.blit(preview_surface, (preview_x, preview_y))

        # Maliņa
        pygame.draw.rect(self._screen, WHITE,
                         (preview_x, preview_y, TILE_SIZE, TILE_SIZE), 2)

        # Pozīcija
        pos_text = self._font_small.render(f"({grid_x}, {grid_y})", True, WHITE)
        self._screen.blit(pos_text, (preview_x, preview_y - 18))

    def _draw_top_bar(self):
        pygame.draw.rect(self._screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, TOP_BAR_HEIGHT), (SCREEN_WIDTH, TOP_BAR_HEIGHT), 2)

        unsaved_mark = " *" if self._unsaved_changes else ""
        current_name = ""
        if self._current_tile_id:
            tile_def = self._registry.get_tile(self._current_tile_id)
            if tile_def:
                current_name = tile_def.get_name()

        info = f"LEVEL EDITOR | Fails: {self._current_filename}{unsaved_mark} | Izvēlēts: {current_name} | Tiles: {self._world.get_tile_count()}"
        text = self._font.render(info, True, WHITE)
        self._screen.blit(text, (20, 10))

    def _draw_category_bar(self):
        y = TOP_BAR_HEIGHT
        pygame.draw.rect(self._screen, (30, 30, 50), (0, y, SCREEN_WIDTH, CATEGORY_BAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, y + CATEGORY_BAR_HEIGHT),
                         (SCREEN_WIDTH, y + CATEGORY_BAR_HEIGHT), 2)

        x_offset = 20
        for i, cat_name in enumerate(self._categories):
            text_width = self._font.size(cat_name)[0] + 30
            is_selected = (i == self._current_category_index)

            # Cilnes fons
            if is_selected:
                pygame.draw.rect(self._screen, NEON_CYAN, (x_offset - 5, y + 5, text_width, 30))
                text_color = BLACK
            else:
                pygame.draw.rect(self._screen, (50, 50, 70), (x_offset - 5, y + 5, text_width, 30))
                text_color = WHITE

            text = self._font.render(cat_name, True, text_color)
            self._screen.blit(text, (x_offset + 10, y + 12))

            x_offset += text_width + 10

    def _draw_toolbar(self):
        toolbar_y = SCREEN_HEIGHT - TOOLBAR_HEIGHT


        pygame.draw.rect(self._screen, DARK_GRAY, (0, toolbar_y, SCREEN_WIDTH, TOOLBAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, toolbar_y), (SCREEN_WIDTH, toolbar_y), 2)

        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)

        x_offset = 20 - self._toolbar_scroll

        for tile_def in tiles:
            btn_x = x_offset
            btn_y = toolbar_y + 15

            if btn_x + BUTTON_SIZE >= 0 and btn_x <= SCREEN_WIDTH:
                is_selected = (tile_def.get_id() == self._current_tile_id)
                self._registry.draw_tile(self._screen, tile_def.get_id(),
                                          btn_x, btn_y, pygame.time.get_ticks() // 16)
                border_color = NEON_CYAN if is_selected else GRAY
                border_width = 4 if is_selected else 1
                pygame.draw.rect(self._screen, border_color,
                                 (btn_x, btn_y, BUTTON_SIZE, BUTTON_SIZE), border_width)

                name_text = self._font_small.render(tile_def.get_name()[:9], True, WHITE)
                self._screen.blit(name_text, (btn_x, btn_y + BUTTON_SIZE + 4))

            x_offset += BUTTON_SIZE + BUTTON_SPACING

        controls_x = SCREEN_WIDTH - 380
        controls_y = toolbar_y + 10
        controls = [
            "MOUSE: Kreisais=likt, Labais=dzēst",
            "WASD/Bultiņas: Kamera",
            "TAB: Nākamā kategorija",
            "Ctrl+S: Saglabāt | Ctrl+N: Jauns | G: Režģis",
        ]
        for i, line in enumerate(controls):
            text = self._font_small.render(line, True, WHITE)
            self._screen.blit(text, (controls_x, controls_y + i * 18))

    def _draw_message(self):
        text = self._font_big.render(self._message, True, NEON_YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 90))

        bg_rect = text_rect.inflate(40, 20)
        pygame.draw.rect(self._screen, BLACK, bg_rect)
        pygame.draw.rect(self._screen, NEON_YELLOW, bg_rect, 2)

        self._screen.blit(text, text_rect)

    # === PALĪGI ===
    def _show_message(self, msg):
        self._message = msg
        self._message_timer = 120

    def _switch_level(self, filename, force=False):
        if self._unsaved_changes and not force:
            self._show_message("Nesaglabātas izmaiņas! Ctrl+S vai Shift+Ctrl+1/2/3 lai pārslēgtu")
            return
        self._current_filename = filename
        if os.path.exists(os.path.join(LEVELS_FOLDER, filename)):
            self._world.load_from_file(filename)
            self._show_message(f"Ielādēts: {filename}")
        else:
            self._world.clear()
            self._show_message(f"Jauns: {filename}")
        self._unsaved_changes = False


if __name__ == "__main__":
    editor = LevelEditor()
    editor.run()