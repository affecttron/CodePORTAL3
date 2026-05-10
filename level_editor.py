# level_editor.py - Vizuālais līmeņu redaktors
# Ļauj klikšķināt un veidot līmeņus, saglabāt JSON, ielādēt atpakaļ.
# Demonstrē OOP, peles input apstrādi, faila apstrādi.

import pygame
import sys
import os
from world import World
from camera import Camera
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, BACKGROUND_COLOR, TILE_SIZE,
    EDITOR_TOOLBAR_HEIGHT, EDITOR_GRID_COLOR,
    TILE_GROUND, TILE_PLATFORM,
    TILE_PORTAL_RED, TILE_PORTAL_YELLOW, TILE_PORTAL_GREEN, TILE_SPAWN,
    NEON_RED, NEON_YELLOW, NEON_GREEN, NEON_CYAN, NEON_PINK,
    WHITE, BLACK, GRAY, DARK_GRAY,
    LEVELS_FOLDER,
)


# Tile tipu konfigurācija (taustiņš -> tips, krāsa, nosaukums)
TILE_OPTIONS = [
    {"key": pygame.K_1, "type": TILE_GROUND,        "color": (60, 60, 90),   "name": "GROUND"},
    {"key": pygame.K_2, "type": TILE_PLATFORM,      "color": (80, 90, 120),  "name": "PLATFORM"},
    {"key": pygame.K_3, "type": TILE_PORTAL_RED,    "color": NEON_RED,        "name": "PORTAL R"},
    {"key": pygame.K_4, "type": TILE_PORTAL_YELLOW, "color": NEON_YELLOW,     "name": "PORTAL Y"},
    {"key": pygame.K_5, "type": TILE_PORTAL_GREEN,  "color": NEON_GREEN,      "name": "PORTAL G"},
    {"key": pygame.K_6, "type": TILE_SPAWN,         "color": NEON_PINK,       "name": "SPAWN"},
]


