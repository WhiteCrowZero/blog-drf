import uuid

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView, ListCreateAPIView, ListAPIView, \
    RetrieveAPIView, GenericAPIView

from services.code_send import email_service
from .models import UserContact
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, LoginSerializer, OauthLoginSerializer, \
    UserInfoSerializer, UserContactSerializer
from rest_framework.response import Response
from services import auth, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny

User = get_user_model()


class RegisterView(GenericAPIView):
    """ 用户注册视图（普通注册，只支持邮箱+用户名） """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 发送激活链接
        email_service.send_activate(user.email)

        access_token, refresh_token = auth.generate_tokens_for_user(user)
        return Response({
            "user_id": user.id,
            "username": user.username,
            "access": access_token,
            "refresh": refresh_token
        })


class LoginView(GenericAPIView):
    """ 普通登录视图（邮箱/用户名登录） """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        access_token, refresh_token = auth.generate_tokens_for_user(user)
        return Response({
            "user_id": user.id,
            "username": user.username,
            "access": access_token,
            "refresh": refresh_token
        })


class LogoutView(APIView):
    """ 通用登出视图 """

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            print(e)
            return Response({"detail": "登出失败"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "登出成功"}, status=status.HTTP_200_OK)


class OauthLoginView(GenericAPIView):
    """ 第三方登录视图（可以选择登录后绑定，未绑定新创建账户） """
    serializer_class = OauthLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        type = serializer.validated_data['type']
        openid = serializer.validated_data['openid']

        try:
            user_contact = UserContact.objects.get(type=type, openid=openid)
            user = user_contact.user
        except UserContact.DoesNotExist:
            # 创建新账号（注册）
            with transaction.atomic():
                # 创建 User
                user = User.objects.create_user(
                    username=f"{type}-{uuid.uuid4()}",
                    password=auth.make_random_password(),
                    is_active_account = True
                )

                # 创建 UserContact
                user_contact = UserContact.objects.create(
                    user=user,
                    type=type,
                    openid=openid,
                    is_bound=True
                )

        access_token, refresh_token = auth.generate_tokens_for_user(user)
        return Response({
            "user_id": user.id,
            "username": user.username,
            "access": access_token,
            "refresh": refresh_token
        })


class UserContactView(ListCreateAPIView):
    """ 用户绑定的第三方登录方式视图，展示或创建 """
    serializer_class = UserContactSerializer
    pagination_class = None  # 关闭分页

    def get_queryset(self):
        return UserContact.objects.filter(user=self.request.user)


class UserContactDetailView(RetrieveUpdateDestroyAPIView):
    """ 用户绑定的第三方登录方式视图，修改或删除 """
    serializer_class = UserContactSerializer
    lookup_field = 'type'  # URL中传 type

    def get_object(self):
        type = self.kwargs['type']
        obj, _ = UserContact.objects.get_or_create(user=self.request.user, type=type)
        return obj

    # PUT / PATCH -> 绑定或更新
    def perform_update(self, serializer):
        code = self.request.data.get('code')
        if not code:
            raise serializers.ValidationError("授权码不能为空")

        # 调用第三方接口获取 openid
        openid = auth.oauth_authentication(serializer.instance.type, code)
        if not openid:
            raise serializers.ValidationError("第三方授权失败")

        serializer.save(openid=openid, is_bound=True)

    # DELETE -> 解绑
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_bound = False
        instance.openid = None
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserInfoView(RetrieveAPIView):
    """用户基本信息展示视图"""
    serializer_class = UserInfoSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                required=False,
                location='query',
                description="指定用户ID，如果不填则返回当前登录用户信息"
            )
        ],
        operation_id="user_info_retrieve"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return User.objects.get(id=user_id)
        return self.request.user


class UserInfoDetailView(RetrieveUpdateAPIView):
    """ 用户基本信息修改视图 """
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated, permissions.IsSelf, permissions.IsActiveAccount]
    lookup_field = 'id'  # 指定查找字段，但其实下面 get_object 会直接用 request.user

    def get_object(self):
        # 直接返回当前登录用户
        return self.request.user
