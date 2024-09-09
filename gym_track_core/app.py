from litestar import Litestar, get
from litestar.config.cors import CORSConfig

cors_config = CORSConfig(allow_origins=["http://localhost:80"])

@get("/")
async def hello_world() -> str:
    return "Hello, world!"

app = Litestar([hello_world], cors_config=cors_config)
