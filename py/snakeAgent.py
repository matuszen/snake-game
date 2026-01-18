"""Snake Agent wrapper for loading and using trained neural network models."""

from py.training.neural import Neural
from py.training.utils import load_network


class SnakeAgent:
    """Agent that controls the snake using a trained neural network model.

    This class wraps a Neural network model and provides a simple interface
    for loading models from disk and making movement predictions.

    Attributes:
        _model (Neural): The loaded neural network model.

    """

    def __init__(self, path: str) -> None:
        """Initialize the SnakeAgent by loading a model from file.

        Args:
            path (str): Path to the JSON file containing the saved neural network.

        """
        try:
            self._model: Neural = load_network(path)
        except Exception as e:
            print(f"Error loading model: {e}")

    def move(self, inputs):
        """Predict the next move based on the given inputs.

        Args:
            inputs: Neural network input vector (typically sensor distances).

        Returns:
            list: Output activations for each direction (UP, DOWN, LEFT, RIGHT).

        Raises:
            ValueError: If the model is not loaded.

        """
        if not self._model:
            raise ValueError("Model not loaded.")
        return self._model.predict(inputs)
