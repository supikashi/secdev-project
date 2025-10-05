from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from .entities import SuggestionIn, SuggestionOut

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
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Example minimal entity (for tests/demo)
_DB = {"items": [], "suggestions": []}


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
def create_suggestion(s: SuggestionIn):
    if not s.title or len(s.title) > 200:
        raise ApiError("validation_error", "title must be 1..200 chars", 422)
    if not s.text or len(s.text) > 2000:
        raise ApiError("validation_error", "text must be 1..2000 chars", 422)

    new_id = len(_DB["suggestions"]) + 1
    suggestion = {"id": new_id, **s.model_dump()}
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
def update_suggestion(suggestion_id: int, s: SuggestionIn):
    for idx, sg in enumerate(_DB["suggestions"]):
        if sg["id"] == suggestion_id:
            updated = {"id": suggestion_id, **s.model_dump()}
            _DB["suggestions"][idx] = updated
            return updated
    raise ApiError("not_found", "suggestion not found", 404)


@app.delete("/suggestions/{suggestion_id}")
def delete_suggestion(suggestion_id: int):
    for idx, sg in enumerate(_DB["suggestions"]):
        if sg["id"] == suggestion_id:
            del _DB["suggestions"][idx]
            return {"status": "deleted"}
    raise ApiError("not_found", "suggestion not found", 404)
