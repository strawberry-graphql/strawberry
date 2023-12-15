
from hashlib import sha256


def hash256(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()

def is_valid_hash256(text: str) -> bool:
    return len(text) == 64
