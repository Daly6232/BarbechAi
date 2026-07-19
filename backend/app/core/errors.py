from fastapi.responses import JSONResponse


def error_response(message: str, status_code: int = 400):
    """Returns a proper HTTP status code while keeping the exact same
    {"error": "..."} JSON body shape the frontend has always checked for.
    This is the safe middle ground: fixes status codes (so browser devtools,
    monitoring, and any future API consumer see real 401/403/404s instead of
    everything reporting 200 OK) without changing the response body shape,
    which would break every existing `if (data.error)` check across the
    frontend and the already-built mobile APK.
    """
    return JSONResponse(status_code=status_code, content={"error": message})


# Common status codes, named for readability at call sites.
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
CONFLICT = 409
TOO_MANY_REQUESTS = 429
