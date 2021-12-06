from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    Enum, Boolean, ForeignKey,
)
from sqlalchemy.orm import Session

from app.database.conn import Base, db


class BaseMixin:
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.utc_timestamp())
    updated_at = Column(DateTime, nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp())

    def __init__(self):
        """ init 은 실행되지 않는다. 다만 아래 변수를 쓸 것이라고 알리기 위해 정의해 두었다. """
        self._q = None
        self._session = None

    def all_columns(self):
        """ 테이블에 있는 모든 칼럼을 받아서 list로 반환한다."""
        return [c for c in self.__table__.columns if c.primary_key is False and c.name != "created_at"]

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def create(cls, session: Session, auto_commit=False, **kwargs):
        """
        테이블 데이터 적재 전용 함수
        :param session:
        :param auto_commit: 자동 커밋 여부
        :param kwargs: 적재 할 데이터
        :return:
        """
        obj = cls()
        for col in obj.all_columns():
            col_name = col.name
            if col_name in kwargs:
                setattr(obj, col_name, kwargs.get(col_name))
        session.add(obj)
        session.flush()
        if auto_commit:
            session.commit()
        return obj

    @classmethod
    def get(cls, **kwargs):
        """ select하는 것. 1개의 값을 가졍올 때 사용."""
        session = next(db.session())
        query = session.query(cls)
        for key, val in kwargs.items():
            col = getattr(cls, key)
            query = query.filter(col == val)

        if query.count() > 1:
            raise Exception("1개의 값만 리턴 가능합니다. 2개 이상이 검색되었습니다.")
        result = query.first()
        session.close()
        return result

    @classmethod
    def filter(cls, session: Session = None, **kwargs):
        """
        여러 row를 가져온다.
        :param session:
        :param kwargs:
        :return:
        """
        cond = []
        for key, val in kwargs.items():
            key = key.split("__")
            if len(key) > 2:
                raise Exception("No 2 more dunders")
            col = getattr(cls, key[0])
            if len(key) == 1:
                cond.append((col == val))
            elif len(key) == 2 and key[1] == 'gt':
                cond.append((col > val))
            elif len(key) == 2 and key[1] == 'gte':
                cond.append((col >= val))
            elif len(key) == 2 and key[1] == 'lt':
                cond.append((col < val))
            elif len(key) == 2 and key[1] == 'lte':
                cond.append((col <= val))
            elif len(key) == 2 and key[1] == 'in':
                cond.append((col.in_(val)))

        obj = cls()
        if session:
            obj._session = session
            obj._sess_served = True
        else:
            obj._session = next(db.session())
            obj._sess_served = False
        query = obj._session.query(cls)
        query = query.filter(*cond)
        obj._q = query  # filter 는 직접 쿼리해서 반환하지 않기 때문에 일단 담아 둔 다음 아래 메서드들에서 쿼리를 마친다.
        return obj

    @classmethod
    def cls_attr(cls, col_name=None):
        if col_name:
            col = getattr(cls, col_name)
            return col
        else:
            return cls

    def order_by(self, *args: str):
        for a in args:
            if a.startswith("-"):
                col_name = a[1:]
                is_asc = False
            else:
                col_name = a
                is_asc = True
            col = self.cls_attr(col_name)
            self._q = self._q.order_by(col.asc()) if is_asc else self._q.order_by(col.desc())
        return self

    def update(self, sess: Session = None, auto_commit: bool = False, **kwargs):
        cls = self.cls_attr()
        if sess:
            query = sess.query(cls)
        else:
            sess = next(db.session())
            query = sess.query(cls)
        self.close()
        return query.update(**kwargs)

    def first(self):
        result = self._q.first()
        self.close()
        return result

    def delete(self, auto_commit: bool = False, **kwargs):
        self._q.delete()
        if auto_commit:
            self._session.commit()
        self.close()

    def all(self):
        result = self._q.all()
        self.close()
        return result

    def count(self):
        result = self._q.count()
        self.close()
        return result

    def dict(self, *args: str):
        q_dict = {}
        for c in self.__table__.columns:
            if c.name in args:
                q_dict[c.name] = getattr(self, c.name)

        return q_dict

    def close(self):
        if self._sess_served:
            self._session.commit()
            self._session.close()
        else:
            self._session.flush()


class Users(Base, BaseMixin):
    """ Base는 conn에 객체로 정의한 sqlalchemy의 declarative_base()임
    """
    __tablename__ = "users"
    status = Column(Enum("active", "deleted", "blocked"), default="active")
    email = Column(String(length=255), nullable=True)
    pw = Column(String(length=2000), nullable=True)
    name = Column(String(length=255), nullable=True)
    phone_number = Column(String(length=20), nullable=True, unique=True)
    profile_img = Column(String(length=1000), nullable=True)
    sns_type = Column(Enum("FB", "G", "K"), nullable=True)
    marketing_agree = Column(Boolean, nullable=True, default=True)


class ApiKeys(Base, BaseMixin):
    __tablename__ = "api_keys"
    access_key = Column(String(length=64), nullable=False, index=True)
    secret_key = Column(String(length=64), nullable=False)
    user_memo = Column(String(length=40), nullable=True)
    status = Column(Enum("active", "stopped", "deleted"), default="active")
    is_whitelisted = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
