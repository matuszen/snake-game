"""Snake game library."""

from enum import Enum


class Direction(Enum):
    """Directions for snake movement."""

    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class GameState(Enum):
    """Possible states of the game."""

    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    QUIT = 4


class StepResult:
    """Result of a game step."""

    distances: list[float]
    """Distances to obstacles in various directions."""
    is_game_over: bool
    """Indicates if the game is over."""
    fruit_picked_up: bool
    """Indicates if the fruit was picked up in this step."""

    def __init__(self) -> None: ...


class Game:
    """Snake game class."""

    def __init__(self, board_width: int = 20, board_height: int = 20) -> None: ...

    def initialize_game(self) -> StepResult:
        """Initialize the game and return the initial game state."""
        ...

    def step_game(self, direction: Direction) -> StepResult:
        """Advance the game by one step in the given direction."""
        ...
