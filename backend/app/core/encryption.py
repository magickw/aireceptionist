"""
Credential encryption service using Fernet (AES-128-CBC + HMAC-SHA256).

Key is derived from ENCRYPTION_KEY env var (falls back to SECRET_KEY) using PBKDF2.
Encrypted values are stored as {"_encrypted": "<fernet_token>"} in JSON columns
for backward compatibility with existing plaintext data.
"""

import json
import base64
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)

# Static salt - changing this invalidates all encrypted data
_SALT = b"aireceptionist-credential-encryption-v1"


class EncryptionService:
    """Encrypts and decrypts credential data using Fernet symmetric encryption."""

    def __init__(self):
        key_source = settings.ENCRYPTION_KEY or settings.SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_SALT,
            iterations=480_000,
        )
        derived = kdf.derive(key_source.encode("utf-8"))
        fernet_key = base64.urlsafe_b64encode(derived)
        self._fernet = Fernet(fernet_key)

    def encrypt_json(self, data: Any) -> dict:
        """Encrypt a JSON-serializable value. Returns {"_encrypted": "<token>"}."""
        plaintext = json.dumps(data).encode("utf-8")
        token = self._fernet.encrypt(plaintext).decode("ascii")
        return {"_encrypted": token}

    def decrypt_json(self, wrapper: dict) -> Any:
        """Decrypt a {"_encrypted": "<token>"} wrapper back to the original value."""
        token = wrapper["_encrypted"].encode("ascii")
        plaintext = self._fernet.decrypt(token)
        return json.loads(plaintext)

    def is_encrypted(self, value: Any) -> bool:
        """Check if a value is an encrypted wrapper."""
        if not isinstance(value, dict):
            return False
        encrypted = value.get("_encrypted")
        if not isinstance(encrypted, str):
            return False
        # Fernet tokens start with 'gAAAAA'
        return encrypted.startswith("gAAAAA")

    def encrypt_if_needed(self, data: Any) -> Any:
        """Encrypt data only if it's not already encrypted."""
        if data is None:
            return data
        if self.is_encrypted(data):
            return data
        return self.encrypt_json(data)

    def decrypt_if_needed(self, data: Any) -> Any:
        """Decrypt data only if it's encrypted; return plaintext as-is."""
        if data is None:
            return data
        if self.is_encrypted(data):
            try:
                return self.decrypt_json(data)
            except (InvalidToken, KeyError, json.JSONDecodeError):
                logger.error("Failed to decrypt credential data - key may have changed")
                return data
        return data


encryption_service = EncryptionService()
