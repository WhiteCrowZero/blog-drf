#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name   : oauth.py
Author      : wzw
Date Created: 2025/9/2
Description : Add your script's purpose here.
"""

import abc
import requests
from django.conf import settings

# 可复用的第三方类型
CONTACT_CHOICES = (
    ('google', 'Google'),
    ('facebook', 'Facebook'),
    ('qq', 'QQ'),
    ('wechat', 'WeChat'),
    ('weibo', 'Weibo'),
)


# 抽象基类
class OauthVerify(abc.ABC):
    """第三方 OAuth 验证抽象类"""

    @staticmethod
    @abc.abstractmethod
    def _get_access_token(code: str) -> dict:
        """获取 access_token"""
        pass

    @staticmethod
    @abc.abstractmethod
    def _get_user_info(access_token: str, openid: str) -> dict:
        """获取用户信息（仅类内调用）"""
        pass

    @abc.abstractmethod
    def get_user_info(self, code: str) -> dict:
        """获取用户信息"""
        pass

    @abc.abstractmethod
    def authentication(self, code: str) -> str:
        """返回第三方用户唯一标识（如 uid）"""
        pass


# 微博实现类
class OauthWeiboVerify(OauthVerify):

    @staticmethod
    def _get_access_token(code: str) -> dict:
        """获取微博 access_token"""
        url = "https://api.weibo.com/oauth2/access_token"
        data = {
            "client_id": settings.WEIBO_APP_KEY,
            "client_secret": settings.WEIBO_APP_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.WEIBO_REDIRECT_URI,
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to get access_token: {e}")

        return response.json()

    @staticmethod
    def _get_user_info(access_token: str, openid: str) -> dict:
        url = "https://api.weibo.com/2/users/show.json"
        params = {"access_token": access_token, "uid": openid}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to get user info: {e}")

        return response.json()

    def get_user_info(self, code: str) -> dict:
        """获取微博用户信息"""
        token_data = self._get_access_token(code)
        access_token = token_data["access_token"]
        openid = token_data["uid"]
        user_info = self._get_user_info(access_token, openid)
        return user_info

    def authentication(self, code: str) -> str:
        """获取微博 uid"""
        token_data = self._get_access_token(code)
        openid = token_data["uid"]
        return openid


# 谷歌实现类
class OauthGoogleVerify(OauthVerify):
    pass
