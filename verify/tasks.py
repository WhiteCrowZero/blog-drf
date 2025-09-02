
import base64
import hashlib
import logging
import time

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

from mysite.celery import app


@app.task
def send_email(email, verify_code):
    try:
        # 收件人列表格式化
        if isinstance(email, str):
            email = [email]

        # 邮件标题
        subject = getattr(settings, 'EMAIL_SUBJECT', 'XXX 邮件验证码')

        # HTML 邮件内容
        html_message = f"""
                    <p>尊敬的用户，您好！</p>
                    <p>感谢您注册 <strong>XX</strong>，请使用以下验证码完成注册：</p>
                    <p style="font-size: 22px; font-weight: bold; color: #FF4C4C;">{verify_code}</p>
                    <p>该验证码 <strong>{int(settings.EMAIL_EXPIRE_SECONDS / 60)} 分钟</strong> 内有效，请尽快使用。</p>
                    <p>如果您未进行过注册操作，请忽略此邮件。</p>
                    <hr>
                    <p style="color: gray; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
                """

        # 纯文本内容（避免部分邮箱不支持 HTML）
        plain_message = strip_tags(html_message)
        # 发件人
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')
        # 发送
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=email,
            html_message=html_message
        )
        logging.info(f'邮件发送到: {email}')
    except Exception as e:
        logging.error(f'邮件发送失败: {e}')


class Sms:
    base_url = 'https://app.cloopen.com:8883'

    def __init__(self, account_id, app_id, account_key, template_id):
        self.account_id = account_id
        self.app_id = app_id
        self.account_key = account_key
        self.template_id = template_id
        self.timestamp = time.strftime('%Y%m%d%H%M%S')
        pass

    def _get_url(self):
        url = self.base_url + f'/2013-12-26/Accounts/{self.account_id}/SMS/TemplateSMS?sig={self._get_signature()}'
        return url

    def _get_headers(self):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=utf-8',
            'Authorization': self._get_auth()
        }
        return headers

    def _get_body(self, phone_ls, code):
        body = {
            'to': ','.join(phone_ls),
            'appId': self.app_id,
            'templateId': self.template_id,
            'datas': [code, '5']
        }
        return body

    def _get_signature(self):
        md5 = hashlib.md5()
        md5.update(f'{self.account_id}{self.account_key}{self.timestamp}'.encode('utf-8'))
        return md5.hexdigest().upper()

    def run(self, phone, code):
        if len(code) > 4 or len(code) < 1:
            raise Exception('验证码长度不合法')

        url = self._get_url()
        headers = self._get_headers()
        body = self._get_body([phone], code)
        resp = requests.post(url=url, json=body, headers=headers)
        print(resp.json())
        return resp.json()

    def _get_auth(self):
        return base64.b64encode(f'{self.account_id}:{self.timestamp}'.encode('utf-8')).decode('utf-8')


sms_api = Sms(**settings.SMS_CONFIG)


@app.task
def send_sms(phone, verify_code):
    sms_api.run(phone, verify_code)
