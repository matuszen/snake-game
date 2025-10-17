import keras
import numpy as np


class SnakeAgent:
    def __init__(self, name: str) -> None:
        try:
            self._model: keras.Model = keras.models.load_model(name)
        except Exception as e:
            print(f"Error loading model: {e}")

    def predict(self, state: np.ndarray) -> np.ndarray:
        return self._model.predict(state, verbose=0)

    def move(self, state: np.ndarray, current_direction: int) -> int:
        self._prediction = self.predict(state)
        relative_direction = np.argmax(self._prediction)

        if relative_direction == 0:
            absolute_direction = current_direction
        elif relative_direction == 1:
            if current_direction == 0:
                absolute_direction = 3
            elif current_direction == 1:
                absolute_direction = 2
            elif current_direction == 2:
                absolute_direction = 0
            elif current_direction == 3:
                absolute_direction = 1
        elif relative_direction == 2:
            if current_direction == 0:
                absolute_direction = 2
            elif current_direction == 1:
                absolute_direction = 3
            elif current_direction == 2:
                absolute_direction = 1
            elif current_direction == 3:
                absolute_direction = 0
        else:
            absolute_direction = current_direction

        return absolute_direction
