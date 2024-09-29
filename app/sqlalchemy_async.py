from __future__ import annotations

import json

from litestar import get
from litestar.contrib.sqlalchemy.base import BigIntBase, UUIDBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy import Column, String, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base

dbname = "gymtrack"
driver = "mariadbconnector"

try:
    with open("/mnt/db-secrets/username", "r") as f:
        db_username = f.read()
    with open("/mnt/db-secrets/password", "r") as f:
        db_password = f.read()

    host = "gym-track-core.cziymq0g8e9k.eu-west-2.rds.amazonaws.com"
    port = 3306

except Exception as e:
    print(e)
    print("Connecting to local DB instead")
    db_username = "root"
    db_password = "mypass"
    host = "0.0.0.0"
    port = 3306


DATABASE_URL_WITHOUT_DB = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}"
DATABASE_URL = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}/{dbname}"
session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL, session_config=session_config
)


Base = declarative_base()


class Exercise(BigIntBase):
    __tablename__ = "exercises"

    name = Column("name", String(length=100), nullable=False, unique=True)
    video_link = Column("video_link", String(length=100))


# # The `AuditBase` class includes the same UUID` based primary key (`id`) and 2
# # additional columns: `created` and `updated`. `created` is a timestamp of when the
# # record created, and `updated` is the last time the record was modified.
# class WorkoutModel(UUIDAuditBase):
#     __tablename__ = "workout"  #  type: ignore[assignment]
#     title: Mapped[str]
#     user:
#     exercise_id: Mapped[UUID] = mapped_column(ForeignKey("exercise.id"))
#     # exercise: Mapped[ExerciseModel] = relationship(lazy="joined", innerjoin=True, viewonly=True)
#     sets: Mapped[int]
#     reps: Mapped[int]
#     weight: Mapped[float]
#     rpe: Mapped[int | None]


async def on_startup() -> None:
    """Adds some dummy data if no data is present."""

    async with create_async_engine(DATABASE_URL_WITHOUT_DB, echo=True).begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {dbname}"))

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


@get(path="/api/exercises")
async def get_exercises(db_session: AsyncSession) -> list[Exercise]:
    """Interact with SQLAlchemy engine and session."""
    return list(await db_session.scalars(select(Exercise)))
