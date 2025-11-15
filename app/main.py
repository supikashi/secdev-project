import os
import time
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import (
    create_suggestion_db,
    create_user_db,
    delete_suggestion_db,
    get_suggestion_by_id_db,
    get_suggestions_db,
    get_user_by_username_db,
    init_db,
    update_suggestion_db,
    verify_password_db,
)
from .entities import SuggestionCreate, SuggestionOut

app = FastAPI(
    title="SecDev Course App",
    version="0.1.0",
    description="Secure application with JWT authentication and Argon2id password hashing",
)


def cleanup_expired_tokens():
    """Remove expired tokens from storage."""
    current_time = time.time()
    expired_tokens = [
        token
        for token, data in _TOKENS.items()
        if current_time - data["created_at"] > TOKEN_TTL
    ]
    for token in expired_tokens:
        del _TOKENS[token]
    if expired_tokens:
        print(f"Cleaned up {len(expired_tokens)} expired tokens")


# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    init_db()

    alice_user = os.getenv("DEFAULT_USER_ALICE", "alice")
    alice_pass = os.getenv("DEFAULT_PASSWORD_ALICE", "alicepass")
    bob_user = os.getenv("DEFAULT_USER_BOB", "bob")
    bob_pass = os.getenv("DEFAULT_PASSWORD_BOB", "bobpass")

    if not get_user_by_username_db(alice_user):
        create_user_db(alice_user, alice_pass)
    if not get_user_by_username_db(bob_user):
        create_user_db(bob_user, bob_pass)


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "ok"}


_DB = {"items": []}
_TOKENS: dict[str, dict] = {}
TOKEN_TTL = 3600

security = HTTPBearer(
    auto_error=False, description="JWT Bearer token. Get it from /auth/login endpoint."
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if len(_TOKENS) > 10:
        cleanup_expired_tokens()

    if not credentials:
        raise ApiError("auth_required", "Authorization required", 401)
    token = credentials.credentials
    token_data = _TOKENS.get(token)
    if not token_data:
        raise ApiError("invalid_token", "Invalid or expired token", 401)

    current_time = time.time()
    if current_time - token_data["created_at"] > TOKEN_TTL:
        del _TOKENS[token]
        raise ApiError("token_expired", "Token has expired", 401)

    return {"id": token_data["user_id"]}


RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_IP_ATTEMPTS = 10
_RATE_LIMIT: dict[str, list[float]] = {}
_RATE_LIMIT_IP: dict[str, list[float]] = {}


@app.post("/auth/login", tags=["Authentication"])
def login(username: str, password: str, request: Request):
    """
    Login endpoint with rate limiting (by username and IP) and Argon2id password verification.

    - **username**: Your username (default users: 'alice' or 'bob')
    - **password**: Your password (configured in .env file)

    Returns JWT Bearer token to use in other endpoints.
    Rate limits:
    - Max 5 attempts per 60 seconds per username
    - Max 10 attempts per 60 seconds per IP address
    """
    now = time.time()
    client_ip = request.client.host if request.client else "unknown"

    attempts = _RATE_LIMIT.get(username, [])
    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    _RATE_LIMIT[username] = attempts

    if len(attempts) >= RATE_LIMIT_ATTEMPTS:
        raise ApiError(
            "too_many_requests",
            "Too many login attempts for this username, try again later",
            429,
        )

    ip_attempts = _RATE_LIMIT_IP.get(client_ip, [])
    ip_attempts = [t for t in ip_attempts if now - t < RATE_LIMIT_WINDOW]
    _RATE_LIMIT_IP[client_ip] = ip_attempts

    if len(ip_attempts) >= RATE_LIMIT_IP_ATTEMPTS:
        raise ApiError(
            "too_many_requests",
            "Too many login attempts from this IP address, try again later",
            429,
        )

    user = verify_password_db(username, password)
    if not user:
        _RATE_LIMIT.setdefault(username, []).append(now)
        _RATE_LIMIT_IP.setdefault(client_ip, []).append(now)
        raise ApiError("invalid_credentials", "Invalid username or password", 401)

    _RATE_LIMIT.pop(username, None)
    _RATE_LIMIT_IP.pop(client_ip, None)

    token = str(uuid4())
    _TOKENS[token] = {"user_id": user["id"], "created_at": time.time()}
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL}


