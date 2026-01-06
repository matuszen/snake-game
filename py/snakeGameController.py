import mmap
import select
import socket
import struct
import sys
import termios
import time
import tty
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple

import numpy as np
import posix_ipc
import snakeAgent


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
    neural_vector: List[float]
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


def main():
    controller = SnakeGameController()
    aiMode = 0
    model = None
    if not controller.connect():
        return 1

    print("\n🐍 Snake Game Monitor and Controller")
    print("=" * 70)
    print("Press Ctrl+C to exit\n")
    print("Available commands:")
    print("  r - Start/Restart game")
    print("  t - Toggle AI control ")
    print("  w/↑ - Move up")
    print("  a/← - Move left")
    print("  s/↓ - Move down")
    print("  d/→ - Move right")
    print("  q - Quit game")
    print()

    try:
        last_detailed_version = -1

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            while True:
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()

                    command = None
                    if key == "r":
                        command = IpcCommands.START_GAME
                        print("\n[CMD] Start game")
                    elif key == "t":
                        aiMode = 1
                        command = IpcCommands.START_GAME
                        print("\n[CMD] AI mode ON")
                        network = snakeAgent.SnakeAgent("py/training/models/best_network_gen1200_1609.369.json")
                    elif key == "w" and aiMode == 0:
                        command = IpcCommands.MOVE_UP
                    elif key == "a" and aiMode == 0:
                        command = IpcCommands.MOVE_LEFT
                    elif key == "d" and aiMode == 0:
                        command = IpcCommands.MOVE_RIGHT
                    elif key == "s" and aiMode == 0:
                        command = IpcCommands.MOVE_DOWN
                    elif key == "q":
                        command = IpcCommands.QUIT_GAME
                        print("\n[CMD] Quit game")

                    if command:
                        controller.send_command(command)
                        command = None

                data = controller.read_data()
                if aiMode == 1 and data and network:
                    inputs = data.neural_vector
                    outputs = network.move(inputs)
                    dir_idx = np.argmax(outputs)

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
                    print(
                        f"\r[v{data.version:04d}] "
                        f"State: {data.game_state.name:10s} | "
                        f"Score: {data.score:4d} | "
                        f"Speed: {data.speed:2d} | "
                        f"Snake: {data.snake_length:3d} segments | "
                        f"Head: ({data.snake_head[0]:2d},{data.snake_head[1]:2d}) | "
                        f"Food: {data.food_type.name:6s} ({data.food_position[0]:2d},{data.food_position[1]:2d})",
                        f"Input: {[f'{v:.2f}' for v in data.neural_vector]}",
                        end="",
                        flush=True,
                    )

                    if data.version % 100 == 0 and data.version != last_detailed_version:
                        last_detailed_version = data.version
                        print()
                        print("\n--- Snake position details ---")
                        print(f"Head (segment 0): ({data.snake_head[0]:2d}, {data.snake_head[1]:2d})")

                        segments_to_show = min(10, len(data.snake_body))
                        for i in range(segments_to_show):
                            print(f"Segment {i:2d}: ({data.snake_body[i][0]:2d}, {data.snake_body[i][1]:2d})")

                        if len(data.snake_body) > segments_to_show:
                            print(f"... (and {len(data.snake_body) - segments_to_show} more segments)")
                        print()

                time.sleep(0.01)

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")
    finally:
        controller.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
