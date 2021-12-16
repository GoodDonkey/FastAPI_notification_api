from app.database.conn import db
from app.database.schema import Users


def test_registration(client, session):
    """
    레버 로그인
    :param client:
    :param session:
    :return:
    """
    user = dict(email="donkeytest@example.com", pw="123", name="donkey", phone="01099999999")
    res = client.post("api/auth/register/email", json=user)
    res_body = res.json()
    print(res.json())
    assert res.status_code == 201
    assert "Authorization" in res_body


def test_registration_exist_email(client, session):
    """
    레버 로그인
    :param client:
    :param session:
    :return:
    """
    user = dict(email="Hello@dingrr.com", pw="123", name="라이언", phone="01099999999")
    db_user = Users.create(session=session, **user)
    session.commit()
    res = client.post("api/auth/register/email", json=user)  # 이미 db에 등록된 유저를 다시 api를 통해 가입시키면 에러가 나야함.
    res_body = res.json()
    assert res.status_code == 400
    assert 'EMAIL_EXISTS' == res_body["msg"]
