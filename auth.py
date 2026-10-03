import hashlib
import os
import database as db

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + h.hex()


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, hash_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return h.hex() == hash_hex


def seed_god_user():
    """Create the god-mode user if it doesn't exist."""
    if not db.get_user("god"):
        db.create_user("god", _hash_password("god@admin2025"), "god")


def seed_default_admin():
    if not db.get_user("admin"):
        db.create_user("admin", _hash_password("admin123"), "admin")


def login(username, password):
    user = db.get_user(username)
    if user and _verify_password(password, user["password_hash"]):
        return user
    return None


def register_user(username, password, role="cashier"):
    return db.create_user(username, _hash_password(password), role)


def reset_password(username, new_password):
    db.update_password(username, _hash_password(new_password))
