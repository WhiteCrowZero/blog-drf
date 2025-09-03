from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from services import permissions
from .models import Article, Tag
from .serializers import ArticleSerializer, TagSerializer, ArticleListDetailSerializer, ArticleListSerializer
from rest_framework import generics, filters

User = get_user_model()

# TODO: 阅读历史功能（新建一对多模型）

class ArticleView(generics.ListCreateAPIView):
    """ 用户文章列表视图 """
    serializer_class = ArticleSerializer

    filter_backends = [filters.OrderingFilter]  # 启用排序
    ordering_fields = ['like_count', 'favorite_count', 'published_at', 'created_at']  # 可排序字段
    ordering = ['-published_at']  # 默认排序

    def get_queryset(self):
        # 只返回当前用户的文章
        return (
            Article.objects.filter(author=self.request.user)
            .select_related('author')
            .prefetch_related('tags')
        )

    def perform_create(self, serializer):
        # 保存文章，自动设置作者为当前用户
        serializer.save(author=self.request.user)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ 用户文章修改视图 """
    serializer_class = ArticleSerializer
    lookup_field = 'slug'  # 指定使用 slug 作为查找字段
    permission_classes = [IsAuthenticated, permissions.IsSelf, permissions.IsActiveAccount]

    def get_queryset(self):
        # 只返回当前用户的文章
        return (
            Article.objects.filter(author=self.request.user)
            .select_related('author')
            .prefetch_related('tags')
        )


class ArticleListView(generics.ListAPIView):
    """文章列表视图（公开版本，可选 user_id 查询）"""
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['like_count', 'favorite_count', 'published_at']
    ordering = ['-published_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                required=False,
                description="指定作者ID，如果不填则返回所有文章"
            )
        ],
        operation_id="articles_list"
    )
    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        qs = Article.objects.filter(
            is_draft=False,
            published_at__lte=timezone.now()
        ).select_related('author').prefetch_related('tags')

        if user_id:
            qs = qs.filter(author_id=user_id)

        qs = qs.annotate(
            like_count=Count('likes', distinct=True),
            favorite_count=Count('collected_items', distinct=True)
        )
        return qs


class ArticleListDetailView(generics.RetrieveAPIView):
    """ 文章详情页视图（公开版本） """
    serializer_class = ArticleListDetailSerializer
    permission_classes = [AllowAny]  # 允许任何人访问
    lookup_field = 'slug'

    queryset = (
        Article.objects.filter(
            is_draft=False,
            published_at__lte=timezone.now()
        )
        .select_related('author')
        .prefetch_related('tags')
        .annotate(
            like_count=Count('likes', distinct=True),
            favorite_count=Count('collected_items', distinct=True)
        )
    )


class TagListView(generics.ListAPIView):
    """ 标签列表视图（公开版本） """
    serializer_class = TagSerializer
    permission_classes = [AllowAny]  # 允许任何人访问

    def get_queryset(self):
        # 按需：只列出“至少有一篇已发布文章”的标签
        return (
            Tag.objects.all()
            .prefetch_related('articles')
            .order_by('-name')
        )


class TagArticleView(generics.ListAPIView):
    """ 标签文章列表视图（公开版本） """
    serializer_class = ArticleListSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]  # 允许任何人访问

    filter_backends = [filters.OrderingFilter]  # 启用排序
    ordering_fields = ['like_count', 'favorite_count', 'published_at']  # 可排序字段
    ordering = ['-published_at']  # 默认排序

    def get_queryset(self):
        slug = self.kwargs['slug']
        return (
            Article.objects.filter(
                tags__slug=slug,
                is_draft=False,
                published_at__lte=timezone.now()
            )
            .select_related('author')
            .prefetch_related('tags')
            .distinct()
        )
