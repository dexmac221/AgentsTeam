import pygame

# Screen dimensions
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 500

# Grid dimensions
GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = 20

# Top-left corner of the grid
TOP_LEFT_X = (SCREEN_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - GRID_HEIGHT * BLOCK_SIZE

# Frames per second
FPS = 60