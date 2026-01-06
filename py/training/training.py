import logging
import os
import sys

sys.path.insert(0, '.')
import matplotlib.pyplot as plt
import numpy as np
import ray

from py.training.config import Config
from py.training.utils import save_network
from py.training.worker import Worker

os.environ['RAY_DISABLE_MEMORY_MONITOR'] = '1'
logging.getLogger('ray.core_worker').setLevel(logging.CRITICAL)
logging.getLogger('ray._raylet').setLevel(logging.CRITICAL)

ray.init(log_to_driver=False, ignore_reinit_error=True)


def main():
    config = Config()
    workers = [
        Worker.remote(config, pop_size=config.POPULATION_SIZE, hidden_size=config.HIDDEN_SIZE)
        for _ in range(config.WORKERS)
        ]
    best_network = None
    best_fit = -1
    best_history = []
    worker_history = [ [] for _ in range(config.WORKERS) ]
    print("=" * 60)
    print("SNAKE AI TRAINING - CONFIGURATION".center(60))
    print("=" * 60)
    print(f"  Workers:                  {config.WORKERS}")
    print(f"  Population Size:          {config.POPULATION_SIZE}")
    print(f"  Generations:              {config.GENERATIONS}")
    print(f"  Hidden Layer Size:        {config.HIDDEN_SIZE}")
    print(f"  Board Size:               {config.WIDTH}x{config.HEIGHT}")
    print(f"  Max Steps (no fruit):     {config.MAX_STEPS}")
    print(f"  Mutation Rate:            {config.MUTATION_RATE}")
    print(f"  Mutation Variance:        {config.MUTATION_VARIANCE}")
    print(f"  Retention %:              {config.POP_RETENTION * 100:.0f}%")
    print(f"  Children %:               {config.POP_CHILDREN * 100:.0f}%")
    print(f"  Random %:                 {config.POP_RANDOM * 100:.0f}%")
    print("=" * 60)
    print()

    for gen in range(config.GENERATIONS):
        futures = [worker.run.remote() for worker in workers]
        results = ray.get(futures)
        global_best = 0
        #migrations
        if gen > 0 and gen % config.MIGRATION_INTERVAL == 0:
            try:
                mig_best_net = [result['best_network'] for result in results]
                mig_global_best = mig_best_net[np.argmax([result['best_fitness'] for result in results])]
                futures = [worker.inject_network.remote(mig_global_best) for worker in workers]
                save_network(mig_global_best, f"py/training/models/autosaves/migration{gen}_{int(np.max([result['best_fitness'] for result in results]))}.json") # noqa
                save_network(best_network, f"py/training/models/best/best_network_gen{gen}_{best_fit}.json")

                ray.get(futures, timeout=30)
            except Exception as e:
                print(f"Migration failed: {e}", flush=True)

        output_lines = []
        for worker, result in enumerate(results):
            best_snake = result['best_network']
            max_fit = result['best_fitness']
            avg_fit = result['avg_fitness']
            output_lines.append(f"Worker {worker}: Gen {gen} | Max: {max_fit:.2f} | Avg: {avg_fit:.2f}")

            if max_fit > best_fit:
                best_fit = max_fit
                best_network = best_snake

            if max_fit > global_best:
                global_best = max_fit

            worker_history[worker].append(max_fit)
        best_history.append(global_best)
        output_lines.append(
            f"\nGeneration {gen} complete. Generation Best: {global_best:.2f}. Global Best: {best_fit:.2f}")

        if gen > 0:
            sys.stdout.write(f"\033[{len(output_lines)+1}A")
            sys.stdout.flush()

        for line in output_lines:
            print(f"\033[2K{line}")

    print("Training complete. Saving best network...")
    save_network(best_network, f"py/training/models/network_{int(best_fit)}.json")
    num_workers = config.WORKERS
    fig, axes = plt.subplots(num_workers + 1, 1, figsize=(12, 4 * (num_workers + 1)))

    for i in range(num_workers):
        axes[i].plot(worker_history[i], marker='o', label=f'Worker {i}')
        axes[i].set_ylabel('Best Fitness')
        axes[i].set_title(f'Worker {i} Progress')
        axes[i].grid()
        axes[i].legend()

    axes[-1].plot(best_history, marker='s', color='red', linewidth=2, label='Global Best')
    axes[-1].set_xlabel('Generation')
    axes[-1].set_ylabel('Best Fitness')
    axes[-1].set_title('Global Best Fitness')
    axes[-1].grid()
    axes[-1].legend()

    plt.tight_layout()
    plt.savefig('py/training/models/training_progress.png', dpi=150)
    plt.show()

    ray.shutdown()

if __name__ == "__main__":
    main()
