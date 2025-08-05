import random
import string


def main() -> None:
    print("hello world")
    random_text = ''.join(random.choice(string.ascii_letters) for _ in range(10))
    print(random_text)


if __name__ == "__main__":
    main()
