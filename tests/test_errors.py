from fastapi.testclient import TestClient

import app.main as app_main
from app.main import app

client = TestClient(app)


def setup_module(module):
    """Очистить in-memory хранилища перед запуском тестов модуля."""
    # Очистим items/suggestions и служебные структуры, если они есть
    app_main._DB["items"].clear()
    app_main._DB["suggestions"].clear()
    if hasattr(app_main, "_TOKENS"):
        app_main._TOKENS.clear()
    if hasattr(app_main, "_RATE_LIMIT"):
        app_main._RATE_LIMIT.clear()


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404, r.text
    body = r.json()
    assert "error" in body and body["error"]["code"] == "not_found"
    assert "message" in body["error"]


def test_validation_error():
    # отправляем пустое имя — в приложении это приводит к ApiError с кодом validation_error
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422, r.text
    body = r.json()
    assert "error" in body and body["error"]["code"] == "validation_error"
    assert "message" in body["error"]
