# task.py - Task klase
# Viena uzdevuma datu modelis: jautājums, pareizā atbilde, palīdzība, punkti.
# Katrs Level satur vairākus Task objektus (kompozīcija).
# Atribūti: _question, _correct_answer, _hint, _points
# Metodes: display(), verify(ans), get_hint(), get_points()

class Task:
    def __init__(self, question, correct_answer, hint, points):
        self._question = question
        self._correct_answer = correct_answer
        self._hint = hint
        self._points = points

    def display(self):
        pass

    def verify(self, ans):
        pass

    def get_hint(self):
        return self._hint

    def get_points(self):
        return self._points