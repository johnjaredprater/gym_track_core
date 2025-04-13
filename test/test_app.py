import pytest
from litestar.testing import AsyncTestClient
from sqlalchemy import inspect

from app.models.exercises_and_workouts import Exercise


@pytest.mark.asyncio
async def test_example(test_client: AsyncTestClient, db_session, db_engine):
    """Example test."""
    response = await test_client.get("/api/exercises")

    async with db_engine.connect() as conn:
        # Get inspector using run_sync
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = await conn.run_sync(lambda _: inspector.get_table_names())
        print("Tables:", tables)

    # Create test data
    exercise = Exercise(name="Push-up")
    db_session.add(exercise)
    await db_session.commit()

    # Test API response
    response = await test_client.get("/api/exercises")
    assert response.status_code == 200
    data = response.json()
    print(f"{response.json()=}")
    assert len(data) == 1
    assert data[0]["name"] == "Push-up"
