from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient

from app.main import app


def test_version():
    with TestClient(app=app) as client:
        response = client.get("/api/version")
        assert response.status_code == HTTP_200_OK
