

class ImageCaptchaView(APIView):
    @staticmethod
    def _random_code(length=5):
        """生成随机验证码"""
        chars = string.ascii_letters + string.digits  # abcABC123
        return ''.join(random.choices(chars, k=length))

    def get(self, request):
        """生成图片验证码并返回给前端"""
        # 生成随机验证码
        code = self._random_code()

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

