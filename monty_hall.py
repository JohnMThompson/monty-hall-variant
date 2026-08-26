#!/usr/bin/env python3
"""Simulate the traditional and special-goat versions of Monty Hall."""

from __future__ import annotations

import argparse
import configparser
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DOORS = (0, 1, 2)
TRADITIONAL_MODE = "traditional"
SPECIAL_MODE = "special"
CAR = "car"
ORDINARY_GOAT = "ordinary goat"
VALUABLE_GOAT = "valuable goat"
STAY = "stay"
SWITCH = "switch"
RANDOM = "random"
VALID_DECISIONS = {STAY, SWITCH, RANDOM}
DEFAULT_STRATEGY = {
    TRADITIONAL_MODE: {ORDINARY_GOAT: RANDOM},
    SPECIAL_MODE: {ORDINARY_GOAT: STAY, VALUABLE_GOAT: SWITCH},
}


@dataclass
class SimulationSummary:
    """Counts collected from a series of simulated games."""

    trials: int
    actions: Counter[str]
    final_prizes: Counter[str]
    reveals: Counter[str]
    outcomes_by_action: dict[str, Counter[str]]
    ordinary_reveal_outcomes_by_action: dict[str, Counter[str]]


def validate_inputs(mode: str, trials: int, switch_probability: float) -> None:
    """Raise ValueError when simulation inputs are outside the supported range."""
    if mode not in {TRADITIONAL_MODE, SPECIAL_MODE}:
        raise ValueError(f"Unsupported mode: {mode!r}")
    if trials <= 0:
        raise ValueError("trials must be a positive integer")
    if not 0 <= switch_probability <= 1:
        raise ValueError("switch probability must be between 0 and 1")


def load_strategy(file_path: str | Path) -> dict[str, dict[str, str]]:
    """Load and validate a user-editable INI strategy file."""
    parser = configparser.ConfigParser()
    loaded_files = parser.read(file_path)
    if not loaded_files:
        raise ValueError(f"Strategy file not found: {file_path}")

    strategy: dict[str, dict[str, str]] = {}
    for mode, reveal_types in DEFAULT_STRATEGY.items():
        if mode not in parser:
            raise ValueError(f"Strategy file is missing the [{mode}] section")
        strategy[mode] = {}
        for revealed_prize in reveal_types:
            key = revealed_prize.replace(" ", "_") + "_revealed"
            if key not in parser[mode]:
                raise ValueError(f"Strategy file is missing [{mode}] {key}")
            decision = parser[mode][key].strip().lower()
            if decision not in VALID_DECISIONS:
                choices = ", ".join(sorted(VALID_DECISIONS))
                raise ValueError(
                    f"[{mode}] {key} must be one of: {choices}; got {decision!r}"
                )
            strategy[mode][revealed_prize] = decision
    return strategy


def simulate(
    mode: str,
    trials: int,
    switch_probability: float,
    seed: int | None = None,
    strategy: dict[str, dict[str, str]] | None = None,
) -> SimulationSummary:
    """Run games and return their aggregate outcomes.

    In special mode Monty knows the car location but not which goat is valuable.
    He therefore chooses uniformly from the eligible non-car doors.
    """
    validate_inputs(mode, trials, switch_probability)
    if strategy is None:
        strategy = DEFAULT_STRATEGY
    rng = random.Random(seed)
    actions: Counter[str] = Counter()
    final_prizes: Counter[str] = Counter()
    reveals: Counter[str] = Counter()
    outcomes_by_action = {"stay": Counter(), "switch": Counter()}
    ordinary_reveal_outcomes_by_action = {"stay": Counter(), "switch": Counter()}

    for _ in range(trials):
        selected_door = rng.choice(DOORS)

        if mode == TRADITIONAL_MODE:
            prizes = {door: ORDINARY_GOAT for door in DOORS}
            prizes[rng.choice(DOORS)] = CAR
        else:
            shuffled_prizes = rng.sample([CAR, ORDINARY_GOAT, VALUABLE_GOAT], k=3)
            prizes = dict(zip(DOORS, shuffled_prizes))

        eligible_reveals = [
            door
            for door in DOORS
            if door != selected_door and prizes[door] != CAR
        ]
        revealed_door = rng.choice(eligible_reveals)
        revealed_prize = prizes[revealed_door]
        reveals[revealed_prize] += 1

        decision = strategy[mode][revealed_prize]
        if decision == RANDOM:
            should_switch = rng.random() < switch_probability
        else:
            should_switch = decision == SWITCH
        action = "switch" if should_switch else "stay"
        actions[action] += 1

        if should_switch:
            final_door = next(
                door for door in DOORS if door not in {selected_door, revealed_door}
            )
        else:
            final_door = selected_door
        final_prize = prizes[final_door]
        final_prizes[final_prize] += 1
        outcomes_by_action[action][final_prize] += 1
        if mode == SPECIAL_MODE and revealed_prize == ORDINARY_GOAT:
            ordinary_reveal_outcomes_by_action[action][final_prize] += 1

    return SimulationSummary(
        trials=trials,
        actions=actions,
        final_prizes=final_prizes,
        reveals=reveals,
        outcomes_by_action=outcomes_by_action,
        ordinary_reveal_outcomes_by_action=ordinary_reveal_outcomes_by_action,
    )


