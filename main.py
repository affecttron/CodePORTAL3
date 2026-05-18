import sys

import pygame

from game import Game
from level_editor import LevelEditor
from score_log import ScoreLog
from sound_manager import SoundManager
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, FULLSCREEN,
    WHITE, BLACK, GRAY,
    NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_GREEN,
)


PLAY, EDITOR, SCORES, QUIT = "play", "editor", "scores", "quit"

BG = (10, 12, 28)
DIM = (140, 150, 185)


class MainMenu:

    def __init__(self):
        pygame.init()
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self._screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()

        self._font_title = pygame.font.SysFont("Arial", 140, bold=True)
        self._font_item = pygame.font.SysFont("Arial", 56, bold=True)
        self._font = pygame.font.SysFont("Arial", 28)
        self._font_small = pygame.font.SysFont("Arial", 22)

        self._items = [
            (PLAY,   "SPĒLĒT",            NEON_GREEN),
            (EDITOR, "LĪMEŅU REDAKTORS",  NEON_CYAN),
            (SCORES, "REZULTĀTI",         NEON_YELLOW),
            (QUIT,   "IZIET",             NEON_PINK),
        ]

        self._selected = 0
        self._anim = 0.0  

        self._player_name = "Spēlētājs"
        self._editing = False

        self._scores = ScoreLog()
        self._show_scores = False

        self._sound = SoundManager()
        self._sound.play_music()
        self._sound.start_ambience()

        self._running = True
        pygame.mouse.set_visible(True)

    # loop

    def run(self):
        while self._running:
            self._events()
            self._update()
            self._draw()
            self._clock.tick(FPS)
        self._sound.stop_ambience()
        self._sound.stop_music()
        pygame.quit()
        sys.exit()

    def _update(self):
        self._anim += (self._selected - self._anim) * 0.25
        self._sound.update_ambience()

    # input

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
                self._hover(e.pos)

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._click(e.pos)

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

    # fullscreen/ fade

    def _launch(self, fn):
        self._sound.stop_ambience()
        self._fade(out=True)
        fn()
        # Subscreen may have changed display mode / caption — restore.
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self._screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        pygame.mouse.set_visible(True)
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
            pygame.display.flip()
            self._clock.tick(FPS)

    # layoutrs

    def _item_rect(self, i):
        w, h, gap = 640, 78, 22
        x = (SCREEN_WIDTH - w) // 2
        y = SCREEN_HEIGHT // 2 - 80 + i * (h + gap)
        return pygame.Rect(x, y, w, h)

    def _name_rect(self):
        w, h = 520, 54
        x = (SCREEN_WIDTH - w) // 2
        y = self._item_rect(len(self._items) - 1).bottom + 80
        return pygame.Rect(x, y, w, h)

    # draw

    def _draw(self):
        self._screen.fill(BG)
        self._draw_title()
        self._draw_items()
        self._draw_name()
        self._draw_footer()
        if self._show_scores:
            self._draw_scores()
        pygame.display.flip()

    def _draw_title(self):
        cx = SCREEN_WIDTH // 2
        title = self._font_title.render("CODE PORTAL 3", True, WHITE)
        self._screen.blit(title, title.get_rect(center=(cx, 280)))
        tag = self._font.render("// Python kodēšanas piedzīvojums //", True, DIM)
        self._screen.blit(tag, tag.get_rect(center=(cx, 380)))

    def _draw_items(self):
        # Smooth highlight box.
        base = self._item_rect(0)
        gap = self._item_rect(1).y - self._item_rect(0).y
        hi_y = base.y + int(self._anim * gap)
        color = self._items[self._selected][2]

        hi = pygame.Rect(base.x, hi_y, base.width, base.height)
        glow = pygame.Surface((hi.width, hi.height), pygame.SRCALPHA)
        glow.fill((*color, 28))
        pygame.draw.rect(glow, (*color, 255), (0, 0, 5, hi.height))
        pygame.draw.rect(glow, (*color, 110), (0, 0, hi.width, hi.height), 2)
        self._screen.blit(glow, hi.topleft)

        for i, (_, label, c) in enumerate(self._items):
            rect = self._item_rect(i)
            is_sel = (i == self._selected)
            text = self._font_item.render(label, True, WHITE if is_sel else DIM)
            self._screen.blit(text, text.get_rect(midleft=(rect.x + 40, rect.centery)))
            if is_sel:
                ax = rect.right - 50
                ay = rect.centery
                pygame.draw.polygon(self._screen, c, [
                    (ax, ay - 12), (ax + 16, ay), (ax, ay + 12),
                ])

    def _draw_name(self):
        rect = self._name_rect()
        border = NEON_CYAN if self._editing else (60, 70, 110)
        pygame.draw.rect(self._screen, BLACK, rect)
        pygame.draw.rect(self._screen, border, rect, 2)

        label = self._font_small.render("SPĒLĒTĀJS", True, DIM)
        self._screen.blit(label, (rect.x, rect.y - 28))

        cursor = "_" if self._editing and (pygame.time.get_ticks() // 500) % 2 == 0 else ""
        nt = self._font.render(self._player_name + cursor, True, WHITE)
        self._screen.blit(nt, nt.get_rect(midleft=(rect.x + 18, rect.centery)))

        if not self._editing:
            hint = self._font_small.render("[N] mainīt", True, DIM)
            self._screen.blit(hint, hint.get_rect(midright=(rect.right - 18, rect.centery)))

    def _draw_footer(self):
        cx = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 50
        hint = "↑↓/WS  navigate     ENTER  select     N  rename     ESC  exit"
        t = self._font_small.render(hint, True, DIM)
        self._screen.blit(t, t.get_rect(center=(cx, y)))

    def _draw_scores(self):
        veil = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 225))
        self._screen.blit(veil, (0, 0))

        cx = SCREEN_WIDTH // 2
        title = self._font_title.render("REZULTĀTI", True, NEON_YELLOW)
        self._screen.blit(title, title.get_rect(center=(cx, 260)))

        scores = self._scores.get_top_scores(limit=10)
        if not scores:
            empty = self._font_item.render("Vēl nav rezultātu", True, GRAY)
            self._screen.blit(empty, empty.get_rect(center=(cx, SCREEN_HEIGHT // 2)))
        else:
            y = 460
            for i, e in enumerate(scores):
                color = NEON_GREEN if i == 0 else (NEON_CYAN if i < 3 else WHITE)
                row = f"{i+1:>2}.  {e['name'][:18]:<20}{e['score']:>6} pts   {e['date']}"
                t = self._font.render(row, True, color)
                self._screen.blit(t, t.get_rect(center=(cx, y)))
                y += 48

        hint = self._font_small.render("[ENTER / ESC / klikšķis] atpakaļ", True, DIM)
        self._screen.blit(hint, hint.get_rect(center=(cx, SCREEN_HEIGHT - 90)))


def main():
    MainMenu().run()


if __name__ == "__main__":
    main()
