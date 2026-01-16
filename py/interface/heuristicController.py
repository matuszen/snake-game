import mmap
import socket
import struct
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
        self, start: Tuple[int, int], end: Tuple[int, int], snake_body: List[Tuple[int, int]]
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

        food_pos = path_to_food[-1]

        new_snake = [food_pos]

        for i, pos in enumerate(snake_body):
            if i < len(snake_body):
                new_snake.append(pos)

        new_head = new_snake[0]
        new_tail = new_snake[-1]

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

    def _get_opposite_directions(self) -> dict:
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

    def _try_move_to_food(
        self,
        head: Tuple[int, int],
        food: Tuple[int, int],
        snake_body: List[Tuple[int, int]],
        current_dir: Direction,
        opposite_dirs: dict,
    ) -> Optional[Direction]:
        path_to_food = self.bfs_search(head, food, snake_body)

        if path_to_food and len(path_to_food) > 1:
            if self.is_safe_move(path_to_food, snake_body):
                next_pos = path_to_food[1]
                next_dir = self.get_direction_to_pos(head, next_pos, current_dir)
                if next_dir != opposite_dirs.get(current_dir):
                    return next_dir

        return None

    def _try_move_to_tail(
        self, head: Tuple[int, int], snake_body: List[Tuple[int, int]], current_dir: Direction, opposite_dirs: dict
    ) -> Optional[Direction]:
        if len(snake_body) <= 1:
            return None

        tail = snake_body[-1]
        snake_without_tail = snake_body[:-1]
        path_to_tail = self.bfs_search(head, tail, snake_without_tail)

        if path_to_tail and len(path_to_tail) > 1:
            next_pos = path_to_tail[1]
            next_dir = self.get_direction_to_pos(head, next_pos, current_dir)
            if next_dir != opposite_dirs.get(current_dir):
                return next_dir

        return None

    def _find_best_space_move(
        self, head: Tuple[int, int], snake_body: List[Tuple[int, int]], current_dir: Direction, opposite_dirs: dict
    ) -> Optional[Direction]:
        best_move = None
        best_space = -1

        for next_pos in self.get_adjacencies(head):
            if next_pos in snake_body:
                continue

            next_dir = self.get_direction_to_pos(head, next_pos, current_dir)

            if next_dir == opposite_dirs.get(current_dir):
                continue

            future_snake = [next_pos] + snake_body[:-1]
            free_space = self.count_free_space(next_pos, future_snake)

            if free_space > best_space:
                best_space = free_space
                best_move = next_dir

        return best_move

    def get_next_move(self, data: SnakeGameData) -> Direction:
        self.board_width = data.board_width
        self.board_height = data.board_height

        head = data.snake_head
        food = data.food_position
        snake_body = data.snake_body
        current_dir = data.snake_direction

        opposite_dirs = self._get_opposite_directions()

        move = self._try_move_to_food(head, food, snake_body, current_dir, opposite_dirs)
        if move is not None:
            return move

        move = self._try_move_to_tail(head, snake_body, current_dir, opposite_dirs)
        if move is not None:
            return move

        move = self._find_best_space_move(head, snake_body, current_dir, opposite_dirs)
        if move is not None:
            return move

        return current_dir
