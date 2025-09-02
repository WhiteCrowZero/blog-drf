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
    new_mail = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")],
        source='email'
    )

    def validate(self, attrs):
        email = attrs.get('email')
        new_email = attrs.get('new_email')
        if email == new_email:
            raise serializers.ValidationError({"email": "两次输入的邮箱不能相同"})


class EmailSendVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")]
    )
