from rest_framework import serializers

# POST 请求序列化器
class CaptchaVerifySerializer(serializers.Serializer):
    captcha_id = serializers.CharField(required=True)
    captcha_code = serializers.CharField(required=True)



