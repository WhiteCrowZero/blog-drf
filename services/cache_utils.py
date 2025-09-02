#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name   : cache_utils.py
Author      : wzw
Date Created: 2025/9/2
Description : 为其他服务提供基础的缓存服务
"""

from django.conf import settings
from django.core.cache import caches

class CacheVerifyService:
    @staticmethod
    def set_verify_code(key, code, cache='default', exp=settings.DEFAULT_EXPIRE_SECONDS):
        """设置缓存验证码"""
        caches[cache].set(key, code, exp)

    @staticmethod
    def validate_verify_code(key, code, cache='default'):
        """校验缓存验证码"""
        cached_code = caches[cache].get(key)
        if cached_code is None:
            return False, '验证码已过期'
        if code != cached_code:
            return False, '验证码错误'
        return True, None

    @staticmethod
    def del_verify_code(key, cache='default'):
        """删除缓存验证码"""
        caches[cache].delete(key)

    @staticmethod
    def get_verify_code(key, cache='default'):
        """获取缓存验证码"""
        return caches[cache].get(key)


cache_verify_service = CacheVerifyService()

