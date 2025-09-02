from django.contrib import admin
from .models import UserContact, CustomUser

# 基本注册（无自定义配置）
admin.site.register(CustomUser)
admin.site.register(UserContact)
