from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Article, Tag, ReadingHistory

User = get_user_model()


class AuthorNestedSerializer(serializers.ModelSerializer):
    followers = serializers.IntegerField(source="followers.count", read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'followers']


class TagNestedSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'url']
        extra_kwargs = {
            'slug': {'read_only': True},
            'url': {'read_only': True}
        }

    def get_url(self, obj):
        return obj.get_absolute_url()


class TagSerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField(read_only=True)
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
        # 统计已发布的文章数量（非草稿，发布时间小于等于当前时间）
        return obj.articles.filter(
            is_draft=False,
            published_at__lte=timezone.now()
        ).count()


class ArticleListSerializer(serializers.ModelSerializer):
    tags = TagNestedSerializer(many=True, read_only=True)
    author = AuthorNestedSerializer(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

    like_count = serializers.IntegerField(read_only=True)
    favorite_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Article
        exclude = ['created_at', 'updated_at', 'content', 'is_draft', 'slug']
        extra_kwargs = {
            'published_at': {'read_only': True},
            'cover_pic': {'required': False},
        }

    def get_url(self, obj):
        return obj.get_absolute_url()


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


class ArticleSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),  # 允许前端传字符串列表
        write_only=True,
        required=False,
    )
    tag_list = TagNestedSerializer(many=True, read_only=True, source="tags")
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

    def validate(self, attrs):
        '''
        草稿 → 必须没 published_at
        非草稿 → 没 published_at 就设为当前时间
        非草稿 + future 时间 → 变成定时发布
        '''
        is_draft = attrs.get("is_draft", True)
        published_at = attrs.get("published_at")

        if is_draft and published_at:
            raise serializers.ValidationError("草稿不能设置发布时间")

        if not is_draft and not published_at:
            attrs["published_at"] = timezone.now()

        return attrs

    def get_url(self, obj):
        return obj.get_absolute_url()

    def create(self, validated_data):
        tags_data = validated_data.pop("tags", [])
        article = Article.objects.create(**validated_data)

        tag_objs = []
        for tag_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objs.append(tag)
        article.tags.set(tag_objs)

        return article

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)

        if tags_data is not None:
            tag_objs = []
            for tag_name in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                tag_objs.append(tag)
            instance.tags.set(tag_objs)

        return instance


class ReadingHistorySerializer(serializers.ModelSerializer):
    article = ArticleListSerializer(read_only=True)

    class Meta:
        model = ReadingHistory
        exclude = ['user']
