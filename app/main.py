from dataclasses import asdict

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.common.consts import EXCEPT_PATH_LIST, EXCEPT_PATH_REGEX
from app.database.conn import db
from app.database.schema import Base
from app.common.config import conf

from app.middlewares.token_validator import AccessControl
from app.middlewares.trusted_hosts import TrustedHostMiddleware

from app.routes import index, auth


def create_app():
    """ 앱 생성 함수 """
    c = conf()
    _app = FastAPI()
    conf_dict = asdict(c)  # conf 클래스를 dict로 가져와서 사용. unpacking 한것.
    db.init_app(_app, **conf_dict)
    # print(Base.metadata.tables)
    Base.metadata.create_all(db.engine)  # 없는 테이블이 있으면 만든다.

    # 데이터 베이스 init

    # 래디스 init

    # 미들웨어 정의 (순서 중요. AccessControl이 가장 마지막에 등록되어야 한다고 함. (가장 위가 가장 마지막))
    _app.add_middleware(AccessControl,
                        except_path_list=EXCEPT_PATH_LIST,
                        except_path_regex=EXCEPT_PATH_REGEX,
                        )
    _app.add_middleware(CORSMiddleware,
                        allow_origins=conf().ALLOW_SITE,
                        allow_credentials=True,
                        allow_methods=["*"],
                        allow_headers=["*"],
                        )
    _app.add_middleware(TrustedHostMiddleware,
                        allowed_hosts=conf().TRUSTED_HOST,
                        except_path=["/health"],
                        )

    # 라우터 정의
    _app.include_router(index.router)
    _app.include_router(auth.router, tags=['Authentication'], prefix='/auth')
    return _app


app = create_app()
