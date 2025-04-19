from litestar import Request, Response, Router, delete, get, patch, post
from litestar.datastructures import State
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ExerciseResult, ExerciseResultCreate, ExerciseResultUpdate
from app.user_auth import AccessToken, User


@post(path="")
async def post_exercise_results(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: ExerciseResultCreate,
) -> str:
    """Create an exercise_result for a particular user."""
    user = request.user
    exercise_result = ExerciseResult(
        user_id=user.user_id,
        exercise_id=data.exercise_id,
        sets=data.sets,
        reps=data.reps,
        weight=data.weight,
        rpe=data.rpe,
        date=data.date,
    )
    db_session.add(exercise_result)
    await db_session.commit()
    await db_session.refresh(exercise_result)
    return str(exercise_result.id)


@delete(path="/{exercise_result_id:str}", status_code=200)
async def delete_exercise_results(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    exercise_result_id: str,
) -> Response | None:
    """Create an exercise_result for a particular user."""
    try:
        user = request.user
        exercise_result = await db_session.scalar(
            select(ExerciseResult).filter_by(
                id=exercise_result_id, user_id=user.user_id
            )
        )

        if not exercise_result:
            return Response(
                {"error": f"ExerciseResult with ID {exercise_result_id} not found"},
                status_code=404,
            )

        await db_session.delete(exercise_result)
        await db_session.commit()
        return Response(
            {
                "message": f"ExerciseResult with ID {exercise_result_id} has been deleted."
            },
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"ExerciseResult with ID {exercise_result_id} not found"},
            status_code=404,
        )
    except StatementError:
        return Response(
            {"error": f"ExerciseResult ID {exercise_result_id} was invalid"},
            status_code=422,
        )


@patch(path="/{exercise_result_id:str}", status_code=200)
async def update_exercise_results(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    exercise_result_id: str,
    data: ExerciseResultUpdate,
) -> Response[None | dict[str, str]]:
    """Delete an exercise_result for a particular user."""
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
                    ExerciseResult.id == exercise_result_id,
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
                {
                    "message": f"ExerciseResult with ID {exercise_result_id} has been updated."
                },
                status_code=200,
            )
        return Response(
            {
                "message": f"Nothing to change for to ExerciseResult with ID {exercise_result_id}."
            },
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"ExerciseResult with ID {exercise_result_id} not found"},
            status_code=404,
        )


@get(path="")
async def get_exercise_results(
    db_session: AsyncSession, request: Request[User, AccessToken, State]
) -> list[ExerciseResult]:
    """Get exercise_results for a particular user."""
    user = request.user
    exercise_results = list(
        await db_session.scalars(
            select(ExerciseResult).where(ExerciseResult.user_id == user.user_id)
        )
    )
    return exercise_results


@get(path="/{exercise_result_id:str}")
async def get_exercise_result(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    exercise_result_id: str,
) -> ExerciseResult:
    """Get exercise_results for a particular user."""
    user = request.user
    exercise_result = await db_session.scalar(
        select(ExerciseResult).where(
            ExerciseResult.id == exercise_result_id,
            ExerciseResult.user_id == user.user_id,
        )
    )
    if not exercise_result:
        raise Exception(f"ExerciseResult with ID {exercise_result_id} not found")
    return exercise_result


exercise_result_router = Router(
    path="/api/exercise_results",
    route_handlers=[
        post_exercise_results,
        delete_exercise_results,
        update_exercise_results,
        get_exercise_results,
        get_exercise_result,
    ],
    tags=["exercise_results"],
)
