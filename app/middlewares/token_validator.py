import re
import time
import typing

import jwt
from jwt import PyJWTError, ExpiredSignatureError, DecodeError
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.common import consts
from app.errors import exceptions as ex
from app.errors.exceptions import APIException
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

        request.state.start = time.time()
        request.state.inspect = None  # 500에러 로깅하기 위해 사용(Sentry 를 사용할 수도 있다.)
        request.state.user = None  # 토큰에서 유저 정보를 decode 해서 사용(middleware 에서는 굳이 DB에 접속하지 않고 유저정보를 사용하기 위해 사용.)
        request.state.is_admin_access = None

        ip_from = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else None
        # x-forwarded-for: AWS 로드밸런서를 지나면 위 헤더가 추가되는데, 여기서 고객의 IP가 어디서 왔는지 기록해둠.
        if await self.url_pattern_check(request.url.path,
                                        self.except_path_regex) or request.url.path in self.except_path_list:
            return await self.app(scope, receive, send)  # url 패턴 체크를 한 후 미들웨어 프로세스를 더이상 진행하지 않고 앱으로 넘긴다.
        try:
            if request.url.path.startswith("/api"):
                # api 인경우 헤더로 토큰 검사
                print('1')
                if "authorization" in request.headers.keys():
                    token_info = await self.token_decode(access_token=request.headers.get("Authorization"))
                    request.state.user = UserToken(**token_info)
                    # 토큰 없음

                else:
                    if "authorization" not in request.headers.keys():
                        print(request.headers)
                        raise ex.NotAuthorized()
            else:
                # 템플릿 렌더링인 경우 쿠키에서 토큰 검사: 프론트 고려한 구문
                print(request.cookies)
                request.cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6OSwiZW1haWwiOiJkb25rZXlAZXhhbXBsZS5jb20iLCJuYW1lIjpudWxsLCJwaG9uZV9udW1iZXIiOm51bGwsInByb2ZpbGVfaW1nIjpudWxsLCJzbnNfdHlwZSI6bnVsbH0.6yIY-1mhYQNxBNDBZCQrGKe7N3Tg4BMhTAbFnCH1rWA"

                if "Authorization" not in request.cookies.keys():
                    raise ex.NotAuthorized()

                token_info = await self.token_decode(access_token=request.cookies.get("Authorization"))
                request.state.user = UserToken(**token_info)

            request.state.req_time = D.datetime()
            print(D.datetime())  # 시간이 어떻게 찍히는지 보기 위해 프린트 해봄
            print(D.date())
            print(D.date_num())

            print(request.cookies)
            print(headers)
            res = await self.app(scope, receive, send)
        except APIException as e:
            res = await self.exception_handler(e)
            res = await res(scope, receive, send)
        finally:
            # Logging
            ...
        return res

    @staticmethod
    async def url_pattern_check(path, pattern):
        result = re.match(pattern, path)
        if result:
            return True
        return False

    @staticmethod
    async def token_decode(access_token):
        """
        :param access_token:
        :return:
        """
        try:
            access_token = access_token.replace("Bearer ", "")
            payload = jwt.decode(access_token, key=consts.JWT_SECRET, algorithms=[consts.JWT_ALGORITHM])
        except ExpiredSignatureError:
            raise ex.TokenExpiredEx()
        except DecodeError:
            raise ex.TokenDecodeEx()
        return payload

    @staticmethod
    async def exception_handler(error: APIException):
        error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
        res = JSONResponse(status_code=error.status_code, content=error_dict)
        return res
