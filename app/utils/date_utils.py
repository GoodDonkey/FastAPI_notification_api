from datetime import datetime, date, timedelta


class D:
    """ 시간 정보를 로그 찍는데 편하게 하기 위해 만든 클래스 """

    def __init__(self, *args):
        self.utc_now = datetime.utcnow()
        self.timedelta = 0

    @classmethod
    def datetime(cls, diff: int = 0) -> datetime:
        return cls().utc_now + timedelta(hours=diff) if diff > 0 else cls().utc_now + timedelta(hours=diff)

    @classmethod
    def date(cls, diff: int = 0) -> date:
        return cls.datetime(diff=diff).date()

    @classmethod
    def date_num(cls, diff: int = 0) -> int:
        return int(cls.date(diff=diff).strftime('%Y%m%d'))
