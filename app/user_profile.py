from litestar import Request, Response, Router, delete, get, patch, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound, StatementError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import UserProfileCreate, UserProfileORM, UserProfileUpdate
from app.user_auth import AccessToken, User


@get(path="")
async def get_user_profile(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
) -> UserProfileORM:
    """Get a user's profile"""
    user = request.user
    user_profile = await db_session.scalar(
        select(UserProfileORM).filter_by(user_id=user.user_id)
    )

    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    return user_profile


@post(path="")
async def post_user_profile(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: UserProfileCreate,
) -> UserProfileORM:
    """Post an exercises"""
    user = request.user
    user_profile = UserProfileORM(
        user_id=user.user_id,
        age=data.age,
        gender=data.gender,
        number_of_days=data.number_of_days,
        workout_duration=data.workout_duration,
        fitness_level=data.fitness_level,
        goal=data.goal,
        injury_description=data.injury_description,
    )
    try:
        db_session.add(user_profile)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"An user profile with user_id {user.user_id} already exists",
        )

    await db_session.refresh(user_profile)
    return user_profile


@patch(path="")
async def patch_user_profile(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: UserProfileUpdate,
) -> UserProfileORM:
    """Patch a user's profile"""
    user = request.user
    user_profile = await db_session.scalar(
        select(UserProfileORM).filter_by(user_id=user.user_id)
    )

    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    for field, value in data.model_dump().items():
        if value is not None:
            setattr(user_profile, field, value)

    await db_session.commit()

    return user_profile


@delete(path="/", status_code=200)
async def delete_user_profile(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
) -> Response | None:
    """Delete a user's profile."""
    user = request.user

    try:
        user_profile = await db_session.scalar(
            select(UserProfileORM).filter_by(user_id=user.user_id)
        )
        if not user_profile:
            return Response(
                {"error": f"User profile with ID {user.user_id} not found"},
                status_code=404,
            )

        await db_session.delete(user_profile)
        await db_session.commit()

        return Response(
            {"message": f"User profile with ID {user.user_id} has been deleted."},
            status_code=200,
        )
    except NoResultFound:
        return Response(
            {"error": f"User profile with ID {user.user_id} not found"}, status_code=404
        )
    except StatementError as e:
        print(f"Error during commit: {e}")
        return Response(
            {"error": f"User profile with ID {user.user_id} was invalid"},
            status_code=422,
        )


user_profile_router = Router(
    path="/api/user_profile",
    route_handlers=[
        get_user_profile,
        post_user_profile,
        patch_user_profile,
        delete_user_profile,
    ],
    tags=["user_profile"],
)
