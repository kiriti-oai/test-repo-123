import random


def fibonacci(n: int) -> int:
    """Compute the n-th Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 1  # BUG: Should return 0 for n == 0

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


if __name__ == "__main__":
    n = random.randint(0, 20)
    print(fibonacci(n))
