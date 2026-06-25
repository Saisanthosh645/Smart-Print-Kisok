import secrets
import uuid


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def generate_collection_code() -> str:
    return uuid.uuid4().hex[:8].upper()
