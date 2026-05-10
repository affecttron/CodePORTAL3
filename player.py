# player.py - Player klase
# Glabā spēlētāja sesijas datus: vārds, punkti, mēģinājumi, sasniegtais līmenis.
# Visi atribūti privāti, piekļuve ar getter/setter metodēm (iekapsulēšana).
# Atribūti: _name, _score, _attempts, _level_reached
# Metodes: add_score(), reset_attempts(), get_score(), get_name()

class Player:
    def __init__(self, name):
        self._name = name
        self._score = 0
        self._attempts = 0
        self._level_reached = 1

    def add_score(self, points):
        pass

    def reset_attempts(self):
        pass

    def get_score(self):
        return self._score

    def get_name(self):
        return self._name
    