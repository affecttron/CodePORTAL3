# level.py - Level bāzes klase + 3 apakšklases
# Level: abstraktā bāzes klase līmeņiem (mantošana + polimorfisms)
# ConditionLevel: if/else nosacījumu uzdevumi
# LoopLevel: for/while ciklu uzdevumi
# FunctionLevel: funkciju izsaukumu uzdevumi
# Bāzes atribūti: _level_id, _title, _tasks, _time_limit
# Virtuālā metode: display_task() - pārdefinēta katrā apakšklasē

class Level:
    def __init__(self, level_id, title, time_limit):
        self._level_id = level_id
        self._title = title
        self._tasks = []
        self._time_limit = time_limit

    def display_task(self):
        # Virtuālā metode - tiek pārdefinēta apakšklasēs
        pass

    def check_answer(self, ans):
        pass

    def get_title(self):
        return self._title

    def load_tasks(self):
        pass


class ConditionLevel(Level):
    def __init__(self, level_id, title, time_limit):
        super().__init__(level_id, title, time_limit)
        self._branch_type = ""
        self._code_snippet = ""

    def display_task(self):
        # Pārdefinētā metode - if/else uzdevumu attēlošana
        pass

    def generate_if_else(self):
        pass


class LoopLevel(Level):
    def __init__(self, level_id, title, time_limit):
        super().__init__(level_id, title, time_limit)
        self._loop_type = ""
        self._iterations = 0

    def display_task(self):
        # Pārdefinētā metode - for/while ciklu uzdevumu attēlošana
        pass

    def generate_loop(self):
        pass


class FunctionLevel(Level):
    def __init__(self, level_id, title, time_limit):
        super().__init__(level_id, title, time_limit)
        self._func_name = ""
        self._parametri = []

    def display_task(self):
        # Pārdefinētā metode - funkciju uzdevumu attēlošana
        pass

    def generate_func(self):
        pass