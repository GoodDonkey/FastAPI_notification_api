from dataclasses import asdict

import uvicorn
from fastapi import FastAPI
from app.database.conn import db
from app.database.schema import Base
from app.common.config import conf

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

    # 미들웨어 정의

    # 라우터 정의
    _app.include_router(index.router)
    _app.include_router(auth.router, tags=['Authentication'], prefix='/auth')
    return _app


app = create_app()
