from datetime import datetime
from enum import Enum
from typing import List

from pydantic import Field
from pydantic.main import BaseModel
from pydantic.networks import EmailStr

""" 요청을 받거나 반응을 보낼 때 아래 클래스에 정의된 대로 json 형태로 만들어 소통한다."""


class UserRegister(BaseModel):
    """ 여기 모델로 정의하여 사용하면 request를 받을 때 json 포맷으로 만들어 준다. """
    email: EmailStr = None
    pw: str = None


class SnsType(str, Enum):
    """ 이 중 하나만 선택 가능. 없는 값이 들어오면 422 에러 """
    email: str = "email"
    facebook: str = "facebook"
    google:  str = "google"
    kakao: str = "kakao"


class Token(BaseModel):
    Authorization: str = None


class EmailRecipients(BaseModel):
    name: str
    email: str


class SendEmail(BaseModel):
    email_to: List[EmailRecipients] = None


class KakaoMsgBody(BaseModel):
    msg: str = None


class MessageOk(BaseModel):
    message: str = Field(default="OK")


class UserToken(BaseModel):
    id: int
    pw: str = None
    email: str = None
    name: str = None
    phone_number: str = None
    profile_img: str = None
    sns_type: str = None

    class Config:
        orm_mode = True


class UserMe(BaseModel):
    id: int
    email: str = None
    name: str = None
    phone_number: str = None
    profile_img: str = None
    sns_type: str = None

    class Config:
        orm_mode = True


class AddApiKey(BaseModel):
    user_memo: str = None

    class Config:
        orm_mode = True


class GetApiKeyList(AddApiKey):
    id: int = None
    access_key: str = None
    created_at: datetime = None


class GetApiKeys(GetApiKeyList):
    secret_key: str = None


class CreateAPIWhiteLists(BaseModel):
    ip_addr: str = None


class GetAPIWhiteLists(CreateAPIWhiteLists):
    id: int

    class Config:
        orm_mode = True
