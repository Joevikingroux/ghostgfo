"""AES-256-GCM payload encryption for the Ghost CFO agent.

Each client has a unique 32-byte key stored in the agent config file.
The key is also stored server-side against the agent's API key so the
backend can decrypt the payload on arrival.

Wire format (base64-encoded JSON envelope):
  {
    "v": 1,
    "nonce": "<base64 12-byte nonce>",
    "ciphertext": "<base64 AES-GCM ciphertext>",
    "tag": "<base64 16-byte auth tag>"
  }
"""
from __future__ import annotations

import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def _ensure_bytes(key: str | bytes) -> bytes:
    if isinstance(key, str):
        raw = key.encode()
        # Pad or truncate to 32 bytes if a human-readable key is passed
        if len(raw) != 32:
            raw = raw.ljust(32, b"\x00")[:32]
        return raw
    if len(key) != 32:
        key = key.ljust(32, b"\x00")[:32]
    return key


def derive_agent_key(global_key: str | bytes, agent_id: str) -> bytes:
    """Derive a per-agent 32-byte AES key from the global key using HKDF-SHA256.

    The agent_id (UUID string) acts as the HKDF info parameter so each agent
    gets a unique key even if the global key is ever compromised on one server.
    """
    key_bytes = _ensure_bytes(global_key)
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=agent_id.encode()).derive(key_bytes)


def encrypt_payload(data: dict, key: str | bytes) -> str:
    """Encrypt *data* with AES-256-GCM.  Returns a base64-encoded JSON envelope."""
    key_bytes = _ensure_bytes(key)
    nonce = os.urandom(12)
    plaintext = json.dumps(data, default=str).encode()

    aesgcm = AESGCM(key_bytes)
    # AESGCM.encrypt returns ciphertext + 16-byte tag concatenated
    ct_and_tag = aesgcm.encrypt(nonce, plaintext, None)
    ciphertext = ct_and_tag[:-16]
    tag = ct_and_tag[-16:]

    envelope = {
        "v": 1,
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "tag": base64.b64encode(tag).decode(),
    }
    return base64.b64encode(json.dumps(envelope).encode()).decode()


def decrypt_payload(envelope_b64: str, key: str | bytes) -> dict:
    """Decrypt an envelope produced by :func:`encrypt_payload`.  Used in tests."""
    key_bytes = _ensure_bytes(key)
    envelope = json.loads(base64.b64decode(envelope_b64))
    nonce = base64.b64decode(envelope["nonce"])
    ciphertext = base64.b64decode(envelope["ciphertext"])
    tag = base64.b64decode(envelope["tag"])

    aesgcm = AESGCM(key_bytes)
    plaintext = aesgcm.decrypt(nonce, ciphertext + tag, None)
    return json.loads(plaintext)
