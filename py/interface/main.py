import os
import subprocess
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
py_folder = current_file_path.parent.parent
sys.path.insert(0, str(py_folder))
import numpy as np  # noqa: E402
import pygame  # noqa: E402
from snakeAgent import SnakeAgent  # noqa: E402
from SnakeGameController import Controller, GameState, IpcCommands  # noqa: E402
from snakeHeuristicController import SnakeHeuristicAI  # noqa: E402, F402

if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

project_root = Path(__file__).parent.parent.parent
cpp_game_path = project_root / "build" / "src" / "app" / "snake_game"

print(f"Looking for executable at: {cpp_game_path}")
print(f"Exists: {cpp_game_path.exists()}")

game_process = subprocess.Popen([cpp_game_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603


def reset(controller):
    try:
        controller.disconect()
    except:  # noqa: E722, S110
        pass

    pygame.quit()

    if game_process:
        game_process.terminate()
        try:
            game_process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            game_process.kill()

    os.execl(sys.executable, sys.executable, *sys.argv)  # noqa: S606


# Zmienna globalna na proces gry
game_process = None


def restart_game_process(width, height):
    global game_process, cpp_game_path

    # 1. Zabij stary proces, jeśli istnieje
    if game_process:
        try:
            game_process.terminate()
            game_process.wait(timeout=0.5)
        except:  # noqa: E722
            game_process.kill()

    # 2. Uruchom nowy proces z argumentami wymiarów
    # UWAGA: Twój C++ musi obsługiwać argumenty (argv), np: ./snake_game 20 20
    try:
        print(f"[SYSTEM] Restarting C++ game with size {width}x{height}...")
        game_process = subprocess.Popen(  # noqa: S603
            [str(cpp_game_path), str(width), str(height)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(0.5)  # Daj mu chwilę na start
        return True
    except Exception as e:
        print(f"Error starting game: {e}")
        return False


# Startujemy domyślnie 20x20 na początku skryptu
restart_game_process(20, 20)


def main():
    controller = Controller()

    # Próba połączenia z C++
    for _ in range(20):
        if controller.connect():
            break
        time.sleep(0.1)
    else:
        print("Nie udało się połączyć z grą C++")
        return 1

    # --- Zmienne stanu gry ---
    aiMode = False
    algoMode = False
    network = None
    heuristic_bot = None

    # --- Inicjalizacja Pygame ---
    pygame.display.init()
    pygame.font.init()
    CELL_SIZE = 20
    MARGIN = 100
    WIN_WIDTH = 800
    WIN_HEIGHT = 600
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.DOUBLEBUF)
    pygame.display.set_caption("Snake Game Viewer")
    clock = pygame.time.Clock()

    font_large = pygame.font.SysFont(None, 48)
    font_medium = pygame.font.SysFont(None, 36)
    font_small = pygame.font.SysFont(None, 24)

    running = True
    window_initialized = False

    # --- Menu Konfiguracja ---
    models_dir = Path(__file__).parent.parent / "training" / "models"
    available_models = []
    if models_dir.exists():
        available_models = [f.name for f in models_dir.glob("*.json")]
        available_models.sort()

    current_model_name = available_models[0] if available_models else "Brak modeli"
    menu_options = ["Włącz grę (Manual)", "Tryb AI", "Tryb Algorytmu", "Ustawienia AI", "Zamknij grę"]
    menu_selection = 0
    menu_sub_state = 0
    model_selection_idx = 0

    data = None

    # Główna pętla
    while running:
        new_data = None
        packets_read = 0
        data_updated = False

        while True:
            if packets_read > 50:
                break
            packet = controller.read_data()
            if packet is None:
                break
            new_data = packet
            packets_read += 1
            data_updated = True

        if new_data is not None:
            data = new_data

        if data is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            time.sleep(0.001)
            continue

        # Inicjalizacja okna (wymiary planszy)
        if not window_initialized:
            WIN_WIDTH = data.board_width * CELL_SIZE + 2 * MARGIN
            WIN_HEIGHT = data.board_height * CELL_SIZE + 2 * MARGIN
            screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.DOUBLEBUF)
            window_initialized = True

        if data.game_state == GameState.PLAYING:
            if (aiMode or algoMode) and data_updated:
                calculated_direction = None

                # --- TRYB ALGORYTMU HEURYSTYCZNEGO ---
                if algoMode and heuristic_bot:
                    calculated_direction = heuristic_bot.get_next_move(data)

                # --- TRYB AI (SIEĆ NEURONOWA) ---
                elif aiMode and network:
                    # Upewniamy się, że w danych z pamięci współdzielonej jest wektor dla sieci
                    if hasattr(data, "neural_vector") and data.neural_vector:
                        outputs = network.move(data.neural_vector)
                        print(f"[AI DECYZJA] Wejście: {data.neural_vector[:3]}... Wyjście: {outputs}")
                        if outputs is not None:
                            calculated_direction = np.argmax(outputs)

                # --- WYSŁANIE KOMENDY DO C++ ---
                if calculated_direction is not None:
                    cmd = IpcCommands.NONE
                    dir_val = int(calculated_direction)

                    if dir_val == 0:  # UP
                        cmd = IpcCommands.MOVE_UP
                    elif dir_val == 1:  # DOWN
                        cmd = IpcCommands.MOVE_DOWN
                    elif dir_val == 2:  # LEFT
                        cmd = IpcCommands.MOVE_LEFT
                    elif dir_val == 3:  # RIGHT
                        cmd = IpcCommands.MOVE_RIGHT

                    # Wyślij komendę tylko, jeśli jest poprawna
                    if cmd != IpcCommands.NONE:
                        controller.send_command(cmd)

        # --- OBSŁUGA ZDARZEŃ (Manual + Menu) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    controller.send_command(IpcCommands.QUIT_GAME)
                    running = False
                elif event.key == pygame.K_t:
                    controller.send_command(IpcCommands.START_GAME)
                elif event.key == pygame.K_r:
                    reset(controller)
                elif event.key == pygame.K_ESCAPE:
                    if menu_sub_state == 1:
                        menu_sub_state = 0

                # --- STEROWANIE MANUALNE ---
                if data.game_state == GameState.PLAYING and not aiMode and not algoMode:
                    cmd = None
                    if event.key in [pygame.K_w, pygame.K_UP]:
                        cmd = IpcCommands.MOVE_UP
                    elif event.key in [pygame.K_s, pygame.K_DOWN]:
                        cmd = IpcCommands.MOVE_DOWN
                    elif event.key in [pygame.K_a, pygame.K_LEFT]:
                        cmd = IpcCommands.MOVE_LEFT
                    elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                        cmd = IpcCommands.MOVE_RIGHT

                    if cmd:
                        controller.send_command(cmd)

                # Obsługa Menu (nawigacja)
                if data.game_state == GameState.MENU:
                    if menu_sub_state == 0:
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            menu_selection = (menu_selection - 1) % len(menu_options)
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            menu_selection = (menu_selection + 1) % len(menu_options)
                        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            if menu_selection == 0:  # Manual
                                aiMode, algoMode = False, False
                                controller.send_command(IpcCommands.START_GAME)
                            elif menu_selection == 1:  # AI
                                aiMode, algoMode = True, False
                                full_path = models_dir / current_model_name
                                print(f"\n[DEBUG] Próba wczytania modelu z: {full_path}")
                                if SnakeAgent:
                                    try:
                                        network = SnakeAgent(str(full_path))
                                        print(f"[SUKCES] Model załadowany obiektem: {network}")
                                        controller.send_command(IpcCommands.START_GAME)
                                    except Exception as e:
                                        print(f"[BŁĄD] Nie udało się wczytać modelu: {e}")
                                        aiMode = False
                                else:
                                    print("[BŁĄD] Klasa SnakeAgent nie jest dostępna.")
                                    aiMode = False
                            elif menu_selection == 2:
                                aiMode, algoMode = False, True
                                if SnakeHeuristicAI:
                                    heuristic_bot = SnakeHeuristicAI()
                                    controller.send_command(IpcCommands.START_GAME)
                                else:
                                    algoMode = False
                            elif menu_selection == 3:
                                menu_sub_state = 1
                                if current_model_name in available_models:
                                    model_selection_idx = available_models.index(current_model_name)
                            elif menu_selection == 4:
                                controller.send_command(IpcCommands.QUIT_GAME)
                                running = False

                    elif menu_sub_state == 1:
                        if available_models:
                            if event.key in [pygame.K_w, pygame.K_UP]:
                                model_selection_idx = (model_selection_idx - 1) % len(available_models)
                            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                                model_selection_idx = (model_selection_idx + 1) % len(available_models)
                            elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                                current_model_name = available_models[model_selection_idx]
                                menu_sub_state = 0

        # --- RYSOWANIE ---
        screen.fill((0, 0, 0))

        if data.game_state == GameState.MENU:
            if menu_sub_state == 0:
                t = font_large.render("Snake Game Launcher", True, (0, 255, 0))
                screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 80))
                m_info = font_small.render(f"Model: {current_model_name}", True, (100, 255, 255))
                screen.blit(m_info, (WIN_WIDTH // 2 - m_info.get_width() // 2, 130))
                for i, opt in enumerate(menu_options):
                    col = (255, 255, 0) if i == menu_selection else (255, 255, 255)
                    txt = ("> " if i == menu_selection else "   ") + opt
                    surf = font_medium.render(txt, True, col)
                    screen.blit(surf, (WIN_WIDTH // 2 - 180, 200 + i * 50))
            elif menu_sub_state == 1:
                t = font_large.render("Wybierz model", True, (0, 200, 255))
                screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 50))
                for i, m_file in enumerate(available_models):
                    col = (
                        (0, 255, 0)
                        if i == model_selection_idx
                        else ((100, 255, 255) if m_file == current_model_name else (200, 200, 200))
                    )
                    pre = ">>> " if i == model_selection_idx else (" * " if m_file == current_model_name else "    ")
                    surf = font_medium.render(pre + m_file, True, col)
                    screen.blit(surf, (WIN_WIDTH // 2 - 200, 150 + i * 40))

        elif data.game_state == GameState.PLAYING:
            pygame.draw.rect(
                screen,
                (255, 255, 255),
                (MARGIN, MARGIN, data.board_width * CELL_SIZE, data.board_height * CELL_SIZE),
                3,
            )
            for x, y in data.snake_body:
                pygame.draw.rect(
                    screen, (0, 255, 0), (MARGIN + x * CELL_SIZE, MARGIN + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )
            hx, hy = data.snake_head
            pygame.draw.rect(
                screen, (0, 200, 0), (MARGIN + hx * CELL_SIZE, MARGIN + hy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )
            fx, fy = data.food_position
            pygame.draw.rect(
                screen, (255, 0, 0), (MARGIN + fx * CELL_SIZE, MARGIN + fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )

            m_str = "AI" if aiMode else ("ALGO" if algoMode else "MANUAL")
            screen.blit(font_medium.render(f"Wynik: {data.score} | Tryb: {m_str}", True, (255, 255, 255)), (10, 10))

        elif data.game_state == GameState.GAME_OVER:
            t = font_large.render("KONIEC GRY", True, (255, 0, 0))
            screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 150))
            screen.blit(font_medium.render(f"Wynik: {data.score}", True, (255, 255, 255)), (WIN_WIDTH // 2 - 100, 220))
            screen.blit(
                font_small.render("'T' - Restart | 'R' - Menu | 'Q' - Wyjscie", True, (200, 200, 200)),
                (WIN_WIDTH // 2 - 100, 300),
            )

        pygame.display.flip()
        clock.tick(30)

    controller.disconnect()
    pygame.quit()
    return 0


if __name__ == "__main__":
    time.sleep(0.5)
    sys.exit(main())
