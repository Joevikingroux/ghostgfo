"""AES-256-GCM encryption for PDF files stored at rest.

Format: 12-byte random nonce || ciphertext+tag (AESGCM appends the 16-byte
tag to the ciphertext automatically).  Encrypted files use the .pdf.enc
extension; unencrypted .pdf files (legacy) are read through transparently.

Key: SHA-256(secret_key + ":ghost-cfo-pdf-v1") — derived from the server
secret so the key is never stored separately, but changing SECRET_KEY makes
all existing PDFs unreadable.  Rotate by re-generating reports.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Union


def _key() -> bytes:
    from app.core.config import settings
    return hashlib.sha256(
        settings.secret_key.encode() + b":ghost-cfo-pdf-v1"
    ).digest()


def encrypt_pdf(plaintext: bytes) -> bytes:
    """Return nonce(12) || ciphertext || tag(16)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = os.urandom(12)
    return nonce + AESGCM(_key()).encrypt(nonce, plaintext, None)


def decrypt_pdf(enc_bytes: bytes) -> bytes:
    """Decrypt an AES-256-GCM blob produced by encrypt_pdf()."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    return AESGCM(_key()).decrypt(enc_bytes[:12], enc_bytes[12:], None)


def read_pdf_bytes(path: Union[str, Path]) -> bytes:
    """Read PDF bytes, decrypting transparently if the file ends in .enc."""
    p = Path(path)
    raw = p.read_bytes()
    return decrypt_pdf(raw) if str(p).endswith(".enc") else raw
