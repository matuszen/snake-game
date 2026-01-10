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
from SnakeGameController import Controller, Direction, GameState, IpcCommands  # noqa: E402
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
    except:
        pass

    pygame.quit()

    if game_process:
        game_process.terminate()
        try:
            game_process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            game_process.kill()

    os.execl(sys.executable, sys.executable, *sys.argv)


# Zmienna globalna na proces gry
game_process = None


def restart_game_process(width, height):
    global game_process, cpp_game_path

    # 1. Zabij stary proces, jeśli istnieje
    if game_process:
        try:
            game_process.terminate()
            game_process.wait(timeout=0.5)
        except:
            game_process.kill()

    # 2. Uruchom nowy proces z argumentami wymiarów
    # UWAGA: Twój C++ musi obsługiwać argumenty (argv), np: ./snake_game 20 20
    try:
        print(f"[SYSTEM] Restarting C++ game with size {width}x{height}...")
        game_process = subprocess.Popen(
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

    # NOWE OPCJE MENU
    menu_options = [
        "Włącz grę (Manual)",
        "Tryb AI",
        "Tryb Algorytmu",
        "Wybierz Model AI",
        "Ustawienia Gry",  # <--- NOWA OPCJA
        "Zamknij grę",
    ]

    menu_selection = 0
    menu_sub_state = 0
    # 0 = Main, 1 = Models, 2 = Game Settings (Size)

    model_selection_idx = 0

    # Dostępne rozmiary planszy
    board_sizes = [(10, 10), (20, 20), (30, 30)]
    current_size_idx = 1  # Domyślnie 20x20

    data = None

    # Łączymy się pierwszy raz
    if not controller.connect():
        # Próbujemy połączyć kilka razy (bo C++ się restartuje)
        for _ in range(10):
            time.sleep(0.2)
            if controller.connect():
                break

    # Główna pętla
    while running:
        # --- Odbiór danych ---
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

        # Jeśli brak danych (np. podczas restartu C++), czekamy
        if data is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Ekran ładowania/oczekiwania
            screen.fill((0, 0, 0))
            load_txt = font_medium.render("Oczekiwanie na silnik gry...", True, (100, 100, 100))
            screen.blit(load_txt, (WIN_WIDTH // 2 - 150, WIN_HEIGHT // 2))
            pygame.display.flip()

            # Próba ponownego połączenia (reconnect) jeśli zerwało
            if not controller.memory:
                controller.connect()
            time.sleep(0.1)
            continue

        # Inicjalizacja okna (wymiary planszy) - ODŚWIEŻAMY PRZY ZMIANIE ROZMIARU
        target_width = data.board_width * CELL_SIZE + 2 * MARGIN
        if WIN_WIDTH != target_width or not window_initialized:
            WIN_WIDTH = data.board_width * CELL_SIZE + 2 * MARGIN
            WIN_HEIGHT = data.board_height * CELL_SIZE + 2 * MARGIN
            screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.DOUBLEBUF)
            window_initialized = True

        # --- LOGIKA AUTOMATYCZNA (AI/ALGO) ---
        if data.game_state == GameState.PLAYING:
            if (aiMode or algoMode) and data_updated:
                calculated_direction = None

                if algoMode and heuristic_bot:
                    calculated_direction = heuristic_bot.get_next_move(data)

                elif aiMode and network:
                    if hasattr(data, "neural_vector") and data.neural_vector:
                        outputs = network.move(data.neural_vector)
                        if outputs is not None:
                            calculated_direction = np.argmax(outputs)

                if calculated_direction is not None:
                    cmd = IpcCommands.NONE
                    dir_val = int(calculated_direction)
                    if dir_val == 0:
                        cmd = IpcCommands.MOVE_UP
                    elif dir_val == 1:
                        cmd = IpcCommands.MOVE_DOWN
                    elif dir_val == 2:
                        cmd = IpcCommands.MOVE_LEFT
                    elif dir_val == 3:
                        cmd = IpcCommands.MOVE_RIGHT

                    if cmd != IpcCommands.NONE:
                        controller.send_command(cmd)

        # --- OBSŁUGA ZDARZEŃ ---
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
                    # Restart pełny
                    restart_game_process(board_sizes[current_size_idx][0], board_sizes[current_size_idx][1])
                elif event.key == pygame.K_ESCAPE:
                    if menu_sub_state != 0:
                        menu_sub_state = 0

                # Manualne sterowanie
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

                # --- OBSŁUGA MENU ---
                if data.game_state == GameState.MENU:
                    # GŁÓWNE MENU
                    if menu_sub_state == 0:
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            menu_selection = (menu_selection - 1) % len(menu_options)
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            menu_selection = (menu_selection + 1) % len(menu_options)
                        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            # Logika wyboru
                            if menu_selection == 0:  # Manual
                                aiMode, algoMode = False, False
                                controller.send_command(IpcCommands.START_GAME)
                            elif menu_selection == 1:  # AI
                                aiMode, algoMode = True, False
                                full_path = models_dir / current_model_name
                                try:
                                    network = SnakeAgent(str(full_path))
                                    controller.send_command(IpcCommands.START_GAME)
                                except:
                                    aiMode = False
                            elif menu_selection == 2:  # Algo
                                aiMode, algoMode = False, True
                                if SnakeHeuristicAI:
                                    heuristic_bot = SnakeHeuristicAI()
                                    controller.send_command(IpcCommands.START_GAME)
                            elif menu_selection == 3:  # Wybór Modelu
                                menu_sub_state = 1
                            elif menu_selection == 4:  # Ustawienia Gry (NOWE)
                                menu_sub_state = 2
                            elif menu_selection == 5:  # Quit
                                controller.send_command(IpcCommands.QUIT_GAME)
                                running = False

                    # POD-MENU: MODELE
                    elif menu_sub_state == 1:
                        if available_models:
                            if event.key in [pygame.K_w, pygame.K_UP]:
                                model_selection_idx = (model_selection_idx - 1) % len(available_models)
                            elif event.key in [pygame.K_s, pygame.K_DOWN]:
                                model_selection_idx = (model_selection_idx + 1) % len(available_models)
                            elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                                current_model_name = available_models[model_selection_idx]
                                menu_sub_state = 0

                    # POD-MENU: ROZMIAR PLANSZY (NOWE)
                    elif menu_sub_state == 2:
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            current_size_idx = (current_size_idx - 1) % len(board_sizes)
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            current_size_idx = (current_size_idx + 1) % len(board_sizes)
                        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            # ZASTOSOWANIE ZMIAN -> RESTART C++
                            w, h = board_sizes[current_size_idx]
                            print(f"[MENU] Zmiana rozmiaru na {w}x{h}. Restart silnika...")

                            controller.disconnect()  # Rozłączamy stare SHM
                            restart_game_process(w, h)  # Restart procesu

                            # Resetujemy połączenie w pętli głównej
                            controller.connect()
                            menu_sub_state = 0

        # --- RYSOWANIE ---
        screen.fill((0, 0, 0))

        if data.game_state == GameState.MENU:
            if menu_sub_state == 0:
                # Główne menu
                t = font_large.render("Snake Game Launcher", True, (0, 255, 0))
                screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 50))

                # Info o aktualnych ustawieniach
                info_txt = f"Model: {current_model_name} | Rozmiar: {data.board_width}x{data.board_height}"
                m_info = font_small.render(info_txt, True, (100, 255, 255))
                screen.blit(m_info, (WIN_WIDTH // 2 - m_info.get_width() // 2, 100))

                for i, opt in enumerate(menu_options):
                    col = (255, 255, 0) if i == menu_selection else (255, 255, 255)
                    txt = ("> " if i == menu_selection else "   ") + opt
                    surf = font_medium.render(txt, True, col)
                    screen.blit(surf, (WIN_WIDTH // 2 - 180, 160 + i * 45))

            elif menu_sub_state == 1:
                # Wybór modelu (stare)
                t = font_large.render("Wybierz model", True, (0, 200, 255))
                screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 50))
                for i, m_file in enumerate(available_models):
                    col = (
                        (0, 255, 0)
                        if i == model_selection_idx
                        else ((100, 255, 255) if m_file == current_model_name else (200, 200, 200))
                    )
                    surf = font_medium.render(m_file, True, col)
                    screen.blit(surf, (WIN_WIDTH // 2 - 150, 150 + i * 40))

            elif menu_sub_state == 2:
                # Wybór rozmiaru (NOWE)
                t = font_large.render("Wybierz rozmiar planszy", True, (255, 100, 255))
                screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 50))

                for i, size in enumerate(board_sizes):
                    s_str = f"{size[0]} x {size[1]}"
                    # Podświetlenie
                    is_selected = i == current_size_idx
                    is_active = size[0] == data.board_width and size[1] == data.board_height

                    color = (0, 255, 0) if is_selected else (255, 255, 255)
                    prefix = ">>> " if is_selected else "    "
                    suffix = " (Aktywny)" if is_active else ""

                    surf = font_medium.render(prefix + s_str + suffix, True, color)
                    screen.blit(surf, (WIN_WIDTH // 2 - 100, 150 + i * 50))

                info = font_small.render("Enter = Zastosuj i zrestartuj grę", True, (150, 150, 150))
                screen.blit(info, (WIN_WIDTH // 2 - info.get_width() // 2, 400))

        elif data.game_state == GameState.PLAYING:
            # Rysowanie ramki
            pygame.draw.rect(
                screen,
                (255, 255, 255),
                (MARGIN, MARGIN, data.board_width * CELL_SIZE, data.board_height * CELL_SIZE),
                3,
            )
            # Rysowanie węża
            for x, y in data.snake_body:
                pygame.draw.rect(
                    screen, (0, 255, 0), (MARGIN + x * CELL_SIZE, MARGIN + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )
            # Rysowanie głowy
            hx, hy = data.snake_head
            pygame.draw.rect(
                screen, (0, 200, 0), (MARGIN + hx * CELL_SIZE, MARGIN + hy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )
            # Rysowanie jedzenia
            fx, fy = data.food_position
            pygame.draw.rect(
                screen, (255, 0, 0), (MARGIN + fx * CELL_SIZE, MARGIN + fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )

            # Info
            m_str = "AI" if aiMode else ("ALGO" if algoMode else "MANUAL")
            screen.blit(font_medium.render(f"Wynik: {data.score} | Tryb: {m_str}", True, (255, 255, 255)), (10, 10))

        elif data.game_state == GameState.GAME_OVER:
            t = font_large.render("GAME OVER", True, (255, 0, 0))
            screen.blit(t, (WIN_WIDTH // 2 - t.get_width() // 2, 200))
            screen.blit(font_medium.render("R - Menu", True, (200, 200, 200)), (WIN_WIDTH // 2 - 50, 260))

        pygame.display.flip()
        clock.tick(30)

    # Sprzątanie
    controller.disconnect()
    pygame.quit()
    if game_process:
        game_process.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
