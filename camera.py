import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
    MOVE_SPEED,
    CAMERA_SMOOTHNESS_X, CAMERA_SMOOTHNESS_Y,
    CAMERA_LOOKAHEAD_MAX, CAMERA_LOOKAHEAD_LERP,
    CAMERA_MOTION_BLUR, CAMERA_BLUR_MIN_SPEED,
    CAMERA_BLUR_ALPHA_GAIN, CAMERA_BLUR_ALPHA_MAX,
)


class Camera:
    def __init__(self):

        self._x = 0.0
        self._y = 0.0

        self._target = None

        self._smoothness_x = CAMERA_SMOOTHNESS_X
        self._smoothness_y = CAMERA_SMOOTHNESS_Y

        self._is_following = True

        self._screen_width = SCREEN_WIDTH
        self._screen_height = SCREEN_HEIGHT

        self._world_width = WORLD_WIDTH
        self._world_height = WORLD_HEIGHT

        # Look-ahead
        self._lookahead_x = 0.0
        self._lookahead_target_x = 0.0

        # Kameras ātrums
        self._vel_x = 0.0
        self._vel_y = 0.0

        # Motion blur 
        self._motion_blur_enabled = CAMERA_MOTION_BLUR
        self._prev_frame = None       
        self._next_frame = None       # buferis

    def set_target(self, target):
        self._target = target

    def remove_target(self):
        self._target = None

    def follow(self, enabled=True):
        self._is_following = enabled


    def update(self):
        prev_x, prev_y = self._x, self._y

        if self._target is not None and self._is_following:
            target_x = self._target.get_center_x() - self._screen_width // 2
            target_y = self._target.get_center_y() - self._screen_height // 2


            if hasattr(self._target, "get_vel_x") and MOVE_SPEED > 0:
                vel_ratio = max(-1.0, min(1.0, self._target.get_vel_x() / MOVE_SPEED))
                self._lookahead_target_x = vel_ratio * CAMERA_LOOKAHEAD_MAX

            self._lookahead_x += (self._lookahead_target_x - self._lookahead_x) * CAMERA_LOOKAHEAD_LERP

            self._x += (target_x + self._lookahead_x - self._x) * self._smoothness_x
            self._y += (target_y - self._y) * self._smoothness_y

        # robezas mapei
        self._clamp_to_world()

        self._vel_x = self._x - prev_x
        self._vel_y = self._y - prev_y

    def _clamp_to_world(self):
        # left
        if self._x < 0:
            self._x = 0

        # right
        max_x = self._world_width - self._screen_width
        if self._x > max_x:
            self._x = max_x

        # up
        if self._y < 0:
            self._y = 0

        # down
        max_y = self._world_height - self._screen_height
        if self._y > max_y:
            self._y = max_y


    def move(self, dx, dy):
        self._x += dx
        self._y += dy
        self._clamp_to_world()

    def set_position(self, x, y):
        self._x = float(x)
        self._y = float(y)
        self._clamp_to_world()

    def center_on(self, world_x, world_y):
        self._x = world_x - self._screen_width // 2
        self._y = world_y - self._screen_height // 2
        self._clamp_to_world()


    # koordinates

    def world_to_screen(self, world_x, world_y):
        return (world_x - self._x, world_y - self._y)

    def screen_to_world(self, screen_x, screen_y):
        return (screen_x + self._x, screen_y + self._y)

    #   settingi

    def set_smoothness(self, value):
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._smoothness_x = value
        self._smoothness_y = value

    def set_motion_blur(self, enabled):
        self._motion_blur_enabled = bool(enabled)
        if not enabled:
            self._prev_frame = None
            self._next_frame = None

    def toggle_motion_blur(self):
        self.set_motion_blur(not self._motion_blur_enabled)
        return self._motion_blur_enabled


    def get_x(self):
        return int(self._x)

    def get_y(self):
        return int(self._y)

    def get_offset(self):
        return (int(self._x), int(self._y))

    def get_view_rect(self):
        return (int(self._x), int(self._y), self._screen_width, self._screen_height)

    def get_speed(self):
        return (self._vel_x * self._vel_x + self._vel_y * self._vel_y) ** 0.5


    # MOTION BLUR


    def apply_motion_blur(self, screen):
        if not self._motion_blur_enabled:
            return

        speed = self.get_speed()


        if speed <= CAMERA_BLUR_MIN_SPEED * 0.5:
            self._prev_frame = None
            return

        size = screen.get_size()


        if self._next_frame is None or self._next_frame.get_size() != size:
            self._next_frame = pygame.Surface(size).convert()
        self._next_frame.blit(screen, (0, 0))

        if self._prev_frame is not None and speed > CAMERA_BLUR_MIN_SPEED:
            alpha = int(min(speed * CAMERA_BLUR_ALPHA_GAIN, CAMERA_BLUR_ALPHA_MAX))
            self._prev_frame.set_alpha(alpha)
            screen.blit(self._prev_frame, (0, 0))

        self._prev_frame, self._next_frame = self._next_frame, self._prev_frame
