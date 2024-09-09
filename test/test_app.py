from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient

from gym_track_core.app import app


def test_health_check():
    with TestClient(app=app) as client:
        response = client.get("/")
        assert response.status_code == HTTP_200_OK
