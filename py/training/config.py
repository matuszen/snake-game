class Config:
    """Configuration parameters for the Snake AI training."""

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
