import random
import string

random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
print(f"Hello, world! {random_text}")
