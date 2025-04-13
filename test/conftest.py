from datetime import datetime, timedelta
from typing import Any, AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig as AdvancedAlchemyConfig,
)
from attrs import define
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.plugins import PluginRegistry
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.models.exercises_and_workouts import Exercise


@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create an in-memory SQLite database for testing.

    This is not quite ideal because in production we're currently using a MySQL DB,
    but SQLAlchemy should expose the same interface over both, so we can still get
    a lot of test coverage with this.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
def sqlalchemy_config(db_engine: AsyncEngine) -> AdvancedAlchemyConfig:
    """Create SQLAlchemy config with the test engine."""
    session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    return AdvancedAlchemyConfig(
        engine_instance=db_engine,
        session_maker=session_maker,
        create_all=False,
        session_dependency_key="session",
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(sqlalchemy_config) -> AsyncGenerator[AsyncSession, None]:
    async_session = sqlalchemy_config.session_maker()
    yield async_session
    await async_session.close()


@pytest.fixture(scope="function")
def test_client(sqlalchemy_config: AdvancedAlchemyConfig) -> AsyncTestClient:
    other_plugins = [
        plugin for plugin in app.plugins if not isinstance(plugin, SQLAlchemyPlugin)
    ]

    # Make sure app state has the required keys
    app.state.session_maker_class = sqlalchemy_config.session_maker

    # Replace existing plugin with test plugin
    app.plugins = PluginRegistry(
        other_plugins + [SQLAlchemyPlugin(config=sqlalchemy_config)]
    )
    return AsyncTestClient(app=app)


@define
class MockUser:
    user_id: str
    name: str
    email: str
    picture: str
    custom_claims: dict[str, Any] = {}


@pytest.fixture(autouse=True)
def mock_user():
    return MockUser(
        user_id="test_user_id",
        name="user",
        email="test@example.com",
        picture="https://example.com/test_user_id.png",
    )


@pytest.fixture(autouse=True)
def mock_admin_user():
    return MockUser(
        user_id="admin_user_id",
        name="admin",
        email="admin@example.com",
        picture="https://example.com/admin_user_id.png",
        custom_claims={"admin": True},
    )


@pytest.fixture(autouse=True)
def mock_firebase_auth(mock_user, mock_admin_user):
    """
    Fixture that mocks firebase_admin.auth with just the
    verify_id_token and get_user methods.
    """
    with patch("firebase_admin.auth") as mock_auth:
        # Create a users database for our mock
        users = {
            mock_user.user_id: mock_user,
            mock_admin_user.user_id: mock_admin_user,
        }

        # Mock verify_id_token
        def mock_verify_id_token(token, *args, **kwargs):
            # Simplifying by assuming token is a user ID
            if token in users:
                user = users[token]
                return {
                    "uid": user.user_id,
                    "user_id": user.user_id,
                    "name": user.name,
                    "email": user.email,
                    "picture": user.picture,
                    "iat": datetime.now().timestamp(),
                    "exp": (datetime.now() + timedelta(hours=1)).timestamp(),
                }
            raise ValueError(f"Invalid token: {token}")

        mock_auth.verify_id_token = mock_verify_id_token

        # Mock get_user
        def mock_get_user(uid, *args, **kwargs):
            if uid in users:
                return users[uid]
            raise ValueError(f"No user with UID: {uid}")

        mock_auth.get_user = mock_get_user

        yield mock_auth


# Mock data for testing ---------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def mock_exercise(db_session: AsyncSession):
    mock_exercise = Exercise(
        name="Push-up",
    )
    db_session.add(mock_exercise)
    await db_session.commit()
    return mock_exercise
