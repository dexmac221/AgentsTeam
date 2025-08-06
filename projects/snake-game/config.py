import pygame

WIDTH: int = 640
HEIGHT: int = 480

FPS: int = 60

BLACK: tuple[int, int, int] = (0, 0, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
RED: tuple[int, int, int] = (255, 0, 0)
GREEN: tuple[int, int, int] = (0, 255, 0)
BLUE: tuple[int, int, int] = (0, 0, 255)
YELLOW: tuple[int, int, int] = (255, 255, 0)
GREY: tuple[int, int, int] = (128, 128, 128)
DARK_GREEN: tuple[int, int, int] = (0, 100, 0)

GRID_SIZE: int = 20          # Size of each grid cell in pixels
SNAKE_SEGMENT_SIZE: int = GRID_SIZE  # Snake segment occupies one grid cell
INITIAL_SNAKE_SPEED: int = 10  # Initial movement speed (cells per second)
SCORE_INCREMENT: int = 1      # Points gained per food

GRID_WIDTH: int = WIDTH // GRID_SIZE
GRID_HEIGHT: int = HEIGHT // GRID_SIZE

FONT_NAME: str = pygame.font.get_default_font()
FONT_SIZE: int = 24

FOOD_COLOR: tuple[int, int, int] = RED
SNAKE_COLOR: tuple[int, int, int] = GREEN
BACKGROUND_COLOR: tuple[int, int, int] = BLACK
GAME_OVER_TEXT: str = "Game Over"
GAME_OVER_FONT_SIZE: int = 48

__all__ = [
    "WIDTH",
    "HEIGHT",
    "FPS",
    "BLACK",
    "WHITE",
    "RED",
    "GREEN",
    "BLUE",
    "YELLOW",
    "GREY",
    "DARK_GREEN",
    "GRID_SIZE",
    "SNAKE_SEGMENT_SIZE",
    "INITIAL_SNAKE_SPEED",
    "SCORE_INCREMENT",
    "GRID_WIDTH",
    "GRID_HEIGHT",
    "FONT_NAME",
    "FONT_SIZE",
    "FOOD_COLOR",
    "SNAKE_COLOR",
    "BACKGROUND_COLOR",
    "GAME_OVER_TEXT",
    "GAME_OVER_FONT_SIZE",
]