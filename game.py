import pygame
import sys
import os
from player import Player
from player_sprite import PlayerSprite
from world import World
from camera import Camera
from tile_registry import TileRegistry
from parallax_background import ParallaxBackground
from level import create_level
from score_log import ScoreLog
from sound_manager import SoundManager
from shader_pipeline import ShaderPipeline
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT,
    FPS, TITLE, FULLSCREEN,
    WHITE, BLACK, NEON_CYAN, NEON_GREEN, NEON_RED, NEON_YELLOW,
    GRAY,
    LEVELS_FOLDER,
)


STATE_PLAYING = "playing"
STATE_TASK = "task"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"


class Game:

    def __init__(self, player_name="Spēlētājs"):
        self._pipeline = ShaderPipeline.create(
            (SCREEN_WIDTH, SCREEN_HEIGHT), fullscreen=FULLSCREEN, shader="cyberpunk",
            display_size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
        )
        self._screen = self._pipeline.surface
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()

        # Fonti
        self._font_huge = pygame.font.SysFont("Arial", 64, bold=True)
        self._font_big = pygame.font.SysFont("Arial", 36, bold=True)
        self._font = pygame.font.SysFont("Arial", 24)
        self._font_code = pygame.font.SysFont("Consolas", 20)
        self._font_code_bold = pygame.font.SysFont("Consolas", 20, bold=True)
        self._font_code_small = pygame.font.SysFont("Consolas", 15, bold=True)
        self._font_small = pygame.font.SysFont("Arial", 18)

        self._player = Player(player_name)

        self._registry = TileRegistry()
        self._registry.load()

        # Pasaule
        self._world = World(registry=self._registry)
        self._load_world()

        spawn_x, spawn_y = self._world.get_spawn_position()
        self._player_sprite = PlayerSprite(spawn_x, spawn_y)

        # Kamera
        self._camera = Camera()
        self._camera.set_target(self._player_sprite)

        self._parallax = ParallaxBackground()
        self._parallax.create_cyberpunk_scene()

        self._score_log = ScoreLog()

        self._sound = SoundManager()
        self._sound.play_music()
        self._sound.start_ambience()
        self._win_sound_played = False

        self._state = STATE_PLAYING
        self._running = True
        pygame.key.stop_text_input()

        self._current_level = None
        self._current_portal = None
        self._input_text = ""
        self._feedback_message = ""
        self._feedback_color = WHITE
        self._feedback_timer = 0

        # Statistika
        self._completed_portals = set()

        self._portal_cooldown = 0

        # Backspace hold-to-delete
        self._backspace_held_frames = 0
        self._BACKSPACE_INITIAL_DELAY = 25
        self._BACKSPACE_REPEAT_RATE = 3

    def _load_world(self):
        level_file = "level_1.json"
        filepath = os.path.join(LEVELS_FOLDER, level_file)
        if os.path.exists(filepath):
            self._world.load_from_file(level_file)
        else:
            self._world.create_demo_world()

    def run(self):
        while self._running:
            self._handle_events()
            self._update()
            self._draw()
            self._clock.tick(FPS)

        self._sound.stop_music()
        self._sound.stop_ambience()
        self._score_log.save_score(self._player)
        self._pipeline.shutdown()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._state == STATE_TASK:
                        self._close_task_cancel()
                    else:
                        self._running = False
                    continue

                if event.key == pygame.K_F1:
                    self._pipeline.toggle()
                    continue

                if self._state == STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        self._player_sprite.jump()
                        self._sound.play_sound("jump")
                    elif event.key == pygame.K_UP:
                        self._player_sprite.jump()
                        self._sound.play_sound("jump")
                    elif event.key == pygame.K_r:
                        spawn_x, spawn_y = self._world.get_spawn_position()
                        self._player_sprite.respawn(spawn_x, spawn_y)

                elif self._state == STATE_TASK:
                    if event.key == pygame.K_RETURN:
                        if self._current_level and not self._current_level.is_typewriter_complete():
                            self._current_level.skip_typewriter()
                        else:
                            self._submit_answer()
                    elif event.key == pygame.K_TAB:
                        if self._current_level:
                            self._current_level.skip_typewriter()
                    elif event.key == pygame.K_BACKSPACE:
                        self._input_text = self._input_text[:-1]

                elif self._state in [STATE_GAME_OVER, STATE_WIN]:
                    if event.key == pygame.K_RETURN:
                        self._running = False

            # TEXTINPUT — dead-key composition (Latvian ' + a → ā)
            if event.type == pygame.TEXTINPUT:
                if self._state == STATE_TASK and len(self._input_text) < 50:
                    self._input_text += event.text

    def _handle_continuous_input(self):
        if self._state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()

        # Kustība
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._player_sprite.move_left()
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._player_sprite.move_right()
        else:
            self._player_sprite.stop()

        # Rāpšanās (W=augšup, S=lejup)
        if keys[pygame.K_w]:
            self._player_sprite.climb_up()
        elif keys[pygame.K_s]:
            self._player_sprite.climb_down()
        else:
            self._player_sprite.stop_climbing()

    def _handle_task_hold_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_BACKSPACE]:
            self._backspace_held_frames += 1
            if self._backspace_held_frames > self._BACKSPACE_INITIAL_DELAY:
                if (self._backspace_held_frames - self._BACKSPACE_INITIAL_DELAY) % self._BACKSPACE_REPEAT_RATE == 0:
                    self._input_text = self._input_text[:-1]
        else:
            self._backspace_held_frames = 0

    def _update(self):
        if self._state == STATE_PLAYING:
            self._handle_continuous_input()
            self._update_playing()
        elif self._state == STATE_TASK:
            self._handle_task_hold_input()

        if self._feedback_timer > 0:
            self._feedback_timer -= 1

        if self._portal_cooldown > 0:
            self._portal_cooldown -= 1

        self._sound.update_ambience()

    def _update_playing(self):
        self._player_sprite.update(
            self._world.get_solid_rects(),
            self._world.get_climbable_rects(),
        )
        self._camera.update()

        hazard = self._world.check_hazard_collision(self._player_sprite.get_rect())
        if hazard:
            self._sound.play_sound("death")
            spawn_x, spawn_y = self._world.get_spawn_position()
            self._player_sprite.respawn(spawn_x, spawn_y)
            self._show_feedback("NĀVE! Mēģini vēlreiz!", NEON_RED)
            self._pipeline.pulse_glitch(1.0)

        if self._portal_cooldown == 0:
            portal = self._world.check_portal_collision(self._player_sprite.get_rect())
            if portal and id(portal) not in self._completed_portals:
                self._open_task(portal)
                self._pipeline.pulse_glitch(0.8)

    def _open_task(self, portal):
        level_id = portal.get_level_id()
        self._current_level = create_level(level_id)
        self._current_level.load_tasks()
        self._current_level.reset_typewriter()
        self._current_portal = portal
        self._state = STATE_TASK
        self._input_text = ""
        self._player.reset_attempts()
        pygame.key.start_text_input()
        self._sound.play_sound("portal_open")
        print(f"🌀 Portāls atvērts: Līmenis {level_id}")

    def _submit_answer(self):
        if not self._input_text.strip():
            return

        task = self._current_level.get_current_task()
        if task is None:
            self._close_task_success()
            return

        if task.verify(self._input_text):
            # PAREIZI
            self._player.increment_attempts()
            attempts = self._player.get_attempts()
            points = task.calculate_points(attempts)
            self._player.add_score(points)

            self._sound.play_sound("correct")
            self._show_feedback(f"PAREIZI! +{points} punkti!", NEON_GREEN)
            self._input_text = ""
            self._player.reset_attempts()

            self._current_level.next_task()
            if self._current_level.is_complete():
                self._close_task_success()
        else:
            # NEPAREIZI
            self._player.increment_attempts()
            self._player.deduct_score(5)
            attempts = self._player.get_attempts()

            self._sound.play_sound("wrong")

            if not self._player.has_attempts_left():
                self._show_feedback("Pārāk daudz kļūdu! -5 punkti!", NEON_RED)
                self._pipeline.pulse_glitch(1.0)
                self._close_task_fail()
            else:
                remaining = 3 - attempts
                hint = task.get_hint() if attempts >= 2 else ""
                msg = f"Nepareizi! -5 punkti! Vēl {remaining} mēģ. {hint}"
                self._show_feedback(msg, NEON_YELLOW)
                self._pipeline.pulse_glitch(0.45)
                self._input_text = ""

    def _close_task_success(self):
        if self._current_portal:
            self._current_portal.deactivate()
            self._completed_portals.add(id(self._current_portal))
            self._player.advance_level()
            self._sound.play_sound("portal_complete")

            if len(self._completed_portals) >= 3:
                self._state = STATE_WIN
                return

        self._return_to_playing()

    def _close_task_fail(self):
        self._return_to_playing()

    def _close_task_cancel(self):
        self._return_to_playing()

    def _return_to_playing(self):
        self._state = STATE_PLAYING
        self._current_level = None
        self._current_portal = None
        self._input_text = ""
        self._portal_cooldown = 60
        pygame.key.stop_text_input()

        # Push the player away from the portal so they don't re-trigger it.
        self._player_sprite.nudge(-100)

    def _show_feedback(self, msg, color):
        self._feedback_message = msg
        self._feedback_color = color
        self._feedback_timer = 180

    def _draw(self):
        if self._state == STATE_PLAYING:
            self._draw_playing()
        elif self._state == STATE_TASK:
            self._draw_playing()
            self._draw_task_ui()
        elif self._state == STATE_WIN:
            if not self._win_sound_played:
                self._sound.stop_music()
                self._sound.play_sound("win")
                self._win_sound_played = True
            self._draw_playing()
            self._draw_win_screen()
        elif self._state == STATE_GAME_OVER:
            self._draw_playing()
            self._draw_game_over_screen()

        self._pipeline.present()

    def _draw_playing(self):
        cam_x, cam_y = self._camera.get_offset()
        self._parallax.draw(self._screen, cam_x, cam_y)
        self._world.draw(self._screen, cam_x, cam_y)
        self._player_sprite.draw(self._screen, cam_x, cam_y)
        self._camera.apply_motion_blur(self._screen)
        self._draw_hud()

        if self._feedback_timer > 0:
            self._draw_feedback()

    def _draw_hud(self):
        bar = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 180))
        self._screen.blit(bar, (0, 0))

        info = f"Spēlētājs: {self._player.get_name()}"
        text = self._font.render(info, True, WHITE)
        self._screen.blit(text, (20, 20))

        score = f"Punkti: {self._player.get_score()}"
        text = self._font.render(score, True, NEON_YELLOW)
        self._screen.blit(text, (300, 20))

        portals_text = f"Portāli: {len(self._completed_portals)} / 3"
        text = self._font.render(portals_text, True, NEON_CYAN)
        self._screen.blit(text, (500, 20))

        controls = "A/D = staigāt | SPACE = lekt | W/S = rāpties | R = respawn | F1 = FX | ESC = iziet"
        text = self._font_small.render(controls, True, GRAY)
        self._screen.blit(text, (SCREEN_WIDTH - 640, 25))

    def _draw_feedback(self):
        text = self._font_big.render(self._feedback_message, True, self._feedback_color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 120))

        bg = text_rect.inflate(40, 20)
        pygame.draw.rect(self._screen, BLACK, bg)
        pygame.draw.rect(self._screen, self._feedback_color, bg, 3)

        self._screen.blit(text, text_rect)

    def _draw_task_ui(self):
        if self._current_level is None:
            return

        layout = self._current_level.display_task(
            self._screen, self._font_code,
            attempts=self._player.get_attempts(),
        )
        if layout is None:
            return

        self._draw_terminal_input(layout)
        self._draw_terminal_hints(layout)

    def _draw_terminal_input(self, layout):
        rect = layout["input"]
        color = self._current_level.get_theme_color()
        dim = tuple(int(c * 0.4) for c in color)

        pygame.draw.rect(self._screen, BLACK, rect)
        pygame.draw.rect(self._screen, dim, rect, 1)
        pygame.draw.line(self._screen, color, (rect.x, rect.y), (rect.x, rect.bottom), 3)

        prompt_surf = self._font_code_bold.render(">>>", True, color)
        prompt_x = rect.x + 16
        prompt_y = rect.y + (rect.h - prompt_surf.get_height()) // 2
        self._screen.blit(prompt_surf, (prompt_x, prompt_y))

        text_x = prompt_x + prompt_surf.get_width() + 10
        text_y = prompt_y
        text_surf = self._font_code.render(self._input_text, True, WHITE)
        self._screen.blit(text_surf, (text_x, text_y))

        if (pygame.time.get_ticks() // 400) % 2 == 0:
            cursor_x = text_x + text_surf.get_width() + 1
            cursor_w = max(8, self._font_code.size("M")[0])
            cursor_h = self._font_code.get_height() - 4
            pygame.draw.rect(self._screen, color, (cursor_x, text_y + 2, cursor_w, cursor_h))

    def _draw_terminal_hints(self, layout):
        rect = layout["hint"]
        color = self._current_level.get_theme_color()
        dim_text = (140, 142, 148)

        parts = [
            ("[ENTER]", color), (" execute    ", dim_text),
            ("[ESC]",   color), (" disconnect    ", dim_text),
            ("[TAB]",   color), (" skip",            dim_text),
        ]
        total_w = sum(self._font_code_small.size(t)[0] for t, _ in parts)
        x = rect.centerx - total_w // 2
        y = rect.y
        for text, c in parts:
            surf = self._font_code_small.render(text, True, c)
            self._screen.blit(surf, (x, y))
            x += surf.get_width()

    def _draw_win_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self._screen.blit(overlay, (0, 0))

        win_text = self._font_huge.render("UZVARA!", True, NEON_GREEN)
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self._screen.blit(win_text, win_rect)

        score_text = self._font_big.render(f"Punkti: {self._player.get_score()}", True, NEON_YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(score_text, score_rect)

        portals_text = self._font.render("Pabeigti visi 3 portāli!", True, WHITE)
        portals_rect = portals_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self._screen.blit(portals_text, portals_rect)

        hint = self._font.render("Nospied ENTER, lai izietu", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self._screen.blit(hint, hint_rect)

    def _draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self._screen.blit(overlay, (0, 0))

        gg_text = self._font_huge.render("SPĒLE BEIGUSIES", True, NEON_RED)
        gg_rect = gg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(gg_text, gg_rect)


if __name__ == "__main__":
    pygame.init()
    game = Game("TestSpēlētājs")
    game.run()
    pygame.quit()
