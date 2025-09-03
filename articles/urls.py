from django.urls import path
from .views import ArticleView, ArticleDetailView, TagListView, TagArticleView, ArticleListView, ArticleListDetailView, \
    ReadingHistoryListView, ReadingHistoryDestroyView

urlpatterns = [
    # 公开列表和标签相关放前面，避免被 <slug> 抢占
    path('', ArticleListView.as_view(), name='article-list'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('tags/<slug:slug>/', TagArticleView.as_view(), name='tag-article'),

    # 个人文章（需要登录）
    path('my/', ArticleView.as_view(), name='my-article'),
    path('my/<slug:slug>/', ArticleDetailView.as_view(), name='my-article-detail'),

    # 阅读历史
    path('history/', ReadingHistoryListView.as_view(), name='article-history-list'),
    path('history/<int:history_id>/', ReadingHistoryDestroyView.as_view(), name='article-history-destroy'),

    # 公开详情（最后，以免与上面的前缀冲突）
    path('<slug:slug>/', ArticleListDetailView.as_view(), name='article-detail'),
]
