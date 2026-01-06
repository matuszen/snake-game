import json
import sys
from pathlib import Path

sys.path.insert(0, '.')
from py.training.neural import Neural


def save_network(network: Neural, filepath: str) -> None:
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    data = {
        'input_size': len(network.inputs),
        'hidden_size': len(network.hidden),
        'output_size': len(network.outputs),
        'weight_range': network.weight_range,
        'hidden_weights': network.hidden_weights,
        'output_weights': network.output_weights,
    }

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    #print(f"✓ Saved network to {filepath}", flush=True)


def load_network(filepath: str) -> Neural:
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        network = Neural(
            data['input_size'],
            data['hidden_size'],
            data['output_size'],
            data['weight_range']
        )

        network.hidden_weights = data['hidden_weights']
        network.output_weights = data['output_weights']

        print(f"✓ Loaded network from {filepath}", flush=True)
        return network

    except FileNotFoundError:
        print(f"✗ Network file not found: {filepath}", flush=True)
        return None
    except Exception as e:
        print(f"✗ Error loading network: {e}", flush=True)
        return None
