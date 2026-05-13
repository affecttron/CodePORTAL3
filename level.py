import json
import os
import random
import pygame
from task import Task
from settings import (
    TASKS_FILE, TIME_LIMIT_PER_TASK, MAX_ATTEMPTS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    NEON_RED, NEON_YELLOW, NEON_GREEN, NEON_CYAN, NEON_PINK,
    WHITE, BLACK, GRAY, DARK_GRAY,
)


class Level:
    def __init__(self, level_id, title, time_limit=TIME_LIMIT_PER_TASK):
        self._level_id = level_id
        self._title = title
        self._tasks = []
        self._time_limit = time_limit
        self._current_task_index = 0
        self._theme_color = NEON_CYAN

    def load_tasks(self, tasks_file=TASKS_FILE):
        if not os.path.exists(tasks_file):
            print(f"❌ Tasks fails neatrasts: {tasks_file}")
            return False

        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for level_data in data.get("levels", []):
            if level_data["level_id"] == self._level_id:
                for task_data in level_data["tasks"]:
                    task = Task(
                        question=task_data["question"],
                        correct_answer=task_data["correct_answer"],
                        hint=task_data["hint"],
                        points=task_data["points"]
                    )
                    self._tasks.append(task)

                random.shuffle(self._tasks)
                print(f"✅ Ielādēti {len(self._tasks)} uzdevumi līmenim {self._level_id}")
                return True

        print(f"❌ Līmenis {self._level_id} nav atrasts")
        return False

    def get_current_task(self):
        if self._current_task_index < len(self._tasks):
            return self._tasks[self._current_task_index]
        return None

    def next_task(self):
        self._current_task_index += 1
        return self.get_current_task()

    def is_complete(self):
        return self._current_task_index >= len(self._tasks)

    def check_answer(self, ans):
        task = self.get_current_task()
        if task is None:
            return False
        return task.verify(ans)

    def display_task(self, screen, font_big, font_normal):
        self._draw_base_ui(screen, font_big, font_normal)

    def _draw_base_ui(self, screen, font_big, font_normal):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        panel_width = 1000
        panel_height = 600
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2

        pygame.draw.rect(screen, DARK_GRAY, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, self._theme_color, (panel_x, panel_y, panel_width, panel_height), 4)

        # Virsraksts
        title_text = font_big.render(self._title, True, self._theme_color)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 40))
        screen.blit(title_text, title_rect)

        # Progress
        progress = f"Uzdevums {self._current_task_index + 1} / {len(self._tasks)}"
        prog_text = font_normal.render(progress, True, WHITE)
        prog_rect = prog_text.get_rect(center=(SCREEN_WIDTH // 2, panel_y + 85))
        screen.blit(prog_text, prog_rect)

        return panel_x, panel_y, panel_width, panel_height

    def get_level_id(self):
        return self._level_id

    def get_title(self):
        return self._title

    def get_tasks(self):
        return self._tasks

    def get_task_count(self):
        return len(self._tasks)

    def get_current_index(self):
        return self._current_task_index

    def get_time_limit(self):
        return self._time_limit

    def get_theme_color(self):
        return self._theme_color


class ConditionLevel(Level):
    def __init__(self, level_id=1, title="Drošības vārti - if/else"):
        super().__init__(level_id, title)
        self._branch_type = "if/else"
        self._theme_color = NEON_RED  # Sarkans!

    def display_task(self, screen, font_big, font_normal):
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)

        task = self.get_current_task()
        if task is None:
            return

        code_x = panel_x + 50
        code_y = panel_y + 150
        code_w = panel_w - 100
        code_h = 300

        pygame.draw.rect(screen, BLACK, (code_x, code_y, code_w, code_h))
        pygame.draw.rect(screen, NEON_RED, (code_x, code_y, code_w, code_h), 2)

        label = font_normal.render("[ Python kods ]", True, NEON_RED)
        screen.blit(label, (code_x + 10, code_y - 30))

        question_lines = task.get_question().split("\n")
        line_y = code_y + 20
        for line in question_lines:
            text = font_normal.render(line, True, NEON_GREEN)
            screen.blit(text, (code_x + 20, line_y))
            line_y += 30


class LoopLevel(Level):
    def __init__(self, level_id=2, title="Datu tunelis - cikli"):
        super().__init__(level_id, title)
        self._loop_type = "for/while"
        self._theme_color = NEON_YELLOW  # Dzeltens!

    def display_task(self, screen, font_big, font_normal):
        # Pārdefinēta
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)

        task = self.get_current_task()
        if task is None:
            return

        code_x = panel_x + 50
        code_y = panel_y + 150
        code_w = panel_w - 100
        code_h = 300

        pygame.draw.rect(screen, BLACK, (code_x, code_y, code_w, code_h))
        pygame.draw.rect(screen, NEON_YELLOW, (code_x, code_y, code_w, code_h), 2)

        label = font_normal.render("[ Cikla izsekošana ]", True, NEON_YELLOW)
        screen.blit(label, (code_x + 10, code_y - 30))

        question_lines = task.get_question().split("\n")
        line_y = code_y + 20
        for line in question_lines:
            text = font_normal.render(line, True, NEON_YELLOW)
            screen.blit(text, (code_x + 20, line_y))
            line_y += 30


class FunctionLevel(Level):
    def __init__(self, level_id=3, title="Galvenā servera istaba - funkcijas"):
        super().__init__(level_id, title)
        self._func_name = ""
        self._theme_color = NEON_GREEN  # Zaļš!

    def display_task(self, screen, font_big, font_normal):
        # Pārdefinēta
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)

        task = self.get_current_task()
        if task is None:
            return

        code_x = panel_x + 50
        code_y = panel_y + 150
        code_w = panel_w - 100
        code_h = 300

        pygame.draw.rect(screen, BLACK, (code_x, code_y, code_w, code_h))
        pygame.draw.rect(screen, NEON_GREEN, (code_x, code_y, code_w, code_h), 2)

        label = font_normal.render("[ Funkcijas izsaukums ]", True, NEON_GREEN)
        screen.blit(label, (code_x + 10, code_y - 30))

        question_lines = task.get_question().split("\n")
        line_y = code_y + 20
        for line in question_lines:
            text = font_normal.render(line, True, NEON_CYAN)
            screen.blit(text, (code_x + 20, line_y))
            line_y += 30


def create_level(level_id):
    if level_id == 1:
        return ConditionLevel()
    elif level_id == 2:
        return LoopLevel()
    elif level_id == 3:
        return FunctionLevel()
    else:
        return Level(level_id, f"Līmenis {level_id}")
