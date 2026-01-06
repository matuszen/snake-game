#Hyperparameters and such

class Config():
    def __init__(self):
        self.WIDTH = 20
        self.HEIGHT = 20
        self.MAX_STEPS = 150 #max steps without eating fruit

        self.INPUT_SIZE = 12
        self.HIDDEN_SIZE = 32
        self.OUTPUT_SIZE = 4
        self.WEIGHT_RANGE = 3.0

        self.MUTATION_RATE = 0.2
        self.MUTATION_VARIANCE = 0.5

        self.POP_RETENTION = 0.1 # all 3 of these need to sum to 1.0
        self.POP_CHILDREN = 0.80
        self.POP_RANDOM = 0.1

        self.GENERATIONS = 2000
        self.POPULATION_SIZE = 200 #how many agents per worker
        self.WORKERS = 4
        self.MIGRATION_INTERVAL = 50

        self.FOOD_REWARD = 10
        self.STEP_REWARD = 0.001
