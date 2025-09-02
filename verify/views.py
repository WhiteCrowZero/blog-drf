import base64
import random
import re
import string
import uuid

from django.conf import settings
from django.http import JsonResponse
from captcha.image import ImageCaptcha
from apps.verify.services import cache_verify_service
from rest_framework.permissions import AllowAny
from utils.base_view import BaseView
from .services import sms_service, email_service
from utils import check
from rest_framework.generics import GenericAPIView
from services import auth

class ImageCaptchaView(GenericAPIView):
    permission_classes = [AllowAny]

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
        cache_verify_service.set_verify_code(key, code, exp=settings.CAPTCHA_EXPIRE_SECONDS)

        # 组织响应数据
        data = {
            "captcha_id": captcha_id,
            "captcha_image": f"data:image/png;base64,{img_base64}"
        }
        return JsonResponse(data)


    def post(self, request):
        """验证前端提交的验证码"""
        data = request.data
        captcha_id = data.get('captcha_id')
        user_code = data.get('captcha_code')
        if not all([captcha_id, user_code]):
            return JsonResponse({'code': 400, 'message': '参数不完整'}, status=400)

        is_valid, message = check.check_capcha(captcha_id, user_code)
        # 验证验证码
        if not is_valid:
            return JsonResponse({'code': 400, 'message': message}, status=400)

        return JsonResponse({'code': 200, 'message': '验证码正确'})

