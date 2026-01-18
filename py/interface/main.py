"""Snake Game Viewer - Main interface for the Snake game with AI support."""

import os
import subprocess
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np  # noqa: E402, I001
import pygame  # noqa: E402
from heuristicController import SnakeHeuristicAI  # noqa: E402
from SnakeGameController import Direction, FoodType, GameState, IpcCommands  # noqa: E402
from SnakeGameController import SnakeGameController as Controller  # noqa: E402

from py.snakeAgent import SnakeAgent  # noqa: E402

if os.name != "posix":
    print("[SYSTEM] This program is only supported on Linux systems.")
    sys.exit(1)

if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

cpp_game_path = project_root / "build" / "src" / "app" / "snake_game"
assets_path = current_file_path.parent / "assets"

# --- ZMIENNE GLOBALNE KONFIGURACJI ---
DEFAULT_WINDOW_WIDTH = 1024
DEFAULT_WINDOW_HEIGHT = 768

SCREEN_WIDTH = DEFAULT_WINDOW_WIDTH
SCREEN_HEIGHT = DEFAULT_WINDOW_HEIGHT
CELL_SIZE = 20
OFFSET_X = 0
OFFSET_Y = 0

AVAILABLE_MAP_SIZES = [(10, 10), (20, 20), (30, 30), (40, 40), (20, 10), (10, 20)]

game_process = None
current_process_size = (20, 20)

GRAPHICS = {}
FONTS = {}


def update_fonts():
    global FONTS
    base_scale = SCREEN_HEIGHT
    FONTS["large"] = pygame.font.SysFont(None, int(base_scale * 0.06))
    FONTS["medium"] = pygame.font.SysFont(None, int(base_scale * 0.04))
    FONTS["small"] = pygame.font.SysFont(None, int(base_scale * 0.025))


def update_layout(map_width, map_height):
    global CELL_SIZE, OFFSET_X, OFFSET_Y, SCREEN_WIDTH, SCREEN_HEIGHT

    safe_margin = 10

    available_width = SCREEN_WIDTH - (safe_margin * 2)
    available_height = SCREEN_HEIGHT - (safe_margin * 2)

    cell_w = available_width // map_width
    cell_h = available_height // map_height

    CELL_SIZE = int(min(cell_w, cell_h))
    CELL_SIZE = max(1, CELL_SIZE)

    board_pixel_w = map_width * CELL_SIZE
    board_pixel_h = map_height * CELL_SIZE

    OFFSET_X = (SCREEN_WIDTH - board_pixel_w) // 2
    OFFSET_Y = (SCREEN_HEIGHT - board_pixel_h) // 2

    load_images()


def load_images():  # noqa: C901
    global GRAPHICS

    def get_path(filename):
        paths_to_check = [assets_path / filename, current_file_path.parent / filename]
        for path in paths_to_check:
            if path.exists():
                return path
        return None

    bg_filename = "background.png"
    bg_path = get_path(bg_filename)

    if bg_path:
        try:
            img = pygame.image.load(str(bg_path)).convert()
            GRAPHICS["background"] = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            GRAPHICS["background"] = None
    else:
        GRAPHICS["background"] = None

    def load_game_sprite(filename):
        path = get_path(filename)
        if path:
            try:
                img = pygame.image.load(str(path)).convert_alpha()
                return pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
            except Exception:
                return None
        return None

    GRAPHICS["head"] = load_game_sprite("head.png")
    GRAPHICS["body"] = load_game_sprite("body.png")
    GRAPHICS["corner"] = load_game_sprite("bodyRight.png")
    GRAPHICS["tail"] = load_game_sprite("tail.png")
    GRAPHICS["board1"] = load_game_sprite("board1.png")
    GRAPHICS["board2"] = load_game_sprite("board2.png")

    GRAPHICS["foods"] = {
        FoodType.APPLE: load_game_sprite("apple.png"),
        FoodType.CHERRY: load_game_sprite("cherry.png"),
        FoodType.BANANA: load_game_sprite("banana.png"),
        FoodType.GRAPE: load_game_sprite("grape.png"),
        FoodType.ORANGE: load_game_sprite("orange.png"),
    }


