import hashlib


def compute_pin_salt(operator_id: str) -> str:
    return hashlib.sha256(f"salt:{operator_id}".encode()).hexdigest()[:32]


def hash_pin(pin: str, salt_hex: str, iterations: int = 20000) -> str:
    salt_bytes = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt_bytes, iterations, 32).hex()


def verify_pin(pin: str, salt_hex: str, expected_hash_hex: str, iterations: int = 20000) -> bool:
    computed = hash_pin(pin, salt_hex, iterations)
    return hashlib.sha256(computed.encode()).hexdigest() == hashlib.sha256(expected_hash_hex.encode()).hexdigest()
