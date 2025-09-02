"""Generate Fibonacci numbers.

Running this module as a script prints a random set of jokes followed by a
random Fibonacci number for an index in [0, 20].
"""
from __future__ import annotations

import random
from functools import lru_cache


JOKES = (
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "Why did the developer go broke? Because they used up all their cache!",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
    "Why do Java developers wear glasses? Because they don't C#.",
    "I would tell you a UDP joke, but you might not get it.",
)


def _choose_jokes() -> list[str]:
    """Return a random selection of jokes."""

    number_of_jokes = random.randint(1, min(3, len(JOKES)))
    return random.sample(JOKES, k=number_of_jokes)


@lru_cache(maxsize=None)
def fibonacci(n: int) -> int:
    """Return the *n*th Fibonacci number.

    The sequence is defined by ``F(0) = 0`` and ``F(1) = 1``.
    ``F(n)`` for ``n >= 2`` is the sum of the two preceding numbers.

    Args:
        n: The index of the Fibonacci number to compute. Must be non-negative.

    Returns:
        The ``n``th Fibonacci number.

    Raises:
        ValueError: If ``n`` is negative.
    """
    if n < 0:
        raise ValueError("Fibonacci numbers are only defined for non-negative integers")
    if n in (0, 1):
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def main() -> None:
    for joke in _choose_jokes():
        print(joke)

    index = random.randint(0, 20)
    print(f"Fibonacci number F({index}) = {fibonacci(index)}")


if __name__ == "__main__":
    main()
