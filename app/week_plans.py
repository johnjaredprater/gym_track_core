import json

import anthropic
from anthropic.types import TextBlock
from litestar import Request, Router, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.claude_prompts import SCREENING_PROMPT, workout_plan_system_prompt
from app.models.models import (
    Exercise,
    ScreeningResult,
    ScreeningStatus,
    UserProfileORM,
    WeekPlan,
)
from app.user_auth import AccessToken, User


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
) -> WeekPlan:
    """Create a workout plan"""
    # TODO: Make this a dependency and auth properly
    anthropic_client = anthropic.Anthropic()

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
    exercise_names = [str(exercise.name) for exercise in exercises]

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
    return WeekPlan.model_validate(json.loads(content))


week_plan_router = Router(
    path="/api/week_plans",
    route_handlers=[
        post_week_plan,
    ],
    tags=["week_plans"],
)
