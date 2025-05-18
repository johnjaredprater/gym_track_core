import json
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Exercise,
    ExercisePlanORM,
    UserProfileORM,
    WarmUpPlanORM,
    WeekPlan,
    WeekPlanORM,
    WorkoutPlanORM,
)


@pytest_asyncio.fixture(scope="function")
async def mock_user_profile(
    db_session: AsyncSession,
    mock_user: MockUser,
):
    user_profile = UserProfileORM(
        user_id=mock_user.user_id,
        age=20,
        gender="male",
        number_of_days=5,
        workout_duration=30,
        fitness_level="beginner",
        goal="lose weight",
        injury_description="none",
    )
    db_session.add(user_profile)
    await db_session.commit()
    return user_profile


@pytest_asyncio.fixture(scope="function")
async def mock_week_plan(
    db_session: AsyncSession,
    mock_exercises: list[Exercise],
    mock_user: MockUser,
) -> WeekPlanORM:
    with open(f"{Path(__file__).parent}/data/two_day_plan.json", "r") as f:
        week_plan_data = json.load(f)

    week_plan = WeekPlan.model_validate(week_plan_data)

    exercise_name_to_id = {
        str(exercise.name): exercise.id for exercise in mock_exercises
    }

    week_plan_orm = WeekPlanORM(
        workout_plans=[
            WorkoutPlanORM(
                title=workout_plan.title,
                user_id=mock_user.user_id,
                warm_ups=[
                    WarmUpPlanORM(
                        description=warm_up.description,
                        user_id=mock_user.user_id,
                    )
                    for warm_up in workout_plan.warm_ups
                ],
                exercise_plans=[
                    ExercisePlanORM(
                        exercise_name=exercise.exercise,
                        exercise_id=exercise_name_to_id.get(exercise.exercise),
                        weight=exercise.weight,
                        reps=exercise.reps,
                        sets=exercise.sets,
                        rpe=exercise.rpe,
                        user_id=mock_user.user_id,
                    )
                    for exercise in workout_plan.exercises
                ],
            )
            for workout_plan in week_plan.workouts
        ],
        user_id=mock_user.user_id,
        summary=week_plan.summary,
    )
    db_session.add(week_plan_orm)
    await db_session.commit()
    return week_plan_orm


@pytest.fixture(scope="function")
def mock_week_plan_response_json() -> dict[str, Any]:
    with open(f"{Path(__file__).parent}/data/two_day_plan_response.json", "r") as f:
        return json.load(f)


@pytest_asyncio.fixture(scope="function")
async def mock_week_plan_id(
    mock_week_plan: WeekPlanORM,
):
    return mock_week_plan.id


@pytest.mark.asyncio
async def test_post_week_plan_without_user_profile(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    post_response = await test_client.post(
        "/api/week_plans",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert post_response.status_code == 412


@pytest.mark.asyncio
async def test_post_week_plan(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
    mock_exercises: list[Exercise],
    db_session: AsyncSession,
    mock_week_plan_response_json: dict[str, Any],
):

    post_response = await test_client.post(
        "/api/week_plans",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert post_response.status_code == 201
    assert post_response.json() == mock_week_plan_response_json["week_plans"][0]

    get_response = await test_client.get(
        "/api/week_plans",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert get_response.status_code == 200
    assert get_response.json() == mock_week_plan_response_json

    get_latest_response = await test_client.get(
        "/api/week_plans/latest",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert get_latest_response.status_code == 200
    assert get_latest_response.json() == mock_week_plan_response_json["week_plans"][0]


@pytest.mark.asyncio
async def test_patch_week_plan(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
    mock_exercises: list[Exercise],
    db_session: AsyncSession,
    mock_week_plan_id: str,
    mock_week_plan_response_json: dict[str, Any],
):
    patch_response = await test_client.patch(
        f"/api/week_plans/{mock_week_plan_id}",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json={"complete": True},
    )
    assert patch_response.status_code == 200

    week_plan = mock_week_plan_response_json["week_plans"][0]
    # Update the mock response to match the expected updated week plan
    week_plan["complete"] = True
    for workout_plan in week_plan["workouts"]:
        workout_plan["complete"] = True
        for exercise_plan in workout_plan["exercises"]:
            exercise_plan["complete"] = True

    assert patch_response.json() == week_plan


@pytest.mark.asyncio
async def test_patch_week_plan_incomplete_not_allowed(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
    mock_exercises: list[Exercise],
    db_session: AsyncSession,
    mock_week_plan_id: str,
):
    patch_response = await test_client.patch(
        f"/api/week_plans/{mock_week_plan_id}",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json={"complete": False},
    )
    assert patch_response.status_code == 405


@pytest.mark.asyncio
async def test_get_latest_week_plan_not_found(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/week_plans/latest",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_week_plans_not_found(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/week_plans",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 404
