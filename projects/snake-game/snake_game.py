import pygame
import random
import sys

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
CELL_SIZE = 20
FPS = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.positions = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.grow_pending = 0

    def get_head_position(self):
        return self.positions[0]

    def turn(self, dir):
        if (dir[0] * -1, dir[1] * -1) == self.direction:
            return
        self.direction = dir

    def move(self):
        cur = self.get_head_position()
        x, y = cur
        dx, dy = self.direction
        new_pos = ((x + dx * CELL_SIZE) % SCREEN_WIDTH,
                   (y + dy * CELL_SIZE) % SCREEN_HEIGHT)
        if new_pos in self.positions[1:]:
            return False  # Collision with self
        self.positions.insert(0, new_pos)
        if self.grow_pending:
            self.grow_pending -= 1
        else:
            self.positions.pop()
        return True

    def grow(self):
        self.grow_pending += 1

    def draw(self, surface):
        for pos in self.positions:
            rect = pygame.Rect(pos[0], pos[1], CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, GREEN, rect)
            pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    def __init__(self, snake_positions):
        self.position = self.random_position(snake_positions)

    def random_position(self, snake_positions):
        while True:
            x = random.randint(0, (SCREEN_WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            y = random.randint(0, (SCREEN_HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            if (x, y) not in snake_positions:
                return (x, y)

    def draw(self, surface):
        rect = pygame.Rect(self.position[0], self.position[1], CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, RED, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.food = Food(self.snake.positions)
        self.score = 0
        self.paused = False
        self.game_over = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                global SCREEN_WIDTH, SCREEN_HEIGHT
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.snake.turn(UP)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.snake.turn(DOWN)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.snake.turn(LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.snake.turn(RIGHT)
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    self.reset()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def update(self):
        if self.paused or self.game_over:
            return
        if not self.snake.move():
            self.game_over = True
            return
        head = self.snake.get_head_position()
        if head == self.food.position:
            self.score += 1
            self.snake.grow()
            self.food = Food(self.snake.positions)

    def draw(self):
        self.screen.fill(GRAY)
        self.snake.draw(self.screen)
        self.food.draw(self.screen)
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))
        if self.paused:
            pause_surf = self.font.render("PAUSED", True, WHITE)
            rect = pause_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_surf, rect)
        if self.game_over:
            over_surf = self.font.render("GAME OVER", True, RED)
            over_rect = over_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(over_surf, over_rect)
            restart_surf = self.font.render("Press R to Restart", True, WHITE)
            restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(restart_surf, restart_rect)
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()