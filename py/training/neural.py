import random

import numpy as np


class Neural:
    """Simple feedforward neural network with one hidden layer."""

    def __init__(self, input_size, hidden_size, output_size, weight_range):
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
        self._mutate_weights(self.hidden_weights, mutation_rate, mutation_variance)
        self._mutate_weights(self.output_weights, mutation_rate, mutation_variance)

    def merge(self, other):
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
        return 1 / (1 + np.exp(-x))
