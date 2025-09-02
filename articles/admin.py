from django.contrib import admin
from .models import Article, Tag


# Admin 配置
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_draft', 'published_at', 'created_at')
    list_filter = ('is_draft', 'published_at', 'tags', 'created_at')
    search_fields = ('title', 'content')
    # prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'slug')
    date_hierarchy = 'published_at'
    filter_horizontal = ('tags',)  # 让多对多字段选择更方便
    fieldsets = (
        ('文章与作者', {
            'fields': ('title', 'slug', 'content', 'author')
        }),
        ('状态与时间', {
            'fields': ('is_draft', 'published_at', 'created_at', 'updated_at')
        }),
        ('媒体与分类', {
            'fields': ('cover_pic', 'tags')
        }),
    )
