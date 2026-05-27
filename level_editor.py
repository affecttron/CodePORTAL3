import pygame
import sys
import os
import re
from world import World
from camera import Camera
from tile_registry import TileRegistry
from shader_pipeline import ShaderPipeline
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT,
    FPS, BACKGROUND_COLOR, TILE_SIZE,
    EDITOR_GRID_COLOR,
    NEON_CYAN, NEON_YELLOW, WHITE, BLACK, GRAY, DARK_GRAY,
    LEVELS_FOLDER,
    TILE_DOOR_EXIT,
)



TOP_BAR_HEIGHT = 40
LEVEL_BAR_HEIGHT = 36
CATEGORY_BAR_HEIGHT = 40
TOOLBAR_HEIGHT = 140

HEADER_HEIGHT = TOP_BAR_HEIGHT + LEVEL_BAR_HEIGHT + CATEGORY_BAR_HEIGHT

BUTTON_SIZE = 70
BUTTON_SPACING = 8

LEVEL_FILE_RE = re.compile(r"^level_(\d+)\.json$", re.IGNORECASE)


class LevelEditor:

    def __init__(self):
        self._pipeline = ShaderPipeline.create_passthrough(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            fullscreen=False,
            display_size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
        )
        self._screen = self._pipeline.surface
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

        # Līmeņi
        self._levels = self._discover_levels()
        self._current_filename = self._levels[0] if self._levels else "level_1.json"

        # Tab rects — uzpildām katrā kadrā _draw_level_bar; vajadzīgs klikšķiem
        self._level_tab_rects = []   # [(rect, filename), ...]
        self._new_level_tab_rect = None

        # Stāvoklis
        self._running = True
        self._show_grid = True
        self._unsaved_changes = False
        self._message = ""
        self._message_timer = 0
        self._toolbar_scroll = 0  # Scroll, ja tile ir vairāk par ekrāna platumu

        self._mouse_pos = (0, 0)

        # Cached preview tile surface
        self._preview_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Pre-render all tile name labels (static text, reused every frame)
        self._tile_name_surfs = {}
        for _cat in self._registry.get_categories():
            for _td in self._registry.get_tiles_in_category(_cat):
                _tid = _td.get_id()
                if _tid not in self._tile_name_surfs:
                    self._tile_name_surfs[_tid] = self._font_small.render(
                        _td.get_name()[:9], True, WHITE
                    )

        # Pre-render static toolbar control-hint lines
        self._toolbar_ctrl_surfs = [
            self._font_small.render(line, True, WHITE) for line in [
                "MOUSE: Kreisais=likt, Labais=dzēst",
                "WASD/Bultiņas: Kamera",
                "TAB: Nākamā kategorija",
                "Ctrl+S: Saglabāt | Ctrl+N: Jauns | G: Režģis",
            ]
        ]

        # Top-bar string cache (invalidated when state changes)
        self._top_bar_surf = None
        self._top_bar_cache_key = None

    def _select_first_tile(self):
        if not self._categories:
            return
        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)
        if tiles:
            self._current_tile_id = tiles[0].get_id()

    # === LĪMEŅU PĀRVALDĪBA ===
    def _discover_levels(self):
        if not os.path.isdir(LEVELS_FOLDER):
            return []

        def sort_key(name):
            m = LEVEL_FILE_RE.match(name)
            if m:
                return (0, int(m.group(1)), name.lower())
            return (1, 0, name.lower())

        files = [f for f in os.listdir(LEVELS_FOLDER) if f.lower().endswith(".json")]
        return sorted(files, key=sort_key)

    def _next_level_filename(self):
        used = set()
        for name in self._levels:
            m = LEVEL_FILE_RE.match(name)
            if m:
                used.add(int(m.group(1)))
        n = 1
        while n in used:
            n += 1
        return f"level_{n}.json"

    def _create_new_level(self, force=False):
        if self._unsaved_changes and not force:
            self._show_message("Nesaglabātas izmaiņas! Ctrl+S vai Shift, lai radītu jaunu")
            return
        filename = self._next_level_filename()
        self._world.clear()
        self._current_filename = filename
        self._world.save_to_file(filename)  # Uzreiz saglabā, lai parādās diskā
        self._levels = self._discover_levels()
        self._unsaved_changes = False
        self._show_message(f"Izveidots jauns līmenis: {filename}")

    def _switch_level(self, filename, force=False):
        if filename == self._current_filename:
            return
        if self._unsaved_changes and not force:
            self._show_message("Nesaglabātas izmaiņas! Ctrl+S vai Shift, lai pārslēgtu")
            return
        self._current_filename = filename
        if os.path.exists(os.path.join(LEVELS_FOLDER, filename)):
            self._world.load_from_file(filename)
            self._show_message(f"Ielādēts: {filename}")
        else:
            self._world.clear()
            self._show_message(f"Jauns: {filename}")
        self._unsaved_changes = False

    def _save_current_level(self):
        self._world.save_to_file(self._current_filename)
        self._unsaved_changes = False
        if self._current_filename not in self._levels:
            self._levels = self._discover_levels()
        self._show_message(f"Saglabāts: {self._current_filename}")

    # === GALVENĀ CILPA ===
    def run(self):
        if os.path.exists(os.path.join(LEVELS_FOLDER, self._current_filename)):
            self._world.load_from_file(self._current_filename)
            self._show_message(f"Ielādēts: {self._current_filename}")
        else:
            self._show_message("Jauns līmenis")

        try:
            while self._running:
                self._handle_events()
                self._update()
                self._draw()
                self._clock.tick(FPS)
        finally:
            self._pipeline.shutdown()

    # === NOTIKUMI ===
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
            elif event.type == pygame.MOUSEWHEEL:
                mouse_y = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())[1]
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

        ctrl_pressed = bool(event.mod & pygame.KMOD_CTRL)
        shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)

        # TAB bez Ctrl — nākamā kategorija
        if event.key == pygame.K_TAB and not ctrl_pressed:
            if self._categories:
                self._current_category_index = (self._current_category_index + 1) % len(self._categories)
                self._select_first_tile()
                self._toolbar_scroll = 0
                self._show_message(f"Kategorija: {self._categories[self._current_category_index]}")
            return

        if not ctrl_pressed:
            return

        if event.key == pygame.K_s:
            self._save_current_level()
            return

        if event.key == pygame.K_n:
            self._create_new_level(force=shift_pressed)
            return

        # Ctrl+1..9 — pārslēdz uz N-to līmeni
        if pygame.K_1 <= event.key <= pygame.K_9:
            index = event.key - pygame.K_1
            if index < len(self._levels):
                self._switch_level(self._levels[index], force=shift_pressed)
            return

    def _handle_mouse_click(self, event):
        screen_x, screen_y = self._pipeline.scale_mouse_pos(event.pos)

        if screen_y < TOP_BAR_HEIGHT:
            return
        if screen_y < TOP_BAR_HEIGHT + LEVEL_BAR_HEIGHT:
            self._handle_level_click(screen_x, screen_y, event)
            return
        if screen_y < HEADER_HEIGHT:
            self._handle_category_click(screen_x)
            return
        if screen_y >= SCREEN_HEIGHT - TOOLBAR_HEIGHT:
            self._handle_toolbar_click(screen_x, screen_y)
            return

        # Pasaules apgabals — apstrādājam īsu klikšķi, kas var pazust starp kadriem.
        # Garās turēšanas un vilkšanas apstrādā _handle_continuous_input.
        if event.button == 1:
            self._paint_at_mouse(add=True)
        elif event.button == 3:
            self._paint_at_mouse(add=False)

    def _handle_level_click(self, screen_x, screen_y, event):
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        for rect, filename in self._level_tab_rects:
            if rect.collidepoint(screen_x, screen_y):
                if event.button == 1:
                    self._switch_level(filename, force=shift)
                return

        if self._new_level_tab_rect and self._new_level_tab_rect.collidepoint(screen_x, screen_y):
            if event.button == 1:
                self._create_new_level(force=shift)

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
        if not self._categories:
            return
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

        mouse_buttons = pygame.mouse.get_pressed()
        mouse_y = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())[1]

        if HEADER_HEIGHT <= mouse_y < SCREEN_HEIGHT - TOOLBAR_HEIGHT:
            if mouse_buttons[0]:
                self._paint_at_mouse(add=True)
            elif mouse_buttons[2]:
                self._paint_at_mouse(add=False)

    def _is_current_tile_bg(self):
        if self._current_tile_id is None:
            return False
        tile_def = self._registry.get_tile(self._current_tile_id)
        return tile_def is not None and tile_def.is_background()

    def _paint_at_mouse(self, add=True):
        screen_x, screen_y = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())
        world_x, world_y = self._camera.screen_to_world(screen_x, screen_y)
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        if add:
            if self._current_tile_id is None:
                return
            is_bg = self._is_current_tile_bg()
            if is_bg:
                existing = self._world.get_bg_tile_at(grid_x, grid_y)
            else:
                existing = self._world.get_tile_at(grid_x, grid_y)
            if existing is None or existing.get_type() != self._current_tile_id:
                if self._current_tile_id == TILE_DOOR_EXIT:
                    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                        self._world.remove_tile(grid_x + dx, grid_y + dy)
                self._world.add_tile(self._current_tile_id, grid_x, grid_y)
                self._unsaved_changes = True
        else:
            if self._is_current_tile_bg():
                if self._world.get_bg_tile_at(grid_x, grid_y) is not None:
                    self._world.remove_bg_tile(grid_x, grid_y)
                    self._unsaved_changes = True
            else:
                if self._world.get_tile_at(grid_x, grid_y) is not None:
                    self._world.remove_tile(grid_x, grid_y)
                    self._unsaved_changes = True

    def _clamp_scroll(self):
        if not self._categories:
            self._toolbar_scroll = 0
            return
        category = self._categories[self._current_category_index]
        tiles = self._registry.get_tiles_in_category(category)
        total_width = len(tiles) * (BUTTON_SIZE + BUTTON_SPACING)
        max_scroll = max(0, total_width - SCREEN_WIDTH + 40)
        self._toolbar_scroll = max(0, min(self._toolbar_scroll, max_scroll))

    def _update(self):
        self._mouse_pos = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())
        self._camera.update()
        if self._message_timer > 0:
            self._message_timer -= 1

    # === ZĪMĒŠANA ===
    def _draw(self):
        self._screen.fill(BACKGROUND_COLOR)

        cam_x, cam_y = self._camera.get_offset()

        if self._show_grid:
            self._draw_grid(cam_x, cam_y)

        self._world.draw(self._screen, cam_x, cam_y)
        self._draw_spawn_marker(cam_x, cam_y)
        self._draw_mouse_preview(cam_x, cam_y)

        self._draw_top_bar()
        self._draw_level_bar()
        self._draw_category_bar()
        self._draw_toolbar()

        if self._message_timer > 0:
            self._draw_message()

        self._pipeline.present()

    def _draw_grid(self, cam_x, cam_y):
        grid_bottom = SCREEN_HEIGHT - TOOLBAR_HEIGHT
        grid_top = HEADER_HEIGHT

        start_x = -(cam_x % TILE_SIZE)
        for x in range(int(start_x), SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                             (x, grid_top), (x, grid_bottom), 1)

        start_y = int(grid_top - ((cam_y + grid_top) % TILE_SIZE))
        if start_y < grid_top:
            start_y += TILE_SIZE
        for y in range(start_y, grid_bottom, TILE_SIZE):
            pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                             (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_spawn_marker(self, cam_x, cam_y):
        spawn_x, spawn_y = self._world.get_spawn_position()
        screen_x = spawn_x - cam_x
        screen_y = spawn_y - cam_y

        if not (0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT):
            return

        pygame.draw.line(self._screen, NEON_YELLOW,
                         (screen_x + 5, screen_y + 5),
                         (screen_x + TILE_SIZE - 5, screen_y + TILE_SIZE - 5), 3)
        pygame.draw.line(self._screen, NEON_YELLOW,
                         (screen_x + TILE_SIZE - 5, screen_y + 5),
                         (screen_x + 5, screen_y + TILE_SIZE - 5), 3)

        label = self._font_small.render("SPAWN", True, NEON_YELLOW)
        label_y = screen_y - 20 if screen_y >= HEADER_HEIGHT + 20 else screen_y + TILE_SIZE + 4
        self._screen.blit(label, (screen_x, label_y))

    def _draw_mouse_preview(self, cam_x, cam_y):
        mouse_x, mouse_y = self._mouse_pos

        if not (HEADER_HEIGHT <= mouse_y < SCREEN_HEIGHT - TOOLBAR_HEIGHT):
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
            self._preview_surf.fill((*color, 128))
            self._screen.blit(self._preview_surf, (preview_x, preview_y))

        pygame.draw.rect(self._screen, WHITE,
                         (preview_x, preview_y, TILE_SIZE, TILE_SIZE), 2)

        pos_text = self._font_small.render(f"({grid_x}, {grid_y})", True, WHITE)
        self._screen.blit(pos_text, (preview_x, preview_y - 18))

    def _draw_top_bar(self):
        pygame.draw.rect(self._screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, TOP_BAR_HEIGHT), (SCREEN_WIDTH, TOP_BAR_HEIGHT), 2)

        current_name = ""
        if self._current_tile_id:
            tile_def = self._registry.get_tile(self._current_tile_id)
            if tile_def:
                current_name = tile_def.get_name()

        tile_count = self._world.get_tile_count()
        cache_key = (self._unsaved_changes, self._current_filename, self._current_tile_id, tile_count)
        if self._top_bar_cache_key != cache_key:
            unsaved_mark = " *" if self._unsaved_changes else ""
            info = f"LEVEL EDITOR | Fails: {self._current_filename}{unsaved_mark} | Izvēlēts: {current_name} | Tiles: {tile_count}"
            self._top_bar_surf = self._font.render(info, True, WHITE)
            self._top_bar_cache_key = cache_key
        self._screen.blit(self._top_bar_surf, (20, 10))

    def _draw_level_bar(self):
        y = TOP_BAR_HEIGHT
        pygame.draw.rect(self._screen, (20, 20, 35), (0, y, SCREEN_WIDTH, LEVEL_BAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, y + LEVEL_BAR_HEIGHT),
                         (SCREEN_WIDTH, y + LEVEL_BAR_HEIGHT), 1)

        label = self._font_small.render("LĪMEŅI:", True, GRAY)
        self._screen.blit(label, (10, y + 11))

        self._level_tab_rects = []
        x_offset = 80

        for filename in self._levels:
            is_selected = (filename == self._current_filename)
            display = filename[:-5] if filename.lower().endswith(".json") else filename
            if is_selected and self._unsaved_changes:
                display += " *"
            text_width = self._font_small.size(display)[0] + 20
            rect = pygame.Rect(x_offset, y + 5, text_width, LEVEL_BAR_HEIGHT - 10)

            if is_selected:
                pygame.draw.rect(self._screen, NEON_CYAN, rect)
                text_color = BLACK
            else:
                pygame.draw.rect(self._screen, (45, 45, 65), rect)
                text_color = WHITE
            pygame.draw.rect(self._screen, GRAY, rect, 1)

            text = self._font_small.render(display, True, text_color)
            self._screen.blit(text, (rect.x + 10, rect.y + 6))

            self._level_tab_rects.append((rect, filename))
            x_offset += text_width + 6

        # "+ Jauns" poga
        plus_text = "+ Jauns"
        text_width = self._font_small.size(plus_text)[0] + 20
        rect = pygame.Rect(x_offset, y + 5, text_width, LEVEL_BAR_HEIGHT - 10)
        pygame.draw.rect(self._screen, (30, 60, 30), rect)
        pygame.draw.rect(self._screen, NEON_YELLOW, rect, 1)
        text = self._font_small.render(plus_text, True, NEON_YELLOW)
        self._screen.blit(text, (rect.x + 10, rect.y + 6))
        self._new_level_tab_rect = rect

    def _draw_category_bar(self):
        y = TOP_BAR_HEIGHT + LEVEL_BAR_HEIGHT
        pygame.draw.rect(self._screen, (30, 30, 50), (0, y, SCREEN_WIDTH, CATEGORY_BAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY, (0, y + CATEGORY_BAR_HEIGHT),
                         (SCREEN_WIDTH, y + CATEGORY_BAR_HEIGHT), 2)

        x_offset = 20
        for i, cat_name in enumerate(self._categories):
            text_width = self._font.size(cat_name)[0] + 30
            is_selected = (i == self._current_category_index)

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

        if self._categories:
            category = self._categories[self._current_category_index]
            tiles = self._registry.get_tiles_in_category(category)

            x_offset = 20 - self._toolbar_scroll
            tick = pygame.time.get_ticks() // 16
            for tile_def in tiles:
                btn_x = x_offset
                btn_y = toolbar_y + 15

                if btn_x + BUTTON_SIZE >= 0 and btn_x <= SCREEN_WIDTH:
                    is_selected = (tile_def.get_id() == self._current_tile_id)
                    self._registry.draw_tile(self._screen, tile_def.get_id(), btn_x, btn_y, tick)
                    border_color = NEON_CYAN if is_selected else GRAY
                    border_width = 4 if is_selected else 1
                    pygame.draw.rect(self._screen, border_color,
                                     (btn_x, btn_y, BUTTON_SIZE, BUTTON_SIZE), border_width)

                    name_text = self._tile_name_surfs.get(tile_def.get_id())
                    if name_text:
                        self._screen.blit(name_text, (btn_x, btn_y + BUTTON_SIZE + 4))

                x_offset += BUTTON_SIZE + BUTTON_SPACING

        controls_x = SCREEN_WIDTH - 400
        controls_y = toolbar_y + 10
        for i, surf in enumerate(self._toolbar_ctrl_surfs):
            self._screen.blit(surf, (controls_x, controls_y + i * 18))

    def _draw_message(self):
        text = self._font_big.render(self._message, True, NEON_YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, HEADER_HEIGHT + 50))

        bg_rect = text_rect.inflate(40, 20)
        pygame.draw.rect(self._screen, BLACK, bg_rect)
        pygame.draw.rect(self._screen, NEON_YELLOW, bg_rect, 2)

        self._screen.blit(text, text_rect)

    # === PALĪGI ===
    def _show_message(self, msg):
        self._message = msg
        self._message_timer = 120


if __name__ == "__main__":
    pygame.init()
    editor = LevelEditor()
    editor.run()
    pygame.quit()
    sys.exit()
