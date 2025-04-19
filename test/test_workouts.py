from datetime import datetime, timezone

import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Exercise, ExerciseResult


@pytest_asyncio.fixture(scope="function")
async def mock_exercise_result(
    db_session: AsyncSession,
    mock_user: MockUser,
    mock_exercise: Exercise,
):
    exercise_result = ExerciseResult(
        exercise_id=mock_exercise.id,
        sets=4,
        reps=8,
        weight=50.0,
        user_id=mock_user.user_id,
    )
    db_session.add(exercise_result)
    await db_session.commit()
    return exercise_result


def format_datetime(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


@pytest.mark.asyncio
async def test_get_exercise_results(
    test_client: AsyncTestClient,
    mock_exercise: Exercise,
    mock_exercise_result: ExerciseResult,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/exercise_results",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "user_id": mock_user.user_id,
            "exercise": {
                "id": mock_exercise.id,
                "name": mock_exercise.name,
                "video_link": mock_exercise.video_link,
            },
            "exercise_id": mock_exercise_result.exercise_id,
            "sets": mock_exercise_result.sets,
            "reps": mock_exercise_result.reps,
            "weight": mock_exercise_result.weight,
            "rpe": mock_exercise_result.rpe,
            "date": format_datetime(mock_exercise_result.date),
            "id": str(mock_exercise_result.id),
            "updated_at": format_datetime(mock_exercise_result.updated_at),
            "created_at": format_datetime(mock_exercise_result.created_at),
        }
    ]


@pytest.mark.asyncio
async def test_post_and_get_exercise_result(
    test_client: AsyncTestClient,
    mock_user: MockUser,
    mock_exercise: Exercise,
):
    post_response = await test_client.post(
        "/api/exercise_results",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json={"exercise_id": mock_exercise.id, "sets": 4, "reps": 8, "weight": 50.0},
    )
    assert post_response.status_code == 201
    exercise_result_id = post_response.text

    get_response = await test_client.get(
        f"/api/exercise_results/{exercise_result_id}",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert get_response.status_code == 200
    response_json = get_response.json()

    created_at = response_json["created_at"]
    updated_at = response_json["updated_at"]
    date = response_json["date"]

    assert response_json == {
        "user_id": mock_user.user_id,
        "exercise": {
            "id": mock_exercise.id,
            "name": mock_exercise.name,
            "video_link": mock_exercise.video_link,
        },
        "exercise_id": mock_exercise.id,
        "sets": 4,
        "reps": 8,
        "weight": 50.0,
        "rpe": None,
        "date": date,
        "id": str(exercise_result_id),
        "updated_at": updated_at,
        "created_at": created_at,
    }
