#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name   : oauth.py
Author      : wzw
Date Created: 2025/9/2
Description : Add your script's purpose here.
"""
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse

from apps.user.models import User, UserContact
from utils.auth import make_token, make_random_password, password_hash, generate_salt
from apps.oauth.tasks import save_remote_avatar
from utils.base_view import BaseView
from apps.oauth import serivces

"""
绑定 = 登录态下追加一条 UserContact。

登录 = 没有账号就新建，有账号就直接用。

合并 = 把 UserContact 转到目标用户上，同时迁移数据，删除多余的用户。
"""


# Create your views here.
class WeiboView(BaseView):
    def get(self, request):
        # 生成授权地址，返回给前端，供用户点击跳转
        auth_url = (
            f"https://api.weibo.com/oauth2/authorize?"
            f"client_id={settings.WEIBO_APP_KEY}"
            f"&response_type=code"
            f"&redirect_uri={settings.WEIBO_REDIRECT_URI}"  # 回调地址
        )
        return JsonResponse({'code': 200, "auth_url": auth_url})

    def post(self, request):
        # 获取授权码，通过授权码获取access_token，再通过access_token获取用户信息
        data = request.data
        code = data.get("code")
        if not code:
            return JsonResponse({'code': 400, "error": "授权码不能为空"})

        token_data = serivces.get_access_token_weibo(code)
        access_token = token_data["access_token"]
        uid = token_data["uid"]
        # print(access_token, uid)

        user_info = serivces.get_user_info_weibo(access_token, uid)
        # print(user_info)

        # 用户绑定或创建
        try:
            # 有联系方式，就登录
            user_weibo = UserContact.objects.get(type='weibo', value=uid, is_verified=True, is_delete=False)
        except UserContact.DoesNotExist:
            user_weibo = None

        if user_weibo:
            try:
                user = User.objects.get(usercontact=user_weibo)
            except User.DoesNotExist:
                return JsonResponse({'code': 400, "error": "用户不存在"})
        else:
            # 没有联系方式，就创建新用户，绑定该联系方式
            try:
                with transaction.atomic():
                    salt = generate_salt()
                    user = User.objects.create(
                        # 可能重名，拼接一下
                        username=f'weibo_{uid}',
                        salt=salt,
                        password=password_hash(make_random_password(), salt=salt),
                    )
                    user_weibo = UserContact.objects.create(
                        user=user, type='weibo', value=uid,
                        is_verified=True, is_delete=False
                    )
                    user.save()
                    user_weibo.save()
                # 保存用户头像，异步进行
                save_remote_avatar.delay(user.id, user_info["avatar_hd"])
            except Exception as e:
                return JsonResponse({'code': 400, "error": "用户创建失败"})

        token = make_token(user.username)
        return JsonResponse({"code": 200, 'message': '登录成功', "token": token, 'username': user.username})
