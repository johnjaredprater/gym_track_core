from datetime import datetime, timezone

import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercises_and_workouts import Exercise, ExerciseResult


@pytest_asyncio.fixture(scope="function")
async def mock_workout(
    db_session: AsyncSession,
    mock_user: MockUser,
    mock_exercise: Exercise,
):
    workout = ExerciseResult(
        exercise_id=mock_exercise.id,
        sets=4,
        reps=8,
        weight=50.0,
        user_id=mock_user.user_id,
    )
    db_session.add(workout)
    await db_session.commit()
    return workout


def format_datetime(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


@pytest.mark.asyncio
async def test_get_workouts(
    test_client: AsyncTestClient,
    mock_exercise: Exercise,
    mock_workout: ExerciseResult,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/workouts", headers={"Authorization": f"Bearer {mock_user.user_id}"}
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
            "exercise_id": mock_workout.exercise_id,
            "sets": mock_workout.sets,
            "reps": mock_workout.reps,
            "weight": mock_workout.weight,
            "rpe": mock_workout.rpe,
            "date": format_datetime(mock_workout.date),
            "id": str(mock_workout.id),
            "updated_at": format_datetime(mock_workout.updated_at),
            "created_at": format_datetime(mock_workout.created_at),
        }
    ]


@pytest.mark.asyncio
async def test_post_and_get_workout(
    test_client: AsyncTestClient,
    mock_user: MockUser,
    mock_exercise: Exercise,
):
    post_response = await test_client.post(
        "/api/workouts",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json={"exercise_id": mock_exercise.id, "sets": 4, "reps": 8, "weight": 50.0},
    )
    assert post_response.status_code == 201
    workout_id = post_response.text

    get_response = await test_client.get(
        f"/api/workouts/{workout_id}",
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
        "id": str(workout_id),
        "updated_at": updated_at,
        "created_at": created_at,
    }
