from django.contrib import admin
from .models import Like, Collection, CollectionItem, Comment, Follow

# 基本注册（无自定义配置）
admin.site.register(Like)
admin.site.register(Collection)
admin.site.register(CollectionItem)
admin.site.register(Comment)
admin.site.register(Follow)
