import pygame
import sys
import os
from player import Player
from player_sprite import PlayerSprite
from world import World
from camera import Camera
from tile_registry import TileRegistry
from parallax_background import ParallaxBackground
from level import create_level
from score_log import ScoreLog
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BACKGROUND_COLOR,
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    WHITE, BLACK, NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_RED, NEON_YELLOW,
    DARK_GRAY, GRAY,
    LEVELS_FOLDER,
)