import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig as AdvancedAlchemyConfig,
)
from anthropic import Anthropic
from anthropic.types import Message, TextBlock
from attrs import define
from litestar import Litestar
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.plugins import PluginRegistry
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.testing import AsyncTestClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.app import create_app
from app.llm.claude_prompts import SCREENING_PROMPT
from app.models.models import Exercise, ScreeningResult, ScreeningStatus

sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
sqlite3.register_converter("UUID", lambda s: uuid.UUID(s.decode()) if s else None)


@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create an in-memory SQLite database for testing.

    This is not quite ideal because in production we're currently using a MySQL DB,
    but SQLAlchemy should expose the same interface over both, so we can still get
    a lot of test coverage with this.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        # echo=True, ## TODO: Uncomment this when we want to see the SQL queries
        connect_args={
            "check_same_thread": False,
            "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        },
    )

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


class MockMessage(BaseModel):
    role: str
    content: list[TextBlock]


@pytest.fixture(scope="function")
def mock_anthropic_client():
    client = AsyncMock(spec=Anthropic)

    messages = AsyncMock(spec=Message)

    def create(system: str, *args, **kwargs):
        content = Mock(spec=TextBlock)

        if system == SCREENING_PROMPT:
            content.text = ScreeningResult(
                status=ScreeningStatus.accepted
            ).model_dump_json()
        else:
            with open(f"{Path(__file__).parent}/data/two_day_plan.json", "r") as f:
                content.text = f.read()
        return MockMessage(
            role="assistant",
            content=[content],
        )

    messages.create = create
    client.configure_mock(messages=messages)
    return client


@pytest.fixture(scope="function")
def test_app(
    sqlalchemy_config: AdvancedAlchemyConfig,
    mock_anthropic_client: AsyncMock,
):
    async def get_anthropic_client():
        return mock_anthropic_client

    app = create_app(dependencies={"anthropic_client": get_anthropic_client})
    other_plugins = [
        plugin for plugin in app.plugins if not isinstance(plugin, SQLAlchemyPlugin)
    ]

    # Make sure app state has the required keys
    app.state.session_maker_class = sqlalchemy_config.session_maker

    # Replace existing plugin with test plugin
    app.plugins = PluginRegistry(
        other_plugins + [SQLAlchemyPlugin(config=sqlalchemy_config)]
    )

    return app


@pytest_asyncio.fixture(scope="function")
async def test_client(
    test_app: Litestar,
) -> AsyncTestClient:
    return AsyncTestClient(app=test_app)


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
async def mock_exercises(db_session: AsyncSession) -> list[Exercise]:
    with open(
        f"{Path(__file__).parent.parent}/app/data/default_exercises.json", "r"
    ) as f:
        default_exercises = json.load(f)

    exercises = []
    for index, exercise in enumerate(default_exercises, start=1):
        name, video_link = exercise.values()
        exercises.append(Exercise(id=index, name=name, video_link=video_link))
    db_session.add_all(exercises)
    await db_session.commit()
    return exercises
