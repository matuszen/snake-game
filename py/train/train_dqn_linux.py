#!/usr/bin/env python3


import os
import sys
import keras
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from collections import deque
from keras import layers, models, optimizers


# =============================================================================
# SETUP AND IMPORTS
# =============================================================================

#buildPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "build"))
#sys.path.insert(0, buildPath)

try:
    import snake_env
    print("Module imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    #print(f"Looking in: {buildPath}")
    raise


# =============================================================================
# HYPERPARAMETERS
# =============================================================================

LOAD_MODEL = False
LOAD_MODEL_PATH = "models/dqn_model_episode_200.keras"

LEARNING_RATE = 0.00001
BATCH_SIZE = 1000
EPOCHS = 200
MEMORY_SIZE = 100000
EPSILON = 1.0
EPSILON_DECAY = 0.975
MIN_EPSILON = 0.05
GAMMA = 0.95
TARGET_UPDATE_FREQ = 20
TRAINING_THRESHOLD = 1000
TRAINING_STEPS = 8

# Visualization Configuration
SAVE_PLOTS = True                    # Toggle to enable/disable plot saving
PLOT_SAVE_FOLDER = "training_plots"  # Folder to save plots to
PLOT_SAVE_FREQUENCY = 10             # Save every N episodes (set to 1 to save every episode)

WIDTH = 10
HEIGHT = 10

episode = 0

lrScheduler = keras.callbacks.ReduceLROnPlateau(
    monitor='loss',
    factor=0.5,
    patience=5,
    min_lr=1e-6,
    verbose=1
)

replayBuffer = deque(maxlen=MEMORY_SIZE)


# =============================================================================
# GAME WRAPPER
# =============================================================================

class SnakeEnv():
    def __init__(self):
        self.env = snake_env.Neural(WIDTH, HEIGHT)

    def reset(self):
        state = self.env.reset()
        return np.array(state.board, dtype=np.float32)

    def step(self, action):
        state = self.env.step(action)
        return np.array(state.ob.board, dtype=np.float32), state.reward, state.done


# =============================================================================
# NEURAL NETWORK
# =============================================================================

def build_model(inputShape, neuronCount, hiddenLayers, outputShape):
    model = models.Sequential()
    model.add(layers.Input(shape=(inputShape,)))
    for i in range(hiddenLayers):
        model.add(layers.Dense(neuronCount, activation='relu'))
        if neuronCount > 4:
            neuronCount = neuronCount // 2
    model.add(layers.Dense(outputShape))
    return model


if not LOAD_MODEL:
    model = build_model(11, 128, 3, 3)
    model.compile(
        optimizer=optimizers.Adam(learning_rate=LEARNING_RATE, clipnorm=1.0),
        loss=keras.losses.Huber(delta=1.0)
    )
    model.summary()
else:
    try:
        model = keras.models.load_model(LOAD_MODEL_PATH)
        print(f"Model loaded from {LOAD_MODEL_PATH}")
        model.summary()
    except Exception as e:
        print(f"Failed to load model from {LOAD_MODEL_PATH}: {e}")
        raise


# =============================================================================
# EXPERIENCE COLLECTION
# =============================================================================

def collectExperience(batch):
    env = SnakeEnv()
    localModel = keras.models.clone_model(model)
    localModel.set_weights(model.get_weights())
    state = env.reset()
    totalReward = 0
    localExperiences = deque(maxlen=batch)
    doneReset = False
    steps = 0

    for i in range(batch):
        if np.random.rand() < EPSILON:
            action = np.random.randint(0, 3)
        else:
            # Reshape state to (1, 11) for prediction
            qValues = model.predict(state.reshape(1, -1), verbose=0)
            action = np.argmax(qValues)

        if doneReset:
            steps = 0
            doneReset = False

        steps += 1
        if steps % 10 == 0:
            totalReward -= 1

        nextState, reward, done = env.step(action)
        if done:
            reward -= 5

        localExperiences.append((state, action, reward, nextState, done))
        totalReward += reward
        state = nextState

        if done:
            doneReset = True
            state = env.reset()

    return localExperiences, totalReward


def getExperiences(batch):
    experiences, totalReward = collectExperience(batch)
    for exp in experiences:
        replayBuffer.append(exp)
    return totalReward


# =============================================================================
# VISUALIZATION
# =============================================================================

# Global variable to maintain a single plot window
_plot_figure = None

def plot_training_statistics(episode, episodeRewards, episodeLosses, epsilon, replayBufferSize,
                            windowSize=30, figsize=(15, 10)):
    """Plot comprehensive training statistics for DQN training in a single persistent window."""
    global _plot_figure

    # Create figure only once and reuse it
    if _plot_figure is None:
        plt.ion()  # Turn on interactive mode
        _plot_figure = plt.figure(figsize=figsize)
        plt.show(block=False)

    # Clear the current figure content
    _plot_figure.clear()

    gs = _plot_figure.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. Episode Rewards (Raw)
    ax1 = _plot_figure.add_subplot(gs[0, 0])
    if len(episodeRewards) > 0:
        ax1.plot(episodeRewards, alpha=0.8, color='dodgerblue', linewidth=2)
        ax1.set_title('Episode Rewards (Raw)', fontsize=13, fontweight='bold')
        ax1.set_xlabel('Episode', fontsize=11)
        ax1.set_ylabel('Total Reward', fontsize=11)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    else:
        ax1.text(0.5, 0.5, 'Waiting for data...', ha='center', va='center',
                transform=ax1.transAxes, fontsize=12)
        ax1.set_title('Episode Rewards (Raw)', fontsize=13, fontweight='bold')

    # 2. Moving Average Rewards
    ax2 = _plot_figure.add_subplot(gs[0, 1])
    if len(episodeRewards) >= windowSize:
        movingAvg = pd.Series(episodeRewards).rolling(window=windowSize).mean()
        ax2.plot(movingAvg, color='darkblue', linewidth=3)
        ax2.fill_between(range(len(movingAvg)), movingAvg, alpha=0.3, color='blue')
        ax2.set_title(f'Moving Average Rewards (window={windowSize})', fontsize=13, fontweight='bold')
        ax2.set_xlabel('Episode', fontsize=11)
        ax2.set_ylabel('Average Reward', fontsize=11)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    else:
        ax2.text(0.5, 0.5, f'Need {windowSize} episodes\nfor moving average\n({len(episodeRewards)}/{windowSize})',
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title(f'Moving Average Rewards (window={windowSize})', fontsize=13, fontweight='bold')

    # 3. Training Loss
    ax3 = _plot_figure.add_subplot(gs[1, 0])
    if len(episodeLosses) > 0:
        ax3.plot(episodeLosses, color='darkorange', linewidth=2.5)
        ax3.set_title('Training Loss per Episode', fontsize=13, fontweight='bold')
        ax3.set_xlabel('Episode', fontsize=11)
        ax3.set_ylabel('Loss', fontsize=11)
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.set_yscale('log')
    else:
        ax3.text(0.5, 0.5, 'Waiting for training...', ha='center', va='center',
                transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Training Loss per Episode', fontsize=13, fontweight='bold')

    # 4. Epsilon Decay
    ax4 = _plot_figure.add_subplot(gs[1, 1])
    epsilonHistory = [EPSILON * (EPSILON_DECAY ** i) for i in range(episode + 1)]
    epsilonHistory = [max(MIN_EPSILON, e) for e in epsilonHistory]
    ax4.plot(epsilonHistory, color='forestgreen', linewidth=3)
    ax4.set_title('Exploration Rate (Epsilon)', fontsize=13, fontweight='bold')
    ax4.set_xlabel('Episode', fontsize=11)
    ax4.set_ylabel('Epsilon', fontsize=11)
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_ylim([-0.05, 1.05])

    # 5. Reward Distribution (Histogram)
    ax5 = _plot_figure.add_subplot(gs[2, 0])
    if len(episodeRewards) > 0:
        ax5.hist(episodeRewards, bins=30, color='mediumpurple', alpha=0.7, edgecolor='black', linewidth=1.2)
        ax5.axvline(np.mean(episodeRewards), color='red', linestyle='--',
                   linewidth=3, label=f'Mean: {np.mean(episodeRewards):.2f}')
        ax5.set_title('Reward Distribution', fontsize=13, fontweight='bold')
        ax5.set_xlabel('Reward', fontsize=11)
        ax5.set_ylabel('Frequency', fontsize=11)
        ax5.legend(fontsize=10)
        ax5.grid(True, alpha=0.3, linestyle='--')
    else:
        ax5.text(0.5, 0.5, 'Waiting for data...', ha='center', va='center',
                transform=ax5.transAxes, fontsize=12)
        ax5.set_title('Reward Distribution', fontsize=13, fontweight='bold')

    # 6. Statistics Summary (Text)
    ax6 = _plot_figure.add_subplot(gs[2, 1])
    ax6.axis('off')

    if len(episodeRewards) > 0:
        latestLoss = episodeLosses[-1] if episodeLosses else 0
        meanLoss = np.mean(episodeLosses) if episodeLosses else 0

        statsText = f"""
        TRAINING STATISTICS
        {'='*40}

        Current Episode: {episode + 1}

        REWARDS:
        • Latest Reward: {episodeRewards[-1]:.2f}
        • Mean Reward: {np.mean(episodeRewards):.2f}
        • Max Reward: {np.max(episodeRewards):.2f}
        • Min Reward: {np.min(episodeRewards):.2f}

        LOSS:
        • Latest Loss: {latestLoss:.6f}
        • Mean Loss: {meanLoss:.6f}

        EXPLORATION:
        • Current Epsilon: {epsilon:.4f}
        • Decay Rate: {EPSILON_DECAY}

        MEMORY:
        • Replay Buffer: {replayBufferSize}/{MEMORY_SIZE}
        • Buffer Usage: {(replayBufferSize/MEMORY_SIZE)*100:.1f}%
        """
        ax6.text(0.1, 0.5, statsText, fontsize=11, family='monospace',
                verticalalignment='center', transform=ax6.transAxes)

    _plot_figure.suptitle(f'DQN Training Progress - Episode {episode + 1}',
                         fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()

    # Save plots based on configuration
    if SAVE_PLOTS and (episode + 1) % PLOT_SAVE_FREQUENCY == 0:
        # Create save directory if it doesn't exist
        os.makedirs(PLOT_SAVE_FOLDER, exist_ok=True)

        # Save with episode number
        save_path = os.path.join(PLOT_SAVE_FOLDER, f'training_progress_episode_{episode + 1}.png')
        _plot_figure.savefig(save_path, dpi=100, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    # Update the display
    _plot_figure.canvas.draw()
    _plot_figure.canvas.flush_events()
    plt.pause(0.001)

    return _plot_figure


def close_plot_window():
    """Close the persistent plot window."""
    global _plot_figure
    if _plot_figure is not None:
        plt.close(_plot_figure)
        _plot_figure = None
        print("Plot window closed.")


# =============================================================================
# TRAINING LOOP
# =============================================================================

def train():
    global EPSILON

    episodeRewards = []
    episodeLosses = []

    targetModel = keras.models.clone_model(model)
    targetModel.set_weights(model.get_weights())

    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)

    for episode in range(EPOCHS):
        epRewards = getExperiences(BATCH_SIZE)
        episode += 1
        epLosses = []

        if len(replayBuffer) >= TRAINING_THRESHOLD:
            for _ in range(TRAINING_STEPS):
                minibatch = random.sample(list(replayBuffer), min(BATCH_SIZE, len(replayBuffer)))

                initialStates = np.array([exp[0] for exp in minibatch], dtype=np.float32)
                nextStates = np.array([exp[3] for exp in minibatch], dtype=np.float32)

                targetQ = model.predict(initialStates, verbose=0)
                nextQO = model.predict(nextStates, verbose=0)
                nextQ = targetModel.predict(nextStates, verbose=0)

                for i, (state, action, reward, nextState, done) in enumerate(minibatch):
                    if done:
                        targetQ[i][action] = reward
                    else:
                        nextAction = np.argmax(nextQO[i])
                        targetQ[i][action] = reward + GAMMA * nextQ[i][nextAction]

                history = model.fit(initialStates, targetQ, epochs=1, verbose=0, callbacks=[lrScheduler])
                epLosses.append(history.history['loss'][0])

            EPSILON = max(MIN_EPSILON, EPSILON * EPSILON_DECAY)

            episodeRewards.append(epRewards)
            if epLosses:
                episodeLosses.append(np.mean(epLosses))

            avgReward = np.mean(episodeRewards[-30:]) if len(episodeRewards) >= 30 else np.mean(episodeRewards)
            avgLoss = np.mean(epLosses) if epLosses else 0

            # Clear screen (works on both Linux and Windows)
            os.system('clear' if os.name == 'posix' else 'cls')

            print(f"Episode {episode + 1} Summary:")
            print(f"  Reward: {epRewards:.2f}")
            print(f"  Avg Reward (last 30): {avgReward:.2f}")
            print(f"  Avg Loss: {avgLoss:.6f}")
            print(f"  Epsilon: {EPSILON:.3f}")
            print(f"  Replay Buffer: {len(replayBuffer)}/{replayBuffer.maxlen}")

            plot_training_statistics(episode, episodeRewards, episodeLosses, EPSILON, len(replayBuffer))

            if episode % TARGET_UPDATE_FREQ == 0:
                targetModel.set_weights(model.get_weights())
                print(f"Target model updated at episode {episode}")

            if episode % 20 == 0:
                model.save(f"models/dqn_model_episode_{episode}.keras")
                print(f"Model saved at episode {episode}")

    print("\n" + "="*60)
    print("TRAINING COMPLETED")
    print("="*60)
    print(f"Final Epsilon: {EPSILON:.3f}")
    print(f"Total Episodes: {len(episodeRewards)}")
    print(f"Average Reward: {np.mean(episodeRewards):.2f}")
    close_plot_window()
    print("="*60)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Starting DQN Training for Snake Game")
    print("="*60)
    print(f"Configuration:")
    print(f"  Learning Rate: {LEARNING_RATE}")
    print(f"  Batch Size: {BATCH_SIZE}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Memory Size: {MEMORY_SIZE}")
    print(f"  Initial Epsilon: {EPSILON}")
    print(f"  Epsilon Decay: {EPSILON_DECAY}")
    print(f"  Min Epsilon: {MIN_EPSILON}")
    print(f"  Gamma: {GAMMA}")
    print(f"  Grid Size: {WIDTH}x{HEIGHT}")
    print("="*60)

    try:
        train()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
        print(f"Current epsilon: {EPSILON:.3f}")
        print(f"Replay buffer size: {len(replayBuffer)}")
        print("Saving model...")
        model.save("models/dqn_model_interrupted.keras")
        print("Model saved as 'dqn_model_interrupted.keras'")
        close_plot_window()
    except Exception as e:
        print(f"\n\nError during training: {e}")
        import traceback
        traceback.print_exc()
        print("Attempting to save model...")
        try:
            model.save("models/dqn_model_error.keras")
            print("Model saved as 'dqn_model_error.keras'")
        except:
            print("Failed to save model")
        close_plot_window()
