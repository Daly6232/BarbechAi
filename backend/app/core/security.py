import secrets
import uuid


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_token(length: int = 32) -> str:
    return secrets.token_hex(length)


def safe_compare(value1: str, value2: str) -> bool:
    return secrets.compare_digest(value1, value2)
