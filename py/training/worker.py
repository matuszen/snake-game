"""Ray worker for parallel genetic algorithm training."""

import copy

import numpy as np
import ray

from py import snake_lib as snakelib
from py.training.neural import Neural


@ray.remote
class Worker:
    """Distributed worker for training a population of neural networks.

    This Ray remote class manages a population of neural networks, evaluates
    their fitness by playing Snake, and evolves them using genetic algorithms.

    Attributes:
        gen_number (int): Current generation number.
        config (Config): Training configuration.
        pop_size (int): Size of the population.
        hidden_size (int): Size of hidden layer in networks.
        population (list): List of Neural networks in this worker.
        games (list): List of Snake game instances.
        gamestates (list): Current game states for each individual.
        directions (list): Available movement directions.

    """

    def __init__(self, config, pop_size, hidden_size):
        """Initialize worker with a random population.

        Args:
            config (Config): Training configuration object.
            pop_size (int): Number of individuals in the population.
            hidden_size (int): Number of hidden neurons in each network.

        """
        self.gen_number = 0
        self.config = config
        self.pop_size = pop_size
        self.hidden_size = hidden_size
        self.population = [
            Neural(config.INPUT_SIZE, hidden_size, config.OUTPUT_SIZE, config.WEIGHT_RANGE) for _ in range(pop_size)
        ]
        self.games = [snakelib.Game(config.WIDTH, config.HEIGHT) for _ in range(pop_size)]

        self.gamestates = [game.initialize_game() for game in self.games]
        self.directions = [
            snakelib.Direction.UP,
            snakelib.Direction.DOWN,
            snakelib.Direction.LEFT,
            snakelib.Direction.RIGHT,
        ]

    def run(self):
        """Execute one generation: evaluate fitness and evolve population.

        Returns:
            dict: Statistics including best network, best fitness, and average fitness.

        """
        fitness = self.eval()
        stats = self.evolve(fitness)
        return stats

    def eval(self):
        """Evaluate fitness of all individuals in the population.

        Each individual plays a full game of Snake. Fitness is computed based
        on food collected and survival time.

        Returns:
            list: Fitness scores for each individual in the population.

        """
        fitness = [0] * self.pop_size
        active = [True] * self.pop_size
        steps = [0] * self.pop_size
        survived_steps = [0] * self.pop_size
        while any(active):
            for i in range(self.pop_size):
                if not active[i]:
                    continue
                inputs = self.gamestates[i].distances
                outputs = self.population[i].predict(inputs)
                direction = np.argmax(outputs)

                self.gamestates[i] = self.games[i].step_game(self.directions[direction])

                if self.gamestates[i].fruit_picked_up:
                    fitness[i] += 1
                    steps[i] = 0
                else:
                    steps[i] += 1

                if self.gamestates[i].is_game_over or steps[i] >= self.config.MAX_STEPS:
                    active[i] = False
                survived_steps[i] += 1

        self.gen_number += 1
        fitness = [
            fitness[i] * self.config.FOOD_REWARD + survived_steps[i] * self.config.STEP_REWARD
            for i in range(self.pop_size)
        ]
        return fitness

    def evolve(self, fitness):
        """Evolve the population using genetic algorithm operators.

        Applies selection, crossover, and mutation to create the next generation.

        Args:
            fitness (list): Fitness scores for current population.

        Returns:
            dict: Dictionary with best network, best fitness, and average fitness.

        """
        sorted_indices = np.argsort(fitness)[::-1]
        sorted_population = [self.population[i] for i in sorted_indices]
        sorted_fitness = np.array([fitness[i] for i in sorted_indices])

        mutation_rate = self.config.MUTATION_RATE
        new_pop = []

        num_retain = int(self.pop_size * self.config.POP_RETENTION)
        num_children = int(self.pop_size * self.config.POP_CHILDREN)
        num_random = self.pop_size - num_retain - num_children

        for i in range(num_retain):
            new_pop.append(sorted_population[i])

        if np.max(sorted_fitness) > 0:
            probabilities = sorted_fitness / np.sum(sorted_fitness)
        else:
            probabilities = np.ones(len(sorted_fitness)) / len(sorted_fitness)

        for _ in range(num_children):
            parents = np.random.choice(self.pop_size, size=2, p=probabilities)
            p1 = sorted_population[parents[0]]
            p2 = sorted_population[parents[1]]

            child = p1.merge(p2)
            child.mutate(mutation_rate, self.config.MUTATION_VARIANCE)
            new_pop.append(child)

        for _ in range(num_random):
            new_pop.append(
                Neural(self.config.INPUT_SIZE, self.hidden_size, self.config.OUTPUT_SIZE, self.config.WEIGHT_RANGE)
            )

        self.population = new_pop
        self.games = [snakelib.Game(self.config.WIDTH, self.config.HEIGHT) for _ in range(self.pop_size)]
        self.gamestates = [game.initialize_game() for game in self.games]
        return {
            "best_network": sorted_population[0],
            "best_fitness": sorted_fitness[0],
            "avg_fitness": np.mean(sorted_fitness),
        }

    def inject_network(self, network):
        """Inject a migrated network into the population.

        Replaces a random individual with the provided network (typically
        the global best from another worker).

        Args:
            network (Neural): Network to inject into the population.

        """
        try:
            replace_idx = np.random.randint(0, self.pop_size)
            self.population[replace_idx] = copy.deepcopy(network)
        except Exception as e:
            print(f"Error injecting network: {e}", flush=True)
