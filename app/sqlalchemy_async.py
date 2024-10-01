from __future__ import annotations

import json

from litestar import Request, Response, delete, get, post
from litestar.contrib.sqlalchemy.base import BigIntBase, UUIDAuditBase, UUIDBase
from litestar.contrib.sqlalchemy.plugins import (
    AsyncSessionConfig,
    EngineConfig,
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
)
from sqlalchemy.exc import NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, relationship

from app.user_auth import AccessToken, User

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


class WorkoutCreate(BaseModel):
    exercise_id: int
    sets: int
    reps: int
    weight: int
    rpe: int | None = None


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
        rpe=data.weight,
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
        workout = (
            await db_session.scalars(
                select(Workout).filter_by(id=workout_id, user_id=user.user_id)
            )
        ).first()

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


@get(path="/api/workouts")
async def get_workouts(
    db_session: AsyncSession, request: Request[User, AccessToken, State]
) -> list[Workout]:
    """Get workouts for a particular user."""
    user = request.user
    return list(
        await db_session.scalars(select(Workout).where(Workout.user_id == user.user_id))
    )
