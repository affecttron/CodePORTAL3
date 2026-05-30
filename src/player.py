from settings import MAX_ATTEMPTS


class Player:
    # Izveido jaunu spēlētāju ar nosaukumu
    def __init__(self, name):
        self._name = name
        self._score = 0
        self._attempts = 0
        self._max_attempts = MAX_ATTEMPTS
        self._level_reached = 1
        self._tasks_completed = 0  # Cik uzdevumi atrisināti kopā

    # Pievieno punktus un uzskaita uzdevumu
    def add_score(self, points):
        if points > 0:
            self._score += points
            self._tasks_completed += 1

    # Atņem punktus, minimums nulle
    def deduct_score(self, points):
        self._score = max(0, self._score - points)

    # Atiestata mēģinājumu skaitītāju uz nulli
    def reset_attempts(self):
        self._attempts = 0

    # Iestata maksimālo mēģinājumu skaitu
    def set_max_attempts(self, n):
        self._max_attempts = n

    # Palielina mēģinājumu skaitītāju par vienu
    def increment_attempts(self):
        self._attempts += 1

    # Pārbauda vai vēl ir mēģinājumi atlikuši
    def has_attempts_left(self):
        return self._attempts < self._max_attempts

    # Palielina sasniegtā līmeņa numuru
    def advance_level(self):
        self._level_reached += 1

    # Iestata līmeni ja jaunais ir augstāks
    def set_level_reached(self, level):
        if level > self._level_reached:
            self._level_reached = level

    # Atgriež spēlētāja vārdu
    def get_name(self):
        return self._name

    # Atgriež uzkrāto punktu skaitu
    def get_score(self):
        return self._score

    # Atgriež pašreizējo mēģinājumu skaitu
    def get_attempts(self):
        return self._attempts

    # Atgriež augstāko sasniegto līmeni
    def get_level_reached(self):
        return self._level_reached

    # Atgriež pabeigto uzdevumu skaitu
    def get_tasks_completed(self):
        return self._tasks_completed

    # Teksta attēlojums atkļūdošanai
    def __str__(self):
        return f"Player({self._name}, punkti: {self._score}, līmenis: {self._level_reached})"
