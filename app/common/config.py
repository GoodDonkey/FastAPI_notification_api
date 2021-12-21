from dataclasses import dataclass, asdict
from os import path, environ

base_dir = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
print(base_dir)

""" dict 형태로 쓰기 위해 dataclass로 감싼다. """


@dataclass
class Config:
    """ 기본 Configuration """
    BASE_DIR = base_dir  # /FastAPI 를 가리킴

    DB_POOL_RECYCLE: int = 900
    DB_ECHO: bool = False  # db 생성, 데이터 갱신시 에코
    DEBUG = False
    TEST_MODE: bool = False
    DB_URL: str = environ.get("DB_URL", "mysql+pymysql://root:admin@localhost/Fast_API?charset=utf8mb4")


@dataclass
class LocalConfig(Config):
    PROJ_RELOAD: bool = True
    TRUSTED_HOST = ["*"]
    ALLOW_SITE = ["*"]
    DEBUG = True


@dataclass
class ProdConfig(Config):
    PROJ_RELOAD: bool = False
    ALLOW_SITE = ["*"]


@dataclass
class TestConfig(Config):
    DB_URL: str = "mysql+pymysql://root:admin@localhost/Fast_API_test2?charset=utf8mb4"
    TRUSTED_HOST = ["*"]
    ALLOW_SITE = ["*"]
    TEST_MODE: bool = True


def conf():
    """ 환경 불러오기"""
    config = dict(prod=ProdConfig, local=LocalConfig, test=TestConfig)
    return config[environ.get("API_ENV", "local")]()
