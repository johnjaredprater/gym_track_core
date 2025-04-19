import json

from advanced_alchemy.extensions.litestar.plugins.init.config.engine import EngineConfig
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.exercises import Exercise

DB_NAME = "gymtrack"


try:
    with open("/mnt/db-secrets/username", "r") as f:
        db_username = f.read()
    with open("/mnt/db-secrets/password", "r") as f:
        db_password = f.read()
    with open("/mnt/db-secrets/host", "r") as f:
        host = f.read()
    with open("/mnt/db-secrets/port", "r") as f:
        port = f.read()

except Exception as e:
    print(e)
    print("Connecting to local DB instead")
    db_username = "root"
    db_password = "mypass"
    host = "host.docker.internal"  # WSL2 docker engine
    port = "3306"


DATABASE_URL_WITHOUT_DB = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}"
DATABASE_URL = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}/{DB_NAME}"
session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config=session_config,
    engine_config=EngineConfig(echo=True, pool_pre_ping=True),
)


async def on_startup() -> None:
    """Adds some dummy data if no data is present."""

    async with create_async_engine(DATABASE_URL_WITHOUT_DB, echo=False).begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))

    async with sqlalchemy_config.get_engine().begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)

    async with sqlalchemy_config.get_session() as session:
        statement = select(func.count()).select_from(Exercise)
        count = await session.execute(statement)
        if not count.scalar():
            with open("app/data/default_exercises.json") as f:
                default_exercises = json.load(f)
            for index, exercise in enumerate(default_exercises, start=1):
                name, video_link = exercise.values()
                session.add(Exercise(id=index, name=name, video_link=video_link))

        await session.commit()
