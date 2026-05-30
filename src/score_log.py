import csv
import os
from datetime import datetime
from settings import SCORES_FILE, LOG_FILE


class ScoreLog:

    # Izveido rezultātu žurnālu ar CSV failu
    def __init__(self, filename=SCORES_FILE, log_filename=LOG_FILE):
        self._filename = filename
        self._log_filename = log_filename
        self._entries = []
        self._session_id = self._generate_session_id()
        self._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Pjabut mapei kur ievietot
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # veido csv
        self._ensure_csv_exists()

    # Ģenerē unikālu sesijas identifikatoru
    def _generate_session_id(self):
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")

    # Izveido CSV failu ar galveni ja nav
    def _ensure_csv_exists(self):
        if not os.path.exists(self._filename):
            with open(self._filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "date", "score", "level_reached", "tasks_completed"])

    # Saglabā spēlētāja rezultātu failā
    def save_score(self, player):
        try:
            with open(self._filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                safe_name = player.get_name().lstrip("=+-@|")
                writer.writerow([
                    safe_name,
                    self._timestamp,
                    player.get_score(),
                    player.get_level_reached(),
                    player.get_tasks_completed(),
                ])
            print(f"Saglabāts: {player.get_name()} - {player.get_score()} pts")
            self.write_log(f"Score saved: {player.get_name()} = {player.get_score()}")
            return True
        except Exception as e:
            print(f"Kļūda saglabājot: {e}")
            return False

    # Ielādē visus rezultātus no faila
    def load_scores(self):
        if not os.path.exists(self._filename):
            return []

        scores = []
        try:
            with open(self._filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        scores.append({
                            "name": row["name"],
                            "date": row["date"],
                            "score": int(row["score"]),
                            "level_reached": int(row["level_reached"]),
                            "tasks_completed": int(row["tasks_completed"]),
                        })
                    except (ValueError, KeyError):
                        print(f"Skipping malformed score row: {row}")
        except Exception as e:
            print(f"Kļūda ielādējot: {e}")
            return []
        self._entries = scores
        return scores

    # Atgriež augstākos rezultātus sakārtotus
    def get_top_scores(self, limit=5):
        scores = self.load_scores()
        # sorteja
        sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)
        return sorted_scores[:limit]

    # Atgriež konkrēta spēlētāja labāko rezultātu
    def get_player_best(self, player_name):
        scores = self.load_scores()
        player_scores = [s for s in scores if s["name"] == player_name]
        if not player_scores:
            return None
        return max(player_scores, key=lambda x: x["score"])

    # Atgriež kopējo spēļu skaitu
    def get_total_games(self):
        return len(self.load_scores())

    # Aprēķina vidējo rezultātu visām spēlēm
    def get_average_score(self):
        scores = self.load_scores()
        if not scores:
            return 0
        total = sum(s["score"] for s in scores)
        return total // len(scores)

    # Ieraksta ziņojumu žurnāla failā
    def write_log(self, msg):
        try:
            os.makedirs(os.path.dirname(self._log_filename), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_filename, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [{self._session_id}] {msg}\n")
        except Exception as e:
            print(f"Kļūda: {e}")

    # Atgriež sesijas identifikatoru
    def get_session_id(self):
        return self._session_id

    # Atgriež rezultātu faila ceļu
    def get_filename(self):
        return self._filename
