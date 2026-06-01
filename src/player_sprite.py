import os
import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    GRAVITY, JUMP_STRENGTH, MOVE_SPEED, SPRINT_SPEED, MAX_FALL_SPEED, CLIMB_SPEED,
    WORLD_WIDTH, WORLD_HEIGHT,
    IMAGES_FOLDER,
    NEON_CYAN, NEON_PINK, WHITE,
    WORLD_TINT, WORLD_TINT_ALPHA,
)

COYOTE_FRAMES = 6
JUMP_BUFFER_FRAMES = 10

_ANIM_IDLE = "idle"
_ANIM_WALK = "walk"
_ANIM_RUN  = "run"
_ANIM_JUMP = "jump"
_ANIM_DEAD = "dead"

# fails, kadru skaits, spēles kadri uz animācijas kadru
_ANIM_CONFIGS = {
    _ANIM_IDLE: ("Idle.png", 6,  8),
    _ANIM_WALK: ("Walk.png", 10, 5),
    _ANIM_RUN:  ("Run.png",  10, 4),
    _ANIM_JUMP: ("Jump.png", 6,  5),
    _ANIM_DEAD: ("Dead.png", 5,  8),
}

# renderēšanas izmērs pikseļos
_VISUAL_SIZE = 185


class PlayerSprite:

    # Izveido spēlētāja vizuālo objektu ar fiziku
    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)

        self._spawn_x = float(x)
        self._spawn_y = float(y)

        self._width  = PLAYER_WIDTH
        self._height = PLAYER_HEIGHT

        # ātrumi
        self._vel_x = 0.0
        self._vel_y = 0.0

        # stāvoklis
        self._on_ground    = False
        self._facing_right = True
        self._is_moving    = False
        self._is_jumping   = False
        self._is_sprinting = False
        self._is_dead      = False

        self._coyote_timer  = 0
        self._jump_buffer   = 0

        # kāpnes
        self._on_ladder    = False
        self._climb_dir    = 0
        self._climb_lockout = 0

        # piezemēšanās zibsnīša taimeris
        self._landing_timer = 0
        self._airborne_frames = 0

        # animācijas kadri pa labi un pa kreisi
        self._sprites_r: dict = {}
        self._sprites_l: dict = {}
        self._sprites_loaded = False

        # pašreizējais animācijas stāvoklis un tikateris
        self._anim_state = _ANIM_IDLE
        self._anim_tick  = 0

        self._load_sprites()

    # Ielādē visus animācijas sprite sarakstus
    def _load_sprites(self):
        sprite_dir = os.path.join(IMAGES_FOLDER, "PlayerSprite")
        for name, (filename, frame_count, _) in _ANIM_CONFIGS.items():
            path = os.path.join(sprite_dir, filename)
            frames_r = self._slice_sheet(path, frame_count)
            if frames_r:
                self._sprites_r[name] = frames_r
                self._sprites_l[name] = [
                    pygame.transform.flip(f, True, False) for f in frames_r
                ]
        self._sprites_loaded = bool(self._sprites_r)

    # Sagriež sprite sheet atsevišķos kadros
    def _slice_sheet(self, path, frame_count):
        if not os.path.exists(path):
            print(f"[PlayerSprite] nav atrasts: {path}")
            return []
        try:
            sheet = pygame.image.load(path)
            try:
                sheet = sheet.convert_alpha()
            except pygame.error:
                pass
        except pygame.error as exc:
            print(f"[PlayerSprite] nevar ielādēt: {exc}")
            return []

        sw, sh = sheet.get_width(), sheet.get_height()
        frame_w = sw // frame_count
        frames = []
        for i in range(frame_count):
            raw = pygame.Surface((frame_w, sh), pygame.SRCALPHA)
            raw.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, sh))
            scaled = pygame.transform.scale(raw, (_VISUAL_SIZE, _VISUAL_SIZE))
            t = WORLD_TINT_ALPHA / 255.0
            mult = tuple(int(255 * (1.0 - t) + c * t) for c in WORLD_TINT)
            tint = pygame.Surface((_VISUAL_SIZE, _VISUAL_SIZE))
            tint.fill(mult)
            scaled.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            frames.append(scaled)
        return frames

    # Atjaunina fiziku un sadursmes kadrā
    def update(self, platforms, climbables=None):
        prev_on_ground = self._on_ground

        self._update_ladder_state(climbables or [])

        if self._on_ladder and self._climb_dir != 0:
            self._vel_y = CLIMB_SPEED * self._climb_dir
        else:
            self._apply_gravity()

        self._move_horizontal(platforms)
        self._move_vertical(platforms)
        self._check_world_bounds()

        if prev_on_ground and not self._on_ground:
            self._coyote_timer = COYOTE_FRAMES
        elif self._on_ground:
            self._coyote_timer = 0
        elif self._coyote_timer > 0:
            self._coyote_timer -= 1

        if self._jump_buffer > 0:
            self._jump_buffer -= 1
            if self._on_ground or self._coyote_timer > 0:
                self._execute_jump()

        if self._climb_lockout > 0:
            self._climb_lockout -= 1

        # piezemēšanās kadri
        if self._on_ground:
            if self._airborne_frames >= 5:
                self._landing_timer = 4
            self._airborne_frames = 0
        else:
            self._airborne_frames += 1
        if self._landing_timer > 0:
            self._landing_timer -= 1

        self._update_anim_state()

    # Piemēro gravitācijas paātrinājumu
    def _apply_gravity(self):
        self._vel_y += GRAVITY
        if self._vel_y > MAX_FALL_SPEED:
            self._vel_y = MAX_FALL_SPEED

    # Pārbauda vai spēlētājs atrodas uz kāpnēm
    def _update_ladder_state(self, climbables):
        player_rect = self.get_rect()
        self._on_ladder = any(player_rect.colliderect(r) for r in climbables)
        if not self._on_ladder:
            self._climb_dir = 0

    # Pārvieto horizontāli un risina sadursmes
    def _move_horizontal(self, platforms):
        self._x += self._vel_x
        player_rect = self.get_rect()
        for platform_rect in platforms:
            if player_rect.colliderect(platform_rect):
                if self._vel_x > 0:
                    self._x = platform_rect.left - self._width
                elif self._vel_x < 0:
                    self._x = platform_rect.right
                self._vel_x = 0
                player_rect.x = int(self._x)

    # Pārvieto vertikāli un risina sadursmes
    def _move_vertical(self, platforms):
        self._y += self._vel_y
        self._on_ground = False
        player_rect = self.get_rect()
        for platform_rect in platforms:
            if player_rect.colliderect(platform_rect):
                if self._vel_y > 0:
                    self._y = platform_rect.top - self._height
                    self._vel_y = 0
                    self._on_ground = True
                    self._is_jumping = False
                elif self._vel_y < 0:
                    self._y = platform_rect.bottom
                    self._vel_y = 0
                    self._is_jumping = False
                player_rect.y = int(self._y)

    # Notur spēlētāju pasaules robežās
    def _check_world_bounds(self):
        if self._x < 0:
            self._x = 0
        if self._x + self._width > WORLD_WIDTH:
            self._x = WORLD_WIDTH - self._width
        if self._y > WORLD_HEIGHT:
            self.respawn(self._spawn_x, self._spawn_y)

    # Nosaka animācijas stāvokli pēc kustības
    def _update_anim_state(self):
        new_state = self._resolve_anim_state()
        if new_state != self._anim_state:
            self._anim_state = new_state
            self._anim_tick  = 0
        else:
            self._anim_tick += 1

    # Atgriež animācijas nosaukumu pēc statusa
    def _resolve_anim_state(self):
        if self._is_dead:
            return _ANIM_DEAD
        if (not self._on_ground and self._airborne_frames > 2) or self._landing_timer > 0:
            return _ANIM_JUMP
        if abs(self._vel_x) > 0.1:
            return _ANIM_RUN if self._is_sprinting else _ANIM_WALK
        return _ANIM_IDLE

    # Sāk kustību pa kreisi, pēc izvēles sprint
    def move_left(self, sprint=False):
        speed = SPRINT_SPEED if sprint else MOVE_SPEED
        self._vel_x = -speed
        self._facing_right = False
        self._is_moving    = True
        self._is_sprinting = sprint

    # Sāk kustību pa labi, pēc izvēles sprint
    def move_right(self, sprint=False):
        speed = SPRINT_SPEED if sprint else MOVE_SPEED
        self._vel_x = speed
        self._facing_right = True
        self._is_moving    = True
        self._is_sprinting = sprint

    # Apstādina horizontālo kustību
    def stop(self):
        self._vel_x = 0
        self._is_moving    = False
        self._is_sprinting = False

    # Rāpjas augšup pa kāpnēm
    def climb_up(self):
        if self._on_ladder and self._climb_lockout == 0:
            self._climb_dir = -1

    # Rāpjas lejup pa kāpnēm
    def climb_down(self):
        if self._on_ladder and self._climb_lockout == 0:
            self._climb_dir = 1

    # Pārtrauc rāpšanos
    def stop_climbing(self):
        self._climb_dir = 0

    # Vai spēlētājs šobrīd uz kāpnēm
    def is_on_ladder(self):
        return self._on_ladder

    # Izpilda lēcienu ar coyote un buferizāciju
    def jump(self):
        if self._on_ladder:
            self._execute_jump()
            return
        if self._on_ground or self._coyote_timer > 0:
            self._execute_jump()
        else:
            self._jump_buffer = JUMP_BUFFER_FRAMES

    # Tiešā lēciena fizika
    def _execute_jump(self):
        self._vel_y        = JUMP_STRENGTH
        self._on_ground    = False
        self._is_jumping   = True
        self._coyote_timer = 0
        self._jump_buffer  = 0
        self._climb_dir    = 0
        self._climb_lockout = 12

    # Ieslēdz nāves animāciju
    def start_death_anim(self):
        self._is_dead    = True
        self._anim_state = _ANIM_DEAD
        self._anim_tick  = 0

    # Izslēdz nāves animāciju
    def clear_death_anim(self):
        self._is_dead    = False
        self._anim_state = _ANIM_IDLE
        self._anim_tick  = 0

    # Teleportē spēlētāju uz spawn pozīciju
    def respawn(self, x, y):
        self._x = float(x)
        self._y = float(y)
        self._spawn_x = float(x)
        self._spawn_y = float(y)
        self._vel_x = 0
        self._vel_y = 0

    # Nedaudz pabīda spēlētāju par delta
    def nudge(self, dx, dy=0):
        self._x += dx
        self._y += dy

    # Zīmē spēlētāju ekrānā
    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        screen_x = int(self._x - camera_offset_x)
        screen_y = int(self._y - camera_offset_y)

        if self._sprites_loaded:
            self._draw_sprite(screen, screen_x, screen_y)
        else:
            self._draw_fallback(screen, screen_x, screen_y)

    # Izvēlas pareizo lēciena kadru pēc ātruma
    def _get_jump_frame(self):
        if self._landing_timer > 0:
            return 5
        if self._anim_tick < 4:
            return 0
        if self._anim_tick < 8:
            return 1
        if self._vel_y < 0:
            return 2
        if self._vel_y < 8:
            return 3
        return 4

    # Zīmē animētu sprite no sprite sheet
    def _draw_sprite(self, screen, screen_x, screen_y):
        state  = self._anim_state
        bank   = self._sprites_r if self._facing_right else self._sprites_l
        frames = bank.get(state) or bank.get(_ANIM_IDLE, [])
        if not frames:
            self._draw_fallback(screen, screen_x, screen_y)
            return

        _, frame_count, speed = _ANIM_CONFIGS[state]
        if state == _ANIM_JUMP:
            idx = self._get_jump_frame()
        elif state == _ANIM_DEAD:
            # nāves animācija spēlējas vienreiz un apstājas
            idx = min(self._anim_tick // speed, frame_count - 1)
        else:
            idx = (self._anim_tick // speed) % frame_count

        frame  = frames[idx]
        draw_x = screen_x - (_VISUAL_SIZE - self._width)  // 2
        draw_y = screen_y + self._height - _VISUAL_SIZE
        screen.blit(frame, (draw_x, draw_y))

    # Zīmē krāsainu rezerves taisnstūri
    def _draw_fallback(self, screen, screen_x, screen_y):
        if self._is_jumping:
            color = NEON_PINK
        elif self._is_moving:
            if (self._anim_tick // 10) % 2 == 0:
                color = NEON_CYAN
            else:
                color = WHITE
        else:
            color = NEON_CYAN

        pygame.draw.rect(screen, color,
                         (screen_x, screen_y, self._width, self._height))
        pygame.draw.rect(screen, (0, 100, 100),
                         (screen_x, screen_y, self._width, self._height), 2)

        eye_y = screen_y + 15
        eye_x = (screen_x + self._width - 15) if self._facing_right else (screen_x + 8)
        pygame.draw.circle(screen, (0, 0, 0), (eye_x, eye_y), 4)
        pygame.draw.circle(screen, WHITE,     (eye_x, eye_y), 2)

        if self._is_jumping:
            for i in range(3):
                pygame.draw.line(
                    screen, NEON_PINK,
                    (screen_x + 10 + i * 12, screen_y + self._height + 5),
                    (screen_x + 10 + i * 12, screen_y + self._height + 15),
                    2,
                )

    # Atgriež spēlētāja sadursmes taisnstūri
    def get_rect(self):
        return pygame.Rect(int(self._x), int(self._y), self._width, self._height)

    def get_x(self):         return self._x
    def get_y(self):         return self._y
    def get_center_x(self):  return self._x + self._width  // 2
    def get_center_y(self):  return self._y + self._height // 2
    def is_on_ground(self):  return self._on_ground
    def is_moving(self):     return self._is_moving
    def get_vel_x(self):     return self._vel_x
    def get_vel_y(self):     return self._vel_y
