from importlib import metadata
from typing import Any

from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.logging import LoggingConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from app.exercise_results import exercise_result_router
from app.exercises import exercise_router
from app.sqlalchemy_async import on_startup, sqlalchemy_config
from app.user_auth import MyAuthenticationMiddleware
from app.user_profile import user_profile_router
from app.week_plans import week_plan_router


@get("/", exclude_from_auth=True)
async def health_check() -> None:
    return None


@get("/api/version", exclude_from_auth=True)
async def version() -> str:
    from importlib import metadata

    return metadata.version("gym-track-core")


def create_app(
    dependencies: dict[str, Any],
) -> Litestar:
    logging_config = LoggingConfig(
        root={"level": "INFO", "handlers": ["queue_listener"]},
        formatters={
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        log_exceptions="always",
    )

    # Allow local testing
    cors_config = CORSConfig(allow_origins=["http://localhost:3000"])
    auth_mw = DefineMiddleware(MyAuthenticationMiddleware, exclude=["/api/docs"])

    return Litestar(
        route_handlers=[
            health_check,
            version,
            exercise_router,
            exercise_result_router,
            week_plan_router,
            user_profile_router,
        ],
        dependencies=dependencies,
        middleware=[auth_mw],
        openapi_config=OpenAPIConfig(
            title="Gym Track Core",
            path="/api/docs",
            description="API docs",
            version=metadata.version("gym-track-core"),
            render_plugins=[ScalarRenderPlugin()],
        ),
        cors_config=cors_config,
        on_startup=[on_startup],
        logging_config=logging_config,
        plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
    )
