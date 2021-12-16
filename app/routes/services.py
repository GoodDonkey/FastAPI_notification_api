import json
import os
from time import time, sleep

import requests
import yagmail
from fastapi import APIRouter
from fastapi.logger import logger
from starlette.background import BackgroundTasks
from starlette.requests import Request

from app.errors import exceptions as ex
from app.models import MessageOk, KakaoMsgBody, SendEmail

router = APIRouter(prefix='/services')


@router.get('')
async def get_all_services(request: Request):
    """ Api Key의 access_key를 주면 누구인지 email을 반환한다.
        반드시 로컬에서만 사용할 것. """
    return dict(your_email=request.state.user.email)


@router.post('/kakao/send')
async def send_kakao(request: Request, body_param: KakaoMsgBody):
    token = os.environ.get("KAKAO_KEY", "1qDf2uClCgDZuurq4XJKXJtyk2b35xcTiWcHSQo9cxgAAAF9zA8DMA")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}

    body = dict(object_type="text",
                text=body_param.msg,
                link=dict(web_url="https://donkeyFastAPI.com",
                          mobile_url="https://donkeyFastAPI.com"),
                button_title="지금 확인")
    data = {"template_object": json.dumps(body, ensure_ascii=False)}
    print(data)
    res = requests.post(url="https://kapi.kakao.com/v2/api/talk/memo/default/send", headers=headers, data=data)
    try:
        res.raise_for_status()  # 200, 300 대가 아니면 에러를 raise
        if res.json()["result_code"] != 0:  # 성공하면 result_code == 0 임.
            raise Exception("KAKAO SEND FAILED")
    except Exception as e:
        print(res.json())
        logger.warning(e)
        raise ex.KakaoSendFailureEx

    return MessageOk()


@router.get('/kakao/get_friends')
async def get_kakao(request: Request):
    token = os.environ.get("KAKAO_KEY", "*********")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-www-form-urlencoded"}

    # body = dict(offset="text",
    #             limit=body_param.msg,
    #             order=dict(web_url="https://donkeyFastAPI.com",
    #                       mobile_url="https://donkeyFastAPI.com"),
    #             friend_order="지금 확인")
    # data = {"template_object": json.dumps(body, ensure_ascii=False)}

    res = requests.post(url="https://kapi.kakao.com/v1/api/talk/friends", headers=headers)
    try:
        res.raise_for_status()  # 200, 300 대가 아니면 에러를 raise
        if res.json()["result_code"] != 0:  # 성공하면 result_code == 0 임.
            raise Exception("KAKAO SEND FAILED")
    except Exception as e:
        print(res.json())
        logger.warning(e)
        raise ex.KakaoSendFailureEx

    return MessageOk()


email_content = """
<div style='margin-top:0cm;margin-right:0cm;margin-bottom:10.0pt;margin-left:0cm;line-height:115%;font-size:15px;font-family:"Calibri",sans-serif;border:none;border-bottom:solid #EEEEEE 1.0pt;padding:0cm 0cm 6.0pt 0cm;background:white;'>

<p style='margin-top:0cm;margin-right:0cm;margin-bottom:11.25pt;margin-left:0cm;line-height:115%;font-size:15px;font-family:"Calibri",sans-serif;background:white;border:none;padding:0cm;'><span style='font-size:25px;font-family:"Helvetica Neue";color:#11171D;'>{}님! Aristoxeni ingenium consumptum videmus in musicis?</span></p>

</div>

<p style='margin-top:0cm;margin-right:0cm;margin-bottom:11.25pt;margin-left:0cm;line-height:17.25pt;font-size:15px;font-family:"Calibri",sans-serif;background:white;vertical-align:baseline;'><span style='font-size:14px;font-family:"Helvetica Neue";color:#11171D;'>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quid nunc honeste dicit? Tum Torquatus: Prorsus, inquit, assentior; Duo Reges: constructio interrete. Iam in altera philosophiae parte. Sed haec omittamus; Haec para/doca illi, nos admirabilia dicamus. Nihil sane.</span></p>

<p style='margin-top:0cm;margin-right:0cm;margin-bottom:10.0pt;margin-left:0cm;line-height:normal;font-size:15px;font-family:"Calibri",sans-serif;background:white;'><strong><span style='font-size:24px;font-family:"Helvetica Neue";color:#11171D;'>Expressa vero in iis aetatibus, quae iam confirmatae sunt.</span></strong></p>

<p style='margin-top:0cm;margin-right:0cm;margin-bottom:11.25pt;margin-left:0cm;line-height:17.25pt;font-size:15px;font-family:"Calibri",sans-serif;background:white;vertical-align:baseline;'><span style='font-size:14px;font-family:"Helvetica Neue";color:#11171D;'>Sit sane ista voluptas. Non quam nostram quidem, inquit Pomponius iocans; An tu me de L. Sed haec omittamus; Cave putes quicquam esse verius.&nbsp;</span></p>

<p style='margin-top:0cm;margin-right:0cm;margin-bottom:11.25pt;margin-left:0cm;line-height:17.25pt;font-size:15px;font-family:"Calibri",sans-serif;text-align:center;background:white;vertical-align:baseline;'><span style='font-size:14px;font-family:"Helvetica Neue";color:#11171D;'><img width="378" src="https://dl1gtqdymozzn.cloudfront.net/forAuthors/K6Sfkx4f2uH780YGTbEHvHcTX3itiTBtzDWeyswQevxp8jqVttfBgPu86ZtGC6owG.webp" alt="sample1.jpg" class="fr-fic fr-dii"></span></p>

<p>
<br>
</p>

"""


@router.post("email/send_by_gmail")
async def email_by_gmail(request: Request, mailing_list: SendEmail):
    """ 일반적인 방법. 6초정도 걸림 """
    t = time()
    _send_email(mailing_list=mailing_list.email_to)
    print("+*+*" * 30)
    print(str(round((time() - t) * 1000, 5)) + "ms")
    print("+*+*" * 30)
    return MessageOk()


@router.post("email/send_by_gmail2")
async def email_by_gmail2(request: Request, mailing_list: SendEmail, background_tasks: BackgroundTasks):
    t = time()
    background_tasks.add_task(
            _send_email, mailing_list=mailing_list.email_to
    )
    print("+*+*" * 30)
    print(str(round((time() - t) * 1000, 5)) + "ms")
    print("+*+*" * 30)
    return MessageOk()


def _send_email(**kwargs):
    mailing_list = kwargs.get("mailing_list", None)
    email_pw = os.environ.get("EMAIL_PW", None)
    email_addr = os.environ.get("EMAIL_ADDR", None)
    last_email = ""
    if mailing_list:
        try:
            yag = yagmail.SMTP({email_addr: "보낸이 이름"}, email_pw)
            # https://myaccount.google.com/u/1/lesssecureapps
            for m_l in mailing_list:
                contents = [
                    email_content.format(m_l.name)
                ]
                sleep(1)
                yag.send(m_l.email, '이렇게 한번 보내봅시다.', contents)
                last_email = m_l.email
            return True
        except Exception as e:
            print(e)
            print(last_email)
    print("발송 실패시 실패라고 알려야 합니다.")  # 미들웨어를 타지 않음. 따라서 직접 로그를 찍도록 알려야함.

