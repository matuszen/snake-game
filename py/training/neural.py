"""Simple feedforward neural network implementation for genetic algorithm training."""

import random

import numpy as np


class Neural:
    """Simple feedforward neural network with one hidden layer.

    This class implements a basic neural network suitable for evolutionary
    training. It supports forward propagation, mutation, and crossover operations.

    Attributes:
        weight_range (float): Maximum absolute value for weights.
        inputs (list): Input layer activations.
        hidden (list): Hidden layer activations.
        hidden_weights (list): Weights from input to hidden layer (with bias).
        outputs (list): Output layer activations.
        output_weights (list): Weights from hidden to output layer (with bias).

    """

    def __init__(self, input_size, hidden_size, output_size, weight_range):
        """Initialize neural network with random weights.

        Args:
            input_size (int): Number of input neurons.
            hidden_size (int): Number of hidden layer neurons.
            output_size (int): Number of output neurons.
            weight_range (float): Range for random weight initialization.

        """
        self.weight_range = weight_range
        self.inputs = [0.0 for _ in range(input_size)]
        self.hidden = [0.0 for _ in range(hidden_size)]
        self.hidden_weights = [
            [random.uniform(-weight_range, weight_range) for _ in range(input_size + 1)] for _ in range(hidden_size)
        ]
        self.outputs = [0.0 for _ in range(output_size)]
        self.output_weights = [
            [random.uniform(-weight_range, weight_range) for _ in range(hidden_size + 1)] for _ in range(output_size)
        ]

    def predict(self, input):
        """Perform forward propagation to compute network output.

        Args:
            input (list): Input vector matching the network's input size.

        Returns:
            list: Output activations for each output neuron.

        Raises:
            ValueError: If input size doesn't match network input size.

        """
        if len(input) != len(self.inputs):
            raise ValueError("Input sizes dont match!")
        self.inputs = input

        for node, _ in enumerate(self.hidden):
            sum = self.hidden_weights[node][0]
            sum += np.dot(self.hidden_weights[node][1:], self.inputs)
            self.hidden[node] = self.sigmoid(sum)

        for node, _ in enumerate(self.outputs):
            sum = self.output_weights[node][0]
            sum += np.dot(self.output_weights[node][1:], self.hidden)
            self.outputs[node] = self.sigmoid(sum)

        return self.outputs

    def _mutate_weights(self, weights, mutation_rate, mutation_variance):
        for node in range(len(weights)):
            for weight in range(len(weights[node])):
                if random.random() < mutation_rate:
                    weights[node][weight] += random.uniform(-mutation_variance, mutation_variance)
                    if weights[node][weight] > self.weight_range:
                        weights[node][weight] = self.weight_range
                    elif weights[node][weight] < -self.weight_range:
                        weights[node][weight] = -self.weight_range

    def mutate(self, mutation_rate, mutation_variance):
        """Apply random mutations to network weights.

        Args:
            mutation_rate (float): Probability of mutating each individual weight.
            mutation_variance (float): Maximum change magnitude for mutations.

        """
        self._mutate_weights(self.hidden_weights, mutation_rate, mutation_variance)
        self._mutate_weights(self.output_weights, mutation_rate, mutation_variance)

    def merge(self, other):
        """Create a child network by combining weights from two parents.

        Args:
            other (Neural): The other parent network to crossover with.

        Returns:
            Neural: A new network with weights randomly selected from both parents.

        """
        child = Neural(len(self.inputs), len(self.hidden), len(self.outputs), self.weight_range)

        for node in range(len(self.hidden_weights)):
            for weight in range(len(self.hidden_weights[node])):
                if random.random() < 0.5:
                    child.hidden_weights[node][weight] = self.hidden_weights[node][weight]
                else:
                    child.hidden_weights[node][weight] = other.hidden_weights[node][weight]

        for node in range(len(self.output_weights)):
            for weight in range(len(self.output_weights[node])):
                if random.random() < 0.5:
                    child.output_weights[node][weight] = self.output_weights[node][weight]
                else:
                    child.output_weights[node][weight] = other.output_weights[node][weight]

        return child

    def sigmoid(self, x):
        """Sigmoid activation function.

        Args:
            x (float): Input value.

        Returns:
            float: Sigmoid activation output in range (0, 1).

        """
        return 1 / (1 + np.exp(-x))
