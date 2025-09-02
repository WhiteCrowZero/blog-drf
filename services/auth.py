import random
import string

from rest_framework_simplejwt.tokens import RefreshToken


def oauth_register(type, code):
    return f'{type}-{code}-test'

def generate_tokens_for_user(user):
    """使用 simple-jwt 生成 access/refresh token"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)

def make_random_password(length=8):
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))
