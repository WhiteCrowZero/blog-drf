from django.contrib import auth
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import UserContact
from services import auth

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """ 普通注册序列化器 """
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该用户名已被使用")]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
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
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not username and not email:
            raise serializers.ValidationError("请输入用户名或邮箱")

        user = None
        if username:
            user = authenticate(username=username, password=password)
        elif email:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("用户名/邮箱或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("用户账户已被禁用")

        attrs['user'] = user
        return attrs



class OauthLoginSerializer(serializers.ModelSerializer):
    """ 第三方 注册/登录 序列化器 """
    code = serializers.CharField()  # 前端提交的授权码

    class Meta:
        model = UserContact
        fields = ['type', 'code']

    def validate_type(self, value):
        if value not in dict(UserContact.CONTACT_CHOICES):
            raise serializers.ValidationError("不支持的第三方类型")
        return value

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("授权码不能为空")
        return value

    def validate(self, attrs):
        type = attrs.get('type')
        code = attrs.get('code')

        openid = auth.oauth_register(type, code)
        if not openid:
            raise serializers.ValidationError("第三方授权失败")

        attrs['openid'] = openid
        return attrs


class UserContactSerializer(serializers.ModelSerializer):
    """ 用户联系序列化器 """
    code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserContact
        fields = ['type', 'is_bound', 'code']

    def create(self, validated_data):
        type = validated_data['type']
        code = validated_data.get('code')

        openid = auth.oauth_register(type, code)
        if not openid:
            raise serializers.ValidationError("授权失败")

        return UserContact.objects.create(
            user=self.context['request'].user,
            type=type,
            openid=openid,
            is_bound=True
        )



class UserInfoSerializer(serializers.ModelSerializer):
    """ 用户信息序列化器 """
    username = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该用户名已被使用")]
    )
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all(), message="该邮箱已被注册")]
    )
    # fans = serializers.IntegerField(source="follows.count", read_only=True)
    articles = serializers.IntegerField(source="articles.count", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'bio', 'avatar', 'last_name', 'first_name', 'email', 'articles']
        extra_kwargs = {
            'id': {'read_only': True}
        }
