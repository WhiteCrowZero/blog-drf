import base64
import uuid
from django.conf import settings
from captcha.image import ImageCaptcha
from rest_framework.throttling import AnonRateThrottle
from twisted.persisted.aot import NonFormattableDict

from services.cache_utils import cache_verify_service
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from services.code_send import sms_service, email_service
from rest_framework.generics import GenericAPIView
from verify.serializers import CaptchaVerifySerializer
from services import auth
from django.core.cache import caches


class CaptchaRateThrottle(AnonRateThrottle):
    rate = '5/min'  # 每个用户每分钟最多访问5次


class ImageCaptchaView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [CaptchaRateThrottle]
    serializer_class = CaptchaVerifySerializer

    CAPTCHA_CACHE_NAME = "captcha"

    def get(self, request):
        """生成图片验证码并返回给前端"""
        # 生成随机验证码
        code = auth.make_random_verify_code()

        # 生成验证码图片
        image = ImageCaptcha(width=280, height=90)
        img_bytes = image.generate(code).read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        # 将验证码保存到 Redis
        captcha_id = str(uuid.uuid4()).replace('-', '')
        key = f'captcha:{captcha_id}'
        cache_verify_service.set_verify_code(key, code, cache=self.CAPTCHA_CACHE_NAME,
                                             exp=settings.CAPTCHA_EXPIRE_SECONDS)

        # 组织响应数据
        data = {
            "captcha_id": captcha_id,
            "captcha_image": f"data:image/png;base64,{img_base64}"
        }
        return Response(data, status=status.HTTP_200_OK)

    def _check_captcha(self, captcha_id, user_code):
        key = f'captcha:{captcha_id}'
        right_code = cache_verify_service.get_verify_code(key, cache=self.CAPTCHA_CACHE_NAME)
        if user_code != right_code:
            return False
        return True

    def post(self, request):
        """验证前端提交的验证码"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        captcha_id = serializer.validated_data['captcha_id']
        user_code = serializer.validated_data['captcha_code']

        is_valid = self._check_captcha(captcha_id, user_code)
        # 验证验证码
        if not is_valid:
            return Response({"errors": "验证码错误"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "验证码正确"}, status=status.HTTP_200_OK)
