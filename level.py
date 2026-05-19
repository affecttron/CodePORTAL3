import json
import os
import random
import pygame
from task import Task
from sound_manager import SoundManager
from settings import (
    TASKS_FILE, TIME_LIMIT_PER_TASK,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    NEON_RED, NEON_YELLOW, NEON_GREEN, NEON_CYAN,
    WHITE, BLACK, DARK_GRAY,
)


TYPEWRITER_CHARS_PER_SEC = 55
TYPEWRITER_BLIP_EVERY = 2


class Level:

    def __init__(self, level_id, title, time_limit=TIME_LIMIT_PER_TASK):
        self._level_id = level_id
        self._title = title
        self._tasks = []
        self._time_limit = time_limit
        self._current_task_index = 0
        self._theme_color = NEON_CYAN
        # Local RNG so shuffling tasks doesn't perturb the global random stream
        # used by other systems (e.g. parallax silhouette generation).
        self._rng = random.Random()

        self._tw_wrapped = None
        self._tw_total = 0
        self._tw_revealed = 0.0
        self._tw_last_ms = None
        self._tw_blip_counter = 0

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

                self._rng.shuffle(self._tasks)
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
        self.reset_typewriter()
        return self.get_current_task()

    def reset_typewriter(self):
        self._tw_wrapped = None
        self._tw_total = 0
        self._tw_revealed = 0.0
        self._tw_last_ms = None
        self._tw_blip_counter = 0

    def skip_typewriter(self):
        if self._tw_wrapped is not None:
            self._tw_revealed = float(self._tw_total)

    def is_typewriter_complete(self):
        return self._tw_wrapped is not None and self._tw_revealed >= self._tw_total

    def is_complete(self):
        # An empty task list means load failed — don't auto-complete in that case.
        if not self._tasks:
            return False
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

        panel_width = 1100
        panel_height = 650
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

    def _draw_code_block(self, screen, font_normal, panel_x, panel_y, panel_w, color):
        task = self.get_current_task()
        if task is None:
            return

        code_x = panel_x + 50
        code_y = panel_y + 140
        code_w = panel_w - 100
        code_h = 330

        # Fons
        pygame.draw.rect(screen, BLACK, (code_x, code_y, code_w, code_h))
        pygame.draw.rect(screen, color, (code_x, code_y, code_w, code_h), 2)

        # Virsraksts
        labels = {
            NEON_RED: "[ Python kods ]",
            NEON_YELLOW: "[ Cikla izsekošana ]",
            NEON_GREEN: "[ Funkcijas izsaukums ]",
        }
        label_text = labels.get(color, "[ Kods ]")
        label = font_normal.render(label_text, True, color)
        screen.blit(label, (code_x + 10, code_y - 30))

        max_width = code_w - 40
        if self._tw_wrapped is None:
            self._tw_wrapped = self._wrap_question_lines(
                task.get_question(), font_normal, max_width
            )
            self._tw_total = sum(len(line) for line in self._tw_wrapped)
            self._tw_revealed = 0.0
            self._tw_last_ms = None
            self._tw_blip_counter = 0

        self._tick_typewriter()

        revealed_int = int(self._tw_revealed)
        chars_left = revealed_int
        line_y = code_y + 15
        last_line_text = ""
        for line in self._tw_wrapped:
            if chars_left <= 0:
                break
            if chars_left >= len(line):
                shown = line
                chars_left -= len(line)
            else:
                shown = line[:chars_left]
                chars_left = 0
            if shown:
                text = font_normal.render(shown, True, color)
                screen.blit(text, (code_x + 20, line_y))
            last_line_text = shown
            line_y += 26

        if not self.is_typewriter_complete():
            caret_x = code_x + 20 + font_normal.size(last_line_text)[0]
            caret_y = line_y - 26
            blink_on = (pygame.time.get_ticks() // 250) % 2 == 0
            if blink_on:
                caret_w = max(8, font_normal.size("M")[0] // 2)
                caret_h = font_normal.get_height() - 4
                pygame.draw.rect(screen, color, (caret_x, caret_y + 2, caret_w, caret_h))

    def _wrap_question_lines(self, question, font, max_width):
        wrapped = []
        for raw_line in question.split("\n"):
            if font.size(raw_line)[0] <= max_width:
                wrapped.append(raw_line)
                continue
            words = raw_line.split(" ")
            current = ""
            for word in words:
                candidate = current + word + " "
                if font.size(candidate)[0] <= max_width:
                    current = candidate
                else:
                    if current:
                        wrapped.append(current.rstrip())
                    current = word + " "
            if current:
                wrapped.append(current.rstrip())
        return wrapped

    def _tick_typewriter(self):
        if self._tw_total == 0 or self._tw_revealed >= self._tw_total:
            return
        now = pygame.time.get_ticks()
        if self._tw_last_ms is None:
            self._tw_last_ms = now
            return
        dt_ms = now - self._tw_last_ms
        self._tw_last_ms = now
        if dt_ms <= 0:
            return

        prev_int = int(self._tw_revealed)
        self._tw_revealed = min(
            float(self._tw_total),
            self._tw_revealed + dt_ms * TYPEWRITER_CHARS_PER_SEC / 1000.0,
        )
        new_int = int(self._tw_revealed)

        if new_int > prev_int:
            flat = "".join(self._tw_wrapped)
            blipped = False
            for i in range(prev_int, new_int):
                if i >= len(flat):
                    break
                if flat[i].isspace():
                    continue
                self._tw_blip_counter += 1
                if self._tw_blip_counter % TYPEWRITER_BLIP_EVERY == 0 and not blipped:
                    SoundManager().play_sound("keystroke")
                    blipped = True

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
        self._theme_color = NEON_RED

    def display_task(self, screen, font_big, font_normal):
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)
        self._draw_code_block(screen, font_normal, panel_x, panel_y, panel_w, NEON_RED)


class LoopLevel(Level):

    def __init__(self, level_id=2, title="Datu tunelis - cikli"):
        super().__init__(level_id, title)
        self._loop_type = "for/while"
        self._theme_color = NEON_YELLOW

    def display_task(self, screen, font_big, font_normal):
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)
        self._draw_code_block(screen, font_normal, panel_x, panel_y, panel_w, NEON_YELLOW)


class FunctionLevel(Level):

    def __init__(self, level_id=3, title="Galvenā servera istaba - funkcijas"):
        super().__init__(level_id, title)
        self._func_name = ""
        self._theme_color = NEON_GREEN

    def display_task(self, screen, font_big, font_normal):
        panel_x, panel_y, panel_w, panel_h = self._draw_base_ui(screen, font_big, font_normal)
        self._draw_code_block(screen, font_normal, panel_x, panel_y, panel_w, NEON_GREEN)


def create_level(level_id):
    if level_id == 1:
        return ConditionLevel()
    elif level_id == 2:
        return LoopLevel()
    elif level_id == 3:
        return FunctionLevel()
    else:
        return Level(level_id, f"Līmenis {level_id}")
