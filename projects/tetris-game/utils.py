import pygame
from constants import *

def draw_grid(surface, grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(
                TOP_LEFT_X + x * BLOCK_SIZE,
                TOP_LEFT_Y + y * BLOCK_SIZE,
                BLOCK_SIZE,
                BLOCK_SIZE
            )
            pygame.draw.rect(surface, grid[y][x], rect)
            pygame.draw.rect(surface, (128, 128, 128), rect, 1)

def draw_next_piece(surface, piece):
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Next Piece', 1, (255, 255, 255))
    surface.blit(label, (TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE + 20, 30))
    shape = piece.shape
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE + 20 + x * BLOCK_SIZE,
                    TOP_LEFT_Y + 60 + y * BLOCK_SIZE,
                    BLOCK_SIZE,
                    BLOCK_SIZE
                )
                pygame.draw.rect(surface, piece.color, rect)
                pygame.draw.rect(surface, (128, 128, 128), rect, 1)

def draw_window(surface, score, level, lines):
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render(f'Score: {score}', 1, (255, 255, 255))
    surface.blit(label, (TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE + 20, 200))
    label = font.render(f'Level: {level}', 1, (255, 255, 255))
    surface.blit(label, (TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE + 20, 250))
    label = font.render(f'Lines: {lines}', 1, (255, 255, 255))
    surface.blit(label, (TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE + 20, 300))

def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont('comicsans', size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (TOP_LEFT_X + GRID_WIDTH * BLOCK_SIZE // 2 - label.get_width() // 2,
                         TOP_LEFT_Y + GRID_HEIGHT * BLOCK_SIZE // 2 - label.get_height() // 2))