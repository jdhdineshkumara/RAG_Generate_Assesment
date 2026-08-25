from fastapi.testclient import TestClient

from app.api.dependencies import get_database_service
from app.main import app


class FakeDatabaseService:
    def __init__(self):
        self.called = False

    def clear_database(self):
        self.called = True


def test_clear_database_returns_no_content():
    service = FakeDatabaseService()
    app.dependency_overrides[get_database_service] = lambda: service
    try:
        response = TestClient(app).delete("/api/v1/database")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert service.called is True
