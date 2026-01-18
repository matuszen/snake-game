"""Configuration parameters for Snake AI genetic algorithm training."""


class Config:
    """Configuration parameters for the Snake AI training.

    This class contains all hyperparameters and settings for training a neural
    network to play Snake using a genetic algorithm with multiple workers.

    Attributes:
        WIDTH (int): Game board width in tiles.
        HEIGHT (int): Game board height in tiles.
        MAX_STEPS (int): Maximum steps without eating food before game ends.
        INPUT_SIZE (int): Number of input neurons (sensor count).
        HIDDEN_SIZE (int): Number of hidden layer neurons.
        OUTPUT_SIZE (int): Number of output neurons (4 directions).
        WEIGHT_RANGE (float): Range for weight initialization [-range, +range].
        MUTATION_RATE (float): Probability of mutating each weight.
        MUTATION_VARIANCE (float): Maximum variance for weight mutations.
        POP_RETENTION (float): Fraction of top performers to keep unchanged.
        POP_CHILDREN (float): Fraction of population to generate via crossover.
        POP_RANDOM (float): Fraction of population to randomly reinitialize.
        GENERATIONS (int): Total number of training generations.
        POPULATION_SIZE (int): Number of individuals in each worker's population.
        WORKERS (int): Number of parallel training workers.
        MIGRATION_INTERVAL (int): Generations between worker synchronizations.
        FOOD_REWARD (float): Fitness reward for eating food.
        STEP_REWARD (float): Fitness reward per step survived.

    """

    WIDTH = 20
    HEIGHT = 20
    MAX_STEPS = 150

    INPUT_SIZE = 12
    HIDDEN_SIZE = 32
    OUTPUT_SIZE = 4
    WEIGHT_RANGE = 3.0

    MUTATION_RATE = 0.2
    MUTATION_VARIANCE = 0.5

    POP_RETENTION = 0.1
    POP_CHILDREN = 0.80
    POP_RANDOM = 0.1

    GENERATIONS = 2000
    POPULATION_SIZE = 200
    WORKERS = 4
    MIGRATION_INTERVAL = 50

    FOOD_REWARD = 10
    STEP_REWARD = 0.001
