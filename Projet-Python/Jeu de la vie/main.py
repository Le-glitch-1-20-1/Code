import pygame
import sys
from grid import Grid
from renderer import Renderer

CELL_SIZE = 10
FPS_TARGET = 30
W, H = 1000, 700
COLS, ROWS = W // CELL_SIZE, H // CELL_SIZE

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Jeu de la Vie")
    clock = pygame.time.Clock()

    grid = Grid(COLS, ROWS)
    renderer = Renderer(screen, CELL_SIZE)

    running = False
    painting = None  # True = dessiner, False = effacer
    speed = 10       # générations par seconde
    tick_acc = 0

    while True:
        dt = clock.tick(FPS_TARGET) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = not running
                if event.key == pygame.K_c:
                    grid.clear()
                if event.key == pygame.K_r:
                    grid.randomize()
                if event.key == pygame.K_RIGHT and not running:
                    grid.step()
                if event.key == pygame.K_UP:
                    speed = min(60, speed + 5)
                if event.key == pygame.K_DOWN:
                    speed = max(1, speed - 5)

            # Dessin à la souris
            if event.type == pygame.MOUSEBUTTONDOWN:
                painting = not pygame.key.get_mods() & pygame.KMOD_SHIFT
            if event.type == pygame.MOUSEBUTTONUP:
                painting = None

        if painting is not None:
            mx, my = pygame.mouse.get_pos()
            col, row = mx // CELL_SIZE, my // CELL_SIZE
            if 0 <= col < COLS and 0 <= row < ROWS:
                grid.cells[row, col] = 1 if painting else 0

        # Avance la simulation selon la vitesse choisie
        if running:
            tick_acc += dt
            while tick_acc >= 1 / speed:
                grid.step()
                tick_acc -= 1 / speed

        renderer.draw(grid)

        # HUD simple
        font = pygame.font.SysFont("monospace", 14)
        info = f"Gén. {grid.generation}  |  {grid.alive_count} cellules  |  {speed} gen/s  |  ESPACE=pause  R=aléatoire  C=effacer"
        screen.blit(font.render(info, True, (80, 80, 80)), (10, 10))

        pygame.display.flip()

if __name__ == "__main__":
    main()