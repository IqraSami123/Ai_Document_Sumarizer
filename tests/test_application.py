import fitz
from fastapi.testclient import TestClient

from app.main import create_app
from app.config import Settings, get_settings


def make_pdf(text: str = "A small test document.") -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def client() -> TestClient:
    return TestClient(create_app())


def test_home_page_and_health() -> None:
    with client() as test_client:
        home = test_client.get("/")
        health = test_client.get("/health")
    assert home.status_code == 200
    assert 'id="status-panel"' in home.text
    assert health.json() == {"status": "ok"}
    assert health.headers["x-content-type-options"] == "nosniff"


def test_rejects_invalid_uploads() -> None:
    cases = [
        ("notes.txt", b"hello", "text/plain", 415),
        ("renamed.pdf", b"not a pdf", "application/pdf", 415),
        ("empty.pdf", b"", "application/pdf", 422),
        ("broken.pdf", b"%PDF-broken", "application/pdf", 422),
    ]
    with client() as test_client:
        for filename, content, mime_type, expected_status in cases:
            response = test_client.post("/api/summarize", files={"file": (filename, content, mime_type)})
            assert response.status_code == expected_status
            assert "request_id" in response.json()


def test_rejects_oversized_upload() -> None:
    content = b"%PDF-" + (b"0" * (20 * 1024 * 1024))
    with client() as test_client:
        response = test_client.post("/api/summarize", files={"file": ("large.pdf", content, "application/pdf")})
    assert response.status_code == 413


def test_pdf_is_summarized_when_provider_succeeds(monkeypatch) -> None:
    async def fake_summarize(_: str, __: object) -> str:
        return "A concise generated summary."

    monkeypatch.setattr("app.routes.summary.summarize", fake_summarize)
    with client() as test_client:
        response = test_client.post(
            "/api/summarize",
            files={"file": ("document.pdf", make_pdf(), "application/pdf")},
        )
    assert response.status_code == 200
    assert response.json()["summary"] == "A concise generated summary."


def test_missing_openai_key_is_safe() -> None:
    with client() as test_client:
        response = test_client.post(
            "/api/summarize",
            files={"file": ("document.pdf", make_pdf(), "application/pdf")},
        )
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI is not configured. Please contact the administrator."


def test_configured_api_key_protects_api(monkeypatch) -> None:
    monkeypatch.setenv("API_ACCESS_KEY", "test-secret")
    get_settings.cache_clear()
    try:
        with client() as test_client:
            response = test_client.post("/api/summarize")
        assert response.status_code == 401
        assert response.json()["detail"] == "A valid API key is required."
    finally:
        get_settings.cache_clear()


def test_blank_optional_secrets_are_unset() -> None:
    settings = Settings(openai_api_key="", api_access_key="")
    assert settings.openai_api_key is None
    assert settings.api_access_key is None
