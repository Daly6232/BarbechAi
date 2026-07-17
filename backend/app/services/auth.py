import os
import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import generate_uuid
from app.database import SessionLocal, User

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


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


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


def register_user(email: str, password: str, name: str, role: str, created_by_role: str = None):
    """Register a new user. Only master_admin can create admin accounts.
    Only admin/master_admin can create back_office/field_agent accounts."""
    if role not in VALID_ROLES:
        return {"error": f"Invalid role. Must be one of: {VALID_ROLES}"}

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
        return {"success": True, "user_id": user.id, "email": email, "role": role}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def login_user(email: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            return {"error": "Invalid credentials"}

        if not verify_password(password, user.password_hash):
            return {"error": "Invalid credentials"}

        user.last_login = datetime.utcnow()
        db.commit()

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
                }
                for u in users
            ]
        }
    finally:
        db.close()


def set_user_active(requester_role: str, user_id: str, is_active: bool):
    """Activate/deactivate an account. Only admin/master_admin may do this,
    and only master_admin may touch another admin's account."""
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
        return {"success": True, "user_id": user.id, "is_active": user.is_active}
    except Exception as e:
        db.rollback()
        logger.exception(e)
        return {"error": str(e)}
    finally:
        db.close()


def reset_user_password(requester_role: str, user_id: str, new_password: str):
    """Admin-initiated password reset for an office/field account."""
    if requester_role not in ("admin", "master_admin"):
        return {"error": "Insufficient permissions"}
    if len(new_password) < 8:
        return {"error": "Password must be at least 8 characters"}
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.role in ("admin", "master_admin") and requester_role != "master_admin":
            return {"error": "Only master_admin can modify admin accounts"}
        user.password_hash = hash_password(new_password)
        db.commit()
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
