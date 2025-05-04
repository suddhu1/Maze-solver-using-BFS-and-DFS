import tkinter as tk
import random
from collections import deque

# ----- Configuration Constants -----
CELL_SIZE = 25
COLS = 25
ROWS = 25

# Colors for visualization
DEFAULT_COLOR = "black"
VISITED_COLOR = "lightgreen"
CURRENT_COLOR = "yellow"
PATH_COLOR = "red"
WALL_COLOR = "white"

# Global variables for the grid and animation state
grid = []         # 2D list of Cell objects
cell_rects = {}   # Mapping (row, col) -> canvas rectangle id
solver_running = False  # Prevents starting a new solve/maze while one is running

# ----- Cell Class Definition -----
class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        # All walls exist initially.
        self.walls = {"top": True, "right": True, "bottom": True, "left": True}
        self.visited = False

    # Make Cell hashable so we can use it in sets and as dictionary keys.
    def __hash__(self):
        return hash((self.row, self.col))

    def __eq__(self, other):
        return (self.row, self.col) == (other.row, other.col)

# ----- Maze Creation and Drawing Functions -----
def create_grid():
    """Creates a grid of cells and draws the background cells on the canvas."""
    global grid, cell_rects
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    cell_rects = {}
    canvas.delete("all")  # Clear any previous drawings

    # Draw a rectangle for each cell. We later update these rectangles' colors.
    for r in range(ROWS):
        for c in range(COLS):
            x1 = c * CELL_SIZE
            y1 = r * CELL_SIZE
            x2 = x1 + CELL_SIZE
            y2 = y1 + CELL_SIZE
            rect = canvas.create_rectangle(x1, y1, x2, y2, fill=DEFAULT_COLOR, outline=DEFAULT_COLOR)
            cell_rects[(r, c)] = rect

def generate_maze():
    """Generate a maze using an iterative recursive backtracking (DFS) algorithm."""
    stack = []
    current = grid[0][0]
    current.visited = True

    while True:
        next_cell = get_unvisited_neighbor(current)
        if next_cell:
            next_cell.visited = True
            stack.append(current)
            remove_walls(current, next_cell)
            current = next_cell
        elif stack:
            current = stack.pop()
        else:
            break

    # Reset visited flags for later use during solving.
    for row in grid:
        for cell in row:
            cell.visited = False

    draw_walls()

def get_unvisited_neighbor(cell):
    """Return a random unvisited neighbor of the given cell (if any)."""
    neighbors = []
    r, c = cell.row, cell.col
    directions = [(-1, 0, "top"), (0, 1, "right"), (1, 0, "bottom"), (0, -1, "left")]
    for dr, dc, _ in directions:
        new_r, new_c = r + dr, c + dc
        if 0 <= new_r < ROWS and 0 <= new_c < COLS:
            neighbor = grid[new_r][new_c]
            if not neighbor.visited:
                neighbors.append(neighbor)
    return random.choice(neighbors) if neighbors else None

def remove_walls(current, next_cell):
    """Remove the wall between the current cell and the next cell."""
    dr = current.row - next_cell.row
    dc = current.col - next_cell.col
    if dc == 1:
        current.walls["left"] = False
        next_cell.walls["right"] = False
    elif dc == -1:
        current.walls["right"] = False
        next_cell.walls["left"] = False
    if dr == 1:
        current.walls["top"] = False
        next_cell.walls["bottom"] = False
    elif dr == -1:
        current.walls["bottom"] = False
        next_cell.walls["top"] = False

def draw_walls():
    """Draw the maze walls on top of the background cell rectangles."""
    for r in range(ROWS):
        for c in range(COLS):
            cell = grid[r][c]
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            if cell.walls["top"]:
                canvas.create_line(x, y, x + CELL_SIZE, y, fill=WALL_COLOR, width=2)
            if cell.walls["right"]:
                canvas.create_line(x + CELL_SIZE, y, x + CELL_SIZE, y + CELL_SIZE, fill=WALL_COLOR, width=2)
            if cell.walls["bottom"]:
                canvas.create_line(x, y + CELL_SIZE, x + CELL_SIZE, y + CELL_SIZE, fill=WALL_COLOR, width=2)
            if cell.walls["left"]:
                canvas.create_line(x, y, x, y + CELL_SIZE, fill=WALL_COLOR, width=2)

# ----- Maze Solving Functions (DFS and BFS) -----
def get_valid_neighbors(cell):
    """Return a list of accessible neighboring cells (where there is no wall)."""
    neighbors = []
    r, c = cell.row, cell.col
    if not cell.walls["top"] and r > 0:
        neighbors.append(grid[r - 1][c])
    if not cell.walls["right"] and c < COLS - 1:
        neighbors.append(grid[r][c + 1])
    if not cell.walls["bottom"] and r < ROWS - 1:
        neighbors.append(grid[r + 1][c])
    if not cell.walls["left"] and c > 0:
        neighbors.append(grid[r][c - 1])
    return neighbors

def reconstruct_path(prev, start, end):
    """Reconstruct the path from start to end using the prev dictionary."""
    path = []
    current = end
    while current != start:
        path.append(current)
        current = prev[current]
    path.append(start)
    path.reverse()
    return path

def dfs_solver():
    """Depth-first search maze solver (generator function)."""
    stack = []
    start = grid[0][0]
    end = grid[ROWS - 1][COLS - 1]
    visited = set()
    prev = {}
    stack.append(start)
    visited.add(start)

    while stack:
        current = stack.pop()
        yield (current, False)  # Yield the current cell for animation.
        if current == end:
            path = reconstruct_path(prev, start, end)
            yield path  # Yield the complete path.
            return
        for neighbor in get_valid_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                prev[neighbor] = current
                stack.append(neighbor)
    yield None

def bfs_solver():
    """Breadth-first search maze solver (generator function)."""
    queue = deque()
    start = grid[0][0]
    end = grid[ROWS - 1][COLS - 1]
    visited = set()
    prev = {}
    queue.append(start)
    visited.add(start)

    while queue:
        current = queue.popleft()
        yield (current, False)
        if current == end:
            path = reconstruct_path(prev, start, end)
            yield path
            return
        for neighbor in get_valid_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                prev[neighbor] = current
                queue.append(neighbor)
    yield None

# ----- Animation Functions -----
def animate_solution(solver):
    """Animate the solving process by repeatedly calling next() on the solver generator."""
    global solver_running
    try:
        result = next(solver)
        if isinstance(result, tuple):
            cell, _ = result
            # Temporarily mark the current cell.
            canvas.itemconfig(cell_rects[(cell.row, cell.col)], fill=CURRENT_COLOR)
            # After a short delay, mark it as visited.
            root.after(50, lambda: canvas.itemconfig(cell_rects[(cell.row, cell.col)], fill=VISITED_COLOR))
            root.after(60, lambda: animate_solution(solver))
        elif isinstance(result, list):
            # The solver yielded the final path. Animate its drawing.
            animate_path(result, 0)
        else:
            solver_running = False
    except StopIteration:
        solver_running = False

def animate_path(path, index):
    """Animate the final path by coloring each cell in sequence."""
    global solver_running
    if index < len(path):
        cell = path[index]
        canvas.itemconfig(cell_rects[(cell.row, cell.col)], fill=PATH_COLOR)
        root.after(50, lambda: animate_path(path, index + 1))
    else:
        # Reset the flag when the entire path has been animated.
        solver_running = False

# ----- UI Button Callback Functions -----
def new_maze():
    """Handler for the 'New Maze' button."""
    global solver_running
    if solver_running:
        return  # Prevent generating a new maze if a solve is in progress.
    create_grid()
    generate_maze()

def solve_maze():
    """Handler for the 'Solve' button. Starts the selected solving algorithm."""
    global solver_running
    if solver_running:
        return
    algorithm = algorithm_var.get()
    solver_running = True
    solver = dfs_solver() if algorithm == "DFS" else bfs_solver()
    animate_solution(solver)

# ----- Tkinter UI Setup -----
root = tk.Tk()
root.title("Maze Solver - DFS & BFS")

# Create a frame for controls (buttons and algorithm selector)
controls_frame = tk.Frame(root)
controls_frame.pack(pady=10)

new_maze_button = tk.Button(controls_frame, text="New Maze", command=new_maze)
new_maze_button.pack(side=tk.LEFT, padx=5)

# OptionMenu to select the algorithm ("DFS" or "BFS")
algorithm_var = tk.StringVar(value="DFS")
algorithm_menu = tk.OptionMenu(controls_frame, algorithm_var, "DFS", "BFS")
algorithm_menu.pack(side=tk.LEFT, padx=5)

solve_button = tk.Button(controls_frame, text="Solve", command=solve_maze)
solve_button.pack(side=tk.LEFT, padx=5)

# Create the canvas that displays the maze.
canvas_width = COLS * CELL_SIZE
canvas_height = ROWS * CELL_SIZE
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg=DEFAULT_COLOR)
canvas.pack()

# Generate the initial maze.
new_maze()

# Start the Tkinter main loop.
root.mainloop()
