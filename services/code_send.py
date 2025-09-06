import uuid
from django.conf import settings

from services.auth import make_random_verify_code
from services.tasks import send_email
from services.cache_utils import cache_verify_service


class EmailService:
    EMAIL_CACHE_NAME = 'email'

    def send_activate(self, email):
        """ 一次性激活验证码，不做次数限制 """
        verify_code = uuid.uuid4().hex
        verify_code.replace('-', '')
        verify_url = f'{settings.EMAIL_ACTIVATE_RETURN_URL}/verify/email/activate?verify_code={verify_code}'
        key = f'email:{verify_code}'
        cache_verify_service.set_verify_code(key, email, cache=self.EMAIL_CACHE_NAME)

        send_email.delay(email, verify_code=verify_url)
        return True

    def send_verify(self, email):
        """ 邮箱更改验证码，次数频率进行限制 """
        # 生成验证码
        verify_code = make_random_verify_code(length=6)
        key = f'email:{email}'
        cache_verify_service.set_verify_code(key, verify_code, cache=self.EMAIL_CACHE_NAME)

        # 发送邮件
        send_email.delay(email, verify_code, mode='verify')

        return True

    def check_verify_code(self, email, verify_code):
        key = f'email:{email}'
        right_code = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
        # 一次性，校验一次后，无论对错，立即删除
        cache_verify_service.del_verify_code(key, cache=self.EMAIL_CACHE_NAME)
        if verify_code != right_code:
            return False
        return True

    def check_activate_code(self, verify_code):
        key = f'email:{verify_code}'
        email = cache_verify_service.get_verify_code(key, self.EMAIL_CACHE_NAME)
        # 一次性，校验一次后，无论对错，立即删除
        cache_verify_service.del_verify_code(key, cache=self.EMAIL_CACHE_NAME)
        if not email:
            return None
        return email


email_service = EmailService()
