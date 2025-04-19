from litestar import Request, Response, delete, get, patch, post
from litestar.datastructures import State
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercises_and_workouts import (
    ExerciseResult,
    ExerciseResultCreate,
    ExerciseResultUpdate,
)
from app.user_auth import AccessToken, User


@post(path="/api/workouts")
async def post_workouts(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: ExerciseResultCreate,
) -> str:
    """Create a workout for a particular user."""
    user = request.user
    workout = ExerciseResult(
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
            select(ExerciseResult).filter_by(id=workout_id, user_id=user.user_id)
        )

        if not workout:
            return Response(
                {"error": f"ExerciseResult with ID {workout_id} not found"},
                status_code=404,
            )

        await db_session.delete(workout)
        await db_session.commit()
        return Response(
            {"message": f"ExerciseResult with ID {workout_id} has been deleted."},
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"ExerciseResult with ID {workout_id} not found"}, status_code=404
        )
    except StatementError:
        return Response(
            {"error": f"ExerciseResult ID {workout_id} was invalid"}, status_code=422
        )


@patch(path="/api/workouts/{workout_id:str}", status_code=200)
async def update_workouts(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    workout_id: str,
    data: ExerciseResultUpdate,
) -> Response[None | dict[str, str]]:
    """Delete a workout for a particular user."""
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
                update(ExerciseResult)
                .where(
                    ExerciseResult.id == workout_id,
                    ExerciseResult.user_id == user.user_id,
                )
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
                {"message": f"ExerciseResult with ID {workout_id} has been updated."},
                status_code=200,
            )
        return Response(
            {
                "message": f"Nothing to change for to ExerciseResult with ID {workout_id}."
            },
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"ExerciseResult with ID {workout_id} not found"}, status_code=404
        )


@get(path="/api/workouts")
async def get_workouts(
    db_session: AsyncSession, request: Request[User, AccessToken, State]
) -> list[ExerciseResult]:
    """Get workouts for a particular user."""
    user = request.user
    workouts = list(
        await db_session.scalars(
            select(ExerciseResult).where(ExerciseResult.user_id == user.user_id)
        )
    )
    return workouts


@get(path="/api/workouts/{workout_id:str}")
async def get_workout(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    workout_id: str,
) -> ExerciseResult:
    """Get workouts for a particular user."""
    user = request.user
    workout = await db_session.scalar(
        select(ExerciseResult).where(
            ExerciseResult.id == workout_id, ExerciseResult.user_id == user.user_id
        )
    )
    if not workout:
        raise Exception(f"ExerciseResult with ID {workout_id} not found")
    return workout
