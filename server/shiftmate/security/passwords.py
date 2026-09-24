import argon2

_hasher = argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(hash_val: str, password: str) -> bool:
    try:
        return _hasher.verify(hash_val, password)
    except (argon2.exceptions.VerificationError, argon2.exceptions.InvalidHashError):
        return False
