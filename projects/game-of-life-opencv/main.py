import numpy as np
import cv2
import time
import argparse

def evolve(board):
    # Create a copy of the board to store the next generation
    new_board = np.copy(board)
    rows, cols = board.shape
    
    for i in range(rows):
        for j in range(cols):
            # Count the number of live neighbors
            live_neighbors = np.sum(board[max(0, i-1):min(i+2, rows), max(0, j-1):min(j+2, cols)]) - board[i, j]
            
            # Apply Conway's rules
            if board[i, j] == 1 and (live_neighbors < 2 or live_neighbors > 3):
                new_board[i, j] = 0  # Cell dies
            elif board[i, j] == 0 and live_neighbors == 3:
                new_board[i, j] = 1  # Cell becomes alive
                
    return new_board

def display_board(board, generation):
    # Convert board to a format suitable for OpenCV
    img = (board * 255).astype(np.uint8)
    cv2.imshow('Game of Life', img)
    cv2.setWindowTitle('Game of Life', f'Generation {generation}')
    cv2.waitKey(100)  # Wait for 100 ms

def main():
    # Parse command line arguments for grid dimensions
    parser = argparse.ArgumentParser(description='Conway\'s Game of Life')
    parser.add_argument('--rows', type=int, default=50, help='Number of rows in the grid')
    parser.add_argument('--cols', type=int, default=50, help='Number of columns in the grid')
    args = parser.parse_args()

    # Initialize a random board
    board = np.random.choice([0, 1], size=(args.rows, args.cols), p=[0.8, 0.2])
    
    generation = 0
    cv2.namedWindow('Game of Life', cv2.WINDOW_NORMAL)
    while True:
        display_board(board, generation)  # Display the current generation
        board = evolve(board)  # Evolve to the next generation
        generation += 1  # Increment generation count
        time.sleep(0.1)  # Control the speed of the animation

if __name__ == "__main__":
    main()
    cv2.destroyAllWindows()  # Close all OpenCV windows after exiting the loop