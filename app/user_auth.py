from datetime import datetime

from attrs import define
from cattrs import structure
from firebase_admin.auth import verify_id_token
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult


@define
class User:
    name: str
    user_id: str
    picture: str


@define
class AccessToken:
    exp: datetime
    iat: datetime
    token: str


class MyAuthenticationMiddleware(AbstractAuthenticationMiddleware):

    async def authenticate_request(
        self, connection: ASGIConnection
    ) -> AuthenticationResult:
        try:
            type, access_token = connection.headers["authorization"].split()
            assert type == "Bearer"
            user_raw = verify_id_token(access_token)
        except Exception:
            raise NotAuthorizedException()

        user = structure(user_raw, User)
        token = AccessToken(
            exp=datetime.fromtimestamp(user_raw["exp"]),
            iat=datetime.fromtimestamp(user_raw["iat"]),
            token=access_token,
        )
        return AuthenticationResult(user, token)
