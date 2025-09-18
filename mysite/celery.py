import os
from celery import Celery

# 设置默认的 Django 配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# 创建 Celery 应用
# app = Celery('mysite', broker='redis://127.0.0.1:6379/1')
app = Celery(
    'mysite',
    broker='amqp://guest:guest@127.0.0.1:5672//',  # RabbitMQ 地址
)

# 自动发现所有 app 下的 tasks.py
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.timezone = 'Asia/Shanghai'  # 推荐设置时区，避免定时跑偏

# 定时任务配置
app.conf.beat_schedule = {
    # 任务名：定时清理过期jwt
    'clear-expired-jwt-tokens-daily': {
        'task': 'users.tasks.clear_expired_tokens',  # 指向我们定义的任务
        'schedule': crontab(hour=11, minute=18),  # 使用 crontab 语法
    },
}
