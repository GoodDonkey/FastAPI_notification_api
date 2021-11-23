from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends

# TODO:
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.common.consts import JWT_SECRET, JWT_ALGORITHM  # 원칙상 공유되지 않아야 할 정보
from app.database.conn import db
from app.database.schema import Users
from app.models import SnsType, Token, UserToken, UserRegister

router = APIRouter()

"""
1. 구글 로그인을 위한 구글 앱 준비 (구글 개발자 도구)
2. FB 로그인을 위한 FB 앱 준비 (FB 개발자 도구)
3. 카카오 로그인을 위한 카카오 앱준비( 카카오 개발자 도구)
4. 이메일, 비밀번호로 가입 (v)
5. 가입된 이메일, 비밀번호로 로그인, (v)
6. JWT 발급 (v)

7. 이메일 인증 실패시 이메일 변경
8. 이메일 인증 메일 발송
9. 각 SNS 에서 Unlink 
10. 회원 탈퇴
11. 탈퇴 회원 정보 저장 기간 동안 보유(법적 최대 한도차 내에서, 가입 때 약관 동의 받아야 함, 재가입 방지 용도로 사용하면 가능)

"""


@router.post("/register/{sns_type}", status_code=201, response_model=Token)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """ 회원가입 API
    :param sns_type:
    :param reg_info: 회원 가입 request body
    :param session:
    :return:
    """

    if sns_type == SnsType.email:
        is_exist = await is_email_exist(reg_info.email)
        if not reg_info.email or not reg_info.pw:  # 나중에는 raise로 에러처리 할 예정. raise 로 에러처리를 하면 이를 적절한 형태로 반응을 보내는 미들웨어가
            # 있는 듯.
            return JSONResponse(status_code=400, content=dict(msg="이메일과 패스워드 모두 입력해주세요."))
        if is_exist:
            return JSONResponse(status_code=400, content=dict(msg="이메일이 이미 존재합니다."))
        hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())
        new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email)
        token = dict(
                Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing agree'}), )}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="지원하지 않는 타입"))


@router.post('/login/{sys_type}', status_code=200)
async def login(sns_type: SnsType, user_info: UserRegister):
    if sns_type == SnsType.email:
        is_exist = await is_email_exist(user_info.email)
        if not user_info.email or not user_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="이메일과 패스워드 모두 입력해주세요."))
        if not is_exist:
            return JSONResponse(status_code=400, content=dict(msg="이메일 또는 패스워드를 다시 확인해 주세요"))
        user = Users.get(email=user_info.email)
        is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))
        if not is_verified:
            return JSONResponse(status_code=400, content=dict(msg="이메일 또는 패스워드를 다시 확인해 주세요"))  # 로그인 오류 메시지는 모호하게 전달하는 것이 안전하다.
        token = dict(
            Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing agree'}), )}")
        return token
    return JSONResponse(status_code=400, content=dict(msg="지원하지 않는 타입"))  # 지금은 email 로그인만 지원됨.


async def is_email_exist(email: str) -> bool:
    """ 회원의 email이 있으면 True를 반환. """
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt
