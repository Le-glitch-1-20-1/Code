import numpy as np

class Grid:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.cells = np.zeros((rows, cols), dtype=np.uint8)
        self.generation = 0

    def step(self):
        # Compte les voisins avec roll (pas de boucle Python !)
        c = self.cells
        neighbors = (
            np.roll(np.roll(c, -1, 0), -1, 1) +
            np.roll(c, -1, 0) +
            np.roll(np.roll(c, -1, 0),  1, 1) +
            np.roll(c,  1, 1) +
            np.roll(c, -1, 1) +
            np.roll(np.roll(c,  1, 0), -1, 1) +
            np.roll(c,  1, 0) +
            np.roll(np.roll(c,  1, 0),  1, 1)
        )
        # Règles de Conway en une ligne
        self.cells = np.where(
            (c == 1) & ((neighbors == 2) | (neighbors == 3)), 1,
            np.where((c == 0) & (neighbors == 3), 1, 0)
        ).astype(np.uint8)
        self.generation += 1

    def toggle(self, col, row):
        self.cells[row, col] ^= 1

    def clear(self):
        self.cells[:] = 0
        self.generation = 0

    def randomize(self, density=0.3):
        self.cells = (np.random.rand(self.rows, self.cols) < density).astype(np.uint8)
        self.generation = 0

    @property
    def alive_count(self):
        return int(self.cells.sum())