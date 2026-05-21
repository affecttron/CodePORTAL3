import math
import pygame
import user_config as cfg_mod

BG = (12, 12, 14)
DIM = (128, 128, 132)
DIM_SOFT = (78, 78, 84)
DIM_DARK = (38, 38, 44)
PALE = (210, 212, 216)
COLD = (150, 162, 172)
AMBER = (188, 172, 148)
ACCENT = (170, 174, 180)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON = (100, 200, 160)

W = 2560
H = 1440


class SettingsMenu:
    def __init__(self, screen: pygame.Surface, pipeline, clock, sound_manager):
        self._screen = screen
        self._pipeline = pipeline
        self._clock = clock
        self._sound = sound_manager

        self._cfg = cfg_mod.load()
        self._original_cfg = dict(self._cfg)

        self._font_title = pygame.font.SysFont("Arial", 90, bold=True)
        self._font_head = pygame.font.SysFont("Consolas", 26, bold=True)
        self._font = pygame.font.SysFont("Arial", 38, bold=True)
        self._font_val = pygame.font.SysFont("Consolas", 34)
        self._font_small = pygame.font.SysFont("Arial", 24)

        self._res_idx = self._find_res_idx()
        self._mode_idx = self._find_mode_idx()

        self._rows = [
            "resolution",
            "window_mode",
            "sound_volume",
            "music_volume",
            "ambience_volume",
        ]
        self._labels = {
            "resolution": "IZŠĶIRTSPĒJA",
            "window_mode": "LOGA REŽĪMS",
            "sound_volume": "EFEKTU SKAĻUMS",
            "music_volume": "MŪZIKAS SKAĻUMS",
            "ambience_volume": "FONA SKAĻUMS",
        }
        self._colors = {
            "resolution": COLD,
            "window_mode": AMBER,
            "sound_volume": NEON,
            "music_volume": NEON,
            "ambience_volume": NEON,
        }

        self._selected = 0
        self._hover = [0.0] * len(self._rows)
        self._result = None

        self._back_hover = 0.0
        self._save_hover = 0.0
        self._cursor_state = None

        self._dragging = None

    def run(self) -> bool:
        while self._result is None:
            self._events()
            self._update()
            self._draw()
            self._clock.tick(60)
        return self._result == "save"

    def _find_res_idx(self):
        r = tuple(self._cfg["resolution"])
        for i, res in enumerate(cfg_mod.RESOLUTIONS):
            if res == r:
                return i
        return len(cfg_mod.RESOLUTIONS) - 1

    def _find_mode_idx(self):
        m = self._cfg["window_mode"]
        try:
            return cfg_mod.WINDOW_MODES.index(m)
        except ValueError:
            return 0

    def _row_rect(self, i):
        w, h, gap = 1100, 88, 20
        x = (W - w) // 2
        top = H // 2 - 230
        y = top + i * (h + gap)
        return pygame.Rect(x, y, w, h)

    def _back_rect(self):
        return pygame.Rect((W - 1100) // 2, H - 160, 520, 72)

    def _save_rect(self):
        return pygame.Rect((W - 1100) // 2 + 580, H - 160, 520, 72)

    def _slider_track(self, row_rect):
        x = row_rect.x + 560
        y = row_rect.centery
        w = row_rect.right - x - 30
        return x, y, w

    def _events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self._result = "cancel"

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self._result = "cancel"
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self._selected = (self._selected - 1) % len(self._rows)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self._selected = (self._selected + 1) % len(self._rows)
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self._step(-1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self._step(1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    row = self._rows[self._selected]
                    if row not in ("sound_volume", "music_volume", "ambience_volume"):
                        self._step(1)

            elif e.type == pygame.MOUSEMOTION:
                pos = self._pipeline.scale_mouse_pos(e.pos)
                if self._dragging is not None:
                    self._drag_update(pos)
                else:
                    for i in range(len(self._rows)):
                        if self._row_rect(i).collidepoint(pos):
                            self._selected = i

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = self._pipeline.scale_mouse_pos(e.pos)
                if self._back_rect().collidepoint(pos):
                    self._result = "cancel"
                elif self._save_rect().collidepoint(pos):
                    self._do_save()
                else:
                    for i, row in enumerate(self._rows):
                        r = self._row_rect(i)
                        if r.collidepoint(pos):
                            self._selected = i
                            if row in ("sound_volume", "music_volume", "ambience_volume"):
                                self._dragging = row
                                self._drag_update(pos)
                            else:
                                self._step(1)

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self._dragging = None

    def _drag_update(self, pos):
        if self._dragging is None:
            return
        i = self._rows.index(self._dragging)
        r = self._row_rect(i)
        x, _, w = self._slider_track(r)
        val = max(0.0, min(1.0, (pos[0] - x) / w))
        self._cfg[self._dragging] = round(val, 2)
        self._sound.set_volume(self._cfg["sound_volume"])
        self._sound.set_music_volume(self._cfg["music_volume"])
        self._sound.set_ambience_volume(self._cfg["ambience_volume"])

    def _step(self, direction):
        row = self._rows[self._selected]
        if row == "resolution":
            self._res_idx = (self._res_idx + direction) % len(cfg_mod.RESOLUTIONS)
            self._cfg["resolution"] = list(cfg_mod.RESOLUTIONS[self._res_idx])
        elif row == "window_mode":
            self._mode_idx = (self._mode_idx + direction) % len(cfg_mod.WINDOW_MODES)
            self._cfg["window_mode"] = cfg_mod.WINDOW_MODES[self._mode_idx]

    def _do_save(self):
        cfg_mod.save(self._cfg)
        cfg_mod.apply(self._cfg)
        self._result = "save"

    def _update(self):
        pos = self._pipeline.scale_mouse_pos(pygame.mouse.get_pos())
        for i in range(len(self._rows)):
            target = 1.0 if i == self._selected else 0.0
            self._hover[i] += (target - self._hover[i]) * 0.20

        bh = 1.0 if self._back_rect().collidepoint(pos) else 0.0
        sh = 1.0 if self._save_rect().collidepoint(pos) else 0.0
        self._back_hover += (bh - self._back_hover) * 0.20
        self._save_hover += (sh - self._save_hover) * 0.20

        any_hot = (
            self._back_rect().collidepoint(pos)
            or self._save_rect().collidepoint(pos)
            or any(self._row_rect(i).collidepoint(pos) for i in range(len(self._rows)))
        )
        desired = pygame.SYSTEM_CURSOR_HAND if any_hot else pygame.SYSTEM_CURSOR_ARROW
        if desired != self._cursor_state:
            pygame.mouse.set_cursor(desired)
            self._cursor_state = desired

    def _draw(self):
        self._screen.fill(BG)
        self._draw_title()
        self._draw_rows()
        self._draw_buttons()
        self._pipeline.present()

    def _draw_title(self):
        cx = W // 2
        tag = self._font_head.render("// IESTATĪJUMI //", True, ACCENT)
        self._screen.blit(tag, tag.get_rect(center=(cx, 180)))
        title = self._font_title.render("IESTATĪJUMI", True, PALE)
        self._screen.blit(title, title.get_rect(center=(cx, 290)))
        hint = self._font_small.render("↑↓ / WS pārvietoties   ←→ / AD mainīt   ENTER apstiprināt   ESC atcelt", True, DIM)
        self._screen.blit(hint, hint.get_rect(center=(cx, 360)))

    def _draw_rows(self):
        for i, row in enumerate(self._rows):
            r = self._row_rect(i)
            h = self._hover[i]
            c = self._colors[row]

            if h > 0.005:
                for expand, alpha, radius in [(24, 0.04, 16), (12, 0.09, 10)]:
                    sz = (r.width + expand * 2, r.height + expand * 2)
                    layer = pygame.Surface(sz, pygame.SRCALPHA)
                    pygame.draw.rect(layer, (*c, int(255 * alpha * h)), layer.get_rect(), border_radius=radius)
                    self._screen.blit(layer, (r.x - expand, r.y - expand))
                tint = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(tint, (*c, int(30 * h)), tint.get_rect(), border_radius=6)
                self._screen.blit(tint, r.topleft)
                bord = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(bord, (*c, int(180 * h)), bord.get_rect(), width=2, border_radius=6)
                self._screen.blit(bord, r.topleft)

            bar_h = int(r.height * (0.42 + 0.50 * h))
            bar_y = r.y + (r.height - bar_h) // 2
            pygame.draw.rect(self._screen, c, (r.x, bar_y, 5, bar_h))

            label_c = self._lerp_color(DIM, WHITE, h)
            label = self._font.render(self._labels[row], True, label_c)
            self._screen.blit(label, label.get_rect(midleft=(r.x + 30, r.centery)))

            if row in ("sound_volume", "music_volume", "ambience_volume"):
                self._draw_slider(r, row, c, h)
            else:
                self._draw_cycle(r, row, c, h)

    def _draw_slider(self, r, row, c, h):
        x, cy, w = self._slider_track(r)
        val = self._cfg[row]

        track_surf = pygame.Surface((w, 6), pygame.SRCALPHA)
        pygame.draw.rect(track_surf, (*DIM_DARK, 255), track_surf.get_rect(), border_radius=3)
        self._screen.blit(track_surf, (x, cy - 3))

        fill_w = max(0, int(w * val))
        if fill_w > 0:
            fill_surf = pygame.Surface((fill_w, 6), pygame.SRCALPHA)
            pygame.draw.rect(fill_surf, (*c, 220), fill_surf.get_rect(), border_radius=3)
            self._screen.blit(fill_surf, (x, cy - 3))

        knob_x = x + int(w * val)
        knob_r = int(10 + 4 * h)
        pygame.draw.circle(self._screen, c, (knob_x, cy), knob_r)
        pygame.draw.circle(self._screen, self._lerp_color(c, WHITE, 0.5 * h), (knob_x, cy), knob_r - 3)

        pct = self._font_val.render(f"{int(val * 100)}%", True, self._lerp_color(DIM, PALE, h))
        self._screen.blit(pct, pct.get_rect(midright=(r.right - 20, r.centery)))

    def _draw_cycle(self, r, row, c, h):
        if row == "resolution":
            w, ht = cfg_mod.RESOLUTIONS[self._res_idx]
            val_str = f"{w} × {ht}"
        else:
            mode_labels = {"fullscreen": "FULLSCREEN", "windowed": "WINDOWED"}
            val_str = mode_labels.get(self._cfg[row], self._cfg[row].upper())

        val_c = self._lerp_color(DIM, c, 0.5 + 0.5 * h)
        val = self._font_val.render(val_str, True, val_c)
        self._screen.blit(val, val.get_rect(midright=(r.right - 60, r.centery)))

        arrow_c = self._lerp_color(DIM_SOFT, c, h)
        lx = r.right - 50
        rx = r.right - 20
        cy = r.centery
        pygame.draw.polygon(self._screen, arrow_c, [(lx - 12, cy), (lx, cy - 10), (lx, cy + 10)])
        pygame.draw.polygon(self._screen, arrow_c, [(rx + 12, cy), (rx, cy - 10), (rx, cy + 10)])

    def _draw_buttons(self):
        self._draw_btn(self._back_rect(), "ATCELT", DIM, self._back_hover)
        self._draw_btn(self._save_rect(), "SAGLABĀT", NEON, self._save_hover)

    def _draw_btn(self, r, label, c, h):
        if h > 0.005:
            for expand, alpha, radius in [(20, 0.05, 16), (10, 0.12, 10)]:
                sz = (r.width + expand * 2, r.height + expand * 2)
                layer = pygame.Surface(sz, pygame.SRCALPHA)
                pygame.draw.rect(layer, (*c, int(255 * alpha * h)), layer.get_rect(), border_radius=radius)
                self._screen.blit(layer, (r.x - expand, r.y - expand))

        bg = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (*c, int(40 + 40 * h)), bg.get_rect(), border_radius=6)
        self._screen.blit(bg, r.topleft)

        bord = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.rect(bord, (*c, int(120 + 135 * h)), bord.get_rect(), width=2, border_radius=6)
        self._screen.blit(bord, r.topleft)

        text_c = self._lerp_color(DIM, WHITE, h)
        text = self._font.render(label, True, text_c)
        self._screen.blit(text, text.get_rect(center=r.center))

    @staticmethod
    def _lerp_color(a, b, t):
        t = max(0.0, min(1.0, t))
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )
