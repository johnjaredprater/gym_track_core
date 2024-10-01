import pytest
from litestar.status_codes import HTTP_200_OK
from litestar.testing import AsyncTestClient

from app.main import app


@pytest.mark.asyncio
async def test_version():
    async with AsyncTestClient(app=app) as client:
        response = await client.get("/api/version")
        assert response.status_code == HTTP_200_OK
