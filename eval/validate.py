"""Sealed-worker adapter: same evaluator, bars, features and fills as development."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--data', required=True)
    parser.add_argument('--symbols', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    symbols = json.loads(args.symbols)
    if not isinstance(symbols, list) or not symbols or not all(isinstance(s, str) for s in symbols):
        raise ValueError('symbols must be nonempty JSON list')
    sys.argv = ['sim.py', '--strategy', args.candidate, '--data', args.data,
                '--output', args.output, '--null-seeds', '200', '--symbols', *symbols]
    sim.main()


if __name__ == '__main__':
    main()
