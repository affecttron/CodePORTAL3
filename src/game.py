import pygame
import os
import random
from player import Player
from player_sprite import PlayerSprite
from world import World
from camera import Camera
from tile_registry import TileRegistry
from parallax_background import ParallaxBackground
from rain import Rain
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
    PORTAL_THEME_COLORS,
)
from ui_utils import dim_color, draw_corner_accents


STATE_PLAYING = "playing"
STATE_TASK = "task"
STATE_GAME_OVER = "game_over"
STATE_WIN = "win"
STATE_TRANSITION = "transition"
STATE_PAUSED = "paused"
STATE_LEADERBOARD = "leaderboard"


class Game:

    # Inicializē visu spēles sistēmu
    def __init__(self, player_name="Spēlētājs"):
        self._init_pipeline()
        self._init_fonts()

        self._player = Player(player_name)
        self._endless_mode = False

        self._init_world()

        self._score_log = ScoreLog()
        self._sound = SoundManager()
        self._sound.play_music()
        self._sound.start_ambience()
        self._win_sound_played = False

        self._init_state()
        self._init_surfaces()

    def _init_pipeline(self):
        self._pipeline = ShaderPipeline.create(
            (SCREEN_WIDTH, SCREEN_HEIGHT), fullscreen=FULLSCREEN, shader="cyberpunk",
            display_size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
        )
        self._screen = self._pipeline.surface
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()

    def _init_fonts(self):
        self._font_huge       = pygame.font.SysFont("bahnschrift", 64, bold=True)
        self._font_big        = pygame.font.SysFont("bahnschrift", 36, bold=True)
        self._font            = pygame.font.SysFont("bahnschrift", 24)
        self._font_code       = pygame.font.SysFont("bahnschrift", 20)
        self._font_code_bold  = pygame.font.SysFont("bahnschrift", 20, bold=True)
        self._font_code_small = pygame.font.SysFont("bahnschrift", 15, bold=True)
        self._font_small      = pygame.font.SysFont("bahnschrift", 18)

    def _init_world(self):
        self._registry = TileRegistry()
        self._registry.load()
        self._world = World(registry=self._registry)
        self._load_world()

        spawn_x, spawn_y = self._world.get_spawn_position()
        self._player_sprite = PlayerSprite(spawn_x, spawn_y)
        self._camera = Camera()
        self._camera.set_target(self._player_sprite)

        self._parallax = ParallaxBackground()
        self._parallax.create_cyberpunk_scene()
        self._rain = Rain()

    def _init_state(self):
        self._state = STATE_PLAYING
        self._running = True
        pygame.key.stop_text_input()

        self._transition_timer = 0
        self._next_world_index = 1

        self._pause_selection = 0
        self._pause_items = [("RESUME", "turpināt spēli"), ("LEADERBOARD", "labākie rezultāti"), ("QUIT", "iziet")]
        self._pause_item_rects = []   # aizpilda _draw_pause_menu, klikšķu pārbaudei
        self._lb_panel_rect: pygame.Rect | None = None  # aizpilda _draw_leaderboard

        self._leaderboard_cache = None
        self._leaderboard_stats = None   # kopā spēles, vidējais rezultāts

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
        self._respawn_delay = 0
        self._respawn_spawn = (0, 0)

        self._access_denied_timer = 0

        self._backspace_held_frames = 0
        self._BACKSPACE_INITIAL_DELAY = 25
        self._BACKSPACE_REPEAT_RATE = 3

        self._hud_last_score = self._player.get_score()
        self._hud_score_pulse_ms = -10000
        self._hud_score_delta = 0
        self._hud_last_completed = 0
        self._hud_portal_pulse_ms = -10000

    def _init_surfaces(self):
        # Iepriekš piešķirtas pārklājuma virsmas
        _flash_w = 1100 - 2 * 26   # paneļa platums bez ietvarēm
        _flash_h = 360 + 12 + 32   # koda bloks plus overclock joslas augstums
        self._correct_flash_surf = pygame.Surface((_flash_w, _flash_h), pygame.SRCALPHA)

        self._death_overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._death_stripe_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self._access_denied_overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._access_denied_stripe_surf  = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        self._fullscreen_dark_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._fullscreen_dark_surf.fill((0, 0, 0, 220))

        # HUD virsmas, izveidotas vienu reizi
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
            ("[A/D]",    NEON_CYAN), (" staigāt  ",  _label_dim),
            ("[SHIFT]",  NEON_CYAN), (" sprint  ",   _label_dim),
            ("[SPACE]",  NEON_CYAN), (" lekt  ",     _label_dim),
            ("[W/S]",    NEON_CYAN), (" rāpties",    _label_dim),
        ]
        _row2_data = [
            ("[R]",   NEON_CYAN), (" respawn  ", _label_dim),
            ("[F1]",  NEON_CYAN), (" FX  ",      _label_dim),
            ("[F9]",  NEON_CYAN), (" skip  ",    _label_dim),
            ("[ESC]", NEON_CYAN), (" pauze",      _label_dim),
        ]
        self._ctrl_surfs_row1 = [self._font_code_small.render(t, True, c) for t, c in _row1_data]
        self._ctrl_surfs_row2 = [self._font_code_small.render(t, True, c) for t, c in _row2_data]

    # Ielādē pasauli pēc indeksa
    def _load_world(self, world_index=0):
        self._world_index = world_index
        self._current_world_config = get_world_config(world_index)

        # Endless režīmā izvēlas nejaušus uzdevumu ID
        if self._endless_mode:
            self._current_world_config = dict(self._current_world_config)
            self._current_world_config["level_ids"] = random.sample(range(1, 10), 3)

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
        self._world_score_start = self._player.get_score()

    # Galvenā spēles cilpa
    def run(self):
        try:
            while self._running:
                self._handle_events()
                self._update()
                self._draw()
                self._clock.tick(FPS)
        finally:
            self._sound.stop_music()
            self._sound.stop_ambience()
            self._score_log.save_score(self._player)
            self._pipeline.shutdown()

    # Apstrādā visus pygame notikumus
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._state == STATE_TASK:
                        self._close_task_cancel()
                    elif self._state == STATE_LEADERBOARD:
                        self._state = STATE_PAUSED
                    elif self._state == STATE_PAUSED:
                        self._state = STATE_PLAYING
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    elif self._state == STATE_PLAYING:
                        self._pause_selection = 0
                        self._state = STATE_PAUSED
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
                        if self._current_level and self._current_level.is_typewriter_complete():
                            self._input_text = self._input_text[:-1]

                elif self._state == STATE_PAUSED:
                    n = len(self._pause_items)
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self._pause_selection = (self._pause_selection - 1) % n
                        self._sound.play_sound("menu_click")
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self._pause_selection = (self._pause_selection + 1) % n
                        self._sound.play_sound("menu_click")
                    elif event.key == pygame.K_RETURN:
                        self._activate_pause_selection()

                elif self._state == STATE_LEADERBOARD:
                    if event.key == pygame.K_RETURN:
                        self._state = STATE_PAUSED

                elif self._state == STATE_WIN:
                    if event.key == pygame.K_RETURN:
                        self._endless_mode = True
                        self._load_world(3)
                        spawn_x, spawn_y = self._world.get_spawn_position()
                        self._player_sprite.respawn(spawn_x, spawn_y)
                        self._state = STATE_PLAYING
                elif self._state == STATE_GAME_OVER:
                    if event.key == pygame.K_RETURN:
                        self._running = False

            # TEXTINPUT ļauj ievadīt latviešu burtus
            if event.type == pygame.TEXTINPUT:
                typewriter_done = not self._current_level or self._current_level.is_typewriter_complete()
                if self._state == STATE_TASK and self._correct_flash_timer == 0 and typewriter_done and len(self._input_text) < 50:
                    self._input_text += event.text

            # Peles virzīšana
            if event.type == pygame.MOUSEMOTION:
                mx, my = self._pipeline.scale_mouse_pos(event.pos)
                if self._state == STATE_PAUSED and self._pause_item_rects:
                    hit = False
                    for i, rect in enumerate(self._pause_item_rects):
                        if rect.collidepoint(mx, my):
                            if i != self._pause_selection:
                                self._pause_selection = i
                                self._sound.play_sound("menu_click")
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                            hit = True
                            break
                    if not hit:
                        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = self._pipeline.scale_mouse_pos(event.pos)
                if self._state == STATE_PAUSED and self._pause_item_rects:
                    for i, rect in enumerate(self._pause_item_rects):
                        if rect.collidepoint(mx, my):
                            self._pause_selection = i
                            self._activate_pause_selection()
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                            break
                elif self._state == STATE_LEADERBOARD:
                    if self._lb_panel_rect and self._lb_panel_rect.collidepoint(mx, my):
                        self._state = STATE_PAUSED

    # Apstrādā turētus kustības taustiņus
    def _handle_continuous_input(self):
        if self._state != STATE_PLAYING:
            return
        if self._respawn_delay > 0:
            return

        keys = pygame.key.get_pressed()
        is_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Kustība
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._player_sprite.move_left(sprint=is_sprint)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._player_sprite.move_right(sprint=is_sprint)
        else:
            self._player_sprite.stop()

        # Rāpšanās (W=augšup, S=lejup)
        if keys[pygame.K_w]:
            self._player_sprite.climb_up()
        elif keys[pygame.K_s]:
            self._player_sprite.climb_down()
        else:
            self._player_sprite.stop_climbing()

    # Apstrādā turēto backspace uzdevuma ievadē
    def _handle_task_hold_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_BACKSPACE]:
            self._backspace_held_frames += 1
            if self._backspace_held_frames > self._BACKSPACE_INITIAL_DELAY:
                if (self._backspace_held_frames - self._BACKSPACE_INITIAL_DELAY) % self._BACKSPACE_REPEAT_RATE == 0:
                    self._input_text = self._input_text[:-1]
        else:
            self._backspace_held_frames = 0

    # Atjaunina spēles loģiku kadrā
    def _update(self):
        # Pauzētā stāvoklī pasaule netiek atjaunināta
        if self._state in (STATE_PAUSED, STATE_LEADERBOARD):
            return

        if self._state == STATE_PLAYING:
            self._handle_continuous_input()
            self._update_playing()
        elif self._state == STATE_TASK:
            self._handle_task_hold_input()
            if self._correct_flash_timer > 0:
                self._correct_flash_timer -= 1
                if self._correct_flash_timer == 0 and self._pending_next_task and self._current_level is not None:
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

        if self._respawn_delay > 0:
            self._respawn_delay -= 1
            if self._respawn_delay == 0:
                sx, sy = self._respawn_spawn
                self._player_sprite.respawn(sx, sy)
                self._player_sprite.clear_death_anim()

        if self._death_flash_timer > 0:
            self._death_flash_timer -= 1

        if self._access_denied_timer > 0:
            self._access_denied_timer -= 1

        if self._portal_cooldown > 0:
            self._portal_cooldown -= 1

        self._sound.update_ambience()

    # Atjaunina aktīvās spēles fiziku un sadursmes
    def _update_playing(self):
        self._player_sprite.update(
            self._world.get_solid_rects(),
            self._world.get_climbable_rects(),
        )
        self._camera.update()
        self._rain.update()

        hazard = self._world.check_hazard_collision(self._player_sprite.get_rect())
        if hazard and self._death_flash_timer == 0:
            self._sound.play_sound("death")
            spawn_x, spawn_y = self._world.get_spawn_position()
            self._player_sprite.start_death_anim()
            self._player_sprite.stop()
            self._player.deduct_score(self._death_flash_points)
            self._death_flash_timer = 90
            self._respawn_delay = 40
            self._respawn_spawn = (spawn_x, spawn_y)
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

    # Atjaunina pārejas animācijas taimeri
    def _update_transition(self):
        self._transition_timer += 1
        # Pēc 2. pasaules durvis ved uz uzvaras ekrānu
        if self._next_world_index == 3 and not self._endless_mode:
            if self._transition_timer >= 30:
                self._state = STATE_WIN
            return
        # Parāda titulkarti, ielādē nākamo pasauli
        if self._transition_timer >= 121:
            self._load_world(self._next_world_index)
            spawn_x, spawn_y = self._world.get_spawn_position()
            self._player_sprite.respawn(spawn_x, spawn_y)
            self._portal_cooldown = 60
            self._state = STATE_PLAYING

    # Atver uzdevuma paneli portāla aktivizēšanai
    def _open_task(self, portal):
        portal_slot = portal.get_level_id() - 1
        level_ids = self._current_world_config.get("level_ids", [1, 2, 3])
        level_id = level_ids[portal_slot] if 0 <= portal_slot < len(level_ids) else portal.get_level_id()
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

    # Iesniedz atbildi un vērtē rezultātu
    def _submit_answer(self):
        if not self._input_text.strip():
            return
        if self._current_level is None:
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
            self._access_denied_timer = 45
            self._pipeline.pulse_glitch(0.6)

            self._hint_revealed = True
            self._hint_text = task.get_hint()

            if not self._player.has_attempts_left():
                self._show_feedback("Parāk daudz kļūdu!", NEON_RED)
                self._pipeline.pulse_glitch(1.0)
                self._close_task_fail()
            else:
                remaining = self._current_world_config["max_attempts"] - attempts
                self._show_feedback(f"Nepareizi! Vel {remaining} meginjums. -5 pts", NEON_YELLOW)
                self._pipeline.pulse_glitch(0.45)
                self._input_text = ""

    # Aizver uzdevumu pēc veiksmīgas pabeigšanas
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

    # Aizver uzdevumu un beidz spēli
    def _close_task_fail(self):
        self._return_to_playing()
        self._state = STATE_GAME_OVER

    # Aizver uzdevumu bez rezultāta
    def _close_task_cancel(self):
        self._return_to_playing()

    # Atgriežas spēlē no uzdevuma paneļa
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

        # Attālo spēlētāju no portāla
        self._player_sprite.nudge(-100)

    # Izlaiž visu pasauli atkļūdošanai
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

    # Izpilda izvēlēto pauzes punktu
    def _activate_pause_selection(self):
        self._sound.play_sound("menu_click")
        sel = self._pause_selection
        if sel == 0:                          # Turpināt
            self._state = STATE_PLAYING
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        elif sel == 1:                        # Rezultātu tabula
            self._leaderboard_cache = None    # ielādē no jauna
            self._leaderboard_stats = None
            self._state = STATE_LEADERBOARD
        elif sel == 2:                        # Iziet
            self._running = False

    # Parāda statusu ziņojumu ekrānā
    def _show_feedback(self, msg, color):
        self._feedback_message = msg
        self._feedback_color = color
        self._feedback_timer = 180

    # Zīmē pašreizējo spēles stāvokli
    def _draw(self):
        if self._state == STATE_PLAYING:
            self._draw_playing()
        elif self._state == STATE_TASK:
            self._draw_playing()
            self._draw_task_ui()
            if self._access_denied_timer > 0:
                self._draw_access_denied_flash()
        elif self._state == STATE_PAUSED:
            self._draw_playing()
            self._draw_pause_menu()
        elif self._state == STATE_LEADERBOARD:
            self._draw_playing()
            self._draw_leaderboard()
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

    # Zīmē pareizas atbildes mirgoņas efektu
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

    # Zīmē pasauli, spēlētāju un HUD
    def _draw_playing(self):
        cam_x, cam_y = self._camera.get_offset()
        self._parallax.draw(self._screen, cam_x, cam_y)
        self._rain.draw(self._screen)
        self._world.draw(self._screen, cam_x, cam_y)
        self._player_sprite.draw(self._screen, cam_x, cam_y)
        self._camera.apply_motion_blur(self._screen)
        self._draw_hud()

        if self._feedback_timer > 0:
            self._draw_feedback()
        if self._death_flash_timer > 0:
            self._draw_death_flash()

    # HUD josla apakšā

    HUD_MARGIN_X = 32
    HUD_MARGIN_BOTTOM = 24
    HUD_HEIGHT = 112
    HUD_TITLE_HEIGHT = 32
    HUD_BG = (10, 12, 16, 215)

    # Aptumšo HUD krāsu
    def _hud_dim(self, color, factor):
        return dim_color(color, factor)

    # Izseko punktu un portālu izmaiņas pulsam
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

    # Aprēķina pulsācijas intensitāti pēc laika
    def _hud_pulse(self, start_ms, duration=520):
        if start_ms < 0:
            return 0.0
        elapsed = pygame.time.get_ticks() - start_ms
        if elapsed < 0 or elapsed >= duration:
            return 0.0
        return 1.0 - elapsed / duration

    # Zīmē visu HUD joslu apakšā
    def _draw_hud(self):
        self._hud_track_pulses()

        color = NEON_CYAN
        dim = self._hud_dim(color, 0.45)
        dimmer = self._hud_dim(color, 0.22)

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
        self._draw_hud_sections(content_rect, color, dimmer)

        # Rāmis, stūri un skenlīnijas
        pygame.draw.rect(self._screen, color, hud_rect, 2)
        draw_corner_accents(self._screen, hud_rect, color)
        self._draw_hud_scanlines(hud_rect)

    # Zīmē HUD virsrakstu joslu ar statusu
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

    # Zīmē HUD sadaļas ar dažādiem datiem
    def _draw_hud_sections(self, content, color, dimmer):
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
                self._draw_hud_controls(sect)

            x_cursor += sw
            if i < len(sections) - 1:
                pygame.draw.line(
                    self._screen, dimmer,
                    (x_cursor, content.y + 8),
                    (x_cursor, content.bottom - 8), 1,
                )

    # Zīmē spēlētāja vārdu un līmeni HUD
    def _draw_hud_operator(self, sect, color):
        name = self._player.get_name()
        name_surf = self._font_code_bold.render(name, True, WHITE)
        self._screen.blit(name_surf, (sect.x + 18, sect.y + 30))
        meta = f"lvl.{self._player.get_level_reached():02d}  /  tasks.{self._player.get_tasks_completed():02d}"
        meta_surf = self._font_code_small.render(meta, True, self._hud_dim(color, 0.55))
        self._screen.blit(meta_surf, (sect.x + 18, sect.y + 56))

    # Zīmē punktu skaitu ar pulsācijas efektu
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

    # Zīmē portālu progresu HUD joslas segmentos
    def _draw_hud_portals(self, sect, color):
        completed = len(self._completed_portals)
        portal_colors = PORTAL_THEME_COLORS
        seg_w, seg_h, seg_gap = 38, 14, 8
        world_label = self._font_code_small.render(
            f"WORLD {self._world_index + 1}", True, (0, 140, 140)
        )
        self._screen.blit(world_label, (sect.x + 18, sect.y + 20))
        seg_y = sect.y + 50
        pulse = self._hud_pulse(self._hud_portal_pulse_ms, duration=700)
        total_portals = self._world.get_portal_count()

        portals = self._world.get_portals()
        for i in range(total_portals):
            lvl_id = portals[i].get_level_id() if i < len(portals) else (i + 1)
            seg_color = portal_colors.get(lvl_id, NEON_CYAN)
            seg_rect = pygame.Rect(sect.x + 18 + i * (seg_w + seg_gap), seg_y, seg_w, seg_h)
            if i < completed:
                pygame.draw.rect(self._screen, seg_color, seg_rect)
                pygame.draw.line(
                    self._screen, WHITE,
                    (seg_rect.x + 2, seg_rect.y + 2),
                    (seg_rect.right - 3, seg_rect.y + 2), 1,
                )
                # Spīdums pēdējam aizpildītajam portālam
                if pulse > 0 and i == completed - 1:
                    self._portal_halo_surf.fill((
                        seg_color[0], seg_color[1], seg_color[2],
                        int(80 * pulse),
                    ))
                    self._screen.blit(self._portal_halo_surf, (seg_rect.x - 7, seg_rect.y - 7))
            else:
                pygame.draw.rect(self._screen, self._hud_dim(seg_color, 0.3), seg_rect, 1)

        count_surf = self._font_code.render(f"{completed} / {total_portals}", True, color)
        seg_total_w = total_portals * seg_w + (total_portals - 1) * seg_gap
        self._screen.blit(count_surf, (sect.x + 18 + seg_total_w + 14, seg_y - 4))

    # Zīmē vadības pogu padomus
    def _draw_hud_controls(self, sect):
        x = sect.x + 18
        for surf in self._ctrl_surfs_row1:
            self._screen.blit(surf, (x, sect.y + 32))
            x += surf.get_width()
        x = sect.x + 18
        for surf in self._ctrl_surfs_row2:
            self._screen.blit(surf, (x, sect.y + 56))
            x += surf.get_width()

    # Zīmē HUD skenlīniju efektu
    def _draw_hud_scanlines(self, rect):
        self._screen.blit(self._hud_scanline_surf, rect.topleft)

    # Zīmē atgriezeniskās saites ziņojumu
    def _draw_feedback(self):
        text = self._font_big.render(self._feedback_message, True, self._feedback_color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 120))

        bg = text_rect.inflate(40, 20)
        pygame.draw.rect(self._screen, BLACK, bg)
        pygame.draw.rect(self._screen, self._feedback_color, bg, 3)

        self._screen.blit(text, text_rect)

    # Zīmē uzdevuma paneli ar ievadi
    def _draw_task_ui(self):
        if self._current_level is None:
            return

        layout = self._current_level.display_task(
            self._screen, self._font_code,
            attempts=self._player.get_attempts(),
            max_attempts=self._current_world_config["max_attempts"],
        )
        if layout is None:
            return

        self._draw_terminal_input(layout)
        self._draw_terminal_hints(layout)
        if self._correct_flash_timer > 0:
            self._draw_correct_flash(layout)

    # Zīmē termināla ievades lauku ar kursoru
    def _draw_terminal_input(self, layout):
        if self._current_level is None:
            return
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

    # Zīmē padomu un vadības palīdzību
    def _draw_terminal_hints(self, layout):
        if self._current_level is None:
            return
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

    # Zīmē nāves sarkano pārklājumu
    def _draw_death_flash(self):
        t = self._death_flash_timer
        # Ienāk 15 kadros, tur, iziet 30 kadros
        if t > 75:
            frac = (90 - t) / 15.0        # 0 uz 1 kad t no 90 uz 75
        elif t > 30:
            frac = 1.0
        else:
            frac = t / 30.0               # 1 uz 0 kad t no 30 uz 0

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

        # Atskaitītie punkti
        pts_surf = self._font_big.render(f"-{self._death_flash_points} pts", True, c)
        pts_rect = pts_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 32))
        self._screen.blit(pts_surf, pts_rect)

        # Stūru akcenta līnijas
        al = 32
        for cx, cy, dx, dy in [
            (0, 0, 1, 1),
            (SCREEN_WIDTH - 1, 0, -1, 1),
            (0, SCREEN_HEIGHT - 1, 1, -1),
            (SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1, -1, -1),
        ]:
            pygame.draw.line(self._screen, c, (cx, cy), (cx + dx * al, cy), 3)
            pygame.draw.line(self._screen, c, (cx, cy), (cx, cy + dy * al), 3)

        # Plāna sarkana apmale
        pygame.draw.rect(self._screen, c, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

    # Zīmē piekļuves lieguma uzliesmojumu
    def _draw_access_denied_flash(self):
        t = self._access_denied_timer
        if t > 35:
            frac = (45 - t) / 10.0
        elif t > 15:
            frac = 1.0
        else:
            frac = t / 15.0
        frac = max(0.0, min(1.0, frac))

        self._access_denied_overlay_surf.fill((200, 0, 0, int(170 * frac)))
        self._screen.blit(self._access_denied_overlay_surf, (0, 0))

        self._access_denied_stripe_surf.fill((0, 0, 0, 0))
        for sy in range(0, SCREEN_HEIGHT, 8):
            pygame.draw.line(self._access_denied_stripe_surf, (0, 0, 0, int(70 * frac)), (0, sy), (SCREEN_WIDTH, sy))
        self._screen.blit(self._access_denied_stripe_surf, (0, 0))

        c = tuple(int(ch * frac) for ch in NEON_RED)

        denied_surf = self._font_huge.render("ACCESS DENIED", True, c)
        denied_rect = denied_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 44))
        self._screen.blit(denied_surf, denied_rect)

        pts_surf = self._font_big.render("-5 pts", True, c)
        pts_rect = pts_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 36))
        self._screen.blit(pts_surf, pts_rect)

        al = 32
        for cx, cy, dx, dy in [
            (0, 0, 1, 1),
            (SCREEN_WIDTH - 1, 0, -1, 1),
            (0, SCREEN_HEIGHT - 1, 1, -1),
            (SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1, -1, -1),
        ]:
            pygame.draw.line(self._screen, c, (cx, cy), (cx + dx * al, cy), 3)
            pygame.draw.line(self._screen, c, (cx, cy), (cx, cy + dy * al), 3)

        pygame.draw.rect(self._screen, c, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

    # Zīmē uzvaras ekrānu
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

    # Zīmē pasaules pārejas karti
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

        total_score = self._player.get_score()
        world_delta = total_score - self._world_score_start
        score_surf = self._font.render(f"Kopā: {total_score}", True, NEON_YELLOW)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self._screen.blit(score_surf, score_rect)

        if world_delta > 0:
            delta_surf = self._font_code_small.render(
                f"+{world_delta} šajā pasaulē", True, NEON_GREEN
            )
            self._screen.blit(delta_surf,
                               delta_surf.get_rect(center=(SCREEN_WIDTH // 2,
                                                            SCREEN_HEIGHT // 2 + 126)))

    # Zīmē spēles beigšanās ekrānu
    def _draw_game_over_screen(self):
        self._screen.blit(self._fullscreen_dark_surf, (0, 0))

        gg_text = self._font_huge.render("SPĒLE BEIGUSIES", True, NEON_RED)
        gg_rect = gg_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self._screen.blit(gg_text, gg_rect)

    # PAUZES IZVĒLNE

    _PAUSE_W = 820
    _PAUSE_H = 520
    _PAUSE_TITLE_H = 50

    # Zīmē pauzes izvēlni ar statusu
    def _draw_pause_menu(self):
        from ui_utils import draw_corner_accents  # jau importēts moduļa līmenī

        color = NEON_CYAN
        dim   = dim_color(color, 0.45)
        dimmer = dim_color(color, 0.22)

        pw, ph = self._PAUSE_W, self._PAUSE_H
        px = (SCREEN_WIDTH  - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Rect(px, py, pw, ph)

        # Tumšs pārklājums aiz paneļa
        self._screen.blit(self._fullscreen_dark_surf, (0, 0))

        # Paneļa fons
        pygame.draw.rect(self._screen, (10, 12, 16), panel)

        # Virsrakstjoslas tints
        title_bar = pygame.Rect(px, py, pw, self._PAUSE_TITLE_H)
        tint = pygame.Surface((pw, self._PAUSE_TITLE_H), pygame.SRCALPHA)
        tint.fill((color[0], color[1], color[2], 26))
        self._screen.blit(tint, title_bar.topleft)
        pygame.draw.line(self._screen, dim,
                         (title_bar.left, title_bar.bottom - 1),
                         (title_bar.right, title_bar.bottom - 1), 1)

        # Virsraksta etiķete
        chip_surf = self._font_code_bold.render("[ SYSTEM // PAUSED ]", True, color)
        self._screen.blit(chip_surf, (px + 20, py + 14))

        # Mirgojošs REC punkts
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        rec_col = color if blink else dim
        if blink:
            pygame.draw.circle(self._screen, color, (panel.right - 88, py + 25), 5)
        rec_surf = self._font_code_small.render("REC", True, rec_col)
        self._screen.blit(rec_surf, (panel.right - 76, py + 17))

        # Statusa josla ar pasaules datiem
        STATUS_H = 44
        status_y = py + self._PAUSE_TITLE_H
        status_bar = pygame.Rect(px, status_y, pw, STATUS_H)
        status_tint = pygame.Surface((pw, STATUS_H), pygame.SRCALPHA)
        status_tint.fill((color[0], color[1], color[2], 10))
        self._screen.blit(status_tint, status_bar.topleft)

        world_label  = f"WORLD {self._world_index + 1}"
        score_label  = f"SCORE  {self._player.get_score():05d}"
        total_p      = self._world.get_portal_count()
        portals_label = f"PORTALS  {len(self._completed_portals)}/{total_p}"
        status_parts = [world_label, "  //  ", score_label, "  //  ", portals_label]
        status_text  = "".join(status_parts)
        status_surf  = self._font_code_small.render(status_text, True, dim)
        self._screen.blit(status_surf,
                          status_surf.get_rect(midleft=(px + 20, status_bar.centery)))

        pygame.draw.line(self._screen, dimmer,
                         (px, status_bar.bottom - 1), (px + pw, status_bar.bottom - 1), 1)

        # Izvēlnes punkti, izveido taisnstūrus klikšķiem
        items = self._pause_items
        item_h = 72
        items_y = py + self._PAUSE_TITLE_H + STATUS_H + 20
        self._pause_item_rects = [
            pygame.Rect(px + 20, items_y + i * item_h, pw - 40, item_h - 8)
            for i in range(len(items))
        ]

        for i, (label, subtitle) in enumerate(items):
            selected = (i == self._pause_selection)
            row_y = items_y + i * item_h

            if selected:
                # Izgaismo izvēlētās rindas fonu
                hi = pygame.Surface((pw - 40, item_h - 8), pygame.SRCALPHA)
                hi.fill((color[0], color[1], color[2], 18))
                self._screen.blit(hi, (px + 20, row_y))
                pygame.draw.line(self._screen, color,
                                 (px + 20, row_y), (px + 20, row_y + item_h - 8), 3)

            arrow_col = color if selected else dimmer
            label_col = color if selected else dim
            sub_col   = dim   if selected else dimmer

            arrow_surf = self._font_code_bold.render("▶" if selected else " ", True, arrow_col)
            self._screen.blit(arrow_surf, (px + 30, row_y + 8))

            label_surf = self._font_big.render(label, True, label_col)
            self._screen.blit(label_surf, (px + 70, row_y + 4))

            sub_surf = self._font_code_small.render(subtitle, True, sub_col)
            self._screen.blit(sub_surf, (px + 72, row_y + 44))

        # Navigācijas padomi
        nav_parts = [
            ("[↑/↓]", color), ("  navigēt    ", dim),
            ("[ENTER]", color), ("  apstiprināt    ", dim),
            ("[ESC]", color), ("  turpināt", dim),
        ]
        total_w = sum(self._font_code_small.size(t)[0] for t, _ in nav_parts)
        nx = panel.centerx - total_w // 2
        ny = panel.bottom - 36
        for txt, col in nav_parts:
            s = self._font_code_small.render(txt, True, col)
            self._screen.blit(s, (nx, ny))
            nx += s.get_width()

        # Rāmis un stūri
        pygame.draw.rect(self._screen, color, panel, 2)
        draw_corner_accents(self._screen, panel, color)

    # REZULTĀTU TABULA

    _LB_W = 1160
    _LB_H = 780
    _LB_TITLE_H = 50
    _LB_COLS = (60, 340, 180, 120, 140, 260)   # rangs, vārds, punkti, līmenis, uzdevumi, datums

    # Zīmē rezultātu tabulu ar rindām
    def _draw_leaderboard(self):
        from ui_utils import draw_corner_accents

        # Ielādē rezultātus vienu reizi
        if self._leaderboard_cache is None:
            self._leaderboard_cache = self._score_log.get_top_scores(limit=12)
            self._leaderboard_stats = (
                self._score_log.get_total_games(),
                self._score_log.get_average_score(),
            )

        color  = NEON_CYAN
        dim    = dim_color(color, 0.45)
        dimmer = dim_color(color, 0.22)
        gold   = NEON_YELLOW
        player_name = self._player.get_name()

        lw, lh = self._LB_W, self._LB_H
        lx = (SCREEN_WIDTH  - lw) // 2
        ly = (SCREEN_HEIGHT - lh) // 2
        panel = pygame.Rect(lx, ly, lw, lh)
        self._lb_panel_rect = panel   # saglabāts klikšķu pārbaudei

        self._screen.blit(self._fullscreen_dark_surf, (0, 0))
        pygame.draw.rect(self._screen, (10, 12, 16), panel)

        # Virsrakstjosla
        title_bar = pygame.Rect(lx, ly, lw, self._LB_TITLE_H)
        tint = pygame.Surface((lw, self._LB_TITLE_H), pygame.SRCALPHA)
        tint.fill((color[0], color[1], color[2], 26))
        self._screen.blit(tint, title_bar.topleft)
        pygame.draw.line(self._screen, dim,
                         (title_bar.left, title_bar.bottom - 1),
                         (title_bar.right, title_bar.bottom - 1), 1)

        chip_surf = self._font_code_bold.render("[ LEADERBOARD // TOP_SCORES ]", True, color)
        self._screen.blit(chip_surf, (lx + 20, ly + 14))

        total_games, avg_score = self._leaderboard_stats or (0, 0)
        stats_txt    = f"sessions: {total_games:03d}   avg.score: {avg_score:05d}"
        stats_surf   = self._font_code_small.render(stats_txt, True, dim)
        self._screen.blit(stats_surf, (panel.right - stats_surf.get_width() - 20, ly + 17))

        # Kolonnu galvenes rinda
        col_labels = ("#", "NAME", "SCORE", "LVL", "TASKS", "DATE")
        header_y = ly + self._LB_TITLE_H + 16
        cx = lx + 24
        for lbl, cw in zip(col_labels, self._LB_COLS):
            hs = self._font_code_small.render(lbl, True, dim)
            self._screen.blit(hs, (cx, header_y))
            cx += cw

        # Atdalītājs zem galvenēm
        div_y = header_y + 26
        pygame.draw.line(self._screen, dimmer, (lx + 20, div_y), (panel.right - 20, div_y), 1)

        # Rezultātu rindas
        row_h   = 52
        rows_y  = div_y + 10
        entries = self._leaderboard_cache

        if not entries:
            empty = self._font_big.render("Nav saglabātu rezultātu", True, dim)
            self._screen.blit(empty, empty.get_rect(center=(panel.centerx, panel.centery)))
        else:
            for rank, entry in enumerate(entries, 1):
                ry = rows_y + (rank - 1) * row_h
                if ry + row_h > panel.bottom - 60:
                    break  # apgriež ja pārāk daudz rindu

                is_me = entry["name"] == player_name

                # Izgaismo pašreizējo spēlētāju
                if is_me:
                    hi = pygame.Surface((lw - 40, row_h - 6), pygame.SRCALPHA)
                    hi.fill((color[0], color[1], color[2], 14))
                    self._screen.blit(hi, (lx + 20, ry))
                    pygame.draw.line(self._screen, color,
                                     (lx + 20, ry), (lx + 20, ry + row_h - 6), 3)

                # Zelta 1., sudraba 2., bronzas 3. vieta
                rank_col = (
                    (255, 215, 0)   if rank == 1 else
                    (192, 192, 192) if rank == 2 else
                    (205, 127, 50)  if rank == 3 else
                    (color if is_me else dim)
                )
                text_col = color if is_me else dim

                cx = lx + 24
                cells = [
                    (f"{rank:02d}", rank_col),
                    (entry["name"][:22], color if is_me else WHITE),
                    (f"{entry['score']:05d}", gold),
                    (f"{entry['level_reached']:02d}", text_col),
                    (f"{entry['tasks_completed']:02d}", text_col),
                    (entry["date"][:10], dimmer),
                ]
                for (cell_txt, cell_col), cw in zip(cells, self._LB_COLS):
                    cs = self._font_code.render(cell_txt, True, cell_col)
                    self._screen.blit(cs, (cx, ry + 12))
                    cx += cw

                # Plāns atdalītājs
                sep_y = ry + row_h - 4
                pygame.draw.line(self._screen, dimmer,
                                 (lx + 20, sep_y), (panel.right - 20, sep_y), 1)

        # Apakšas navigācijas padomi
        hint_parts = [
            ("[ESC]", color), (" / ", dimmer), ("[ENTER]", color), ("  atpakaļ", dim),
        ]
        total_w = sum(self._font_code_small.size(t)[0] for t, _ in hint_parts)
        hx = panel.centerx - total_w // 2
        hy = panel.bottom - 34
        for txt, col in hint_parts:
            s = self._font_code_small.render(txt, True, col)
            self._screen.blit(s, (hx, hy))
            hx += s.get_width()

        pygame.draw.rect(self._screen, color, panel, 2)
        draw_corner_accents(self._screen, panel, color)


if __name__ == "__main__":
    pygame.init()
    game = Game("TestSpēlētājs")
    game.run()
    pygame.quit()
