"""PyNaCl-based E2E crypto. Box (not SealedBox) so decryption also authenticates the sender."""

import base64

from nacl.public import Box, PrivateKey, PublicKey


def generate_keypair() -> tuple[str, str]:
    """Returns (public_key_b64, private_key_b64)."""
    private_key = PrivateKey.generate()
    public_b64 = base64.b64encode(bytes(private_key.public_key)).decode("ascii")
    private_b64 = base64.b64encode(bytes(private_key)).decode("ascii")
    return public_b64, private_b64


def encrypt_message(my_private_key_b64: str, their_public_key_b64: str, plaintext: str) -> bytes:
    """Returns nonce+ciphertext combined (PyNaCl's default EncryptedMessage form)."""
    box = Box(
        PrivateKey(base64.b64decode(my_private_key_b64)),
        PublicKey(base64.b64decode(their_public_key_b64)),
    )
    return bytes(box.encrypt(plaintext.encode("utf-8")))


def decrypt_message(my_private_key_b64: str, their_public_key_b64: str, sealed: bytes) -> str:
    """Raises nacl.exceptions.CryptoError if tampered or from the wrong keypair."""
    box = Box(
        PrivateKey(base64.b64decode(my_private_key_b64)),
        PublicKey(base64.b64decode(their_public_key_b64)),
    )
    return box.decrypt(sealed).decode("utf-8")
