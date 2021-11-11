from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.database.conn import db
from app.database.schema import Users
router = APIRouter()


@router.get("/")
async def index(session: Session = Depends(db.session)):
    """
    ELB 상태 체크용 API
    :return:
    """
    # 쿼리 예시: 기존 방식
    user = Users(status='active', name='ehdrl')
    session.add(user)
    session.commit()

    # 쿼리 예시: schema.BaseMixin의 create 메서드 사용
    Users().create(session, auto_commit=True,
                   name='동기')

    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")
