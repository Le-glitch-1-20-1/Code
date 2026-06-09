import pygame
import numpy as np

class Renderer:
    def __init__(self, screen, cell_size=10):
        self.screen = screen
        self.cell_size = cell_size
        self.COLOR_ALIVE = (83, 74, 183)   # violet
        self.COLOR_DEAD  = (245, 245, 245)
        self.COLOR_GRID  = (220, 220, 220)

    def draw(self, grid):
        cs = self.cell_size
        # Convertit la grille NumPy en surface d'un coup (très rapide)
        rgb = np.where(
            grid.cells[:, :, np.newaxis],
            self.COLOR_ALIVE,
            self.COLOR_DEAD
        ).astype(np.uint8)

        surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
        surface = pygame.transform.scale(
            surface,
            (grid.cols * cs, grid.rows * cs)
        )
        self.screen.blit(surface, (0, 0))