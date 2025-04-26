import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_db_setup(db_engine):
    """Example test."""
    async with db_engine.connect() as conn:
        # Get inspector using run_sync
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        tables = await conn.run_sync(lambda _: inspector.get_table_names())

    assert set(tables) == {"exercises", "exercise_results", "user_profiles"}
