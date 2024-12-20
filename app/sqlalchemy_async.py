from __future__ import annotations

import json
from datetime import datetime, timezone

from advanced_alchemy.extensions.litestar.plugins.init.config.engine import EngineConfig
from advanced_alchemy.types import DateTimeUTC
from litestar import Request, Response, delete, get, patch, post
from litestar.contrib.sqlalchemy.base import BigIntBase, UUIDAuditBase, UUIDBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.datastructures import State
from pydantic import BaseModel
from sqlalchemy import (
    BigInteger,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
    select,
    text,
    update,
)
from sqlalchemy.exc import NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.user_auth import AccessToken, User

DB_NAME = "gymtrack"
driver = "mariadbconnector"

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
    host = "0.0.0.0"
    port = "3306"


DATABASE_URL_WITHOUT_DB = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}"
DATABASE_URL = f"mysql+aiomysql://{db_username}:{db_password}@{host}:{port}/{DB_NAME}"
session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config=session_config,
    engine_config=EngineConfig(echo=True, pool_pre_ping=True),
)


class Exercise(BigIntBase):
    __tablename__ = "exercises"

    name = Column("name", String(length=100), nullable=False, unique=True)
    video_link = Column("video_link", String(length=100))

    workouts: Mapped[list[Workout]] = relationship(
        back_populates="exercise", lazy="noload"
    )


class Workout(UUIDAuditBase):
    __tablename__ = "workouts"

    user_id = Column("user_id", String(length=100), nullable=False)

    exercise_id = Column(BigInteger, ForeignKey("exercises.id"))
    exercise: Mapped[Exercise] = relationship(back_populates="workouts", lazy="joined")

    sets = Column("sets", Integer, nullable=False)
    reps = Column("reps", Integer, nullable=False)
    weight = Column("weight", Float, nullable=False)
    rpe = Column("rpe", Integer())

    date: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class WorkoutCreate(BaseModel):
    exercise_id: int
    sets: int
    reps: int
    weight: float
    rpe: int | None = None
    date: datetime | None = None


class WorkoutUpdate(BaseModel):
    exercise_id: int | None = None
    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    rpe: int | None = None
    date: datetime | None = None


async def on_startup() -> None:
    """Adds some dummy data if no data is present."""

    async with create_async_engine(DATABASE_URL_WITHOUT_DB, echo=True).begin() as conn:
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


@get(path="/api/exercises")
async def get_exercises(db_session: AsyncSession) -> list[Exercise]:
    """Get all exercises"""
    return list(await db_session.scalars(select(Exercise)))


@post(path="/api/workouts")
async def post_workouts(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: WorkoutCreate,
) -> str:
    """Create a workout for a particular user."""
    user = request.user
    workout = Workout(
        user_id=user.user_id,
        exercise_id=data.exercise_id,
        sets=data.sets,
        reps=data.reps,
        weight=data.weight,
        rpe=data.rpe,
        date=data.date,
    )
    db_session.add(workout)
    await db_session.commit()
    await db_session.refresh(workout)
    return str(workout.id)


@delete(path="/api/workouts/{workout_id:str}", status_code=200)
async def delete_workouts(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    workout_id: str,
) -> Response | None:
    """Create a workout for a particular user."""
    try:
        user = request.user
        workout = await db_session.scalar(
            select(Workout).filter_by(id=workout_id, user_id=user.user_id)
        )

        if not workout:
            return Response(
                {"error": f"Workout with ID {workout_id} not found"}, status_code=404
            )

        await db_session.delete(workout)
        await db_session.commit()
        return Response(
            {"message": f"Workout with ID {workout_id} has been deleted."},
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"Workout with ID {workout_id} not found"}, status_code=404
        )
    except StatementError:
        return Response(
            {"error": f"Workout ID {workout_id} was invalid"}, status_code=422
        )


@patch(path="/api/workouts/{workout_id:str}", status_code=200)
async def update_workouts(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    workout_id: str,
    data: WorkoutUpdate,
) -> Response[None | dict[str, str]]:
    """Create a workout for a particular user."""
    try:
        user = request.user

        if set(data.model_dump().values()) != {None}:
            print(
                {
                    field: value
                    for field, value in data.model_dump().items()
                    if value is not None
                }
            )
            await db_session.execute(
                update(Workout)
                .where(Workout.id == workout_id, Workout.user_id == user.user_id)
                .values(
                    **{
                        field: value
                        for field, value in data.model_dump().items()
                        if value is not None
                    }
                )
            )

            await db_session.commit()
            return Response(
                {"message": f"Workout with ID {workout_id} has been updated."},
                status_code=200,
            )
        return Response(
            {"message": f"Nothing to change for to Workout with ID {workout_id}."},
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"Workout with ID {workout_id} not found"}, status_code=404
        )


@get(path="/api/workouts")
async def get_workouts(
    db_session: AsyncSession, request: Request[User, AccessToken, State]
) -> list[Workout]:
    """Get workouts for a particular user."""
    user = request.user
    workouts = list(
        await db_session.scalars(select(Workout).where(Workout.user_id == user.user_id))
    )
    return workouts


@get(path="/api/workouts/{workout_id:str}")
async def get_workout(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    workout_id: str,
) -> Workout:
    """Get workouts for a particular user."""
    user = request.user
    workout = await db_session.scalar(
        select(Workout).where(Workout.id == workout_id, Workout.user_id == user.user_id)
    )
    if not workout:
        raise Exception(f"Workout with ID {workout_id} not found")
    return workout
