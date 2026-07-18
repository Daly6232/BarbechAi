from fastapi import APIRouter, Header, Request
from app.services.auth import (
    register_user,
    login_user,
    verify_mfa_login,
    refresh_token,
    get_current_user,
    list_agents,
    set_user_active,
    reset_user_password,
    setup_mfa,
    confirm_mfa,
    disable_mfa,
)

router = APIRouter()


def _require_requester(authorization: str):
    if not authorization:
        return None, {"error": "No token provided"}
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token)
    if not user:
        return None, {"error": "Invalid or expired token"}
    return user, None


def _client_info(request: Request):
    """Best-effort IP + device string for login visibility. X-Forwarded-For
    is used first since Render/Vercel sit behind a proxy."""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else None)
    device = request.headers.get("user-agent", "")[:200]
    return ip, device


@router.post("/auth/register")
def register(email: str, password: str, name: str, role: str, authorization: str = Header(None)):
    """Create a new user account. Requires admin/master_admin token for agent creation."""
    requester = None
    if authorization:
        token = authorization.replace("Bearer ", "")
        requester = get_current_user(token)

    if role in ["admin", "master_admin"]:
        if not requester or requester["role"] != "master_admin":
            return {"error": "Only master_admin can create admin accounts"}
    elif role in ["back_office", "field_agent"]:
        if not requester or requester["role"] not in ["admin", "master_admin"]:
            return {"error": "Only admin or master_admin can create agent accounts"}

    return register_user(email, password, name, role)


@router.post("/auth/login")
def login(email: str, password: str, request: Request = None):
    ip, device = _client_info(request) if request else (None, None)
    return login_user(email, password, ip=ip, device=device)


@router.post("/auth/login/mfa")
def login_mfa(user_id: str, code: str, request: Request = None):
    """Second step of login for accounts with MFA enabled."""
    ip, device = _client_info(request) if request else (None, None)
    return verify_mfa_login(user_id, code, ip=ip, device=device)


@router.post("/auth/refresh")
def refresh(authorization: str = Header(None)):
    """Silently extend a still-valid session — called periodically by the
    frontend so an active agent is never kicked out mid-shift."""
    if not authorization:
        return {"error": "No token provided"}
    token = authorization.replace("Bearer ", "")
    return refresh_token(token)


@router.get("/auth/me")
def me(authorization: str = Header(None)):
    if not authorization:
        return {"error": "No token provided"}
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token)
    if not user:
        return {"error": "Invalid or expired token"}
    return {"user": user}


@router.get("/auth/agents")
def agents(authorization: str = Header(None)):
    if not authorization:
        return {"error": "No token provided"}
    token = authorization.replace("Bearer ", "")
    user = get_current_user(token)
    if not user:
        return {"error": "Invalid or expired token"}
    return list_agents(user["role"])


@router.post("/auth/deactivate")
def deactivate(user_id: str, authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return set_user_active(requester["role"], user_id, False)


@router.post("/auth/reactivate")
def reactivate(user_id: str, authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return set_user_active(requester["role"], user_id, True)


@router.post("/auth/reset-password")
def reset_password(user_id: str, new_password: str, authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return reset_user_password(requester["role"], user_id, new_password)


# --- MFA (admin/master_admin only) ---

@router.post("/auth/mfa/setup")
def mfa_setup(authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return setup_mfa(requester["id"])


@router.post("/auth/mfa/confirm")
def mfa_confirm(code: str, authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return confirm_mfa(requester["id"], code)


@router.post("/auth/mfa/disable")
def mfa_disable(code: str, authorization: str = Header(None)):
    requester, error = _require_requester(authorization)
    if error:
        return error
    return disable_mfa(requester["id"], code)
