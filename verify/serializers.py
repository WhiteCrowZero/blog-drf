from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


# POST 请求序列化器
class CaptchaVerifySerializer(serializers.Serializer):
    captcha_id = serializers.CharField(required=True)
    captcha_code = serializers.CharField(required=True)


class EmailVerifySerializer(serializers.Serializer):
    verify_code = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    new_email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        new_email = attrs.get('new_email')

        if not email or not new_email:
            raise serializers.ValidationError({"errors": "原邮箱和新邮箱不能为空"})
        if email == new_email:
            raise serializers.ValidationError({"errors": "两次输入的邮箱不能相同"})
        # 校验新邮箱是否已存在
        if User.objects.filter(email=new_email).exists():
            raise serializers.ValidationError({"errors": "该邮箱已被注册"})

        return attrs


class EmailSendVerifySerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)

    def validated_new_email(self, value):
        # 校验新邮箱是否已存在
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError({"errors": "该邮箱已被注册"})
        return value


class EmailSendActivateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