def percentage(count: int, total: int) -> str:
    """Format a count as a percentage, handling an empty subset."""
    return "n/a" if total == 0 else f"{count / total:.2%}"


def print_metric(label: str, count: int, total: int, indent: str = "  ") -> None:
    """Print one numeric metric with its count and percentage."""
    print(f"{indent}{label:<16} {count:>8,} ({percentage(count, total)})")


def print_summary(
    summary: SimulationSummary,
    mode: str,
    switch_probability: float,
    seed: int | None,
    strategy: dict[str, dict[str, str]],
) -> None:
    """Print a compact, human-readable simulation report."""
    print(f"Monty Hall simulation: {mode} mode")
    print(f"Trials: {summary.trials:,}")
    print("Strategy")
    for revealed_prize, decision in strategy[mode].items():
        print(f"  After {revealed_prize} reveal: {decision}")
    if RANDOM in strategy[mode].values():
        print(f"Random switch probability: {switch_probability:.2%}")
    if seed is not None:
        print(f"Seed: {seed}")

    print("\nPlayer actions")
    for action in ("stay", "switch"):
        print_metric(action.title(), summary.actions[action], summary.trials)

    print("\nFinal selection")
    prize_order = (CAR, ORDINARY_GOAT) if mode == TRADITIONAL_MODE else (
        VALUABLE_GOAT,
        CAR,
        ORDINARY_GOAT,
    )
    for prize in prize_order:
        print_metric(prize.title(), summary.final_prizes[prize], summary.trials)



def positive_integer(value: str) -> int:
    """argparse validator for a positive whole number."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def probability(value: str) -> float:
    """argparse validator for a probability in the inclusive 0--1 range."""
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a number from 0 to 1") from error
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("must be a number from 0 to 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=(TRADITIONAL_MODE, SPECIAL_MODE),
        default=TRADITIONAL_MODE,
        help="simulation rules to use (default: traditional)",
    )
    parser.add_argument(
        "--trials",
        type=positive_integer,
        default=10_000,
        help="number of games to simulate (default: 10000)",
    )
    parser.add_argument(
        "--switch-probability",
        type=probability,
        default=0.5,
        help="chance the player switches after Monty's reveal, from 0 to 1 (default: 0.5)",
    )
    parser.add_argument(
        "--strategy-file",
        default="strategy.ini",
        help="INI file containing post-reveal choices (default: strategy.ini)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="optional random seed for reproducible results",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(arguments)
    try:
        strategy = load_strategy(args.strategy_file)
    except ValueError as error:
        build_parser().error(str(error))
    summary = simulate(
        args.mode,
        args.trials,
        args.switch_probability,
        args.seed,
        strategy,
    )
    print_summary(
        summary,
        args.mode,
        args.switch_probability,
        args.seed,
        strategy,
    )


if __name__ == "__main__":
    main()
