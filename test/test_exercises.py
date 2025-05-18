import pytest
from conftest import MockUser
from litestar.testing import AsyncTestClient

from app.models.models import Exercise


@pytest.mark.asyncio
async def test_get_exercises(
    test_client: AsyncTestClient,
    mock_exercises: list[Exercise],
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {mock_user.user_id}"}
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": exercise.name,
            "video_link": exercise.video_link,
            "exercise_results": [],
            "id": exercise.id,
        }
        for exercise in mock_exercises
    ]


@pytest.mark.asyncio
async def test_post_exercise(
    test_client: AsyncTestClient,
    mock_user: MockUser,
    mock_admin_user: MockUser,
):
    post_response = await test_client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {mock_admin_user.user_id}"},
        json={"exercises": [{"name": "New Exercise"}]},
    )
    assert post_response.status_code == 201

    get_response = await test_client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {mock_user.user_id}"}
    )
    assert get_response.status_code == 200
    assert get_response.json() == [
        {"name": "New Exercise", "video_link": None, "exercise_results": [], "id": 1}
    ]


@pytest.mark.asyncio
async def test_post_exercise_fails_for_non_admin(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    post_response = await test_client.post(
        "/api/exercises",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json={"exercises": [{"name": "New Exercise"}]},
    )
    assert post_response.status_code == 500  # FIXME: This should be a 403


@pytest.mark.asyncio
async def test_delete_exercise(
    test_client: AsyncTestClient,
    mock_user: MockUser,
    mock_admin_user: MockUser,
    mock_exercises: list[Exercise],
):
    mock_exercise = mock_exercises[0]
    post_response = await test_client.delete(
        f"/api/exercises/{mock_exercise.id}",
        headers={"Authorization": f"Bearer {mock_admin_user.user_id}"},
    )
    assert post_response.status_code == 200

    get_response = await test_client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {mock_user.user_id}"}
    )
    assert get_response.status_code == 200
    assert mock_exercise.id not in [exercise["id"] for exercise in get_response.json()]
