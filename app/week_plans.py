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
from app.models.models import Exercise, ScreeningResult, ScreeningStatus, WeekPlan
from app.user_auth import AccessToken, User

anthropic_client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
)


class UserPrompt(BaseModel):
    user_prompt: str


@post(path="")
async def post_week_plan(
    db_session: AsyncSession,
    request: Request[User, AccessToken, State],
    data: UserPrompt,
) -> WeekPlan:
    """Create a workout plan"""
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
                        "text": data.user_prompt,
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
                        "text": data.user_prompt,
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
