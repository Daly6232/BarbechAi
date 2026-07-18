"""
Minimal TOTP (RFC 6238) implementation using only the Python standard
library — no pyotp/qrcode dependency. Compatible with any standard
authenticator app (Google Authenticator, Authy, 1Password, etc.).
"""
import base64
import hashlib
import hmac
import os
import struct
import time


def generate_secret(length: int = 20) -> str:
    """Random base32 secret, the standard format authenticator apps expect."""
    random_bytes = os.urandom(length)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")


def _hotp(secret: str, counter: int, digits: int = 6) -> str:
    # Base32 secrets need padding restored to a multiple of 8 before decoding.
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded.upper())
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code_int).zfill(digits)


def get_totp(secret: str, for_time: int = None, interval: int = 30, digits: int = 6) -> str:
    if for_time is None:
        for_time = int(time.time())
    counter = for_time // interval
    return _hotp(secret, counter, digits)


def verify_totp(secret: str, code: str, interval: int = 30, window: int = 1) -> bool:
    """Accepts a code valid for the current 30s window, plus one window
    before/after to tolerate normal clock drift between phone and server."""
    if not secret or not code:
        return False
    code = code.strip().replace(" ", "")
    now = int(time.time())
    for offset in range(-window, window + 1):
        if hmac.compare_digest(get_totp(secret, now + offset * interval), code):
            return True
    return False


def build_otpauth_uri(secret: str, email: str, issuer: str = "BarbechAi") -> str:
    return f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
