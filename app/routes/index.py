from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.requests import Request

from app.database.conn import db
from app.database.schema import Users
router = APIRouter()


@router.get("/")
async def index(session: Session = Depends(db.session)):
    """
    ELB 상태 체크용 API
    :return:
    """
    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")

@router.get("/test")
async def test(request: Request):
    """
    ELB 상태 체크용 API
    :return:
    """
    print("state.user", request.state.user)  # 미들웨어에서 저장한 state.user 정보를 확인한다.
    current_time = datetime.utcnow()
    return Response(f"Notification API (UTC: {current_time.strftime('%Y.%m.%d %H:%M:%S')})")
