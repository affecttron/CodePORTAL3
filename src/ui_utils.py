import pygame


def dim_color(color, factor=0.4):
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def draw_corner_accents(screen, rect, color, size=14, thickness=3):
    for x_dir, x_anchor in ((1, rect.left), (-1, rect.right - 1)):
        for y_dir, y_anchor in ((1, rect.top), (-1, rect.bottom - 1)):
            pygame.draw.line(
                screen, color,
                (x_anchor, y_anchor),
                (x_anchor + x_dir * size, y_anchor),
                thickness,
            )
            pygame.draw.line(
                screen, color,
                (x_anchor, y_anchor),
                (x_anchor, y_anchor + y_dir * size),
                thickness,
            )
