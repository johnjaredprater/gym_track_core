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

from app.exercises import delete_exercise, get_exercises, post_exercise
from app.sqlalchemy_async import on_startup, sqlalchemy_config
from app.user_auth import AccessToken, MyAuthenticationMiddleware, User
from app.workouts import (
    delete_workouts,
    get_workout,
    get_workouts,
    post_workouts,
    update_workouts,
)


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
    route_handlers=[
        health_check,
        hello_world,
        version,
        delete_exercise,
        post_exercise,
        get_exercises,
        post_workouts,
        get_workouts,
        get_workout,
        update_workouts,
        delete_workouts,
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
    on_startup=[on_startup],
    logging_config=logging_config,
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
)
decode_kubernetes_secret_file()
initialize_app()
