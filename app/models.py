from enum import Enum

from pydantic.main import BaseModel
from pydantic.networks import EmailStr


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
