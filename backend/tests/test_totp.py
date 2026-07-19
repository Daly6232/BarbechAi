from app.core.totp import generate_secret, get_totp, verify_totp


def test_generate_secret_is_valid_base32():
    import base64
    secret = generate_secret()
    assert secret
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    # Raises if not valid base32 — the test itself is the assertion.
    base64.b32decode(padded.upper())


def test_totp_round_trip_succeeds():
    secret = generate_secret()
    code = get_totp(secret)
    assert verify_totp(secret, code)


def test_totp_rejects_wrong_code():
    secret = generate_secret()
    assert not verify_totp(secret, "000000")


def test_totp_rejects_empty_inputs():
    secret = generate_secret()
    assert not verify_totp(secret, "")
    assert not verify_totp("", "123456")


def test_totp_different_secrets_produce_different_codes():
    s1, s2 = generate_secret(), generate_secret()
    # Astronomically unlikely to collide for random secrets at the same instant.
    assert get_totp(s1) != get_totp(s2) or s1 == s2
