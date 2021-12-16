from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging


def _database_exist(engine, schema_name):
    query = f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{schema_name}'"
    print("query", query)
    with engine.connect() as conn:
        result_proxy = conn.execute(query)
        result = result_proxy.scalar()
        print("_database_exist: ", bool(result))
        return bool(result)


def _drop_database(engine, schema_name):
    with engine.connect() as conn:
        conn.execute(f"DROP DATABASE {schema_name};")


def _create_database(engine, schema_name):
    with engine.connect() as conn:
        conn.execute(f"CREATE DATABASE {schema_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;")


class SQLAlchemy:
    def __init__(self, app: FastAPI = None, **kwargs):
        self._engine = None
        self._session = None
        if app is not None:
            self.init_app(app=app, **kwargs)

    def init_app(self, app: FastAPI, **kwargs):
        """
        DB 초기화 함수
        :param app: FastAPI 인스턴스
        :param kwargs:
        :return:
        """
        database_url = kwargs.get("DB_URL")
        pool_recycle = kwargs.setdefault("DB_POOL_RECYCLE", 900)
        echo = kwargs.setdefault("DB_ECHO", True)
        is_testing = kwargs.setdefault("TEST_MODE", False)

        self._engine = create_engine(
            database_url,
            echo=echo,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )

        if is_testing:  # create schema
            db_url = self._engine.url
            print(f"\n{db_url}")
            print(db_url.drivername)
            print(db_url.username)
            print(db_url.host)
            print(db_url.database)

            if db_url.host != "localhost":
                raise Exception("db host must be 'localhost' in test environment")
            except_schema_db_url = f"{db_url.drivername}://{db_url.username}:admin@{db_url.host}"
            schema_name = db_url.database
            temp_engine = create_engine(except_schema_db_url, echo=echo, pool_recycle=pool_recycle, pool_pre_ping=True)
            if _database_exist(temp_engine, schema_name):
                _drop_database(temp_engine, schema_name)
            # _drop_database(temp_engine, schema_name)
            _create_database(temp_engine, schema_name)
            temp_engine.dispose()
        self._session = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

        @app.on_event("startup")  # app이 실행될때 함수를 실행해준다.
        def startup():
            self._engine.connect()
            logging.info("DB connected.")

        @app.on_event("shutdown")  # app이 종료될때 함수를 실행해준다.
        def shutdown():
            self._session.close_all()
            self._engine.dispose()
            logging.info("DB disconnected")

        # @app.on_event("startup")
        # def if_db_not_exists():
        #     if not database_exists(self._engine.url):
        #         print("존재하지 않는 Database입니다. database_url에 따라 database를 생성합니다.")
        #         create_database(self._engine.url)

        # @app.on_event("startup")
        # def if_table_not_exists():
        #     if not self._engine.has_table(self._engine, ):
        #         pass

    def get_db(self):
        """
        요청마다 DB 세션 유지 함수
        :return:
        """
        if self._session is None:
            raise Exception("must be called 'init_app'")
        db_session = None
        try:
            db_session = self._session()
            yield db_session
        finally:
            db_session.close()

    @property
    def session(self):
        return self.get_db

    @property
    def engine(self):
        return self._engine


db = SQLAlchemy()
Base = declarative_base()
