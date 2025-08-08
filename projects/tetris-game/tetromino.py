import pygame
from constants import *

class Tetromino:
    SHAPES = {
        'I': [
            [[0, 0, 0, 0],
             [1, 1, 1, 1],
             [0, 0, 0, 0],
             [0, 0, 0, 0]],
            [[0, 0, 1, 0],
             [0, 0, 1, 0],
             [0, 0, 1, 0],
             [0, 0, 1, 0]]
        ],
        'O': [
            [[1, 1],
             [1, 1]]
        ],
        'T': [
            [[0, 1, 0],
             [1, 1, 1],
             [0, 0, 0]],
            [[0, 1, 0],
             [0, 1, 1],
             [0, 1, 0]],
            [[0, 0, 0],
             [1, 1, 1],
             [0, 1, 0]],
            [[0, 1, 0],
             [1, 1, 0],
             [0, 1, 0]]
        ],
        'S': [
            [[0, 1, 1],
             [1, 1, 0],
             [0, 0, 0]],
            [[0, 1, 0],
             [0, 1, 1],
             [0, 0, 1]]
        ],
        'Z': [
            [[1, 1, 0],
             [0, 1, 1],
             [0, 0, 0]],
            [[0, 0, 1],
             [0, 1, 1],
             [0, 1, 0]]
        ],
        'J': [
            [[1, 0, 0],
             [1, 1, 1],
             [0, 0, 0]],
            [[0, 1, 1],
             [0, 1, 0],
             [0, 1, 0]],
            [[0, 0, 0],
             [1, 1, 1],
             [0, 0, 1]],
            [[0, 1, 0],
             [0, 1, 0],
             [1, 1, 0]]
        ],
        'L': [
            [[0, 0, 1],
             [1, 1, 1],
             [0, 0, 0]],
            [[0, 1, 0],
             [0, 1, 0],
             [0, 1, 1]],
            [[0, 0, 0],
             [1, 1, 1],
             [1, 0, 0]],
            [[1, 1, 0],
             [0, 1, 0],
             [0, 1, 0]]
        ]
    }

    COLORS = {
        'I': (0, 240, 240),
        'O': (240, 240, 0),
        'T': (160, 0, 240),
        'S': (0, 240, 0),
        'Z': (240, 0, 0),
        'J': (0, 0, 240),
        'L': (240, 160, 0)
    }

    def __init__(self, shape):
        self.shape_type = shape
        self.rotation = 0
        self.shape = self.get_shape()
        self.color = self.COLORS[shape]
        self.position = (GRID_WIDTH // 2 - len(self.shape[0]) // 2, 0)

    def get_shape(self):
        return [row[:] for row in self.SHAPES[self.shape_type][self.rotation]]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.SHAPES[self.shape_type])
        self.shape = self.get_shape()