from litestar.middleware import (
   AbstractAuthenticationMiddleware,
   AuthenticationResult,
)
from litestar.connection import ASGIConnection
from firebase_admin import initialize_app


class MyAuthenticationMiddleware(AbstractAuthenticationMiddleware):


   async def authenticate_request(
       self, connection: ASGIConnection
   ) -> AuthenticationResult:
       # do something here.

        type, access_token = connection.headers['authorization'].split()
        assert type == "Bearer"
        
        default_app = initialize_app(access_token)

        user = None
        auth = None
        return AuthenticationResult(user, auth)