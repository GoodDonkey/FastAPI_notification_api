from fastapi import APIRouter
from starlette.requests import Request

from app.database.schema import Users
from app.errors.exceptions import NotFoundUserEx
from app.models import UserMe

router = APIRouter()


# response_model=UserMe:
#         - 반응 모델을 설정해주지 않으면 모든 정보가 반응으로 노출된다.
#         - 따라서 따로 정의해서 response 로 보여줄 값을 따로 정의하여 사용한다.
@router.get("/me", response_model=UserMe)
async def get_user(request: Request):
    """
    get my info
    :param request:
    :return:
    """
    user = request.state.user
    user_info = Users.get(id=user.id)
    raise NotFoundUserEx(user_info.id)
    return user_info

