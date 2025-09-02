import os
from celery import Celery

# 设置默认的 Django 配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# 创建 Celery 应用
app = Celery('mysite', broker='redis://127.0.0.1:6379/1')

# 自动发现所有 app 下的 tasks.py
app.autodiscover_tasks()
