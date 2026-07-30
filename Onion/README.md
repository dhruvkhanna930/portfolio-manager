# Whisper

Decentralized, anonymous, peer-owned chat over real Tor hidden services with end-to-end encryption. No central server ever sees message content or metadata; each user's chat history lives only in their own local SQLite database.

## Stack

- **Backend**: Python, FastAPI, `stem` (Tor control), PyNaCl (E2E crypto), SQLite
- **Frontend**: React (Vite)
- **Transport**: real Tor hidden services by default, with a `MockTransport` loopback fallback for demo safety

## Status

Day 1 (core P2P proof) complete: identity/contact/message persistence, PyNaCl `Box` encryption, and a real Tor hidden service exchanging an encrypted, msgpack-framed envelope between two independent local processes — end to end, decrypting correctly on the receiving side.

Day 2 (FastAPI routes, WebSocket push, React UI, presence, delete flows) is in progress.

## Setup

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install -r requirements.txt   # Windows
```

Tor must be running locally with a control port before starting the app:

```
tor -f ../scripts/torrc.template
```

Wait for `Bootstrapped 100% (done)` in the Tor log before starting any instance.

## Manual proof scripts (`backend/tests/`)

These aren't pytest suites — they're standalone scripts used to retire risk on each layer before wiring the full app:

- `test_db_manual.py` — SQLite schema/DAO sanity check
- `test_crypto_manual.py` — PyNaCl `Box` round trip, tamper/wrong-key rejection
- `test_tor_auth_manual.py` — confirms `stem` can authenticate to the running Tor control port
- `tor_server_manual.py` / `tor_client_manual.py` — raw byte exchange over a real ephemeral hidden service, proving the onion address is stable across restarts
- `test_full_roundtrip_manual.py` — the full proof: two processes, real Tor, an encrypted envelope sent and correctly decrypted end to end
