import mmap
import socket
import struct
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


class Controller:
    SHM_NAME = "/snake_game_shm"
    SOCKET_PATH = "/tmp/snake_game.sock"

    def __init__(self):
        self.memory = None
        self.last_version = 0

    def connect(self) -> bool:
        try:
            self.shm = posix_ipc.SharedMemory(self.SHM_NAME, flags=0)
            self.memory = mmap.mmap(self.shm.fd, self.shm.size)
            print(f"✓ Connected to shared memory: {self.SHM_NAME}")
            return True
        except posix_ipc.ExistentialError:
            print(f"✗ Shared memory {self.SHM_NAME} does not exist. Start the game first.")
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
            neural_vector = [struct.unpack("<i", self.memory.read(4))[0] for _ in range(11)]
            snake_direction = Direction(struct.unpack("B", self.memory.read(1))[0])
            snake_body = [
                (struct.unpack("B", self.memory.read(1))[0], struct.unpack("B", self.memory.read(1))[0])
                for _ in range(min(snake_length, 2048))
            ]
            self.last_version = version
            return SnakeGameData(
                version,
                board_width,
                board_height,
                score,
                speed,
                game_state,
                food_position,
                food_type,
                snake_head,
                snake_length,
                snake_body,
                neural_vector,
                snake_direction,
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
        except Exception as e:
            print(f"Command error: {e}")
            return False
