import random

def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def main() -> None:
    n = random.randint(0, 10)
    print(f"Index: {n}")
    print(f"Fibonacci number: {fibonacci(n)}")


if __name__ == "__main__":
    main()
