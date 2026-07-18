import os
import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import generate_uuid
from app.core.totp import generate_secret, get_totp, verify_totp, build_otpauth_uri
from app.database import SessionLocal, User
from app.services.audit import log_audit_event

logger = get_logger(__name__)

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY is not set. Refusing to start in production with no secret — "
            "set it in Render's environment variables."
        )
    SECRET_KEY = "barbechai-dev-secret-change-in-production-8f3a9c2e"
    logger.warning("JWT_SECRET_KEY not set — using insecure dev fallback. Do not use in production.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

VALID_ROLES = ["master_admin", "admin", "back_office", "field_agent"]

# Roles that get an MFA option — office/field roles don't have anything to
# protect beyond their own leads, admins have the keys to the whole system.
MFA_ELIGIBLE_ROLES = ("admin", "master_admin")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def validate_password_strength(password: str):
    """Beyond the old 8-char minimum: require a mix of cases and a digit.
    Returns (ok, error_message)."""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not any(c.islower() for c in password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, None


def create_access_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None


def register_user(email: str, password: str, name: str, role: str, requester: dict = None):
    """Register a new user. Only master_admin can create admin accounts.
    Only admin/master_admin can create back_office/field_agent accounts."""
    if role not in VALID_ROLES:
        return {"error": f"Invalid role. Must be one of: {VALID_ROLES}"}

    ok, err = validate_password_strength(password)
    if not ok:
        return {"error": err}

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return {"error": "Email already registered"}

        user = User(
            id=generate_uuid(),
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        log_audit_event("USER_CREATED", actor=requester, target_type="user", target_id=user.id,
                         details=f"email={email}, role={role}")
        return {"success": True, "user_id": user.id, "email": email, "role": role}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def login_user(email: str, password: str, ip: str = None, device: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            log_audit_event("LOGIN_FAILED", target_type="user", details=f"unknown or inactive account: {email}", ip=ip)
            return {"error": "Invalid credentials"}

        # Lockout check — happens before password verification so a locked
        # account doesn't leak whether the password itself was right.
        if user.locked_until and user.locked_until > datetime.utcnow():
            minutes_left = max(1, int((user.locked_until - datetime.utcnow()).total_seconds() // 60))
            return {"error": f"Compte temporairement verrouillé suite à plusieurs échecs. Réessayez dans {minutes_left} min."}

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                db.commit()
                log_audit_event("ACCOUNT_LOCKED", actor={"id": user.id, "name": user.name, "role": user.role},
                                 target_type="user", target_id=user.id, ip=ip,
                                 details=f"{MAX_FAILED_ATTEMPTS} failed attempts")
                return {"error": f"Trop de tentatives échouées. Compte verrouillé {LOCKOUT_MINUTES} minutes."}
            db.commit()
            log_audit_event("LOGIN_FAILED", actor={"id": user.id, "name": user.name, "role": user.role},
                             target_type="user", target_id=user.id, ip=ip)
            return {"error": "Invalid credentials"}

        # Correct password — reset the failure counter regardless of what
        # happens next (MFA gate or straight-through login).
        user.failed_login_attempts = 0
        user.locked_until = None

        if user.mfa_enabled:
            db.commit()
            # No token yet — the frontend must call verify_mfa_login with a
            # valid TOTP code before a session is actually issued.
            return {"mfa_required": True, "user_id": user.id}

        user.last_login = datetime.utcnow()
        if ip:
            user.last_login_ip = ip
        if device:
            user.last_login_device = device
        db.commit()
        log_audit_event("LOGIN_SUCCESS", actor={"id": user.id, "name": user.name, "role": user.role},
                         target_type="user", target_id=user.id, ip=ip)

        token = create_access_token(user.id, user.email, user.role)
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def verify_mfa_login(user_id: str, code: str, ip: str = None, device: str = None):
    """Second step of login when the account has MFA enabled."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return {"error": "Invalid credentials"}
        if not user.mfa_enabled or not user.mfa_secret:
            return {"error": "MFA not enabled for this account"}
        if not verify_totp(user.mfa_secret, code):
            log_audit_event("MFA_LOGIN_FAILED", actor={"id": user.id, "name": user.name, "role": user.role},
                             target_type="user", target_id=user.id, ip=ip)
            return {"error": "Code invalide"}

        user.last_login = datetime.utcnow()
        if ip:
            user.last_login_ip = ip
        if device:
            user.last_login_device = device
        db.commit()
        log_audit_event("LOGIN_SUCCESS", actor={"id": user.id, "name": user.name, "role": user.role},
                         target_type="user", target_id=user.id, ip=ip, details="via MFA")

        token = create_access_token(user.id, user.email, user.role)
        return {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def refresh_token(current_token: str):
    """Issue a fresh 12h token as long as the current one is still valid.
    The frontend calls this periodically while the app is open so an agent
    mid-shift never gets silently logged out — they only need to actually
    re-enter credentials if they've been away longer than the token's life."""
    payload = decode_access_token(current_token)
    if not payload:
        return {"error": "Invalid or expired token"}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user or not user.is_active:
            return {"error": "Invalid or expired token"}
        new_token = create_access_token(user.id, user.email, user.role)
        return {"success": True, "token": new_token}
    finally:
        db.close()


def setup_mfa(user_id: str):
    """Generate a new TOTP secret for a user to scan/enter into an
    authenticator app. Not enabled until confirm_mfa verifies a code."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.role not in MFA_ELIGIBLE_ROLES:
            return {"error": "MFA is only available for admin accounts"}
        secret = generate_secret()
        user.mfa_secret = secret
        user.mfa_enabled = False  # not active until confirmed
        db.commit()
        return {
            "success": True,
            "secret": secret,
            "otpauth_url": build_otpauth_uri(secret, user.email),
        }
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def confirm_mfa(user_id: str, code: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.mfa_secret:
            return {"error": "Run setup first"}
        if not verify_totp(user.mfa_secret, code):
            return {"error": "Code invalide"}
        user.mfa_enabled = True
        db.commit()
        log_audit_event("MFA_ENABLED", actor={"id": user.id, "name": user.name, "role": user.role},
                         target_type="user", target_id=user.id)
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def disable_mfa(user_id: str, code: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.mfa_enabled:
            return {"error": "MFA not enabled"}
        if not verify_totp(user.mfa_secret, code):
            return {"error": "Code invalide"}
        user.mfa_enabled = False
        user.mfa_secret = None
        db.commit()
        log_audit_event("MFA_DISABLED", actor={"id": user.id, "name": user.name, "role": user.role},
                         target_type="user", target_id=user.id)
        return {"success": True}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def get_current_user(token: str):
    payload = decode_access_token(token)
    if not payload:
        return None
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user or not user.is_active:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        }
    finally:
        db.close()


def list_agents(requester_role: str):
    """Admin/master_admin can view all agents."""
    if requester_role not in ["admin", "master_admin"]:
        return {"error": "Insufficient permissions"}

    visible_roles = ["back_office", "field_agent"]
    if requester_role == "master_admin":
        visible_roles.append("admin")

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.role.in_(visible_roles)).all()
        return {
            "agents": [
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                    "last_login_ip": u.last_login_ip,
                    "last_login_device": u.last_login_device,
                    "mfa_enabled": u.mfa_enabled,
                }
                for u in users
            ]
        }
    finally:
        db.close()


def set_user_active(requester: dict, user_id: str, is_active: bool):
    """Activate/deactivate an account. Only admin/master_admin may do this,
    and only master_admin may touch another admin's account."""
    requester_role = requester.get("role") if requester else None
    if requester_role not in ("admin", "master_admin"):
        return {"error": "Insufficient permissions"}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.role in ("admin", "master_admin") and requester_role != "master_admin":
            return {"error": "Only master_admin can modify admin accounts"}
        user.is_active = is_active
        db.commit()
        log_audit_event("USER_REACTIVATED" if is_active else "USER_DEACTIVATED", actor=requester,
                         target_type="user", target_id=user.id, details=f"target_email={user.email}")
        return {"success": True, "user_id": user.id, "is_active": user.is_active}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def reset_user_password(requester: dict, user_id: str, new_password: str):
    """Admin-initiated password reset for an office/field account."""
    requester_role = requester.get("role") if requester else None
    if requester_role not in ("admin", "master_admin"):
        return {"error": "Insufficient permissions"}
    ok, err = validate_password_strength(new_password)
    if not ok:
        return {"error": err}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.role in ("admin", "master_admin") and requester_role != "master_admin":
            return {"error": "Only master_admin can modify admin accounts"}
        user.password_hash = hash_password(new_password)
        db.commit()
        log_audit_event("PASSWORD_RESET", actor=requester, target_type="user", target_id=user.id,
                         details=f"target_email={user.email}")
        return {"success": True, "user_id": user.id}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def require_auth(authorization: str, allowed_roles: list = None):
    """Validate a Bearer token and optionally restrict by role.
    Returns (user_dict, None) on success, or (None, error_dict) on failure."""
    if not authorization:
        return None, {"error": "No token provided"}
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token)
    if not user:
        return None, {"error": "Invalid or expired token"}
    if allowed_roles and user["role"] not in allowed_roles:
        return None, {"error": "Insufficient permissions"}
    return user, None
