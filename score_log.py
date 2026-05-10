# score_log.py - ScoreLog klase
# Atbild par datu persistenci: rezultātu rakstīšanu CSV failā un sesiju žurnalēšanu.
# Nodrošina datu ievadi, apstrādi un izvadi (failu apstrāde).
# Atribūti: _filename, _entries, _session_id, _timestamp
# Metodes: save_score(player), load_scores(), write_log(msg), get_top_scores()

import csv
from datetime import datetime


class ScoreLog:
    def __init__(self, filename="data/scores.csv"):
        self._filename = filename
        self._entries = []
        self._session_id = ""
        self._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save_score(self, player):
        pass

    def load_scores(self):
        pass

    def write_log(self, msg):
        pass

    def get_top_scores(self):
        pass