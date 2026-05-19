class Task:
    def __init__(self, question, correct_answer, hint, points):
        self._question = question
        self._correct_answer = correct_answer
        self._hint = hint
        self._points = points

    def verify(self, ans):
        player_answer = ans.strip().lower()
        correct = self._correct_answer.strip().lower()
        return player_answer == correct

    def calculate_points(self, attempt_number):
        if attempt_number == 1:
            return 100
        if attempt_number == 2:
            return 50
        if attempt_number == 3:
            return 20
        return 0

    def get_question(self):
        return self._question

    def get_hint(self):
        return self._hint
