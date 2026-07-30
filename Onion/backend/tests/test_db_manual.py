"""Standalone sanity check for db.py — not pytest, just run directly."""

import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db

DATA_DIR = Path(__file__).resolve().parent / "_scratch_db"
shutil.rmtree(DATA_DIR, ignore_errors=True)

conn = db.get_connection(str(DATA_DIR))

assert db.get_identity(conn) is None
db.save_identity(conn, "pub123", "priv123", "abcdefg.onion", "onionpriv123", time.time())
identity = db.get_identity(conn)
assert identity["public_key"] == "pub123"
assert identity["onion_address"] == "abcdefg.onion"
print("identity ok:", dict(identity))

contact_id = db.create_contact(conn, "Alice", "aliceonion.onion", "alicepub", time.time())
assert db.get_contact(conn, contact_id)["alias"] == "Alice"
assert db.get_contact_by_onion(conn, "aliceonion.onion")["id"] == contact_id

try:
    db.create_contact(conn, "Alice2", "aliceonion.onion", "otherpub", time.time())
    raise SystemExit("FAIL: duplicate onion_address should have raised")
except Exception as e:
    print("duplicate onion_address correctly rejected:", type(e).__name__)

msg_id = db.create_message(conn, contact_id, "sent", "hello", "uuid-1", "sending", time.time())
db.update_message_status(conn, "uuid-1", "delivered")
msgs = db.list_messages(conn, contact_id)
assert len(msgs) == 1 and msgs[0]["delivery_status"] == "delivered"
print("message ok:", dict(msgs[0]))

db.delete_contact(conn, contact_id)
assert db.get_contact(conn, contact_id) is None
assert db.list_messages(conn, contact_id) == []
print("cascade delete on contact removal ok")

db.save_identity(conn, "pub123", "priv123", "abcdefg.onion", "onionpriv123", time.time())
db.wipe_all(conn)
assert db.get_identity(conn) is None
print("wipe_all ok")

conn.close()
shutil.rmtree(DATA_DIR, ignore_errors=True)
print("ALL DB TESTS PASSED")
