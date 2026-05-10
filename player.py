from settings import MAX_ATTEMPTS


class Player:
    def __init__(self, name):
        self._name = name
        self._score = 0
        self._attempts = 0
        self._level_reached = 1
        self._tasks_completed = 0  # Cik uzdevumi atrisināti kopā

    def add_score(self, points):
        """Pievieno punktus kopējam rezultātam"""
        if points > 0:
            self._score += points
            self._tasks_completed += 1

    def reset_attempts(self):
        """Atjauno mēģinājumu skaitītāju uz 0 (jaunam uzdevumam)"""
        self._attempts = 0

    def increment_attempts(self):
        """Palielina mēģinājumu skaitu par 1"""
        self._attempts += 1

    def has_attempts_left(self):
        """Pārbauda vai spēlētājam vēl ir mēģinājumi (max 3)"""
        return self._attempts < MAX_ATTEMPTS

    def advance_level(self):
        """Pāriet uz nākamo līmeni"""
        self._level_reached += 1

    def set_level_reached(self, level):
        """Iestata sasniegto līmeni (setter)"""
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
        """Spēlētāja apraksts kā teksts (noderīgi debug-ošanai)"""
        return f"Player({self._name}, punkti: {self._score}, līmenis: {self._level_reached})"