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
from app.common.consts import EXCEPT_PATH_REGEX
from app.errors import exceptions as ex
from app.errors.exceptions import APIException
from app.models import UserToken
from app.utils.date_utils import D
from app.utils.logger import api_logger


async def access_control(request: Request, call_next):
    request.state.req_time = D.datetime()
    request.state.start = time.time()
    request.state.inspect = None
    request.state.user = None
    ip = request.headers["x-forwarded-for"] if "x-forwarded-for" in request.headers.keys() else request.client.host
    request.state.ip = ip.split(",")[0] if "," in ip else ip
    headers = request.headers
    cookies = request.cookies
    url = request.url.path

    if await url_pattern_check(url, EXCEPT_PATH_REGEX) or url in EXCEPT_PATH_REGEX:
        response = await call_next(request)  # url 패턴 체크를 한 후 미들웨어 프로세스를 더이상 진행하지 않고 앱으로 넘긴다.
        if url != "/":
            await api_logger(request=request, response=response)
        return response

    try:
        print("token_validator: 5")

        if url.startswith("/api"):
            # api 인경우 헤더로 토큰 검사
            print("token_validator: 1")
            if "authorization" in headers.keys():
                token_info = await token_decode(access_token=request.headers.get("Authorization"))
                request.state.user = UserToken(**token_info)
                # 토큰 없음

            else:
                if "Authorization" not in headers.keys():
                    print("headers", request.headers)
                    raise ex.NotAuthorized()
        else:
            print("token_validator: 6")
            # 템플릿 렌더링인 경우 쿠키에서 토큰 검사: 프론트 고려한 구문
            print("cookies", request.cookies)
            request.cookies["Authorization"] = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6OSwiZW1haWwiOiJkb25rZXlAZXhhbXBsZS5jb20iLCJuYW1lIjpudWxsLCJwaG9uZV9udW1iZXIiOm51bGwsInByb2ZpbGVfaW1nIjpudWxsLCJzbnNfdHlwZSI6bnVsbH0.6yIY-1mhYQNxBNDBZCQrGKe7N3Tg4BMhTAbFnCH1rWA"

            if "Authorization" not in cookies.keys():
                print("token_validator: 3")
                raise ex.NotAuthorized()

            token_info = await token_decode(access_token=cookies.get("Authorization"))
            request.state.user = UserToken(**token_info)

        response = await call_next(request)  # 토큰 검사가 끝난 후 함수 실행 (다음 미들웨어 또는 endpoint 함수 등)
        print("token_validator: 7", response)
        await api_logger(request=request, response=response)
    except Exception as e:
        print("token_validator: 4")
        error = await exception_handler(e)
        error_dict = dict(status=error.status_code, msg=error.msg, detail=error.detail, code=error.code)
        print(error_dict)
        response = JSONResponse(status_code=error.status_code, content=error_dict)
        await api_logger(request=request, error=error)
    print("token_validator: 8")
    return response


async def url_pattern_check(path, pattern):
    result = re.match(pattern, path)
    if result:
        return True
    return False


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


async def exception_handler(error: Exception):
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error
