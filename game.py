
from player import Player
from level import ConditionLevel, LoopLevel, FunctionLevel
from score_log import ScoreLog


class Game:
    def __init__(self, title="CODE Portal 3"):
        self._title = title
        self._current_level = 0
        self._is_running = False
        self._levels = []
        self._player = None
        self._score_log = ScoreLog()

    def start_game(self):
        pass

    def load_levels(self):
        pass

    def next_level(self):
        pass

    def end_game(self):
        pass