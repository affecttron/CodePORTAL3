from settings import MAX_ATTEMPTS


class Player:
    def __init__(self, name):
        self._name = name
        self._score = 0
        self._attempts = 0
        self._level_reached = 1
        self._tasks_completed = 0  # Cik uzdevumi atrisināti kopā

    def add_score(self, points):
        if points > 0:
            self._score += points
            self._tasks_completed += 1

    def reset_attempts(self):
        self._attempts = 0

    def increment_attempts(self):
        self._attempts += 1

    def has_attempts_left(self):
        return self._attempts < MAX_ATTEMPTS

    def advance_level(self):
        self._level_reached += 1

    def set_level_reached(self, level):
        if level > self._level_reached:
            self._level_reached = level
            
    def get_name(self):
        return self._name

    def get_score(self):
        return self._score

    def get_attempts(self):
        return self._attempts

    def get_level_reached(self):
        return self._level_reached

    def get_tasks_completed(self):
        return self._tasks_completed

    def __str__(self):
        return f"Player({self._name}, punkti: {self._score}, līmenis: {self._level_reached})"