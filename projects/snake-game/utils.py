import json
import os
import random
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Any, Optional

Position = Tuple[int, int]
Snake = List[Position]
GridSize = Tuple[int, int]

@dataclass
class GameState:
    snake: Snake
    food: Position
    direction: str
    score: int
    grid_size: GridSize
    game_over: bool = False

def check_collision(snake: Snake, food: Position, grid_size: GridSize) -> bool:
    """
    Check if the snake has collided with walls or itself.
    Returns True if collision occurs, False otherwise.
    """
    head = snake[0]
    if not (0 <= head[0] < grid_size[0] and 0 <= head[1] < grid_size[1]):
        return True
    if head in snake[1:]:
        return True
    return False

def generate_food_position(snake: Snake, grid_size: GridSize) -> Position:
    """
    Generate a random food position that does not overlap the snake.
    """
    available_positions = [
        (x, y)
        for x in range(grid_size[0])
        for y in range(grid_size[1])
        if (x, y) not in snake
    ]
    if not available_positions:
        raise RuntimeError("No available positions for food.")
    return random.choice(available_positions)

def calculate_score(snake: Snake, initial_length: int = 3) -> int:
    """
    Calculate score based on snake length.
    """
    return len(snake) - initial_length

VALID_DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}

def validate_direction(direction: str) -> bool:
    """
    Validate that the direction is one of the allowed values.
    """
    return direction.upper() in VALID_DIRECTIONS

def sanitize_direction(direction: str) -> str:
    """
    Convert direction to uppercase and validate.
    Raises ValueError if invalid.
    """
    dir_upper = direction.upper()
    if dir_upper not in VALID_DIRECTIONS:
        raise ValueError(f"Invalid direction: {direction}")
    return dir_upper

def save_state(state: GameState, filepath: str) -> None:
    """
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, indent=4)

def load_state(filepath: str) -> GameState:
    """
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No such file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return GameState(**data)

def reset_state(grid_size: GridSize, initial_length: int = 3) -> GameState:
    """
    Create a new game state with a default snake and food position.
    """
    mid_x = grid_size[0] // 2
    mid_y = grid_size[1] // 2
    snake = [(mid_x, mid_y - i) for i in range(initial_length)]
    food = generate_food_position(snake, grid_size)
    return GameState(
        snake=snake,
        food=food,
        direction="UP",
        score=0,
        grid_size=grid_size,
        game_over=False,
    )

def clamp(value: int, min_value: int, max_value: int) -> int:
    """
    Clamp an integer value between min_value and max_value.
    """
    return max(min_value, min(value, max_value))

def distance(a: Position, b: Position) -> int:
    """
    Manhattan distance between two positions.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

__all__ = [
    "GameState",
    "check_collision",
    "generate_food_position",
    "calculate_score",
    "validate_direction",
    "sanitize_direction",
    "save_state",
    "load_state",
    "reset_state",
    "clamp",
    "distance",
]