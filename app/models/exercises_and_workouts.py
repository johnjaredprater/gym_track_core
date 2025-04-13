from __future__ import annotations

from datetime import datetime, timezone

from advanced_alchemy.types import DateTimeUTC
from litestar.contrib.sqlalchemy.base import BigIntBase, UUIDAuditBase
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Exercise(BigIntBase):
    __tablename__ = "exercises"

    name = Column("name", String(length=100), nullable=False, unique=True)
    video_link = Column("video_link", String(length=100))

    workouts: Mapped[list[Workout]] = relationship(
        back_populates="exercise", lazy="noload"
    )


class ExerciseCreate(BaseModel):
    name: str
    video_link: str | None = None


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
    exercise_id: int | None = None
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