class LevelEditor:
    """Level Editor klase - vizuālais līmeņu redaktors."""

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("CODE Portal 3 - Level Editor")
        self._clock = pygame.time.Clock()

        # Fonti
        self._font = pygame.font.SysFont("Arial", 20)
        self._font_small = pygame.font.SysFont("Arial", 16)
        self._font_big = pygame.font.SysFont("Arial", 28, bold=True)

        # Pasaule un kamera
        self._world = World()
        self._camera = Camera()

        # Stāvoklis
        self._running = True
        self._current_tile_index = 0  # Indekss uz TILE_OPTIONS
        self._show_grid = True
        self._current_filename = "level_1.json"
        self._unsaved_changes = False
        self._message = ""
        self._message_timer = 0

        # Pele
        self._mouse_pos = (0, 0)

    # ========================================================
    # GALVENAIS CIKLS
    # ========================================================
    def run(self):
        """Galvenais editora cikls."""
        # Ja eksistē level_1.json - ielādējam to. Citādi izveidojam tukšu.
        if os.path.exists(os.path.join(LEVELS_FOLDER, self._current_filename)):
            self._world.load_from_file(self._current_filename)
            self._show_message(f"Ielādēts: {self._current_filename}")
        else:
            self._show_message("Jauns līmenis (tukšs)")

        while self._running:
            self._handle_events()
            self._update()
            self._draw()
            self._clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # ========================================================
    # NOTIKUMU APSTRĀDE
    # ========================================================
    def _handle_events(self):
        """Apstrādā visus pygame notikumus."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

        # Turamie taustiņi - kameras kustība
        self._handle_continuous_input()

    def _handle_keydown(self, event):
        """Apstrādā taustiņu nospiešanu."""
        # ESC - iziet
        if event.key == pygame.K_ESCAPE:
            self._running = False
            return

        # G - režģis on/off
        if event.key == pygame.K_g:
            self._show_grid = not self._show_grid
            self._show_message(f"Režģis: {'IESL' if self._show_grid else 'IZSL'}")
            return

        # TAB - nākamais tile
        if event.key == pygame.K_TAB:
            self._current_tile_index = (self._current_tile_index + 1) % len(TILE_OPTIONS)
            self._show_message(f"Izvēlēts: {TILE_OPTIONS[self._current_tile_index]['name']}")
            return

        # 1-6 - izvēlies tile tipu
        for i, option in enumerate(TILE_OPTIONS):
            if event.key == option["key"]:
                self._current_tile_index = i
                self._show_message(f"Izvēlēts: {option['name']}")
                return

        # Ctrl + taustiņi
        keys = pygame.key.get_pressed()
        ctrl_pressed = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]

        if ctrl_pressed:
            # Ctrl+S - saglabāt
            if event.key == pygame.K_s:
                self._world.save_to_file(self._current_filename)
                self._unsaved_changes = False
                self._show_message(f"Saglabāts: {self._current_filename}")
                return

            # Ctrl+N - jauns (tukšs)
            if event.key == pygame.K_n:
                self._world.clear()
                self._unsaved_changes = True
                self._show_message("Jauns tukšs līmenis")
                return

            # Ctrl+1, Ctrl+2, Ctrl+3 - mainām failu
            if event.key == pygame.K_1:
                self._switch_level("level_1.json")
                return
            if event.key == pygame.K_2:
                self._switch_level("level_2.json")
                return
            if event.key == pygame.K_3:
                self._switch_level("level_3.json")
                return

    def _handle_mouse_click(self, event):
        """Apstrādā peles klikšķi."""
        screen_x, screen_y = event.pos

        # Nereaģējam, ja klikšķis ir uz toolbar
        if screen_y >= SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT:
            return

        # Pārvēršam ekrāna koordinātes pasaules koordinātēs
        world_x, world_y = self._camera.screen_to_world(screen_x, screen_y)

        # Atrodam režģa koordinātes
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        if event.button == 1:  # Kreisais klikšķis - liec tile
            current_tile = TILE_OPTIONS[self._current_tile_index]
            self._world.add_tile(current_tile["type"], grid_x, grid_y)
            self._unsaved_changes = True

        elif event.button == 3:  # Labais klikšķis - dzēš tile
            self._world.remove_tile(grid_x, grid_y)
            self._unsaved_changes = True

    def _handle_continuous_input(self):
        """Apstrādā taustiņus, kas tiek turēti."""
        keys = pygame.key.get_pressed()
        camera_speed = 15

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._camera.move(-camera_speed, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._camera.move(camera_speed, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._camera.move(0, -camera_speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._camera.move(0, camera_speed)

        # Kreisais peles taustiņš tiek turēts - rasēšanas režīms
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # Kreisais turēts
            self._paint_at_mouse(add=True)
        elif mouse_buttons[2]:  # Labais turēts
            self._paint_at_mouse(add=False)

    def _paint_at_mouse(self, add=True):
        """Liec/dzēš tile pie peles pozīcijas (turot taustiņu)."""
        screen_x, screen_y = pygame.mouse.get_pos()

        # Nereaģējam uz toolbar
        if screen_y >= SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT:
            return

        world_x, world_y = self._camera.screen_to_world(screen_x, screen_y)
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        if add:
            current_tile = TILE_OPTIONS[self._current_tile_index]
            # Pārbaudām, vai nav jau tāds tile
            existing = self._world.get_tile_at(grid_x, grid_y)
            if existing is None or existing.get_type() != current_tile["type"]:
                self._world.add_tile(current_tile["type"], grid_x, grid_y)
                self._unsaved_changes = True
        else:
            self._world.remove_tile(grid_x, grid_y)
            self._unsaved_changes = True

    # ========================================================
    # ATJAUNINĀŠANA
    # ========================================================
    def _update(self):
        """Atjaunina editora stāvokli."""
        self._mouse_pos = pygame.mouse.get_pos()
        self._camera.update()

        # Ziņojuma timer
        if self._message_timer > 0:
            self._message_timer -= 1

    # ========================================================
    # ZĪMĒŠANA
    # ========================================================
    def _draw(self):
        """Zīmē visu editoru."""
        self._screen.fill(BACKGROUND_COLOR)

        cam_x, cam_y = self._camera.get_offset()

        # 1. Režģis
        if self._show_grid:
            self._draw_grid(cam_x, cam_y)

        # 2. Pasaule (tiles)
        self._world.draw(self._screen, cam_x, cam_y)

        # 3. Spawn pozīcijas atzīme
        self._draw_spawn_marker(cam_x, cam_y)

        # 4. Peles "priekšskatījums"
        self._draw_mouse_preview(cam_x, cam_y)

        # 5. Toolbar apakšā
        self._draw_toolbar()

        # 6. Augšējais info bars
        self._draw_top_bar()

        # 7. Ziņojums (ja ir)
        if self._message_timer > 0:
            self._draw_message()

        pygame.display.flip()

    def _draw_grid(self, cam_x, cam_y):
        """Zīmē režģi."""
        # Vertikālās līnijas
        start_x = -(cam_x % TILE_SIZE)
        for x in range(int(start_x), SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                             (x, 0), (x, SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT), 1)

        # Horizontālās līnijas
        start_y = -(cam_y % TILE_SIZE)
        for y in range(int(start_y), SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT, TILE_SIZE):
            pygame.draw.line(self._screen, EDITOR_GRID_COLOR,
                             (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_spawn_marker(self, cam_x, cam_y):
        """Zīmē spawn pozīciju ar X krustu."""
        spawn_x, spawn_y = self._world.get_spawn_position()
        screen_x = spawn_x - cam_x
        screen_y = spawn_y - cam_y

        if 0 <= screen_x <= SCREEN_WIDTH and 0 <= screen_y <= SCREEN_HEIGHT:
            # Dzeltens X krusts
            pygame.draw.line(self._screen, NEON_YELLOW,
                             (screen_x + 5, screen_y + 5),
                             (screen_x + TILE_SIZE - 5, screen_y + TILE_SIZE - 5), 3)
            pygame.draw.line(self._screen, NEON_YELLOW,
                             (screen_x + TILE_SIZE - 5, screen_y + 5),
                             (screen_x + 5, screen_y + TILE_SIZE - 5), 3)
            # "SPAWN" teksts
            spawn_label = self._font_small.render("SPAWN", True, NEON_YELLOW)
            self._screen.blit(spawn_label, (screen_x, screen_y - 20))

    def _draw_mouse_preview(self, cam_x, cam_y):
        """Zīmē priekšskatījumu tur, kur ir pele."""
        mouse_x, mouse_y = self._mouse_pos


        if mouse_y >= SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT:
            return


        world_x, world_y = self._camera.screen_to_world(mouse_x, mouse_y)
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)

        preview_x = grid_x * TILE_SIZE - cam_x
        preview_y = grid_y * TILE_SIZE - cam_y

        current_tile = TILE_OPTIONS[self._current_tile_index]
        preview_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        preview_color = (*current_tile["color"], 128)  # Pus-caurspīdīgs
        preview_surface.fill(preview_color)
        self._screen.blit(preview_surface, (preview_x, preview_y))

        # Maliņa
        pygame.draw.rect(self._screen, WHITE,
                         (preview_x, preview_y, TILE_SIZE, TILE_SIZE), 2)

        # Pozīcijas teksts
        pos_text = self._font_small.render(f"({grid_x}, {grid_y})", True, WHITE)
        self._screen.blit(pos_text, (preview_x, preview_y - 18))

    def _draw_toolbar(self):
        """Zīmē apakšējo toolbar ar tile izvēlēm."""
        toolbar_y = SCREEN_HEIGHT - EDITOR_TOOLBAR_HEIGHT

        # Fons
        pygame.draw.rect(self._screen, DARK_GRAY,
                         (0, toolbar_y, SCREEN_WIDTH, EDITOR_TOOLBAR_HEIGHT))
        pygame.draw.line(self._screen, GRAY,
                         (0, toolbar_y), (SCREEN_WIDTH, toolbar_y), 2)

        # Tile pogas
        button_size = 80
        button_spacing = 10
        start_x = 20

        for i, option in enumerate(TILE_OPTIONS):
            btn_x = start_x + i * (button_size + button_spacing)
            btn_y = toolbar_y + 10

            # Pogas fons
            is_selected = (i == self._current_tile_index)
            border_color = NEON_CYAN if is_selected else GRAY
            border_width = 4 if is_selected else 1

            pygame.draw.rect(self._screen, option["color"],
                             (btn_x, btn_y, button_size, button_size))
            pygame.draw.rect(self._screen, border_color,
                             (btn_x, btn_y, button_size, button_size), border_width)

            # Numurs
            num_text = self._font.render(str(i + 1), True, WHITE)
            self._screen.blit(num_text, (btn_x + 5, btn_y + 5))

            # Nosaukums
            name_text = self._font_small.render(option["name"], True, WHITE)
            name_rect = name_text.get_rect(center=(btn_x + button_size // 2, btn_y + button_size + 8))
            self._screen.blit(name_text, name_rect)


        controls_x = SCREEN_WIDTH - 600
        controls_y = toolbar_y + 10
        controls = [
            "MOUSE: Kreisais=likt, Labais=dzēst",
            "WASD/Bultiņas: Kamera",
            "Ctrl+S: Saglabāt | Ctrl+N: Tukšs",
            "Ctrl+1/2/3: level_1/2/3 | G: Režģis | TAB: Nākamais",
        ]
        for i, line in enumerate(controls):
            text = self._font_small.render(line, True, WHITE)
            self._screen.blit(text, (controls_x, controls_y + i * 20))

    def _draw_top_bar(self):
        """Zīmē augšējo info bar."""
        pygame.draw.rect(self._screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, 40))
        pygame.draw.line(self._screen, GRAY, (0, 40), (SCREEN_WIDTH, 40), 2)

        # Teksts
        current = TILE_OPTIONS[self._current_tile_index]
        unsaved_mark = " *" if self._unsaved_changes else ""

        info = f"LEVEL EDITOR  |  Fails: {self._current_filename}{unsaved_mark}  |  Tile: {current['name']}  |  Kopā tiles: {self._world.get_tile_count()}"
        text = self._font.render(info, True, WHITE)
        self._screen.blit(text, (20, 10))

    def _draw_message(self):
        """Zīmē īslaicīgu ziņojumu ekrāna centrā."""
        text = self._font_big.render(self._message, True, NEON_YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        bg_rect = text_rect.inflate(40, 20)
        pygame.draw.rect(self._screen, BLACK, bg_rect)
        pygame.draw.rect(self._screen, NEON_YELLOW, bg_rect, 2)

        self._screen.blit(text, text_rect)


    def _show_message(self, msg):
        """Parāda īslaicīgu ziņojumu."""
        self._message = msg
        self._message_timer = 120

    def _switch_level(self, filename):
        """Pārslēdzas uz citu līmeni."""
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