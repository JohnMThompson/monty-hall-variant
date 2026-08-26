import contextlib
import io
import unittest
from pathlib import Path

from monty_hall import (
    CAR,
    ORDINARY_GOAT,
    SPECIAL_MODE,
    TRADITIONAL_MODE,
    VALUABLE_GOAT,
    build_parser,
    load_strategy,
    print_summary,
    simulate,
    validate_inputs,
)


class MontyHallTests(unittest.TestCase):
    def test_seed_makes_results_reproducible(self) -> None:
        first = simulate(SPECIAL_MODE, 200, 0.4, seed=123)
        second = simulate(SPECIAL_MODE, 200, 0.4, seed=123)
        self.assertEqual(first, second)

    def test_strategy_file_lists_rules_for_every_possible_reveal(self) -> None:
        strategy = load_strategy(Path(__file__).with_name("strategy.ini"))
        self.assertEqual(set(strategy[TRADITIONAL_MODE]), {ORDINARY_GOAT})
        self.assertEqual(set(strategy[SPECIAL_MODE]), {ORDINARY_GOAT, VALUABLE_GOAT})
        for rules in strategy.values():
            self.assertTrue(set(rules.values()).issubset({"stay", "switch", "random"}))

    def test_never_switch_records_only_stays(self) -> None:
        summary = simulate(TRADITIONAL_MODE, 100, 0, seed=5)
        self.assertEqual(summary.actions["stay"], 100)
        self.assertEqual(summary.actions["switch"], 0)

    def test_always_switch_wins_about_two_thirds_of_traditional_games(self) -> None:
        summary = simulate(TRADITIONAL_MODE, 50_000, 1, seed=9)
        car_win_rate = summary.final_prizes[CAR] / summary.trials
        self.assertEqual(summary.actions["switch"], summary.trials)
        self.assertGreater(car_win_rate, 0.64)
        self.assertLess(car_win_rate, 0.69)

    def test_special_mode_tracks_every_prize_and_reveal_type(self) -> None:
        summary = simulate(SPECIAL_MODE, 1_000, 0.5, seed=12)
        self.assertEqual(sum(summary.final_prizes.values()), summary.trials)
        self.assertEqual(sum(summary.reveals.values()), summary.trials)
        self.assertEqual(
            sum(sum(outcomes.values()) for outcomes in summary.outcomes_by_action.values()),
            summary.trials,
        )
        self.assertGreater(summary.final_prizes[VALUABLE_GOAT], 0)
        self.assertGreater(summary.final_prizes[CAR], 0)
        self.assertGreater(summary.final_prizes[ORDINARY_GOAT], 0)
        self.assertGreater(summary.reveals[ORDINARY_GOAT], 0)
        self.assertGreater(summary.reveals[VALUABLE_GOAT], 0)
        self.assertLessEqual(
            summary.final_prizes[VALUABLE_GOAT], summary.reveals[ORDINARY_GOAT]
        )

    def test_conditional_strategy_stays_for_ordinary_reveals_and_switches_for_valuable(self) -> None:
        summary = simulate(SPECIAL_MODE, 1_000, 0.5, seed=12)
        ordinary_stays = sum(
            summary.ordinary_reveal_outcomes_by_action["stay"].values()
        )
        ordinary_switches = sum(
            summary.ordinary_reveal_outcomes_by_action["switch"].values()
        )
        self.assertEqual(ordinary_stays, summary.reveals[ORDINARY_GOAT])
        self.assertEqual(ordinary_switches, 0)
        self.assertEqual(summary.actions["stay"], summary.reveals[ORDINARY_GOAT])
        self.assertEqual(summary.actions["switch"], summary.reveals[VALUABLE_GOAT])

    def test_special_mode_switching_wins_valuable_goat_one_third_of_ordinary_reveals(self) -> None:
        random_special_strategy = {
            TRADITIONAL_MODE: {ORDINARY_GOAT: "random"},
            SPECIAL_MODE: {ORDINARY_GOAT: "random", VALUABLE_GOAT: "random"},
        }
        summary = simulate(SPECIAL_MODE, 50_000, 1, seed=7, strategy=random_special_strategy)
        switch_outcomes = summary.ordinary_reveal_outcomes_by_action["switch"]
        conditional_rate = switch_outcomes[VALUABLE_GOAT] / sum(switch_outcomes.values())
        self.assertGreater(conditional_rate, 0.30)
        self.assertLess(conditional_rate, 0.36)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_inputs("other", 1, 0.5)
        with self.assertRaises(ValueError):
            validate_inputs(TRADITIONAL_MODE, 0, 0.5)
        with self.assertRaises(ValueError):
            validate_inputs(TRADITIONAL_MODE, 1, 1.1)

    def test_cli_rejects_invalid_trial_count_and_probability(self) -> None:
        parser = build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["--trials", "0"])
            with self.assertRaises(SystemExit):
                parser.parse_args(["--switch-probability", "1.1"])

    def test_summary_contains_numeric_metrics(self) -> None:
        strategy = load_strategy(Path(__file__).with_name("strategy.ini"))
        summary = simulate(TRADITIONAL_MODE, 10, 0.5, seed=1, strategy=strategy)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            print_summary(summary, TRADITIONAL_MODE, 0.5, 1, strategy)
        report = output.getvalue()
        self.assertNotIn("█", report)
        self.assertIn("Final selection", report)
        self.assertNotIn("Monty's reveal", report)
        self.assertIn("%", report)


if __name__ == "__main__":
    unittest.main()
