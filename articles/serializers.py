from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Article, Tag, ReadingHistory

User = get_user_model()


# 嵌套序列化作者信息（仅展示部分字段）
class AuthorNestedSerializer(serializers.ModelSerializer):
    followers = serializers.IntegerField(source="followers.count", read_only=True)  # 统计关注者数量

    class Meta:
        model = User
        fields = ['id', 'username', 'followers']


# 嵌套序列化标签信息，用于文章列表
class TagNestedSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()  # 动态生成标签链接

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'url']
        extra_kwargs = {
            'slug': {'read_only': True},
            'url': {'read_only': True}
        }

    def get_url(self, obj):
        return obj.get_absolute_url()  # 返回标签详情页 URL


# 标签序列化器（带文章数量统计）
class TagSerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField(read_only=True)  # 统计已发布文章数量
    url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'url', 'article_count']
        extra_kwargs = {
            'slug': {'read_only': True},
            'url': {'read_only': True}
        }

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_article_count(self, obj):
        # 统计已发布的文章数量（非草稿，发布时间 <= 当前时间）
        return obj.articles.filter(
            is_draft=False,
            published_at__lte=timezone.now()
        ).count()


# 文章列表序列化器（用于列表接口）
class ArticleListSerializer(serializers.ModelSerializer):
    tags = TagNestedSerializer(many=True, read_only=True)
    author = AuthorNestedSerializer(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        # 列表接口不返回 content 字段
        exclude = ['created_at', 'updated_at', 'content', 'is_draft', 'slug']
        extra_kwargs = {
            'published_at': {'read_only': True},
            'cover_pic': {'required': False},
        }

    def get_url(self, obj):
        return obj.get_absolute_url()


# 文章详情序列化器（比列表多 content 字段）
class ArticleListDetailSerializer(serializers.ModelSerializer):
    tags = TagNestedSerializer(many=True, read_only=True)
    author = AuthorNestedSerializer(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        exclude = ['created_at', 'updated_at', 'is_draft', 'slug']
        extra_kwargs = {
            'published_at': {'read_only': True},
            'cover_pic': {'required': False},
        }

    def get_url(self, obj):
        return obj.get_absolute_url()


# 用于创建/更新文章接口，支持前端传入标签列表
class ArticleSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),  # 允许前端传字符串列表
        write_only=True,
        required=False,
    )
    tag_list = TagNestedSerializer(many=True, read_only=True, source="tags")  # 返回嵌套标签信息
    url = serializers.SerializerMethodField(read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        exclude = ['created_at', 'updated_at', 'author', 'slug']
        extra_kwargs = {
            'published_at': {'required': False},
            'cover_pic': {'required': False},
        }

    def _validate_published_at(self, is_draft, published_at):
        if is_draft and published_at:
            raise serializers.ValidationError("草稿不能设置发布时间")
        if not is_draft and not published_at:
            return timezone.now()
        return published_at

    def validate(self, attrs):
        """
        草稿与发布时间校验：
        - 草稿不允许设置 published_at
        - 非草稿未设置 published_at → 自动填充当前时间
        - 非草稿 + future 时间 → 定时发布
        """
        is_draft = attrs.get("is_draft", True)
        published_at = attrs.get("published_at")
        return attrs

    def get_url(self, obj):
        return obj.get_absolute_url()

    def _handle_tags(self, tags_data):
        """创建或获取 Tag 对象列表"""
        if not tags_data:
            return []
        return [Tag.objects.get_or_create(name=name)[0] for name in tags_data]

    def create(self, validated_data):
        # 处理前端传入的标签
        tags_data = validated_data.pop("tags", [])
        article = Article.objects.create(**validated_data)
        article.tags.set(self._handle_tags(tags_data))
        return article

    def update(self, instance, validated_data):
        # 更新文章时也可修改标签
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags_data is not None:
            instance.tags.set(self._handle_tags(tags_data))
        return instance


# 阅读历史序列化器
class ReadingHistorySerializer(serializers.ModelSerializer):
    article = ArticleListSerializer(read_only=True)  # 嵌套返回文章信息

    class Meta:
        model = ReadingHistory
        exclude = ['user']  # 用户字段不对外展示
