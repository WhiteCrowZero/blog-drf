import random
import string

from rest_framework_simplejwt.tokens import RefreshToken
from services.oauth import OauthWeiboVerify

def generate_tokens_for_user(user):
    """使用 simple-jwt 生成 access/refresh token"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def make_random_password(length=8):
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))


def make_random_verify_code(length=5):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

oauth_weibo_verify = OauthWeiboVerify()

def oauth_authentication(type, code):
    try:
        if type == 'weibo':
            openid = oauth_weibo_verify.authentication(code)
            return openid
        elif type == 'google':
            pass
        elif type == 'facebook':
            pass
        elif type == 'wechat':
            pass
        elif type == 'qq':
            pass
        else:
            return None
    except Exception as e:
        return None

    # # 测试业务逻辑用
    # return f'{type}-{code}-test'
