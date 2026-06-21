import base64
import hashlib
from app.settings.config import settings


def _key_bytes() -> bytes:
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()


def encrypt_api_key(plain: str) -> str:
    key = _key_bytes()
    return base64.urlsafe_b64encode(
        bytes(p ^ key[i % len(key)] for i, p in enumerate(plain.encode("utf-8")))
    ).decode()


def decrypt_api_key(encrypted: str) -> str:
    key = _key_bytes()
    return bytes(
        e ^ key[i % len(key)]
        for i, e in enumerate(base64.urlsafe_b64decode(encrypted.encode()))
    ).decode("utf-8")
