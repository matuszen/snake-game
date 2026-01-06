import sys

sys.path.insert(0, '.')

from py.training.neural import Neural
from py.training.utils import load_network


class SnakeAgent:
    def __init__(self, path: str) -> None:
        try:
            self._model: Neural = load_network(path)
        except Exception as e:
            print(f"Error loading model: {e}")

    def move(self, inputs):
        if not self._model:
            raise ValueError("Model not loaded.")
        return self._model.predict(inputs)