def restart_game_process():
    global game_process, cpp_game_path, current_process_size
    if game_process:
        try:
            game_process.terminate()
            game_process.wait(timeout=0.5)
        except Exception:
            game_process.kill()

    try:
        current_process_size = (20, 20)
        print(f"[SYSTEM] Restarting C++ game with size {current_process_size[0]}x{current_process_size[1]}...")
        game_process = subprocess.Popen(  # noqa: S603
            [str(cpp_game_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"Error starting game: {e}")
        return False


restart_game_process()


def draw_text_with_bg(screen, text_surf, x, y, align="topleft", bg_color=(0, 0, 0, 150)):
    rect = text_surf.get_rect()
    if align == "topleft":
        rect.topleft = (x, y)
    elif align == "bottomright":
        rect.bottomright = (x, y)
    elif align == "center":
        rect.center = (x, y)

    padding = 6
    bg_rect = rect.inflate(padding * 2, padding * 2)
    s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    s.fill(bg_color)
    screen.blit(s, bg_rect.topleft)

    screen.blit(text_surf, rect)
    return bg_rect.height


def draw_legend(screen, font, lines):
    start_y = SCREEN_HEIGHT - 10
    for line in lines:
        text_surf = font.render(line, True, (220, 220, 220))
        h = draw_text_with_bg(screen, text_surf, SCREEN_WIDTH - 10, start_y, align="bottomright")
        start_y -= h + 4


def draw_board(screen, width, height):
    b1 = GRAPHICS.get("board1")
    b2 = GRAPHICS.get("board2")

    for y in range(height):
        for x in range(width):
            pos_x = OFFSET_X + x * CELL_SIZE
            pos_y = OFFSET_Y + y * CELL_SIZE
            is_even = (x + y) % 2 == 0
            if is_even:
                if b1:
                    screen.blit(b1, (pos_x, pos_y))
                else:
                    pygame.draw.rect(screen, (30, 30, 30), (pos_x, pos_y, CELL_SIZE, CELL_SIZE))
            else:
                if b2:
                    screen.blit(b2, (pos_x, pos_y))
                else:
                    pygame.draw.rect(screen, (40, 40, 40), (pos_x, pos_y, CELL_SIZE, CELL_SIZE))

    board_px_w = width * CELL_SIZE
    board_px_h = height * CELL_SIZE
    pygame.draw.rect(screen, (100, 100, 100), (OFFSET_X, OFFSET_Y, board_px_w, board_px_h), 2)


def draw_snake(screen, snake_head, snake_body, snake_dir):  # noqa: C901
    body_without_head = [part for part in snake_body if part != snake_head]
    segments = [snake_head] + body_without_head
    tail_pos = segments[-1] if segments else None

    img_head = GRAPHICS.get("head")
    img_body = GRAPHICS.get("body")
    img_corner = GRAPHICS.get("corner")
    img_tail = GRAPHICS.get("tail")

    if img_body and not img_corner:
        img_corner = img_body

    for i in range(1, len(segments)):
        segment = segments[i]
        if segment == tail_pos and i != len(segments) - 1:
            continue

        px = OFFSET_X + segment[0] * CELL_SIZE
        py = OFFSET_Y + segment[1] * CELL_SIZE

        prev_seg = segments[i - 1]
        next_seg = segments[i + 1] if i + 1 < len(segments) else None

        if not img_body:
            pygame.draw.rect(screen, (0, 255, 0), (px, py, CELL_SIZE, CELL_SIZE))
            continue

        if next_seg is None:
            dx = prev_seg[0] - segment[0]
            dy = prev_seg[1] - segment[1]
            angle = 0
            if dy == 1:
                angle = 180
            elif dy == -1:
                angle = 0
            elif dx == 1:
                angle = -90
            elif dx == -1:
                angle = 90
            img_to_draw = img_tail if img_tail else img_body
            rotated = pygame.transform.rotate(img_to_draw, angle)
            screen.blit(rotated, (px, py))
        else:
            if prev_seg[0] == segment[0] == next_seg[0] or prev_seg[1] == segment[1] == next_seg[1]:
                angle = 0
                if prev_seg[1] == segment[1]:
                    angle = 90
                rotated = pygame.transform.rotate(img_body, angle)
                screen.blit(rotated, (px, py))
            else:
                rel_prev = (prev_seg[0] - segment[0], prev_seg[1] - segment[1])
                rel_next = (next_seg[0] - segment[0], next_seg[1] - segment[1])
                corner_sum = (rel_prev[0] + rel_next[0], rel_prev[1] + rel_next[1])
                angle = 0
                if corner_sum == (1, 1):
                    angle = 0
                elif corner_sum == (-1, 1):
                    angle = -90
                elif corner_sum == (-1, -1):
                    angle = 180
                elif corner_sum == (1, -1):
                    angle = 90
                rotated = pygame.transform.rotate(img_corner, angle)
                screen.blit(rotated, (px, py))

    px = OFFSET_X + snake_head[0] * CELL_SIZE
    py = OFFSET_Y + snake_head[1] * CELL_SIZE
    if img_head:
        angle = 0
        if snake_dir == Direction.DOWN:
            angle = 180
        elif snake_dir == Direction.LEFT:
            angle = 90
        elif snake_dir == Direction.RIGHT:
            angle = -90
        rotated = pygame.transform.rotate(img_head, angle)
        screen.blit(rotated, (px, py))
    else:
        pygame.draw.rect(screen, (0, 200, 0), (px, py, CELL_SIZE, CELL_SIZE))


def main():  # noqa: C901
    global SCREEN_WIDTH, SCREEN_HEIGHT, current_process_size
    controller = Controller()

    for _ in range(20):
        if controller.connect():
            break
        time.sleep(0.1)
    else:
        print("Nie udało się połączyć z grą C++")
        return 1

    aiMode = False
    algoMode = False
    network = None
    heuristic_bot = None

    pygame.display.init()
    pygame.font.init()

    os.environ["SDL_VIDEO_CENTERED"] = "1"

    is_fullscreen = False
    SCREEN_WIDTH = DEFAULT_WINDOW_WIDTH
    SCREEN_HEIGHT = DEFAULT_WINDOW_HEIGHT

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Snake Game Viewer")

    update_fonts()
    update_layout(current_process_size[0], current_process_size[1])

    clock = pygame.time.Clock()
    running = True

    models_dir = Path(__file__).parent.parent / "training" / "models"
    available_models = []
    if models_dir.exists():
        available_models = [f.name for f in models_dir.glob("*.json")]
        available_models.sort(reverse=True)

    current_model_name = available_models[0] if available_models else "Brak modeli"

    menu_selection = 0
    menu_sub_state = 0
    model_selection_idx = 0
    map_menu_idx = 1

    data = None
    should_render = True
    last_ai_decision_version = -1

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                if not is_fullscreen:
                    SCREEN_WIDTH = event.w
                    SCREEN_HEIGHT = event.h
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    update_fonts()
                    if data:
                        update_layout(data.board_width, data.board_height)
                    else:
                        update_layout(current_process_size[0], current_process_size[1])
                    should_render = True

            elif event.type == pygame.KEYDOWN:
                should_render = True

                if event.key == pygame.K_q:
                    controller.send_command(IpcCommands.QUIT_GAME)
                    running = False
                elif event.key == pygame.K_t:
                    controller.send_command(IpcCommands.START_GAME)
                elif event.key == pygame.K_r:
                    w, h = current_process_size
                    if restart_game_process():
                        controller.disconnect()
                        time.sleep(0.5)
                        controller = Controller()
                        controller.connect()
                        last_ai_decision_version = -1
                        data = None
                elif event.key == pygame.K_ESCAPE:
                    if menu_sub_state != 0:
                        menu_sub_state = 0

                if data and data.game_state == GameState.PLAYING and not aiMode and not algoMode:
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

                # --- MENU ---
                if data and data.game_state == GameState.MENU:
                    MENU_ITEMS_COUNT = 7

                    if menu_sub_state == 0:
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            menu_selection = (menu_selection - 1) % MENU_ITEMS_COUNT
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            menu_selection = (menu_selection + 1) % MENU_ITEMS_COUNT
                        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            if menu_selection == 0:
                                aiMode, algoMode = False, False
                                controller.send_command(IpcCommands.START_GAME)
                            elif menu_selection == 1:
                                aiMode, algoMode = True, False
                                full_path = models_dir / current_model_name
                                try:
                                    network = SnakeAgent(str(full_path))
                                    controller.send_command(IpcCommands.START_GAME)
                                except Exception:
                                    aiMode = False
                            elif menu_selection == 2:
                                aiMode, algoMode = False, True
                                heuristic_bot = SnakeHeuristicAI()
                                controller.send_command(IpcCommands.START_GAME)
                            elif menu_selection == 3:
                                menu_sub_state = 1
                            elif menu_selection == 4:
                                menu_sub_state = 2
                                if current_process_size in AVAILABLE_MAP_SIZES:
                                    map_menu_idx = AVAILABLE_MAP_SIZES.index(current_process_size)
                                else:
                                    map_menu_idx = 0
                            elif menu_selection == 5:
                                is_fullscreen = not is_fullscreen
                                if is_fullscreen:
                                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                else:
                                    os.environ["SDL_VIDEO_CENTERED"] = "1"
                                    SCREEN_WIDTH = DEFAULT_WINDOW_WIDTH
                                    SCREEN_HEIGHT = DEFAULT_WINDOW_HEIGHT
                                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

                                    pygame.event.clear()

                                SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
                                update_fonts()
                                if data:
                                    update_layout(data.board_width, data.board_height)
                                else:
                                    update_layout(current_process_size[0], current_process_size[1])

                            elif menu_selection == 6:
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

                    elif menu_sub_state == 2:
                        if event.key in [pygame.K_w, pygame.K_UP]:
                            map_menu_idx = (map_menu_idx - 1) % len(AVAILABLE_MAP_SIZES)
                        elif event.key in [pygame.K_s, pygame.K_DOWN]:
                            map_menu_idx = (map_menu_idx + 1) % len(AVAILABLE_MAP_SIZES)
                        elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                            target_w, target_h = AVAILABLE_MAP_SIZES[map_menu_idx]
                            if (target_w, target_h) != current_process_size:
                                success = controller.send_command(IpcCommands.CHANGE_BOARD_SIZE, target_w, target_h)
                                if success:
                                    current_process_size = (target_w, target_h)
                                    update_layout(target_w, target_h)
                            menu_sub_state = 0

        # --- DANE ---
        packets_read = 0
        data_updated = False
        while True:
            if packets_read > 200:
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
            time.sleep(0.001)
            continue
        if data_updated:
            should_render = True

        # --- AI ---
        if data.game_state == GameState.PLAYING and data_updated:
            if aiMode or algoMode:
                if data.version != last_ai_decision_version:
                    calculated_direction = None
                    current_dir = int(data.snake_direction)

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
                        is_opposite = (
                            (current_dir == 0 and dir_val == 1)
                            or (current_dir == 1 and dir_val == 0)
                            or (current_dir == 2 and dir_val == 3)
                            or (current_dir == 3 and dir_val == 2)
                        )

                        if not is_opposite and dir_val != current_dir:
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

                    last_ai_decision_version = data.version

        # --- RENDER ---
        if should_render:
            if GRAPHICS.get("background"):
                screen.blit(GRAPHICS["background"], (0, 0))
            else:
                screen.fill((20, 20, 20))

            if data.game_state == GameState.MENU:
                if menu_sub_state == 0:
                    current_screen_text = "Tryb Okienkowy" if is_fullscreen else "Pełny Ekran"
                    menu_options = [
                        "Włącz grę (Manual)",
                        "Tryb AI",
                        "Tryb Algorytmu",
                        "Ustawienia AI",
                        "Rozmiar Mapy",
                        current_screen_text,
                        "Zamknij grę",
                    ]

                    t = FONTS["large"].render("Snake Game Launcher", True, (0, 255, 0))
                    screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT * 0.1))

                    m_info = FONTS["small"].render(f"Model: {current_model_name}", True, (100, 255, 255))
                    screen.blit(m_info, (SCREEN_WIDTH // 2 - m_info.get_width() // 2, SCREEN_HEIGHT * 0.18))

                    cur_w, cur_h = current_process_size
                    size_info = FONTS["small"].render(f"Mapa: {cur_w}x{cur_h}", True, (200, 200, 200))
                    screen.blit(size_info, (SCREEN_WIDTH // 2 - size_info.get_width() // 2, SCREEN_HEIGHT * 0.22))

                    menu_start_y = SCREEN_HEIGHT * 0.35
                    for i, opt in enumerate(menu_options):
                        col = (255, 255, 0) if i == menu_selection else (255, 255, 255)
                        prefix = "> " if i == menu_selection else "   "
                        surf = FONTS["medium"].render(prefix + opt, True, col)
                        text_x = SCREEN_WIDTH // 2 - 200
                        screen.blit(surf, (text_x, menu_start_y + i * (SCREEN_HEIGHT * 0.06)))

                    draw_legend(screen, FONTS["small"], ["[ENTER] Wybierz", "[W / S] Nawigacja", "[Q] Zamknij"])

                elif menu_sub_state == 1:
                    t = FONTS["large"].render("Wybierz model", True, (0, 200, 255))
                    screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT * 0.1))
                    list_start_y = SCREEN_HEIGHT * 0.25
                    for i, m_file in enumerate(available_models):
                        if i > 15:
                            break
                        is_selected = i == model_selection_idx
                        is_active = m_file == current_model_name
                        color = (255, 255, 0) if is_selected else (200, 200, 200)
                        if is_active:
                            color = (0, 255, 0)
                        prefix = "> " if is_selected else "  "
                        suffix = " [AKTYWNY]" if is_active else ""
                        text_str = f"{prefix}{m_file}{suffix}"
                        surf = FONTS["medium"].render(text_str, True, color)
                        screen.blit(surf, (SCREEN_WIDTH // 2 - 350, list_start_y + i * (SCREEN_HEIGHT * 0.045)))
                    draw_legend(screen, FONTS["small"], ["[ENTER] Wybierz model", "[W / S] Nawigacja", "[ESC] Powrót"])

                elif menu_sub_state == 2:
                    t = FONTS["large"].render("Wybierz Rozmiar Mapy", True, (255, 100, 255))
                    screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT * 0.1))
                    list_start_y = SCREEN_HEIGHT * 0.25
                    for i, (w, h) in enumerate(AVAILABLE_MAP_SIZES):
                        is_selected = i == map_menu_idx
                        is_active = (w, h) == current_process_size
                        color = (255, 255, 0) if is_selected else (255, 255, 255)
                        if is_active:
                            color = (0, 255, 0)
                        prefix = "> " if is_selected else "  "
                        suffix = " [AKTYWNY]" if is_active else ""
                        text_str = f"{prefix}{w} x {h}{suffix}"
                        surf = FONTS["medium"].render(text_str, True, color)
                        screen.blit(surf, (SCREEN_WIDTH // 2 - 150, list_start_y + i * (SCREEN_HEIGHT * 0.06)))
                    draw_legend(screen, FONTS["small"], ["[ENTER] Zatwierdź", "[W / S] Nawigacja", "[ESC] Anuluj"])

            elif data.game_state in [GameState.PLAYING, GameState.GAME_OVER]:
                draw_board(screen, data.board_width, data.board_height)
                draw_snake(screen, data.snake_head, data.snake_body, data.snake_direction)

                fx, fy = data.food_position
                ftype = data.food_type
                food_img = GRAPHICS.get("foods", {}).get(ftype)
                if food_img:
                    screen.blit(food_img, (OFFSET_X + fx * CELL_SIZE, OFFSET_Y + fy * CELL_SIZE))
                else:
                    colors = [(255, 0, 0), (200, 0, 0), (255, 255, 0), (128, 0, 128), (255, 165, 0)]
                    c = colors[int(ftype)] if int(ftype) < len(colors) else (255, 255, 255)
                    pygame.draw.rect(
                        screen, c, (OFFSET_X + fx * CELL_SIZE, OFFSET_Y + fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    )

                m_str = "AI" if aiMode else ("ALGO" if algoMode else "MANUAL")
                score_txt = FONTS["medium"].render(f"Wynik: {data.score} | Tryb: {m_str}", True, (255, 255, 255))
                draw_text_with_bg(screen, score_txt, 10, 10)

                if data.game_state == GameState.GAME_OVER:
                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 180))
                    screen.blit(overlay, (0, 0))

                    t = FONTS["large"].render("KONIEC GRY", True, (255, 0, 0))
                    screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

                    s_msg = FONTS["medium"].render(f"Wynik: {data.score}", True, (255, 255, 255))
                    screen.blit(s_msg, (SCREEN_WIDTH // 2 - s_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 10))

                    restart_msg = FONTS["medium"].render("[T] ZAGRAJ PONOWNIE", True, (0, 255, 0))
                    screen.blit(
                        restart_msg, (SCREEN_WIDTH // 2 - restart_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 60)
                    )

                legend_lines = []
                if aiMode or algoMode:
                    legend_lines = ["[R] Menu Główne", "[Q] Zamknij"]
                else:
                    legend_lines = ["[WASD] Ruch", "[R] Menu Główne", "[Q] Zamknij"]
                draw_legend(screen, FONTS["small"], legend_lines)

            pygame.display.flip()
            should_render = False

        clock.tick(200)

    controller.disconnect()
    pygame.quit()
    return 0


if __name__ == "__main__":
    time.sleep(0.5)
    sys.exit(main())
