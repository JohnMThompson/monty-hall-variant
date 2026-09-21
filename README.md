# Monty Hall Simulator

Some friends and I were discussing a Monty Hall problem variant in which one goat is secretly worth more than the car, but Monty only knows where the car is. He opens an unselected non-car door at random, so he may reveal either the ordinary or valuable goat. The contestant can identify which goat was revealed and then decides whether to stay or switch.

To test the different strategies, I built this Python project.

## How to play

Edit [strategy.ini](strategy.ini) to choose what the player does after each possible reveal. Each setting accepts `stay`, `switch`, or `random`; the latter uses `--switch-probability`.

The included strategy always switches in traditional mode. In special mode, it stays after the ordinary-goat reveal and switches after the valuable-goat reveal.

Run the traditional game (the default is 10,000 trials and the behavior comes from `strategy.ini`):

```bash
python3 monty_hall.py
```

Run the special-goat scenario reproducibly:

```bash
python3 monty_hall.py --mode special --trials 100000 --seed 42
```

Pass `--strategy-file path/to/strategy.ini` to use a different strategy file.

Metrics are displayed as numeric counts and percentages.

Run the tests:

```bash
python3 -m unittest -v
```

🦆
