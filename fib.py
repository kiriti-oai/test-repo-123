"""Generate and display a random Fibonacci number.

The module chooses a random index between 0 and 20 (inclusive) and prints the
Fibonacci number at that position.
"""
from __future__ import annotations

import random
from typing import Final

_MAX_INDEX: Final[int] = 20


def fibonacci(index: int) -> int:
    """Return the Fibonacci number at the given ``index``.

    The implementation intentionally uses an iterative algorithm for clarity.
    """
    if index < 0:
        raise ValueError("Fibonacci index must be non-negative")

    previous, current = 0, 1
    for _ in range(index):
        previous, current = current, previous + current
    return current


def main() -> None:
    index = random.randint(0, _MAX_INDEX)
    value = fibonacci(index)
    print(f"F({index}) = {value}")


if __name__ == "__main__":
    main()
