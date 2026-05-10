class Level:
    def __init__(self, level_id, title, time_limit):
        self._level_id = level_id
        self._title = title
        self._tasks = []
        self._time_limit = time_limit

    def display_task(self):
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
        pass

    def generate_if_else(self):
        pass


class LoopLevel(Level):
    def __init__(self, level_id, title, time_limit):
        super().__init__(level_id, title, time_limit)
        self._loop_type = ""
        self._iterations = 0

    def display_task(self):
        pass

    def generate_loop(self):
        pass


class FunctionLevel(Level):
    def __init__(self, level_id, title, time_limit):
        super().__init__(level_id, title, time_limit)
        self._func_name = ""
        self._parametri = []

    def display_task(self):
        pass

    def generate_func(self):
        pass