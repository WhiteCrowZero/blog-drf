from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from articles.models import Article, ReadingHistory
from mysite.celery import app

User = get_user_model()

# TODO:异步任务缩略图

@app.task
def compress_avatar():
    """ 生成用户上传图片的缩略图 """
    pass


@app.task
def clear_expired_tokens():
    """
    定时清理过期的黑名单和白名单 token
    """
    now = timezone.now()

    # 清理已过期的黑名单 token
    expired_blacklist = BlacklistedToken.objects.filter(
        token__expires_at__lt=now
    )
    count_blacklist = expired_blacklist.count()
    expired_blacklist.delete()

    # 清理已过期的 OutstandingToken（未被黑名单的）
    expired_outstanding = OutstandingToken.objects.filter(expires_at__lt=now)
    count_outstanding = expired_outstanding.count()
    expired_outstanding.delete()

    print(f"[{now}] 清理过期 token: blacklist={count_blacklist}, outstanding={count_outstanding}")
    return {"blacklist_deleted": count_blacklist, "outstanding_deleted": count_outstanding}


