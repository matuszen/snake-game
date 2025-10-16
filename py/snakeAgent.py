import keras
import numpy as np


class SnakeAgent:
    def __init__(self, name):
        try:
            self.model = keras.models.load_model(name)
        except Exception as e:
            print(f"Error loading model: {e}")

    def predict(self, state):
        return self.model.predict(state, verbose=0)

    def move(self, state, current_direction):
        prediction = self.predict(state)
        relative_direction = np.argmax(prediction)  # 0=straight, 1=right, 2=left

        if relative_direction == 0:
            absolute_direction = current_direction
        elif relative_direction == 1:
            # Turn right
            if current_direction == 0:  # UP -> RIGHT
                absolute_direction = 3
            elif current_direction == 1:  # DOWN -> LEFT
                absolute_direction = 2
            elif current_direction == 2:  # LEFT -> UP
                absolute_direction = 0
            elif current_direction == 3:  # RIGHT -> DOWN
                absolute_direction = 1
        elif relative_direction == 2:
            # Turn left
            if current_direction == 0:  # UP -> LEFT
                absolute_direction = 2
            elif current_direction == 1:  # DOWN -> RIGHT
                absolute_direction = 3
            elif current_direction == 2:  # LEFT -> DOWN
                absolute_direction = 1
            elif current_direction == 3:  # RIGHT -> UP
                absolute_direction = 0
        else:
            absolute_direction = current_direction

        return absolute_direction
