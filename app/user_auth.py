from datetime import datetime

import firebase_admin.auth  # imported like this to allow easy mocking
from attrs import define
from cattrs import structure
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult


@define
class User:
    name: str
    user_id: str
    picture: str
    admin: bool = False


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

            user_raw = firebase_admin.auth.verify_id_token(access_token)

            user_id = user_raw["uid"]
            user = firebase_admin.auth.get_user(user_id)
            if user.custom_claims:
                user_raw["admin"] = user.custom_claims.get("admin", False)

        except Exception:
            raise NotAuthorizedException()

        user = structure(user_raw, User)
        token = AccessToken(
            exp=datetime.fromtimestamp(user_raw["exp"]),
            iat=datetime.fromtimestamp(user_raw["iat"]),
            token=access_token,
        )
        return AuthenticationResult(user, token)
