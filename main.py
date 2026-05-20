import math
import os
import sys

import pygame

from game import Game
from level_editor import LevelEditor
from score_log import ScoreLog
from sound_manager import SoundManager
from shader_pipeline import ShaderPipeline
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT, FPS, TITLE, FULLSCREEN,
    WHITE, BLACK, GRAY,
)


PLAY, EDITOR, SCORES, QUIT = "play", "editor", "scores", "quit"

BG       = (12,  12,  14)
DIM      = (128, 128, 132)
DIM_SOFT = (78,  78,  84)
DIM_DARK = (38,  38,  44)

PALE     = (210, 212, 216)
COLD     = (150, 162, 172)
AMBER    = (188, 172, 148)
RED      = (178, 78,  68)
ACCENT   = (170, 174, 180)


class MainMenu:

    def __init__(self):
        self._pipeline = ShaderPipeline.create(
            (SCREEN_WIDTH, SCREEN_HEIGHT), fullscreen=FULLSCREEN, shader="menu",
            display_size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
        )
        self._screen = self._pipeline.surface
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()

        self._font_title = pygame.font.SysFont("Arial",    140, bold=True)
        self._font_item  = pygame.font.SysFont("Arial",    56,  bold=True)
        self._font_idx   = pygame.font.SysFont("Consolas", 20,  bold=True)
        self._font_tag   = pygame.font.SysFont("Consolas", 22,  bold=True)
        self._font       = pygame.font.SysFont("Arial",    28)
        self._font_small = pygame.font.SysFont("Arial",    22)

        self._items = [
            (PLAY,   "SPĒLĒT",            PALE),
            (EDITOR, "LĪMEŅU REDAKTORS",  COLD),
            (SCORES, "REZULTĀTI",         AMBER),
            (QUIT,   "IZIET",             RED),
        ]

        self._logo = self._load_logo(target_h=240)

        self._selected = 0
        self._hover_amounts = [0.0] * len(self._items)
        self._name_hover    = 0.0
        self._cursor_state  = None

        self._player_name = "Spēlētājs"
        self._editing = False

        self._scores = ScoreLog()
        self._show_scores = False

        self._sound = SoundManager()
        self._sound.play_music()
        self._sound.start_ambience()

        self._running = True
        pygame.mouse.set_visible(True)

    def run(self):
        while self._running:
            self._events()
            self._update()
            self._draw()
            self._clock.tick(FPS)
            
        self._sound.stop_ambience()
        self._sound.stop_music()
        self._pipeline.shutdown()
        
        pygame.quit()
        sys.exit()

    def _update(self):
        # self._anim += (self._selected - self._anim) * 0.25
        self._sound.update_ambience()
        for i in range(len(self._items)):
            target = 1.0 if i == self._selected else 0.0
            self._hover_amounts[i] += (target - self._hover_amounts[i]) * 0.20

        pos = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())

        name_t = 1.0 if (self._editing or self._name_rect().collidepoint(pos)) else 0.0
        self._name_hover += (name_t - self._name_hover) * 0.18

        any_hot = self._name_rect().collidepoint(pos) or any(
            self._item_rect(i).collidepoint(pos) for i in range(len(self._items))
        )
        desired = pygame.SYSTEM_CURSOR_HAND if any_hot else pygame.SYSTEM_CURSOR_ARROW
        if desired != self._cursor_state:
            pygame.mouse.set_cursor(desired)
            self._cursor_state = desired

    def _events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self._running = False
                return

            if e.type == pygame.KEYDOWN:
                if self._show_scores:
                    if e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self._show_scores = False
                    continue
                if self._editing:
                    if e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        self._stop_edit()
                    elif e.key == pygame.K_BACKSPACE:
                        self._player_name = self._player_name[:-1]
                    continue
                self._menu_key(e)

            elif e.type == pygame.TEXTINPUT and self._editing:
                if len(self._player_name) < 18:
                    self._player_name += e.text

            elif e.type == pygame.MOUSEMOTION:
                self._hover(self._pipeline.scale_mouse_pos(e.pos))

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._click(self._pipeline.scale_mouse_pos(e.pos))

            if e.type == pygame.KEYDOWN and e.key == pygame.K_F1:
                self._pipeline.toggle()

    def _menu_key(self, e):
        if e.key == pygame.K_ESCAPE:
            self._running = False
        elif e.key in (pygame.K_UP, pygame.K_w):
            self._selected = (self._selected - 1) % len(self._items)
        elif e.key in (pygame.K_DOWN, pygame.K_s):
            self._selected = (self._selected + 1) % len(self._items)
        elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate()
        elif e.key == pygame.K_n:
            self._start_edit()

    def _start_edit(self):
        self._editing = True
        if self._player_name == "Spēlētājs":
            self._player_name = ""
        pygame.key.start_text_input()

    def _stop_edit(self):
        self._editing = False
        if not self._player_name.strip():
            self._player_name = "Spēlētājs"
        pygame.key.stop_text_input()

    def _hover(self, pos):
        for i in range(len(self._items)):
            if self._item_rect(i).collidepoint(pos):
                self._selected = i
                return

    def _click(self, pos):
        if self._show_scores:
            self._show_scores = False
            return
        if self._editing:
            if not self._name_rect().collidepoint(pos):
                self._stop_edit()
            return
        for i in range(len(self._items)):
            if self._item_rect(i).collidepoint(pos):
                self._selected = i
                self._activate()
                return
        if self._name_rect().collidepoint(pos):
            self._start_edit()

    def _activate(self):
        action = self._items[self._selected][0]
        self._sound.play_sound("menu_click")
        if action == PLAY:
            self._launch(lambda: Game(self._player_name).run())
        elif action == EDITOR:
            self._launch(lambda: LevelEditor().run())
        elif action == SCORES:
            self._show_scores = True
        elif action == QUIT:
            self._running = False

    def _launch(self, fn):
        self._sound.stop_ambience()
        self._fade(out=True)
        self._pipeline.shutdown()
        try:
            fn()
        finally:
            self._pipeline = ShaderPipeline.create(
                (SCREEN_WIDTH, SCREEN_HEIGHT), fullscreen=FULLSCREEN, shader="menu",
                display_size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
            )
            self._screen = self._pipeline.surface
            pygame.display.set_caption(TITLE)
            pygame.mouse.set_visible(True)
            self._cursor_state = None

        self._sound.play_music()
        self._sound.start_ambience()
        self._draw()
        self._fade(out=False)

    def _fade(self, out, frames=10):
        snap = self._screen.copy()
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        veil.fill(BLACK)
        rng = range(1, frames + 1) if out else range(frames, -1, -1)
        for i in rng:
            self._screen.blit(snap, (0, 0))
            veil.set_alpha(int(255 * i / frames))
            self._screen.blit(veil, (0, 0))
            self._pipeline.present()
            self._clock.tick(FPS)


    def _item_rect(self, i):
        w, h, gap = 680, 82, 24
        x = (SCREEN_WIDTH - w) // 2
        y = SCREEN_HEIGHT // 2 - 80 + i * (h + gap)
        return pygame.Rect(x, y, w, h)

    def _name_rect(self):
        w, h = 520, 54
        x = (SCREEN_WIDTH - w) // 2
        y = self._item_rect(len(self._items) - 1).bottom + 80
        return pygame.Rect(x, y, w, h)

    def _draw(self):
        self._screen.fill(BG)
        self._draw_title()
        self._draw_items()
        self._draw_name()
        self._draw_footer()
        if self._show_scores:
            self._draw_scores()
        self._pipeline.present()

    def _draw_title(self):
        cx = SCREEN_WIDTH // 2

        pre = self._font_tag.render("//  S Y S T E M . O N L I N E  //", True, ACCENT)
        self._screen.blit(pre, pre.get_rect(center=(cx, 180)))

        if self._logo is not None:
            title_rect = self._logo.get_rect(center=(cx, 320))
            self._screen.blit(self._logo, title_rect)
        else:
            title = self._font_title.render("CODE PORTAL 3", True, WHITE)
            title_rect = title.get_rect(center=(cx, 300))
            self._screen.blit(title, title_rect)

        frame = title_rect.inflate(140, 56)
        self._draw_brackets(frame, ACCENT, DIM_SOFT, arm=40, thickness=4)

        tag = self._font.render("// Python kodēšanas piedzīvojums //", True, DIM)
        tag_rect = tag.get_rect(center=(cx, title_rect.bottom + 38))
        self._screen.blit(tag, tag_rect)
        line_w = 220
        line_y = tag_rect.bottom + 14
        pygame.draw.line(self._screen, DIM_SOFT,
                         (cx - line_w // 2, line_y), (cx - 30, line_y), 2)
        pygame.draw.line(self._screen, DIM_SOFT,
                         (cx + 30, line_y), (cx + line_w // 2, line_y), 2)
        pygame.draw.circle(self._screen, PALE, (cx, line_y), 3)

    def _draw_brackets(self, rect, c_top, c_bot, arm=24, thickness=3):
        pygame.draw.line(self._screen, c_top, (rect.left,  rect.top), (rect.left + arm, rect.top), thickness)
        pygame.draw.line(self._screen, c_top, (rect.left,  rect.top), (rect.left, rect.top + arm), thickness)
        pygame.draw.line(self._screen, c_top, (rect.right, rect.top), (rect.right - arm, rect.top), thickness)
        pygame.draw.line(self._screen, c_top, (rect.right, rect.top), (rect.right, rect.top + arm), thickness)
        pygame.draw.line(self._screen, c_bot, (rect.left,  rect.bottom), (rect.left + arm, rect.bottom), thickness)
        pygame.draw.line(self._screen, c_bot, (rect.left,  rect.bottom), (rect.left, rect.bottom - arm), thickness)
        pygame.draw.line(self._screen, c_bot, (rect.right, rect.bottom), (rect.right - arm, rect.bottom), thickness)
        pygame.draw.line(self._screen, c_bot, (rect.right, rect.bottom), (rect.right, rect.bottom - arm), thickness)

    def _draw_items(self):
        for i, (_, label, c) in enumerate(self._items):
            rect = self._item_rect(i)
            h    = self._hover_amounts[i]

            if h > 0.005:
                for expand, alpha, radius in [
                    (34, 0.03, 22),
                    (20, 0.07, 14),
                    (10, 0.13, 10),
                ]:
                    sz = (rect.width + expand * 2, rect.height + expand * 2)
                    layer = pygame.Surface(sz, pygame.SRCALPHA)
                    pygame.draw.rect(layer, (*c, int(255 * alpha * h)),
                                     layer.get_rect(), border_radius=radius)
                    self._screen.blit(layer, (rect.x - expand, rect.y - expand))

                tint = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(tint, (*c, int(35 * h)), tint.get_rect(), border_radius=6)
                self._screen.blit(tint, rect.topleft)

                bord = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(bord, (*c, int(180 * h)),
                                 bord.get_rect(), width=2, border_radius=6)
                self._screen.blit(bord, rect.topleft)

            bar_h = int(rect.height * (0.42 + 0.50 * h))
            bar_y = rect.y + (rect.height - bar_h) // 2
            pygame.draw.rect(self._screen, c, (rect.x, bar_y, 5, bar_h))

            idx_color = self._lerp_color(DIM_SOFT, c, h)
            idx_text  = self._font_idx.render(f"0{i+1}", True, idx_color)
            self._screen.blit(idx_text, (rect.x + 20, rect.y + 12))

            pygame.draw.circle(self._screen, idx_color,
                               (rect.x + 22 + idx_text.get_width() + 6, rect.y + 23), 2)

            text_color = self._lerp_color(DIM, WHITE, h)
            slide      = int(h * 18)
            text       = self._font_item.render(label, True, text_color)
            self._screen.blit(text, text.get_rect(midleft=(rect.x + 60 + slide, rect.centery + 6)))

            if h > 0.02:
                cx = rect.right - 64 + int(h * 12)
                cy = rect.centery
                chev = pygame.Surface((28, 32), pygame.SRCALPHA)
                pygame.draw.polygon(chev, (*c, int(255 * min(h, 1.0))), [
                    (0, 0), (20, 16), (0, 32),
                ])
                self._screen.blit(chev, (cx, cy - 16))

                hint = self._font_idx.render("[ENTER]", True, c)
                hint.set_alpha(int(200 * h))
                self._screen.blit(hint, hint.get_rect(midright=(rect.right - 22, rect.bottom - 14)))

    def _draw_name(self):
        rect = self._name_rect()
        h    = self._name_hover

        if h > 0.005:
            for expand, alpha, radius in [(20, 0.05, 16), (10, 0.12, 10)]:
                sz = (rect.width + expand * 2, rect.height + expand * 2)
                layer = pygame.Surface(sz, pygame.SRCALPHA)
                pygame.draw.rect(layer, (*PALE, int(255 * alpha * h)),
                                 layer.get_rect(), border_radius=radius)
                self._screen.blit(layer, (rect.x - expand, rect.y - expand))

        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 220), bg.get_rect(), border_radius=4)
        self._screen.blit(bg, rect.topleft)

        border_color = self._lerp_color(DIM_DARK, PALE, h)
        bord = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bord, (*border_color, 255), bord.get_rect(),
                         width=2, border_radius=4)
        self._screen.blit(bord, rect.topleft)

        label_color = self._lerp_color(DIM, PALE, h)
        label       = self._font_small.render("SPĒLĒTĀJS", True, label_color)
        self._screen.blit(label, (rect.x, rect.y - 28))

        caret_color = PALE if h > 0.05 else DIM_SOFT
        caret       = self._font.render(">", True, caret_color)
        self._screen.blit(caret, caret.get_rect(midleft=(rect.x + 14, rect.centery)))

        blink_on = self._editing and (pygame.time.get_ticks() // 500) % 2 == 0
        nt = self._font.render(self._player_name + ("_" if blink_on else ""), True, WHITE)
        self._screen.blit(nt, nt.get_rect(midleft=(rect.x + 40, rect.centery)))

        if not self._editing:
            hint = self._font_small.render("[N] mainīt", True, DIM)
            self._screen.blit(hint, hint.get_rect(midright=(rect.right - 18, rect.centery)))

    def _draw_footer(self):
        cx = SCREEN_WIDTH // 2
        y  = SCREEN_HEIGHT - 50

        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 1000.0 * 2.2)
        dot   = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*AMBER, int(140 + 90 * pulse)), (7, 7), 5)
        self._screen.blit(dot, (40, y - 7))
        status = self._font_small.render("ONLINE", True, AMBER)
        self._screen.blit(status, status.get_rect(midleft=(60, y)))

        hint = "↑↓ / WS  pārvietoties     ENTER  izvēlēties     N  pārdēvēt     F1  ēnotāji     ESC  iziet"
        t    = self._font_small.render(hint, True, DIM)
        self._screen.blit(t, t.get_rect(center=(cx, y)))

        ver = self._font_small.render("v0.3", True, DIM_SOFT)
        self._screen.blit(ver, ver.get_rect(midright=(SCREEN_WIDTH - 40, y)))

    def _draw_scores(self):
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 225))
        self._screen.blit(veil, (0, 0))

        cx = SCREEN_WIDTH // 2
        title = self._font_title.render("REZULTĀTI", True, PALE)
        title_rect = title.get_rect(center=(cx, 260))
        self._screen.blit(title, title_rect)
        self._draw_brackets(title_rect.inflate(120, 50), ACCENT, DIM_SOFT,
                            arm=36, thickness=4)

        scores = self._scores.get_top_scores(limit=10)
        if not scores:
            empty = self._font_item.render("Vēl nav rezultātu", True, GRAY)
            self._screen.blit(empty, empty.get_rect(center=(cx, SCREEN_HEIGHT // 2)))
        else:
            y = 460
            for i, e in enumerate(scores):
                color = PALE if i == 0 else (COLD if i < 3 else DIM)
                row = f"{i+1:>2}.  {e['name'][:18]:<20}{e['score']:>6} pts   {e['date']}"
                t = self._font.render(row, True, color)
                self._screen.blit(t, t.get_rect(center=(cx, y)))
                y += 48

        hint = self._font_small.render("[ENTER / ESC / klikšķis] atpakaļ", True, DIM)
        self._screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 90)))

    @staticmethod
    def _load_logo(target_h=240):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "code3logo.png"
        )
        try:
            img = pygame.image.load(path).convert_alpha()
        except Exception as exc:
            print(f"[menu] logo failed to load ({exc}) — falling back to text title")
            return None
        bbox = img.get_bounding_rect()
        if bbox.width > 0 and bbox.height > 0 and bbox.size != img.get_size():
            img = img.subsurface(bbox).copy()
        h = img.get_height()
        if h != target_h and h > 0:
            ratio = target_h / h
            new_w = max(1, int(img.get_width() * ratio))
            img = pygame.transform.smoothscale(img, (new_w, target_h))
        return img

    @staticmethod
    def _lerp_color(a, b, t):
        t = max(0.0, min(1.0, t))
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )


def main():
    pygame.init()
    MainMenu().run()


if __name__ == "__main__":
    main()
