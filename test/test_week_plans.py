import pytest
import pytest_asyncio
from conftest import MockUser
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import UserProfileORM


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
async def test_post_week_plan_without_user_profile(
    test_client: AsyncTestClient,
    mock_user: MockUser,
):
    post_response = await test_client.post(
        "/api/week_plans",
        headers={"Authorization": f"Bearer {mock_user.user_id}"},
    )
    assert post_response.status_code == 412


# @pytest.mark.asyncio
# async def test_post_week_plan(
#     test_client: AsyncTestClient,
#     mock_user_profile: UserProfileORM,
#     mock_anthropic_client: MockAnthropicClient,
#     mock_user: MockUser,
# ):
#     response = await test_client.post(
#         "/api/week_plans",
#         headers={"Authorization": f"Bearer {mock_user.user_id}"},
#     )
#     assert response.status_code == 200
