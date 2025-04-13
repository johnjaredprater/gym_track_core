from typing import AsyncGenerator

import pytest
import pytest_asyncio
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig as AdvancedAlchemyConfig,
)
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


@pytest_asyncio.fixture(scope="session")
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


@pytest.fixture(scope="session")
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
async def db_session(sqlalchemy_config) -> AsyncGenerator[AsyncTestClient, None]:
    """Create a test client."""
    async_session = sqlalchemy_config.session_maker()
    yield async_session
    await async_session.close()


@pytest.fixture(scope="function")
def test_client(sqlalchemy_config: AdvancedAlchemyConfig) -> AsyncTestClient:
    """Configure app with test database."""
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
