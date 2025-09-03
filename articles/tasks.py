from django.contrib.auth import get_user_model
from django.utils import timezone

from articles.models import Article, ReadingHistory
from mysite.celery import app

User = get_user_model()


@app.task
def record_reading_history(user_id, article_id):
    """ 异步记录用户阅读历史 """
    user = User.objects.get(id=user_id)
    article = Article.objects.get(id=article_id)
    ReadingHistory.objects.get_or_create(
        user=user,
        article=article,
        defaults={'last_read_at': timezone.now()}
    )
