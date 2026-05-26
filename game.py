import pygame
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
    WORLD_LABELS, get_world_config,
)
from ui_utils import dim_color, draw_corner_accents


STATE_PLAYING = "playing"
STATE_TASK = "task"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"
STATE_TRANSITION = "transition"


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

        self._world_index = 0
        self._current_world_config = get_world_config(0)
        self._door_unlocked = False
        self._transition_timer = 0
        self._next_world_index = 1
        self._endless_mode = False

        self._player.set_max_attempts(self._current_world_config["max_attempts"])

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

        self._portal_cooldown = 0

        self._correct_flash_timer = 0
        self._correct_flash_points = 0
        self._correct_flash_oc = 0
        self._pending_next_task = False
        self._hint_revealed = False
        self._hint_text = ""

        self._death_flash_timer = 0
        self._death_flash_points = 10

        # Pre-allocated overlay surfaces — filled each frame, never reallocated
        _flash_w = 1100 - 2 * 26   # PANEL_WIDTH - 2*PANEL_PADDING_X
        _flash_h = 360 + 12 + 32   # CODE_BLOCK_HEIGHT + gap + OVERCLOCK_AREA_HEIGHT
        self._correct_flash_surf = pygame.Surface((_flash_w, _flash_h), pygame.SRCALPHA)

        self._death_overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._death_stripe_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self._fullscreen_dark_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._fullscreen_dark_surf.fill((0, 0, 0, 220))

        # Backspace hold-to-delete
        self._backspace_held_frames = 0
        self._BACKSPACE_INITIAL_DELAY = 25
        self._BACKSPACE_REPEAT_RATE = 3

        # HUD pulse state (score change flash + completion latch)
        self._hud_last_score = self._player.get_score()
        self._hud_score_pulse_ms = -10000
        self._hud_score_delta = 0
        self._hud_last_completed = 0
        self._hud_portal_pulse_ms = -10000

        # === Cached HUD surfaces (allocated once, reused every frame) ===
        _hud_w = SCREEN_WIDTH - self.HUD_MARGIN_X * 2
        _dim_cyan = dim_color(NEON_CYAN, 0.45)
        _label_dim = (140, 142, 148)

        self._hud_bg_surf = pygame.Surface((_hud_w, self.HUD_HEIGHT), pygame.SRCALPHA)
        self._hud_bg_surf.fill(self.HUD_BG)

        self._hud_title_tint_surf = pygame.Surface((_hud_w, self.HUD_TITLE_HEIGHT), pygame.SRCALPHA)
        self._hud_title_tint_surf.fill((NEON_CYAN[0], NEON_CYAN[1], NEON_CYAN[2], 26))

        self._hud_scanline_surf = pygame.Surface((_hud_w, self.HUD_HEIGHT), pygame.SRCALPHA)
        _sl_color = (NEON_CYAN[0], NEON_CYAN[1], NEON_CYAN[2], 14)
        for _y in range(0, self.HUD_HEIGHT, 3):
            pygame.draw.line(self._hud_scanline_surf, _sl_color, (0, _y), (_hud_w, _y))

        _score_max = self._font_code_bold.render("99999", True, NEON_YELLOW)
        self._score_halo_surf = pygame.Surface(
            (_score_max.get_width() + 28, _score_max.get_height() + 14), pygame.SRCALPHA
        )
        self._portal_halo_surf = pygame.Surface((52, 28), pygame.SRCALPHA)

        self._hud_chip_surf = self._font_code_small.render("[ HUD // OPERATOR_LINK ]", True, NEON_CYAN)
        _name = self._player.get_name()
        _sid = sum(ord(c) for c in _name) & 0xFFFF
        self._hud_prompt_surf = self._font_code_small.render(
            f"root@portal:~# ./monitor --uid=0x{_sid:04X}", True, _dim_cyan
        )
        self._hud_sys_bright_surf = self._font_code_small.render("SYS: ONLINE", True, NEON_CYAN)
        self._hud_sys_dim_surf    = self._font_code_small.render("SYS: ONLINE", True, _dim_cyan)

        self._hud_section_label_surfs = [
            self._font_code_small.render(lbl, True, _label_dim)
            for lbl in ("OPERATOR", "SCORE", "PORTALS", "CONTROLS")
        ]

        _row1_data = [
            ("[A/D]",   NEON_CYAN), (" staigāt  ", _label_dim),
            ("[SPACE]", NEON_CYAN), (" lekt  ",    _label_dim),
            ("[W/S]",   NEON_CYAN), (" rāpties",   _label_dim),
        ]
        _row2_data = [
            ("[R]",   NEON_CYAN), (" respawn  ", _label_dim),
            ("[F1]",  NEON_CYAN), (" FX  ",      _label_dim),
            ("[F9]",  NEON_CYAN), (" skip  ",    _label_dim),
            ("[ESC]", NEON_CYAN), (" iziet",      _label_dim),
        ]
        self._ctrl_surfs_row1 = [self._font_code_small.render(t, True, c) for t, c in _row1_data]
        self._ctrl_surfs_row2 = [self._font_code_small.render(t, True, c) for t, c in _row2_data]

    def _load_world(self, world_index=0):
        self._world_index = world_index
        self._current_world_config = get_world_config(world_index)

        level_file = f"level_{world_index + 1}.json"
        if not os.path.exists(os.path.join(LEVELS_FOLDER, level_file)):
            level_file = "level_1.json"

        filepath = os.path.join(LEVELS_FOLDER, level_file)
        if os.path.exists(filepath):
            self._world.load_from_file(level_file)
        else:
            self._world.create_demo_world()

        self._completed_portals = set()
        self._door_unlocked = False
        self._world.lock_doors()
        self._player.set_max_attempts(self._current_world_config["max_attempts"])

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
                    elif event.key == pygame.K_F9:
                        self._debug_skip_world()

                elif self._state == STATE_TASK:
                    if self._correct_flash_timer > 0:
                        pass
                    elif event.key == pygame.K_RETURN:
                        if self._current_level and not self._current_level.is_typewriter_complete():
                            self._current_level.skip_typewriter()
                        else:
                            self._submit_answer()
                    elif event.key == pygame.K_TAB:
                        if self._current_level:
                            self._current_level.skip_typewriter()
                    elif event.key == pygame.K_BACKSPACE:
                        self._input_text = self._input_text[:-1]

                elif self._state == STATE_WIN:
                    if event.key == pygame.K_RETURN:
                        self._endless_mode = True
                        self._load_world(3)
                        spawn_x, spawn_y = self._world.get_spawn_position()
                        self._player_sprite.respawn(spawn_x, spawn_y)
                        self._state = STATE_PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        self._running = False
                elif self._state == STATE_GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self._running = False

            # TEXTINPUT — dead-key composition (Latvian ' + a → ā)
            if event.type == pygame.TEXTINPUT:
                if self._state == STATE_TASK and self._correct_flash_timer == 0 and len(self._input_text) < 50:
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
            if self._correct_flash_timer > 0:
                self._correct_flash_timer -= 1
                if self._correct_flash_timer == 0 and self._pending_next_task:
                    self._pending_next_task = False
                    self._hint_revealed = False
                    self._hint_text = ""
                    self._current_level.next_task()
                    if self._current_level.is_complete():
                        self._close_task_success()
                    else:
                        self._current_level.reset_typewriter()
        elif self._state == STATE_TRANSITION:
            self._update_transition()

        if self._feedback_timer > 0:
            self._feedback_timer -= 1

        if self._death_flash_timer > 0:
            self._death_flash_timer -= 1

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
        if hazard and self._death_flash_timer == 0:
            self._sound.play_sound("death")
            spawn_x, spawn_y = self._world.get_spawn_position()
            self._player_sprite.respawn(spawn_x, spawn_y)
            self._player.deduct_score(self._death_flash_points)
            self._death_flash_timer = 90
            self._pipeline.pulse_glitch(1.0)

        if self._portal_cooldown == 0:
            portal = self._world.check_portal_collision(self._player_sprite.get_rect())
            if portal and id(portal) not in self._completed_portals:
                self._open_task(portal)
                self._pipeline.pulse_glitch(0.8)

        if self._door_unlocked and self._portal_cooldown == 0:
            if self._world.check_door_collision(self._player_sprite.get_rect()):
                self._next_world_index = self._world_index + 1
                self._transition_timer = 0
                self._state = STATE_TRANSITION
                self._pipeline.pulse_glitch(1.0)

    def _update_transition(self):
        self._transition_timer += 1
        # After completing world 2 (index 2): door walk leads to win screen, not world 4
        if self._next_world_index == 3 and not self._endless_mode:
            if self._transition_timer >= 30:
                self._state = STATE_WIN
            return
        # Normal: show title card then load next world
        if self._transition_timer >= 121:
            self._load_world(self._next_world_index)
            spawn_x, spawn_y = self._world.get_spawn_position()
            self._player_sprite.respawn(spawn_x, spawn_y)
            self._portal_cooldown = 60
            self._state = STATE_PLAYING

    def _open_task(self, portal):
        portal_slot = portal.get_level_id() - 1
        level_ids = self._current_world_config.get("level_ids", [1, 2, 3])
        level_id = level_ids[portal_slot] if portal_slot < len(level_ids) else portal.get_level_id()
        overclock_ms = self._current_world_config["overclock_ms"]
        self._current_level = create_level(level_id, overclock_ms=overclock_ms)
        self._current_level.load_tasks()
        self._current_level.reset_typewriter()
        self._current_portal = portal
        self._state = STATE_TASK
        self._input_text = ""
        self._correct_flash_timer = 0
        self._pending_next_task = False
        self._hint_revealed = False
        self._hint_text = ""
        self._player.reset_attempts()
        pygame.key.start_text_input()
        self._sound.play_sound("portal_open")
        print(f"Portal opened: Level {level_id}")

    def _submit_answer(self):
        if not self._input_text.strip():
            return

        task = self._current_level.get_current_task()
        if task is None:
            self._close_task_success()
            return

        if task.verify(self._input_text):
            self._player.increment_attempts()
            attempts = self._player.get_attempts()
            points = task.calculate_points(attempts)
            oc_bonus = self._current_level.consume_overclock_bonus()
            self._player.add_score(points + oc_bonus)
            self._sound.play_sound("correct")

            self._correct_flash_points = points
            self._correct_flash_oc = oc_bonus
            self._correct_flash_timer = 70
            self._pending_next_task = True
            self._input_text = ""
            self._player.reset_attempts()
        else:
            self._player.increment_attempts()
            self._player.deduct_score(5)
            attempts = self._player.get_attempts()
            self._current_level.void_overclock()
            self._sound.play_sound("wrong")

            self._hint_revealed = True
            self._hint_text = task.get_hint()

            if not self._player.has_attempts_left():
                self._show_feedback("Parāk daudz kļūdu!", NEON_RED)
                self._pipeline.pulse_glitch(1.0)
                self._close_task_fail()
            else:
                remaining = 3 - attempts
                self._show_feedback(f"Nepareizi! Vel {remaining} meginjums. -5 pts", NEON_YELLOW)
                self._pipeline.pulse_glitch(0.45)
                self._input_text = ""

    def _close_task_success(self):
        if self._current_portal:
            self._current_portal.deactivate()
            self._completed_portals.add(id(self._current_portal))
            self._player.advance_level()
            self._sound.play_sound("portal_complete")

            if len(self._completed_portals) >= self._world.get_portal_count():
                self._door_unlocked = True
                self._world.unlock_door()
                self._show_feedback("DURVIS ATSLĒGTAS — sasniedz izeju!", NEON_CYAN)
                self._return_to_playing()
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
        self._correct_flash_timer = 0
        self._pending_next_task = False
        self._hint_revealed = False
        self._hint_text = ""
        self._portal_cooldown = 60
        pygame.key.stop_text_input()

        # Push the player away from the portal so they don't re-trigger it.
        self._player_sprite.nudge(-100)

    def _debug_skip_world(self):
        for portal in self._world.get_portals():
            portal.deactivate()
            self._completed_portals.add(id(portal))
        self._door_unlocked = True
        self._world.unlock_door()
        self._next_world_index = self._world_index + 1
        self._transition_timer = 0
        self._state = STATE_TRANSITION
        self._pipeline.pulse_glitch(1.0)

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
        elif self._state == STATE_TRANSITION:
            self._draw_playing()
            if self._transition_timer >= 31:
                self._draw_transition_screen()

        self._pipeline.present()

    def _draw_correct_flash(self, layout):
        t = self._correct_flash_timer
        frac = min(1.0, t / 22.0)

        code_rect = layout["code"]
        oc_rect = layout["overclock"]
        flash_rect = pygame.Rect(code_rect.x, code_rect.y, code_rect.w, oc_rect.bottom - code_rect.y)

        self._correct_flash_surf.fill((0, int(30 * frac), 0, int(210 * frac)))
        self._screen.blit(self._correct_flash_surf, flash_rect.topleft)

        color = NEON_GREEN
        c = tuple(int(ch * frac) for ch in color)

        pygame.draw.rect(self._screen, c, flash_rect, 3)
        al = 12
        for cx2, cy2, dx, dy in [
            (flash_rect.x, flash_rect.y, 1, 1),
            (flash_rect.right - 1, flash_rect.y, -1, 1),
            (flash_rect.x, flash_rect.bottom - 1, 1, -1),
            (flash_rect.right - 1, flash_rect.bottom - 1, -1, -1),
        ]:
            pygame.draw.line(self._screen, c, (cx2, cy2), (cx2 + dx * al, cy2), 2)
            pygame.draw.line(self._screen, c, (cx2, cy2), (cx2, cy2 + dy * al), 2)

        ok_surf = self._font_huge.render("PAREIZI!", True, c)
        ok_rect = ok_surf.get_rect(center=(flash_rect.centerx, flash_rect.centery - 28))
        self._screen.blit(ok_surf, ok_rect)

        if self._correct_flash_oc:
            pts_text = f"+{self._correct_flash_points} pts   [ +{self._correct_flash_oc} OVERCLOCK ]"
        else:
            pts_text = f"+{self._correct_flash_points} pts"
        pts_surf = self._font_big.render(pts_text, True, c)
        pts_rect = pts_surf.get_rect(center=(flash_rect.centerx, flash_rect.centery + 36))
        self._screen.blit(pts_surf, pts_rect)

    def _draw_playing(self):
        cam_x, cam_y = self._camera.get_offset()
        self._parallax.draw(self._screen, cam_x, cam_y)
        self._world.draw(self._screen, cam_x, cam_y)
        self._player_sprite.draw(self._screen, cam_x, cam_y)
        self._camera.apply_motion_blur(self._screen)
        self._draw_hud()

        if self._feedback_timer > 0:
            self._draw_feedback()
        if self._death_flash_timer > 0:
            self._draw_death_flash()

    # === HUD (bottom-anchored cyberpunk terminal) ===

    HUD_MARGIN_X = 32
    HUD_MARGIN_BOTTOM = 24
    HUD_HEIGHT = 112
    HUD_TITLE_HEIGHT = 32
    HUD_BG = (10, 12, 16, 215)

    def _hud_dim(self, color, factor):
        return dim_color(color, factor)

    def _hud_track_pulses(self):
        now = pygame.time.get_ticks()
        cur_score = self._player.get_score()
        if cur_score != self._hud_last_score:
            self._hud_score_delta = cur_score - self._hud_last_score
            self._hud_score_pulse_ms = now
            self._hud_last_score = cur_score
        cur_done = len(self._completed_portals)
        if cur_done != self._hud_last_completed:
            self._hud_portal_pulse_ms = now
            self._hud_last_completed = cur_done

    def _hud_pulse(self, start_ms, duration=520):
        if start_ms < 0:
            return 0.0
        elapsed = pygame.time.get_ticks() - start_ms
        if elapsed < 0 or elapsed >= duration:
            return 0.0
        return 1.0 - elapsed / duration

    def _draw_hud(self):
        self._hud_track_pulses()

        color = NEON_CYAN
        dim = self._hud_dim(color, 0.45)
        dimmer = self._hud_dim(color, 0.22)
        label_dim = (140, 142, 148)

        hud_w = SCREEN_WIDTH - self.HUD_MARGIN_X * 2
        hud_x = self.HUD_MARGIN_X
        hud_y = SCREEN_HEIGHT - self.HUD_HEIGHT - self.HUD_MARGIN_BOTTOM
        hud_rect = pygame.Rect(hud_x, hud_y, hud_w, self.HUD_HEIGHT)

        self._screen.blit(self._hud_bg_surf, hud_rect.topleft)

        self._draw_hud_title_bar(hud_rect, color, dim)

        content_rect = pygame.Rect(
            hud_x, hud_y + self.HUD_TITLE_HEIGHT,
            hud_w, self.HUD_HEIGHT - self.HUD_TITLE_HEIGHT,
        )
        self._draw_hud_sections(content_rect, color, dimmer, label_dim)

        # Border + corners + scanlines on top
        pygame.draw.rect(self._screen, color, hud_rect, 2)
        draw_corner_accents(self._screen, hud_rect, color)
        self._draw_hud_scanlines(hud_rect)

    def _draw_hud_title_bar(self, hud_rect, color, dim):
        title_bar = pygame.Rect(hud_rect.x, hud_rect.y, hud_rect.w, self.HUD_TITLE_HEIGHT)
        self._screen.blit(self._hud_title_tint_surf, title_bar.topleft)
        pygame.draw.line(
            self._screen, dim,
            (title_bar.left, title_bar.bottom - 1),
            (title_bar.right, title_bar.bottom - 1), 1,
        )

        self._screen.blit(self._hud_chip_surf, (hud_rect.x + 18, hud_rect.y + 8))

        prompt_surf = self._hud_prompt_surf
        self._screen.blit(
            prompt_surf,
            (hud_rect.centerx - prompt_surf.get_width() // 2, hud_rect.y + 8),
        )

        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        status_surf = self._hud_sys_bright_surf if blink else self._hud_sys_dim_surf
        sx = hud_rect.right - 18 - status_surf.get_width()
        self._screen.blit(status_surf, (sx, hud_rect.y + 8))
        if blink:
            pygame.draw.circle(self._screen, color, (sx - 10, hud_rect.y + 16), 4)

    def _draw_hud_sections(self, content, color, dimmer, label_dim):
        sections = ("OPERATOR", "SCORE", "PORTALS", "CONTROLS")
        weights = (0.22, 0.16, 0.22, 0.40)
        widths = [int(content.w * w) for w in weights]
        widths[-1] = content.w - sum(widths[:-1])

        x_cursor = content.x
        for i, (label, sw) in enumerate(zip(sections, widths)):
            sect = pygame.Rect(x_cursor, content.y, sw, content.h)
            self._screen.blit(self._hud_section_label_surfs[i], (sect.x + 18, sect.y + 8))

            if label == "OPERATOR":
                self._draw_hud_operator(sect, color)
            elif label == "SCORE":
                self._draw_hud_score(sect)
            elif label == "PORTALS":
                self._draw_hud_portals(sect, color)
            elif label == "CONTROLS":
                self._draw_hud_controls(sect, color, label_dim)

            x_cursor += sw
            if i < len(sections) - 1:
                pygame.draw.line(
                    self._screen, dimmer,
                    (x_cursor, content.y + 8),
                    (x_cursor, content.bottom - 8), 1,
                )

    def _draw_hud_operator(self, sect, color):
        name = self._player.get_name()
        name_surf = self._font_code_bold.render(name, True, WHITE)
        self._screen.blit(name_surf, (sect.x + 18, sect.y + 30))
        meta = f"lvl.{self._player.get_level_reached():02d}  /  tasks.{self._player.get_tasks_completed():02d}"
        meta_surf = self._font_code_small.render(meta, True, self._hud_dim(color, 0.55))
        self._screen.blit(meta_surf, (sect.x + 18, sect.y + 56))

    def _draw_hud_score(self, sect):
        pulse = self._hud_pulse(self._hud_score_pulse_ms)
        base = NEON_YELLOW
        if pulse > 0:
            target = NEON_GREEN if self._hud_score_delta >= 0 else NEON_RED
            score_color = tuple(int(base[i] * (1 - pulse) + target[i] * pulse) for i in range(3))
        else:
            score_color = base

        cur = self._player.get_score()
        text = f"{cur:0>5}"
        surf = self._font_code_bold.render(text, True, score_color)

        if pulse > 0:
            self._score_halo_surf.fill((score_color[0], score_color[1], score_color[2], int(70 * pulse)))
            self._screen.blit(self._score_halo_surf, (sect.x + 18 - 14, sect.y + 30 - 7))

        self._screen.blit(surf, (sect.x + 18, sect.y + 30))

        if pulse > 0:
            sign = "+" if self._hud_score_delta >= 0 else ""
            delta_surf = self._font_code_small.render(
                f"{sign}{self._hud_score_delta} pts", True, score_color
            )
            self._screen.blit(delta_surf, (sect.x + 18, sect.y + 56))

    def _draw_hud_portals(self, sect, color):
        completed = len(self._completed_portals)
        portal_colors = (NEON_RED, NEON_YELLOW, NEON_GREEN)
        seg_w, seg_h, seg_gap = 38, 14, 8
        world_label = self._font_code_small.render(
            f"WORLD {self._world_index + 1}", True, (0, 140, 140)
        )
        self._screen.blit(world_label, (sect.x + 18, sect.y + 20))
        seg_y = sect.y + 50
        pulse = self._hud_pulse(self._hud_portal_pulse_ms, duration=700)

        for i in range(3):
            seg_rect = pygame.Rect(sect.x + 18 + i * (seg_w + seg_gap), seg_y, seg_w, seg_h)
            if i < completed:
                pygame.draw.rect(self._screen, portal_colors[i], seg_rect)
                pygame.draw.line(
                    self._screen, WHITE,
                    (seg_rect.x + 2, seg_rect.y + 2),
                    (seg_rect.right - 3, seg_rect.y + 2), 1,
                )
                # glow halo on the most recent fill
                if pulse > 0 and i == completed - 1:
                    self._portal_halo_surf.fill((
                        portal_colors[i][0], portal_colors[i][1], portal_colors[i][2],
                        int(80 * pulse),
                    ))
                    self._screen.blit(self._portal_halo_surf, (seg_rect.x - 7, seg_rect.y - 7))
            else:
                pygame.draw.rect(self._screen, self._hud_dim(portal_colors[i], 0.3), seg_rect, 1)

        count_surf = self._font_code.render(f"{completed} / {self._world.get_portal_count()}", True, color)
        seg_total_w = 3 * seg_w + 2 * seg_gap
        self._screen.blit(count_surf, (sect.x + 18 + seg_total_w + 14, seg_y - 4))

    def _draw_hud_controls(self, sect, color, label_dim):
        x = sect.x + 18
        for surf in self._ctrl_surfs_row1:
            self._screen.blit(surf, (x, sect.y + 32))
            x += surf.get_width()
        x = sect.x + 18
        for surf in self._ctrl_surfs_row2:
            self._screen.blit(surf, (x, sect.y + 56))
            x += surf.get_width()

    def _draw_hud_scanlines(self, rect):
        self._screen.blit(self._hud_scanline_surf, rect.topleft)

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
        if self._correct_flash_timer > 0:
            self._draw_correct_flash(layout)

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
        dim_color_hint = tuple(int(c * 0.45) for c in color)

        task = self._current_level.get_current_task()
        hint_text = task.get_hint() if task else ""

        if hint_text:
            if self._hint_revealed:
                label_col = color
                text_col = WHITE
                prefix = "HINT: "
                bg_alpha = 60
            else:
                label_col = dim_color_hint
                text_col = (90, 92, 96)
                prefix = "HINT: "
                bg_alpha = 0

            label_surf = self._font_code_small.render(prefix, True, label_col)
            hint_surf = self._font_code_small.render(hint_text, True, text_col)
            total_hw = label_surf.get_width() + hint_surf.get_width()
            hx = rect.centerx - total_hw // 2
            hy = rect.y

            if self._hint_revealed and bg_alpha > 0:
                bg = pygame.Surface((total_hw + 24, label_surf.get_height() + 6), pygame.SRCALPHA)
                bg.fill((color[0], color[1], color[2], bg_alpha))
                self._screen.blit(bg, (hx - 12, hy - 2))

            self._screen.blit(label_surf, (hx, hy))
            self._screen.blit(hint_surf, (hx + label_surf.get_width(), hy))

        parts = [
            ("[ENTER]", color), (" execute    ", dim_text),
            ("[ESC]",   color), (" disconnect    ", dim_text),
            ("[TAB]",   color), (" skip",            dim_text),
        ]
        total_w = sum(self._font_code_small.size(t)[0] for t, _ in parts)
        x = rect.centerx - total_w // 2
        y = rect.y + 26
        for text, c in parts:
            surf = self._font_code_small.render(text, True, c)
            self._screen.blit(surf, (x, y))
            x += surf.get_width()

    def _draw_death_flash(self):
        t = self._death_flash_timer
        # 0-90: fade in over first 15 frames, hold, fade out over last 30
        if t > 75:
            frac = (90 - t) / 15.0        # 0 → 1 as t goes 90 → 75
        elif t > 30:
            frac = 1.0
        else:
            frac = t / 30.0               # 1 → 0 as t goes 30 → 0

        frac = max(0.0, min(1.0, frac))

        self._death_overlay_surf.fill((180, 0, 0, int(180 * frac)))
        self._screen.blit(self._death_overlay_surf, (0, 0))

        self._death_stripe_surf.fill((0, 0, 0, 0))
        for sy in range(0, SCREEN_HEIGHT, 6):
            pygame.draw.line(self._death_stripe_surf, (0, 0, 0, int(60 * frac)), (0, sy), (SCREEN_WIDTH, sy))
        self._screen.blit(self._death_stripe_surf, (0, 0))

        c = tuple(int(ch * frac) for ch in NEON_RED)

        killed_surf = self._font_huge.render("NĀVE", True, c)
        killed_rect = killed_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 44))
        self._screen.blit(killed_surf, killed_rect)

        # Points deducted
        pts_surf = self._font_big.render(f"-{self._death_flash_points} pts", True, c)
        pts_rect = pts_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 32))
        self._screen.blit(pts_surf, pts_rect)

        # Corner accent lines
        al = 32
        for cx, cy, dx, dy in [
            (0, 0, 1, 1),
            (SCREEN_WIDTH - 1, 0, -1, 1),
            (0, SCREEN_HEIGHT - 1, 1, -1),
            (SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1, -1, -1),
        ]:
            pygame.draw.line(self._screen, c, (cx, cy), (cx + dx * al, cy), 3)
            pygame.draw.line(self._screen, c, (cx, cy), (cx, cy + dy * al), 3)

        # Thin red border
        pygame.draw.rect(self._screen, c, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

    def _draw_win_screen(self):
        self._screen.blit(self._fullscreen_dark_surf, (0, 0))

        win_text = self._font_huge.render("UZVARA!", True, NEON_GREEN)
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self._screen.blit(win_text, win_rect)

        score_text = self._font_big.render(f"Punkti: {self._player.get_score()}", True, NEON_YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self._screen.blit(score_text, score_rect)

        worlds_text = self._font.render(f"Pasaules: {self._world_index}", True, WHITE)
        worlds_rect = worlds_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self._screen.blit(worlds_text, worlds_rect)

        portals_text = self._font.render("Pabeigti visi 3 portāli!", True, WHITE)
        portals_rect = portals_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self._screen.blit(portals_text, portals_rect)

        hint = self._font.render("ENTER: turpināt (ENDLESS) | ESC: iziet", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 160))
        self._screen.blit(hint, hint_rect)

    def _draw_transition_screen(self):
        self._screen.blit(self._fullscreen_dark_surf, (0, 0))

        nwi = self._next_world_index
        if nwi < len(WORLD_LABELS):
            title_text = f"WORLD {nwi + 1}"
            label_text = WORLD_LABELS[nwi]
        else:
            loop_n = nwi - len(WORLD_LABELS) + 1
            title_text = "ENDLESS"
            label_text = f"ENDLESS // LOOP_{loop_n}"

        title_surf = self._font_huge.render(title_text, True, NEON_CYAN)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self._screen.blit(title_surf, title_rect)

        dim_cyan = (0, 140, 140)
        label_surf = self._font_big.render(label_text, True, dim_cyan)
        label_rect = label_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(label_surf, label_rect)

        score_surf = self._font.render(f"Punkti: {self._player.get_score()}", True, NEON_YELLOW)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self._screen.blit(score_surf, score_rect)

    def _draw_game_over_screen(self):
        self._screen.blit(self._fullscreen_dark_surf, (0, 0))

        gg_text = self._font_huge.render("SPĒLE BEIGUSIES", True, NEON_RED)
        gg_rect = gg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(gg_text, gg_rect)


if __name__ == "__main__":
    pygame.init()
    game = Game("TestSpēlētājs")
    game.run()
    pygame.quit()