@app.post("/auth/register", tags=["Authentication"])
def register(username: str, password: str):
    """
    Register a new user account.

    - **username**: Choose a unique username (3-50 characters, alphanumeric and underscore only)
    - **password**: Choose a strong password (minimum 8 characters)

    Password will be hashed with Argon2id before storing.
    Returns the newly created user info (without password).
    """
    if not username or len(username) < 3 or len(username) > 50:
        raise ApiError("validation_error", "username must be 3-50 characters", 422)

    if not username.replace("_", "").isalnum():
        raise ApiError(
            "validation_error",
            "username must contain only letters, numbers, and underscores",
            422,
        )

    dangerous_patterns = [
        "--",
        "/*",
        "*/",
        ";",
        "'",
        '"',
        "\\",
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "SELECT",
    ]
    username_upper = username.upper()
    if any(pattern in username_upper for pattern in dangerous_patterns):
        raise ApiError(
            "validation_error", "username contains invalid characters or patterns", 422
        )

    if not password or len(password) < 8:
        raise ApiError(
            "validation_error", "password must be at least 8 characters", 422
        )

    if get_user_by_username_db(username):
        raise ApiError("user_exists", "Username already taken", 409)

    user = create_user_db(username, password)
    if not user:
        raise ApiError("server_error", "Failed to create user", 500)

    return {
        "id": user["id"],
        "username": user["username"],
        "message": "User created successfully. You can now login.",
    }


@app.post("/auth/logout", tags=["Authentication"])
def logout(
    current_user=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Logout endpoint - invalidates current JWT token.
    Requires Bearer token in Authorization header.
    """
    token = credentials.credentials
    _TOKENS.pop(token, None)
    return {"status": "logged_out"}


@app.get("/auth/token-info", tags=["Authentication"])
def token_info(
    current_user=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Get information about current token including time to live.
    Requires Bearer token in Authorization header.
    """
    token = credentials.credentials
    token_data = _TOKENS.get(token)
    if not token_data:
        raise ApiError("invalid_token", "Token not found", 401)

    current_time = time.time()
    age = current_time - token_data["created_at"]
    ttl_remaining = TOKEN_TTL - age

    return {
        "user_id": token_data["user_id"],
        "token_age_seconds": int(age),
        "ttl_remaining_seconds": int(ttl_remaining),
        "expires_at": int(token_data["created_at"] + TOKEN_TTL),
    }


@app.post("/items", tags=["Items (Demo)"])
def create_item(name: str):
    """Create item."""
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}", tags=["Items (Demo)"])
def get_item(item_id: int):
    """Get item by ID."""
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.post("/suggestions", response_model=SuggestionOut, tags=["Suggestions"])
def create_suggestion(s: SuggestionCreate, current_user=Depends(get_current_user)):
    """
    Create a new suggestion.
    Requires authentication - use Bearer token from /auth/login.
    """
    if not s.title or len(s.title) > 200:
        raise ApiError("validation_error", "title must be 1..200 chars", 422)
    if not s.text or len(s.text) > 2000:
        raise ApiError("validation_error", "text must be 1..2000 chars", 422)

    suggestion = create_suggestion_db(
        user_id=current_user["id"], title=s.title, text=s.text, status=s.status or "new"
    )
    return suggestion


@app.get("/suggestions", response_model=List[SuggestionOut], tags=["Suggestions"])
def list_suggestions(
    status: Optional[str] = Query(
        None, description="Filter by status (e.g., 'new', 'reviewed')"
    )
):
    """
    Get all suggestions, optionally filtered by status.
    No authentication required.
    """
    return get_suggestions_db(status=status)


@app.get(
    "/suggestions/{suggestion_id}", response_model=SuggestionOut, tags=["Suggestions"]
)
def get_suggestion(suggestion_id: int):
    """
    Get suggestion by ID.
    No authentication required.
    """
    suggestion = get_suggestion_by_id_db(suggestion_id)
    if not suggestion:
        raise ApiError("not_found", "suggestion not found", 404)
    return suggestion


@app.put(
    "/suggestions/{suggestion_id}", response_model=SuggestionOut, tags=["Suggestions"]
)
def update_suggestion(
    suggestion_id: int, s: SuggestionCreate, current_user=Depends(get_current_user)
):
    """
    Update suggestion by ID (only owner can update).
    Requires authentication - use Bearer token from /auth/login.
    Returns 403 if you try to update someone else's suggestion.
    """
    suggestion = get_suggestion_by_id_db(suggestion_id)
    if not suggestion:
        raise ApiError("not_found", "suggestion not found", 404)

    if suggestion["user_id"] != current_user["id"]:
        raise ApiError("forbidden", "You are not the owner of this suggestion", 403)

    updated = update_suggestion_db(
        suggestion_id=suggestion_id,
        title=s.title,
        text=s.text,
        status=s.status or suggestion["status"],
    )
    return updated


@app.delete("/suggestions/{suggestion_id}", tags=["Suggestions"])
def delete_suggestion(suggestion_id: int, current_user=Depends(get_current_user)):
    """
    Delete suggestion by ID (only owner can delete).
    Requires authentication - use Bearer token from /auth/login.
    Returns 403 if you try to delete someone else's suggestion.
    """
    suggestion = get_suggestion_by_id_db(suggestion_id)
    if not suggestion:
        raise ApiError("not_found", "suggestion not found", 404)

    if suggestion["user_id"] != current_user["id"]:
        raise ApiError("forbidden", "You are not the owner of this suggestion", 403)

    delete_suggestion_db(suggestion_id)
    return {"status": "deleted"}
