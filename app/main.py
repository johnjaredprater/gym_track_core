import importlib

# from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from firebase_admin import initialize_app
from litestar import Litestar, Request, get
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.logging import LoggingConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from app.sqlalchemy_sync_repository import get_exercises, on_startup
from app.user_auth import AccessToken, MyAuthenticationMiddleware, User

logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["queue_listener"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
    log_exceptions="always",
)


# Allow local testing
cors_config = CORSConfig(allow_origins=["http://localhost:3000"])
auth_mw = DefineMiddleware(MyAuthenticationMiddleware, exclude="/api/docs")


@get("/", exclude_from_auth=True)
async def health_check() -> None:
    return None


@get("/api")
async def hello_world(request: Request[User, AccessToken, State]) -> str:
    user = request.user
    return f"Hello, {user.name}!"


@get("/api/version", exclude_from_auth=True)
async def version() -> str:
    version = importlib.metadata.version("gym-track-core")
    return version


app = Litestar(
    route_handlers=[health_check, hello_world, version, get_exercises],
    middleware=[auth_mw],
    openapi_config=OpenAPIConfig(
        title="Gym Track Core",
        path="/api/docs",
        description="API docs",
        version=importlib.metadata.version("gym-track-core"),
        render_plugins=[ScalarRenderPlugin()],
    ),
    cors_config=cors_config,
    on_startup=[on_startup],
    logging_config=logging_config,
    # plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
)
initialize_app()
