
from services.auth import make_random_verify_code
from verify.tasks import send_email, send_sms

class SendService(abc.ABC):
    @staticmethod
    def _random_code(length=6):
        chars = string.ascii_letters
        return ''.join(random.choices(chars, k=length))

    def send(self, target):
        pass


class SmsService(SendService):
    def send(self, phone):
        # 生成验证码
        verify_code = self._random_code()
        key = f'phone:{phone}'
        cache_verify_service.set_verify_code(key, verify_code)

        # 发送次数限制
        times_key = f'phone:times:{phone}'
        times = cache_verify_service.get_verify_code(times_key)
        if times is None:
            times = 0
        if times >= settings.MAX_SEND_TIMES:
            return False, f'发送次数过多，{settings.SMS_EXPIRE_SECONDS / 60} 分钟后重试'
        times += 1
        cache_verify_service.set_verify_code(times_key, times)

        # 发送间隔限制
        last_key = f'phone:last:{phone}'
        if times > 1:
            last_time = cache_verify_service.get_verify_code(last_key)
            if last_time is not None:
                return False, f'发送间隔过短，{settings.SEND_INTERVAL} 秒后重试'
        cache_verify_service.set_verify_code(last_key, True, exp=settings.SEND_INTERVAL)

        # 发送短信
        send_sms.delay(phone, verify_code)
        return True, None


class EmailService(SendService):
    def send(self, email):
        # 生成验证码
        verify_code = self._random_code()
        key = f'email:{email}'
        cache_verify_service.set_verify_code(key, verify_code)

        # 发送次数限制
        times_key = f'email:times:{email}'
        times = cache_verify_service.get_verify_code(times_key)
        if times is None:
            times = 0
        if times >= settings.MAX_SEND_TIMES:
            return False, f'发送次数过多，{settings.EMAIL_EXPIRE_SECONDS / 60} 分钟后重试'
        times += 1
        cache_verify_service.set_verify_code(times_key, times)

        # 发送间隔限制
        last_key = f'email:last:{email}'
        if times > 1:
            last_time = cache_verify_service.get_verify_code(last_key)
            if last_time is not None:
                return False, f'发送间隔过短，{settings.SEND_INTERVAL} 秒后重试'
        cache_verify_service.set_verify_code(last_key, True, exp=settings.SEND_INTERVAL)

        # 发送短信
        send_email.delay(email, verify_code)
        return True, None


sms_service = SmsService()
email_service = EmailService()
