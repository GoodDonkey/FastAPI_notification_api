import base64
import hmac
import re
import time

import jwt
import sqlalchemy.exc
from jwt import ExpiredSignatureError, DecodeError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.common import consts, config
from app.common.consts import EXCEPT_PATH_REGEX
from app.database.conn import db
from app.database.schema import ApiKeys, Users
from app.errors import exceptions as ex
from app.errors.exceptions import APIException, SqlFailureEx
from app.models import UserToken
from app.utils.date_utils import D
from app.utils.logger import api_logger
from app.utils.query_utils import to_dict


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
            if url.startswith("/api/services"):
                qs = str(request.query_params)  # http://example.com/aaa?abc=123&xyz=456 에서 ?뒤가 params
                qs_list = qs.split("&")
                session = next(db.session())  # 여기서는 db 세션을 직접 가져오지만 느리므로 나중엔 redis로 대체할 예정.

                if not config.conf().DEBUG:  # DEBUG가 False 이면
                    try:
                        # query_params 를 key value 로 잘라서 dict에 저장.
                        qs_dict = {qs_split.split("=")[0]: qs_split.split("=")[1] for qs_split in qs_list}
                    except Exception:
                        raise ex.APIQueryStringEx()

                    qs_keys = qs_dict.keys()

                    if "key" not in qs_keys or "timestamp" not in qs_keys:
                        raise ex.APIQueryStringEx()

                    if "secret" not in headers.keys():
                        raise ex.APIHeaderInvalidEx()

                    api_key = ApiKeys.get(session=session, access_key=qs_dict["key"])

                    if not api_key:
                        raise ex.NotFoundAccessKeyEx(api_key=qs_dict["key"])
                        # hmac은 해싱 패키지. "key", "timestampe" 를 해싱한다.
                        # 해싱후 base64로 만들고 utf-8 로 인코딩하여 문자열로 만듬.
                    mac = hmac.new(bytes(api_key.secret_key, encoding='utf8'), bytes(qs, encoding='utf-8'), digestmod='sha256')
                    d = mac.digest()
                    validating_secret = str(base64.b64encode(d).decode('utf-8'))

                    if headers["secret"] != validating_secret:
                        raise ex.APIHeaderInvalidEx()

                    now_timestamp = int(D.datetime(diff=9).timestamp())  # diff=9 : 한국시간 얻기
                        # timestamp의 10초 이전 요청까지만 허용. Replay attack을 막기 위함.
                    if now_timestamp - 10 > int(qs_dict["timestamp"]) or now_timestamp < int(qs_dict["timestamp"]):
                        raise ex.APITimestampEx()

                    user_info = to_dict(api_key.users)
                    request.state.user = UserToken(**user_info)

                else:  # DEBUG가 True 이면 Request User
                    if "authorization" in headers.keys():
                        key = headers.get("authorization")
                        api_key_obj = ApiKeys.get(session=session, access_key=key)
                        user_info = to_dict(Users.get(session=session, id=api_key_obj.user_id))
                        request.state.user = UserToken(**user_info)
                    else:
                        if "authorization" not in headers.keys():
                            raise ex.NotAuthorized()
                session.close()
                response = await call_next(request)
                return response

            else:  # api/service 가 아니면
                if "authorization" in headers.keys():  # 토큰이 있으면
                    token_info = await token_decode(access_token=request.headers.get("Authorization"))
                    request.state.user = UserToken(**token_info)

                else:  # 토큰이 없으면
                    if "authorization" not in headers.keys():
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
    if isinstance(error, sqlalchemy.exc.OperationalError):
        error = SqlFailureEx(ex=error)
    if not isinstance(error, APIException):
        error = APIException(ex=error, detail=str(error))
    return error
