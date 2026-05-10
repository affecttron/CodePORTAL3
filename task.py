
class Task:
    def __init__(self, question, correct_answer, hint, points):
        self._question = question
        self._correct_answer = correct_answer
        self._hint = hint
        self._points = points
        self._attempts_used = 0

    def display(self):
        """Atgriež uzdevuma tekstu (vēlāk to zīmēsim uz pygame ekrāna)"""
        return self._question

    def verify(self, ans):
        """Pārbauda atbildi - atgriež True ja pareiza, False ja nepareiza"""
        spēlētāja_atbilde = ans.strip().lower()
        pareizā_atbilde = self._correct_answer.strip().lower()
        return spēlētāja_atbilde == pareizā_atbilde

    def calculate_points(self, attempt_number, time_taken):
        """Aprēķina punktus pēc README sistēmas:
        - 1. mēģinājums: 100 pts
        - 2. mēģinājums: 50 pts
        - 3. mēģinājums: 20 pts
        - Ātruma bonuss (< 15 sek): +25 pts
        """
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
        """Palielina izmantoto mēģinājumu skaitu"""
        self._attempts_used += 1

    def reset_attempts(self):
        """Atjauno mēģinājumus uz 0 (jaunam uzdevumam)"""
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