"""Generate Fibonacci numbers.

Running this module as a script prints a random Fibonacci number for an index in
[0, 20].
"""
from __future__ import annotations

import random
from functools import lru_cache


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
    index = random.randint(0, 20)
    print(f"Fibonacci number F({index}) = {fibonacci(index)}")


if __name__ == "__main__":
    main()
