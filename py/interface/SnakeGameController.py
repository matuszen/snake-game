"""Interface for communicating with the C++ Snake Game engine via Shared Memory and IPC Sockets."""

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
    CHANGE_BOARD_SIZE = 8


@dataclass
class SnakeGameData:
    """Data structure representing the snapshot of the game state.

    Attributes:
        version (int): Protocol version / frame counter.
        board_width (int): Width of the game board.
        board_height (int): Height of the game board.
        score (int): Current player score.
        speed (int): Current game speed level.
        game_state (GameState): Current enum state of the game.
        food_position (Tuple[int, int]): (x, y) coordinates of the food.
        food_type (FoodType): Type of the food item.
        snake_head (Tuple[int, int]): (x, y) coordinates of the snake's head.
        snake_length (int): Current length of the snake.
        snake_body (List[Tuple[int, int]]): List of (x, y) coordinates for body segments.
        neural_vector (List[int]): Sensor inputs for neural network.
        snake_direction (Direction): Current movement direction.

    """

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
    """Interface for communicating with the C++ Snake Game engine via Shared Memory and IPC Sockets.

    This controller allows reading game state (via shared memory) and sending commands
    (via a UNIX domain socket).
    """

    SHM_NAME = "/snake_game_shm"
    SOCKET_PATH = "/tmp/snake_game.sock"

    def __init__(self, shm_name: str = SHM_NAME, socket_path: str = SOCKET_PATH):
        """Initialize the controller with paths to shared memory and socket.

        Args:
            shm_name (str): Name of the POSIX shared memory object.
            socket_path (str): Path to the UNIX domain socket.

        """
        self.shm_name = shm_name
        self.socket_path = socket_path
        self.shm: Optional[posix_ipc.SharedMemory] = None
        self.memory: Optional[mmap.mmap] = None
        self.last_version = 0

    def connect(self) -> bool:
        """Establish connection to the shared memory segment.

        Returns:
            bool: True if connection successful, False otherwise.

        """
        try:
            self.shm = posix_ipc.SharedMemory(self.shm_name, flags=0)
            self.memory = mmap.mmap(self.shm.fd, self.shm.size)
            print(f"Connected to shared memory: {self.shm_name}")
            return True
        except posix_ipc.ExistentialError:
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Close the shared memory connection and release resources."""
        if self.memory:
            self.memory.close()
            self.memory = None
        if hasattr(self, "shm") and self.shm:
            self.shm.close_fd()
            self.shm = None

    def read_data(self) -> Optional[SnakeGameData]:
        """Read the current game state from shared memory.

        Returns:
            Optional[SnakeGameData]: Parsed game data object, or None if reading fails.

        """
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
            for _ in range(12):
                value = struct.unpack("<f", self.memory.read(4))[0]
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

        except Exception:
            return None

    def send_command(self, command: IpcCommands, *args) -> bool:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(self.socket_path)
            sock.send(struct.pack("B", command.value))

            if command == IpcCommands.CHANGE_BOARD_SIZE and len(args) == 2:
                try:
                    width = int(args[0])
                    height = int(args[1])
                except (TypeError, ValueError):
                    print("Invalid board size arguments: must be integers.")
                    sock.close()
                    return False

                if not (0 <= width <= 255 and 0 <= height <= 255):
                    print("Invalid board size arguments: must be in range 0-255.")
                    sock.close()
                    return False

                sock.send(struct.pack("BB", width, height))
            ack = sock.recv(1)
            sock.close()

            return len(ack) == 1 and ack[0] == 1

        except (socket.error, socket.timeout) as e:
            print(f"Command sending error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
