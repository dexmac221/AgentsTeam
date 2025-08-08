import pygame
import random
import sys
from constants import *
from tetromino import Tetromino
from utils import draw_grid, draw_next_piece, draw_window, draw_text_middle

class TetrisGame:
    SCREEN_WIDTH = SCREEN_WIDTH
    SCREEN_HEIGHT = SCREEN_HEIGHT

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.grid = [[(0, 0, 0) for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.get_new_piece()
        self.next_piece = self.get_new_piece()
        self.fall_time = 0
        self.fall_speed = 0.5
        self.level = 0
        self.lines_cleared = 0
        self.score = 0
        self.paused = False
        self.game_over = False

    def get_new_piece(self):
        shape = random.choice(list(Tetromino.SHAPES.keys()))
        return Tetromino(shape)

    def valid_space(self, shape, offset):
        off_x, off_y = offset
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = x + off_x
                    new_y = y + off_y
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x] != (0, 0, 0):
                        return False
        return True

    def check_lost(self):
        for x in range(GRID_WIDTH):
            if self.grid[0][x] != (0, 0, 0):
                return True
        return False

    def clear_lines(self):
        lines_to_clear = []
        for i, row in enumerate(self.grid):
            if all(cell != (0, 0, 0) for cell in row):
                lines_to_clear.append(i)
        for i in lines_to_clear:
            del self.grid[i]
            self.grid.insert(0, [(0, 0, 0) for _ in range(GRID_WIDTH)])
        lines = len(lines_to_clear)
        if lines:
            self.lines_cleared += lines
            self.score += {1: 40, 2: 100, 3: 300, 4: 1200}[lines] * (self.level + 1)
            self.level = self.lines_cleared // 10
            self.fall_speed = max(0.1, 0.5 - self.level * 0.05)

    def lock_piece(self):
        shape = self.current_piece.shape
        off_x, off_y = self.current_piece.position
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[off_y + y][off_x + x] = self.current_piece.color
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.get_new_piece()
        if not self.valid_space(self.current_piece.shape, self.current_piece.position):
            self.game_over = True

    def rotate_piece(self):
        original_rotation = self.current_piece.rotation
        self.current_piece.rotate()
        if not self.valid_space(self.current_piece.shape, self.current_piece.position):
            self.current_piece.rotation = original_rotation
            self.current_piece.shape = self.current_piece.get_shape()

    def move_piece(self, dx):
        new_x = self.current_piece.position[0] + dx
        if self.valid_space(self.current_piece.shape, (new_x, self.current_piece.position[1])):
            self.current_piece.position = (new_x, self.current_piece.position[1])

    def hard_drop(self):
        while self.valid_space(self.current_piece.shape, (self.current_piece.position[0], self.current_piece.position[1] + 1)):
            self.current_piece.position = (self.current_piece.position[0], self.current_piece.position[1] + 1)
        self.lock_piece()

    def run(self):
        while True:
            self.clock.tick(FPS)
            if not self.paused and not self.game_over:
                self.fall_time += self.clock.get_time() / 1000
                if self.fall_time > self.fall_speed:
                    self.fall_time = 0
                    if self.valid_space(self.current_piece.shape, (self.current_piece.position[0], self.current_piece.position[1] + 1)):
                        self.current_piece.position = (self.current_piece.position[0], self.current_piece.position[1] + 1)
                    else:
                        self.lock_piece()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move_piece(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.move_piece(1)
                    elif event.key == pygame.K_DOWN:
                        if self.valid_space(self.current_piece.shape, (self.current_piece.position[0], self.current_piece.position[1] + 1)):
                            self.current_piece.position = (self.current_piece.position[0], self.current_piece.position[1] + 1)
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        self.hard_drop()
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
            self.draw()
            if self.game_over:
                draw_text_middle(self.screen, "GAME OVER", 80, (255, 255, 255))
                pygame.display.update()
                pygame.time.delay(2000)
                break

    def draw(self):
        self.screen.fill((0, 0, 0))
        draw_grid(self.screen, self.grid)
        draw_next_piece(self.screen, self.next_piece)
        draw_window(self.screen, self.score, self.level, self.lines_cleared)
        shape = self.current_piece.shape
        off_x, off_y = self.current_piece.position
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        self.current_piece.color,
                        (TOP_LEFT_X + (off_x + x) * BLOCK_SIZE,
                         TOP_LEFT_Y + (off_y + y) * BLOCK_SIZE,
                         BLOCK_SIZE,
                         BLOCK_SIZE),
                        0)
        pygame.display.update()