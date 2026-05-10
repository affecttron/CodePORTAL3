from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    """Kameras klase 2D spēlei.
    Seko mērķim (spēlētājam) un nodrošina, ka neiznāk ārpus pasaules."""

    def __init__(self):

        self._x = 0.0
        self._y = 0.0

        self._target = None

        self._smoothness = 0.15


        self._is_following = True


        self._screen_width = SCREEN_WIDTH
        self._screen_height = SCREEN_HEIGHT


        self._world_width = WORLD_WIDTH
        self._world_height = WORLD_HEIGHT


    def set_target(self, target):
        """Iestata mērķi, kuram sekot (parasti PlayerSprite)."""
        self._target = target

    def remove_target(self):
        """Atceļ sekošanu (kamera paliek vietā)."""
        self._target = None

    def follow(self, enabled=True):
        """Ieslēdz/izslēdz automātisko sekošanu."""
        self._is_following = enabled


    def update(self):
        """Atjaunina kameras pozīciju (seko mērķim, ja iestatīts)."""
        if self._target is not None and self._is_following:
            target_x = self._target.get_center_x() - self._screen_width // 2
            target_y = self._target.get_center_y() - self._screen_height // 2


            self._x += (target_x - self._x) * self._smoothness
            self._y += (target_y - self._y) * self._smoothness

        # robezas mapei
        self._clamp_to_world()

    def _clamp_to_world(self):
        """Neļauj kamerai iziet ārpus pasaules robežām (privāta metode)."""
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
        """Pārvieto kameru manuāli (lieto Level Editoram)."""
        self._x += dx
        self._y += dy
        self._clamp_to_world()

    def set_position(self, x, y):
        """Iestata kameras pozīciju tieši (teleportē)."""
        self._x = float(x)
        self._y = float(y)
        self._clamp_to_world()

    def center_on(self, world_x, world_y):
        """Centrē kameru uz dotu pasaules punktu."""
        self._x = world_x - self._screen_width // 2
        self._y = world_y - self._screen_height // 2
        self._clamp_to_world()


    # koordinates

    def world_to_screen(self, world_x, world_y):
        """Pārvērš pasaules koordinātes ekrāna koordinātēs."""
        return (world_x - self._x, world_y - self._y)

    def screen_to_world(self, screen_x, screen_y):
        """Pārvērš ekrāna koordinātes pasaules koordinātēs (peles klikšķis!).
        Šī metode ir kritiski svarīga Level Editoram!"""
        return (screen_x + self._x, screen_y + self._y)

    #   settingi

    def set_smoothness(self, value):
        """Iestata sekošanas plūstamību (0.0 līdz 1.0)."""
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._smoothness = value


    def get_x(self):
        """X nobīde pikseļos (cik daudz pasaule pārvietota pa kreisi)."""
        return int(self._x)

    def get_y(self):
        """Y nobīde pikseļos."""
        return int(self._y)

    def get_offset(self):
        """Atgriež kameras nobīdi kā tuple (x, y) - ērti zīmēšanai."""
        return (int(self._x), int(self._y))

    def get_view_rect(self):
        """Atgriež redzamo zonu kā tuple (x, y, w, h) - optimizācijai."""
        return (int(self._x), int(self._y), self._screen_width, self._screen_height)