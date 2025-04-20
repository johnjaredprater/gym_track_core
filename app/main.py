import base64
import importlib
import os

from firebase_admin import initialize_app
from litestar import Litestar, Request, get
from litestar.config.cors import CORSConfig
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.datastructures import State
from litestar.logging import LoggingConfig
from litestar.middleware import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from app.exercise_results import exercise_result_router
from app.exercises import exercise_router
from app.sqlalchemy_async import on_startup, sqlalchemy_config
from app.user_auth import AccessToken, MyAuthenticationMiddleware, User
from app.week_plans import week_plan_router


def decode_kubernetes_secret_file():
    base_64_secret_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if base_64_secret_file:
        with open(base_64_secret_file, "rb") as f:
            encoded_data = f.read()
            if encoded_data.decode("utf-8").startswith("{"):
                return
            decoded_data = base64.b64decode(encoded_data).decode("utf-8")

        decoded_secret_file = "gym-tracking-firebase-key.json"
        with open(decoded_secret_file, "w") as f:
            f.write(decoded_data)

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = decoded_secret_file


def export_anthropic_api_key():
    try:
        with open("/mnt/anthropic-api-key/key", "r") as f:
            os.environ["ANTHROPIC_API_KEY"] = f.read()
    except Exception as e:
        print(e)
        print("Anthropic API key secret not found")


logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["queue_listener"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
    },
    log_exceptions="always",
)


# Allow local testing
cors_config = CORSConfig(allow_origins=["http://localhost:3000"])
auth_mw = DefineMiddleware(MyAuthenticationMiddleware, exclude=["/api/docs"])


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
    route_handlers=[
        health_check,
        hello_world,
        version,
        exercise_router,
        exercise_result_router,
        week_plan_router,
    ],
    middleware=[auth_mw],
    openapi_config=OpenAPIConfig(
        title="Gym Track Core",
        path="/api/docs",
        description="API docs",
        version=importlib.metadata.version("gym-track-core"),
        render_plugins=[ScalarRenderPlugin()],
    ),
    cors_config=cors_config,
    on_startup=[on_startup, export_anthropic_api_key],
    logging_config=logging_config,
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
)
decode_kubernetes_secret_file()
initialize_app()
