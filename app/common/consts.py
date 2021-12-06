# 환경 별로 공통된 값을 정의한다.

JWT_SECRET = "donkey"  # 여기서는 임의로 지정하였지만, 나중엔 AWS의 서비스를 사용하여 동적으로 설정할 예정.
JWT_ALGORITHM = "HS256"

EXCEPT_PATH_LIST = ["/", "/openapi.json"]
EXCEPT_PATH_REGEX = "^(/docs|/redoc|/api/auth)"
