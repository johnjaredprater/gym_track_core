from litestar import Request, Response, Router, delete, get, post
from litestar.datastructures import State
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Exercise, ExercisesCreate
from app.user_auth import AccessToken, User


@get(path="")
async def get_exercises(
    db_session: AsyncSession,
) -> list[Exercise]:
    """Get all exercises"""
    return list(await db_session.scalars(select(Exercise)))


@post(path="")
async def post_exercise(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: ExercisesCreate,
) -> list[Exercise]:
    """Post an exercise"""
    user = request.user
    if not user.admin:
        raise Exception("User does not have admin status")

    exercises = [
        Exercise(
            name=exercise.name,
            video_link=exercise.video_link,
        )
        for exercise in data.exercises
    ]
    try:
        for exercise in exercises:
            db_session.add(exercise)
        await db_session.commit()
    except IntegrityError:
        raise Exception("An exercise with that name already exists")

    for exercise in exercises:
        await db_session.refresh(exercise)
    return exercises


@delete(path="/{exercise_id:int}", status_code=200)
async def delete_exercise(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    exercise_id: int,
) -> Response | None:
    """Delete an exercise for a particular user."""
    user = request.user
    if not user.admin:
        return Response({"error": "User does not have admin status"}, status_code=401)

    try:
        exercise = await db_session.scalar(select(Exercise).filter_by(id=exercise_id))
        if not exercise:
            return Response(
                {"error": f"Exercise with ID {exercise_id} not found"}, status_code=404
            )

        await db_session.delete(exercise)
        await db_session.commit()

        return Response(
            {"message": f"Exercise with ID {exercise_id} has been deleted."},
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"Exercise with ID {exercise_id} not found"}, status_code=404
        )
    except StatementError as e:
        print(f"Error during commit: {e}")
        return Response(
            {"error": f"Exercise ID {exercise_id} was invalid"}, status_code=422
        )


exercise_router = Router(
    path="/api/exercises",
    route_handlers=[
        post_exercise,
        delete_exercise,
        get_exercises,
    ],
    tags=["exercises"],
)
