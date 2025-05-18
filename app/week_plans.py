import json
from uuid import UUID

import anthropic
from anthropic.types import TextBlock
from litestar import Request, Router, get, patch, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.claude_prompts import SCREENING_PROMPT, workout_plan_system_prompt
from app.models.models import (
    Exercise,
    ExercisePlanORM,
    ScreeningResult,
    ScreeningStatus,
    UserProfileORM,
    WarmUpPlanORM,
    WeekPlan,
    WeekPlanORM,
    WeekPlansResponse,
    WeekPlanUpdate,
    WorkoutPlanORM,
)
from app.user_auth import AccessToken, User


async def provide_anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


class UserPrompt(BaseModel):
    user_prompt: str


def _create_prompt_from_user_profile(user_profile: UserProfileORM) -> str:
    return f"""
    My gender is {user_profile.gender}.
    I am {user_profile.age} years old.
    My fitness level is {user_profile.fitness_level}.
    My goals are the following:
    {user_profile.goal}
    I would like a workout plan with {user_profile.number_of_days} days.
    """ + (
        f"I have the following injury description: {user_profile.injury_description}."
        if str(user_profile.injury_description)
        else ""
    )


@post(path="")
async def post_week_plan(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    anthropic_client: anthropic.Anthropic,
) -> WeekPlan:
    """Create a workout plan"""

    user = request.user
    user_profile = await db_session.scalar(
        select(UserProfileORM).where(UserProfileORM.user_id == request.user.user_id)
    )
    if not user_profile:
        raise HTTPException(status_code=412, detail="User profile not found")

    screening_message = anthropic_client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=8_000,
        temperature=1,
        system=SCREENING_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _create_prompt_from_user_profile(user_profile),
                    }
                ],
            }
        ],
    )
    screening_text_block = screening_message.content[-1]
    assert isinstance(screening_text_block, TextBlock)
    screening_content = screening_text_block.text
    screening_result = ScreeningResult.model_validate(json.loads(screening_content))

    if screening_result.status == ScreeningStatus.rejected and screening_result.reason:
        raise HTTPException(
            status_code=400,
            detail=screening_result.reason,
        )

    assert screening_result.status == ScreeningStatus.accepted

    exercises = await db_session.scalars(select(Exercise))
    exercise_name_to_id = {str(exercise.name): exercise.id for exercise in exercises}
    exercise_names = list(exercise_name_to_id.keys())

    message = anthropic_client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=12_000,
        temperature=1,
        system=workout_plan_system_prompt(exercise_names),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _create_prompt_from_user_profile(user_profile),
                    }
                ],
            }
        ],
    )
    text_block = message.content[-1]
    assert isinstance(text_block, TextBlock)
    content = text_block.text

    week_plan_response = WeekPlan.model_validate(json.loads(content))

    week_plan_orm = WeekPlanORM(
        workout_plans=[
            WorkoutPlanORM(
                title=workout_plan.title,
                user_id=user.user_id,
                warm_ups=[
                    WarmUpPlanORM(
                        description=warm_up.description,
                        user_id=user.user_id,
                    )
                    for warm_up in workout_plan.warm_ups
                ],
                exercise_plans=[
                    ExercisePlanORM(
                        exercise_name=exercise.exercise,
                        exercise_id=exercise_name_to_id[str(exercise.exercise)],
                        weight=exercise.weight,
                        reps=exercise.reps,
                        sets=exercise.sets,
                        rpe=exercise.rpe,
                        user_id=user.user_id,
                    )
                    for exercise in workout_plan.exercises
                ],
            )
            for workout_plan in week_plan_response.workouts
        ],
        user_id=user.user_id,
        summary=week_plan_response.summary,
    )
    db_session.add(week_plan_orm)

    await db_session.commit()

    return week_plan_response


@get(path="")
async def get_week_plans(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
) -> WeekPlansResponse:
    """Get all workout plans"""
    user = request.user

    query = (
        select(WeekPlanORM)
        .options(
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.warm_ups
            ),
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.exercise_plans
            ),
        )
        .where(WeekPlanORM.user_id == user.user_id)
    )
    week_plans = list(await db_session.scalars(query))

    if not week_plans:
        raise HTTPException(status_code=404, detail="Week plans not found")

    return WeekPlansResponse(
        week_plans=[
            WeekPlan.model_validate(week_plan, strict=False) for week_plan in week_plans
        ]
    )


@get(path="/latest")
async def get_latest_week_plan(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
) -> WeekPlan:
    """Get a workout plan"""
    user = request.user

    query = (
        select(WeekPlanORM)
        .options(
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.warm_ups
            ),
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.exercise_plans
            ),
        )
        .where(WeekPlanORM.user_id == user.user_id)
        .order_by(WeekPlanORM.created_at.desc())
        .limit(1)
    )
    week_plan_orm = await db_session.scalar(query)

    if not week_plan_orm:
        raise HTTPException(status_code=404, detail="Week plan not found")

    return WeekPlan.model_validate(week_plan_orm, strict=False)


@patch(path="/{week_plan_id:uuid}")
async def patch_week_plan(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    week_plan_id: UUID,
    data: WeekPlanUpdate,
) -> WeekPlan:
    """Get a workout plan"""

    if data.complete is False:
        raise HTTPException(
            status_code=405, detail="Can't go from complete to incomplete at the moment"
        )

    user = request.user
    query = (
        select(WeekPlanORM)
        .options(
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.warm_ups
            ),
            selectinload(WeekPlanORM.workout_plans).selectinload(
                WorkoutPlanORM.exercise_plans
            ),
        )
        .where(WeekPlanORM.user_id == user.user_id, WeekPlanORM.id == week_plan_id)
    )
    week_plan_orm = await db_session.scalar(query)

    if not week_plan_orm:
        raise HTTPException(status_code=404, detail="Week plan not found")

    setattr(week_plan_orm, "complete", data.complete)
    for workout_plan in week_plan_orm.workout_plans:
        setattr(workout_plan, "complete", data.complete)
        for exercise_plan in workout_plan.exercise_plans:
            setattr(exercise_plan, "complete", data.complete)

    await db_session.commit()
    return WeekPlan.model_validate(week_plan_orm, strict=False)


week_plan_router = Router(
    path="/api/week_plans",
    route_handlers=[
        post_week_plan,
        get_week_plans,
        get_latest_week_plan,
        patch_week_plan,
    ],
    tags=["week_plans"],
)
