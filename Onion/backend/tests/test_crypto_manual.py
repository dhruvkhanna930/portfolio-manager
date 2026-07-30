"""Standalone sanity check for crypto.py — not pytest, just run directly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nacl.exceptions import CryptoError

from app import crypto

alice_pub, alice_priv = crypto.generate_keypair()
bob_pub, bob_priv = crypto.generate_keypair()
print("alice pub:", alice_pub)
print("bob pub:  ", bob_pub)

sealed = crypto.encrypt_message(alice_priv, bob_pub, "hello bob, this is alice")
plaintext = crypto.decrypt_message(bob_priv, alice_pub, sealed)
assert plaintext == "hello bob, this is alice"
print("round trip ok:", plaintext)

# wrong recipient key must fail to decrypt
mallory_pub, mallory_priv = crypto.generate_keypair()
try:
    crypto.decrypt_message(mallory_priv, alice_pub, sealed)
    raise SystemExit("FAIL: decryption with wrong private key should have raised")
except CryptoError:
    print("wrong-key decryption correctly rejected")

# tampered ciphertext must fail to decrypt (sender authentication)
tampered = bytearray(sealed)
tampered[-1] ^= 0xFF
try:
    crypto.decrypt_message(bob_priv, alice_pub, bytes(tampered))
    raise SystemExit("FAIL: tampered ciphertext should have raised")
except CryptoError:
    print("tampered ciphertext correctly rejected")

# nonce must differ between calls (never reused)
sealed2 = crypto.encrypt_message(alice_priv, bob_pub, "hello bob, this is alice")
assert sealed[:24] != sealed2[:24]
print("nonces differ across calls")

print("ALL CRYPTO TESTS PASSED")
