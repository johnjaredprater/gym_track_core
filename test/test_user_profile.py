import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import FitnessLevel, Gender, UserProfileCreate, UserProfileORM


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


@pytest.mark.asyncio
async def test_get_user_profile(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
):
    response = await test_client.get(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "user_id": mock_user.user_id,
        "age": mock_user_profile.age,
        "gender": mock_user_profile.gender,
        "number_of_days": mock_user_profile.number_of_days,
        "workout_duration": mock_user_profile.workout_duration,
        "fitness_level": mock_user_profile.fitness_level,
        "goal": mock_user_profile.goal,
        "injury_description": mock_user_profile.injury_description,
    }


@pytest.mark.asyncio
async def test_post_and_get_user_profile(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    user_profile = UserProfileCreate(
        age=20,
        gender=Gender.male,
        number_of_days=5,
        workout_duration=30,
        fitness_level=FitnessLevel.beginner,
        goal="lose weight",
    )

    expected_response = {
        "user_id": mock_user.user_id,
        **user_profile.model_dump(),
    }

    post_response = await test_client.post(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json=user_profile.model_dump(),
    )
    assert post_response.status_code == 201
    assert post_response.json() == expected_response

    get_response = await test_client.get(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert get_response.status_code == 200
    assert get_response.json() == expected_response


@pytest.mark.asyncio
async def test_patch_user_profile(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
):
    update_data = {
        "age": 21,
        "gender": Gender.female,
        "number_of_days": 6,
        "injury_description": "I can't lift my arm",
    }
    expected_response = {
        "user_id": mock_user.user_id,
        "workout_duration": mock_user_profile.workout_duration,
        "fitness_level": mock_user_profile.fitness_level,
        "goal": mock_user_profile.goal,
        **update_data,
    }

    response = await test_client.patch(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
        json=update_data,
    )
    assert response.status_code == 200
    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_delete_user_profile(
    test_client: AsyncTestClient,
    mock_user_profile: UserProfileORM,
    mock_user: MockUser,
):
    expected_response = {
        "message": f"User profile with ID {mock_user.user_id} has been deleted."
    }

    response = await test_client.delete(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 200
    assert response.json() == expected_response

    response = await test_client.get(
        "/api/user_profile",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert response.status_code == 404
