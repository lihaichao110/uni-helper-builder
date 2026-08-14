import base64
import hashlib
import os
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str, expected_type: str) -> str:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise jwt.InvalidTokenError("invalid token type")
    return str(payload["sub"])


def create_access_token(user_id: str) -> str:
    return create_token(user_id, "access", timedelta(minutes=get_settings().access_token_minutes))


def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, "refresh", timedelta(days=get_settings().refresh_token_days))


def _encryption_key() -> bytes:
    raw = get_settings().credential_encryption_key.encode()
    try:
        decoded = base64.urlsafe_b64decode(raw)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    return hashlib.sha256(raw).digest()


def encrypt_secret(secret: str) -> str:
    nonce = os.urandom(12)
    encrypted = AESGCM(_encryption_key()).encrypt(nonce, secret.encode(), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode()


def decrypt_secret(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    return AESGCM(_encryption_key()).decrypt(raw[:12], raw[12:], None).decode()
