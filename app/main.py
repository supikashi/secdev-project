import time
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .entities import SuggestionCreate, SuggestionOut

app = FastAPI(title="SecDev Course App", version="0.1.0")


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


@app.get("/health")
def health():
    return {"status": "ok"}


# --- in-memory DBs for demo ---
_DB = {"items": [], "suggestions": []}

_USERS = {
    1: {"id": 1, "username": "alice", "password": "alicepass"},
    2: {"id": 2, "username": "bob", "password": "bobpass"},
}
_TOKENS: dict[str, int] = {}  # token -> user_id

security = HTTPBearer(auto_error=False)


# Dependency: get current user from Bearer token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise ApiError("auth_required", "Authorization required", 401)
    token = credentials.credentials
    user_id = _TOKENS.get(token)
    if not user_id:
        raise ApiError("invalid_token", "Invalid or expired token", 401)
    user = _USERS.get(user_id)
    if not user:
        raise ApiError("invalid_token", "Invalid token (user not found)", 401)
    return user


# Rate limiting (in-memory, demo)
RATE_LIMIT_ATTEMPTS = 5
RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT: dict[str, list[float]] = {}  # username -> list of attempt timestamps


@app.post("/auth/login")
def login(username: str, password: str):
    """
    Простейший логин с rate limiting по username:
    максимум RATE_LIMIT_ATTEMPTS попыток в RATE_LIMIT_WINDOW секунд.
    """
    now = time.time()
    attempts = _RATE_LIMIT.get(username, [])

    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]
    _RATE_LIMIT[username] = attempts

    if len(attempts) >= RATE_LIMIT_ATTEMPTS:
        raise ApiError(
            "too_many_requests", "Too many login attempts, try again later", 429
        )

    for u in _USERS.values():
        if u["username"] == username and u["password"] == password:
            _RATE_LIMIT.pop(username, None)
            token = str(uuid4())
            _TOKENS[token] = u["id"]
            return {"access_token": token, "token_type": "bearer"}

    _RATE_LIMIT.setdefault(username, []).append(now)
    raise ApiError("invalid_credentials", "Invalid username or password", 401)


@app.post("/auth/logout")
def logout(
    current_user=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    _TOKENS.pop(token, None)
    return {"status": "logged_out"}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.post("/suggestions", response_model=SuggestionOut)
def create_suggestion(s: SuggestionCreate, current_user=Depends(get_current_user)):
    if not s.title or len(s.title) > 200:
        raise ApiError("validation_error", "title must be 1..200 chars", 422)
    if not s.text or len(s.text) > 2000:
        raise ApiError("validation_error", "text must be 1..2000 chars", 422)

    new_id = len(_DB["suggestions"]) + 1
    payload = s.model_dump()
    suggestion = {"id": new_id, "user_id": current_user["id"], **payload}
    _DB["suggestions"].append(suggestion)
    return suggestion


@app.get("/suggestions", response_model=List[SuggestionOut])
def list_suggestions(status: Optional[str] = Query(None)):
    if status:
        return [s for s in _DB["suggestions"] if s["status"] == status]
    return _DB["suggestions"]


@app.get("/suggestions/{suggestion_id}", response_model=SuggestionOut)
def get_suggestion(suggestion_id: int):
    for s in _DB["suggestions"]:
        if s["id"] == suggestion_id:
            return s
    raise ApiError("not_found", "suggestion not found", 404)


@app.put("/suggestions/{suggestion_id}", response_model=SuggestionOut)
def update_suggestion(
    suggestion_id: int, s: SuggestionCreate, current_user=Depends(get_current_user)
):
    for idx, sg in enumerate(_DB["suggestions"]):
        if sg["id"] == suggestion_id:
            # only owner can update
            if sg["user_id"] != current_user["id"]:
                raise ApiError(
                    "forbidden", "You are not the owner of this suggestion", 403
                )
            updated = {"id": suggestion_id, "user_id": sg["user_id"], **s.model_dump()}
            _DB["suggestions"][idx] = updated
            return updated
    raise ApiError("not_found", "suggestion not found", 404)


@app.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: int, current_user=Depends(get_current_user)):
    for idx, sg in enumerate(_DB["suggestions"]):
        if sg["id"] == suggestion_id:
            if sg["user_id"] != current_user["id"]:
                raise ApiError(
                    "forbidden", "You are not the owner of this suggestion", 403
                )
            del _DB["suggestions"][idx]
            return {"status": "deleted"}
    raise ApiError("not_found", "suggestion not found", 404)
