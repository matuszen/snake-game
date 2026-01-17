from collections import deque
from typing import Optional

from SnakeGameController import (
    Direction,
    SnakeGameData,
)


class SnakeHeuristicAI:
    def __init__(self):
        self.board_width = 0
        self.board_height = 0

    def get_adjacencies(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = pos
        adjacencies = []
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board_width and 0 <= ny < self.board_height:
                adjacencies.append((nx, ny))
        return adjacencies

    def bfs_search(
        self, start: tuple[int, int], end: tuple[int, int], snake_body: list[tuple[int, int]]
    ) -> Optional[list[tuple[int, int]]]:
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

    def count_free_space(self, start: tuple[int, int], snake_body: list[tuple[int, int]]) -> int:
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

    def is_safe_move(self, path_to_food: list[tuple[int, int]], snake_body: list[tuple[int, int]]) -> bool:
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
        self, from_pos: tuple[int, int], to_pos: tuple[int, int], current_dir: Direction
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
        head: tuple[int, int],
        food: tuple[int, int],
        snake_body: list[tuple[int, int]],
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
        self, head: tuple[int, int], snake_body: list[tuple[int, int]], current_dir: Direction, opposite_dirs: dict
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
        self, head: tuple[int, int], snake_body: list[tuple[int, int]], current_dir: Direction, opposite_dirs: dict
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
