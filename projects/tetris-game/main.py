import pygame
import sys
from game import TetrisGame

def main():
    pygame.init()
    screen = pygame.display.set_mode((TetrisGame.SCREEN_WIDTH, TetrisGame.SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris')
    clock = pygame.time.Clock()
    game = TetrisGame(screen, clock)
    game.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()