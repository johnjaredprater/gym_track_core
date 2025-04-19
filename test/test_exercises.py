import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Exercise


@pytest_asyncio.fixture(scope="function")
async def mock_exercise_with_video_url(
    db_session: AsyncSession,
    mock_exercise: Exercise,  # Ensure mock_exercise is added to the database first
):
    mock_exercise = Exercise(
        name="Pull-up",
        video_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    db_session.add(mock_exercise)
    await db_session.commit()
    yield mock_exercise


@pytest.mark.asyncio
async def test_get_exercises(
    test_client: AsyncTestClient,
    mock_exercise: Exercise,
    mock_exercise_with_video_url: Exercise,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {mock_user.user_id}"}
    )
    assert response.status_code == 200
    assert response.json() == [
        {
            "name": mock_exercise.name,
            "video_link": None,
            "exercise_results": [],
            "id": mock_exercise.id,
        },
        {
            "name": mock_exercise_with_video_url.name,
            "video_link": mock_exercise_with_video_url.video_link,
            "exercise_results": [],
            "id": mock_exercise_with_video_url.id,
        },
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
        json={"name": "New Exercise"},
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
        json={"name": "New Exercise"},
    )
    assert post_response.status_code == 500  # FIXME: This should be a 403


@pytest.mark.asyncio
async def test_delete_exercise(
    test_client: AsyncTestClient,
    mock_user: MockUser,
    mock_admin_user: MockUser,
    mock_exercise: Exercise,
):
    post_response = await test_client.delete(
        f"/api/exercises/{mock_exercise.id}",
        headers={"Authorization": f"Bearer {mock_admin_user.user_id}"},
    )
    assert post_response.status_code == 200

    get_response = await test_client.get(
        "/api/exercises", headers={"Authorization": f"Bearer {mock_user.user_id}"}
    )
    assert get_response.status_code == 200
    assert get_response.json() == []
