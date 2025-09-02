import time
import uuid
from django.conf import settings
from verify.tasks import send_email
from services.cache_utils import cache_verify_service


class EmailService:
    EMAIL_CACHE_NAME = 'email'

    @staticmethod
    def send_activate(email):
        """ 一次性激活验证码，不做次数限制 """
        verify_code = uuid.uuid4().hex
        verify_url = f'127.0.0.1:8000/verify/email/activate?verify_code={verify_code}'
        key = f'email:{verify_code}'
        cache_verify_service.set_verify_code(key, email)

        send_email.delay(email, verify_url)
        return True

    @staticmethod
    def send_verify(email):
        """ 邮箱更改验证码，次数频率进行限制 """
        now_ts = int(time.time())  # 当前时间戳，秒级

        # 发送间隔限制
        last_key = f'email:last:{email}'
        last_ts = cache_verify_service.get_verify_code(last_key)
        if last_ts and now_ts - int(last_ts) < settings.SEND_INTERVAL:
            return False

        # 生成验证码
        verify_code = uuid.uuid4().hex
        key = f'email:{email}'
        cache_verify_service.set_verify_code(key, verify_code)

        # 发送邮件
        send_email.delay(email, verify_code, mode='verify')

        # 保存最后发送时间
        cache_verify_service.set_verify_code(last_key, now_ts, exp=settings.SEND_INTERVAL)

        return True

    def check_verify_code(self, email, verify_code):
        key = f'email:{email}'
        right_code = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
        cache_verify_service.delete_verify_code(key, cache=self.EMAIL_CACHE_NAME)
        if verify_code != right_code:
            return False
        return True

    def check_activate_code(self, verify_code):
        key = f'email:{verify_code}'
        email = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
        cache_verify_service.delete_verify_code(key, cache=self.EMAIL_CACHE_NAME)
        if not email:
            return None
        return email


email_service = EmailService()
