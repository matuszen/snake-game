import mmap
import select
import socket
import struct
import sys
import termios
import time
import tty
from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple

import posix_ipc


class Direction(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class GameState(IntEnum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    QUIT = 4


class FoodType(IntEnum):
    APPLE = 0
    CHERRY = 1
    BANANA = 2
    GRAPE = 3
    ORANGE = 4


class IpcCommands(IntEnum):
    NONE = 0
    START_GAME = 1
    MOVE_UP = 2
    MOVE_DOWN = 3
    MOVE_LEFT = 4
    MOVE_RIGHT = 5
    RESTART_GAME = 6
    QUIT_GAME = 7


@dataclass
class SnakeGameData:
    version: int
    board_width: int
    board_height: int
    score: int
    speed: int
    game_state: GameState
    food_position: Tuple[int, int]
    food_type: FoodType
    snake_head: Tuple[int, int]
    snake_length: int
    snake_body: List[Tuple[int, int]]
    neural_vector: List[int]
    snake_direction: Direction


class SnakeGameController:
    SHM_NAME = "/snake_game_shm"
    SOCKET_PATH = "/tmp/snake_game.sock"

    def __init__(self):
        self.shm_fd = None
        self.memory = None
        self.last_version = 0
        self.socket = None

    def connect(self) -> bool:
        try:
            self.shm = posix_ipc.SharedMemory(self.SHM_NAME, flags=0)
            self.memory = mmap.mmap(self.shm.fd, self.shm.size)

            print(f"✓ Connected to shared memory: {self.SHM_NAME}")
            print(f"  Size: {self.shm.size} bytes")
            return True

        except posix_ipc.ExistentialError:
            print(f"✗ Error: Shared memory {self.SHM_NAME} does not exist.")
            print("  Make sure the Snake game is running.")
            return False
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False

    def disconnect(self):
        if self.memory:
            self.memory.close()
        if hasattr(self, "shm"):
            self.shm.close_fd()

    def read_data(self) -> Optional[SnakeGameData]:
        if not self.memory:
            return None

        try:
            self.memory.seek(0)

            is_writing = struct.unpack("?", self.memory.read(1))[0]

            if is_writing:
                return None

            self.memory.read(3)

            version = struct.unpack("I", self.memory.read(4))[0]

            if version == self.last_version:
                return None

            board_width = struct.unpack("B", self.memory.read(1))[0]
            board_height = struct.unpack("B", self.memory.read(1))[0]
            score = struct.unpack("H", self.memory.read(2))[0]
            speed = struct.unpack("B", self.memory.read(1))[0]
            game_state = GameState(struct.unpack("B", self.memory.read(1))[0])

            food_x = struct.unpack("B", self.memory.read(1))[0]
            food_y = struct.unpack("B", self.memory.read(1))[0]
            food_position = (food_x, food_y)

            food_type = FoodType(struct.unpack("B", self.memory.read(1))[0])

            snake_head_x = struct.unpack("B", self.memory.read(1))[0]
            snake_head_y = struct.unpack("B", self.memory.read(1))[0]
            snake_head = (snake_head_x, snake_head_y)

            self.memory.read(1)

            snake_length = struct.unpack("H", self.memory.read(2))[0]

            self.memory.read(2)

            neural_vector = []
            for _ in range(11):
                value = struct.unpack("<i", self.memory.read(4))[0]
                neural_vector.append(value)

            snake_direction = Direction(struct.unpack("B", self.memory.read(1))[0])

            snake_body = []
            for _ in range(min(snake_length, 2048)):
                x = struct.unpack("B", self.memory.read(1))[0]
                y = struct.unpack("B", self.memory.read(1))[0]
                snake_body.append((x, y))

            self.last_version = version

            return SnakeGameData(
                version=version,
                board_width=board_width,
                board_height=board_height,
                score=score,
                speed=speed,
                game_state=game_state,
                food_position=food_position,
                food_type=food_type,
                snake_head=snake_head,
                snake_length=snake_length,
                snake_body=snake_body,
                neural_vector=neural_vector,
                snake_direction=snake_direction,
            )

        except Exception as e:
            print(f"Error reading data: {e}")
            return None

    def send_command(self, command: IpcCommands) -> bool:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(self.SOCKET_PATH)
            sock.send(struct.pack("B", command))

            ack = sock.recv(1)

            sock.close()

            return len(ack) == 1 and ack[0] == 1

        except (socket.error, socket.timeout) as e:
            print(f"\nCommand sending error: {e}")
            return False
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            return False


class SnakeHeuristicAI:
    def __init__(self):
        self.board_width = 0
        self.board_height = 0

    def get_adjacencies(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pos
        adjacencies = []
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_width and 0 <= ny < self.board_height:
                adjacencies.append((nx, ny))
        return adjacencies

    def bfs_search(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        snake_body: List[Tuple[int, int]],
    ) -> Optional[List[Tuple[int, int]]]:
        if start == end:
            return [start]

        queue = deque([start])
        paths = {start: [start]}
        snake_set = set(snake_body)

        while queue:
            current = queue.popleft()

            if current == end:
                return paths[current]

            for next_pos in self.get_adjacencies(current):
                # Sprawdź czy pozycja jest wolna (nie zajęta przez węża)
                # Ogon można odwiedzić, bo w momencie dotarcia tam już się przesunie
                if next_pos not in paths:
                    if next_pos not in snake_set or next_pos == end:
                        queue.append(next_pos)
                        paths[next_pos] = paths[current] + [next_pos]

        return None

    def count_free_space(self, start: Tuple[int, int], snake_body: List[Tuple[int, int]]) -> int:
        visited = set()
        queue = deque([start])
        snake_set = set(snake_body)

        while queue:
            current = queue.popleft()
            if current in visited or current in snake_set:
                continue

            visited.add(current)

            for next_pos in self.get_adjacencies(current):
                if next_pos not in visited and next_pos not in snake_set:
                    queue.append(next_pos)

        return len(visited)

    def is_safe_move(self, path_to_food: List[Tuple[int, int]], snake_body: List[Tuple[int, int]]) -> bool:
        if not path_to_food or len(path_to_food) < 2:
            return False

        # Symuluj węża po przejściu ścieżki i zjedzeniu
        # Nowa głowa będzie na końcu ścieżki (tam gdzie jedzenie)
        food_pos = path_to_food[-1]

        # Symuluj ruch węża wzdłuż ścieżki
        # Wąż przesuwa się o długość ścieżki-1 (bo głowa już jest na starcie)
        # path_length = len(path_to_food) - 1

        # Buduj nowego węża po zjedzeniu
        # Głowa na pozycji jedzenia + wąż przesuwa się o path_length i rośnie o 1
        new_snake = [food_pos]  # Nowa głowa na jedzeniu

        # Dodaj resztę ciała - wąż rośnie, więc nie usuwamy ogona
        for i, pos in enumerate(snake_body):
            if i < len(snake_body):  # Wąż rośnie, zachowujemy wszystkie segmenty
                new_snake.append(pos)

        # Teraz sprawdź czy z nowej pozycji można dotrzeć do ogona
        new_head = new_snake[0]
        new_tail = new_snake[-1]

        # Usuń ogon ze sprawdzania, bo gdy tam dotrzemy, będzie już wolny
        path_to_tail = self.bfs_search(new_head, new_tail, new_snake[:-1])

        return path_to_tail is not None

    def get_direction_to_pos(
        self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], current_dir: Direction
    ) -> Direction:
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]

        if dy == -1:
            return Direction.UP
        elif dy == 1:
            return Direction.DOWN
        elif dx == -1:
            return Direction.LEFT
        elif dx == 1:
            return Direction.RIGHT
        else:
            return current_dir

    def get_next_move(self, data: SnakeGameData) -> Direction:
        self.board_width = data.board_width
        self.board_height = data.board_height

        head = data.snake_head
        food = data.food_position
        snake_body = data.snake_body
        current_dir = data.snake_direction

        # Nie zawracaj w miejscu
        opposite_dirs = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        # 1. Spróbuj znaleźć ścieżkę do jedzenia
        path_to_food = self.bfs_search(head, food, snake_body)

        if path_to_food and len(path_to_food) > 1:
            # Sprawdź czy ścieżka jest bezpieczna (czy po zjedzeniu można dotrzeć do ogona)
            if self.is_safe_move(path_to_food, snake_body):
                next_pos = path_to_food[1]  # Pierwszy krok w ścieżce
                next_dir = self.get_direction_to_pos(head, next_pos, current_dir)
                if next_dir != opposite_dirs.get(current_dir):
                    return next_dir

        # 2. Jeśli nie ma bezpiecznej ścieżki do jedzenia, idź w kierunku ogona
        if len(snake_body) > 1:
            tail = snake_body[-1]
            # Usuń ogon z przeszkód bo będzie się przesuwał
            snake_without_tail = snake_body[:-1]
            path_to_tail = self.bfs_search(head, tail, snake_without_tail)

            if path_to_tail and len(path_to_tail) > 1:
                next_pos = path_to_tail[1]
                next_dir = self.get_direction_to_pos(head, next_pos, current_dir)
                if next_dir != opposite_dirs.get(current_dir):
                    return next_dir

        # 3. W ostateczności, wybierz ruch z największą wolną przestrzenią
        best_move = None
        best_space = -1

        for next_pos in self.get_adjacencies(head):
            # Nie wchodź w ciało węża
            if next_pos in snake_body:
                continue

            next_dir = self.get_direction_to_pos(head, next_pos, current_dir)

            # Nie zawracaj
            if next_dir == opposite_dirs.get(current_dir):
                continue

            # Symuluj ruch i sprawdź dostępną przestrzeń
            future_snake = [next_pos] + snake_body[:-1]  # Wąż się przesuwa (nie rośnie)
            free_space = self.count_free_space(next_pos, future_snake)

            if free_space > best_space:
                best_space = free_space
                best_move = next_dir

        if best_move is not None:
            return best_move

        # 4. Jeśli wszystko zawodzi, kontynuuj obecny kierunek (prawdopodobnie game over)
        return current_dir


def main() -> None:
    controller = SnakeGameController()
    heuristic_ai = SnakeHeuristicAI()

    if not controller.connect():
        return 1

    print("\n🐍 Snake Heuristic AI Controller")
    print("=" * 70)
    print("Algorytm heurystyczny (pathfinding + bezpieczeństwo)")
    print()
    print("Sterowanie:")
    print("  r - Start/Restart gry z algorytmem")
    print("  q - Quit")
    print("  Ctrl+C - Wyjście")
    print()

    ai_active = False
    game_started = False

    try:
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            while True:
                # Sprawdź input od użytkownika
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()

                    if key == "r":
                        controller.send_command(IpcCommands.START_GAME)
                        ai_active = True
                        game_started = True
                        print("\n[CMD] Start game with Heuristic AI")
                    elif key == "q":
                        controller.send_command(IpcCommands.QUIT_GAME)
                        print("\n[CMD] Quit game")
                        break

                # Odczytaj stan gry
                data = controller.read_data()

                if data:
                    # Wyświetl status
                    print(
                        f"\r[v{data.version:04d}] "
                        f"State: {data.game_state.name:10s} | "
                        f"Score: {data.score:4d} | "
                        f"Speed: {data.speed:2d} | "
                        f"Snake: {data.snake_length:3d} | "
                        f"Head: ({data.snake_head[0]:2d},{data.snake_head[1]:2d}) | "
                        f"Food: ({data.food_position[0]:2d},{data.food_position[1]:2d})",
                        end="",
                        flush=True,
                    )

                    # Jeśli AI jest aktywne i gra trwa
                    if ai_active and data.game_state == GameState.PLAYING:
                        # Pobierz decyzję od algorytmu heurystycznego
                        direction = heuristic_ai.get_next_move(data)

                        # Wyślij komendę
                        command_map = {
                            Direction.UP: IpcCommands.MOVE_UP,
                            Direction.DOWN: IpcCommands.MOVE_DOWN,
                            Direction.LEFT: IpcCommands.MOVE_LEFT,
                            Direction.RIGHT: IpcCommands.MOVE_RIGHT,
                        }

                        if direction in command_map:
                            controller.send_command(command_map[direction])

                    # Jeśli gra się skończyła
                    elif game_started and data.game_state == GameState.GAME_OVER:
                        print(f"\n\n🎮 GAME OVER! Final Score: {data.score}")
                        print(f"   Snake Length: {data.snake_length}")
                        ai_active = False
                        game_started = False

                time.sleep(0.01)  # 10ms delay

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    except KeyboardInterrupt:
        print("\n\n✓ Heuristic AI stopped")
    finally:
        controller.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
