import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT,
    GRAVITY, JUMP_STRENGTH, MOVE_SPEED, MAX_FALL_SPEED,
    WORLD_WIDTH, WORLD_HEIGHT,
    NEON_CYAN, NEON_PINK, WHITE,
)


class PlayerSprite:
    """Spēlētāja sprite ar platformer fiziku."""

    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)

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

        self._animation_frame = 0


    def update(self, platforms):
        """Galvenā update metode - tiek izsaukta katru kadru.
        platforms = saraksts ar pygame.Rect objektiem (no World.get_solid_rects())"""

        self._apply_gravity()
        self._move_horizontal(platforms)
        self._move_vertical(platforms)
        self._check_world_bounds()
        self._animation_frame += 1

    def _apply_gravity(self):
        """Pielietojam gravitāciju (privāta metode)."""
        self._vel_y += GRAVITY
        if self._vel_y > MAX_FALL_SPEED:
            self._vel_y = MAX_FALL_SPEED

    def _move_horizontal(self, platforms):
        """Kustība X virzienā ar sadursmju pārbaudi."""
        self._x += self._vel_x


        player_rect = self.get_rect()
        for platform_rect in platforms:
            if player_rect.colliderect(platform_rect):
                if self._vel_x > 0:
                    self._x = platform_rect.left - self._width
                elif self._vel_x < 0: 
                    self._x = platform_rect.right
                self._vel_x = 0

    def _move_vertical(self, platforms):
        """Kustība Y virzienā ar sadursmju pārbaudi."""
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

    def _check_world_bounds(self):
        """Neļauj iziet ārpus pasaules robežām."""
        if self._x < 0:
            self._x = 0
        if self._x + self._width > WORLD_WIDTH:
            self._x = WORLD_WIDTH - self._width
        # Ja iekrīt bedrē - atgriež uz sākumu
        if self._y > WORLD_HEIGHT:
            self.respawn(100, 500)

 # kustibas

    def move_left(self):
        """Sāk kustību pa kreisi."""
        self._vel_x = -MOVE_SPEED
        self._facing_right = False
        self._is_moving = True

    def move_right(self):
        """Sāk kustību pa labi."""
        self._vel_x = MOVE_SPEED
        self._facing_right = True
        self._is_moving = True

    def stop(self):
        """Aptur horizontālo kustību."""
        self._vel_x = 0
        self._is_moving = False

    def jump(self):
        """Lec (tikai ja ir uz zemes)."""
        if self._on_ground:
            self._vel_y = JUMP_STRENGTH
            self._on_ground = False
            self._is_jumping = True

    def respawn(self, x, y):
        """Pārvieto spēlētāju uz dotu pozīciju (pēc nāves)."""
        self._x = float(x)
        self._y = float(y)
        self._vel_x = 0
        self._vel_y = 0


    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        """Zīmē spēlētāju ar kameras nobīdi."""
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

    def get_rect(self):
        """Pygame Rect spēlētājam (sadursmēm)."""
        return pygame.Rect(int(self._x), int(self._y), self._width, self._height)

    def get_x(self):
        return self._x

    def get_y(self):
        return self._y

    def get_center_x(self):
        """X koordināta no spēlētāja vidus (kamerai)."""
        return self._x + self._width // 2

    def get_center_y(self):
        return self._y + self._height // 2

    def is_on_ground(self):
        return self._on_ground

    def is_moving(self):
        return self._is_moving