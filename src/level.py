import json
import os
import random
import pygame
from task import Task
from sound_manager import SoundManager
from ui_utils import dim_color, draw_corner_accents
from settings import (
    TASKS_FILE, TIME_LIMIT_PER_TASK,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    NEON_RED, NEON_YELLOW, NEON_GREEN, NEON_CYAN, NEON_PINK,
    OVERCLOCK_DURATION_MS, OVERCLOCK_BONUS_POINTS,
    PORTAL_THEME_COLORS,
)


TYPEWRITER_CHARS_PER_SEC = 55
TYPEWRITER_BLIP_EVERY = 2

PANEL_WIDTH = 1100
PANEL_HEIGHT = 650
PANEL_PADDING_X = 26
TITLE_BAR_HEIGHT = 50
SUBTITLE_BAR_HEIGHT = 28
CODE_BLOCK_HEIGHT = 360
INPUT_AREA_HEIGHT = 56
HINT_AREA_HEIGHT = 48
OVERCLOCK_AREA_HEIGHT = 32
PANEL_BG = (10, 12, 16)
CODE_BG = (6, 8, 10)


class Level:

    _code_label = "DECODE: payload"

    # Izveido līmeni ar nosaukumu un laika limitu
    def __init__(self, level_id, title, time_limit=TIME_LIMIT_PER_TASK, overclock_ms=OVERCLOCK_DURATION_MS):
        self._level_id = level_id
        self._title = title
        self._tasks = []
        self._time_limit = time_limit
        self._overclock_duration_ms = overclock_ms
        self._current_task_index = 0
        self._theme_color = PORTAL_THEME_COLORS.get(level_id, NEON_CYAN)
        # rng lai sajauktu uzdevumu secību
        self._rng = random.Random()

        self._tw_wrapped = None
        self._tw_total = 0
        self._tw_revealed = 0.0
        self._tw_last_ms = None
        self._tw_blip_counter = 0

        # OVERCLOCK laika logs bonusa punktiem uz uzdevumu
        self._oc_started_ms = None
        self._oc_consumed = False
        self._oc_voided = False

        # Kešotas virsmas, izveido vienu reizi un pārlieto
        self._sound = SoundManager()
        self._overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._overlay_surf.fill((0, 0, 0, 215))
        self._title_tint_surf = None
        self._scanline_surf = None
        self._code_label_surf = None
        self._oc_surf_cache = {}
        self._mono_cache = {}

    # Ielādē uzdevumus no JSON faila
    def load_tasks(self, tasks_file=TASKS_FILE):
        if not os.path.exists(tasks_file):
            print(f"Tasks fails neatrasts: {tasks_file}")
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
                print(f"Ieladeti {len(self._tasks)} uzdevumi limenim {self._level_id}")
                return True

        print(f"Limenis {self._level_id} nav atrasts")
        return False

    # Ierobežo uzdevumu skaitu
    def set_task_limit(self, n):
        if n < len(self._tasks):
            self._tasks = self._tasks[:n]

    # Atgriež overclock laika logu milisekundēs
    def get_overclock_duration_ms(self):
        return self._overclock_duration_ms

    # Atgriež pašreizējo uzdevumu
    def get_current_task(self):
        if self._current_task_index < len(self._tasks):
            return self._tasks[self._current_task_index]
        return None

    # Pāriet uz nākamo uzdevumu
    def next_task(self):
        self._current_task_index += 1
        self.reset_typewriter()
        return self.get_current_task()

    # Atiestata typewriter animāciju jaunam tekstam
    def reset_typewriter(self):
        self._tw_wrapped = None
        self._tw_total = 0
        self._tw_revealed = 0.0
        self._tw_last_ms = None
        self._tw_blip_counter = 0
        self._oc_started_ms = None
        self._oc_consumed = False
        self._oc_voided = False

    # Uzreiz parāda visu tekstu
    def skip_typewriter(self):
        if self._tw_wrapped is not None:
            self._tw_revealed = float(self._tw_total)

    # Vai typewriter animācija pabeigta
    def is_typewriter_complete(self):
        return self._tw_wrapped is not None and self._tw_revealed >= self._tw_total

    # Vai visi uzdevumi pabeigti
    def is_complete(self):
        # Tukšs saraksts nozīmē ielādes kļūdu, nepabeigt automātiski
        if not self._tasks:
            return False
        return self._current_task_index >= len(self._tasks)

    # Pārbauda atbildi pret pašreizējo uzdevumu
    def check_answer(self, ans):
        task = self.get_current_task()
        if task is None:
            return False
        return task.verify(ans)

    # Zīmē uzdevuma UI un atgriež izkārtojumu
    def display_task(self, screen, font_normal, attempts=0, max_attempts=3):
        layout = self.get_panel_layout()
        self._draw_base_ui(screen, layout, attempts, max_attempts)
        self._draw_code_block(screen, font_normal, layout["code"])
        self._ensure_overclock_started()
        self._draw_overclock_strip(screen, layout["overclock"])
        return layout

    # Aprēķina un atgriež paneļa elementu pozīcijas
    def get_panel_layout(self):
        panel_x = (SCREEN_WIDTH - PANEL_WIDTH) // 2
        panel_y = (SCREEN_HEIGHT - PANEL_HEIGHT) // 2
        panel = pygame.Rect(panel_x, panel_y, PANEL_WIDTH, PANEL_HEIGHT)
        code = pygame.Rect(
            panel_x + PANEL_PADDING_X,
            panel_y + TITLE_BAR_HEIGHT + SUBTITLE_BAR_HEIGHT + 12,
            PANEL_WIDTH - 2 * PANEL_PADDING_X,
            CODE_BLOCK_HEIGHT,
        )
        overclock = pygame.Rect(
            panel_x + PANEL_PADDING_X,
            code.bottom + 12,
            PANEL_WIDTH - 2 * PANEL_PADDING_X,
            OVERCLOCK_AREA_HEIGHT,
        )
        input_rect = pygame.Rect(
            panel_x + PANEL_PADDING_X,
            overclock.bottom + 10,
            PANEL_WIDTH - 2 * PANEL_PADDING_X,
            INPUT_AREA_HEIGHT,
        )
        hint = pygame.Rect(
            panel_x + PANEL_PADDING_X,
            input_rect.bottom + 14,
            PANEL_WIDTH - 2 * PANEL_PADDING_X,
            HINT_AREA_HEIGHT,
        )
        return {
            "panel": panel,
            "code": code,
            "overclock": overclock,
            "input": input_rect,
            "hint": hint,
        }

    # Aptumšo krāsu par norādītu koeficientu
    def _dim_color(self, color, factor=0.4):
        return dim_color(color, factor)

    # Atgriež kešotu monospacea fontu pēc izmēra
    _MONO_CACHE_LIMIT = 16

    def _mono_font(self, size, bold=False):
        key = (size, bold)
        if key not in self._mono_cache:
            if len(self._mono_cache) >= self._MONO_CACHE_LIMIT:
                self._mono_cache.pop(next(iter(self._mono_cache)))
            self._mono_cache[key] = pygame.font.SysFont("bahnschrift", size, bold=bold)
        return self._mono_cache[key]

    # Ģenerē sesijas ID no uzdevuma teksta
    def _session_id(self):
        task = self.get_current_task()
        if task is None:
            return "0x0000"
        h = sum(ord(c) for c in task.get_question()) & 0xFFFF
        return f"0x{h:04X}"

    # Zīmē pamata paneļa rāmi un virsrakstu
    def _draw_base_ui(self, screen, layout, attempts, max_attempts=3):
        panel = layout["panel"]
        color = self._theme_color
        dim = self._dim_color(color, 0.45)
        dimmer = self._dim_color(color, 0.22)

        screen.blit(self._overlay_surf, (0, 0))

        pygame.draw.rect(screen, PANEL_BG, panel)

        title_bar = pygame.Rect(panel.x, panel.y, panel.w, TITLE_BAR_HEIGHT)
        if self._title_tint_surf is None:
            self._title_tint_surf = pygame.Surface((title_bar.w, title_bar.h), pygame.SRCALPHA)
            self._title_tint_surf.fill((color[0], color[1], color[2], 26))
        screen.blit(self._title_tint_surf, title_bar.topleft)
        pygame.draw.line(
            screen, dim,
            (title_bar.left, title_bar.bottom - 1),
            (title_bar.right, title_bar.bottom - 1),
            1,
        )

        font_chip = self._mono_font(22, bold=True)
        slug = self._title.upper().replace(" ", "_")
        chip = f"[ {slug} // {self._current_task_index + 1:02d}/{len(self._tasks):02d} ]"
        screen.blit(font_chip.render(chip, True, color), (panel.x + 18, panel.y + 13))

        self._draw_attempt_dots(screen, panel, attempts, max_attempts)

        font_chip_sm = self._mono_font(16, bold=True)
        rec_blink = (pygame.time.get_ticks() // 500) % 2 == 0
        if rec_blink:
            pygame.draw.circle(screen, color, (panel.right - 140, panel.y + 25), 5)
        rec_color = color if rec_blink else dim
        screen.blit(font_chip_sm.render("REC", True, rec_color), (panel.right - 128, panel.y + 17))
        screen.blit(font_chip_sm.render("[ x ]", True, dim), (panel.right - 75, panel.y + 17))

        subtitle_bar = pygame.Rect(panel.x, title_bar.bottom, panel.w, SUBTITLE_BAR_HEIGHT)
        font_sub = self._mono_font(15)
        prompt = "root@portal:~#"
        cmd = f" ./decrypt --task={self._current_task_index + 1:02d}/{len(self._tasks):02d} --sig={self._session_id()}"
        status = "[decrypting...]" if not self.is_typewriter_complete() else "[ready]"
        sub_x = panel.x + 18
        sub_y = subtitle_bar.y + 6
        prompt_surf = font_sub.render(prompt, True, color)
        cmd_surf = font_sub.render(cmd, True, dim)
        status_surf = font_sub.render(status, True, color if status == "[ready]" else dimmer)
        screen.blit(prompt_surf, (sub_x, sub_y))
        screen.blit(cmd_surf, (sub_x + prompt_surf.get_width(), sub_y))
        screen.blit(status_surf, (sub_x + prompt_surf.get_width() + cmd_surf.get_width() + 12, sub_y))
        pygame.draw.line(
            screen, dimmer,
            (subtitle_bar.left, subtitle_bar.bottom - 1),
            (subtitle_bar.right, subtitle_bar.bottom - 1),
            1,
        )

        pygame.draw.rect(screen, color, panel, 2)
        draw_corner_accents(screen, panel, color)

    # Zīmē mēģinājumu punktus virsrakstjoslā
    def _draw_attempt_dots(self, screen, panel, attempts, max_attempts=3):
        color = self._theme_color
        dim = self._dim_color(color, 0.35)
        font_label = self._mono_font(14, bold=True)
        label = font_label.render("ATTEMPTS", True, dim)
        label_x = panel.right - 270
        screen.blit(label, (label_x, panel.y + 19))
        dot_x0 = label_x + label.get_width() + 10
        dot_y = panel.y + 26
        used = min(attempts, max_attempts)
        for i in range(max_attempts):
            cx = dot_x0 + i * 14
            if i < (max_attempts - used):
                pygame.draw.circle(screen, color, (cx, dot_y), 5)
            else:
                pygame.draw.circle(screen, dim, (cx, dot_y), 5, 1)

    # Zīmē CRT skenlīniju efektu apgabalam
    def _draw_scanlines(self, screen, rect, color):
        if self._scanline_surf is None:
            surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            line_color = (color[0], color[1], color[2], 14)
            for y in range(0, rect.h, 3):
                pygame.draw.line(surf, line_color, (0, y), (rect.w, y))
            self._scanline_surf = surf
        screen.blit(self._scanline_surf, rect.topleft)

    # Zīmē koda bloku ar typewriter animāciju
    def _draw_code_block(self, screen, font_normal, code_rect):
        task = self.get_current_task()
        if task is None:
            return

        color = self._theme_color
        dim = self._dim_color(color, 0.45)
        gutter_dim = self._dim_color(color, 0.35)

        pygame.draw.rect(screen, CODE_BG, code_rect)
        pygame.draw.rect(screen, dim, code_rect, 1)

        if self._code_label_surf is None:
            _font_label = self._mono_font(14, bold=True)
            self._code_label_surf = _font_label.render(f"[ {self._code_label} ]", True, color)
        label_surf = self._code_label_surf
        label_bg = pygame.Rect(code_rect.x + 12, code_rect.y - label_surf.get_height() // 2,
                               label_surf.get_width() + 12, label_surf.get_height())
        pygame.draw.rect(screen, PANEL_BG, label_bg)
        screen.blit(label_surf, (label_bg.x + 6, label_bg.y))

        gutter_w = 64
        text_pad_x = 14
        text_pad_y = 18
        line_h = 26

        max_width = code_rect.w - gutter_w - text_pad_x * 2
        if self._tw_wrapped is None:
            self._tw_wrapped = self._wrap_question_lines(
                task.get_question(), font_normal, max_width
            )
            self._tw_total = sum(len(line) for line in self._tw_wrapped)
            self._tw_revealed = 0.0
            self._tw_last_ms = None
            self._tw_blip_counter = 0

        self._tick_typewriter()

        pygame.draw.line(
            screen, dim,
            (code_rect.x + gutter_w, code_rect.y + 4),
            (code_rect.x + gutter_w, code_rect.bottom - 4),
            1,
        )

        font_gutter = self._mono_font(font_normal.get_height() - 6, bold=False)
        text_start_x = code_rect.x + gutter_w + text_pad_x

        revealed_int = int(self._tw_revealed)
        chars_left = revealed_int
        line_y = code_rect.y + text_pad_y
        last_line_text = ""
        last_line_index = 0
        for i, line in enumerate(self._tw_wrapped):
            num_surf = font_gutter.render(f"{i + 1:03d}", True, gutter_dim)
            screen.blit(num_surf, (code_rect.x + gutter_w - num_surf.get_width() - 10, line_y + 2))

            if chars_left <= 0:
                line_y += line_h
                continue
            if chars_left >= len(line):
                shown = line
                chars_left -= len(line)
            else:
                shown = line[:chars_left]
                chars_left = 0
            if shown:
                text = font_normal.render(shown, True, color)
                screen.blit(text, (text_start_x, line_y))
            last_line_text = shown
            last_line_index = i
            line_y += line_h

        if not self.is_typewriter_complete():
            caret_x = text_start_x + font_normal.size(last_line_text)[0]
            caret_y = code_rect.y + text_pad_y + last_line_index * line_h
            blink_on = (pygame.time.get_ticks() // 250) % 2 == 0
            if blink_on:
                caret_w = max(8, font_normal.size("M")[0])
                caret_h = font_normal.get_height() - 4
                pygame.draw.rect(screen, color, (caret_x, caret_y + 2, caret_w, caret_h))

        self._draw_scanlines(screen, code_rect, color)

    # Sadala tekstu rindās pēc platuma
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

    # Atjaunina typewriter animācijas progresu
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
            flat = "".join(self._tw_wrapped or [])
            blipped = False
            for i in range(prev_int, new_int):
                if i >= len(flat):
                    break
                if flat[i].isspace():
                    continue
                self._tw_blip_counter += 1
                if self._tw_blip_counter % TYPEWRITER_BLIP_EVERY == 0 and not blipped:
                    self._sound.play_sound("keystroke")
                    blipped = True

    # === OVERCLOCK ===
    # Sāk overclock taimeri pēc typewriter
    def _ensure_overclock_started(self):
        if self._oc_started_ms is None and self.is_typewriter_complete():
            self._oc_started_ms = pygame.time.get_ticks()

    # Atgriež atlikušo overclock laiku ms
    def get_overclock_remaining_ms(self):
        if self._oc_started_ms is None:
            return self._overclock_duration_ms
        elapsed = pygame.time.get_ticks() - self._oc_started_ms
        return max(0, self._overclock_duration_ms - elapsed)

    # Vai overclock logs pašlaik aktīvs
    def is_overclock_active(self):
        return (
            self._oc_started_ms is not None
            and not self._oc_consumed
            and not self._oc_voided
            and self.get_overclock_remaining_ms() > 0
        )

    # Patērē overclock bonusu un atgriež punktus
    def consume_overclock_bonus(self):
        if not self.is_overclock_active():
            return 0
        self._oc_consumed = True
        return OVERCLOCK_BONUS_POINTS

    # Anulē overclock logu pēc nepareizas atbildes
    def void_overclock(self):
        # Anulē overclock logu pēc nepareizas atbildes
        self._oc_voided = True

    # Atgriež overclock stāvokļa tekstu
    def _oc_state(self):
        if not self.is_typewriter_complete() or self._oc_started_ms is None:
            return "standby"
        if self._oc_voided:
            return "voided"
        if self._oc_consumed or self.get_overclock_remaining_ms() <= 0:
            return "expired"
        frac = self.get_overclock_remaining_ms() / self._overclock_duration_ms
        if frac < 0.15:
            return "critical"
        if frac < 0.35:
            return "warning"
        return "active"

    # Atgriež krāsu paleti pēc overclock stāvokļa
    def _oc_palette(self, state):
        color = self._theme_color
        if state == "standby":
            return (
                self._dim_color(color, 0.45),
                self._dim_color(color, 0.25),
                self._dim_color(color, 0.30),
                self._dim_color(color, 0.18),
            )
        if state == "critical":
            return (NEON_RED, self._dim_color(NEON_RED, 0.45),
                    NEON_RED, self._dim_color(NEON_RED, 0.20))
        if state == "warning":
            return (NEON_YELLOW, self._dim_color(NEON_YELLOW, 0.45),
                    NEON_YELLOW, self._dim_color(NEON_YELLOW, 0.20))
        if state == "expired":
            return (self._dim_color(NEON_RED, 0.55),
                    self._dim_color(NEON_RED, 0.30),
                    self._dim_color(NEON_RED, 0.30),
                    self._dim_color(NEON_RED, 0.15))
        if state == "voided":
            return (self._dim_color(NEON_RED, 0.75),
                    self._dim_color(NEON_RED, 0.35),
                    self._dim_color(NEON_RED, 0.35),
                    self._dim_color(NEON_RED, 0.18))
        return (color, self._dim_color(color, 0.45),
                color, self._dim_color(color, 0.20))

    # Atgriež ciparu tekstu taimera displejam
    def _oc_digits_text(self, state):
        if state == "standby":
            return "--.---s"
        if state == "expired":
            return "00.000s"
        if state == "voided":
            return "##.###s"
        secs = max(0, self.get_overclock_remaining_ms()) / 1000.0
        return f"{secs:06.3f}s"

    # Atgriež statusa etiķetes tekstu
    def _oc_badge_text(self, state):
        if state == "standby":
            return "STANDBY"
        if state == "expired":
            return "EXPIRED"
        if state == "voided":
            return "VOIDED"
        return f"+{OVERCLOCK_BONUS_POINTS} PT"

    # Zīmē overclock joslu ar taimeri un statusu
    def _draw_overclock_strip(self, screen, rect):
        state = self._oc_state()
        primary, accent, bar_color, bar_dim = self._oc_palette(state)
        now = pygame.time.get_ticks()

        pygame.draw.rect(screen, CODE_BG, rect)

        border_color = primary
        if state == "critical" and (now // 100) % 2:
            border_color = accent
        pygame.draw.rect(screen, border_color, rect, 1)

        # Kreisā vertikālā akcenta svītra
        pygame.draw.line(screen, primary, (rect.x, rect.y), (rect.x, rect.bottom), 3)

        # Izveido teksta virsmu kešu pirmajā reizē
        if state not in self._oc_surf_cache:
            label_font = self._mono_font(15, bold=True)
            badge_font = self._mono_font(14, bold=True)
            self._oc_surf_cache[state] = {
                "label":   label_font.render("OVERCLOCK", True, primary),
                "sep":     label_font.render("::", True, accent),
                "badge":   badge_font.render(self._oc_badge_text(state), True, primary),
                "open_b":  badge_font.render("[", True, accent),
                "close_b": badge_font.render("]", True, accent),
            }
        cached = self._oc_surf_cache[state]

        label_surf = cached["label"]
        label_x = rect.x + 14
        label_y = rect.y + (rect.h - label_surf.get_height()) // 2
        screen.blit(label_surf, (label_x, label_y))

        sep_x = label_x + label_surf.get_width() + 8
        sep_surf = cached["sep"]
        screen.blit(sep_surf, (sep_x, label_y))

        digit_font = self._mono_font(17, bold=True)
        digits_text = self._oc_digits_text(state)
        digit_jitter = 1 if (state == "critical" and (now // 80) % 3 == 0) else 0
        digits_surf = digit_font.render(digits_text, True, primary)
        digit_x = sep_x + sep_surf.get_width() + 10
        digit_y = rect.y + (rect.h - digits_surf.get_height()) // 2
        screen.blit(digits_surf, (digit_x + digit_jitter, digit_y))

        badge_surf = cached["badge"]
        badge_w = badge_surf.get_width()
        badge_pad = 18

        # Josla sākas pēc skaitļu platuma, lai taimeris to nepārvieto
        bar_x = digit_x + digit_font.size("00.000s")[0] + 22
        bar_right = rect.right - badge_pad - badge_w - 26
        bar_w = max(0, bar_right - bar_x)
        bar_h = 12
        bar_y = rect.y + (rect.h - bar_h) // 2

        n_segments = 24
        seg_gap = 2
        seg_w = max(2.0, (bar_w - (n_segments - 1) * seg_gap) / n_segments)

        if state == "standby":
            fraction = 1.0
        elif state in ("expired", "voided"):
            fraction = 0.0
        else:
            fraction = self.get_overclock_remaining_ms() / self._overclock_duration_ms

        filled = int(round(fraction * n_segments))
        for i in range(n_segments):
            sx = bar_x + i * (seg_w + seg_gap)
            seg_rect = pygame.Rect(int(sx), bar_y, int(seg_w), bar_h)
            if i < filled:
                fill = bar_dim if state == "standby" else bar_color
                pygame.draw.rect(screen, fill, seg_rect)
            else:
                pygame.draw.rect(screen, bar_dim, seg_rect, 1)

        # Iekavota etiķete labajā pusē ar statusu
        open_b  = cached["open_b"]
        close_b = cached["close_b"]
        badge_x = rect.right - badge_pad - badge_w
        badge_y = rect.y + (rect.h - badge_surf.get_height()) // 2
        screen.blit(open_b,  (badge_x - open_b.get_width() - 4, badge_y))
        screen.blit(badge_surf, (badge_x, badge_y))
        screen.blit(close_b, (badge_x + badge_w + 4, badge_y))

    # Atgriež līmeņa ID numuru
    def get_level_id(self):
        return self._level_id

    # Atgriež līmeņa nosaukumu
    def get_title(self):
        return self._title

    # Atgriež uzdevumu sarakstu
    def get_tasks(self):
        return self._tasks

    # Atgriež uzdevumu skaitu
    def get_task_count(self):
        return len(self._tasks)

    # Atgriež pašreizējā uzdevuma indeksu
    def get_current_index(self):
        return self._current_task_index

    # Atgriež laika limitu sekundēs
    def get_time_limit(self):
        return self._time_limit

    # Atgriež līmeņa tēmas krāsu
    def get_theme_color(self):
        return self._theme_color


class ConditionLevel(Level):

    _code_label = "DECODE: python.if_else"

    # Izveido if/else nosacījumu līmeni
    def __init__(self, level_id=1, title="Drošības vārti - if/else", overclock_ms=OVERCLOCK_DURATION_MS):
        super().__init__(level_id, title, overclock_ms=overclock_ms)
        self._branch_type = "if/else"


class LoopLevel(Level):

    _code_label = "DECODE: python.loop"

    # Izveido ciklu tēmas līmeni
    def __init__(self, level_id=2, title="Datu tunelis - cikli", overclock_ms=OVERCLOCK_DURATION_MS):
        super().__init__(level_id, title, overclock_ms=overclock_ms)
        self._loop_type = "for/while"


class FunctionLevel(Level):

    _code_label = "DECODE: python.function"

    # Izveido funkciju tēmas līmeni
    def __init__(self, level_id=3, title="Galvenā servera istaba - funkcijas", overclock_ms=OVERCLOCK_DURATION_MS):
        super().__init__(level_id, title, overclock_ms=overclock_ms)


class AdvancedLevel(Level):

    _code_label = "DECODE: python.advanced"

    # Izveido sarežģītu algoritmu līmeni
    def __init__(self, level_id=7, title="Kvantu matrica", overclock_ms=OVERCLOCK_DURATION_MS):
        super().__init__(level_id, title, overclock_ms=overclock_ms)


class ExpertLevel(Level):

    _code_label = "DECODE: python.expert"

    # Izveido ekspertu līmeni ar baltu tēmu
    def __init__(self, level_id=9, title="Singularitāte", overclock_ms=OVERCLOCK_DURATION_MS):
        super().__init__(level_id, title, overclock_ms=overclock_ms)


_LEVEL_CATALOGUE = {
    1: (ConditionLevel, "Drošības vārti - if/else nosacījumi"),
    2: (LoopLevel,      "Datu tunelis - for/while cikli"),
    3: (FunctionLevel,  "Galvenā servera istaba - funkcijas"),
    4: (ConditionLevel, "Šifrēšanas mezgls - sarežģīti nosacījumi"),
    5: (LoopLevel,      "Dziļais kodols - ciklu kombinācijas"),
    6: (FunctionLevel,  "AI kontroles centrs - funkciju loģika"),
    7: (AdvancedLevel,  "Kvantu matrica - algoritmu izaicinājumi"),
    8: (AdvancedLevel,  "Neironu tīkls - datu manipulācija"),
    9: (ExpertLevel,    "Singularitāte - elite programmēšanas tests"),
}


# Izveido pareizā tipa līmeni pēc ID
def create_level(level_id, overclock_ms=OVERCLOCK_DURATION_MS):
    entry = _LEVEL_CATALOGUE.get(level_id)
    if entry is None:
        return Level(level_id, f"Limenis {level_id}", overclock_ms=overclock_ms)
    cls, title = entry
    return cls(level_id=level_id, title=title, overclock_ms=overclock_ms)
