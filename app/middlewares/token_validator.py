import time
import typing
import jwt

from fastapi.params import Header
from jwt import PyJWTError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common import config
from app.common.config import conf
from app.models import UserToken

from app.utils.date_utils import D


class AccessControl:
    def __init__(
            self,
            app: ASGIApp,
            except_path_list: typing.Sequence[str] = None,
            except_path_regex: str = None,
    ) -> None:
        if except_path_list is None:
            except_path_list = ["*"]
        self.app = app
        self.except_path_list = except_path_list
        self.except_path_regex = except_path_regex

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print(self.except_path_regex)
        print(self.except_path_list)

        request = Request(scope=scope)
        headers = Headers(scope=scope)

        request.state.req_time = D.datetime()
        print(D.datetime())  # 시간이 어떻게 찍히는지 보기 위해 프린트 해봄
        print(D.date())
        print(D.date_num())
        request.state.start = time.time()
        request.state.inspect = None  # 500에러 로깅하기 위해 사용(Sentry 를 사용할 수도 있다.)
        request.state.user = None  # 토큰에서 유저 정보를 decode 해서 사용(middleware 에서는 굳이 DB에 접속하지 않고 유저정보를 사용하기 위해 사용.)
        request.state.is_admin_access = None
        print(request.cookies)
        print(headers)
        res = await self.app(scope, receive, send)
        return res
