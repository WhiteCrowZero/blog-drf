import io
import uuid

from PIL import Image
from django.contrib import auth
from django.contrib.auth import get_user_model, authenticate
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from services import auth, oauth
from services.auth import CaptchaValidateMixin
from users.models import UserContact

User = get_user_model()


class RegisterSerializer(CaptchaValidateMixin, serializers.ModelSerializer):
    """ 普通注册序列化器 """
    # 密码和二次确认密码
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    # 用户和邮箱保持唯一性，防止重复
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该用户名已被使用")]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")]
    )

    # 额外添加的校验码字段
    captcha_id = serializers.CharField(write_only=True)
    captcha_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'captcha_id', 'captcha_code']

    def validate(self, attrs):
        # 单独使用工具类校验 captcha
        attrs = self.validate_captcha(attrs)  # 直接传 attrs
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def validate_username(self, value):
        if '@' in value:
            raise serializers.ValidationError({"username": "不能含有 @ 符号"})
        return value

    def create(self, validated_data):
        # 保留密码字段
        password = validated_data.pop('password')

        # 其余字段检验完后丢弃
        validated_data.pop('confirm_password')
        validated_data.pop('captcha_id')
        validated_data.pop('captcha_code')

        # 其余字段创建模型
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """ 普通登录序列化器 """
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        identifier = attrs.get('username') or attrs.get('email')
        password = attrs.get('password')

        if not identifier:
            raise serializers.ValidationError("用户名或邮箱不能为空")

        # authenticate 会自动判断用户名或邮箱
        user = authenticate(username=identifier, password=password)

        # 检查用户状态
        if not user:
            raise serializers.ValidationError("用户名/邮箱或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("用户账户已被禁用")

        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    """ 密码重置序列化器 """
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs


class OauthLoginSerializer(serializers.ModelSerializer):
    """ 第三方 注册/登录 序列化器 """
    code = serializers.CharField()  # 前端提交的授权码

    class Meta:
        model = UserContact
        fields = ['type', 'code']

    def validate_type(self, value):
        if value not in dict(oauth.CONTACT_CHOICES):
            raise serializers.ValidationError("不支持的第三方类型")
        return value

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("授权码不能为空")
        return value

    def validate(self, attrs):
        type = attrs.get('type')
        code = attrs.get('code')
        if not code:
            raise serializers.ValidationError("授权码不能为空")

        openid = auth.oauth_authentication(type, code)
        if not openid:
            raise serializers.ValidationError("第三方授权失败")

        attrs['openid'] = openid
        return attrs


# 拆分出来两个序列化器，一个用于联系方式绑定，一个用于联系方式解绑
class UserContactBindSerializer(serializers.ModelSerializer):
    """ 联系方式绑定序列化器 """
    code = serializers.CharField(write_only=True)

    class Meta:
        model = UserContact
        fields = ['type', 'code']

    def update(self, instance, validated_data):
        code = validated_data['code']
        openid = auth.oauth_authentication(instance.type, code)
        if not openid:
            raise serializers.ValidationError("授权失败")

        instance.is_bound = True
        instance.openid = openid
        instance.save()
        return instance


class UserContactUnbindSerializer(serializers.ModelSerializer):
    """ 联系方式解绑序列化器 """

    class Meta:
        model = UserContact
        fields = ['type', 'is_bound']

    def update(self, instance, validated_data):
        instance.is_bound = False
        instance.openid = None
        instance.save()
        return instance


class UserContactSerializer(serializers.ModelSerializer):
    """ 用户联系序列化器 """
    code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserContact
        fields = ['type', 'is_bound', 'code']
        extra_kwargs = {
            "is_bound": {"read_only": True}
        }

    def create(self, validated_data):
        type = validated_data['type']
        code = validated_data.get('code')
        if not code:
            raise serializers.ValidationError("授权码不能为空")

        openid = auth.oauth_authentication(type, code)
        if not openid:
            raise serializers.ValidationError("授权失败")

        user = self.context['request'].user
        user_contact, created = UserContact.objects.get_or_create(
            user=user,
            type=type,
            defaults={'openid': openid, 'is_bound': True}
        )

        if not created and not user_contact.is_bound:
            user_contact.is_bound = True
            user_contact.openid = openid  # 更新 openid
            user_contact.save()

        return user_contact


class UserInfoSerializer(serializers.ModelSerializer):
    """ 用户信息序列化器 """
    username = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该用户名已被使用")]
    )
    # 邮箱的修改单独通过其他接口验证
    email = serializers.EmailField(read_only=True)
    followers = serializers.IntegerField(source="followers.count", read_only=True)
    articles_count = serializers.IntegerField(source="articles.count", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'last_name', 'first_name', 'email', 'articles_count', 'followers']
        extra_kwargs = {
            'id': {'read_only': True}
        }


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'avatar']
        extra_kwargs = {
            'id': {'read_only': True}
        }

    def validate(self, attrs):
        avatar_file = attrs.get("avatar")
        if avatar_file:
            # 文件格式检查
            if not avatar_file.content_type.startswith("image/"):
                raise serializers.ValidationError("必须上传图片文件")

            # 文件大小（字节）
            size = avatar_file.size
            if size > 10 * 1024 * 1024:
                raise serializers.ValidationError("文件超过 10MB")
        else:
            raise serializers.ValidationError("上传文件不能为空")

        return attrs

    @staticmethod
    def _process_image(uploaded_file, target_size=400 * 1024):
        # 打开图片
        img = Image.open(uploaded_file)
        img = img.convert("RGB")  # 避免 PNG 转 JPG 出错

        # 压缩循环（保证小于400KB）
        quality = 95
        while True:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", optimize=True, quality=quality)
            size = buffer.tell()
            if size <= target_size or quality <= 20:
                break
            quality -= 5

        buffer.seek(0)
        return buffer  # 可以直接传给 MinIO 客户端上传

    def create(self, validated_data):
        avatar_file = validated_data.get("avatar")
        buffer = self._process_image(avatar_file)

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.jpg"

        # Django 默认使用 DEFAULT_FILE_STORAGE 上传到 MinIO
        validated_data["avatar"] = ContentFile(buffer.read(), name=filename)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        avatar_file = validated_data.get("avatar")
        buffer = self._process_image(avatar_file)

        filename = f"{instance.id}.jpg"
        validated_data["avatar"] = ContentFile(buffer.read(), name=filename)
        return super().update(instance, validated_data)

# TODO: 文件去重