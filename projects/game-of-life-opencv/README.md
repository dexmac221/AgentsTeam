# Conway's Game of Life

## Overview
This project implements Conway's Game of Life in a single Python file. The game simulates the evolution of a grid of cells based on simple rules.

## Requirements
- Python 3.x
- OpenCV
- NumPy

## Installation
To install the required packages, run the following command:

pip install -r requirements.txt

## Usage
Run the main Python file to start the simulation:

python main.py

## Game Rules
1. Any live cell with two or three live neighbors survives.
2. Any dead cell with exactly three live neighbors becomes a live cell.
3. All other live cells die in the next generation. Similarly, all other dead cells stay dead.

## File Structure
- main.py: Contains the implementation of the Game of Life.
- requirements.txt: Lists the dependencies required for the project.

## License
This project is licensed under the MIT License. See the LICENSE file for details.