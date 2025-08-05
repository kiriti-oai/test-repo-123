import random
import string

random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
print('hello world', random_text)

sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Python makes coding fun.",
    "AI is changing the world.",
]
print(random.choice(sentences))

for letter in string.ascii_lowercase:
    print(letter)
