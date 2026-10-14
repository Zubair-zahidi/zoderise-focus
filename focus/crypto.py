"""Password backup envelopes: scrypt-derived AES-256-GCM, never stored passwords."""
import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"ZFOCUS-ENCRYPTED-1\n"
AAD = b"Zoderise Focus backup v1; AES-256-GCM; scrypt n=32768 r=8 p=1"


def key(password, salt):
    if not isinstance(password, str) or not 12 <= len(password) <= 256:
        raise ValueError("Use a backup password with 12–256 characters.")
    return Scrypt(salt=salt, length=32, n=32768, r=8, p=1).derive(password.encode("utf-8"))


def encrypt_backup(blob, password):
    if len(blob) > 20_000_000:
        raise ValueError("Backup exceeds 20 MB.")
    salt, nonce = os.urandom(32), os.urandom(12)
    cipher = AESGCM(key(password, salt)).encrypt(nonce, blob, AAD)
    return MAGIC + json.dumps({"salt": base64.b64encode(salt).decode(), "nonce": base64.b64encode(nonce).decode(),
                              "ciphertext": base64.b64encode(cipher).decode()}, separators=(",", ":")).encode()


def decrypt_backup(blob, password):
    if not blob.startswith(MAGIC) or len(blob) > 28_000_000:
        raise ValueError("Unsupported encrypted backup or size.")
    try:
        values = json.loads(blob[len(MAGIC):])
        if set(values) != {"salt", "nonce", "ciphertext"}:
            raise ValueError("Invalid encrypted backup fields.")
        salt, nonce, cipher = (base64.b64decode(values[k], validate=True) for k in ("salt", "nonce", "ciphertext"))
        if len(salt) != 32 or len(nonce) != 12 or len(cipher) > 20_000_016:
            raise ValueError("Invalid encrypted backup parameters.")
        return AESGCM(key(password, salt)).decrypt(nonce, cipher, AAD)
    except InvalidTag as exc:
        raise ValueError("Incorrect password or damaged encrypted backup. Nothing was restored.") from exc
    except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid encrypted backup.") from exc
