import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    GRAVITY, JUMP_STRENGTH, MOVE_SPEED, MAX_FALL_SPEED, CLIMB_SPEED,
    WORLD_WIDTH, WORLD_HEIGHT,
    NEON_CYAN, NEON_PINK, WHITE,
)

COYOTE_FRAMES = 6      # frames after leaving ground where jump still works
JUMP_BUFFER_FRAMES = 10  # frames before landing where a queued jump fires


class PlayerSprite:

    # Izveido spēlētāja vizuālo objektu ar fiziku
    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)
        # Remember the last respawn

        self._spawn_x = float(x)
        self._spawn_y = float(y)

        # setingu importi
        self._width = PLAYER_WIDTH
        self._height = PLAYER_HEIGHT

        # atrumi
        self._vel_x = 0.0
        self._vel_y = 0.0

        # stavoklis
        self._on_ground = False      # Vai stāv uz platformas?
        self._facing_right = True    # Kurp skatās (animācijai)
        self._is_moving = False      # Vai pašlaik kustas?
        self._is_jumping = False     # Vai lec?

        self._coyote_timer = 0       # frames left where jump works after leaving ground
        self._jump_buffer = 0        # frames left for a buffered jump to fire

        # Kāpnes: pārklājas ar climbable tile + W/S
        self._on_ladder = False
        self._climb_dir = 0          # -1 = augšup, +1 = lejup, 0 = stāv
        self._climb_lockout = 0      # frames where climb is ignored (post-jump)

        self._animation_frame = 0

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

        # Coyote time: allow jumping for a few frames after walking off a ledge
        if prev_on_ground and not self._on_ground:
            self._coyote_timer = COYOTE_FRAMES
        elif self._on_ground:
            self._coyote_timer = 0
        elif self._coyote_timer > 0:
            self._coyote_timer -= 1

        # Jump buffer: fire a buffered jump as soon as we can
        if self._jump_buffer > 0:
            self._jump_buffer -= 1
            if self._on_ground or self._coyote_timer > 0:
                self._execute_jump()

        if self._climb_lockout > 0:
            self._climb_lockout -= 1

        self._animation_frame += 1

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
                if self._vel_y > 0:  # Krīt uz leju
                    self._y = platform_rect.top - self._height
                    self._vel_y = 0
                    self._on_ground = True
                    self._is_jumping = False
                elif self._vel_y < 0:  # Lec uz augšu
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
        # Ja iekrīt bedrē - atgriež uz pēdējo spawn punktu
        if self._y > WORLD_HEIGHT:
            self.respawn(self._spawn_x, self._spawn_y)

 # kustibas

    # Sāk kustību pa kreisi
    def move_left(self):
        self._vel_x = -MOVE_SPEED
        self._facing_right = False
        self._is_moving = True

    # Sāk kustību pa labi
    def move_right(self):
        self._vel_x = MOVE_SPEED
        self._facing_right = True
        self._is_moving = True

    # Apstādina horizontālo kustību
    def stop(self):
        self._vel_x = 0
        self._is_moving = False

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
        self._vel_y = JUMP_STRENGTH
        self._on_ground = False
        self._is_jumping = True
        self._coyote_timer = 0
        self._jump_buffer = 0
        self._climb_dir = 0
        self._climb_lockout = 12

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

    # Zīmē spēlētāju ar krāsainu animāciju
    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        screen_x = int(self._x - camera_offset_x)
        screen_y = int(self._y - camera_offset_y)

        if self._is_jumping:
            color = NEON_PINK
        elif self._is_moving:
            if (self._animation_frame // 10) % 2 == 0:
                color = NEON_CYAN
            else:
                color = WHITE
        else:
            color = NEON_CYAN

        # kermenis testiem
        pygame.draw.rect(screen, color, (screen_x, screen_y, self._width, self._height))
        pygame.draw.rect(screen, (0, 100, 100), (screen_x, screen_y, self._width, self._height), 2)

        eye_y = screen_y + 15
        if self._facing_right:
            eye_x = screen_x + self._width - 15
        else:
            eye_x = screen_x + 8

        pygame.draw.circle(screen, (0, 0, 0), (eye_x, eye_y), 4)
        pygame.draw.circle(screen, WHITE, (eye_x, eye_y), 2)


        if self._is_jumping:
            for i in range(3):
                pygame.draw.line(
                    screen, NEON_PINK,
                    (screen_x + 10 + i * 12, screen_y + self._height + 5),
                    (screen_x + 10 + i * 12, screen_y + self._height + 15),
                    2
                )

    # Atgriež spēlētāja sadursmes taisnstūri
    def get_rect(self):
        return pygame.Rect(int(self._x), int(self._y), self._width, self._height)

    # Atgriež x pozīciju pikseļos
    def get_x(self):
        return self._x

    # Atgriež y pozīciju pikseļos
    def get_y(self):
        return self._y

    # Atgriež spēlētāja centra x koordinātu
    def get_center_x(self):
        return self._x + self._width // 2

    # Atgriež spēlētāja centra y koordinātu
    def get_center_y(self):
        return self._y + self._height // 2

    # Vai spēlētājs stāv uz zemes
    def is_on_ground(self):
        return self._on_ground

    # Vai spēlētājs kustas horizontāli
    def is_moving(self):
        return self._is_moving

    # Atgriež horizontālo ātrumu
    def get_vel_x(self):
        return self._vel_x

    # Atgriež vertikālo ātrumu
    def get_vel_y(self):
        return self._vel_y
