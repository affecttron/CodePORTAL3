
class Task:
    def __init__(self, question, correct_answer, hint, points):
        self._question = question
        self._correct_answer = correct_answer
        self._hint = hint
        self._points = points
        self._attempts_used = 0

    def display(self):
        return self._question

    def verify(self, ans):
        spēlētāja_atbilde = ans.strip().lower()
        pareizā_atbilde = self._correct_answer.strip().lower()
        return spēlētāja_atbilde == pareizā_atbilde

    def calculate_points(self, attempt_number, time_taken):
        if attempt_number == 1:
            base_points = 100
        elif attempt_number == 2:
            base_points = 50
        elif attempt_number == 3:
            base_points = 20
        else:
            base_points = 0

        speed_bonus = 0
        if time_taken < 15 and base_points > 0:
            speed_bonus = 25

        return base_points + speed_bonus

    def increment_attempts(self):
        self._attempts_used += 1

    def reset_attempts(self):
        self._attempts_used = 0

    # Getters
    def get_question(self):
        return self._question

    def get_hint(self):
        return self._hint

    def get_points(self):
        return self._points

    def get_correct_answer(self):
        return self._correct_answer

    def get_attempts_used(self):
        return self._attempts_used