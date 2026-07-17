from fastapi import APIRouter, Header
from app.services.auth import (
    register_user,
    login_user,
    get_current_user,
    list_agents,
    set_user_active,
    reset_user_password,
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
def login(email: str, password: str):
    return login_user(email, password)


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
