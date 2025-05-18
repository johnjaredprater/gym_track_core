from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from advanced_alchemy.types import GUID, DateTimeUTC
from litestar.contrib.sqlalchemy.base import BigIntBase, UUIDAuditBase, orm_registry
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import BigInteger, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Database Models ------------------------------------------------------------


class Base(DeclarativeBase):
    registry = orm_registry


class Exercise(BigIntBase):
    __tablename__ = "exercises"

    name = Column("name", String(length=100), nullable=False, unique=True)
    video_link = Column("video_link", String(length=100))

    exercise_results: Mapped[list[ExerciseResult]] = relationship(
        back_populates="exercise", lazy="noload"
    )


class ExercisesCreate(BaseModel):
    exercises: list[ExerciseCreate]


class ExerciseCreate(BaseModel):
    name: str
    video_link: str | None = None


class ExerciseResult(UUIDAuditBase):
    __tablename__ = "exercise_results"

    user_id = Column("user_id", String(length=100), nullable=False)

    exercise_id = Column(BigInteger, ForeignKey("exercises.id"))
    exercise: Mapped[Exercise] = relationship(
        back_populates="exercise_results", lazy="joined"
    )

    sets = Column("sets", Integer, nullable=False)
    reps = Column("reps", Integer, nullable=False)
    weight = Column("weight", Float, nullable=False)
    rpe = Column("rpe", Integer())

    date: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserProfileORM(Base):
    __tablename__ = "user_profiles"

    user_id = Column("user_id", String(length=100), primary_key=True, nullable=False)
    age = Column("age", Integer, nullable=False)
    gender = Column("gender", String(length=12), nullable=False)
    number_of_days = Column("number_of_days", Integer, nullable=False)
    workout_duration = Column("workout_duration", Integer, nullable=False)
    fitness_level = Column("fitness_level", String(length=24), nullable=False)
    goal = Column("goal", String(length=1_000), nullable=False)
    injury_description = Column("injury_description", String(length=1_000))


class WeekPlanORM(UUIDAuditBase):
    __tablename__ = "week_plans"

    user_id = Column("user_id", String(length=100), nullable=False)
    summary = Column("summary", String(length=1_000), nullable=False)
    complete = Column("complete", Boolean, nullable=False, default=False)
    workout_plans: Mapped[list[WorkoutPlanORM]] = relationship(
        back_populates="week_plan", lazy="joined"
    )


class WorkoutPlanORM(UUIDAuditBase):
    __tablename__ = "workout_plans"

    user_id = Column("user_id", String(length=100), nullable=False)
    title = Column("title", String(length=100), nullable=False)
    complete = Column("complete", Boolean, nullable=False, default=False)
    week_plan_id = Column(GUID, ForeignKey("week_plans.id"), nullable=False)
    week_plan: Mapped[WeekPlanORM] = relationship(
        back_populates="workout_plans", lazy="noload"
    )
    warm_ups: Mapped[list[WarmUpPlanORM]] = relationship(
        back_populates="workout_plan", lazy="joined"
    )
    exercise_plans: Mapped[list[ExercisePlanORM]] = relationship(
        back_populates="workout_plan", lazy="joined"
    )


class WarmUpPlanORM(UUIDAuditBase):
    __tablename__ = "warm_up_plans"

    user_id = Column("user_id", String(length=100), nullable=False)
    workout_plan_id = Column(GUID, ForeignKey("workout_plans.id"), nullable=False)

    workout_plan: Mapped[WorkoutPlanORM] = relationship(
        back_populates="warm_ups", lazy="noload"
    )
    description = Column("description", String(length=1_000), nullable=False)


class ExercisePlanORM(UUIDAuditBase):
    __tablename__ = "exercise_plans"

    user_id = Column("user_id", String(length=100), nullable=False)
    workout_plan_id = Column(GUID, ForeignKey("workout_plans.id"), nullable=False)
    workout_plan: Mapped[WorkoutPlanORM] = relationship(
        back_populates="exercise_plans", lazy="noload"
    )
    exercise_name = Column("exercise_name", String(length=100), nullable=False)
    exercise_id = Column("exercise_id", Integer, nullable=False)

    complete = Column("complete", Boolean, nullable=False, default=False)

    exercise_result_id = Column(
        GUID, ForeignKey("exercise_results.id"), nullable=True, default=None
    )
    exercise_result: Mapped[ExerciseResult | None] = relationship(
        lazy="joined", foreign_keys=[exercise_result_id]
    )
    weight = Column("weight", Float, nullable=True)
    reps = Column("reps", Integer, nullable=True)
    sets = Column("sets", Integer, nullable=True)
    rpe = Column("rpe", Integer, nullable=True)


# App Data Models ------------------------------------------------------------


class ExerciseResultCreate(BaseModel):
    exercise_id: int | None = None
    sets: int
    reps: int
    weight: float
    rpe: int | None = None
    date: datetime | None = None


class ExerciseResultUpdate(BaseModel):
    exercise_id: int | None = None
    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    rpe: int | None = None
    date: datetime | None = None


class WeekPlansResponse(BaseModel):
    week_plans: list[WeekPlan]


class WeekPlan(BaseModel):
    summary: str
    complete: bool = False
    workouts: list[WorkoutPlan] = Field(alias="workout_plans")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WeekPlanUpdate(BaseModel):
    complete: bool


class WorkoutPlan(BaseModel):
    title: str
    complete: bool = False
    warm_ups: list[WarmUpPlan]
    exercises: list[ExercisePlan] = Field(alias="exercise_plans")

    model_config = {"from_attributes": True, "populate_by_name": True}


class WarmUpPlan(BaseModel):
    description: str

    model_config = {"from_attributes": True}


class ExercisePlan(BaseModel):
    exercise: str = Field(alias="exercise_name")
    reps: int | None = None
    sets: int | None = None
    weight: float | None = None
    rpe: int | None = None
    complete: bool = False

    model_config = {"from_attributes": True, "populate_by_name": True}


class ScreeningStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"


class ScreeningResult(BaseModel):
    status: ScreeningStatus
    reason: str | None = None


class Gender(str, Enum):
    male = "male"
    female = "female"


class FitnessLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class UserProfileCreate(BaseModel):
    age: int
    gender: Gender
    number_of_days: int
    workout_duration: int
    fitness_level: FitnessLevel
    goal: str
    injury_description: str | None = None


class UserProfileUpdate(BaseModel):
    age: int | None = None
    gender: Gender | None = None
    number_of_days: int | None = None
    workout_duration: int | None = None
    fitness_level: FitnessLevel | None = None
    goal: str | None = None
    injury_description: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_present(self) -> "UserProfileUpdate":
        if all(field is None for field in self.model_fields_set):
            raise ValueError("At least one field must be non-None")
        return self
