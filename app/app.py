from litestar import Litestar, get
from litestar.config.cors import CORSConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from app.sqlalchemy_sync_repository import get_exercises, on_startup
# from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin


import importlib
from app.auth import MyAuthenticationMiddleware


# Allow local testing
cors_config = CORSConfig(allow_origins=["http://localhost:3000"])
auth_mw = DefineMiddleware(MyAuthenticationMiddleware, exclude="/api/docs")


@get("/")
async def health_check() -> None:
    return None


@get("/api")
async def hello_world() -> str:
    return "Hello, world!"


@get("/api/version", exclude_from_auth=True)
async def version() -> str:
    version = importlib.metadata.version('gym-track-core')
    return version


app = Litestar(
    route_handlers=[health_check, hello_world, version, get_exercises],
    openapi_config=OpenAPIConfig(
        title="Gym Track Core",
        path="/api/docs",
        description="API docs",
        version=importlib.metadata.version('gym-track-core'),
        render_plugins=[ScalarRenderPlugin()],
    ),
    cors_config=cors_config,
    on_startup=[on_startup],
    debug=True,
    # plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
)
