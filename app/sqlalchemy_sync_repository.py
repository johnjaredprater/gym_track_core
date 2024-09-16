from __future__ import annotations

from contextlib import contextmanager
import attrs
import sqlalchemy
from sqlalchemy import func, select, String, Integer, Column
from sqlalchemy.orm import Mapped, registry
import mariadb
from litestar import get

from attrs import define
import mariadb.cursors
from sqlalchemy import Table
from sqlalchemy.orm import Mapped
import json


mapper_registry = registry()

@mapper_registry.mapped
@define(slots=False)
class Exercise:
    __table__ = Table(
        "exercises",
        mapper_registry.metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(length=100), nullable=False, unique=True),
        Column("video_link", String(length=100)),
    )

    id: Mapped[int]
    name: Mapped[str]
    video_link: Mapped[str | None] = None


# # The `AuditBase` class includes the same UUID` based primary key (`id`) and 2
# # additional columns: `created` and `updated`. `created` is a timestamp of when the
# # record created, and `updated` is the last time the record was modified.
# class WorkoutModel(UUIDAuditBase):
#     __tablename__ = "workout"  #  type: ignore[assignment]
#     date: Mapped[date | None]
#     title: Mapped[str]
#     user: 
#     exercise_id: Mapped[UUID] = mapped_column(ForeignKey("exercise.id"))
#     # exercise: Mapped[ExerciseModel] = relationship(lazy="joined", innerjoin=True, viewonly=True)
#     sets: Mapped[int]
#     reps: Mapped[int]
#     weight: Mapped[float]
#     rpe: Mapped[int | None]


# user="root"
# password="mypass"
# host="0.0.0.0"
# port=3306
dbname="gymtrack"
driver="mariadbconnector"
# session_config=SyncSessionConfig(expire_on_commit=False)
# sqlalchemy_config = SQLAlchemySyncConfig(
#     connection_string=f"mariadb+{driver}://{user}:{password}@{host}:{port}/{dbname}", session_config=session_config, create_all=True
# )

with open("/mnt/secrets-store/dbusername", "r") as f:
    db_username = f.read()

with open("/mnt/secrets-store/dbpassword", "r") as f:
    db_password = f.read()

host="gym-track-core.cz0ki8esooam.eu-north-1.rds.amazonaws.com"
port=3306

# engine = sqlalchemy.create_engine(f"mariadb+{driver}://{user}:{password}@{host}:{port}/{dbname}")
engine = sqlalchemy.create_engine(f"mariadb+{driver}://{db_username}:{db_password}@{host}:{port}/{dbname}")
mapper_registry.metadata.create_all(engine)


def on_startup() -> None:
    """Adds some dummy data if no data is present."""
    with connect_sqlalchemy_db() as session:

        statement = select(func.count()).select_from(Exercise)
        count = session.execute(statement)
        if not count.scalar():
            with open("app/data/default_exercises.json") as f:
                default_exercises = json.load(f)
            for index, exercise in enumerate(default_exercises, start=1):
                name, video_link = exercise.values()
                session.add(
                    Exercise(id=index, name=name, video_link=video_link)
                )


@contextmanager
def connect_sqlalchemy_db() -> sqlalchemy.Session:
    try:
        Session = sqlalchemy.orm.sessionmaker()
        Session.configure(bind=engine)
        session = Session()
        yield session
        session.commit() 
    except mariadb.Error as e:
        session.rollback()
        raise
    finally:
        session.close()


@get(path="/api/exercises")
async def get_exercises() -> list[Exercise]:
    """Interact with SQLAlchemy engine and session."""

    with connect_sqlalchemy_db() as session:
        exercises = session.query(Exercise)
        return [attrs.asdict(exercise) for exercise in exercises.all()]
