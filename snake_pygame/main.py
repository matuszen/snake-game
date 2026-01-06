
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pygame
from SnakeGameController import Controller, Direction, GameState, IpcCommands

project_root = Path(__file__).parent.parent
cpp_game_path = project_root / "build" / "snake"

# Debug: print the path to verify
print(f"Looking for executable at: {cpp_game_path}")
print(f"Exists: {cpp_game_path.exists()}")

game_process = subprocess.Popen([cpp_game_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603


time.sleep(0.5)



def main():
    controller = Controller()
    if not controller.connect():
        return 1

    aiMode = False
    network = None

    pygame.init()
    CELL_SIZE = 20
    MARGIN = 100
    WIN_WIDTH = 800
    WIN_HEIGHT = 600
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Snake Game Viewer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    running = True
    window_initialized = False
    screen.fill((0, 0, 0))
    title_surf = font.render("Snake Game", True, (255, 255, 255))
    controls_surf1 = font.render("Sterowanie:", True, (255, 255, 255))
    controls_surf2 = font.render("WASD - ruch, R - start, Q - wyjście", True, (255, 255, 255))

    screen.blit(title_surf, (WIN_WIDTH // 2 - title_surf.get_width() // 2, 150))
    screen.blit(controls_surf1, (WIN_WIDTH // 2 - controls_surf1.get_width() // 2, 200))
    screen.blit(controls_surf2, (WIN_WIDTH // 2 - controls_surf2.get_width() // 2, 230))
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        data = controller.read_data()
        if data and not window_initialized:
            WIN_WIDTH = data.board_width * CELL_SIZE + 2 * MARGIN
            WIN_HEIGHT = data.board_height * CELL_SIZE + 2 * MARGIN
            screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.DOUBLEBUF)
            window_initialized = True

        keys = pygame.key.get_pressed()
        command = None
        if keys[pygame.K_r]:
            command = IpcCommands.START_GAME
        elif keys[pygame.K_w] and not aiMode:
            command = IpcCommands.MOVE_UP
        elif keys[pygame.K_s] and not aiMode:
            command = IpcCommands.MOVE_DOWN
        elif keys[pygame.K_a] and not aiMode:
            command = IpcCommands.MOVE_LEFT
        elif keys[pygame.K_d] and not aiMode:
            command = IpcCommands.MOVE_RIGHT
        elif keys[pygame.K_q]:
            command = IpcCommands.QUIT_GAME
            running = False

        if command:
            controller.send_command(command)

        if aiMode and data and network:
            inputs = data.neural_vector
            outputs = network.predict(inputs)
            dir_idx = np.argmax(outputs)  # Get index of max output

            directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
            dir = directions[dir_idx]

            if dir == Direction.UP:
                controller.send_command(IpcCommands.MOVE_UP)
            elif dir == Direction.DOWN:
                controller.send_command(IpcCommands.MOVE_DOWN)
            elif dir == Direction.LEFT:
                controller.send_command(IpcCommands.MOVE_LEFT)
            elif dir == Direction.RIGHT:
                controller.send_command(IpcCommands.MOVE_RIGHT)

        if data:
            screen.fill((0, 0, 0))

            if data.game_state == GameState.PLAYING:
                pygame.draw.rect(screen, (255, 255, 255),
                                (MARGIN, MARGIN, data.board_width * CELL_SIZE, data.board_height * CELL_SIZE), 3)
                for x, y in data.snake_body:
                    pygame.draw.rect(screen, (0, 255, 0), (MARGIN + x*CELL_SIZE, MARGIN + y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                hx, hy = data.snake_head
                pygame.draw.rect(screen, (0, 200, 0), (MARGIN + hx*CELL_SIZE, MARGIN + hy*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                fx, fy = data.food_position
                pygame.draw.rect(screen, (255, 0, 0), (MARGIN + fx*CELL_SIZE, MARGIN + fy*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                score_surf = font.render(f"Score: {data.score}", True, (255, 255, 255))
                screen.blit(score_surf, (10, 10))

            elif data.game_state == GameState.PAUSED:
                pygame.draw.rect(screen, (255, 255, 255),
                                (MARGIN, MARGIN, data.board_width * CELL_SIZE, data.board_height * CELL_SIZE), 3)
                paused_surf = font.render("PAUSED", True, (255, 255, 0))
                screen.blit(paused_surf, (WIN_WIDTH // 2 - paused_surf.get_width() // 2, 150))

            elif data.game_state == GameState.GAME_OVER:
                over_surf = font.render("Koniec gry", True, (255, 255, 255))
                score_surf = font.render(f"Wynik: {data.score}", True, (255, 255, 255))
                restart_surf = font.render("Aby zagrać ponownie wciśnij R", True, (255, 255, 255))
                quit_surf = font.render("Aby wyjść wciśnij Q", True, (255, 255, 255))

                screen.blit(over_surf, (WIN_WIDTH // 2 - over_surf.get_width() // 2, 150))
                screen.blit(score_surf, (WIN_WIDTH // 2 - score_surf.get_width() // 2, 200))
                screen.blit(restart_surf, (WIN_WIDTH // 2 - restart_surf.get_width() // 2, 250))
                screen.blit(quit_surf, (WIN_WIDTH // 2 - quit_surf.get_width() // 2, 280))



        pygame.display.flip()
        clock.tick(300)

    controller.disconnect()
    pygame.quit()
    return 0


if __name__ == "__main__":
    time.sleep(0.5)
    subprocess.call("reset", shell=True)  # noqa: S602
    sys.exit(main())
