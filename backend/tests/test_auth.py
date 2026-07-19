from app.services.auth import (
    validate_password_strength,
    register_user,
    login_user,
    require_auth,
    MAX_FAILED_ATTEMPTS,
)


# --- Password strength ---

def test_password_strength_rejects_too_short():
    ok, err = validate_password_strength("Ab1")
    assert not ok


def test_password_strength_rejects_no_uppercase():
    ok, err = validate_password_strength("abcdefg1")
    assert not ok


def test_password_strength_rejects_no_lowercase():
    ok, err = validate_password_strength("ABCDEFG1")
    assert not ok


def test_password_strength_rejects_no_digit():
    ok, err = validate_password_strength("Abcdefgh")
    assert not ok


def test_password_strength_accepts_valid_password():
    ok, err = validate_password_strength("Abcdefg1")
    assert ok
    assert err is None


# --- Register / login ---

def test_register_and_login_success(unique_email):
    result = register_user(unique_email, "Abcdefg1", "Test User", "field_agent")
    assert result.get("success") is True

    login = login_user(unique_email, "Abcdefg1")
    assert login.get("success") is True
    assert "token" in login
    assert login["user"]["email"] == unique_email
    assert login["user"]["role"] == "field_agent"


def test_register_rejects_weak_password(unique_email):
    result = register_user(unique_email, "weak", "Test User", "field_agent")
    assert "error" in result


def test_register_rejects_duplicate_email(unique_email):
    register_user(unique_email, "Abcdefg1", "First", "field_agent")
    result = register_user(unique_email, "Abcdefg1", "Second", "field_agent")
    assert "error" in result


def test_register_rejects_invalid_role(unique_email):
    result = register_user(unique_email, "Abcdefg1", "Test", "superuser")
    assert "error" in result


def test_login_wrong_password_fails(unique_email):
    register_user(unique_email, "Abcdefg1", "Test User", "field_agent")
    result = login_user(unique_email, "WrongPass1")
    assert "error" in result
    assert "token" not in result


def test_login_unknown_email_fails():
    result = login_user("nobody-here@example.com", "Whatever1")
    assert "error" in result


def test_login_lockout_after_max_failed_attempts(unique_email):
    register_user(unique_email, "Abcdefg1", "Test User", "field_agent")
    for _ in range(MAX_FAILED_ATTEMPTS):
        login_user(unique_email, "WrongPass1")
    # Even the CORRECT password should now be rejected — account is locked.
    result = login_user(unique_email, "Abcdefg1")
    assert "error" in result
    assert "verrouill" in result["error"].lower()


def test_login_succeeds_normally_before_lockout_threshold(unique_email):
    register_user(unique_email, "Abcdefg1", "Test User", "field_agent")
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        login_user(unique_email, "WrongPass1")
    # One failed attempt short of lockout — correct password should still work.
    result = login_user(unique_email, "Abcdefg1")
    assert result.get("success") is True


# --- require_auth status codes ---
# These are the exact function the July 2026 production incident traced
# back to — a missing status code meant auth failures returned HTTP 200,
# and separately, a dropped function broke the whole module. Testing this
# function directly (not just via a live server) catches both classes of
# regression at CI time instead of after a deploy.

def test_require_auth_no_token_returns_401():
    user, error = require_auth(None)
    assert user is None
    assert error is not None
    assert error.status_code == 401


def test_require_auth_invalid_token_returns_401():
    user, error = require_auth("Bearer not-a-real-token")
    assert user is None
    assert error.status_code == 401


def test_require_auth_valid_token_succeeds(unique_email):
    register_user(unique_email, "Abcdefg1", "Test Agent", "field_agent")
    login = login_user(unique_email, "Abcdefg1")
    token = login["token"]

    user, error = require_auth(f"Bearer {token}")
    assert error is None
    assert user["email"] == unique_email


def test_require_auth_insufficient_role_returns_403(unique_email):
    register_user(unique_email, "Abcdefg1", "Test Agent", "field_agent")
    login = login_user(unique_email, "Abcdefg1")
    token = login["token"]

    user, error = require_auth(f"Bearer {token}", allowed_roles=["admin", "master_admin"])
    assert user is None
    assert error.status_code == 403


def test_require_auth_allowed_role_succeeds(unique_email):
    result = register_user(unique_email, "Abcdefg1", "Test Admin", "admin")
    assert result.get("success") is True
    login = login_user(unique_email, "Abcdefg1")
    token = login["token"]

    user, error = require_auth(f"Bearer {token}", allowed_roles=["admin", "master_admin"])
    assert error is None
    assert user["role"] == "admin"
